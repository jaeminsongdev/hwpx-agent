//! Explicit whitespace policies on exact original matches, including typed tab/lineBreak atoms.
pub(super) mod plan;
pub(super) mod readback;
pub(super) mod lexical;
use super::*;
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},
    reviews::{SourceReviewTextPolicy,selector::{SourceReviewScopeIndex,styles::SourceReviewStyleFilter}}},structure::review::ImportedDocumentReviewBodies};
use serde::Deserialize;
pub use super::unicode::matches::SourceUnicodeMatchSearch as SourceWhitespaceMatchSearch;
pub const SOURCE_WHITESPACE_NORMALIZATION_PROFILE:&str="hwpx-agent.source-match-whitespace-normalization/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceWhitespaceTextPolicy {None,AsciiSpace,Unicode17Breaking,Unicode17AllModelAdmitted}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceWhitespaceSequencePolicy {CollapseEachMatchedSequence,EachOriginalScalar}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case",deny_unknown_fields)]
pub enum SourceWhitespaceOutput {Spaces{count:u16},Tab{width:u32,leader:u32,tab_type:u32},LineBreak,Remove}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceWhitespacePolicy {
    pub text:SourceWhitespaceTextPolicy,pub tabs:bool,pub line_breaks:bool,
    pub sequence:SourceWhitespaceSequencePolicy,pub output:SourceWhitespaceOutput,
}
impl SourceWhitespacePolicy {
    /// # Errors
    /// A finite explicit policy; no implicit NBSP, raw control, paragraph merge or Native semantics.
    pub fn validate(self)->Result<(),E>{
        if self.text==SourceWhitespaceTextPolicy::None&&!self.tabs&&!self.line_breaks{return Err(E::Value);}
        if matches!(self.output,SourceWhitespaceOutput::Spaces{count}if count==0||count>1024){return Err(E::Value);}Ok(())
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceWhitespaceNormalizationReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,
    #[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::optional_review")]
    pub filter:Option<SourceReviewStyleFilter>,pub policy:SourceWhitespacePolicy,
    pub run_policy:SourceReplacementRunPolicy,pub search:SourceWhitespaceMatchSearch,pub request_sha256:[u8;32],
    pub selected_original_scalars:usize,pub whitespace_sequences:usize,pub changed_scalar_ranges:usize,
    pub changed_original_controls:usize,pub changed_parts:usize,pub changes:Vec<SourceReplacementTextSpanChange>,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub source_review_import:review::ReviewBodyImportReceipt,pub output_review_import:review::ReviewBodyImportReceipt,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub exact_original_selection_verified:bool,
    pub original_run_shells_styles_references_and_non_whitespace_preserved:bool,
    pub output_uses_first_original_contributor:bool,pub output_spans_and_exact_outside_edits_verified:bool,
    pub full_contract_native_service_or_execution_authority:bool,
}
pub struct SourceWhitespaceNormalizationCandidate {artifact:PackageArtifact,receipt:SourceWhitespaceNormalizationReceipt}
impl fmt::Debug for SourceWhitespaceNormalizationCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("SourceWhitespaceNormalizationCandidate(<redacted>; not_service_native_or_execution_authority)")}}
impl SourceWhitespaceNormalizationCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceWhitespaceNormalizationReceipt{&self.receipt}
    /// # Errors
    /// Pure writer integrity, not current service authorization, a revision commit or Native proof.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Normalize exact matched original whitespace; non-selected controls and paragraph/run shells stay exact.
    pub fn lower_review_selector_whitespace_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body_policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,policy:SourceWhitespacePolicy,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceWhitespaceNormalizationCandidate,E>{
        policy.validate()?;self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_selector_whitespace_candidate(self,query,selector,body_policy,filter,policy,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One proof/field/review/index/matcher/writer; sparse lexical readback permits only planned control changes.
    pub fn lower_review_selector_whitespace_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        body_policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,policy:SourceWhitespacePolicy,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceWhitespaceNormalizationCandidate,E>{
        policy.validate()?;let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let found=if let Some(filter)=filter.as_ref(){SourceWhitespaceMatchSearch::Style(index.find_style(query,selector,body_policy,filter.clone())?)}
            else{SourceWhitespaceMatchSearch::Text(index.find(query,selector,body_policy)?)};
        let search=found.search();let text=index.source_index();if search.result().matches().is_empty(){return Err(E::NoMatches);}
        let mut groups=Vec::new();let mut selected=BTreeSet::new();
        for m in search.result().matches(){let origins=selected_origins(text,m)?;
            for &origin in &origins{if !selected.insert(origin){return Err(E::Selection);}}groups.push(origins.into_iter().collect());}
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,body_policy)?;
        let plan=plan::compile(text,&fields,&context,groups,&selected,policy)?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify(text.original.source(),&artifact,&plan.spans,&context)?;
        let mut binding=Output{bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_WHITESPACE_NORMALIZATION_PROFILE,search.request_sha256(),&filter,policy,run_policy)).map_err(|_|E::Limit)?;
        let receipt=SourceWhitespaceNormalizationReceipt{profile:SOURCE_WHITESPACE_NORMALIZATION_PROFILE,source_package_sha256:text.original.source().receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),body_policy,filter,policy,run_policy,search:found,
            request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),selected_original_scalars:selected.len(),whitespace_sequences:plan.sequences,
            changed_scalar_ranges:plan.ranges,changed_original_controls:plan.controls,changed_parts:plan.spans.len(),changes:plan.changes,
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,source_review_import:review.receipt().clone(),output_review_import:output_review,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),exact_original_selection_verified:true,
            original_run_shells_styles_references_and_non_whitespace_preserved:true,output_uses_first_original_contributor:true,
            output_spans_and_exact_outside_edits_verified:true,full_contract_native_service_or_execution_authority:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceWhitespaceNormalizationCandidate{artifact,receipt})
    }
}
