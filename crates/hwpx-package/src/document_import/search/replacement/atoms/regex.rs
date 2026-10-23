//! One regex capture pass -> distinct bounded expansions -> original protected atom writer.
mod template;
pub(super) mod insertions;
use super::*;
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},reviews::{selector::SourceReviewScopeIndex,SourceReviewTextPolicy,SourceTextRegion}},
    structure::review::{ImportedDocumentReviewBodies,ReviewBodyImportReceipt}};
pub use template::validate_regex_replacement_template;
pub use insertions::SourceRegexInsertionPolicy;
pub const SOURCE_SELECTOR_REGEX_PROFILE:&str="hwpx-agent.source-selector-regex-replacement-candidate/v1";
pub const SOURCE_REGEX_TEXT_ATOM_PROFILE:&str="hwpx-agent.source-regex-text-atom-output/v1";
pub const SOURCE_SELECTOR_REGEX_INSERTION_PROFILE:&str="hwpx-agent.source-selector-regex-replacement-candidate/v2";
pub const SOURCE_REGEX_INSERTION_ATOM_PROFILE:&str="hwpx-agent.source-regex-text-atom-output/v2";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceRegexReplacementError {
    #[error("SOURCE_REGEX_REPLACEMENT_SOURCE_REJECTED")] Source,
    #[error("SOURCE_REGEX_REPLACEMENT_PATTERN_OR_MATCH:{0}")] Search(#[from] SourceSearchError),
    #[error("SOURCE_REGEX_REPLACEMENT_TEMPLATE_REJECTED")] Template,
    #[error("SOURCE_REGEX_REPLACEMENT_REGEX_MODE_REQUIRED")] Mode,
    #[error("SOURCE_REGEX_REPLACEMENT_EXPANSION_LIMIT")] Limit,
    #[error("SOURCE_REGEX_REPLACEMENT_PROTECTED_COMPILER:{0}")] Compile(#[from] SourceLiteralReplacementError),
}
type R=SourceRegexReplacementError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSelectorRegexReceipt {
    pub profile:&'static str,pub selector:SourceIndexScopeReceipt,pub body_policy:SourceReviewTextPolicy,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,pub search_request_sha256:[u8;32],
    pub template_sha256:[u8;32],pub template_bytes:usize,pub expansion_sha256:[u8;32],pub expanded_replacement_bytes:usize,
    pub expansion_work_units:usize,pub expansion_work_limit:usize,
    pub match_regions:Vec<SourceTextRegion>,pub output:SourceLiteralTextAtomReceipt,
    pub captures_from_one_original_match_pass:bool,pub capture_values_are_index_nfc_text:bool,pub scope_window_enforced:bool,
    pub zero_width_control_or_field_cache_edit_qualified:bool,pub native_or_execution_authority:bool,
}
pub struct SourceSelectorRegexCandidate {inner:SourceLiteralTextAtomCandidate,receipt:SourceSelectorRegexReceipt}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSelectorRegexInsertionReceipt {
    pub profile:&'static str,pub output:SourceSelectorRegexReceipt,pub insertion_policy:SourceRegexInsertionPolicy,
    pub zero_width_matches:usize,pub insertion_boundaries_sha256:[u8;32],pub exact_original_cut_verified:bool,
    pub text_insertion_next_to_controls_qualified:bool,pub original_empty_text_expansion_qualified:bool,
    pub control_replacement_field_cache_native_or_execution_authority:bool,
}
pub struct SourceSelectorRegexInsertionCandidate {inner:SourceSelectorRegexCandidate,receipt:SourceSelectorRegexInsertionReceipt}
impl fmt::Debug for SourceSelectorRegexInsertionCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSelectorRegexInsertionCandidate(<redacted>; source_insertions_not_execution)")}}
impl SourceSelectorRegexInsertionCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceSelectorRegexInsertionReceipt {&self.receipt}
    /// # Errors
    /// Original writer integrity only; not stored access, Native execution or revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.inner.with_verified_bytes(consume)}
}
impl fmt::Debug for SourceSelectorRegexCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSelectorRegexCandidate(<redacted>; protected_source_text_not_execution)")}}
impl SourceSelectorRegexCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceSelectorRegexReceipt {&self.receipt}
    /// # Errors
    /// Original writer integrity only, not current stored access or revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.inner.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Explicit v2 inverse-NFC insertion policy. The v1 method still rejects zero-width matches.
    pub fn lower_review_selector_regex_insertion_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,insertion_policy:SourceRegexInsertionPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorRegexInsertionCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|R::Source)?
            .lower_review_selector_regex_insertion_candidate(self,query,selector,policy,replacement,run_policy,insertion_policy,limits,writer)
    }
    /// # Errors
    /// Whole original proof plus exact selector/body policy and capture-template expansion.
    pub fn lower_review_selector_regex_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorRegexCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|R::Source)?
            .lower_review_selector_regex_candidate(self,query,selector,policy,replacement,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Whole-original proof, one capture pass and one protected transaction for all matches.
    pub fn lower_review_selector_regex_insertion_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,insertion_policy:SourceRegexInsertionPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorRegexInsertionCandidate,R> {
        let(inner,insertions)=self.lower_regex(original,query,selector,policy,replacement,run_policy,limits,writer,Some(insertion_policy))?;
        let insertions=insertions.ok_or(E::Selection)?;
        let receipt=SourceSelectorRegexInsertionReceipt {profile:SOURCE_SELECTOR_REGEX_INSERTION_PROFILE,output:inner.receipt().clone(),insertion_policy,
            zero_width_matches:insertions.carets.len(),insertion_boundaries_sha256:insertions.sha256,exact_original_cut_verified:true,
            text_insertion_next_to_controls_qualified:true,original_empty_text_expansion_qualified:true,control_replacement_field_cache_native_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|R::Limit)?;
        Ok(SourceSelectorRegexInsertionCandidate {inner,receipt})
    }
    /// # Errors
    /// One field collector/review projection/index and regex pass. No caller-provided captures or graph.
    pub fn lower_review_selector_regex_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorRegexCandidate,R> {
        self.lower_regex(original,query,selector,policy,replacement,run_policy,limits,writer,None).map(|(candidate,_)|candidate)
    }
    fn lower_regex(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,insertion_policy:Option<SourceRegexInsertionPolicy>)->Result<(SourceSelectorRegexCandidate,Option<insertions::Insertions>),R> {
        let rebuilt=self.for_original(original).map_err(|_|R::Source)?;
        if query.mode!=SourceSearchMode::Regex{return Err(R::Mode);}
        let mut collector=template::Collector::new(replacement,limits)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|R::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|R::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let found=index.find_with_captures(query,selector,policy,Some(&mut collector)).map_err(|e|collector.error(e))?;
        let(work,work_limit)=collector.work_counters();let expanded=collector.expansions();let text=index.source_index();
        let insertions=insertion_policy.map(|p|insertions::Insertions::build(text,found.result(),p)).transpose()?;
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let(inner,readback)=lower_found_with_insertions(text,&fields,rebuilt.source().original.as_ref(),found.result(),found.scope_receipt().scope_sha256,
            replacement,run_policy,writer,Some(&context),Some(&expanded),insertions.as_ref())?;
        let receipt=SourceSelectorRegexReceipt {profile:if insertions.is_some(){SOURCE_SELECTOR_REGEX_INSERTION_PROFILE}else{SOURCE_SELECTOR_REGEX_PROFILE},selector:found.scope_receipt().clone(),body_policy:policy,
            source_review_import:review.receipt().clone(),output_review_import:readback.ok_or(E::Readback)?,search_request_sha256:found.request_sha256(),
            template_sha256:Sha256::digest(replacement.as_bytes()).into(),template_bytes:replacement.len(),expansion_sha256:expanded.sha256,expanded_replacement_bytes:expanded.bytes,
            expansion_work_units:work,expansion_work_limit:work_limit,
            match_regions:found.match_regions().to_vec(),output:inner.receipt().clone(),captures_from_one_original_match_pass:true,capture_values_are_index_nfc_text:true,
            scope_window_enforced:true,zero_width_control_or_field_cache_edit_qualified:false,native_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|R::Limit)?;
        Ok((SourceSelectorRegexCandidate {inner,receipt},insertions))
    }
}
