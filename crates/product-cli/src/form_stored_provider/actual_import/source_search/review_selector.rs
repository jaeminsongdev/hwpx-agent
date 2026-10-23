//! Review-aware scope discovery/search shares the original sealed-result access and final head.
use super::*;
use hwpx_package::document_import::search::navigation as source_navigation;
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,
    reviews::selector::{SourceReviewScopeInventory,SourceReviewSelectorResult}};
#[derive(Clone,Copy,Debug)]
pub enum SourceReviewScopeOperation<'a> {Inventory,Find {query:SourceSearchQuery<'a>,selector:SourceIndexScopeSelector<'a>,policy:SourceReviewTextPolicy}}
enum ReviewScopeData {Inventory(SourceReviewScopeInventory),Find(SourceReviewSelectorResult)}
pub(super) struct ReviewScopeResult {data:ReviewScopeData,pub scope:SourceSearchScopeReceipt,pub request_sha:[u8;32]}
impl ReviewScopeResult {
    pub(super) fn navigate(&self,request:&source_navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<source_navigation::SourceSearchNavigationResult,SourceSearchError> {
        match &self.data {ReviewScopeData::Inventory(_)=>Err(SourceSearchError::Cursor),ReviewScopeData::Find(r)=>r.navigate(request,context)}
    }
    pub(super) fn index(&self)->&SourceSearchIndexReceipt {match &self.data {ReviewScopeData::Inventory(i)=>&i.inventory.index,ReviewScopeData::Find(r)=>r.result().index_receipt()}}
    pub(super) fn json(&self)->Result<Vec<u8>,SourceSearchError> {match &self.data {ReviewScopeData::Inventory(i)=>i.canonical_json(),ReviewScopeData::Find(r)=>r.canonical_json()}}
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Current write/scope/head/ACL/quarantine/AEAD and one complete original Form proof.
    pub fn into_review_source_scope<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,operation:SourceReviewScopeOperation<'_>,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;let index=proof.source_review_scope_index(&self.imported,limits)?;
        let result=match operation {
            SourceReviewScopeOperation::Inventory=>{let inventory=index.scope_inventory()?;
                let sha=Sha256::digest(inventory.canonical_json()?).into();
                ReviewScopeResult {scope:SourceSearchScopeReceipt {kind:"review_scope_inventory",scope_sha256:sha,selected_paragraphs:0,selected_blocks:0,whole_document_visibility_qualified:false},
                    request_sha:sha,data:ReviewScopeData::Inventory(inventory)}},
            SourceReviewScopeOperation::Find {query,selector,policy}=>{let found=index.find(query,selector,policy)?;let scope=found.scope_receipt();
                ReviewScopeResult {scope:SourceSearchScopeReceipt {kind:scope.kind,scope_sha256:scope.scope_sha256,selected_paragraphs:scope.selected_paragraphs,selected_blocks:scope.selected_blocks,
                    whole_document_visibility_qualified:false},request_sha:found.request_sha256(),data:ReviewScopeData::Find(found)}},
        };
        let result=SearchResult::ReviewScope(result);
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
}
