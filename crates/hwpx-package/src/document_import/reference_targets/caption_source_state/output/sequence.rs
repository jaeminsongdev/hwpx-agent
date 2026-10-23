//! One source-bound transaction for caption content and the complete observed
//! native control stream. Stored values are not calculated/rendered counters.
use super::{ImportedCaptionSourceState,E,content::{self,CaptionSourceStateContentOutputCandidate,CaptionSourceStateContentOutputReceipt}};
use crate::{WriterError,WriterLimits};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},structure::{
    caption_text_batch::CaptionTextReplacement,caption_edit_batch::{CaptionLayoutReplacement,CaptionEditBatchOutputCandidate},
    caption_style_batch::CaptionStyleReplacement,
    caption_numbering_sequence::{NativeNumberSequenceReplacement,NativeNumberSequenceOutputReceipt}}};
use domain_ir::ReferenceAuxiliaryLimits;
use serde::Serialize;
use std::fmt;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateSequenceOutputReceipt {
    pub content:CaptionSourceStateContentOutputReceipt,pub number_sequence:NativeNumberSequenceOutputReceipt,
    pub qualification:&'static str,pub execution_publication_authority:bool,
}
pub struct CaptionSourceStateSequenceOutputCandidate {output:CaptionSourceStateContentOutputCandidate,receipt:CaptionSourceStateSequenceOutputReceipt}
impl fmt::Debug for CaptionSourceStateSequenceOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionSourceStateSequenceOutputCandidate(<redacted>; stored_values_not_native_counter_CAS_or_service_authority)")}
}
impl CaptionSourceStateSequenceOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateSequenceOutputReceipt {&self.receipt}
    /// Writer integrity only. Never current service access or publication authority.
    /// # Errors
    /// Rejects artifact integrity failure before exposing bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.output.with_verified_bytes(consume)}
}
fn bind(state:&ImportedCaptionSourceState<'_>,output:CaptionEditBatchOutputCandidate,styles:usize)->Result<CaptionSourceStateSequenceOutputCandidate,E> {
    let number_sequence=output.number_sequence.clone().ok_or(E::Source)?;
    let output=content::bind(state,output,styles)?;
    let receipt=CaptionSourceStateSequenceOutputReceipt {content:output.receipt().clone(),number_sequence,
        qualification:"source_bound_caption_content_and_complete_original_number_control_stream_not_native_counter_interpretation_full_protection_CAS_or_service_authority",execution_publication_authority:false};
    Ok(CaptionSourceStateSequenceOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_> {
    /// Requires every original number control in exact spine/XML order plus the
    /// exact presence of document start. Retains structural topology and unknown
    /// original properties. Uses one original verification/patch/output import.
    /// # Errors
    /// Rejects missing/duplicate/reordered/foreign/stale events, wrong control
    /// kinds, invalid formats/values, protection, limits and complete readback drift.
    pub fn lower_sequence_batch_candidate(&self,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],
        styles:&[CaptionStyleReplacement<'_>],sequence:&NativeNumberSequenceReplacement<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateSequenceOutputCandidate,E> {
        let output=self.source.lower_caption_sequence_batch_using_state(fresh,texts,layouts,styles,Some(sequence),limits,writer,Some(self),
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))?;
        bind(self,output,styles.len())
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Whole proof, joined state, admission limits and fresh bytes must match
    /// the same original. The proof never becomes a retained service permission.
    /// # Errors
    /// Rejects foreign original/state/proof/bytes and every sequence compiler error.
    pub fn lower_caption_state_sequence_batch_candidate(&self,original:&ImportedDocumentForms,state:&ImportedCaptionSourceState<'_>,fresh:&[u8],
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        sequence:&NativeNumberSequenceReplacement<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateSequenceOutputCandidate,E> {
        let output=original.body_structure().lower_caption_sequence_batch_using_state(fresh,texts,layouts,styles,Some(sequence),limits,writer,Some(state),||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })?;
        bind(state,output,styles.len())
    }
}
