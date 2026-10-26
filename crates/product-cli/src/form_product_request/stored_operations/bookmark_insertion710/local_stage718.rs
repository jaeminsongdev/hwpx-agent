//! Authenticated current product -> private generated preview, never public candidate promotion.
use super::*;
use local_workflow::{GeneratedPreviewReceipt,LocalWorkflow,WorkflowError};
#[derive(Debug,Error)]
pub enum LocalBookmarkStageError{
    #[error("LOCAL_BOOKMARK_STAGE_CURRENT_PRODUCT_DENIED")]Product(#[from]BookmarkInsertionProductError),
    #[error("LOCAL_BOOKMARK_STAGE_WORKSPACE_DENIED")]Workspace(#[from]WorkflowError),
    #[error("LOCAL_BOOKMARK_STAGE_BINDING_DENIED")]Binding,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct LocalBookmarkStageReceipt{
    pub profile:&'static str,pub operation_id:String,pub workspace_binding_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub compiled_plan_sha256:[u8;32],
    pub source_package_sha256:[u8;32],pub preview_package_sha256:[u8;32],pub preview_bytes:u64,
    pub current_source_checked_before_and_after_staging:bool,pub private_preview_not_publish_candidate:bool,
    pub publication_execution_or_revision_adoption_authority:bool,
}
fn matches(receipt:&GeneratedPreviewReceipt,source:&[u8;32],output:&[u8;32])->bool{
    receipt.profile=="hwpx-agent.local-generated-preview/unqualified-v1"
        &&receipt.source.sha256==hex::encode(source)&&receipt.preview.sha256==hex::encode(output)
        &&!receipt.publication_or_revision_authority
}
impl PreparedBookmarkInsertionProduct{
    /// The host owns the configured workspace and managed source, never the public JSON caller.
    /// This private preview cannot be read by the existing public publish candidate slot.
    /// # Errors
    /// Original final writer-callback ACL/head/AEAD check precedes create-new I/O.
    /// A fresh check after disk readback must also succeed. Failures preserve the
    /// private unqualified file, without any new result/head/registry/Native grant.
    pub fn stage_private_local_preview<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        workspace:&LocalWorkflow,operation_id:&str,now:u64)->Result<LocalBookmarkStageReceipt,LocalBookmarkStageError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let bound=&self.receipt.compiled;
        let staged=self.with_verified_bytes(provider,now,|bytes|workspace.stage_generated_preview(
            operation_id,&bound.source_package_sha256,&bound.output_package_sha256,bytes))??;
        let fresh=workspace.inspect_generated_preview(operation_id,&bound.source_package_sha256,&bound.output_package_sha256)?;
        if staged!=fresh||!matches(&fresh,&bound.source_package_sha256,&bound.output_package_sha256){return Err(LocalBookmarkStageError::Binding);}
        self.verify(provider,now)?;
        Ok(LocalBookmarkStageReceipt{profile:"hwpx-agent.current-bookmark-private-local-staging/v1",
            operation_id:staged.operation_id,workspace_binding_sha256:staged.workspace_binding_sha256,
            canonical_request_sha256:self.receipt.canonical_request_sha256.clone(),scoped_request_sha256:self.receipt.scoped_request_sha256.clone(),
            compiled_plan_sha256:bound.compiled_plan_sha256,source_package_sha256:bound.source_package_sha256,
            preview_package_sha256:bound.output_package_sha256,preview_bytes:staged.preview.size_bytes,
            current_source_checked_before_and_after_staging:true,private_preview_not_publish_candidate:true,
            publication_execution_or_revision_adoption_authority:false})
    }
}
