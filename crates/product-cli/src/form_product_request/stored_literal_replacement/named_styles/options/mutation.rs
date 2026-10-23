//! Mutation-only original owner and a preview with no output/compiler API.
use super::*;
pub struct PreparedStoredNamedStyleOptionsMutation{request:Request,candidate:PreparedStoredNamedStyleOptionsCandidate<'static>,receipt:NamedStyleOptionsProductReceipt,maximum_metadata_bytes:usize}
compiler_product!(PreparedStoredNamedStyleOptionsMutation,request,plain);
search_lookup_product!(StoredNamedStyleOptionsMutationRequest,|raw|Request::parse(raw),root,normal,mutation);
impl fmt::Debug for PreparedStoredNamedStyleOptionsMutation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleOptionsMutation(<redacted>; route_unqualified)")}}
pub struct PreparedStoredNamedStyleOptionsPreviewProduct{product:PreparedStoredNamedStyleOptionsProduct}
impl fmt::Debug for PreparedStoredNamedStyleOptionsPreviewProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleOptionsPreviewProduct(<redacted>; no_output_or_compiler)")}}
#[derive(Debug)]pub struct StoredNamedStyleOptionsMutationRequest;
pub(crate) fn preview_mode(raw:&[u8])->Result<bool,X>{Ok(Request::parse(raw)?.operation.preview_only)}
impl StoredNamedStyleOptionsProductRequest{
    pub(crate) fn prepare_preview_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleOptionsPreviewProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if !request.operation.preview_only{return Err(X::Request);}
        Ok(PreparedStoredNamedStyleOptionsPreviewProduct{product:Self::prepare_parsed(provider,raw,request,limits,writer,now)?})
    }
}
impl StoredNamedStyleOptionsMutationRequest{
    /// # Errors
    /// Full strict v2 parsing; previews are rejected before authorized source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleOptionsMutation,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if request.operation.preview_only{return Err(X::PreviewOnly);}
        let product=StoredNamedStyleOptionsProductRequest::prepare_parsed(provider,raw,request,limits,writer,now)?;
        let PreparedStoredNamedStyleOptionsProduct{request,prepared,receipt,maximum_metadata_bytes}=product;let Prepared::Candidate(candidate)=prepared else{return Err(X::Binding)};
        Ok(PreparedStoredNamedStyleOptionsMutation{request,candidate,receipt,maximum_metadata_bytes})
    }
}
impl PreparedStoredNamedStyleOptionsMutation{
    #[must_use]pub const fn receipt(&self)->&NamedStyleOptionsProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if self.request.operation.preview_only{return Err(X::Binding);}check_binding(&self.request,&self.receipt,self.candidate.receipt(),self.maximum_metadata_bytes,provider)
    }
    /// # Errors
    /// Current source/access/writer integrity without name/filter/lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NamedStyleOptionsProductReceipt,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(X::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original current byte verification and consumer-final head remain the only delivery path.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// A compilable candidate is not current execution/CAS/publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(X::RouteUnqualified)}
}
impl PreparedStoredNamedStyleOptionsPreviewProduct{
    #[must_use]pub const fn receipt(&self)->&NamedStyleOptionsProductReceipt{self.product.receipt()}
    /// # Errors
    /// Current source/access only; predicted metadata is not a retained output artifact.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NamedStyleOptionsProductReceipt,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.verify(provider,now)}
    /// # Errors
    /// Bounded metadata only, through the original consumer-final head check.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.with_verified_json(provider,now,consume)}
    /// # Errors
    /// No bytes/inventory/compile API or reverse conversion; all route denials retained.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.require_current_product_route(provider,now)}
}
