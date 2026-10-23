//! Explicit source style predicates over the same review-aware selector windows, not a cascade.
pub(in crate::document_import::search) mod paragraphs;
use super::*;
use crate::document_import::search::inspection::{SourceDeclaredStyleFilter,SourceInspectionReceipt,
    definitions::{SourceDefinitionStyleFilter,SourceStyleDefinitionReceipt}};
use serde::Deserialize;
pub const REVIEW_SELECTOR_STYLE_PROFILE:&str="hwpx-agent.source-review-selector-style-search/v1";
#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",content="filter",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceReviewStyleFilter {Declared(SourceDeclaredStyleFilter),Definition(SourceDefinitionStyleFilter)}
impl SourceReviewStyleFilter {
    /// # Errors
    /// Explicit nonempty declared axes or validated typed definition axes; never match-all defaults.
    pub fn validate(&self)->Result<(),E> {match self {Self::Declared(f)=>if f.is_empty(){Err(E::Filter)}else{Ok(())},Self::Definition(f)=>f.validate()}}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewSelectorStyleResult {profile:&'static str,#[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::review")] filter:SourceReviewStyleFilter,inspection:SourceInspectionReceipt,
    definitions:Option<SourceStyleDefinitionReceipt>,search:SourceReviewSelectorResult,effective_style_visibility_or_execution_authority:bool,#[serde(skip)] maximum:usize}
impl SourceReviewSelectorStyleResult {
    #[must_use] pub const fn search(&self)->&SourceReviewSelectorResult {&self.search}
    #[must_use] pub const fn inspection_receipt(&self)->&SourceInspectionReceipt {&self.inspection}
    #[must_use] pub const fn definition_receipt(&self)->Option<&SourceStyleDefinitionReceipt> {self.definitions.as_ref()}
    /// # Errors
    /// Binds source predicates, exact windows and policy without another index or query.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.search.result().matches(),Some(self.search.match_regions())),self.maximum,request,context)
    }
    /// # Errors
    /// The entire filter/definition/window/region response must fit; no truncated success.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl SourceReviewScopeIndex<'_> {
    /// # Errors
    /// Select windows and exclude bodies before matching; every contributing NFC scalar must satisfy the source style.
    pub fn find_style(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter)->Result<SourceReviewSelectorStyleResult,E> {
        self.find_style_checked(query,selector,policy,filter,None).map(|(found,_)|found)
    }
    pub(in crate::document_import::search) fn find_style_for_character_replacement(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,target:u32)->Result<(SourceReviewSelectorStyleResult,SourceAnchorHandle),E> {
        let(found,declaration)=self.find_style_checked(query,selector,policy,filter,Some(target))?;Ok((found,declaration.ok_or(E::Definition)?))
    }
    fn find_style_checked(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,target:Option<u32>)->Result<(SourceReviewSelectorStyleResult,Option<SourceAnchorHandle>),E> {
        filter.validate()?;let selected=self.resolve_windows(selector,policy)?;let inspection=self.base.index.inspection()?;
        let bound=if target.is_some()||matches!(filter,SourceReviewStyleFilter::Definition(_)){Some(inspection.resolve_style_definitions()?)}else{None};
        let declaration=target.map(|id|bound.as_ref().ok_or(E::Definition)?.character_declaration(id)).transpose()?;
        let(result,definitions)=match &filter {
            SourceReviewStyleFilter::Declared(filter)=>{let accept=|points:&BTreeSet<usize>|inspection.accepts_declared_points(points,*filter);
                (self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?,bound.as_ref().map(|d|d.receipt().clone()))},
            SourceReviewStyleFilter::Definition(filter)=>{let definitions=bound.as_ref().ok_or(E::Definition)?;
                let accept=definitions.matcher(filter)?;
                (self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?,Some(definitions.receipt().clone()))},
        };
        let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&(REVIEW_SELECTOR_STYLE_PROFILE,self.base.index.receipt.index_sha256,selected.scope.scope_sha256,query,policy,&filter,inspection.receipt(),&definitions)).map_err(|_|E::Output)?;
        let search=self.finish_resolved(selected,policy,result,hash.sha.finalize().into(),REVIEW_SELECTOR_STYLE_PROFILE)?;
        let value=SourceReviewSelectorStyleResult {profile:REVIEW_SELECTOR_STYLE_PROFILE,filter,inspection:inspection.receipt().clone(),definitions,search,
            effective_style_visibility_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:value.maximum};serde_json::to_writer(&mut count,&value).map_err(|_|E::Output)?;Ok((value,declaration))
    }
}
