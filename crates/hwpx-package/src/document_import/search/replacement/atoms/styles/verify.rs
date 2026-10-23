//! One output import and independent scalar/style readback, not a count-only run-split claim.
use super::*;
#[derive(Eq,PartialEq)]
pub(super) enum Scalar {Text(char),Tab(u32,u32,u32),LineBreak}
pub(super) struct PointValue {pub(super) scalar:Scalar,pub(super) run:Option<u32>,pub(super) text:Option<u32>}
pub(super) fn values(index:&SourceTextIndex<'_>)->Result<Vec<PointValue>,E> {
    let mut values=Vec::new();let source=index.original.source();
    for anchor in &index.segments {
        let resolved=source.resolve_anchor(anchor).map_err(|_|E::Readback)?;let xml=resolved.part().xml().ok_or(E::Readback)?;let i=resolved.element_index().ok_or(E::Readback)?;
        let text=render::reference(&xml.elements()[i],"charStyleIDRef")?;let run=render::reference(&xml.elements()[xml.elements()[i].parent().ok_or(E::Readback)?],"charPrIDRef")?;
        let span=crate::text_flow::read_source_text_span(xml,i).map_err(|_|E::Readback)?;
        for atom in span.atoms {match atom {
            TextAtom::Text(value)=>for ch in value.chars(){values.push(PointValue {scalar:Scalar::Text(ch),run,text});},
            TextAtom::Tab {width,leader,tab_type}=>values.push(PointValue {scalar:Scalar::Tab(width,leader,tab_type),run,text}),
            TextAtom::LineBreak=>values.push(PointValue {scalar:Scalar::LineBreak,run,text}),
        }}
    }if values.len()!=index.points.len(){return Err(E::Readback);}Ok(values)
}
pub(super) fn output(index:&SourceTextIndex<'_>,plan:&Plan,target:u32,artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<ReviewBodyImportReceipt,E> {
    artifact.with_verified_bytes(|bytes|->Result<ReviewBodyImportReceipt,E>{
        let source=index.original.source();let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(&rebuilt,&fields).map_err(|_|E::Readback)?;
        let output_review=context.readback_receipt(review.receipt())?;
        // Compare raw outside-edit gaps and the entire compiled replacement bytes. This also covers
        // ancestor control shells containing intentionally restyled nested review/note/table runs.
        for(path,edits)in &plan.edits {
            let old=source.parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let exact=old.with_source_bytes(|a|new.with_source_bytes(|b|->Result<(),E>{let(mut left,mut right)=(0usize,0usize);
                for(&start,edit)in edits {let edge=right.checked_add(start.checked_sub(left).ok_or(E::Readback)?).ok_or(E::Limit)?;
                    if a.get(left..start)!=b.get(right..edge){return Err(E::Preservation);}
                    let end=edge.checked_add(edit.bytes.len()).ok_or(E::Limit)?;if b.get(edge..end)!=Some(edit.bytes.as_slice()){return Err(E::Readback);}
                    left=edit.end;right=end;
                }if a.get(left..)!=b.get(right..){return Err(E::Preservation);}Ok(())
            }));exact?;
        }
        let after=SourceReviewScopeIndex::from_review(&rebuilt,&review,index.limits).map_err(|_|E::Readback)?;let after=after.source_index();
        if index.blocks.len()!=after.blocks.len()||index.blocks.iter().zip(&after.blocks).any(|(a,b)|a.text!=b.text){return Err(E::Readback);}
        let before=values(index)?;let after=values(after)?;if before.len()!=after.len(){return Err(E::Readback);}
        for(i,(before,after))in before.into_iter().zip(after).enumerate() {
            if before.scalar!=after.scalar||before.text!=after.text||after.run!=if plan.selected.contains(&i){Some(target)}else{before.run}{return Err(E::Readback);}
        }Ok(output_review)
    }).map_err(|_|E::Writer)?
}
