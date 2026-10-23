//! Current source access around one retained multi-parent sort, never a revision transaction.
use super::*;
compiler_source!(PreparedStoredParagraphSortGroupsCandidate);
use super::product::LiteralSource;
use std::collections::BTreeSet;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::sort::{SourceParagraphSortSpec,groups::{SourceParagraphSortGroupsCandidate,SourceParagraphSortGroupsReceipt,SOURCE_PARAGRAPH_SORT_GROUPS_PROFILE}}};
pub use super::sort::StoredParagraphSortError as StoredParagraphSortGroupsError;
pub const STORED_PARAGRAPH_SORT_GROUPS_PROFILE:&str="hwpx-agent.stored-paragraph-sort-groups-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredParagraphSortGroupsReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceParagraphSortGroupsReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredParagraphSortGroupsCandidate<'a> {source:LiteralSource<'a>,output:SourceParagraphSortGroupsCandidate,receipt:StoredParagraphSortGroupsReceipt}
impl fmt::Debug for PreparedStoredParagraphSortGroupsCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredParagraphSortGroupsCandidate(<redacted>; current_access_not_transaction)")}}
type C=StoredParagraphSortGroupsError;

pub(crate) fn sort_groups_receipt_matches(r:&SourceParagraphSortGroupsReceipt,source:[u8;32])->bool {
    if r.profile!=SOURCE_PARAGRAPH_SORT_GROUPS_PROFILE||r.source_package_sha256!=source||r.scope.index_sha256!=r.source_index_sha256
        ||r.groups.is_empty()||r.groups.len()>4096||r.spec.max_comparison_bytes==0||r.spec.max_comparison_bytes>32*1024*1024
        ||r.output_bytes==0||r.output_package_sha256==source||!r.whole_paragraph_scope_verified||!r.exact_subtrees_and_positional_gaps_read_back
        ||!r.stable_equal_keys||r.scope.whole_document_visibility_native_flow_or_revision_authority||r.locale_native_full_protection_or_execution_authority{return false;}
    let(mut total,mut moved,mut work,mut changed)=(0usize,0usize,0usize,0usize);
    let mut previous=None;let mut parts=BTreeSet::new();let mut anchors=BTreeSet::new();
    for group in &r.groups {
        let n=group.entries.len();if n==0||n>4096||group.source_order.len()!=n{return false;}
        let key=(group.part.as_str(),group.parent_element);if previous.is_some_and(|p|p>=key){return false;}previous=Some(key);
        let Some(next)=total.checked_add(n).filter(|v|*v<=4096)else{return false;};total=next;
        let order:BTreeSet<_>=group.source_order.iter().copied().collect();
        if order.len()!=n||!order.iter().copied().eq(0..n)||group.entries.iter().any(|e|e.subtree_bytes==0||!anchors.insert(&e.paragraph_anchor.opaque_handle)){return false;}
        let actual=group.source_order.iter().enumerate().filter(|(i,j)|*i!=**j).count();
        if group.moved_paragraphs!=actual||(n==1&&group.comparison_bytes!=0)||(n>1&&group.comparison_bytes==0){return false;}
        let Some(next)=work.checked_add(group.comparison_bytes).filter(|v|*v<=r.spec.max_comparison_bytes)else{return false;};work=next;
        let Some(next)=moved.checked_add(actual)else{return false;};moved=next;
        if actual>0 {changed+=1;parts.insert(group.part.as_str());}
    }
    total>=2&&moved>0&&work>0&&r.selected_paragraphs==total&&r.moved_paragraphs==moved&&r.comparison_bytes==work
        &&r.changed_groups==changed&&r.changed_parts==parts.len()
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current document.write and complete original proof, then one actual multi-group source sort.
    pub fn prepare_paragraph_sort_groups_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortGroupsCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_selector_paragraph_sort_groups_candidate(&self.imported,selector,body,spec,limits,writer)?;
        if !sort_groups_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredParagraphSortGroupsReceipt{source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_PARAGRAPH_SORT_GROUPS_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredParagraphSortGroupsCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Transfers the same original owner; no clone or repeated source sort.
    pub fn into_paragraph_sort_groups_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortGroupsCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_paragraph_sort_groups_candidate(provider,selector,body,spec,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredParagraphSortGroupsCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredParagraphSortGroupsCandidate<'_> {
    pub(crate) fn compiler_sort_splices(&self)->&hwpx_package::document_import::search::replacement::atoms::sort::intents::SourceParagraphSortSpliceInventory{self.output.splice_inventory()}
    #[must_use] pub const fn receipt(&self)->&StoredParagraphSortGroupsReceipt{&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_PARAGRAPH_SORT_GROUPS_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!sort_groups_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without sorting or importing the source again.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredParagraphSortGroupsReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Last current head is checked inside writer verification, before any consumer callback.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Candidate preparation does not grant execution, commit, durable idempotency or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
