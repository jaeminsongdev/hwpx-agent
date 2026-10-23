//! Exact selector windows lower through the original review/MEMO writer, not paragraph expansion.
use super::*;
use crate::document_import::search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},reviews::selector::SourceReviewScopeIndex};
pub const SOURCE_SELECTOR_LITERAL_PROFILE:&str="hwpx-agent.source-selector-literal-replacement-candidate/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSelectorLiteralReceipt {pub profile:&'static str,pub selector:SourceIndexScopeReceipt,pub body_candidate:SourceReviewLiteralReceipt,
    pub scope_window_enforced:bool,pub native_or_execution_authority:bool}
pub struct SourceSelectorLiteralCandidate {inner:SourceReviewLiteralCandidate,receipt:SourceSelectorLiteralReceipt}
impl fmt::Debug for SourceSelectorLiteralCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSelectorLiteralCandidate(<redacted>; source_window_not_revision_or_execution)")}}
impl SourceSelectorLiteralCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceSelectorLiteralReceipt {&self.receipt}
    /// # Errors
    /// The same immutable writer integrity; fresh authorization remains a stored-service obligation.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.inner.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Whole original proof plus exact selector windows and explicit body policy.
    pub fn lower_review_selector_literal_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorLiteralCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_selector_literal_candidate(self,query,selector,policy,replacement,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One field collector/review projection; no query-per-match import or widened selection.
    pub fn lower_review_selector_literal_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceSelectorLiteralCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        if query.mode!=SourceSearchMode::Literal{return Err(E::Value);}validate_literal_replacement(replacement)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;let found=index.find(query,selector,policy)?;
        let inner=compile_review_found(index.source_index(),&fields,&review,rebuilt.source().original.as_ref(),
            ReviewMatches {result:found.result(),scope_sha:found.scope_receipt().scope_sha256,request_sha:found.request_sha256(),regions:found.match_regions()},
            policy,replacement,run_policy,limits,writer)?;
        if inner.receipt().output.scope_sha256!=found.scope_receipt().scope_sha256||inner.receipt().output.source_index_sha256!=found.scope_receipt().index_sha256{return Err(E::Readback);}
        let receipt=SourceSelectorLiteralReceipt {profile:SOURCE_SELECTOR_LITERAL_PROFILE,selector:found.scope_receipt().clone(),body_candidate:inner.receipt().clone(),
            scope_window_enforced:true,native_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceSelectorLiteralCandidate {inner,receipt})
    }
}
