use super::*;
use crate::document_import::ImportedSourcePackage;
pub(in crate::document_import::search::replacement::atoms) fn verify(source:&ImportedSourcePackage,artifact:&PackageArtifact,plans:&BTreeMap<&PackagePath,Vec<plan::Span>>,
    context:&review::ReviewWriteContext)->Result<review::ReviewBodyImportReceipt,E>{
    artifact.with_verified_bytes(|bytes|->Result<review::ReviewBodyImportReceipt,E>{
        let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
        let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
        let receipt=context.readback(&rebuilt,&fields)?;
        for(path,spans)in plans{
            let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let mut edits:Vec<_>=spans.iter().flat_map(|p|p.lexical.iter()).collect();edits.sort_by_key(|e|e.old.start);
            old.with_source_bytes(|a|new.with_source_bytes(|b|lexical::verify(a,b,&edits))).map_err(|_|E::Preservation)?;
            // Typed controls cannot create/remove a text container; use stable text-container order,
            // never a shifted all-element index or a stale output source anchor.
            let text_nodes=|xml:&PreservingXmlDocument|xml.elements().iter().enumerate().filter_map(|(i,n)|
                (n.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&n.name().local_name()=="t").then_some(i)).collect::<Vec<_>>();
            let old_text=text_nodes(old);let new_text=text_nodes(new);if old_text.len()!=new_text.len(){return Err(E::Readback);}
            for span in spans{
                let ordinal=old_text.binary_search(&span.element).map_err(|_|E::Readback)?;
                let value=crate::text_flow::read_source_text_span(new,new_text[ordinal]).map_err(|_|E::Readback)?;
                if value!=span.expected||span_sha(&value)!=span_sha(&span.expected)||text_bytes(&value)?!=text_bytes(&span.expected)?{return Err(E::Readback);}
            }
        }Ok(receipt)
    }).map_err(|_|E::Writer)?
}

