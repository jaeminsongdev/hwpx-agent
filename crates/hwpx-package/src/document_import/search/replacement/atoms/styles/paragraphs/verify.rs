//! Attribute-only exact bytes, all paragraph references and the original scalar/two-axis readback.
use super::*;
pub(super) fn output(index:&SourceTextIndex<'_>,plan:&Plan,target:SourceParagraphStyleTarget,artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<ReviewBodyImportReceipt,E> {
    artifact.with_verified_bytes(|bytes|->Result<ReviewBodyImportReceipt,E>{
        let source=index.original.source();let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(&rebuilt,&fields).map_err(|_|E::Readback)?;
        let receipt=context.readback_receipt(review.receipt())?;
        for(path,edits)in &plan.edits {
            let old=source.parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            old.with_source_bytes(|a|new.with_source_bytes(|b|->Result<(),E>{let(mut left,mut right)=(0usize,0usize);
                for edit in edits {let edge=right.checked_add(edit.start.checked_sub(left).ok_or(E::Readback)?).ok_or(E::Limit)?;
                    if a.get(left..edit.start)!=b.get(right..edge){return Err(E::Preservation);}
                    let end=edge.checked_add(edit.bytes.len()).ok_or(E::Limit)?;if b.get(edge..end)!=Some(edit.bytes.as_slice()){return Err(E::Readback);}
                    left=edit.end;right=end;
                }if a.get(left..)!=b.get(right..){return Err(E::Preservation);}Ok(())
            }))?;
            if old.elements().len()!=new.elements().len(){return Err(E::Readback);}
            for(i,(a,b))in old.elements().iter().zip(new.elements()).enumerate() {
                if a.name()!=b.name(){return Err(E::Readback);}if !paragraph(a){continue;}
                for name in["paraPrIDRef","styleIDRef"] {
                    let expected=if name==target.attribute()&&plan.paragraphs.get(path).is_some_and(|p|p.contains(&i)){Some(target.declaration_id())}else{super::super::render::reference(a,name)?};
                    if super::super::render::reference(b,name)?!=expected{return Err(E::Readback);}
                }
            }
        }
        let after=SourceReviewScopeIndex::from_review(&rebuilt,&review,index.limits).map_err(|_|E::Readback)?;let after=after.source_index();
        if index.blocks.len()!=after.blocks.len()||index.blocks.iter().zip(&after.blocks).any(|(a,b)|a.text!=b.text){return Err(E::Readback);}
        let before=super::super::verify::values(index)?;let after=super::super::verify::values(after)?;
        if before.len()!=after.len(){return Err(E::Readback);}
        for(a,b)in before.into_iter().zip(after){if a.scalar!=b.scalar||a.run!=b.run||a.text!=b.text{return Err(E::Readback);}}
        Ok(receipt)
    }).map_err(|_|E::Writer)?
}
