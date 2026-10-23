//! Exactly the moved destination slots already verified against the original permutation output.
//! Immutable compiler metadata, not independent XML edits or source/service/execution authority.
use super::*;
pub(super) mod groups;
pub const PARAGRAPH_SORT_SPLICE_PROFILE:&str="hwpx-agent.source-paragraph-sort-splices/v1";
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortSplice {
    source_anchor:SourceAnchorHandle,source_start:usize,source_end:usize,replacement_sha256:[u8;32],replacement_bytes:usize,
}
impl fmt::Debug for SourceParagraphSortSplice {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortSplice(<redacted>)")}}
impl SourceParagraphSortSplice {
    #[must_use] pub const fn source_anchor(&self)->&SourceAnchorHandle {&self.source_anchor}
    #[must_use] pub const fn source_start(&self)->usize {self.source_start}
    #[must_use] pub const fn source_end(&self)->usize {self.source_end}
    #[must_use] pub const fn replacement_sha256(&self)->[u8;32] {self.replacement_sha256}
    #[must_use] pub const fn replacement_bytes(&self)->usize {self.replacement_bytes}
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortSpliceInventory {
    profile:&'static str,source_package_sha256:[u8;32],output_package_sha256:[u8;32],legacy_receipt_sha256:[u8;32],
    splices:Vec<SourceParagraphSortSplice>,#[serde(skip)]canonical_sha256:[u8;32],
}
impl fmt::Debug for SourceParagraphSortSpliceInventory {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortSpliceInventory(<redacted>; not_authority)")}}
impl SourceParagraphSortSpliceInventory {
    #[must_use] pub const fn profile(&self)->&'static str {self.profile}
    #[must_use] pub const fn source_package_sha256(&self)->[u8;32] {self.source_package_sha256}
    #[must_use] pub const fn output_package_sha256(&self)->[u8;32] {self.output_package_sha256}
    #[must_use] pub const fn legacy_receipt_sha256(&self)->[u8;32] {self.legacy_receipt_sha256}
    #[must_use] pub fn splices(&self)->&[SourceParagraphSortSplice] {&self.splices}
    #[must_use] pub const fn canonical_sha256(&self)->[u8;32] {self.canonical_sha256}
}
pub(super) fn build(receipt:&SourceParagraphSortReceipt,spans:&[(usize,usize)],maximum:usize)->Result<SourceParagraphSortSpliceInventory,E> {
    let n=receipt.entries.len();if n<2||n>PatchLimits::default().config().max_intents||n!=spans.len()||n!=receipt.source_order.len(){return Err(E::Selection);}
    let mut seen=Vec::new();seen.try_reserve_exact(n).map_err(|_|E::Limit)?;seen.resize(n,false);
    for &i in &receipt.source_order {let slot=seen.get_mut(i).ok_or(E::Selection)?;if std::mem::replace(slot,true){return Err(E::Selection);}}
    let mut splices=Vec::new();splices.try_reserve_exact(receipt.moved_paragraphs).map_err(|_|E::Limit)?;
    let(mut previous,mut copied)=(0usize,0usize);
    for(destination,&source)in receipt.source_order.iter().enumerate(){let(start,end)=spans[destination];
        if start<previous||start>=end||end-start!=receipt.entries[destination].subtree_bytes{return Err(E::Selection);}previous=end;
        if destination==source{continue;}let moved=&receipt.entries[source];
        copied=copied.checked_add(moved.subtree_bytes).filter(|n|*n<=PatchLimits::default().config().max_fragment_bytes).ok_or(E::Limit)?;
        splices.push(SourceParagraphSortSplice {source_anchor:receipt.entries[destination].paragraph_anchor.clone(),source_start:start,source_end:end,
            replacement_sha256:moved.subtree_sha256,replacement_bytes:moved.subtree_bytes});
    }
    if splices.is_empty()||splices.len()!=receipt.moved_paragraphs{return Err(E::Selection);}
    let mut inventory=SourceParagraphSortSpliceInventory {profile:PARAGRAPH_SORT_SPLICE_PROFILE,source_package_sha256:receipt.source_package_sha256,
        output_package_sha256:receipt.output_package_sha256,legacy_receipt_sha256:hash(receipt,maximum)?,splices,canonical_sha256:[0;32]};
    inventory.canonical_sha256=hash(&inventory,8*1024*1024)?;Ok(inventory)
}
pub(super) fn hash(value:&impl Serialize,maximum:usize)->Result<[u8;32],E> {
    struct Hash{state:Sha256,length:usize,maximum:usize}
    impl std::io::Write for Hash {
        fn write(&mut self,bytes:&[u8])->std::io::Result<usize>{self.length=self.length.checked_add(bytes.len()).filter(|n|*n<=self.maximum)
            .ok_or_else(||std::io::Error::other("sort_splice_inventory_limit"))?;self.state.update(bytes);Ok(bytes.len())}
        fn flush(&mut self)->std::io::Result<()>{Ok(())}
    }
    let mut out=Hash{state:Sha256::new(),length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|E::Limit)?;Ok(out.state.finalize().into())
}
