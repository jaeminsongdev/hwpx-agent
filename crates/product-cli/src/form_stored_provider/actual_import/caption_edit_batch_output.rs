//! Fresh service authorization for one original-bound caption text/layout candidate.
use super::*;
use super::caption_text_output::StoredCaptionTextError as E;
use super::caption_text_batch_output::StoredCaptionTextRequestBinding;
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::structure::{
    caption_layout::CaptionLayout,caption_text_batch::CaptionTextReplacement,
    caption_edit_batch::{CaptionLayoutReplacement,CaptionEditBatchOutputCandidate,CaptionEditBatchOutputReceipt},
}};
use sha2::{Digest as _,Sha256};
use std::collections::BTreeMap;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionLayoutRequestBinding {
    pub source_caption_id:LogicalId,pub requested_layout:CaptionLayout,pub changed:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionEditBatchReceipt {
    pub source:StoredActualFormImportReceipt,
    pub text_requests:Vec<StoredCaptionTextRequestBinding>,
    pub layout_requests:Vec<StoredCaptionLayoutRequestBinding>,
    pub output:CaptionEditBatchOutputReceipt,
    pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionEditBatchCandidate<'a> {
    source:&'a StoredImportedDocumentForms,output:CaptionEditBatchOutputCandidate,
    receipt:StoredCaptionEditBatchReceipt,
}
impl fmt::Debug for PreparedStoredCaptionEditBatchCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionEditBatchCandidate(<redacted>; not_sequence_CAS_or_execution_authority)")}
}
impl StoredImportedDocumentForms {
    /// One current service source and whole Form proof for both edit families.
    /// No per-request source read, intermediate package, ingest or revision commit.
    /// # Errors
    /// Rejects stale/revoked/tampered/foreign inputs, any compiler failure,
    /// request/output binding drift or a changed head before returning a candidate.
    pub fn prepare_caption_edit_batch_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionEditBatchCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_caption_edit_batch_candidate(&self.imported,&fresh.bytes,texts,layouts,limits,writer)?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        let changed_text:BTreeMap<_,_>=output.receipt().text_changes.iter().map(|c|(&c.source_text_id,c)).collect();
        let changed_layout:BTreeMap<_,_>=output.receipt().layout_changes.iter().map(|c|(&c.source_caption_id,c)).collect();
        let mut text_requests=Vec::new();text_requests.try_reserve_exact(texts.len()).map_err(|_|E::Binding)?;
        let mut layout_requests=Vec::new();layout_requests.try_reserve_exact(layouts.len()).map_err(|_|E::Binding)?;
        for request in texts {
            text_requests.push(StoredCaptionTextRequestBinding {source_caption_id:request.caption_id.clone(),source_text_id:request.text_id.clone(),
                requested_text_sha256:Sha256::digest(request.replacement.as_bytes()).into(),requested_text_bytes:request.replacement.len(),
                changed:changed_text.contains_key(request.text_id)});
        }
        for request in layouts {
            layout_requests.push(StoredCaptionLayoutRequestBinding {source_caption_id:request.caption_id.clone(),
                requested_layout:request.layout,changed:changed_layout.contains_key(request.caption_id)});
        }
        drop(changed_text);drop(changed_layout);
        let receipt=StoredCaptionEditBatchReceipt {source:self.receipt.clone(),text_requests,layout_requests,output:output.receipt().clone(),
            qualification:"fresh_service_source_bound_atomic_caption_text_layout_memory_candidate_not_full_sequence_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        if !bindings_match(&receipt){return Err(E::Binding);}
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredCaptionEditBatchCandidate {source:self,output,receipt})
    }
}
impl PreparedStoredCaptionEditBatchCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionEditBatchReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()||!bindings_match(&self.receipt){return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Every verification reauthorizes/reconstructs the current whole source.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionEditBatchReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(self.receipt.clone())
    }
    /// # Errors
    /// No callback after fresh source/access/integrity/final-head rejection.
    /// This last read is not atomic CAS or authority to retain plaintext access.
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
    /// Always denies execution/publication even after fresh successful verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
fn bindings_match(receipt:&StoredCaptionEditBatchReceipt)->bool {
    !receipt.issuer_execution_publication_authority&&request_bindings_match(&receipt.text_requests,&receipt.layout_requests,&receipt.output)
}
pub(super) fn request_bindings_match(text_requests:&[StoredCaptionTextRequestBinding],layout_requests:&[StoredCaptionLayoutRequestBinding],
    output:&CaptionEditBatchOutputReceipt)->bool {
    if output.execution_publication_authority||text_requests.len()!=output.requested_text_leaves||layout_requests.len()!=output.requested_layouts{return false;}
    let texts:BTreeMap<_,_>=text_requests.iter().map(|r|(&r.source_text_id,r)).collect();
    let text_changes:BTreeMap<_,_>=output.text_changes.iter().map(|c|(&c.source_text_id,c)).collect();
    let layouts:BTreeMap<_,_>=layout_requests.iter().map(|r|(&r.source_caption_id,r)).collect();
    let layout_changes:BTreeMap<_,_>=output.layout_changes.iter().map(|c|(&c.source_caption_id,c)).collect();
    if texts.len()!=text_requests.len()||text_changes.len()!=output.text_changes.len()
        ||layouts.len()!=layout_requests.len()||layout_changes.len()!=output.layout_changes.len()
        ||text_requests.iter().any(|r|r.changed!=text_changes.contains_key(&r.source_text_id))
        ||layout_requests.iter().any(|r|r.changed!=layout_changes.contains_key(&r.source_caption_id)){return false;}
    output.text_changes.iter().all(|c|texts.get(&c.source_text_id).is_some_and(|r|r.changed&&r.source_caption_id==c.source_caption_id
        &&r.requested_text_sha256==c.output_text_sha256&&r.requested_text_bytes==c.output_text_bytes))
        &&output.layout_changes.iter().all(|c|layouts.get(&c.source_caption_id).is_some_and(|r|
            r.changed&&r.requested_layout==c.requested_layout&&(1..=5).contains(&c.changed_attributes)))
}

