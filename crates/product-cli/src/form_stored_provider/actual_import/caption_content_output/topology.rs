//! Current stored-source access for typed number-control structural edits.
//! The inner content candidate remains private; no alternate bytes/access path.
use super::*;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionTopologyReceipt {
    pub content:StoredCaptionContentReceipt,pub number_topology:NativeNumberTopologyOutputReceipt,
    pub requested_topology_sha256:[u8;32],pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionTopologyCandidate<'a> {content:PreparedStoredCaptionContentCandidate<'a>,receipt:StoredCaptionTopologyReceipt}
impl fmt::Debug for PreparedStoredCaptionTopologyCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionTopologyCandidate(<redacted>; not_native_counter_CAS_or_execution_authority)")}
}
impl StoredImportedDocumentForms {
    /// Uses the same fresh access/AEAD source, whole Form proof and single joined
    /// state as existing content/sequence preparation. Does not write the source.
    /// # Errors
    /// Rejects access/source/compiler/binding failures and head movement before
    /// returning a candidate. Request hashes never serve as access permission.
    pub fn prepare_caption_topology_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        topology:&NativeNumberTopologyRequest<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionTopologyCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let content=self.prepare_caption_content_checked(provider,texts,layouts,styles,StoredCaptionNumberRequest::Topology(topology),limits,writer,now)?;
        let number_topology=content.output.topology().ok_or(StoredCaptionContentError::Binding)?.clone();
        let requested_topology_sha256=topology.canonical_sha256(limits)?;
        let receipt=StoredCaptionTopologyReceipt {content:content.receipt.clone(),number_topology,requested_topology_sha256,
            qualification:"fresh_service_source_bound_caption_content_and_number_control_topology_not_counter_full_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        let candidate=PreparedStoredCaptionTopologyCandidate {content,receipt};candidate.check_binding()?;
        provider.check_head(self.source.head).map_err(StoredActualFormImportError::from)?;Ok(candidate)
    }
}
impl PreparedStoredCaptionTopologyCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionTopologyReceipt {&self.receipt}
    fn check_binding(&self)->Result<(),StoredCaptionContentError> {
        let topology=&self.receipt.number_topology;
        if self.receipt.issuer_execution_publication_authority||topology.execution_publication_authority||topology.native_counter_recalculation_qualified
            ||!topology.complete_original_and_inserted_inventory_read_back
            ||self.receipt.requested_topology_sha256!=topology.caller_request_sha256
            ||topology.source_joined_state_sha256!=self.content.output.receipt().source_state.joined_state_sha256
            ||self.content.output.topology()!=Some(topology)||self.receipt.content!=self.content.receipt{return Err(StoredCaptionContentError::Binding);}Ok(())
    }
    /// # Errors
    /// Reauthorizes current scope/ACL/quarantine/AEAD/source/head every call.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionTopologyReceipt,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.content.verify(provider,now)?;self.check_binding()?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// The existing final writer-head check precedes the consumer callback.
    /// A successful read is not CAS or retained plaintext-access authority.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check_binding()?;self.content.with_verified_bytes(provider,now,consume)
    }
    /// # Errors
    /// Execution and publication remain denied after successful fresh verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionContentError::RouteUnqualified)
    }
}
