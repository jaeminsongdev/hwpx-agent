//! Actual private daemon dispatch -> original strict product -> current private file stage.
use super::*;
use local_companion_daemon::{DaemonError, bookmark_preview722::{BookmarkPreviewRuntime,
    BookmarkWorkspaceBinding, BookmarkWorkspaceContext, BookmarkPreviewMetadata}};

/// Provider and configured workspace binding are trusted host inputs, never public JSON.
/// This borrowing adapter avoids provider/source clones and does not install a live runtime.
pub struct CurrentBookmarkPreviewHost<'a,'p,R,B,S,V> {
    provider:&'a StoredFormProvider<'p,R,B,S,V>, workspace:BookmarkWorkspaceBinding,
}
impl<'a,'p,R,B,S,V> CurrentBookmarkPreviewHost<'a,'p,R,B,S,V> {
    #[must_use]
    pub const fn bind(provider:&'a StoredFormProvider<'p,R,B,S,V>, workspace:BookmarkWorkspaceBinding)->Self { Self{provider,workspace} }
}
impl<R,B,S,V> BookmarkPreviewRuntime for CurrentBookmarkPreviewHost<'_,'_,R,B,S,V>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
    fn stage(&self, context:&BookmarkWorkspaceContext<'_>, raw:&[u8], now:u64)->Result<BookmarkPreviewMetadata,DaemonError>{
        if !self.workspace.matches(context){return Err(DaemonError::Workspace);}
        // Close the operation family before the common dispatcher can read any source.
        ParsedBookmarkInsertionRequest::parse(raw,BookmarkInsertionProductLimits::standard().map_err(|_|DaemonError::Request)?)
            .map_err(|_|DaemonError::Request)?;
        let operation=StoredProductRequest::prepare_json(self.provider,raw,None,now).map_err(|_|DaemonError::Request)?;
        let product=operation.as_bookmark_insertion().ok_or(DaemonError::Request)?;
        let receipt=product.stage_private_local_preview(self.provider,context.workflow(),context.operation_id(),now)
            .map_err(|_|DaemonError::Request)?;
        if !receipt.current_source_checked_before_and_after_staging || !receipt.private_preview_not_publish_candidate
            || receipt.publication_execution_or_revision_adoption_authority {return Err(DaemonError::Request);}
        BookmarkPreviewMetadata::from_staging(context,&receipt.canonical_request_sha256,&receipt.scoped_request_sha256,
            &hex::encode(receipt.compiled_plan_sha256),&hex::encode(receipt.source_package_sha256),
            &hex::encode(receipt.preview_package_sha256),receipt.preview_bytes)
    }
}
