//! Actual original-scalar normalization, not normalization of the search index alone.
pub(super) mod transform;
pub(in crate::document_import) mod plan;
pub mod matches;
use super::*;
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},
    reviews::{SourceReviewTextPolicy,selector::SourceReviewScopeIndex}},structure::review::ImportedDocumentReviewBodies};
use serde::Deserialize;
pub const SOURCE_UNICODE_NORMALIZATION_PROFILE:&str="hwpx-agent.source-selector-unicode-normalization/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceUnicodeNormalizationForm {Nfc,Nfd,Nfkc,Nfkd}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceUnicodeNormalizationReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,pub form:SourceUnicodeNormalizationForm,pub unicode_version:(u8,u8,u8),
    pub run_policy:SourceReplacementRunPolicy,pub request_sha256:[u8;32],pub selected_original_scalars:usize,
    pub excluded_hidden_paragraphs:usize,pub excluded_memo_paragraphs:usize,pub normalized_text_groups:usize,
    pub decomposed_scalars:usize,pub changed_components:usize,pub changed_scalar_ranges:usize,
    pub changes:Vec<SourceReplacementTextSpanChange>,pub changed_parts:usize,pub observed_protection_parts:usize,
    pub observed_protection_element_visits:usize,pub source_review_import:review::ReviewBodyImportReceipt,
    pub output_review_import:review::ReviewBodyImportReceipt,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub exact_original_selection_verified:bool,pub unchanged_components_keep_original_placement:bool,
    pub original_controls_and_all_reference_shells_preserved:bool,pub independent_normalization_oracle_verified:bool,
    pub output_text_spans_and_outside_slots_verified:bool,pub full_contract_native_service_or_execution_authority:bool,
}
pub struct SourceUnicodeNormalizationCandidate {artifact:PackageArtifact,receipt:SourceUnicodeNormalizationReceipt}
impl fmt::Debug for SourceUnicodeNormalizationCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("SourceUnicodeNormalizationCandidate(<redacted>; source_candidate_not_execution_authority)")}}
impl SourceUnicodeNormalizationCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceUnicodeNormalizationReceipt {&self.receipt}
    /// # Errors
    /// Writer integrity only; not a current service access check, commit, or Native qualification.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Normalize exact selected original text, with an explicit form and first-contributor run policy.
    /// Controls and existing source-block boundaries are immutable normalization barriers.
    pub fn lower_review_selector_unicode_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        form:SourceUnicodeNormalizationForm,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceUnicodeNormalizationCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_selector_unicode_candidate(self,selector,policy,form,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One exact original proof, field/review/index, preserving transaction and output import.
    pub fn lower_review_selector_unicode_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        form:SourceUnicodeNormalizationForm,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceUnicodeNormalizationCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(selector,windows,hidden,memo)=index.transformation_windows(selector,policy)?;let text=index.source_index();
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let plan=plan::compile(text,&fields,&context,&windows,form)?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify_artifact(text.original.source(),&artifact,&plan.spans,Some(&context))?.ok_or(E::Readback)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_UNICODE_NORMALIZATION_PROFILE,text.receipt.index_sha256,&selector,policy,form,
            run_policy,unicode_normalization::UNICODE_VERSION)).map_err(|_|E::Limit)?;
        let receipt=SourceUnicodeNormalizationReceipt {profile:SOURCE_UNICODE_NORMALIZATION_PROFILE,
            source_package_sha256:text.original.source().receipt().source_package_sha256,source_index_sha256:text.receipt.index_sha256,
            selector,body_policy:policy,form,unicode_version:unicode_normalization::UNICODE_VERSION,run_policy,
            request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),selected_original_scalars:plan.selected,
            excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,normalized_text_groups:plan.groups,decomposed_scalars:plan.decomposed,
            changed_components:plan.components,changed_scalar_ranges:plan.ranges,changes:plan.changes,changed_parts:plan.spans.len(),
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,
            source_review_import:review.receipt().clone(),output_review_import:output_review,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),exact_original_selection_verified:true,
            unchanged_components_keep_original_placement:true,original_controls_and_all_reference_shells_preserved:true,
            independent_normalization_oracle_verified:true,output_text_spans_and_outside_slots_verified:true,full_contract_native_service_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceUnicodeNormalizationCandidate {artifact,receipt})
    }
}
