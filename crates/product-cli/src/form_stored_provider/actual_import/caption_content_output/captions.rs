//! Fresh stored access for whole-caption creation/deletion, not Native authority.
//! All bytes still pass the existing private content and final-head boundary.
use super::*;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionStructureReceipt {
    pub content:StoredCaptionContentReceipt,pub caption_topology:CaptionTopologyOutputReceipt,
    pub requested_structure_sha256:[u8;32],pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionStructureCandidate<'a> {content:PreparedStoredCaptionContentCandidate<'a>,receipt:StoredCaptionStructureReceipt}
impl fmt::Debug for PreparedStoredCaptionStructureCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionStructureCandidate(<redacted>; not_native_counter_CAS_or_execution_authority)")}
}
/// Receipt creations follow source owner order, not caller request order.
/// One owner index avoids repeated scans; no generated plaintext is retained.
fn request_matches(request:&SourceCaptionTopologyRequest<'_>,output:&CaptionTopologyOutputReceipt)->bool {
    if request.expected_joined_state_sha256!=output.source_joined_state_sha256
        ||request.deletions.len()!=output.deleted.len()||request.creations.len()!=output.created.len(){return false;}
    if !request.deletions.iter().zip(&output.deleted).all(|(r,b)|r.caption_id==&b.source_caption_id&&r.caption_fingerprint_sha256==b.source_caption_sha256){return false;}
    let mut created:BTreeMap<_,_>=output.created.iter().map(|b|(&b.source_object_id,b)).collect();
    if created.len()!=output.created.len(){return false;}
    for r in request.creations {
        let Some(b)=created.remove(r.object_id)else{return false};
        if b.local_id_sha256!=<[u8;32]>::from(Sha256::digest(r.local_id.as_str().as_bytes()))||b.allocated_paragraph_ids.len()!=r.paragraphs.len(){return false;}
    }created.is_empty()
}
impl StoredImportedDocumentForms {
    /// Shares one fresh authenticated source, whole Form proof and joined state
    /// with retained text/layout/style edits. Does not ingest or commit a result.
    /// # Errors
    /// Rejects current access/source/compiler/request-output binding failures
    /// and head changes. Caller digests never grant access permission.
    pub fn prepare_caption_structure_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        request:&SourceCaptionTopologyRequest<'_>,texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionStructureCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let content=self.prepare_caption_content_checked(provider,texts,layouts,styles,StoredCaptionNumberRequest::Captions(request),limits,writer,now)?;
        let caption_topology=content.output.captions().ok_or(StoredCaptionContentError::Binding)?.clone();
        if !request_matches(request,&caption_topology){return Err(StoredCaptionContentError::Binding);}
        let requested_structure_sha256=request.canonical_sha256(limits)?;
        let receipt=StoredCaptionStructureReceipt {content:content.receipt.clone(),caption_topology,requested_structure_sha256,
            qualification:"fresh_service_source_bound_whole_caption_creation_deletion_not_native_counter_full_state_flow_protection_CAS_execution_or_native",issuer_execution_publication_authority:false};
        let candidate=PreparedStoredCaptionStructureCandidate {content,receipt};candidate.check_binding()?;
        provider.check_head(self.source.head).map_err(StoredActualFormImportError::from)?;Ok(candidate)
    }
}
impl PreparedStoredCaptionStructureCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionStructureReceipt{&self.receipt}
    fn check_binding(&self)->Result<(),StoredCaptionContentError> {
        let topology=&self.receipt.caption_topology;
        if self.receipt.issuer_execution_publication_authority||topology.execution_publication_authority||topology.native_counter_recalculation_qualified
            ||!topology.complete_owner_caption_and_native_control_inventory_read_back
            ||self.receipt.requested_structure_sha256!=topology.caller_request_sha256
            ||topology.source_joined_state_sha256!=self.content.output.receipt().source_state.joined_state_sha256
            ||self.content.output.captions()!=Some(topology)||self.receipt.content!=self.content.receipt{return Err(StoredCaptionContentError::Binding);}Ok(())
    }
    /// # Errors
    /// Reauthorizes current scope/ACL/quarantine/AEAD/source/head every call.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionStructureReceipt,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.content.verify(provider,now)?;self.check_binding()?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Current access and the final writer-head read precede the callback.
    /// This is not atomic CAS or authority to retain plaintext access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check_binding()?;self.content.with_verified_bytes(provider,now,consume)
    }
    /// # Errors
    /// Execution and publication remain denied after fresh verification succeeds.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionContentError::RouteUnqualified)
    }
}
