//! Fresh stored-source access around a verified one-caption-text memory candidate.
//! No output ingest, revision commit, service route or cached authorization.
use super::*;
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::structure::caption_text::{
    CaptionTextOutputCandidate,CaptionTextOutputError,CaptionTextOutputReceipt,
}};
use sha2::{Digest as _,Sha256};

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionTextOutputReceipt {
    pub source:StoredActualFormImportReceipt,
    pub source_caption_id:LogicalId,
    pub source_text_id:LogicalId,
    pub requested_text_sha256:[u8;32],
    pub requested_text_bytes:usize,
    pub output:CaptionTextOutputReceipt,
    pub qualification:&'static str,
    pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionTextCandidate<'a> {
    source:&'a StoredImportedDocumentForms,
    output:CaptionTextOutputCandidate,
    receipt:StoredCaptionTextOutputReceipt,
}
impl fmt::Debug for PreparedStoredCaptionTextCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionTextCandidate(<redacted>; text_only_not_service_authority)")}
}
#[derive(Debug,Error)]
pub enum StoredCaptionTextError {
    #[error("stored caption text source access rejected")] Source(#[from] StoredActualFormImportError),
    #[error("stored caption text output rejected")] Output(#[from] CaptionTextOutputError),
    #[error("stored caption text artifact integrity rejected")] Integrity,
    #[error("stored caption text source/output binding rejected")] Binding,
    #[error("stored caption text product route unqualified")] RouteUnqualified,
}
impl StoredImportedDocumentForms {
    /// Fresh scope/head/ACL/quarantine/AEAD read plus whole reconstruction before
    /// lowering. Its exact original-bound proof avoids another input import.
    /// Only the existing metadata/download read audits are service effects.
    /// # Errors
    /// Rejects stale/revoked/tampered/foreign access and every original text
    /// selection, protection, value, ID, limit, writer and readback rejection.
    pub fn prepare_caption_text_candidate<R,B,S,V>(&self,
        provider:&StoredFormProvider<'_,R,B,S,V>,caption_id:&LogicalId,text_id:&LogicalId,
        replacement:&str,limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionTextCandidate<'_>,StoredCaptionTextError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_caption_text_candidate(&self.imported,&fresh.bytes,caption_id,text_id,replacement,limits,writer_limits)?;
        let requested_text_sha256:[u8;32]=Sha256::digest(replacement.as_bytes()).into();
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes()
            ||output.receipt().output_text_sha256!=requested_text_sha256
            ||output.receipt().output_text_bytes!=replacement.len() {return Err(StoredCaptionTextError::Binding);}
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        let receipt=StoredCaptionTextOutputReceipt {source:self.receipt.clone(),source_caption_id:caption_id.clone(),source_text_id:text_id.clone(),
            requested_text_sha256,requested_text_bytes:replacement.len(),output:output.receipt().clone(),
            qualification:"fresh_service_source_bound_plain_caption_text_memory_candidate_not_sequence_state_full_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        Ok(PreparedStoredCaptionTextCandidate {source:self,output,receipt})
    }
}
impl PreparedStoredCaptionTextCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionTextOutputReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionTextError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        // A retained source, proof, receipt or candidate never retains access.
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()
            ||self.receipt.requested_text_sha256!=self.receipt.output.output_text_sha256
            ||self.receipt.requested_text_bytes!=self.receipt.output.output_text_bytes
            ||self.receipt.issuer_execution_publication_authority {return Err(StoredCaptionTextError::Binding);}
        Ok(())
    }
    /// # Errors
    /// Reauthorizes against current service bytes and verifies writer integrity.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
        ->Result<StoredCaptionTextOutputReceipt,StoredCaptionTextError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|_|()).map_err(|_|StoredCaptionTextError::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(self.receipt.clone())
    }
    /// Each exposure requires fresh access, writer integrity and a final head
    /// check inside the writer callback. These reads are not an atomic CAS.
    /// # Errors
    /// Never invokes the consumer after source/access/integrity rejection.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionTextError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(consume(bytes))
        }).map_err(|_|StoredCaptionTextError::Integrity)?
    }
    /// # Errors
    /// Always denies executable routes, including after successful verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
        ->Result<(),StoredCaptionTextError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionTextError::RouteUnqualified)
    }
}
