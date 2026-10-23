//! Current sealed source -> explicit selected-scope Unicode candidate, not a commit or key claim.
pub mod matches;
use super::*;
compiler_source!(PreparedStoredUnicodeCandidate);
use super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::unicode::{SourceUnicodeNormalizationCandidate,SourceUnicodeNormalizationReceipt,SourceUnicodeNormalizationForm,
        SOURCE_UNICODE_NORMALIZATION_PROFILE}};
pub const STORED_UNICODE_PROFILE:&str="hwpx-agent.stored-unicode-normalization-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredUnicodeReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceUnicodeNormalizationReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredUnicodeCandidate<'a> {source:LiteralSource<'a>,output:SourceUnicodeNormalizationCandidate,receipt:StoredUnicodeReceipt}
impl fmt::Debug for PreparedStoredUnicodeCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredUnicodeCandidate(<redacted>; scope_candidate_not_execution_authority)")}}
#[derive(Debug,Error)]
pub enum StoredUnicodeError {
    #[error("STORED_UNICODE_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_UNICODE_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_UNICODE_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_UNICODE_BINDING_REJECTED")] Binding,
    #[error("STORED_UNICODE_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_UNICODE_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=StoredUnicodeError;
pub(crate) fn source_receipt_matches(r:&SourceUnicodeNormalizationReceipt,source:[u8;32])->bool {
    r.profile==SOURCE_UNICODE_NORMALIZATION_PROFILE&&r.source_package_sha256==source&&r.source_index_sha256==r.selector.index_sha256
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.selected_original_scalars>0&&r.normalized_text_groups>0&&r.decomposed_scalars>0&&r.changed_components>0
        &&r.changed_scalar_ranges>0&&!r.changes.is_empty()&&r.changed_parts>0&&r.output_bytes>0
        &&r.changes.iter().try_fold(0usize,|n,c|n.checked_add(c.changed_scalar_ranges))==Some(r.changed_scalar_ranges)
        &&r.exact_original_selection_verified&&r.unchanged_components_keep_original_placement&&r.original_controls_and_all_reference_shells_preserved
        &&r.independent_normalization_oracle_verified&&r.output_text_spans_and_outside_slots_verified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.full_contract_native_service_or_execution_authority
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/source access and one original proof; no caller-supplied graph or permission flag.
    pub fn prepare_unicode_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeCandidate<'_>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_unicode_candidate(&self.imported,selector,policy,form,run,limits,writer)?;
        if !source_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(R::Binding);}
        let receipt=StoredUnicodeReceipt {source:self.receipt.clone(),output:output.receipt().clone(),profile:STORED_UNICODE_PROFILE,issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredUnicodeCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the existing imported owner without cloning or rebuilding the source/index.
    pub fn into_unicode_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeCandidate<'static>,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_unicode_candidate(provider,selector,policy,form,run,limits,writer,now)?;(prepared.output,prepared.receipt)};
        Ok(PreparedStoredUnicodeCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredUnicodeCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredUnicodeReceipt {&self.receipt}
    fn fresh<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(R::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()||self.receipt.profile!=STORED_UNICODE_PROFILE
            ||self.receipt.issuer_execution_publication_authority||!source_receipt_matches(&self.receipt.output,*fresh.digest.as_bytes()){return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Recheck current access/source and writer integrity without repeating normalization.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredUnicodeReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|R::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// The final head check stays inside writer-integrity verification, before calling the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|R::Integrity)?
    }
    /// # Errors
    /// Candidate integrity never grants dispatcher, CAS, durable idempotency claim or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
