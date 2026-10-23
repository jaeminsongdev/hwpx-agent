//! v2 atom candidates share the original sealed-source/current-access boundaries, not authority.
mod product;
pub mod review;
use super::*;
compiler_source!(PreparedStoredLiteralTextAtomCandidate);
use hwpx_package::document_import::search::replacement::atoms::{SourceLiteralTextAtomCandidate,SourceLiteralTextAtomReceipt};
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredLiteralTextAtomReceipt {pub source:StoredActualFormImportReceipt,pub output:SourceLiteralTextAtomReceipt,
    pub profile:&'static str,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredLiteralTextAtomCandidate<'a> {source:super::product::LiteralSource<'a>,output:SourceLiteralTextAtomCandidate,receipt:StoredLiteralTextAtomReceipt}
impl fmt::Debug for PreparedStoredLiteralTextAtomCandidate<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredLiteralTextAtomCandidate(<redacted>; not_CAS_or_product_route)")}}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write access and one whole-source proof for this complete v2 batch.
    pub fn prepare_literal_text_atom_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralTextAtomCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_literal_text_atom_candidate(&self.imported,query,scope,replacement,run_policy,limits,writer)?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let receipt=StoredLiteralTextAtomReceipt {source:self.receipt.clone(),output:output.receipt().clone(),
            profile:"hwpx-agent.stored-literal-search-candidate/v2",issuer_execution_publication_authority:false};
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredLiteralTextAtomCandidate {source:super::product::LiteralSource::Borrowed(self),output,receipt})
    }
}
impl PreparedStoredLiteralTextAtomCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredLiteralTextAtomReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()||self.receipt.issuer_execution_publication_authority
            ||self.receipt.output.full_protection_native_or_execution_authority||self.receipt.output.field_cached_content_edit_qualified
            ||self.receipt.output.control_atom_replacement_qualified||!self.receipt.output.original_control_bytes_preserved {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Fresh authorization/source and writer integrity, without repeating the query or lowering.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredLiteralTextAtomReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head inside the writer-integrity callback, before consumer access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// A prepared artifact is neither durable key reservation nor CAS/execution/publication.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
