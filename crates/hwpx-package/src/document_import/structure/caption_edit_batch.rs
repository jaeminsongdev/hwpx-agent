//! One original-bound caption text/layout transaction, not sequence or service authority.
use super::{ImportedDocumentStructure,caption_layout::CaptionLayout,
    caption_text::CaptionTextOutputError,caption_text_batch::{CaptionTextReplacement,CaptionTextBatchChange}};
use crate::{PackageArtifact,WriterError,WriterLimits};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
use serde::Serialize;
use std::fmt;

#[derive(Clone,Copy)]
pub struct CaptionLayoutReplacement<'a> {pub caption_id:&'a LogicalId,pub layout:CaptionLayout}
impl fmt::Debug for CaptionLayoutReplacement<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionLayoutReplacement(<redacted>)")}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionLayoutBatchChange {
    pub source_caption_id:LogicalId,pub source_caption_sha256:String,
    pub requested_layout:CaptionLayout,pub changed_attributes:usize,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionEditBatchOutputReceipt {
    pub qualification:&'static str,
    pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub requested_text_leaves:usize,pub requested_layouts:usize,pub changed_parts:usize,
    pub text_changes:Vec<CaptionTextBatchChange>,pub layout_changes:Vec<CaptionLayoutBatchChange>,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub id_rule_profile:&'static str,pub outside_selected_edits_exact:bool,
    #[serde(skip_serializing_if="Option::is_none")]
    pub output_review_import:Option<super::review::ReviewBodyImportReceipt>,
    pub complete_auxiliary_state_and_protection_verified:bool,pub execution_publication_authority:bool,
}
pub struct CaptionEditBatchOutputCandidate {
    pub(super) artifact:PackageArtifact,pub(super) receipt:CaptionEditBatchOutputReceipt,
    pub(in crate::document_import) style_changes:Vec<super::caption_style_batch::CaptionStyleBatchChange>,
    pub(in crate::document_import) number_sequence:Option<super::caption_numbering_sequence::NativeNumberSequenceOutputReceipt>,
    pub(in crate::document_import) number_topology:Option<super::caption_number_topology::NativeNumberTopologyOutputReceipt>,
    pub(in crate::document_import) caption_topology:Option<super::caption_topology::CaptionTopologyOutputReceipt>,
}
impl fmt::Debug for CaptionEditBatchOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionEditBatchOutputCandidate(<redacted>; not_sequence_CAS_or_service_authority)")}
}
impl CaptionEditBatchOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionEditBatchOutputReceipt {&self.receipt}
    /// Writer integrity only, never current service access or execution authority.
    /// # Errors
    /// Rejects artifact integrity failure before exposing bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
impl ImportedDocumentStructure {
    /// One original verification, numbering/frame model, protection map per part,
    /// patch/writer and complete output readback for all text and layout requests.
    /// Does not chain intermediate packages, change numbering, or write the source.
    /// # Errors
    /// Rejects any invalid/stale/foreign/protected/duplicate request, finite limit,
    /// all-no-op transaction, patch/writer failure or byte/semantic readback drift.
    pub fn lower_caption_edit_batch_candidate(&self,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],
        layouts:&[CaptionLayoutReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionEditBatchOutputCandidate,CaptionTextOutputError> {
        self.lower_caption_edit_batch_checked(fresh,texts,layouts,limits,writer,
            ||self.verify_source(fresh).map(|_|()).map_err(|_|CaptionTextOutputError::Source))
    }
}
impl crate::document_import::forms::VerifiedFormReconstruction<'_> {
    /// Reuses only a whole reconstruction bound to this exact original and bytes.
    /// # Errors
    /// Rejects foreign proof/original/bytes and every original compiler failure.
    pub fn lower_caption_edit_batch_candidate(&self,original:&crate::document_import::forms::ImportedDocumentForms,
        fresh:&[u8],texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],
        limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionEditBatchOutputCandidate,CaptionTextOutputError> {
        original.body_structure().lower_caption_edit_batch_checked(fresh,texts,layouts,limits,writer,||{
            let rebuilt=self.for_original(original).map_err(|_|CaptionTextOutputError::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(CaptionTextOutputError::Source);}Ok(())
        })
    }
}

