//! Selector-window candidates keep the original v3 meaning separate and retain current access.
use super::*;
compiler_source!(PreparedStoredSelectorLiteralCandidate);
use super::super::super::product::LiteralSource;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,
    replacement::atoms::review::selector::{SourceSelectorLiteralCandidate,SourceSelectorLiteralReceipt,SOURCE_SELECTOR_LITERAL_PROFILE}};
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredSelectorLiteralReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceSelectorLiteralReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredSelectorLiteralCandidate<'a> {source:LiteralSource<'a>,output:SourceSelectorLiteralCandidate,receipt:StoredSelectorLiteralReceipt}
impl fmt::Debug for PreparedStoredSelectorLiteralCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSelectorLiteralCandidate(<redacted>; not_CAS_or_product_route)")}}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write access and one complete source proof; selector windows never expand to paragraphs.
    pub fn prepare_review_selector_literal_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorLiteralCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_selector_literal_candidate(&self.imported,query,selector,policy,replacement,run_policy,limits,writer)?;
        if output.receipt().body_candidate.output.source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let receipt=StoredSelectorLiteralReceipt {source:self.receipt.clone(),output:output.receipt().clone(),
            profile:"hwpx-agent.stored-selector-literal-candidate/v1",issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredSelectorLiteralCandidate {source:LiteralSource::Borrowed(self),output,receipt})
    }
    /// # Errors
    /// Move the original source owner and already prepared output; no clone or ownership-transfer import.
    pub fn into_review_selector_literal_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorLiteralCandidate<'static>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)={let prepared=self.prepare_review_selector_literal_candidate(provider,query,selector,policy,replacement,run_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredSelectorLiteralCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
impl PreparedStoredSelectorLiteralCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredSelectorLiteralReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        let selector=&self.receipt.output;let review=&selector.body_candidate;let output=&review.output;
        if self.receipt.source!=self.source.receipt||selector!=self.output.receipt()
            ||self.receipt.profile!="hwpx-agent.stored-selector-literal-candidate/v1"||selector.profile!=SOURCE_SELECTOR_LITERAL_PROFILE
            ||output.source_package_sha256!=*fresh.digest.as_bytes()
            ||selector.selector.index_sha256!=output.source_index_sha256||selector.selector.scope_sha256!=output.scope_sha256
            ||!selector.scope_window_enforced||selector.native_or_execution_authority||selector.selector.whole_document_visibility_native_flow_or_revision_authority
            ||self.receipt.issuer_execution_publication_authority||output.full_protection_native_or_execution_authority||output.field_cached_content_edit_qualified
            ||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved
            ||review.native_author_visibility_resolution_or_execution_qualified||!review.memo_payload_not_cached_result_verified {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source, original writer integrity and final head; no repeated query or lowering.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredSelectorLiteralReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head remains inside the integrity callback and precedes all consumer access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// Source candidate preparation is not a durable request claim, revision CAS or execution route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
