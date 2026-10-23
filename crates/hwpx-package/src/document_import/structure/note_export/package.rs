//! A derived archive through the existing writer's package/ID/preservation checks.
use super::{Collection,E,NoteFileExportCandidate,NoteFileExportReceipt,NoteFileSelection,xml,note_file_export_request_sha256};
use crate::{BoundedZipReader,NoteHwpxLimits,PackageLimits,PackagePath,PreservingXmlDocument as Xml,
    WriterLimits,document_import::{ImportedSourcePackage,structure::ImportedDocumentStructure},
    writer::BoundedArchiveBuffer};
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},io::{Cursor,Write as _}};
use zip::{CompressionMethod,DateTime,ZipWriter,write::SimpleFileOptions};

pub(super) fn build(original:&ImportedDocumentStructure,fresh:&[u8],selection:NoteFileSelection,
    collection:Collection,limits:NoteHwpxLimits,writer:WriterLimits,zip:PackageLimits)->Result<NoteFileExportCandidate,E> {
    let source=original.source();
    let forbidden=["META-INF/signatures.xml","META-INF/encryption.xml","META-INF/rights.xml"];
    for part in source.parts() {
        if forbidden.iter().any(|name|part.path().as_str().eq_ignore_ascii_case(name)){return Err(E::Security);}
        if let Some(doc)=part.xml(){
            if doc.elements().iter().any(|n|n.name().namespace()==Some("http://www.w3.org/2000/09/xmldsig#")
                ||n.name().namespace()==Some("urn:oasis:names:tc:opendocument:xmlns:manifest:1.0")&&n.name().local_name()=="encryption-data") {return Err(E::Security);}
        }
    }
    let removed_ids:BTreeSet<_>=source.graph.relationships.iter().filter(|r|collection.omitted.contains(&r.target)).map(|r|r.id.as_str()).collect();
    let removed_paths:BTreeSet<_>=collection.omitted.iter().map(PackagePath::as_str).collect();
    let mut changes=BTreeMap::<PackagePath,Vec<u8>>::new();
    let sections:BTreeMap<_,_>=collection.sections.iter().map(|s|(&s.path,s.bytes.as_slice())).collect();
    let mut body_elements=0usize;
    for section in &collection.sections {
        body_elements=body_elements.checked_add(section.elements).filter(|n|*n<=limits.config().paragraphs).ok_or(E::Limit)?;
    }
    for part in source.parts() {
        let path=part.path();let name=path.as_str();
        if name.starts_with("Preview/")&&!matches!(name,"Preview/PrvText.txt"|"Preview/PrvImage.png"){return Err(E::Shape);}
        let Some(doc)=part.xml()else{continue};
        // Body namespace/spine classification wins over coincidental metadata
        // filenames. Do not scan/copy its original payload a second time.
        if sections.contains_key(path)||collection.omitted.contains(path){continue;}
        let mut remove=Vec::new();
        let metadata=path==&source.graph.package_document||matches!(name,"META-INF/container.rdf"|"META-INF/manifest.xml"|"settings.xml");
        if metadata { for n in doc.elements() {
            let ns=n.name().namespace();let local=n.name().local_name();
            let is_opf=matches!(ns,Some("http://www.idpf.org/2007/opf"|"http://www.idpf.org/2007/opf/"));
            let opf_drop=path==&source.graph.package_document&&is_opf&&match local {
                "item"=>xml::attr(n,"id").is_some_and(|id|removed_ids.contains(id)),
                "itemref"=>xml::attr(n,"idref").is_some_and(|id|removed_ids.contains(id)),_=>false,
            };
            let rdf_drop=name=="META-INF/container.rdf"&&n.attributes().iter().any(|a|
                a.name().namespace()==Some("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
                    &&matches!(a.name().local_name(),"about"|"resource")&&removed_paths.contains(a.semantic_value()));
            let odf_drop=name=="META-INF/manifest.xml"&&n.attributes().iter().any(|a|
                a.name().local_name()=="full-path"&&removed_paths.contains(a.semantic_value()));
            let caret_drop=name=="settings.xml"&&ns==Some("http://www.hancom.co.kr/hwpml/2011/app")&&local=="CaretPosition";
            if opf_drop||rdf_drop||odf_drop||caret_drop {
                if n.parent().is_none(){return Err(E::Shape);}
                let span=n.outer_span().ok_or(E::Shape)?;remove.push((span.start(),span.end()));
            }
        }}
        if !remove.is_empty(){changes.insert(path.clone(),prune(doc,remove,limits.config().section_bytes)?);}
        let root=&doc.elements()[doc.root_element()];
        if root.name().namespace()==Some("http://www.hancom.co.kr/hwpml/2011/head")&&root.name().local_name()=="head" {
            if let Some(a)=root.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="secCnt") {
                if a.semantic_value().parse::<usize>().ok()!=Some(original.receipt().sections){return Err(E::Shape);}
                let value=collection.sections.len().to_string();
                if a.semantic_value()!=value {
                    let span=a.value_span();
                    changes.insert(path.clone(),doc.with_source_bytes(|raw|xml::replace(raw,span.start(),span.end(),value.as_bytes(),limits.config().section_bytes))?);
                }
            }
        }
    }
    let cap=writer.config().max_output_bytes.min(zip.config().max_archive_bytes).min(limits.config().output_bytes as u64);
    let mut output=ZipWriter::new(BoundedArchiveBuffer::new(cap));
    let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
    let mut fingerprints=BTreeMap::<PackagePath,[u8;32]>::new();
    let(mut preserved,mut expanded)=(0usize,0usize);
    for i in 0..reader.entries().len() {
        let path=reader.entries()[i].path.clone();
        if collection.omitted.contains(&path){continue;}
        let source_bytes=reader.read_entry(i).map_err(|_|E::Source)?;
        let bytes=if path.as_str()=="Preview/PrvText.txt" {b"".as_slice()}
            else if path.as_str()=="Preview/PrvImage.png" {crate::vs0::neutral_preview_png()}
            else if let Some(value)=sections.get(&path){*value}
            else if let Some(value)=changes.get(&path){value.as_slice()}else{preserved+=1;source_bytes.as_slice()};
        expanded=expanded.checked_add(bytes.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        output.start_file(path.as_str(),SimpleFileOptions::default().compression_method(CompressionMethod::Stored)
            .last_modified_time(DateTime::default()).unix_permissions(0o644)).map_err(|_|E::Zip)?;
        output.write_all(bytes).map_err(|_|E::Limit)?;
        fingerprints.insert(path,Sha256::digest(bytes).into());
    }
    let bytes=output.finish().map_err(|_|E::Zip)?.into_inner().map_err(|_|E::Limit)?;
    crate::writer::validate_note_export_archive(&bytes,zip).map_err(|e|E::Trust(e.code()))?;
    let sha=Sha256::digest(&bytes).into();
    let imported=ImportedSourcePackage::import(&bytes,source.document_id().clone(),sha,source.limits).map_err(|_|E::Readback)?;
    let reopened=ImportedDocumentStructure::import(imported).map_err(|_|E::Readback)?;
    if !reopened.notes().is_empty()||reopened.receipt().sections!=collection.sections.len(){return Err(E::Readback);}
    let actual:BTreeMap<_,_>=reopened.source().parts().iter().map(|p|(p.path(),p)).collect();
    if actual.len()!=fingerprints.len(){return Err(E::Preservation);}
    for (path,sha) in &fingerprints {
        let part=actual.get(path).ok_or(E::Preservation)?;
        if part.anchor().fingerprint_sha256!=*sha{return Err(E::Preservation);}
    }
    for section in &collection.sections {
        let next=actual.get(&section.path).and_then(|p|p.xml()).ok_or(E::Readback)?;
        if !next.with_source_bytes(|b|b==section.bytes){return Err(E::Preservation);}
    }
    let receipt=NoteFileExportReceipt {
        profile:"hwpx-agent.source-note-file-hwpx/v1",capability_id:"ref.note_export",selection,
        source_package_sha256:source.receipt().source_package_sha256,output_package_sha256:sha,
        request_sha256:note_file_export_request_sha256(source.receipt().source_package_sha256,selection),
        selected_note_source_sha256:collection.body_sha,selected_notes:collection.notes,output_body_elements:body_elements,
        output_body_sections:collection.sections.len(),omitted_body_sections:collection.omitted.len(),preserved_source_parts:preserved,
        output_bytes:bytes.len(),protection_element_visits:collection.visits,source_order_preserved:true,
        selected_body_xml_namespace_closed:true,header_style_and_resource_bytes_preserved:true,
        original_main_body_and_standard_previews_not_reused:true,non_body_metadata_and_resources_may_contain_source_data:true,
        note_container_layout_and_native_numbering_qualified:false,native_save_reopen_render_qualified:false,
        complete_protection_qualified:false,execution_publication_authority:false,
    };
    Ok(NoteFileExportCandidate {bytes:bytes.into_boxed_slice(),receipt,package_limits:zip})
}
fn prune(doc:&Xml,mut remove:Vec<(usize,usize)>,max:usize)->Result<Vec<u8>,E> {
    remove.sort_unstable_by_key(|&(start,end)|(start,std::cmp::Reverse(end)));
    doc.with_source_bytes(|bytes|{
        let mut out=Vec::new();let mut at=0usize;
        for (start,end) in remove {
            if start<at {if end<=at{continue;}return Err(E::Shape);}
            xml::append(&mut out,bytes.get(at..start).ok_or(E::Source)?,max)?;at=end;
        }
        xml::append(&mut out,bytes.get(at..).ok_or(E::Source)?,max)?;Ok(out)
    })
}
