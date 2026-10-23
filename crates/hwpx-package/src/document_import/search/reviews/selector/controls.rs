//! Controls use their own original anchor, not membership of an enclosing selected paragraph.
use super::*;
use crate::document_import::search::{inspection::{SourceControlKind,SourceControlMatch,SourceInspectionReceipt},selector::control_geometry::ControlGeometry};
pub const REVIEW_SELECTOR_CONTROL_PROFILE:&str="hwpx-agent.source-review-selector-control-search/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewSelectorControlResult {
    profile:&'static str,index:SourceSearchIndexReceipt,review:ReviewBodyImportReceipt,inspection:SourceInspectionReceipt,
    scope:SourceIndexScopeReceipt,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize,request_sha256:[u8;32],
    control_matches:Vec<SourceControlMatch>,match_regions:Vec<SourceTextRegion>,
    scope_membership:&'static str,control_order:&'static str,excluded_hidden_controls:usize,excluded_memo_controls:usize,
    native_visibility_flow_control_semantics_or_execution_authority:bool,#[serde(skip)] maximum:usize,
}
impl SourceReviewSelectorControlResult {
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index}
    #[must_use] pub const fn scope_receipt(&self)->&SourceIndexScopeReceipt {&self.scope}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    #[must_use] pub const fn policy(&self)->SourceReviewTextPolicy {self.policy}
    #[must_use] pub const fn kind(&self)->SourceControlKind {self.kind}
    #[must_use] pub const fn max_results(&self)->usize {self.max_results}
    #[must_use] pub fn controls(&self)->&[SourceControlMatch] {&self.control_matches}
    #[must_use] pub fn match_regions(&self)->&[SourceTextRegion] {&self.match_regions}
    /// # Errors
    /// Binds original controls, exact scope and explicit review regions without searching again.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::ControlRegions(&self.control_matches,&self.match_regions),self.maximum,request,context)
    }
    /// # Errors
    /// Counts the complete bounded response; no truncated-success or source text output.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl SourceReviewScopeIndex<'_> {
    /// # Errors
    /// Source control START anchors must be in the half-open original range. Parent paragraph
    /// windows remain descriptive text coverage only, never control membership or edit authority.
    pub fn find_control(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize)->Result<SourceReviewSelectorControlResult,E> {
        self.find_control_with_windows(selector,policy,kind,max_results).map(|(result,_)|result)
    }
    pub(in crate::document_import::search) fn find_control_with_windows(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize)
        ->Result<(SourceReviewSelectorControlResult,BTreeMap<usize,(usize,usize)>),E> {
        self.find_control_with_geometry(selector,policy,kind,max_results).map(|(result,windows,_)|(result,windows))
    }
    pub(in crate::document_import::search) fn find_control_with_geometry(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize)
        ->Result<(SourceReviewSelectorControlResult,BTreeMap<usize,(usize,usize)>,ControlGeometry),E> {
        if max_results==0||max_results>self.base.limits.0.matches{return Err(E::Limit);}
        let index=&self.base.index;let mut geometry=ControlGeometry::All;
        let(scope,windows)=index.resolve_index_selector_with_geometry(selector,Some(&self.nodes),Some(&mut geometry))?;
        let inspection=index.inspection()?;let mut found=Vec::new();let mut hidden=0;let mut memo=0;
        for control in inspection.observed_controls() {
            if control.kind!=kind||!geometry.contains(index,&control.control_anchor)?{continue;}
            let region=self.base.region(&control.paragraph_anchor.opaque_handle);
            if !policy.permits(region){match region {SourceTextRegion::HiddenExplanation=>hidden+=1,SourceTextRegion::MemoBody=>memo+=1,SourceTextRegion::BodyAndNotes=>{}}continue;}
            if found.len()>=max_results{return Err(E::Limit);}found.push(control.clone());
        }
        // Original inspection visits an outer paragraph before nested body paragraphs. Sort once
        // by actual control anchors, not paragraph or result ordinal, for source-order navigation.
        let parts:BTreeMap<_,_>=index.original.source().spine().iter().enumerate().map(|(i,p)|(p.as_str(),i)).collect();
        let mut keyed=Vec::new();
        for control in found {let resolved=index.original.source().resolve_anchor(&control.control_anchor).map_err(|_|E::Source)?;
            keyed.push((*parts.get(resolved.part().path().as_str()).ok_or(E::Mapping)?,resolved.element().ok_or(E::Mapping)?.start_tag_span().start(),control));}
        keyed.sort_by_key(|(part,start,_)|(*part,*start));let control_matches:Vec<_>=keyed.into_iter().map(|(_,_,control)|control).collect();
        let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&(REVIEW_SELECTOR_CONTROL_PROFILE,index.receipt.index_sha256,inspection.receipt().inspection_sha256,scope.scope_sha256,policy,kind,max_results)).map_err(|_|E::Output)?;
        let value=SourceReviewSelectorControlResult {profile:REVIEW_SELECTOR_CONTROL_PROFILE,index:index.receipt.clone(),review:self.base.projection.receipt.clone(),
            inspection:inspection.receipt().clone(),scope,policy,kind,max_results,request_sha256:hash.sha.finalize().into(),
            match_regions:control_matches.iter().map(|m|self.base.region(&m.paragraph_anchor.opaque_handle)).collect(),control_matches,
            scope_membership:"original_control_start_in_half_open_source_range_not_parent_paragraph_windows",control_order:"spine_and_original_control_start_not_native_flow",
            excluded_hidden_controls:hidden,excluded_memo_controls:memo,native_visibility_flow_control_semantics_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:value.maximum};serde_json::to_writer(&mut count,&value).map_err(|_|E::Output)?;Ok((value,windows,geometry))
    }
}
