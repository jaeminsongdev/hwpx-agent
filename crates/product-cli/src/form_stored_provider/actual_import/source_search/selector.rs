//! Scope discovery/search uses the original stored result authorization and final head boundary.
use super::*;
use hwpx_package::document_import::search::navigation as source_navigation;
use hwpx_package::document_import::search::selector::{SourceIndexScopeSelector,SourceSelectorSearchResult,inventory::SourceScopeInventory};
#[derive(Clone,Copy,Debug)]
pub enum SourceScopeOperation<'a> {Inventory,Find {query:SourceSearchQuery<'a>,selector:SourceIndexScopeSelector<'a>}}
enum ScopeData {Inventory(SourceScopeInventory),Find(SourceSelectorSearchResult)}
pub(super) struct ScopeResult {data:ScopeData,pub scope:SourceSearchScopeReceipt,pub request_sha:[u8;32]}
impl ScopeResult {
    pub(super) fn navigate(&self,request:&source_navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<source_navigation::SourceSearchNavigationResult,SourceSearchError> {
        match &self.data {ScopeData::Inventory(_)=>Err(SourceSearchError::Cursor),ScopeData::Find(r)=>r.navigate(request,context)}
    }
    pub(super) fn index(&self)->&SourceSearchIndexReceipt {match &self.data {ScopeData::Inventory(i)=>&i.index,ScopeData::Find(r)=>r.result().index_receipt()}}
    pub(super) fn json(&self)->Result<Vec<u8>,SourceSearchError> {match &self.data {ScopeData::Inventory(i)=>i.canonical_json(),ScopeData::Find(r)=>r.canonical_json()}}
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Same current write/scope/head/ACL/AEAD and one complete Form reconstruction as original search.
    pub fn into_source_scope<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,operation:SourceScopeOperation<'_>,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;let index=proof.source_text_index(&self.imported,limits)?;
        let result=match operation {
            SourceScopeOperation::Inventory=>{let inventory=index.scope_inventory()?;let sha=inventory.binding_sha256()?;
                ScopeResult {scope:SourceSearchScopeReceipt {kind:"scope_inventory",scope_sha256:sha,selected_paragraphs:0,selected_blocks:0,whole_document_visibility_qualified:false},
                    request_sha:sha,data:ScopeData::Inventory(inventory)}},
            SourceScopeOperation::Find {query,selector}=>{let found=index.find_selector(query,selector)?;let scope=found.scope_receipt();
                ScopeResult {scope:SourceSearchScopeReceipt {kind:scope.kind,scope_sha256:scope.scope_sha256,selected_paragraphs:scope.selected_paragraphs,selected_blocks:scope.selected_blocks,
                    whole_document_visibility_qualified:false},request_sha:found.request_sha256(),data:ScopeData::Find(found)}},
        };
        let result=SearchResult::Scope(result);
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
}
