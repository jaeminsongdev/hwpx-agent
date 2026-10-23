//! Fresh stored-source binding for explicit caption arithmetic and generated labels.
//! Reuses the original access/writer boundary; no retained access or source writes.
use super::*;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionProgramReceipt {
    pub content:StoredCaptionContentReceipt,pub program:SourceCaptionSequenceOutputReceipt,
    pub requested_program_sha256:[u8;32],pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionProgramCandidate<'a> {content:PreparedStoredCaptionContentCandidate<'a>,receipt:StoredCaptionProgramReceipt}
impl fmt::Debug for PreparedStoredCaptionProgramCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredCaptionProgramCandidate(<redacted>; not_native_counter_CAS_or_execution_authority)")}}
/// Match generated labels, including no-ops, without rebuilding source models or
/// serializing plaintext. Definition/member indexes are built once, not per leaf.
pub(super) fn generated_label_bindings(request:&SourceCaptionSequenceRequest<'_>,output:&SourceCaptionSequenceOutputReceipt,
    changed:&BTreeMap<&LogicalId,&hwpx_package::document_import::structure::caption_text_batch::CaptionTextBatchChange>,limits:ReferenceAuxiliaryLimits,
)->Result<Vec<StoredCaptionTextRequestBinding>,StoredCaptionContentError> {
    let mut definitions=BTreeMap::new();
    for sequence in request.sequences {
        let bytes=sequence.label.len().checked_add(sequence.separator.len()).filter(|n|*n<=limits.config().text_bytes).ok_or(StoredCaptionContentError::Binding)?;
        let mut digest=Sha256::new();digest.update(sequence.label.as_bytes());digest.update(sequence.separator.as_bytes());let digest:[u8;32]=digest.finalize().into();
        if definitions.insert(&sequence.logical_sequence_id,(digest,bytes)).is_some(){return Err(StoredCaptionContentError::Binding);}
    }
    let assignments:BTreeMap<_,_>=request.assignments.iter().map(|m|(m.caption_id,m)).collect();
    if assignments.len()!=request.assignments.len()||output.bindings.len()!=assignments.len(){return Err(StoredCaptionContentError::Binding);}
    let mut bindings=Vec::new();bindings.try_reserve_exact(output.bindings.len()).map_err(|_|StoredCaptionContentError::Binding)?;
    let mut seen=std::collections::BTreeSet::new();
    for binding in &output.bindings {
        if !seen.insert(&binding.source_caption_id){return Err(StoredCaptionContentError::Binding);}
        let assignment=*assignments.get(&binding.source_caption_id).ok_or(StoredCaptionContentError::Binding)?;
        let &(digest,bytes)=definitions.get(assignment.sequence_id).ok_or(StoredCaptionContentError::Binding)?;
        let sequence_sha:[u8;32]=Sha256::digest(assignment.sequence_id.as_str().as_bytes()).into();
        if assignment.object_id!=&binding.source_object_id||assignment.label_text_id!=&binding.source_label_text_id||assignment.number_control_id!=&binding.source_number_control_id
            ||assignment.document_order!=binding.caller_document_order||binding.sequence_id_sha256!=sequence_sha||binding.requested_label_sha256!=digest{return Err(StoredCaptionContentError::Binding);}
        bindings.push(StoredCaptionTextRequestBinding {source_caption_id:binding.source_caption_id.clone(),source_text_id:binding.source_label_text_id.clone(),
            requested_text_sha256:digest,requested_text_bytes:bytes,changed:changed.contains_key(&binding.source_label_text_id)});
    }Ok(bindings)
}
impl StoredImportedDocumentForms {
    /// One fresh authenticated source/proof/state for explicit program, generated
    /// labels and additional text/layout/style requests. No native order inference.
    /// # Errors
    /// Rejects current access/source/compiler/binding failures and head movement;
    /// no partial output, new source revision or saved authorization is returned.
    pub fn prepare_caption_program_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        request:&SourceCaptionSequenceRequest<'_>,texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionProgramCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let content=self.prepare_caption_content_checked(provider,texts,layouts,styles,StoredCaptionNumberRequest::Program(request),limits,writer,now)?;
        let program=content.output.program().ok_or(StoredCaptionContentError::Binding)?.clone();let requested_program_sha256=request.canonical_sha256(limits)?;
        let receipt=StoredCaptionProgramReceipt {content:content.receipt.clone(),program,requested_program_sha256,
            qualification:"fresh_service_source_bound_explicit_caption_program_and_generated_labels_not_native_counter_full_state_flow_protection_CAS_execution_or_native",issuer_execution_publication_authority:false};
        let candidate=PreparedStoredCaptionProgramCandidate {content,receipt};candidate.check_binding()?;
        provider.check_head(self.source.head).map_err(StoredActualFormImportError::from)?;Ok(candidate)
    }
}
impl PreparedStoredCaptionProgramCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionProgramReceipt{&self.receipt}
    fn check_binding(&self)->Result<(),StoredCaptionContentError> {
        let program=&self.receipt.program;
        if self.receipt.issuer_execution_publication_authority||program.execution_publication_authority||program.native_counter_recalculation_qualified
            ||!program.complete_original_caption_membership_checked||!program.labels_stored_numbers_and_declared_styles_read_back||!program.caller_order_not_native_counter_order
            ||program.caller_request_sha256!=self.receipt.requested_program_sha256||program.lowered_number_request_sha256!=program.output.number_sequence.caller_request_sha256
            ||self.content.output.program()!=Some(program)||self.receipt.content!=self.content.receipt||self.receipt.content.output!=program.output.content{return Err(StoredCaptionContentError::Binding);}Ok(())
    }
    /// # Errors
    /// Rechecks current service access/source/integrity/head on every call.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionProgramReceipt,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.content.verify(provider,now)?;self.check_binding()?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// No callback after current scope/ACL/quarantine/AEAD/source/head rejection.
    /// The final head read is not CAS or retained plaintext-access permission.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check_binding()?;self.content.with_verified_bytes(provider,now,consume)
    }
    /// # Errors
    /// Always denies execution/publication after fresh verification succeeds.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionContentError::RouteUnqualified)
    }
}
