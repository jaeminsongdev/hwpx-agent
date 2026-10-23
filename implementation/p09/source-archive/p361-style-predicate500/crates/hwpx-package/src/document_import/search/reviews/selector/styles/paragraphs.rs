//! Whole-paragraph mutation keeps the original matcher and carries its exact selected windows.
use super::*;
use crate::document_import::search::inspection::definitions::SourceParagraphStyleTarget;
pub(in crate::document_import::search) type ParagraphStyleSearch=(SourceReviewSelectorStyleResult,SourceAnchorHandle,BTreeMap<usize,(usize,usize)>);
impl SourceReviewScopeIndex<'_> {
    pub(in crate::document_import::search) fn find_style_for_paragraph_replacement(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,target:SourceParagraphStyleTarget)->Result<ParagraphStyleSearch,E> {
        filter.validate()?;let selected=self.resolve_windows(selector,policy)?;let inspection=self.base.index.inspection()?;
        let bound=inspection.resolve_style_definitions()?;let declaration=bound.paragraph_declaration(target)?;
        let result=match filter {
            SourceReviewStyleFilter::Declared(filter)=>{let accept=|points:&BTreeSet<usize>|inspection.accepts_declared_points(points,filter);
                self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?},
            SourceReviewStyleFilter::Definition(filter)=>{let accept=|points:&BTreeSet<usize>|bound.accepts_points(points,filter);
                self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?},
        };
        let definitions=Some(bound.receipt().clone());let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};
        serde_json::to_writer(&mut hash,&(REVIEW_SELECTOR_STYLE_PROFILE,self.base.index.receipt.index_sha256,selected.scope.scope_sha256,query,policy,filter,inspection.receipt(),&definitions)).map_err(|_|E::Output)?;
        // Move, rather than clone or re-resolve, the exact window map into the compiler context.
        let search=SourceReviewSelectorResult {profile:REVIEW_SELECTOR_STYLE_PROFILE,index:self.base.index.receipt.clone(),review:self.base.projection.receipt.clone(),
            scope:selected.scope,policy,request_sha256:hash.sha.finalize().into(),match_regions:result.matches().iter().map(|m|self.base.region(&m.paragraph_anchor.opaque_handle)).collect(),result,
            searched_paragraphs:selected.searched_paragraphs,searched_blocks:selected.windows.len(),excluded_hidden_paragraphs:selected.hidden,excluded_memo_paragraphs:selected.memo,
            opaque_node_count_is_base_graph_only:true,native_visibility_flow_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let value=SourceReviewSelectorStyleResult {profile:REVIEW_SELECTOR_STYLE_PROFILE,filter,inspection:inspection.receipt().clone(),definitions,search,
            effective_style_visibility_or_execution_authority:false,maximum:self.base.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:value.maximum};serde_json::to_writer(&mut count,&value).map_err(|_|E::Output)?;
        Ok((value,declaration,selected.windows))
    }
}
