//! Original hidden/MEMO bodies, with explicit corpus policy instead of inferred app visibility.
pub mod selector;
use super::*;
use super::scope::{SourceSearchScope,SourceSearchScopeReceipt};
use super::super::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},structure::review::{ImportedDocumentReviewBodies,ReviewBodyKind,ReviewBodyImportReceipt}};
use domain_ir::LogicalId;
use serde::Deserialize;
use std::collections::BTreeMap;
pub const REVIEW_TEXT_INDEX_PROFILE:&str="hwpx-agent.source-text-search/nfc-review-map-v2";
pub const REVIEW_TEXT_RESULT_PROFILE:&str="hwpx-agent.source-review-text-search/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceTextRegion {BodyAndNotes,HiddenExplanation,MemoBody}
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceReviewTextPolicy {pub include_hidden_explanations:bool,pub include_memo_bodies:bool}
impl SourceReviewTextPolicy {fn permits(self,region:SourceTextRegion)->bool {match region {
    SourceTextRegion::BodyAndNotes=>true,SourceTextRegion::HiddenExplanation=>self.include_hidden_explanations,SourceTextRegion::MemoBody=>self.include_memo_bodies}}}
#[derive(Eq,PartialEq)]
pub(super) struct ReviewProjection {pub(super) regions:BTreeMap<LogicalId,SourceTextRegion>,pub(super) receipt:ReviewBodyImportReceipt}
impl ReviewProjection {
    pub(super) fn binding_sha256(&self,maximum:usize)->Result<[u8;32],E> {
        let mut digest=BindingHash {length:0,maximum,sha:Sha256::new()};
        serde_json::to_writer(&mut digest,&(REVIEW_TEXT_INDEX_PROFILE,&self.receipt,&self.regions)).map_err(|_|E::Output)?;Ok(digest.sha.finalize().into())
    }
}
pub struct SourceReviewTextIndex<'a> {forms:&'a ImportedDocumentForms,index:SourceTextIndex<'a>,projection:ReviewProjection,limits:SourceSearchLimits}
impl fmt::Debug for SourceReviewTextIndex<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceReviewTextIndex(<redacted>; explicit_file_body_policy_only)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewTextResult {
    profile:&'static str,coverage:&'static str,index:SourceSearchIndexReceipt,review:ReviewBodyImportReceipt,scope:SourceSearchScopeReceipt,policy:SourceReviewTextPolicy,
    searched_paragraphs:usize,searched_blocks:usize,excluded_hidden_paragraphs:usize,excluded_memo_paragraphs:usize,
    request_sha256:[u8;32],matches:SourceSearchResult,match_regions:Vec<SourceTextRegion>,
    opaque_node_count_is_base_graph_only:bool,app_visibility_cascade_or_full_document_search_qualified:bool,
    #[serde(skip)] output_limit:usize,
}
impl SourceReviewTextResult {
    /// # Errors
    /// Explicit body policy, coverage and original region order remain cursor-bound.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.matches.matches(),Some(&self.match_regions)),self.output_limit,request,context)
    }
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index}
    #[must_use] pub const fn scope_receipt(&self)->&SourceSearchScopeReceipt {&self.scope}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    #[must_use] pub const fn matches(&self)->&SourceSearchResult {&self.matches}
    #[must_use] pub fn match_regions(&self)->&[SourceTextRegion] {&self.match_regions}
    /// # Errors
    /// Bounds the entire result, including coverage and region annotations.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Fresh complete original Form reconstruction, then original review-body admission.
    pub fn source_review_text_index(&self,fresh:&[u8],limits:SourceSearchLimits)->Result<SourceReviewTextIndex<'_>,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?.source_review_text_index(self,limits)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// The original pointer-bound proof is pure validation, never a service grant.
    pub fn source_review_text_index<'a>(&self,original:&'a ImportedDocumentForms,limits:SourceSearchLimits)->Result<SourceReviewTextIndex<'a>,E> {
        self.for_original(original).map_err(|_|E::Source)?;SourceReviewTextIndex::build(original,limits)
    }
}
impl<'a> SourceReviewTextIndex<'a> {
    fn build(forms:&'a ImportedDocumentForms,limits:SourceSearchLimits)->Result<Self,E> {
        let review=ImportedDocumentReviewBodies::import(forms).map_err(|_|E::Review)?;
        Self::from_review(forms,&review,limits)
    }
    pub(super) fn from_review(forms:&'a ImportedDocumentForms,review:&ImportedDocumentReviewBodies<'_>,limits:SourceSearchLimits)->Result<Self,E> {
        if !review.is_for_original(forms){return Err(E::Source);}
        let mut regions=BTreeMap::new();
        for observation in review.observations() {
            let region=match observation.kind {ReviewBodyKind::HiddenExplanation=>SourceTextRegion::HiddenExplanation,ReviewBodyKind::MemoField=>SourceTextRegion::MemoBody};
            if let Some(body)=&observation.body {
                let mut anchors=BTreeSet::new();extract::paragraphs(body,&mut anchors,limits.0.paragraphs,0)?;
                for id in anchors {if regions.insert(id,region).is_some(){return Err(E::Mapping);}if regions.len()>limits.0.paragraphs{return Err(E::Limit);}}
            }
        }
        let projection=ReviewProjection {regions,receipt:review.receipt().clone()};
        let index=extract::build_extended(forms.body_structure(),limits,Some(&projection))?;
        Ok(Self {forms,index,projection,limits})
    }
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index.receipt}
    pub(super) fn source_index(&self)->&SourceTextIndex<'a> {&self.index}
    #[must_use] pub const fn review_receipt(&self)->&ReviewBodyImportReceipt {&self.projection.receipt}
    /// # Errors
    /// Rechecks complete fresh original and deterministic original review projection.
    pub fn verify_source(&self,fresh:&[u8])->Result<(),E> {
        self.forms.verify_source(fresh).map_err(|_|E::Source)?;let rebuilt=Self::build(self.forms,self.limits)?;
        if self.index.receipt!=rebuilt.index.receipt||self.projection!=rebuilt.projection{return Err(E::Mapping);}Ok(())
    }
    /// # Errors
    /// Scope is resolved against the whole admitted corpus, then policy exclusions
    /// apply before result limits. Declared body regions are not app display states.
    pub fn find(&self,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy)->Result<SourceReviewTextResult,E> {
        let(scope,selected)=self.index.resolve_search_scope(scope)?;let mut eligible=BTreeSet::new();let mut hidden=0;let mut memo=0;
        for id in &selected {
            let region=self.region(id);
            if policy.permits(region){eligible.insert(id.clone());}else{match region {SourceTextRegion::HiddenExplanation=>hidden+=1,SourceTextRegion::MemoBody=>memo+=1,SourceTextRegion::BodyAndNotes=>{}}}
        }
        let matches=self.index.find_selected(query,Some(&eligible))?;
        let match_regions=matches.matches().iter().map(|m|self.region(&m.paragraph_anchor.opaque_handle)).collect();
        let binding=serde_json::to_vec(&(REVIEW_TEXT_RESULT_PROFILE,self.index.receipt.index_sha256,scope.scope_sha256,query,policy)).map_err(|_|E::Mapping)?;
        let result=SourceReviewTextResult {profile:REVIEW_TEXT_RESULT_PROFILE,coverage:"selected_admitted_file_regions",index:self.index.receipt.clone(),review:self.projection.receipt.clone(),scope,policy,
            searched_paragraphs:eligible.len(),searched_blocks:self.index.blocks.iter().filter(|b|eligible.contains(&b.paragraph.opaque_handle)).count(),
            excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,request_sha256:Sha256::digest(binding).into(),matches,match_regions,
            opaque_node_count_is_base_graph_only:true,app_visibility_cascade_or_full_document_search_qualified:false,output_limit:self.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:result.output_limit};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
    fn region(&self,id:&LogicalId)->SourceTextRegion {self.projection.regions.get(id).copied().unwrap_or(SourceTextRegion::BodyAndNotes)}
}
struct BindingHash {length:usize,maximum:usize,sha:Sha256}
impl io::Write for BindingHash {
    fn write(&mut self,bytes:&[u8])->io::Result<usize> {self.length=self.length.checked_add(bytes.len()).filter(|n|*n<=self.maximum).ok_or_else(||io::Error::other("review binding bound"))?;
        self.sha.update(bytes);Ok(bytes.len())}
    fn flush(&mut self)->io::Result<()> {Ok(())}
}
pub(super) fn order_source_blocks(index:&mut SourceTextIndex<'_>)->Result<(),E> {
    let source=index.original.source();let order:BTreeMap<_,_>=source.spine().iter().enumerate().map(|(i,p)|(p.as_str(),i)).collect();
    let mut keyed=Vec::new();
    for block in std::mem::take(&mut index.blocks) {
        let first=block.units.iter().flat_map(|u|u.origins.iter().copied()).min();
        let anchor=first.map(|p|&index.segments[index.points[p].segment]).unwrap_or(&block.paragraph);
        let resolved=source.resolve_anchor(anchor).map_err(|_|E::Source)?;
        let part=*order.get(resolved.part().path().as_str()).ok_or(E::Mapping)?;
        let start=resolved.element().ok_or(E::Mapping)?.start_tag_span().start();keyed.push((part,start,block));
    }
    keyed.sort_by_key(|(part,start,_)|(*part,*start));index.blocks=keyed.into_iter().map(|(_,_,b)|b).collect();Ok(())
}
