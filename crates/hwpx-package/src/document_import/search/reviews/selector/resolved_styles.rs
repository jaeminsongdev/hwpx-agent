//! Bounded selected-region direct formatting predicates with explicit unresolved-axis rejection.
use super::*;
use crate::document_import::search::inspection::definitions::resolved::{SourceResolvedStyleFilter,SourceResolvedStyleCoverage,SOURCE_RESOLVED_STYLE_PROFILE};
use thiserror::Error;

#[derive(Debug,Error)]
pub enum SourceResolvedStyleSearchError {
    #[error("SOURCE_RESOLVED_STYLE_SEARCH_REJECTED")] Search(#[from] E),
    #[error("SOURCE_RESOLVED_STYLE_REQUIRED_AXES_UNRESOLVED")] Unresolved(Box<SourceResolvedStyleCoverage>),
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceResolvedSelectorStyleResult {
    profile:&'static str,#[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::resolved")] filter:SourceResolvedStyleFilter,coverage:SourceResolvedStyleCoverage,search:SourceReviewSelectorResult,
    native_cascade_visibility_or_execution_authority:bool,#[serde(skip)] maximum:usize,
}
impl SourceResolvedSelectorStyleResult {
    #[must_use] pub const fn search(&self)->&SourceReviewSelectorResult {&self.search}
    #[must_use] pub const fn coverage(&self)->&SourceResolvedStyleCoverage {&self.coverage}
    /// # Errors
    /// The result, selected coverage and predicate bind the original retained-result cursor.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.search.result().matches(),Some(self.search.match_regions())),self.maximum,request,context)
    }
    /// # Errors
    /// No truncated match or coverage wrapper is returned on exhaustion.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl SourceReviewScopeIndex<'_> {
    /// # Errors
    /// Assess every selected, policy-admitted source segment before searching. Unresolved required
    /// axes reject even when the query has no matches; excluded regions do not silently become hits.
    pub fn find_resolved_style(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceResolvedStyleFilter)
        ->Result<SourceResolvedSelectorStyleResult,SourceResolvedStyleSearchError> {
        filter.validate()?;let selected=self.resolve_windows(selector,policy)?;let inspection=self.base.index.inspection()?;
        let definitions=inspection.resolve_style_definitions()?;
        let mut segments=BTreeSet::new();
        for (&block,&(a,b)) in &selected.windows {
            let units=self.base.index.blocks.get(block).ok_or(E::Mapping)?.units.get(a..b).ok_or(E::Mapping)?;
            for unit in units {for &point in &unit.origins {segments.insert(self.base.index.points.get(point).ok_or(E::Mapping)?.segment);}}
        }
        let coverage=definitions.assess_resolved_segments(&segments,&filter)?;
        if !coverage.requested_axes_complete(){return Err(SourceResolvedStyleSearchError::Unresolved(Box::new(coverage)));}
        let explicit=filter.explicit();let accept=definitions.matcher(&explicit)?;
        let result=self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?;
        drop(accept);
        let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&(SOURCE_RESOLVED_STYLE_PROFILE,self.base.index.receipt.index_sha256,selected.scope.scope_sha256,query,policy,&filter,&coverage)).map_err(|_|E::Output)?;
        let search=self.finish_resolved(selected,policy,result,hash.sha.finalize().into(),SOURCE_RESOLVED_STYLE_PROFILE)?;
        let found=SourceResolvedSelectorStyleResult {profile:SOURCE_RESOLVED_STYLE_PROFILE,filter,coverage,search,native_cascade_visibility_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:found.maximum};serde_json::to_writer(&mut count,&found).map_err(|_|E::Output)?;Ok(found)
    }
}
