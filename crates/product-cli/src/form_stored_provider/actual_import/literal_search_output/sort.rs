//! Actual original paragraph sort with fresh current access; no retained receipt is an authorization grant.
use super::*;
compiler_source!(PreparedStoredParagraphSortCandidate);
use super::product::LiteralSource;
use std::collections::BTreeSet;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::sort::{SourceParagraphSortSpec,SourceParagraphSortCandidate,SourceParagraphSortReceipt,SourceParagraphSortError,SOURCE_PARAGRAPH_SORT_PROFILE}};
pub const STORED_PARAGRAPH_SORT_PROFILE:&str="hwpx-agent.stored-paragraph-sort-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredParagraphSortReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceParagraphSortReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredParagraphSortCandidate<'a> {source:LiteralSource<'a>,output:SourceParagraphSortCandidate,receipt:StoredParagraphSortReceipt}
impl fmt::Debug for PreparedStoredParagraphSortCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredParagraphSortCandidate(<redacted>; single_sibling_group_current_access_not_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredParagraphSortError {
    #[error("STORED_PARAGRAPH_SORT_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_PARAGRAPH_SORT_OUTPUT_REJECTED")] Output(#[from] SourceParagraphSortError),
    #[error("STORED_PARAGRAPH_SORT_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_PARAGRAPH_SORT_BINDING_REJECTED")] Binding,
    #[error("STORED_PARAGRAPH_SORT_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_PARAGRAPH_SORT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredParagraphSortError;
pub(crate) fn sort_receipt_matches(r:&SourceParagraphSortReceipt,source:[u8;32])->bool {
    let n=r.entries.len();let order:BTreeSet<_>=r.source_order.iter().copied().collect();
    r.profile==SOURCE_PARAGRAPH_SORT_PROFILE&&r.source_package_sha256==source&&r.scope.index_sha256==r.source_index_sha256
        &&n>=2&&n<=4096&&r.source_order.len()==n&&order.len()==n&&order.iter().copied().eq(0..n)
        &&r.moved_paragraphs==r.source_order.iter().enumerate().filter(|(i,j)|*i!=**j).count()&&r.moved_paragraphs>0
        &&r.spec.max_comparison_bytes>0&&r.spec.max_comparison_bytes<=32*1024*1024&&r.comparison_bytes>0&&r.comparison_bytes<=r.spec.max_comparison_bytes
        &&r.entries.iter().all(|e|e.subtree_bytes>0)&&r.output_bytes>0&&r.output_package_sha256!=source
        &&r.whole_paragraph_scope_verified&&r.exact_subtrees_and_positional_gaps_read_back&&r.stable_equal_keys
        &&!r.scope.whole_document_visibility_native_flow_or_revision_authority&&!r.locale_native_full_protection_or_execution_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current document.write/source reconstruction and the actual original sort compiler.
    pub fn prepare_paragraph_sort_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_selector_paragraph_sort_candidate(&self.imported,selector,body,spec,limits,writer)?;
        if !sort_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredParagraphSortReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_PARAGRAPH_SORT_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredParagraphSortCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Moves the same original owner; no clone, second source import, or repeated sort.
    pub fn into_paragraph_sort_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_paragraph_sort_candidate(provider,selector,body,spec,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredParagraphSortCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredParagraphSortCandidate<'_> {
    pub(crate) fn compiler_sort_splices(&self)->&hwpx_package::document_import::search::replacement::atoms::sort::intents::SourceParagraphSortSpliceInventory {self.output.splice_inventory()}
    #[must_use] pub const fn receipt(&self)->&StoredParagraphSortReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_PARAGRAPH_SORT_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!sort_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head; never reruns the retained sort.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredParagraphSortReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Checks the last current head inside writer verification, before invoking the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// No execution dispatcher, durable key claim, CAS, Native or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
