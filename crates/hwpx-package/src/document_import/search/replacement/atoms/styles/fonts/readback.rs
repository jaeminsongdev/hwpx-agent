//! Entire scalar/reference and typed catalog comparison plus exact compiled source gaps.
use super::*;
pub(super) fn verify(index:&SourceTextIndex<'_>,plan:&FontPlan,axis:SourceFontStyleAxis,artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<(),E>{
    artifact.with_verified_bytes(|bytes|->Result<(),E>{
        let source=index.original.source();let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(&forms,&fields).map_err(|_|E::Readback)?;context.readback_receipt(review.receipt())?;
        let meanings=ImportedDocumentFieldSemantics::import(&fields).map_err(|_|E::Readback)?;
        let catalog=ImportedDocumentCatalog::import(&meanings).map_err(|_|E::Readback)?;
        if catalog.character_catalog()!=&plan.characters{return Err(E::Readback);}
        let old_parts:BTreeMap<_,_>=source.parts().iter().map(|p|(p.path(),p)).collect();
        let new_parts:BTreeMap<_,_>=forms.source().parts().iter().map(|p|(p.path(),p)).collect();
        for(path,edits)in &plan.edits{
            let old=old_parts.get(path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=new_parts.get(path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            old.with_source_bytes(|a|new.with_source_bytes(|b|->Result<(),E>{let(mut left,mut right)=(0usize,0usize);
                for(&at,edit)in edits{let start=right.checked_add(at.checked_sub(left).ok_or(E::Preservation)?).ok_or(E::Limit)?;
                    if a.get(left..at)!=b.get(right..start){return Err(E::Preservation);}
                    let end=start.checked_add(edit.bytes.len()).ok_or(E::Limit)?;
                    if b.get(start..end)!=Some(edit.bytes.as_slice()){return Err(E::Readback);}left=edit.end;right=end;
                }if a.get(left..)!=b.get(right..){return Err(E::Preservation);}Ok(())
            }))?;
        }
        let after=SourceReviewScopeIndex::from_review(&forms,&review,index.limits).map_err(|_|E::Readback)?;let after=after.source_index();
        if index.blocks.len()!=after.blocks.len()||index.blocks.iter().zip(&after.blocks).any(|(a,b)|a.text!=b.text){return Err(E::Readback);}
        let values=super::super::verify::values(after)?;if values.len()!=plan.before.len(){return Err(E::Readback);}
        for(i,(old,new))in plan.before.iter().zip(values).enumerate(){
            let expected=plan.selected.get(&i).copied();
            if old.scalar!=new.scalar||new.run!=if axis==SourceFontStyleAxis::RunProperty{expected.or(old.run)}else{old.run}
                ||new.text!=if axis==SourceFontStyleAxis::TextStyle{expected.or(old.text)}else{old.text}{return Err(E::Readback);}
        }Ok(())
    }).map_err(|_|E::Writer)?
}
