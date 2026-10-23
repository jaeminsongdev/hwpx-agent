//! Current authorized sealed source -> actual original-bound literal replacement candidate.
#[macro_use] mod compiler_view;
mod product;
pub mod atoms;
pub mod regex;
pub mod styles;
pub mod text_styles;
pub mod paragraph_styles;
pub mod named_styles;
pub mod unicode;
pub mod case;
pub mod width;
pub mod fonts;
pub mod whitespace;
pub mod controls;
pub mod number_controls;
pub mod sort;
pub mod sort_groups;
pub mod personal_info;
use super::*;
compiler_source!(PreparedStoredLiteralSearchCandidate);
use artifact_service::AuthScope;
use hwpx_package::{WriterLimits,document_import::search::{SourceSearchQuery,SourceSearchLimits,scope::SourceSearchScope,
    replacement::{SourceLiteralReplacementCandidate,SourceLiteralReplacementReceipt,SourceLiteralReplacementError,SourceReplacementRunPolicy}}};
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredLiteralSearchOutputReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceLiteralReplacementReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredLiteralSearchCandidate<'a> {source:product::LiteralSource<'a>,output:SourceLiteralReplacementCandidate,receipt:StoredLiteralSearchOutputReceipt}
impl fmt::Debug for PreparedStoredLiteralSearchCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredLiteralSearchCandidate(<redacted>; not_CAS_or_product_route)")}}
#[derive(Debug,Error)]
pub enum StoredLiteralSearchError {
    #[error("STORED_LITERAL_SEARCH_SOURCE_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_LITERAL_SEARCH_OUTPUT_REJECTED")] Output(#[from] SourceLiteralReplacementError),
    #[error("STORED_LITERAL_SEARCH_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_LITERAL_SEARCH_BINDING_REJECTED")] Binding,
    #[error("STORED_LITERAL_SEARCH_INTEGRITY_REJECTED")] Integrity,
    #[error("STORED_LITERAL_SEARCH_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type E=StoredLiteralSearchError;
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current service read and complete original proof for the whole batch.
    pub fn prepare_literal_search_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralSearchCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_literal_search_candidate(&self.imported,query,scope,replacement,run_policy,limits,writer)?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let receipt=StoredLiteralSearchOutputReceipt {source:self.receipt.clone(),output:output.receipt().clone(),
            profile:"hwpx-agent.stored-literal-search-candidate/v1",issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredLiteralSearchCandidate {source:product::LiteralSource::Borrowed(self),output,receipt})
    }
}
impl PreparedStoredLiteralSearchCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredLiteralSearchOutputReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()||self.receipt.issuer_execution_publication_authority
            ||self.receipt.output.full_protection_native_or_execution_authority||self.receipt.output.field_cached_content_edit_qualified {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Rechecks current access/source and writer integrity without rerunning the query.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredLiteralSearchOutputReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Fresh source and final head inside the writer-integrity callback, before consumer.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// Candidate preparation is not durable key claim, revision CAS or executable route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
