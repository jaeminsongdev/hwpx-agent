//! Current sealed source -> original control-anchor scope, sharing original access and final head.
use super::*;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,navigation as source_navigation,
    reviews::selector::controls::SourceReviewSelectorControlResult};
pub(super) struct ReviewControlResult {data:SourceReviewSelectorControlResult,pub scope:SourceSearchScopeReceipt}
impl ReviewControlResult {
    pub(super) fn index(&self)->&SourceSearchIndexReceipt {self.data.index_receipt()}
    pub(super) fn request_sha(&self)->[u8;32] {self.data.request_sha256()}
    pub(super) fn json(&self)->Result<Vec<u8>,SourceSearchError> {self.data.canonical_json()}
    pub(super) fn navigate(&self,request:&source_navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<source_navigation::SourceSearchNavigationResult,SourceSearchError> {self.data.navigate(request,context)}
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// One current write/scope/head/ACL/quarantine/AEAD reconstruction and original source proof.
    pub fn into_review_control_search<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        kind:SourceControlKind,max_results:usize,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;let index=proof.source_review_scope_index(&self.imported,limits)?;
        let data=index.find_control(selector,policy,kind,max_results)?;let selected=data.scope_receipt();
        let scope=SourceSearchScopeReceipt {kind:selected.kind,scope_sha256:selected.scope_sha256,selected_paragraphs:selected.selected_paragraphs,
            selected_blocks:selected.selected_blocks,whole_document_visibility_qualified:false};
        let result=SearchResult::ReviewControl(ReviewControlResult {data,scope});
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
}
