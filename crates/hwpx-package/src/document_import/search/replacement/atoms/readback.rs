use super::*;
use crate::document_import::ImportedSourcePackage;

pub(super) fn empty_shell(xml:&PreservingXmlDocument,index:usize)->Result<Range<usize>,E> {
    let n=xml.elements().get(index).ok_or(E::Readback)?;let tag=n.start_tag_span();
    // Only '/>' may expand. The original qualified name, attributes and whitespace stay exact.
    if !n.is_empty()||tag.len()<2{return Err(E::Readback);}
    Ok(tag.end()-2..tag.end())
}
fn expanded_empty_slot(old:&PreservingXmlDocument,new:&PreservingXmlDocument,index:usize)->Result<Vec<Range<usize>>,E> {
    let(a,b)=(&old.elements()[index],&new.elements()[index]);
    let shell=empty_shell(old,index)?;let end=b.end_token().ok_or(E::Readback)?;let close=new.tokens()[end].span();
    let exact=old.with_source_bytes(|x|new.with_source_bytes(|y| {
        let name=a.start_name_span();let mut expected=Vec::from(b"</".as_slice());expected.extend_from_slice(&x[name.start()..name.end()]);expected.push(b'>');
        x.get(a.start_tag_span().start()..shell.start)==y.get(b.start_tag_span().start()..b.start_tag_span().end()-1)
            &&y.get(b.start_tag_span().end()-1)==Some(&b'>')&&y.get(close.start()..close.end())==Some(expected.as_slice())
    }));
    if !exact{return Err(E::Preservation);}Ok(vec![b.start_tag_span().end()-1..close.end()])
}

/// A slot lies between whole original controls, not inside a control's whitespace or attributes.
pub(super) fn slots(xml:&PreservingXmlDocument,index:usize)->Result<Vec<Range<usize>>,E> {
    let node=xml.elements().get(index).ok_or(E::Readback)?;let content=node.content_span().ok_or(E::Readback)?;
    let mut result=Vec::new();let mut before=content.start();let mut child=node.first_child();
    while let Some(i)=child {
        let control=&xml.elements()[i];let range=control.outer_span().ok_or(E::Readback)?;
        if range.start()<before||range.end()>content.end(){return Err(E::Readback);}
        result.push(before..range.start());before=range.end();child=control.next_sibling();
    }result.push(before..content.end());Ok(result)
}

pub(super) fn build(source:&ImportedSourcePackage,fresh:&[u8],intents:&[PatchIntent],plans:&BTreeMap<&PackagePath,Vec<PlannedSpan>>,writer:WriterLimits,
    review:Option<&review::ReviewWriteContext>)->Result<(PackageArtifact,Option<review::ReviewBodyImportReceipt>),E> {
    let artifact=super::super::output::build_artifact(source,fresh,intents,plans,writer)?;
    let output_review=verify_artifact(source,&artifact,plans,review)?;Ok((artifact,output_review))
}

/// The same complete value/outside-slot verifier for an explicitly selected preserving writer profile.
pub(super) fn verify_artifact(source:&ImportedSourcePackage,artifact:&PackageArtifact,plans:&BTreeMap<&PackagePath,Vec<PlannedSpan>>,
    review:Option<&review::ReviewWriteContext>)->Result<Option<review::ReviewBodyImportReceipt>,E> {
    artifact.with_verified_bytes(|bytes|->Result<Option<review::ReviewBodyImportReceipt>,E>{
        let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
        let output_review=if let Some(review)=review {
            let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
            Some(review.readback(&rebuilt,&fields)?)
        }else{let _=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;None};
        for (path,leaves) in plans {
            let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            if old.elements().len()!=new.elements().len(){return Err(E::Readback);}
            let mut ordered:Vec<_>=leaves.iter().collect();ordered.sort_by_key(|p|p.element);let(mut before,mut after)=(0,0);
            for plan in ordered {
                let value=crate::text_flow::read_source_text_span(new,plan.element).map_err(|_|E::Readback)?;
                if value!=plan.expected||span_sha(&value)!=plan.change.output_span_sha256||text_bytes(&value)?!=plan.change.output_text_bytes{return Err(E::Readback);}
                let new_slots=if plan.expanded_empty{expanded_empty_slot(old,new,plan.element)?}else{slots(new,plan.element)?};
                if plan.old_slots.len()!=new_slots.len(){return Err(E::Readback);}
                // Slot numbers stay stable even when deleting Text atoms shifts parsed atom ordinals.
                for &slot in &plan.changed_slots {
                    let a=plan.old_slots.get(slot).ok_or(E::Readback)?;let b=new_slots.get(slot).ok_or(E::Readback)?;
                    if !old.with_source_bytes(|old|new.with_source_bytes(|new|old.get(before..a.start)==new.get(after..b.start))){return Err(E::Preservation);}
                    before=a.end;after=b.end;
                }
            }
            if !old.with_source_bytes(|old|new.with_source_bytes(|new|old.get(before..)==new.get(after..))){return Err(E::Preservation);}
        }Ok(output_review)
    }).map_err(|_|E::Writer)?
}
