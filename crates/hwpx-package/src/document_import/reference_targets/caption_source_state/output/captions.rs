//! Whole-caption topology candidates, not stored access or Native authority.
use super::{ImportedCaptionSourceState,E,content::{self,CaptionSourceStateContentOutputCandidate,CaptionSourceStateContentOutputReceipt}};
use crate::{WriterError,WriterLimits};
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},structure::{caption_topology::{SourceCaptionTopologyRequest,CaptionTopologyOutputReceipt},
    caption_edit_batch::{CaptionEditBatchOutputCandidate,CaptionLayoutReplacement},caption_text_batch::CaptionTextReplacement,caption_style_batch::CaptionStyleReplacement}};
use domain_ir::ReferenceAuxiliaryLimits;
use serde::Serialize;
use std::fmt;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionSourceStateStructureOutputReceipt {pub content:CaptionSourceStateContentOutputReceipt,pub caption_topology:CaptionTopologyOutputReceipt,pub execution_publication_authority:bool}
pub struct CaptionSourceStateStructureOutputCandidate {output:CaptionSourceStateContentOutputCandidate,receipt:CaptionSourceStateStructureOutputReceipt}
impl fmt::Debug for CaptionSourceStateStructureOutputCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CaptionSourceStateStructureOutputCandidate(<redacted>; not_native_or_service_authority)")}}
impl CaptionSourceStateStructureOutputCandidate {
    #[must_use] pub const fn receipt(&self)->&CaptionSourceStateStructureOutputReceipt{&self.receipt}
    /// Writer integrity only, not current service access or publication.
    /// # Errors
    /// Rejects artifact integrity failures before exposing candidate bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.output.with_verified_bytes(consume)}
}
fn bind(state:&ImportedCaptionSourceState<'_>,output:CaptionEditBatchOutputCandidate,styles:usize)->Result<CaptionSourceStateStructureOutputCandidate,E>{
    let caption_topology=output.caption_topology.clone().ok_or(E::Source)?;
    if !caption_topology.complete_owner_caption_and_native_control_inventory_read_back||caption_topology.source_joined_state_sha256!=state.receipt().joined_state_sha256{return Err(E::Readback);}
    let output=content::bind(state,output,styles)?;let receipt=CaptionSourceStateStructureOutputReceipt {content:output.receipt().clone(),caption_topology,execution_publication_authority:false};
    Ok(CaptionSourceStateStructureOutputCandidate {output,receipt})
}
impl ImportedCaptionSourceState<'_>{
    /// One verified original, typed caption creation/deletion and retained
    /// text/layout/style transaction, followed by a complete output inventory.
    /// # Errors
    /// Rejects source/selection/protection/style/ID/overlap/limit/readback failures.
    pub fn lower_caption_structure_candidate(&self,fresh:&[u8],request:&SourceCaptionTopologyRequest<'_>,texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits)
        ->Result<CaptionSourceStateStructureOutputCandidate,E>{
        let output=self.source.lower_caption_structure_batch_using_state(fresh,texts,layouts,styles,None,None,Some(request),limits,writer,Some(self),||self.verify_source(fresh).map(|_|()).map_err(|_|E::Source))?;
        bind(self,output,styles.len())
    }
}
impl VerifiedFormReconstruction<'_>{
    /// Only the operation-local whole Form proof for this exact original/state.
    /// # Errors
    /// Rejects foreign original/state/proof/bytes and every compiler failure.
    pub fn lower_caption_state_structure_candidate(&self,original:&ImportedDocumentForms,state:&ImportedCaptionSourceState<'_>,fresh:&[u8],request:&SourceCaptionTopologyRequest<'_>,texts:&[CaptionTextReplacement<'_>],layouts:&[CaptionLayoutReplacement<'_>],styles:&[CaptionStyleReplacement<'_>],limits:ReferenceAuxiliaryLimits,writer:WriterLimits)
        ->Result<CaptionSourceStateStructureOutputCandidate,E>{
        let output=original.body_structure().lower_caption_structure_batch_using_state(fresh,texts,layouts,styles,None,None,Some(request),limits,writer,Some(state),||{
            let rebuilt=self.for_original(original).map_err(|_|E::Source)?;if fresh!=rebuilt.source().original.as_ref(){return Err(E::Source);}Ok(())
        })?;bind(state,output,styles.len())
    }
}
