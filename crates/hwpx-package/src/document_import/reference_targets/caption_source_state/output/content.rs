//! Atomic text/layout/declared-style compilation over one exact source state.
use super::{ImportedCaptionSourceState,CaptionSourceStateReceipt,E};
use crate::{WriterError,WriterLimits};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},
    structure::{caption_text_batch::CaptionTextReplacement,
        caption_edit_batch::{CaptionLayoutReplacement,CaptionEditBatchOutputCandidate,CaptionEditBatchOutputReceipt},
        caption_style_batch::{CaptionStyleReplacement,CaptionStyleBatchChange}}};
use domain_ir::ReferenceAuxiliaryLimits;
use serde::Serialize;
use std::fmt;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateContentOutputReceipt {
    pub qualification:&'static str,
    pub source_state:CaptionSourceStateReceipt,pub output:CaptionEditBatchOutputReceipt,
    pub requested_styles:usize,pub style_changes:Vec<CaptionStyleBatchChange>,
    pub input_numbering_and_frames_reused:bool,
    pub effective_style_and_sequence_semantics_qualified:bool,
    pub execution_publication_authority:bool,
}
pub struct CaptionSourceStateContentOutputCandidate {
    output:CaptionEditBatchOutputCandidate,receipt:CaptionSourceStateContentOutputReceipt,
}
impl fmt::Debug for CaptionSourceStateContentOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionSourceStateContentOutputCandidate(<redacted>; not_effective_style_sequence_CAS_or_service_authority)")}
}
impl CaptionSourceStateContentOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateContentOutputReceipt {&self.receipt}
    /// Writer integrity only, not current service access or publication authority.
    /// # Errors
    /// Rejects artifact integrity failure before exposing bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
pub(super) fn bind(state:&ImportedCaptionSourceState<'_>,output:CaptionEditBatchOutputCandidate,requested_styles:usize)
    ->Result<CaptionSourceStateContentOutputCandidate,E> {
    if output.receipt().source_package_sha256!=state.receipt().numbering.source_package_sha256{return Err(E::Source);}
    let receipt=CaptionSourceStateContentOutputReceipt {
        qualification:"source_bound_atomic_caption_content_declared_style_references_not_effective_style_sequence_full_protection_native_CAS_or_service_authority",
        source_state:state.receipt().clone(),output:output.receipt().clone(),requested_styles,style_changes:output.style_changes.clone(),
        input_numbering_and_frames_reused:true,effective_style_and_sequence_semantics_qualified:false,execution_publication_authority:false};
    Ok(CaptionSourceStateContentOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_> {
    /// Reuses exact original models and one transaction/output import. Style
    /// targets must be unique declarations in the original header; no guessed
    /// inherited formatting, new declarations, source overwrite or authorization.
    /// # Errors
    /// Rejects foreign/stale/wrong-family/duplicate/protected requests, ambiguous
    /// declarations, admission drift, finite limits, all-no-op and readback drift.
    pub fn lower_content_batch_candidate(&self,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateContentOutputCandidate,E> {
        let output=self.source.lower_caption_content_batch_using_state(fresh,texts,layouts,styles,limits,writer,Some(self),
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))?;
        bind(self,output,styles.len())
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Reuses only an operation-local whole Form proof tied to this exact
    /// original object, admitted state and fresh bytes. Not saved service access.
    /// # Errors
    /// Rejects foreign original/state/proof/bytes and all content compiler errors.
    pub fn lower_caption_state_content_batch_candidate(&self,original:&ImportedDocumentForms,
        state:&ImportedCaptionSourceState<'_>,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateContentOutputCandidate,E> {
        let output=original.body_structure().lower_caption_content_batch_using_state(fresh,texts,layouts,styles,limits,writer,Some(state),||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })?;
        bind(state,output,styles.len())
    }
}
