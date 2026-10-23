//! Explicit review-body literal candidates under the original current source boundary.
mod product;
pub mod selector;
use super::*;
compiler_source!(PreparedStoredReviewLiteralCandidate);
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,
    replacement::atoms::review::{SourceReviewLiteralCandidate,SourceReviewLiteralReceipt}};
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredReviewLiteralReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceReviewLiteralReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredReviewLiteralCandidate<'a> {source:super::super::product::LiteralSource<'a>,output:SourceReviewLiteralCandidate,receipt:StoredReviewLiteralReceipt}
impl fmt::Debug for PreparedStoredReviewLiteralCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredReviewLiteralCandidate(<redacted>; not_CAS_or_product_route)")}}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write access and one whole original proof for the explicit review-body batch.
    pub fn prepare_review_literal_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredReviewLiteralCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_review_literal_candidate(&self.imported,query,scope,policy,replacement,run_policy,limits,writer)?;
        if output.receipt().output.source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let receipt=StoredReviewLiteralReceipt {source:self.receipt.clone(),output:output.receipt().clone(),
            profile:"hwpx-agent.stored-literal-search-candidate/v3",issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredReviewLiteralCandidate {source:super::super::product::LiteralSource::Borrowed(self),output,receipt})
    }
}
impl PreparedStoredReviewLiteralCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredReviewLiteralReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.output.source_package_sha256!=*fresh.digest.as_bytes()||self.receipt.issuer_execution_publication_authority
            ||self.receipt.output.output.full_protection_native_or_execution_authority||self.receipt.output.output.field_cached_content_edit_qualified
            ||self.receipt.output.output.control_atom_replacement_qualified||!self.receipt.output.output.original_control_bytes_preserved
            ||self.receipt.output.native_author_visibility_resolution_or_execution_qualified||!self.receipt.output.memo_payload_not_cached_result_verified {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Fresh access/source and writer integrity without repeating search, lowering or review import.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredReviewLiteralReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original final head boundary is inside the writer callback, before consumer access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// Source-body preparation is not durable claim, revision CAS or an executable route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
