//! Current sealed source -> assessed selected direct formatting; no silent unresolved matches.
use super::*;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,navigation as source_navigation,
    inspection::definitions::resolved::SourceResolvedStyleFilter,
    reviews::selector::resolved_styles::SourceResolvedSelectorStyleResult};

pub(super) struct ResolvedStyleResult {data:SourceResolvedSelectorStyleResult,pub scope:SourceSearchScopeReceipt}
impl ResolvedStyleResult {
    pub(super) fn index(&self)->&SourceSearchIndexReceipt {self.data.search().result().index_receipt()}
    pub(super) fn request_sha(&self)->[u8;32] {self.data.search().request_sha256()}
    pub(super) fn json(&self)->Result<Vec<u8>,SourceSearchError> {self.data.canonical_json()}
    pub(super) fn navigate(&self,request:&source_navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<source_navigation::SourceSearchNavigationResult,SourceSearchError> {self.data.navigate(request,context)}
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Shares the original current-access proof, result integrity and final-consumer boundaries.
    /// Unresolved required source axes remain typed errors, never empty stored results.
    pub fn into_resolved_style_search<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceResolvedStyleFilter,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let index=proof.source_review_scope_index(&self.imported,limits)?;
        let data=index.find_resolved_style(query,selector,policy,filter)?;
        if !data.coverage().requested_axes_complete()||data.coverage().inferred_default_or_named_fallback
            ||data.coverage().native_effective_visibility_or_execution_authority{return Err(E::Binding);}
        let selected=data.search().scope_receipt();let scope=SourceSearchScopeReceipt {kind:selected.kind,scope_sha256:selected.scope_sha256,
            selected_paragraphs:selected.selected_paragraphs,selected_blocks:selected.selected_blocks,whole_document_visibility_qualified:false};
        let result=SearchResult::ResolvedStyle(ResolvedStyleResult {data,scope});
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
}
