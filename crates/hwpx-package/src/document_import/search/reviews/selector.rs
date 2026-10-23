//! One original review projection and authenticated supplemental node catalog for selector windows.
pub mod styles;
pub mod controls;
pub mod resolved_styles;
use super::*;
use crate::document_import::search::selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt,SupplementalNodes,inventory::SourceScopeInventory};
use domain_ir::{Flow,Node};
pub const REVIEW_SELECTOR_SEARCH_PROFILE:&str="hwpx-agent.source-review-selector-search/v1";
struct ResolvedReviewWindows {scope:SourceIndexScopeReceipt,windows:BTreeMap<usize,(usize,usize)>,searched_paragraphs:usize,hidden:usize,memo:usize}
pub struct SourceReviewScopeIndex<'a> {base:SourceReviewTextIndex<'a>,nodes:SupplementalNodes}
impl fmt::Debug for SourceReviewScopeIndex<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceReviewScopeIndex(<redacted>; file_regions_not_native_flow)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewScopeInventory {pub profile:&'static str,pub inventory:SourceScopeInventory,pub review:ReviewBodyImportReceipt,
    pub block_regions:Vec<SourceTextRegion>,pub native_visibility_or_execution_authority:bool,#[serde(skip)] maximum:usize}
impl SourceReviewScopeInventory {
    /// # Errors
    /// Finite whole response, including supplemental node identities and region labels.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewSelectorResult {profile:&'static str,index:SourceSearchIndexReceipt,review:ReviewBodyImportReceipt,
    scope:SourceIndexScopeReceipt,policy:SourceReviewTextPolicy,request_sha256:[u8;32],result:SourceSearchResult,match_regions:Vec<SourceTextRegion>,
    searched_paragraphs:usize,searched_blocks:usize,excluded_hidden_paragraphs:usize,excluded_memo_paragraphs:usize,
    opaque_node_count_is_base_graph_only:bool,native_visibility_flow_or_execution_authority:bool,#[serde(skip)] maximum:usize}
impl SourceReviewSelectorResult {
    /// # Errors
    /// Retains exact windows, explicit policy and region labels in the original result binding.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.result.matches(),Some(&self.match_regions)),self.maximum,request,context)
    }
    #[must_use] pub const fn result(&self)->&SourceSearchResult {&self.result}
    #[must_use] pub const fn scope_receipt(&self)->&SourceIndexScopeReceipt {&self.scope}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    #[must_use] pub fn match_regions(&self)->&[SourceTextRegion] {&self.match_regions}
    pub(in crate::document_import::search) const fn transformation_exclusions(&self)->(usize,usize) {
        (self.excluded_hidden_paragraphs,self.excluded_memo_paragraphs)
    }
    /// # Errors
    /// Bounds all matches, scope, policy and explicit exclusions without truncation.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.maximum};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Fresh whole original proof and the original field/review admission, not caller-supplied graph.
    pub fn source_review_scope_index(&self,fresh:&[u8],limits:SourceSearchLimits)->Result<SourceReviewScopeIndex<'_>,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?.source_review_scope_index(self,limits)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One exact original proof; reused by subsequent scope search or selector-aware lowering.
    pub fn source_review_scope_index<'a>(&self,original:&'a ImportedDocumentForms,limits:SourceSearchLimits)->Result<SourceReviewScopeIndex<'a>,E> {
        self.for_original(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import(original).map_err(|_|E::Review)?;SourceReviewScopeIndex::from_review(original,&review,limits)
    }
}
impl<'a> SourceReviewScopeIndex<'a> {
    pub(in crate::document_import) fn from_review(original:&'a ImportedDocumentForms,review:&ImportedDocumentReviewBodies<'_>,limits:SourceSearchLimits)->Result<Self,E> {
        let base=SourceReviewTextIndex::from_review(original,review,limits)?;let mut nodes=SupplementalNodes::new();
        for observation in review.observations(){if let Some(body)=&observation.body{collect_nodes(body,original,&mut nodes,limits.0.blocks,0)?;}}
        Ok(Self {base,nodes})
    }
    pub(in crate::document_import) fn source_index(&self)->&SourceTextIndex<'a> {&self.base.index}
    /// Move the original exact windows; transformations must not reconstruct or widen a selection.
    pub(in crate::document_import::search) fn transformation_windows(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy)
        ->Result<(SourceIndexScopeReceipt,BTreeMap<usize,(usize,usize)>,usize,usize),E> {
        let selected=self.resolve_windows(selector,policy)?;
        Ok((selected.scope,selected.windows,selected.hidden,selected.memo))
    }
    /// # Errors
    /// Supplemental identities come only from the original admitted review bodies.
    pub fn scope_inventory(&self)->Result<SourceReviewScopeInventory,E> {
        let inventory=self.base.index.scope_inventory_with_nodes(Some(&self.nodes))?;
        let value=SourceReviewScopeInventory {profile:"hwpx-agent.source-review-scope-inventory/v1",review:self.base.projection.receipt.clone(),
            block_regions:inventory.blocks.iter().map(|b|self.base.region(&b.paragraph_handle)).collect(),inventory,
            native_visibility_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:value.maximum};serde_json::to_writer(&mut count,&value).map_err(|_|E::Output)?;Ok(value)
    }
    /// # Errors
    /// Resolve exact scope on the whole admitted corpus, then exclude bodies before matching windows.
    pub fn find(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy)->Result<SourceReviewSelectorResult,E> {
        self.find_with_captures(query,selector,policy,None)
    }
    pub(in crate::document_import::search) fn find_with_captures(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,capture:Option<&mut dyn crate::document_import::search::captures::CaptureSink>)->Result<SourceReviewSelectorResult,E> {
        let selected=self.resolve_windows(selector,policy)?;
        let result=self.base.index.find_windowed_captured(query,None,None,Some(&selected.windows),capture)?;
        let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&(REVIEW_SELECTOR_SEARCH_PROFILE,self.base.index.receipt.index_sha256,selected.scope.scope_sha256,query,policy)).map_err(|_|E::Output)?;
        self.finish_resolved(selected,policy,result,hash.sha.finalize().into(),REVIEW_SELECTOR_SEARCH_PROFILE)
    }
    fn resolve_windows(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy)->Result<ResolvedReviewWindows,E> {
        let(scope,windows)=self.base.index.resolve_index_selector_with_nodes(selector,Some(&self.nodes))?;
        let mut eligible=BTreeMap::new();let mut hidden=BTreeSet::new();let mut memo=BTreeSet::new();let mut paragraphs=BTreeSet::new();
        for (i,window) in windows {let id=&self.base.index.blocks[i].paragraph.opaque_handle;let region=self.base.region(id);
            if policy.permits(region){eligible.insert(i,window);paragraphs.insert(id);}else{match region {SourceTextRegion::HiddenExplanation=>{hidden.insert(id);},
                SourceTextRegion::MemoBody=>{memo.insert(id);},SourceTextRegion::BodyAndNotes=>{}}}}
        Ok(ResolvedReviewWindows {scope,windows:eligible,searched_paragraphs:paragraphs.len(),hidden:hidden.len(),memo:memo.len()})
    }
    pub(in crate::document_import::search) fn find_precompiled_catalog(&self,expression:Option<&regex::Regex>,request_sha:[u8;32],selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        capture:&mut dyn crate::document_import::search::captures::CaptureSink)->Result<SourceReviewSelectorResult,E>{
        let selected=self.resolve_windows(selector,policy)?;
        let result=if let Some(expression)=expression{capture.compiled(expression)?;
            self.base.index.scan_compiled_windowed(expression,request_sha,self.base.limits.0.matches,None,None,Some(&selected.windows),Some(capture))?
        }else{SourceSearchResult{profile:self.base.index.receipt.profile,index:self.base.index.receipt.clone(),query_sha256:request_sha,matches:Vec::new(),
            complete_within_indexed_blocks:true,edit_or_execution_authority:false,output_limit:self.base.limits.0.result_bytes}};
        let mut hash=BindingHash{length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&("hwpx-agent.source-personal-info-catalog-search/v1",self.base.index.receipt.index_sha256,selected.scope.scope_sha256,request_sha,policy)).map_err(|_|E::Output)?;
        self.finish_resolved(selected,policy,result,hash.sha.finalize().into(),"hwpx-agent.source-personal-info-catalog-search/v1")
    }
    fn finish_resolved(&self,selected:ResolvedReviewWindows,policy:SourceReviewTextPolicy,result:SourceSearchResult,request_sha256:[u8;32],profile:&'static str)->Result<SourceReviewSelectorResult,E> {
        let value=SourceReviewSelectorResult {profile,index:self.base.index.receipt.clone(),review:self.base.projection.receipt.clone(),scope:selected.scope,policy,
            request_sha256,match_regions:result.matches().iter().map(|m|self.base.region(&m.paragraph_anchor.opaque_handle)).collect(),result,
            searched_paragraphs:selected.searched_paragraphs,searched_blocks:selected.windows.len(),excluded_hidden_paragraphs:selected.hidden,excluded_memo_paragraphs:selected.memo,
            opaque_node_count_is_base_graph_only:true,native_visibility_flow_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:value.maximum};serde_json::to_writer(&mut count,&value).map_err(|_|E::Output)?;Ok(value)
    }
}
fn collect_nodes(flow:&Flow,forms:&ImportedDocumentForms,nodes:&mut SupplementalNodes,maximum:usize,depth:usize)->Result<(),E> {
    if depth>128{return Err(E::Limit);}for node in &flow.children {
        if nodes.len()>=maximum{return Err(E::Limit);}let common=node.common();let anchor=common.source_anchor.as_ref().ok_or(E::Source)?;
        forms.source().resolve_anchor(anchor).map_err(|_|E::Source)?;
        if nodes.insert(common.node_id.clone(),anchor.clone()).is_some(){return Err(E::Mapping);}
        match node {Node::Table(t)=>for cell in &t.cells {collect_nodes(&cell.body,forms,nodes,maximum,depth+1)?;},
            Node::Drawing(d)=>collect_nodes(&d.children,forms,nodes,maximum,depth+1)?,_=>{}}
    }Ok(())
}
