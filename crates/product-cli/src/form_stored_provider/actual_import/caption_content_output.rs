//! Fresh authenticated stored-source access for atomic caption content candidates.
//! No cached access, source overwrite, ingest, revision commit or product authority.
pub mod topology;
pub mod program;
pub mod captions;
use super::*;
use super::caption_text_batch_output::StoredCaptionTextRequestBinding;
use super::caption_edit_batch_output::{StoredCaptionLayoutRequestBinding,request_bindings_match};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::{reference_targets::{
    caption_source_state::{ImportedCaptionSourceState,output::content::{CaptionSourceStateContentOutputCandidate,CaptionSourceStateContentOutputReceipt}},
    caption_source_state::output::sequence::CaptionSourceStateSequenceOutputCandidate,
    caption_source_state::output::topology::CaptionSourceStateTopologyOutputCandidate,
    caption_source_state::output::program::{SourceCaptionSequenceRequest,SourceCaptionSequenceOutputCandidate,SourceCaptionSequenceOutputReceipt},
    caption_source_state::output::captions::CaptionSourceStateStructureOutputCandidate,
    caption_frames::{CaptionStyleFamily,CaptionStyleReference,CaptionStyleReferenceStatus as Status},
    numbering::CaptionNumberingImportError,
},structure::{caption_text::CaptionTextOutputError,caption_text_batch::CaptionTextReplacement,
    caption_edit_batch::CaptionLayoutReplacement,caption_style_batch::CaptionStyleReplacement,
    caption_numbering_sequence::{NativeNumberSequenceReplacement,NativeNumberSequenceOutputReceipt},
    caption_number_topology::{NativeNumberTopologyRequest,NativeNumberTopologyOutputReceipt},
    caption_topology::{SourceCaptionTopologyRequest,CaptionTopologyOutputReceipt}}}};
use sha2::{Digest as _,Sha256};
use std::collections::BTreeMap;

#[derive(Debug,Error)]
pub enum StoredCaptionContentError {
    #[error("stored caption content source access rejected")] Source(#[from] StoredActualFormImportError),
    #[error("stored caption content source state rejected")] State(#[from] CaptionNumberingImportError),
    #[error("stored caption content output rejected")] Output(#[from] CaptionTextOutputError),
    #[error("stored caption content artifact integrity rejected")] Integrity,
    #[error("stored caption content source/request/output binding rejected")] Binding,
    #[error("stored caption content product route unqualified")] RouteUnqualified,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionStyleRequestBinding {
    pub source_caption_id:LogicalId,pub source_node_id:LogicalId,pub family:CaptionStyleFamily,
    pub requested_declaration:CaptionStyleReference,pub changed:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionContentReceipt {
    pub source:StoredActualFormImportReceipt,
    pub text_requests:Vec<StoredCaptionTextRequestBinding>,pub layout_requests:Vec<StoredCaptionLayoutRequestBinding>,
    pub style_requests:Vec<StoredCaptionStyleRequestBinding>,pub output:CaptionSourceStateContentOutputReceipt,
    pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionContentCandidate<'a> {
    source:&'a StoredImportedDocumentForms,output:StoredCaptionOutput,receipt:StoredCaptionContentReceipt,
}
// Private closed variants share the same current-access and writer boundary.
// No caller-implemented output, saved authorization or alternate byte accessor.
enum StoredCaptionOutput {Content(CaptionSourceStateContentOutputCandidate),Sequence(CaptionSourceStateSequenceOutputCandidate),Topology(CaptionSourceStateTopologyOutputCandidate),Program(SourceCaptionSequenceOutputCandidate),Captions(CaptionSourceStateStructureOutputCandidate)}
#[derive(Clone,Copy)]
enum StoredCaptionNumberRequest<'a,'r> {None,Sequence(&'a NativeNumberSequenceReplacement<'r>),Topology(&'a NativeNumberTopologyRequest<'r>),Program(&'a SourceCaptionSequenceRequest<'r>),Captions(&'a SourceCaptionTopologyRequest<'r>)}
impl StoredCaptionOutput {
    fn receipt(&self)->&CaptionSourceStateContentOutputReceipt {match self {Self::Content(c)=>c.receipt(),Self::Sequence(c)=>&c.receipt().content,Self::Topology(c)=>&c.receipt().content,Self::Program(c)=>&c.receipt().output.content,Self::Captions(c)=>&c.receipt().content}}
    fn numbers(&self)->Option<&NativeNumberSequenceOutputReceipt> {match self {Self::Content(_)|Self::Topology(_)|Self::Program(_)|Self::Captions(_)=>None,Self::Sequence(c)=>Some(&c.receipt().number_sequence)}}
    fn topology(&self)->Option<&NativeNumberTopologyOutputReceipt> {match self {Self::Topology(c)=>Some(&c.receipt().number_topology),Self::Content(_)|Self::Sequence(_)|Self::Program(_)|Self::Captions(_)=>None}}
    fn program(&self)->Option<&SourceCaptionSequenceOutputReceipt> {match self {Self::Program(c)=>Some(c.receipt()),Self::Content(_)|Self::Sequence(_)|Self::Topology(_)|Self::Captions(_)=>None}}
    fn captions(&self)->Option<&CaptionTopologyOutputReceipt> {match self {Self::Captions(c)=>Some(&c.receipt().caption_topology),Self::Content(_)|Self::Sequence(_)|Self::Topology(_)|Self::Program(_)=>None}}
    fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,hwpx_package::WriterError> {
        match self {Self::Content(c)=>c.with_verified_bytes(consume),Self::Sequence(c)=>c.with_verified_bytes(consume),Self::Topology(c)=>c.with_verified_bytes(consume),Self::Program(c)=>c.with_verified_bytes(consume),Self::Captions(c)=>c.with_verified_bytes(consume)}
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredCaptionSequenceReceipt {
    pub content:StoredCaptionContentReceipt,pub number_sequence:NativeNumberSequenceOutputReceipt,
    pub requested_sequence_sha256:[u8;32],pub qualification:&'static str,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredCaptionSequenceCandidate<'a> {content:PreparedStoredCaptionContentCandidate<'a>,receipt:StoredCaptionSequenceReceipt}
impl fmt::Debug for PreparedStoredCaptionSequenceCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionSequenceCandidate(<redacted>; stored_values_not_native_counter_CAS_or_execution_authority)")}
}
impl fmt::Debug for PreparedStoredCaptionContentCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionContentCandidate(<redacted>; not_effective_style_sequence_CAS_or_execution_authority)")}
}
impl StoredImportedDocumentForms {
    /// One fresh service source, operation-local whole Form proof and joined
    /// original state for all text/layout/style requests. No intermediate output
    /// or per-request source/state import, persisted trust or write capability.
    /// # Errors
    /// Rejects stale/revoked/tampered/foreign access, incomplete state, any
    /// compiler/binding error and head movement before returning a candidate.
    pub fn prepare_caption_content_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionContentCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.prepare_caption_content_checked(provider,texts,layouts,styles,StoredCaptionNumberRequest::None,limits,writer,now)
    }
    /// Fresh service source/proof and one joined input for all four families.
    /// Requires the complete original number stream, not inferred counters.
    /// # Errors
    /// Rejects current access/state/compiler failures, mismatched complete request
    /// identity and head movement. Does not ingest, commit, publish or retain access.
    pub fn prepare_caption_sequence_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        sequence:&NativeNumberSequenceReplacement<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionSequenceCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let content=self.prepare_caption_content_checked(provider,texts,layouts,styles,StoredCaptionNumberRequest::Sequence(sequence),limits,writer,now)?;
        let number_sequence=content.output.numbers().ok_or(StoredCaptionContentError::Binding)?.clone();
        let requested_sequence_sha256=sequence.canonical_sha256(limits)?;
        let receipt=StoredCaptionSequenceReceipt {content:content.receipt.clone(),number_sequence,requested_sequence_sha256,
            qualification:"fresh_service_source_bound_caption_content_and_complete_original_number_stream_not_native_counter_full_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        let candidate=PreparedStoredCaptionSequenceCandidate {content,receipt};
        candidate.check_binding()?;
        provider.check_head(self.source.head).map_err(StoredActualFormImportError::from)?;Ok(candidate)
    }
    fn prepare_caption_content_checked<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        numbers:StoredCaptionNumberRequest<'_,'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64,
    )->Result<PreparedStoredCaptionContentCandidate<'_>,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let state=ImportedCaptionSourceState::import(self.imported.body_structure(),limits)?;
        let output=match numbers {
            StoredCaptionNumberRequest::None=>StoredCaptionOutput::Content(proof.lower_caption_state_content_batch_candidate(&self.imported,&state,&fresh.bytes,texts,layouts,styles,limits,writer)?),
            StoredCaptionNumberRequest::Sequence(sequence)=>StoredCaptionOutput::Sequence(proof.lower_caption_state_sequence_batch_candidate(&self.imported,&state,&fresh.bytes,texts,layouts,styles,sequence,limits,writer)?),
            StoredCaptionNumberRequest::Topology(topology)=>StoredCaptionOutput::Topology(proof.lower_caption_state_topology_batch_candidate(&self.imported,&state,&fresh.bytes,texts,layouts,styles,topology,limits,writer)?),
            StoredCaptionNumberRequest::Program(program)=>StoredCaptionOutput::Program(proof.lower_caption_state_program_candidate(&self.imported,&state,&fresh.bytes,program,texts,layouts,styles,limits,writer)?),
            StoredCaptionNumberRequest::Captions(request)=>StoredCaptionOutput::Captions(proof.lower_caption_state_structure_candidate(&self.imported,&state,&fresh.bytes,request,texts,layouts,styles,limits,writer)?),
        };
        if output.receipt().output.source_package_sha256!=*fresh.digest.as_bytes(){return Err(StoredCaptionContentError::Binding);}
        let changed_text:BTreeMap<_,_>=output.receipt().output.text_changes.iter().map(|c|(&c.source_text_id,c)).collect();
        let changed_layout:BTreeMap<_,_>=output.receipt().output.layout_changes.iter().map(|c|(&c.source_caption_id,c)).collect();
        let changed_style:BTreeMap<_,_>=output.receipt().style_changes.iter().map(|c|((&c.source_node_id,c.family),c)).collect();
        let mut text_requests=Vec::new();text_requests.try_reserve_exact(output.receipt().output.requested_text_leaves).map_err(|_|StoredCaptionContentError::Binding)?;
        let mut layout_requests=Vec::new();layout_requests.try_reserve_exact(layouts.len()).map_err(|_|StoredCaptionContentError::Binding)?;
        let mut style_requests=Vec::new();style_requests.try_reserve_exact(styles.len()).map_err(|_|StoredCaptionContentError::Binding)?;
        if let StoredCaptionNumberRequest::Program(request)=numbers {
            text_requests.extend(program::generated_label_bindings(request,output.program().ok_or(StoredCaptionContentError::Binding)?,&changed_text,limits)?);
        }
        for request in texts {
            text_requests.push(StoredCaptionTextRequestBinding {source_caption_id:request.caption_id.clone(),source_text_id:request.text_id.clone(),
                requested_text_sha256:Sha256::digest(request.replacement.as_bytes()).into(),requested_text_bytes:request.replacement.len(),changed:changed_text.contains_key(request.text_id)});
        }
        for request in layouts {
            layout_requests.push(StoredCaptionLayoutRequestBinding {source_caption_id:request.caption_id.clone(),requested_layout:request.layout,changed:changed_layout.contains_key(request.caption_id)});
        }
        for request in styles {
            style_requests.push(StoredCaptionStyleRequestBinding {source_caption_id:request.caption_id.clone(),source_node_id:request.source_node_id.clone(),family:request.family,
                requested_declaration:state.frames().style_declaration(request.family,request.declaration_id),changed:changed_style.contains_key(&(request.source_node_id,request.family))});
        }
        drop(changed_text);drop(changed_layout);drop(changed_style);
        let receipt=StoredCaptionContentReceipt {source:self.receipt.clone(),text_requests,layout_requests,style_requests,output:output.receipt().clone(),
            qualification:"fresh_service_source_bound_atomic_caption_content_memory_candidate_not_effective_style_full_sequence_protection_issuer_CAS_execution_or_native",
            issuer_execution_publication_authority:false};
        if !bindings_match(&receipt){return Err(StoredCaptionContentError::Binding);}
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredCaptionContentCandidate {source:self,output,receipt})
    }
}
impl PreparedStoredCaptionContentCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionContentReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.output.source_package_sha256!=*fresh.digest.as_bytes()||!bindings_match(&self.receipt){return Err(StoredCaptionContentError::Binding);}Ok(())
    }
    /// # Errors
    /// Every call reauthorizes and reconstructs the current whole source.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionContentReceipt,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|StoredCaptionContentError::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// No consumer callback after fresh access/source/integrity/final-head failure.
    /// This final read is not atomic CAS or authority to retain plaintext access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|StoredCaptionContentError::Integrity)?
    }
    /// # Errors
    /// Still denies execution/publication after successful fresh verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionContentError::RouteUnqualified)
    }
}
impl PreparedStoredCaptionSequenceCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredCaptionSequenceReceipt {&self.receipt}
    fn check_binding(&self)->Result<(),StoredCaptionContentError> {
        let numbers=&self.receipt.number_sequence;
        if self.receipt.issuer_execution_publication_authority||numbers.execution_publication_authority||numbers.native_counter_interpretation_and_recalculation_qualified
            ||!numbers.complete_original_control_order_checked||!numbers.all_requested_values_read_back
            ||self.receipt.requested_sequence_sha256!=numbers.caller_request_sha256||self.content.output.numbers()!=Some(numbers)
            ||self.receipt.content!=self.content.receipt{return Err(StoredCaptionContentError::Binding);}Ok(())
    }
    /// # Errors
    /// Reuses the same fresh current-access/source/integrity/final-head boundary.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredCaptionSequenceReceipt,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.content.verify(provider,now)?;self.check_binding()?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// No callback after current scope/ACL/quarantine/AEAD/source/head rejection.
    /// A successful read is not CAS or authority to retain plaintext access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check_binding()?;self.content.with_verified_bytes(provider,now,consume)
    }
    /// # Errors
    /// Always denies execution/publication, including after fresh verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionContentError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(StoredCaptionContentError::RouteUnqualified)
    }
}
fn bindings_match(receipt:&StoredCaptionContentReceipt)->bool {
    let content=&receipt.output;
    if receipt.issuer_execution_publication_authority||content.execution_publication_authority||content.effective_style_and_sequence_semantics_qualified
        ||!content.input_numbering_and_frames_reused||content.source_state.numbering.source_package_sha256!=content.output.source_package_sha256
        ||receipt.style_requests.len()!=content.requested_styles
        ||!request_bindings_match(&receipt.text_requests,&receipt.layout_requests,&content.output){return false;}
    let styles:BTreeMap<_,_>=receipt.style_requests.iter().map(|r|((&r.source_node_id,r.family),r)).collect();
    let changes:BTreeMap<_,_>=content.style_changes.iter().map(|c|((&c.source_node_id,c.family),c)).collect();
    if styles.len()!=receipt.style_requests.len()||changes.len()!=content.style_changes.len()
        ||receipt.style_requests.iter().any(|r|r.changed!=changes.contains_key(&(&r.source_node_id,r.family))
            ||r.requested_declaration.reference_id.is_none()||r.requested_declaration.status!=Status::UniqueSourceDeclaration||r.requested_declaration.declaration_sha256.is_none()){return false;}
    content.style_changes.iter().all(|c|styles.get(&(&c.source_node_id,c.family)).is_some_and(|r|r.changed&&r.source_caption_id==c.source_caption_id
        &&r.requested_declaration==c.output_reference&&c.source_reference.reference_id!=c.output_reference.reference_id
        &&c.inserted_attribute==c.source_reference.reference_id.is_none()))
}
