//! Nonmutating common preview, never a SearchMutation, compiled plan or execution manifest owner.
use super::*;
use super::super::stored_literal_replacement::fonts::options::{PreparedStoredFontOptionsProduct,StoredFontOptionsProductRequest,
    FontOptionsProductReceipt,FontOptionsProductError};
pub struct PreparedStoredSearchPreview{product:PreparedStoredFontOptionsProduct}
impl std::fmt::Debug for PreparedStoredSearchPreview{
    fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result{f.write_str("PreparedStoredSearchPreview(<redacted>; no_output_or_compiler)")}
}
pub(super) fn prepare<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:search_mutations::SearchMutationLimits,now:u64)
    ->Result<PreparedStoredSearchPreview,FontOptionsProductError>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    let product=StoredFontOptionsProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?;
    Ok(PreparedStoredSearchPreview{product})
}
impl PreparedStoredSearchPreview{
    #[must_use]pub const fn receipt(&self)->&FontOptionsProductReceipt{self.product.receipt()}
    /// # Errors
    /// Original current source/access and head checks; no matching or lowering replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<FontOptionsProductReceipt,FontOptionsProductError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.verify(provider,now)}
    /// # Errors
    /// Metadata only. The original fresh current checks include the consumer-final head.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,FontOptionsProductError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.with_verified_json(provider,now,consume)}
    /// # Errors
    /// Preview never grants execution/CAS/publication, even after current verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),FontOptionsProductError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.require_current_product_route(provider,now)}
}
