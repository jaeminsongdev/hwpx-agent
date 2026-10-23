//! Exact original-state input reuse for caption compilation, not cached authorization.
pub mod content;
pub mod sequence;
pub mod topology;
pub mod program;
pub mod captions;
use super::{ImportedCaptionSourceState,CaptionSourceStateReceipt};
use crate::{WriterError,WriterLimits};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},
    structure::{caption_text::CaptionTextOutputError as E,caption_text_batch::CaptionTextReplacement,
        caption_edit_batch::{CaptionLayoutReplacement,CaptionEditBatchOutputCandidate,CaptionEditBatchOutputReceipt}}};
use domain_ir::ReferenceAuxiliaryLimits;
use serde::Serialize;
use std::fmt;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateOutputReceipt {
    pub source_state:CaptionSourceStateReceipt,pub output:CaptionEditBatchOutputReceipt,
    pub input_numbering_and_frames_reused:bool,
    pub execution_publication_authority:bool,
}
pub struct CaptionSourceStateOutputCandidate {
    output:CaptionEditBatchOutputCandidate,receipt:CaptionSourceStateOutputReceipt,
}
impl fmt::Debug for CaptionSourceStateOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionSourceStateOutputCandidate(<redacted>; not_sequence_CAS_or_service_authority)")}
}
impl CaptionSourceStateOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateOutputReceipt {&self.receipt}
    /// Writer integrity only. A source-state receipt is not current service access.
    /// # Errors
    /// Rejects artifact integrity failure before exposing bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
fn bind(state:&ImportedCaptionSourceState<'_>,output:CaptionEditBatchOutputCandidate)->Result<CaptionSourceStateOutputCandidate,E> {
    if output.receipt().source_package_sha256!=state.receipt().numbering.source_package_sha256{return Err(E::Source);}
    let receipt=CaptionSourceStateOutputReceipt {source_state:state.receipt().clone(),output:output.receipt().clone(),
        input_numbering_and_frames_reused:true,execution_publication_authority:false};
    Ok(CaptionSourceStateOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_> {
    /// Verifies the whole fresh original, then reuses this exact immutable input
    /// numbering/frames in the common compiler. Full output import/readback stays.
    /// # Errors
    /// Rejects source drift, limits different from this state's admission scope,
    /// and every original selection/protection/value/patch/writer/readback failure.
    pub fn lower_edit_batch_candidate(&self,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateOutputCandidate,E> {
        let output=self.source.lower_caption_edit_batch_using_state(fresh,texts,layouts,limits,writer,Some(self),
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))?;
        bind(self,output)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Operation-local whole Form proof and assembled models must refer to the
    /// same exact original object, admission limits and fresh bytes. No new input
    /// import, caller-supplied graph, trusted flag or saved service authorization.
    /// # Errors
    /// Rejects foreign original/state/proof/bytes or any common compiler failure.
    pub fn lower_caption_state_edit_batch_candidate(&self,original:&ImportedDocumentForms,
        state:&ImportedCaptionSourceState<'_>,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateOutputCandidate,E> {
        let output=original.body_structure().lower_caption_edit_batch_using_state(fresh,texts,layouts,limits,writer,Some(state),||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })?;
        bind(state,output)
    }
}

