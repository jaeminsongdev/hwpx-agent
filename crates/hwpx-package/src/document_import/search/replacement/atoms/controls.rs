//! Exact observed control anchors, whole atomic control coverage, original protections and byte readback.
mod plan;
use super::*;
use crate::document_import::{search::{inspection::SourceControlKind,selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},
    reviews::{SourceReviewTextPolicy,selector::{SourceReviewScopeIndex,controls::SourceReviewSelectorControlResult}}},structure::review::ImportedDocumentReviewBodies};
use thiserror::Error;
pub const SOURCE_CONTROL_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-text-control-replacement/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceControlReplacementError {
    #[error("SOURCE_CONTROL_REPLACEMENT_KIND_UNQUALIFIED")] UnsupportedKind,
    #[error("SOURCE_CONTROL_REPLACEMENT_REJECTED:{0}")] Output(#[from] SourceLiteralReplacementError),
}
type C=SourceControlReplacementError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceControlAtomChange {
    pub source_control_anchor:SourceAnchorHandle,pub original_atom:u32,pub original_kind:SourceControlKind,
    pub output_atoms:usize,pub output_semantic_sha256:[u8;32],
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceControlReplacementReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,pub kind:SourceControlKind,pub search:SourceReviewSelectorControlResult,
    pub replacement_sha256:[u8;32],pub replacement_atoms:usize,pub replacement_text_bytes:usize,pub request_sha256:[u8;32],
    pub selected_controls:usize,pub changed_controls:usize,pub changes:Vec<SourceControlAtomChange>,
    pub span_changes:Vec<SourceReplacementTextSpanChange>,pub changed_parts:usize,pub rendered_replacement_bytes:usize,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub source_review_import:review::ReviewBodyImportReceipt,pub output_review_import:review::ReviewBodyImportReceipt,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub whole_atomic_control_selection_verified:bool,
    pub original_text_run_shells_styles_references_and_outside_control_bytes_preserved:bool,
    pub output_spans_and_exact_outside_edits_verified:bool,pub full_control_contract_native_service_or_execution_authority:bool,
}
pub struct SourceControlReplacementCandidate {artifact:PackageArtifact,receipt:SourceControlReplacementReceipt}
impl fmt::Debug for SourceControlReplacementCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("SourceControlReplacementCandidate(<redacted>; exact_text_controls_not_full_control_or_execution_authority)")}}
impl SourceControlReplacementCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceControlReplacementReceipt{&self.receipt}
    /// # Errors
    /// Pure writer integrity, not current service access, a revision commit or Native qualification.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
fn qualified(kind:SourceControlKind)->Result<crate::TextControlKind,C>{match kind{
    SourceControlKind::Tab=>Ok(crate::TextControlKind::Tab),SourceControlKind::LineBreak=>Ok(crate::TextControlKind::LineBreak),_=>Err(C::UnsupportedKind)}}
/// Immutable validated parameters only. No source identity, current access or execution grant.
pub struct ValidatedTextControlOutput<'a>{kind:SourceControlKind,expected:crate::TextControlKind,output:&'a [TextAtom],
    limits:SourceSearchLimits,validated:([u8;32],usize)}
impl fmt::Debug for ValidatedTextControlOutput<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("ValidatedTextControlOutput(<redacted>; parameters_not_source_or_execution_authority)")}}
impl<'a> ValidatedTextControlOutput<'a>{
    /// # Errors
    /// Bind a borrowed immutable payload and finite limits, checking kind/value/hash once.
    pub fn new(kind:SourceControlKind,output:&'a [TextAtom],limits:SourceSearchLimits)->Result<Self,C>{
        let expected=qualified(kind)?;let validated=plan::validate_output(output,limits)?;Ok(Self{kind,expected,output,limits,validated})
    }
    #[must_use] pub const fn kind(&self)->SourceControlKind{self.kind}
    #[must_use] pub const fn replacement_sha256(&self)->[u8;32]{self.validated.0}
    #[must_use] pub fn output_atoms(&self)->usize{self.output.len()}
    #[must_use] pub const fn text_bytes(&self)->usize{self.validated.1}
    /// # Errors
    /// A fresh original proof is still required; this value cannot bypass any compiler guard.
    pub fn lower(&self,proof:&VerifiedFormReconstruction<'_>,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        max_results:usize,writer:WriterLimits)->Result<SourceControlReplacementCandidate,C>{
        proof.lower_control_validated(original,selector,body,self.kind,max_results,self.output,self.limits,writer,self.expected,self.validated)
    }
}
impl ImportedDocumentForms {
    /// # Errors
    /// Observed Tab/LineBreak controls in four exact original scopes, never raw XML or caller anchors.
    pub fn lower_review_selector_control_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,output:&[TextAtom],limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceControlReplacementCandidate,C>{
        let expected=qualified(kind)?;let validated=plan::validate_output(output,limits)?;
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_control_validated(self,selector,body_policy,kind,max_results,output,limits,writer,expected,validated)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Reuse one original proof/index/selector/matcher and sparse output verifier. Other kinds stay unavailable.
    pub fn lower_review_selector_control_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,output:&[TextAtom],limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceControlReplacementCandidate,C>{
        let expected=qualified(kind)?;let validated=plan::validate_output(output,limits)?;
        self.lower_control_validated(original,selector,body_policy,kind,max_results,output,limits,writer,expected,validated)
    }
    fn lower_control_validated(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,output:&[TextAtom],limits:SourceSearchLimits,writer:WriterLimits,
        expected:crate::TextControlKind,validated:([u8;32],usize))->Result<SourceControlReplacementCandidate,C>{
        let(replacement_sha256,replacement_text_bytes)=validated;
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits).map_err(E::from)?;
        let(search,windows)=index.find_control_with_windows(selector,body_policy,kind,max_results).map_err(E::from)?;
        if search.controls().is_empty(){return Err(E::NoMatches.into());}
        let text=index.source_index();let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,body_policy)?;
        let plan=plan::compile(text,&fields,&context,&search,&windows,expected,output,replacement_sha256)?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=whitespace::readback::verify(text.original.source(),&artifact,&plan.spans,&context)?;
        let mut binding=Output{bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_CONTROL_REPLACEMENT_PROFILE,search.request_sha256(),replacement_sha256,output.len())).map_err(|_|E::Limit)?;
        let receipt=SourceControlReplacementReceipt{profile:SOURCE_CONTROL_REPLACEMENT_PROFILE,source_package_sha256:text.original.source().receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),body_policy,kind,selected_controls:search.controls().len(),search,
            replacement_sha256,replacement_atoms:output.len(),replacement_text_bytes,request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),
            changed_controls:plan.changes.len(),changes:plan.changes,span_changes:plan.span_changes,changed_parts:plan.spans.len(),rendered_replacement_bytes:plan.bytes,
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,source_review_import:review.receipt().clone(),output_review_import:output_review,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),whole_atomic_control_selection_verified:true,
            original_text_run_shells_styles_references_and_outside_control_bytes_preserved:true,output_spans_and_exact_outside_edits_verified:true,
            full_control_contract_native_service_or_execution_authority:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceControlReplacementCandidate{artifact,receipt})
    }
}
