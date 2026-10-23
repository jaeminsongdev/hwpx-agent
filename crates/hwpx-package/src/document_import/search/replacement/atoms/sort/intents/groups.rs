//! Metadata from all exact original slots, including identity groups; no XML or fragment copies.
use super::*;
type GroupReceipt=super::super::groups::SourceParagraphSortGroupsReceipt;
const PROFILE:&str="hwpx-agent.source-paragraph-sort-group-splices/v1";
pub(in crate::document_import::search::replacement::atoms::sort) fn prepare<'a>(
    slots:impl Iterator<Item=(&'a PackagePath,&'a SourceParagraphSortEntry,&'a SourceParagraphSortEntry,usize,usize)>,
    selected:usize,moved:usize)->Result<Vec<SourceParagraphSortSplice>,E>{
    if selected<2||selected>PatchLimits::default().config().max_intents||moved==0||moved>selected{return Err(E::Selection);}
    let mut splices=Vec::new();splices.try_reserve_exact(moved).map_err(|_|E::Limit)?;
    let(mut count,mut copied)=(0usize,0usize);let mut previous=None;let mut anchors=BTreeSet::new();
    for(path,destination,source,start,end)in slots {
        count=count.checked_add(1).filter(|n|*n<=selected).ok_or(E::Limit)?;
        if start>=end||end-start!=destination.subtree_bytes||!anchors.insert(&destination.paragraph_anchor.opaque_handle){return Err(E::Selection);}
        if previous.is_some_and(|(p,stop)|path<p||(path==p&&start<stop)){return Err(E::Selection);}previous=Some((path,end));
        if destination.paragraph_anchor==source.paragraph_anchor{continue;}
        if source.subtree_bytes==0||splices.len()>=moved{return Err(E::Selection);}
        copied=copied.checked_add(source.subtree_bytes).filter(|n|*n<=PatchLimits::default().config().max_fragment_bytes).ok_or(E::Limit)?;
        splices.push(SourceParagraphSortSplice{source_anchor:destination.paragraph_anchor.clone(),source_start:start,source_end:end,
            replacement_sha256:source.subtree_sha256,replacement_bytes:source.subtree_bytes});
    }
    if count!=selected||splices.len()!=moved{return Err(E::Selection);}Ok(splices)
}
pub(in crate::document_import::search::replacement::atoms::sort) fn bind(receipt:&GroupReceipt,splices:Vec<SourceParagraphSortSplice>,maximum:usize)->Result<SourceParagraphSortSpliceInventory,E>{
    if splices.is_empty()||splices.len()!=receipt.moved_paragraphs{return Err(E::Selection);}
    let mut inventory=SourceParagraphSortSpliceInventory{profile:PROFILE,source_package_sha256:receipt.source_package_sha256,
        output_package_sha256:receipt.output_package_sha256,legacy_receipt_sha256:hash(receipt,maximum)?,splices,canonical_sha256:[0;32]};
    inventory.canonical_sha256=hash(&inventory,8*1024*1024)?;Ok(inventory)
}
