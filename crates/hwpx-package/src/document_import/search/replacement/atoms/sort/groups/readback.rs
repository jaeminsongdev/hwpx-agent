//! One output admission, exact subtrees and positional gaps for all independent original groups.
use super::*;
pub(super) type Slots<'a>=BTreeMap<&'a PackagePath,Vec<(&'a Row,&'a Row)>>;
pub(super) fn slots<'a>(groups:&'a[PlannedGroup<'_>])->Result<Slots<'a>,E>{
    let mut parts:Slots<'a>=BTreeMap::new();
    for group in groups {
        if group.rows.len()!=group.order.len(){return Err(E::Selection);}
        let target=parts.entry(group.path).or_default();target.try_reserve(group.rows.len()).map_err(|_|E::Limit)?;
        for(destination,&source)in group.order.iter().enumerate(){target.push((&group.rows[destination],group.rows.get(source).ok_or(E::Selection)?));}
    }
    for rows in parts.values_mut(){rows.sort_unstable_by_key(|(row,_)|row.start);let mut previous=0;
        for &(row,_)in rows.iter(){if row.start<previous||row.start>=row.end{return Err(E::Selection);}previous=row.end;}}
    Ok(parts)
}
pub(super) fn output(source:&ImportedSourcePackage,parts:&Slots<'_>,artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<(),E>{
    artifact.with_verified_bytes(|bytes|->Result<(),E>{
        let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;context.readback(&forms,&fields)?;
        for(path,rows)in parts {
            let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=forms.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            old.with_source_bytes(|raw|new.with_source_bytes(|out|->Result<(),E>{
                let(mut before,mut after)=(0usize,0usize);
                for &(destination,moved)in rows {
                    let gap=destination.start.checked_sub(before).ok_or(E::Readback)?;
                    let next=after.checked_add(gap).ok_or(E::Limit)?;
                    if raw.get(before..destination.start).ok_or(E::Readback)?!=out.get(after..next).ok_or(E::Readback)?{return Err(E::Preservation);}
                    let stop=next.checked_add(moved.end-moved.start).ok_or(E::Limit)?;
                    if raw.get(moved.start..moved.end).ok_or(E::Readback)?!=out.get(next..stop).ok_or(E::Readback)?{return Err(E::Readback);}
                    before=destination.end;after=stop;
                }
                if raw.get(before..).ok_or(E::Readback)?!=out.get(after..).ok_or(E::Readback)?{return Err(E::Preservation);}Ok(())
            }))?;
        }Ok(())
    }).map_err(|_|E::Writer)??;Ok(())
}
