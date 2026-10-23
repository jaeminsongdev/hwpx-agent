//! Normalize exact original contributors of bounded literal/regex/style matches, never index text.
use super::*;
use crate::document_import::search::reviews::selector::{SourceReviewSelectorResult,
    styles::{SourceReviewStyleFilter,SourceReviewSelectorStyleResult}};
pub const SOURCE_UNICODE_MATCH_PROFILE:&str="hwpx-agent.source-match-unicode-normalization/v1";
pub const SOURCE_UNICODE_MATCH_OUTPUT_PROFILE:&str="hwpx-agent.source-selector-unicode-normalization/v2";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",content="result",rename_all="snake_case")]
pub enum SourceUnicodeMatchSearch {Text(SourceReviewSelectorResult),Style(SourceReviewSelectorStyleResult)}
impl SourceUnicodeMatchSearch {
    #[must_use] pub const fn search(&self)->&SourceReviewSelectorResult {match self {Self::Text(r)=>r,Self::Style(r)=>r.search()}}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceUnicodeMatchReceipt {
    pub profile:&'static str,
    #[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::optional_review")]
    pub filter:Option<SourceReviewStyleFilter>,pub search:SourceUnicodeMatchSearch,
    pub request_sha256:[u8;32],pub output:SourceUnicodeNormalizationReceipt,pub full_contract_native_service_or_execution_authority:bool,
}
pub struct SourceUnicodeMatchCandidate {inner:SourceUnicodeNormalizationCandidate,receipt:SourceUnicodeMatchReceipt}
impl fmt::Debug for SourceUnicodeMatchCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("SourceUnicodeMatchCandidate(<redacted>; exact_source_matches_not_full_contract)")}}
impl SourceUnicodeMatchCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceUnicodeMatchReceipt {&self.receipt}
    /// # Errors
    /// Pure writer integrity, not current service access, CAS or Native qualification.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.inner.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// One original proof/index/matcher; explicit source-axis filter, not inferred effective styles.
    pub fn lower_review_selector_unicode_matches(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceUnicodeMatchCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_selector_unicode_matches(self,query,selector,policy,filter,form,run,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Matches retain their original source binding and remain separate normalization groups.
    /// Reject zero-width/partial inverse/overlap before writing, including protected noops.
    pub fn lower_review_selector_unicode_matches(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,form:SourceUnicodeNormalizationForm,run:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceUnicodeMatchCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let found=if let Some(filter)=filter.as_ref() {SourceUnicodeMatchSearch::Style(index.find_style(query,selector,policy,filter.clone())?)}
            else{SourceUnicodeMatchSearch::Text(index.find(query,selector,policy)?)};
        let search=found.search();let text=index.source_index();
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let plan=plan::compile_found(text,&fields,&context,search.result(),form)?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify_artifact(text.original.source(),&artifact,&plan.spans,Some(&context))?.ok_or(E::Readback)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_UNICODE_MATCH_PROFILE,search.request_sha256(),&filter,form,run,unicode_normalization::UNICODE_VERSION)).map_err(|_|E::Limit)?;
        let request_sha256=Sha256::digest(binding.bytes.ok_or(E::Limit)?).into();let(hidden,memo)=search.transformation_exclusions();
        let output=SourceUnicodeNormalizationReceipt {profile:SOURCE_UNICODE_MATCH_OUTPUT_PROFILE,
            source_package_sha256:text.original.source().receipt().source_package_sha256,source_index_sha256:text.receipt.index_sha256,
            selector:search.scope_receipt().clone(),body_policy:policy,form,unicode_version:unicode_normalization::UNICODE_VERSION,run_policy:run,
            request_sha256,selected_original_scalars:plan.selected,excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,
            normalized_text_groups:plan.groups,decomposed_scalars:plan.decomposed,changed_components:plan.components,changed_scalar_ranges:plan.ranges,
            changes:plan.changes,changed_parts:plan.spans.len(),observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,
            source_review_import:review.receipt().clone(),output_review_import:output_review,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            exact_original_selection_verified:true,unchanged_components_keep_original_placement:true,original_controls_and_all_reference_shells_preserved:true,
            independent_normalization_oracle_verified:true,output_text_spans_and_outside_slots_verified:true,full_contract_native_service_or_execution_authority:false};
        let receipt=SourceUnicodeMatchReceipt {profile:SOURCE_UNICODE_MATCH_PROFILE,filter,search:found,request_sha256,output:output.clone(),full_contract_native_service_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceUnicodeMatchCandidate {inner:SourceUnicodeNormalizationCandidate {artifact,receipt:output},receipt})
    }
}
