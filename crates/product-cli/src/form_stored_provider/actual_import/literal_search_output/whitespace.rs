//! Current sealed source and retained whitespace/control output; not commit or execution authority.
use super::*;
compiler_source!(PreparedStoredWhitespaceCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::{SourceReviewTextPolicy,
    selector::styles::SourceReviewStyleFilter},replacement::atoms::whitespace::{SourceWhitespaceNormalizationCandidate,SourceWhitespaceNormalizationReceipt,
    SourceWhitespacePolicy,SourceWhitespaceMatchSearch,SOURCE_WHITESPACE_NORMALIZATION_PROFILE}};
pub const STORED_WHITESPACE_PROFILE:&str="hwpx-agent.stored-whitespace-normalization-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredWhitespaceReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceWhitespaceNormalizationReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredWhitespaceCandidate<'a>{source:LiteralSource<'a>,output:SourceWhitespaceNormalizationCandidate,receipt:StoredWhitespaceReceipt}
impl fmt::Debug for PreparedStoredWhitespaceCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredWhitespaceCandidate(<redacted>; current_access_not_full_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredWhitespaceError {
    #[error("STORED_WHITESPACE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_WHITESPACE_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_WHITESPACE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_WHITESPACE_BINDING_REJECTED")] Binding,
    #[error("STORED_WHITESPACE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_WHITESPACE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=StoredWhitespaceError;
pub(crate) fn whitespace_receipt_matches(r:&SourceWhitespaceNormalizationReceipt,source:[u8;32])->bool{
    let search=r.search.search();let result=search.result();
    r.profile==SOURCE_WHITESPACE_NORMALIZATION_PROFILE&&r.source_package_sha256==source&&r.policy.validate().is_ok()
        &&r.run_policy==SourceReplacementRunPolicy::FirstOriginalRunRetainAllRuns
        &&result.index_receipt().source_package_sha256==source&&result.index_receipt().index_sha256==r.source_index_sha256
        &&search.scope_receipt()==&r.selector&&r.selector.index_sha256==r.source_index_sha256
        &&search.match_regions().len()==result.matches().len()&&!result.matches().is_empty()
        &&result.matches().iter().all(|m|!m.zero_width&&m.source_scalar_selection_exact)
        &&matches!((&r.filter,&r.search),(None,SourceWhitespaceMatchSearch::Text(_))|(Some(_),SourceWhitespaceMatchSearch::Style(_)))
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.selected_original_scalars>0&&r.whitespace_sequences>0&&r.changed_scalar_ranges>0&&!r.changes.is_empty()&&r.changed_parts>0&&r.output_bytes>0
        &&r.changes.iter().try_fold(0usize,|n,c|n.checked_add(c.changed_scalar_ranges))==Some(r.changed_scalar_ranges)
        &&r.exact_original_selection_verified&&r.original_run_shells_styles_references_and_non_whitespace_preserved
        &&r.output_uses_first_original_contributor&&r.output_spans_and_exact_outside_edits_verified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.full_contract_native_service_or_execution_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current write/source reconstruction and one original matcher/whitespace compiler.
    pub fn prepare_whitespace_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,policy:SourceWhitespacePolicy,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredWhitespaceCandidate<'_>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}policy.validate()?;
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_whitespace_candidate(&self.imported,query,selector,body,filter,policy,run,limits,writer)?;
        if !whitespace_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(C::Binding);}
        let receipt=StoredWhitespaceReceipt{source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_WHITESPACE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredWhitespaceCandidate{source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing imported owner without clone/reimport or another matcher pass.
    pub fn into_whitespace_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,policy:SourceWhitespacePolicy,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredWhitespaceCandidate<'static>,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt)={let prepared=self.prepare_whitespace_candidate(provider,query,selector,body,filter,policy,run,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredWhitespaceCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredWhitespaceCandidate<'_>{
    #[must_use] pub const fn receipt(&self)->&StoredWhitespaceReceipt{&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(C::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_WHITESPACE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!whitespace_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head; no second query or normalization.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredWhitespaceReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|C::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Keep the current final head inside writer verification before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|C::Integrity)?
    }
    /// # Errors
    /// Candidate integrity is not a dispatcher, durable key claim, revision CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
