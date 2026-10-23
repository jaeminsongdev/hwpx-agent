//! Typed number-control insertion/deletion with complete source/output binding.
use super::{ImportedCaptionSourceState,E,content::{self,CaptionSourceStateContentOutputCandidate,CaptionSourceStateContentOutputReceipt}};
use crate::{WriterError,WriterLimits};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},structure::{
    caption_text_batch::CaptionTextReplacement,caption_edit_batch::{CaptionLayoutReplacement,CaptionEditBatchOutputCandidate},
    caption_style_batch::CaptionStyleReplacement,caption_number_topology::{NativeNumberTopologyRequest,NativeNumberTopologyOutputReceipt}}};
use domain_ir::ReferenceAuxiliaryLimits;
use serde::Serialize;
use std::fmt;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateTopologyOutputReceipt {
    pub content:CaptionSourceStateContentOutputReceipt,pub number_topology:NativeNumberTopologyOutputReceipt,
    pub qualification:&'static str,pub execution_publication_authority:bool,
}
pub struct CaptionSourceStateTopologyOutputCandidate {output:CaptionSourceStateContentOutputCandidate,receipt:CaptionSourceStateTopologyOutputReceipt}
impl fmt::Debug for CaptionSourceStateTopologyOutputCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionSourceStateTopologyOutputCandidate(<redacted>; not_counter_native_CAS_or_service_authority)")}
}
impl CaptionSourceStateTopologyOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateTopologyOutputReceipt {&self.receipt}
    /// Writer integrity only; no service access or publication authorization.
    /// # Errors
    /// Rejects integrity failure before exposing candidate bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.output.with_verified_bytes(consume)}
}
fn bind(state:&ImportedCaptionSourceState<'_>,output:CaptionEditBatchOutputCandidate,styles:usize)->Result<CaptionSourceStateTopologyOutputCandidate,E> {
    let number_topology=output.number_topology.clone().ok_or(E::Source)?;
    if !number_topology.complete_original_and_inserted_inventory_read_back{return Err(E::Readback);}
    let output=content::bind(state,output,styles)?;
    let receipt=CaptionSourceStateTopologyOutputReceipt {content:output.receipt().clone(),number_topology,
        qualification:"source_bound_caption_content_and_number_control_topology_not_native_counter_full_protection_CAS_or_service_authority",execution_publication_authority:false};
    Ok(CaptionSourceStateTopologyOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_> {
    /// One source verification, transaction and output import; no caller XML,
    /// inferred number defaults or retained service permission.
    /// # Errors
    /// Rejects stale/foreign/duplicate/protected/unsupported selections, limits,
    /// overlap, illegal output structure and complete inventory readback drift.
    pub fn lower_topology_batch_candidate(&self,fresh:&[u8],texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],
        styles:&[CaptionStyleReplacement<'_>],topology:&NativeNumberTopologyRequest<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateTopologyOutputCandidate,E> {
        let output=self.source.lower_caption_topology_batch_using_state(fresh,texts,layouts,styles,None,Some(topology),limits,writer,Some(self),
            ||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))?;
        bind(self,output,styles.len())
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Only a whole proof tied to the exact original, state, limits and bytes.
    /// # Errors
    /// Rejects foreign proof/original/state/bytes and every topology compiler error.
    pub fn lower_caption_state_topology_batch_candidate(&self,original:&ImportedDocumentForms,state:&ImportedCaptionSourceState<'_>,fresh:&[u8],
        texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],
        topology:&NativeNumberTopologyRequest<'_>,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,
    )->Result<CaptionSourceStateTopologyOutputCandidate,E> {
        let output=original.body_structure().lower_caption_topology_batch_using_state(fresh,texts,layouts,styles,None,Some(topology),limits,writer,Some(state),||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
            if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })?;
        bind(state,output,styles.len())
    }
}
