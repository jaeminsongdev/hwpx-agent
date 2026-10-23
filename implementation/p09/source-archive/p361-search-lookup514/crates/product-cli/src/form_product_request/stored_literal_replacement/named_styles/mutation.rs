//! Opaque mode-specific owners. Only a mutation can supply a compiler view.
use super::*;
pub struct PreparedStoredNamedStyleMutation{request:Request,candidate:PreparedStoredNamedStyleCandidate<'static>,receipt:NamedStyleProductReceipt,maximum_metadata_bytes:usize}
compiler_product!(PreparedStoredNamedStyleMutation,request,plain);
impl fmt::Debug for PreparedStoredNamedStyleMutation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleMutation(<redacted>; route_unqualified)")}}
pub struct PreparedStoredNamedStylePreviewProduct{product:PreparedStoredNamedStyleProduct}
impl fmt::Debug for PreparedStoredNamedStylePreviewProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStylePreviewProduct(<redacted>; no_output_or_compiler)")}}
#[derive(Debug)]pub struct StoredNamedStyleMutationRequest;
pub(crate) fn preview_mode(raw:&[u8])->Result<bool,N>{Ok(Request::parse(raw)?.operation.preview_only)}
impl StoredNamedStyleProductRequest{
    pub(crate) fn prepare_preview_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStylePreviewProduct,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if !request.operation.preview_only{return Err(N::Request);}
        let product=Self::prepare_parsed(provider,raw,request,limits,writer,now)?;Ok(PreparedStoredNamedStylePreviewProduct{product})
    }
}
impl StoredNamedStyleMutationRequest{
    /// # Errors
    /// Full strict parsing; preview is rejected before any authorized source read.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleMutation,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if request.operation.preview_only{return Err(N::PreviewOnly);}
        let product=StoredNamedStyleProductRequest::prepare_parsed(provider,raw,request,limits,writer,now)?;
        let PreparedStoredNamedStyleProduct{request,prepared,receipt,maximum_metadata_bytes}=product;
        let Prepared::Candidate(candidate)=prepared else{return Err(N::Binding)};
        Ok(PreparedStoredNamedStyleMutation{request,candidate,receipt,maximum_metadata_bytes})
    }
}
impl PreparedStoredNamedStyleMutation{
    #[must_use]pub const fn receipt(&self)->&NamedStyleProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if self.request.operation.preview_only{return Err(N::Binding);}check_binding(&self.request,&self.receipt,self.candidate.receipt(),self.maximum_metadata_bytes,provider)
    }
    /// # Errors
    /// Current original source/access/head/writer checks, without matching or lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NamedStyleProductReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(N::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Only the original fresh byte-integrity and consumer-final head boundary delivers output.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// Compilable metadata never grants execution, CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
impl PreparedStoredNamedStylePreviewProduct{
    #[must_use]pub const fn receipt(&self)->&NamedStyleProductReceipt{self.product.receipt()}
    /// # Errors
    /// Current access and source integrity, not a retained output artifact.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NamedStyleProductReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.verify(provider,now)}
    /// # Errors
    /// Metadata only; the original consumer-final head check is retained.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.with_verified_json(provider,now,consume)}
    /// # Errors
    /// No bytes/inventory/compile API or reverse conversion exists on this type.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.require_current_product_route(provider,now)}
}
