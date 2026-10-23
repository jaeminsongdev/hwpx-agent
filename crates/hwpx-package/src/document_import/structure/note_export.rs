//! REF-025 actual note-only HWPX candidate, not a digest-manifest substitute.
mod xml;
mod package;
use super::{ImportedDocumentStructure,caption_text_batch::observed_protection,caption_style_batch::subtree_protection};
use crate::{NoteHwpxLimits,PackageLimits,PackagePath,WriterLimits};
use domain_ir::NoteKind;
use crate::document_import::forms::{ImportedDocumentForms,VerifiedFormReconstruction};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt};
use thiserror::Error;

#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum NoteFileSelection { Footnotes,Endnotes,Both }
impl NoteFileSelection {
    fn includes(self,kind:NoteKind)->bool {matches!(self,Self::Both)||matches!((self,kind),(Self::Footnotes,NoteKind::Footnote)|(Self::Endnotes,NoteKind::Endnote))}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum NoteFileExportError {
    #[error("NOTE_FILE_SOURCE_REJECTED")] Source,
    #[error("NOTE_FILE_NO_SELECTED_NOTES")] NoNotes,
    #[error("NOTE_FILE_SOURCE_SHAPE_REJECTED")] Shape,
    #[error("NOTE_FILE_NAMESPACE_REJECTED")] Namespace,
    #[error("NOTE_FILE_INHERITED_XML_CONTEXT_UNQUALIFIED")] InheritedContext,
    #[error("NOTE_FILE_SOURCE_COVERAGE_REJECTED")] Coverage,
    #[error("NOTE_FILE_OBSERVED_PROTECTION")] Protection,
    #[error("NOTE_FILE_ACTIVE_OR_SIGNED_SECURITY_UNQUALIFIED")] Security,
    #[error("NOTE_FILE_FINITE_LIMIT")] Limit,
    #[error("NOTE_FILE_WRITER_TRUST_REJECTED:{0}")] Trust(&'static str),
    #[error("NOTE_FILE_ZIP_REJECTED")] Zip,
    #[error("NOTE_FILE_READBACK_REJECTED")] Readback,
    #[error("NOTE_FILE_PRESERVATION_REJECTED")] Preservation,
}
type E=NoteFileExportError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NoteFileExportReceipt {
    pub profile:&'static str,pub capability_id:&'static str,pub selection:NoteFileSelection,
    pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub request_sha256:[u8;32],
    pub selected_note_source_sha256:[u8;32],pub selected_notes:usize,pub output_body_elements:usize,
    pub output_body_sections:usize,pub omitted_body_sections:usize,pub preserved_source_parts:usize,
    pub output_bytes:usize,pub protection_element_visits:usize,
    pub source_order_preserved:bool,pub selected_body_xml_namespace_closed:bool,
    pub header_style_and_resource_bytes_preserved:bool,pub original_main_body_and_standard_previews_not_reused:bool,
    pub non_body_metadata_and_resources_may_contain_source_data:bool,
    pub note_container_layout_and_native_numbering_qualified:bool,pub native_save_reopen_render_qualified:bool,
    pub complete_protection_qualified:bool,pub execution_publication_authority:bool,
}
pub struct NoteFileExportCandidate {
    bytes:Box<[u8]>,receipt:NoteFileExportReceipt,package_limits:PackageLimits,
}
impl fmt::Debug for NoteFileExportCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NoteFileExportCandidate(<redacted>; not_native_or_authority)")}
}
impl NoteFileExportCandidate {
    #[must_use] pub const fn receipt(&self)->&NoteFileExportReceipt {&self.receipt}
    /// Original writer trust chain and immutable bytes only; not source access.
    /// # Errors
    /// Rejects SHA or package/ID/preservation drift before exposing file bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,E> {
        if <[u8;32]>::from(Sha256::digest(&self.bytes))!=self.receipt.output_package_sha256
            ||self.bytes.len()!=self.receipt.output_bytes{return Err(E::Preservation);}
        crate::writer::validate_note_export_archive(&self.bytes,self.package_limits).map_err(|e|E::Trust(e.code()))?;
        Ok(consume(&self.bytes))
    }
}
struct Section {path:PackagePath,bytes:Vec<u8>,elements:usize}
struct Collection {sections:Vec<Section>,omitted:BTreeSet<PackagePath>,notes:usize,body_sha:[u8;32],visits:usize}

/// Original ordered source/selection digest, not source or access authority.
#[must_use]
pub fn note_file_export_request_sha256(source_sha256:[u8;32],selection:NoteFileSelection)->[u8;32] {
    let mut hash=Sha256::new();hash.update(b"hwpx-agent.source-note-file-hwpx/v1\0");hash.update(source_sha256);
    hash.update([match selection {NoteFileSelection::Footnotes=>0,NoteFileSelection::Endnotes=>1,NoteFileSelection::Both=>2}]);
    hash.finalize().into()
}

impl ImportedDocumentStructure {
    /// Exports all notes of the selected families, in source XML insertion order,
    /// into ordinary HWPX body paragraphs without overwriting the original.
    /// Retains source style/resources and metadata; this is NOT a redaction tool.
    /// # Errors
    /// Rejects stale source, empty selection, malformed/hidden notes, protection,
    /// active/signed security, finite limits and original writer/readback failures.
    pub fn export_note_file_candidate(&self,fresh:&[u8],selection:NoteFileSelection,
        limits:NoteHwpxLimits,writer:WriterLimits)->Result<NoteFileExportCandidate,E> {
        self.export_note_file_checked(fresh,selection,limits,writer,
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))
    }
    fn export_note_file_checked(&self,fresh:&[u8],selection:NoteFileSelection,
        limits:NoteHwpxLimits,writer:WriterLimits,check:impl FnOnce()->Result<(),E>)->Result<NoteFileExportCandidate,E> {
        check()?;
        self.export_note_file_verified(fresh,selection,limits,writer)
    }
    // One non-generic compiler shared by direct and operation-local Form proof.
    fn export_note_file_verified(&self,fresh:&[u8],selection:NoteFileSelection,
        limits:NoteHwpxLimits,writer:WriterLimits)->Result<NoteFileExportCandidate,E> {
        let zip=self.source().limits.zip().map_err(|_|E::Source)?;
        crate::writer::validate_note_export_archive(fresh,zip).map_err(|e|E::Trust(e.code()))?;
        let active=self.source().assess_active_content(crate::ActiveContentLimits::default()).map_err(|_|E::Security)?.counts();
        if active.blocked!=0||active.quarantined!=0||active.review_required!=0{return Err(E::Security);}
        let collected=self.collect_note_file(selection,limits)?;
        package::build(self,fresh,selection,collected,limits,writer,zip)
    }
    fn collect_note_file(&self,selection:NoteFileSelection,limits:NoteHwpxLimits)->Result<Collection,E> {
        if self.notes().len()>limits.config().notes{return Err(E::Limit);}
        let mut wanted=BTreeMap::<PackagePath,Vec<(usize,usize)>>::new();
        let mut note_sha=Sha256::new();note_sha.update(b"hwpx-agent.source-note-file-selected-bodies/v1\0");
        let mut notes=0usize;
        for note in self.notes() {
            let kind=match note.native_kind.as_str(){"footNote"=>NoteKind::Footnote,"endNote"=>NoteKind::Endnote,_=>return Err(E::Shape)};
            if !selection.includes(kind){continue;}
            let marker=self.source().resolve_anchor(&note.source_anchor).map_err(|_|E::Source)?;
            let body=self.source().resolve_anchor(&note.body_anchor).map_err(|_|E::Source)?;
            if marker.part().path()!=body.part().path(){return Err(E::Source);}
            wanted.entry(marker.part().path().clone()).or_default().push((marker.element_index().ok_or(E::Source)?,body.element_index().ok_or(E::Source)?));
            note_sha.update(note.source_anchor.fingerprint_sha256);note_sha.update(note.body_anchor.fingerprint_sha256);notes+=1;
        }
        if notes==0{return Err(E::NoNotes);}
        // A hidden/non-body note cannot silently survive in retained metadata.
        let mut native_notes=0usize;
        for part in self.source().parts() {
            if let Some(xml)=part.xml(){native_notes=native_notes.checked_add(xml.elements().iter().filter(|n|xml::named(n,"footNote")||xml::named(n,"endNote")).count()).ok_or(E::Limit)?;}
        }
        if native_notes!=self.notes().len(){return Err(E::Coverage);}
        let(mut sections,mut omitted,mut visits,mut size,mut elements)=(Vec::new(),BTreeSet::new(),0usize,0usize,0usize);
        for path in self.source().spine() {
            let part=self.source().parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;
            let doc=part.xml().ok_or(E::Source)?;let root=&doc.elements()[doc.root_element()];
            if root.name().namespace()!=Some(super::SECTION_NS)||root.name().local_name()!="sec"{continue;}
            elements=elements.checked_add(doc.elements().len()).filter(|n|*n<=limits.config().elements).ok_or(E::Limit)?;
            if doc.original_len()>limits.config().section_bytes{return Err(E::Limit);}
            let Some(items)=wanted.get(path)else{omitted.insert(path.clone());continue};
            let guards=observed_protection(doc).map_err(|_|E::Protection)?;
            let subtree=subtree_protection(doc).map_err(|_|E::Protection)?;
            visits=visits.checked_add(doc.elements().len().checked_mul(4).ok_or(E::Limit)?).ok_or(E::Limit)?;
            let section_run=xml::section_properties_run(doc,limits.config().section_bytes)?;
            let mut content=Vec::new();let mut count=0usize;
            for &(marker,body) in items {
                if guards.get(marker).copied().ok_or(E::Source)?||subtree.get(marker).copied().ok_or(E::Source)?{return Err(E::Protection);}
                let node=&doc.elements()[body];let span=node.content_span().ok_or(E::Shape)?;
                if span.len()>limits.config().payload_bytes{return Err(E::Limit);}
                let mut at=span.start();let mut child=node.first_child();
                while let Some(i)=child {
                    let next=&doc.elements()[i];let outer=next.outer_span().ok_or(E::Shape)?;
                    doc.with_source_bytes(|src|xml::append(&mut content,src.get(at..outer.start()).ok_or(E::Source)?,limits.config().section_bytes))?;
                    let mut bytes=xml::close(doc,i,limits.config().payload_bytes)?;
                    if count==0 {if let Some(run)=&section_run {
                        if !xml::named(next,"p"){return Err(E::Shape);}
                        bytes=xml::prepend_child(&bytes,run,limits.config().payload_bytes)?;
                    }}
                    xml::append(&mut content,&bytes,limits.config().section_bytes)?;
                    count=count.checked_add(1).filter(|n|*n<=limits.config().paragraphs).ok_or(E::Limit)?;
                    at=outer.end();child=next.next_sibling();
                }
                doc.with_source_bytes(|src|xml::append(&mut content,src.get(at..span.end()).ok_or(E::Source)?,limits.config().section_bytes))?;
            }
            if count==0{return Err(E::Shape);}
            let span=root.content_span().ok_or(E::Shape)?;
            let bytes=doc.with_source_bytes(|src|xml::replace(src,span.start(),span.end(),&content,limits.config().section_bytes))?;
            size=size.checked_add(bytes.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            sections.push(Section {path:path.clone(),bytes,elements:count});
        }
        if sections.is_empty(){return Err(E::Coverage);}
        Ok(Collection {sections,omitted,notes,body_sha:note_sha.finalize().into(),visits})
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Uses this operation's original whole Form proof, never retained authority.
    /// # Errors
    /// Rejects a foreign proof/original, fresh-byte drift and compiler failures.
    pub fn export_note_file_candidate(&self,original:&ImportedDocumentForms,fresh:&[u8],selection:NoteFileSelection,
        limits:NoteHwpxLimits,writer:WriterLimits)->Result<NoteFileExportCandidate,E> {
        original.body_structure().export_note_file_checked(fresh,selection,limits,writer,||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })
    }
}
