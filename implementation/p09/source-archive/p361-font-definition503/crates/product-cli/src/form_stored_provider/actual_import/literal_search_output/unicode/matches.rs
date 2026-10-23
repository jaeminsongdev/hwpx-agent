//! Current sealed source -> retained exact-match normalization candidate, not a key claim or CAS.
use super::*;
compiler_source!(PreparedStoredUnicodeMatchCandidate);
use hwpx_package::document_import::search::{reviews::selector::styles::SourceReviewStyleFilter,
    replacement::atoms::unicode::matches::{SourceUnicodeMatchCandidate,SourceUnicodeMatchReceipt,SourceUnicodeMatchSearch,
        SOURCE_UNICODE_MATCH_PROFILE,SOURCE_UNICODE_MATCH_OUTPUT_PROFILE}};
pub const STORED_UNICODE_MATCH_PROFILE:&str="hwpx-agent.stored-unicode-normalization-candidate/v2";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredUnicodeMatchReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceUnicodeMatchReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredUnicodeMatchCandidate<'a> {source:LiteralSource<'a>,output:SourceUnicodeMatchCandidate,receipt:StoredUnicodeMatchReceipt}
impl fmt::Debug for PreparedStoredUnicodeMatchCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredUnicodeMatchCandidate(<redacted>; current_access_not_full_transaction)")}}
#[derive(Debug,Error)]
pub enum StoredUnicodeMatchError {
    #[error("STORED_UNICODE_MATCH_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_UNICODE_MATCH_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_UNICODE_MATCH_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_UNICODE_MATCH_BINDING_REJECTED")] Binding,
    #[error("STORED_UNICODE_MATCH_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_UNICODE_MATCH_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type M=StoredUnicodeMatchError;
pub(crate) fn match_receipt_matches(r:&SourceUnicodeMatchReceipt,source:[u8;32])->bool {
    let out=&r.output;let search=r.search.search();let result=search.result();
    r.profile==SOURCE_UNICODE_MATCH_PROFILE&&out.profile==SOURCE_UNICODE_MATCH_OUTPUT_PROFILE&&out.source_package_sha256==source
        &&result.index_receipt().source_package_sha256==source&&result.index_receipt().index_sha256==out.source_index_sha256
        &&search.scope_receipt()==&out.selector&&out.selector.index_sha256==out.source_index_sha256&&r.request_sha256==out.request_sha256
        &&search.match_regions().len()==result.matches().len()&&!result.matches().is_empty()
        &&result.matches().iter().all(|m|!m.zero_width&&m.source_scalar_selection_exact)
        &&matches!((r.filter,&r.search),(None,SourceUnicodeMatchSearch::Text(_))|(Some(_),SourceUnicodeMatchSearch::Style(_)))
        &&out.source_review_import.source_package_sha256==source&&out.output_review_import.source_package_sha256==out.output_package_sha256
        &&out.selected_original_scalars>0&&out.normalized_text_groups>0&&out.decomposed_scalars>0&&out.changed_components>0
        &&out.changed_scalar_ranges>0&&!out.changes.is_empty()&&out.changed_parts>0&&out.output_bytes>0
        &&out.changes.iter().try_fold(0usize,|n,c|n.checked_add(c.changed_scalar_ranges))==Some(out.changed_scalar_ranges)
        &&out.exact_original_selection_verified&&out.unchanged_components_keep_original_placement&&out.original_controls_and_all_reference_shells_preserved
        &&out.independent_normalization_oracle_verified&&out.output_text_spans_and_outside_slots_verified
        &&!out.selector.whole_document_visibility_native_flow_or_revision_authority&&!out.full_contract_native_service_or_execution_authority
        &&!r.full_contract_native_service_or_execution_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current write/source reconstruction and one original matcher/normalization compiler.
    pub fn prepare_unicode_match_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeMatchCandidate<'_>,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_unicode_matches(&self.imported,query,selector,policy,filter,form,run,limits,writer)?;
        if !match_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(M::Binding);}
        let receipt=StoredUnicodeMatchReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_UNICODE_MATCH_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredUnicodeMatchCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing original owner without clone/reimport or another matcher pass.
    pub fn into_unicode_match_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeMatchCandidate<'static>,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_unicode_match_candidate(provider,query,selector,policy,filter,form,run,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredUnicodeMatchCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredUnicodeMatchCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredUnicodeMatchReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_UNICODE_MATCH_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!match_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(M::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head, without rerunning the retained query or normalization.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredUnicodeMatchReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|M::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final current head remains inside writer-integrity verification, before the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|M::Integrity)?
    }
    /// # Errors
    /// Candidate integrity is not a dispatcher, durable key claim, revision CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
