//! Fresh stored-source authorization around one atomic caption text memory batch.
use super::*;
use super::caption_text_output::StoredCaptionTextError as E;
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::structure::caption_text_batch::{
    CaptionTextReplacement,CaptionTextBatchOutputCandidate,CaptionTextBatchOutputReceipt,
}};
use sha2::{Digest as _,Sha256};
use std::collections::BTreeMap;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionTextRequestBinding {
    pub source_caption_id:LogicalId,pub source_text_id:LogicalId,
    pub requested_text_sha256:[u8;32],pub requested_text_bytes:usize,pub changed:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionTextBatchReceipt {
    pub source:StoredActualFormImportReceipt,
    pub requests:Vec<StoredCaptionTextRequestBinding>,
    pub output:CaptionTextBatchOutputReceipt,
    pub qualification:&'static str,
    pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionTextBatchCandidate<'a> {
    source:&'a StoredImportedDocumentForms,
    output:CaptionTextBatchOutputCandidate,
    receipt:StoredCaptionTextBatchReceipt,
}
impl fmt::Debug for PreparedStoredCaptionTextBatchCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionTextBatchCandidate(<redacted>; not_CAS_or_execution_authority)")}
}
impl StoredImportedDocumentForms {
    /// One current service read/whole form reconstruction supplies the original
    /// proof to the whole batch. No per-leaf source read, output ingest or commit.
    /// # Errors
    /// Rejects stale/revoked/tampered/foreign source, any original batch failure,
    /// request/output mismatches and a changed head before returning a candidate.
    pub fn prepare_caption_text_batch_candidate<R,B,S,V>(&self,
        provider:&StoredFormProvider<'_,R,B,S,V>,requests:&[CaptionTextReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionTextBatchCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_caption_text_batch_candidate(&self.imported,&fresh.bytes,requests,limits,writer_limits)?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let changes:BTreeMap<_,_>=output.receipt().changes.iter().map(|c|(&c.source_text_id,c)).collect();
        let mut bindings=Vec::new();bindings.try_reserve_exact(requests.len()).map_err(|_|E::Binding)?;
        for request in requests {
            bindings.push(StoredCaptionTextRequestBinding {source_caption_id:request.caption_id.clone(),source_text_id:request.text_id.clone(),
                requested_text_sha256:Sha256::digest(request.replacement.as_bytes()).into(),requested_text_bytes:request.replacement.len(),changed:changes.contains_key(request.text_id)});
        }
        drop(changes);
        let receipt=StoredCaptionTextBatchReceipt {source:self.receipt.clone(),requests:bindings,output:output.receipt().clone(),
            qualification:"fresh_service_source_bound_atomic_plain_caption_text_memory_batch_not_full_sequence_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        if !bindings_match(&receipt){return Err(E::Binding);}
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredCaptionTextBatchCandidate {source:self,output,receipt})
    }
}
impl PreparedStoredCaptionTextBatchCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionTextBatchReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        // Every operation reauthorizes the whole current source. Saved receipts,
        // plaintext snapshots or original form proofs are not retained access.
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()||!bindings_match(&self.receipt){return Err(E::Binding);}
        Ok(())
    }
    /// # Errors
    /// Requires current access, whole source reconstruction and artifact integrity.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionTextBatchReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(self.receipt.clone())
    }
    /// One freshly authorized complete batch, with the final head check inside
    /// the writer-integrity callback. These reads do not implement atomic CAS.
    /// # Errors
    /// No callback after source/access/request/integrity rejection.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// Always denies executable/publication routes after fresh verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
fn bindings_match(receipt:&StoredCaptionTextBatchReceipt)->bool {
    if receipt.issuer_execution_publication_authority||receipt.requests.len()!=receipt.output.requested_leaves
        ||receipt.output.changed_leaves!=receipt.output.changes.len(){return false;}
    let bindings:BTreeMap<_,_>=receipt.requests.iter().map(|r|(&r.source_text_id,r)).collect();
    let changes:BTreeMap<_,_>=receipt.output.changes.iter().map(|c|(&c.source_text_id,c)).collect();
    if bindings.len()!=receipt.requests.len()||changes.len()!=receipt.output.changed_leaves{return false;}
    if receipt.requests.iter().any(|r|r.changed!=changes.contains_key(&r.source_text_id)){return false;}
    receipt.output.changes.iter().all(|change|bindings.get(&change.source_text_id).is_some_and(|request|
        request.changed&&request.source_caption_id==change.source_caption_id
            &&request.requested_text_sha256==change.output_text_sha256&&request.requested_text_bytes==change.output_text_bytes))
}
