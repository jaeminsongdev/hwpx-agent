//! Navigation of the private retained result shares its original current-access boundary.
use super::*;
use hwpx_package::document_import::search::navigation::{SourceSearchNavigationRequest,SourceSearchNavigationResult};
impl SearchResult {
    fn navigate(&self,request:&SourceSearchNavigationRequest,context:[u8;32])->Result<SourceSearchNavigationResult,SourceSearchError> {
        match self {Self::Text(r)=>r.navigate(request,context),Self::Inspection(r)=>r.navigate(request,context),
            Self::Definitions(r)=>r.navigate(request,context),Self::Reviews(r)=>r.navigate(request,context),Self::Scope(r)=>r.navigate(request,context),Self::ReviewScope(r)=>r.navigate(request,context),Self::ReviewStyle(r)=>r.navigate(request,context),Self::ReviewControl(r)=>r.navigate(request,context),Self::ResolvedStyle(r)=>r.navigate(request,context)}
    }
}
impl PreparedStoredSourceSearch {
    /// Only the product adapter supplies context derived from its immutable full receipt.
    pub(crate) fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        request:&SourceSearchNavigationRequest,context:[u8;32],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        // Retain all original source/ACL/AEAD/head/result checks. Discard this
        // temporary full response before cloning just one selected occurrence.
        drop(self.fresh_json(provider,now)?);
        let bytes=self.result.navigate(request,context)?.canonical_json()?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(consume(&bytes))
    }
}
