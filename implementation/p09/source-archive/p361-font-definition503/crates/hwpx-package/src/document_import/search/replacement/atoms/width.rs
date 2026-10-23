//! Explicit Unicode17 width pairs and kana pairs on original matches, not general normalization.
mod table;
mod mapping;
use super::*;
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},
    reviews::{SourceReviewTextPolicy,selector::{SourceReviewScopeIndex,styles::SourceReviewStyleFilter}}},structure::review::ImportedDocumentReviewBodies};
pub use super::unicode::matches::SourceUnicodeMatchSearch as SourceWidthMatchSearch;
use serde::Deserialize;
pub const SOURCE_WIDTH_CONVERSION_PROFILE:&str="hwpx-agent.source-match-width-conversion/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceWidthMode {Fullwidth,Halfwidth}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceWidthPolicy {Unicode17WidthPairsWithKanaPairs}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceWidthConversionReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub mode:SourceWidthMode,pub policy:SourceWidthPolicy,pub run_policy:SourceReplacementRunPolicy,
    pub width_unicode_version:(u8,u8,u8),pub mapping_source_sha256:&'static str,pub width_pair_count:usize,pub kana_pair_count:usize,
    pub body_policy:SourceReviewTextPolicy,pub filter:Option<SourceReviewStyleFilter>,pub search:SourceWidthMatchSearch,pub request_sha256:[u8;32],
    pub selected_original_scalars:usize,pub converted_text_groups:usize,pub mapped_scalars:usize,pub changed_components:usize,
    pub changed_scalar_ranges:usize,pub changes:Vec<SourceReplacementTextSpanChange>,pub changed_parts:usize,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub source_review_import:review::ReviewBodyImportReceipt,pub output_review_import:review::ReviewBodyImportReceipt,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub exact_original_selection_verified:bool,
    pub original_run_shells_declared_styles_controls_and_references_preserved:bool,pub composed_output_uses_first_original_contributor:bool,
    pub unrelated_compatibility_and_canonical_text_unchanged:bool,pub output_spans_and_outside_slots_verified:bool,
    pub general_normalization_icu_native_or_service_authority:bool,
}
pub struct SourceWidthConversionCandidate {artifact:PackageArtifact,receipt:SourceWidthConversionReceipt}
impl fmt::Debug for SourceWidthConversionCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("SourceWidthConversionCandidate(<redacted>; width_pairs_not_native_or_execution_authority)")}}
impl SourceWidthConversionCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceWidthConversionReceipt {&self.receipt}
    /// # Errors
    /// Pure writer integrity, not current service access, revision CAS or execution qualification.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Explicit width pair/kana conversion with original run shells and first-contributor style.
    pub fn lower_review_selector_width_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceWidthMode,policy:SourceWidthPolicy,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceWidthConversionCandidate,E>{
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_selector_width_candidate(self,query,selector,body_policy,filter,mode,policy,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One original proof/field/review/index/matcher/writer/readback, not one import per character.
    pub fn lower_review_selector_width_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,body_policy:SourceReviewTextPolicy,
        filter:Option<SourceReviewStyleFilter>,mode:SourceWidthMode,policy:SourceWidthPolicy,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceWidthConversionCandidate,E>{
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let found=if let Some(filter)=filter{SourceWidthMatchSearch::Style(index.find_style(query,selector,body_policy,filter)?)}
            else{SourceWidthMatchSearch::Text(index.find(query,selector,body_policy)?)};
        let search=found.search();let text=index.source_index();if search.result().matches().is_empty(){return Err(E::NoMatches);}
        let mut groups=Vec::new();let mut selected=BTreeSet::new();
        for m in search.result().matches(){let origins=selected_origins(text,m)?;
            for &origin in &origins{if !selected.insert(origin){return Err(E::Selection);}}
            groups.push(origins.into_iter().collect());
        }
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,body_policy)?;
        let plan=unicode::plan::compile_mapped(text,&fields,&context,groups,selected,|chars,ids,remaining,bytes|mapping::convert(text,chars,ids,mode,remaining,bytes))?;
        let artifact=styles::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&plan.spans,writer)?;
        let output_review=readback::verify_artifact(text.original.source(),&artifact,&plan.spans,Some(&context))?.ok_or(E::Readback)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_WIDTH_CONVERSION_PROFILE,search.request_sha256(),filter,mode,policy,run_policy,table::UNICODE_VERSION,table::UCD_SHA256)).map_err(|_|E::Limit)?;
        let receipt=SourceWidthConversionReceipt {profile:SOURCE_WIDTH_CONVERSION_PROFILE,source_package_sha256:text.original.source().receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),mode,policy,run_policy,width_unicode_version:table::UNICODE_VERSION,
            mapping_source_sha256:table::UCD_SHA256,width_pair_count:226,kana_pair_count:28,body_policy,filter,search:found,
            request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),selected_original_scalars:plan.selected,converted_text_groups:plan.groups,
            mapped_scalars:plan.decomposed,changed_components:plan.components,changed_scalar_ranges:plan.ranges,changes:plan.changes,changed_parts:plan.spans.len(),
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,source_review_import:review.receipt().clone(),output_review_import:output_review,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),exact_original_selection_verified:true,
            original_run_shells_declared_styles_controls_and_references_preserved:true,composed_output_uses_first_original_contributor:true,
            unrelated_compatibility_and_canonical_text_unchanged:true,output_spans_and_outside_slots_verified:true,general_normalization_icu_native_or_service_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceWidthConversionCandidate {artifact,receipt})
    }
}
