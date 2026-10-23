//! Opaque mode-specific owners. Only a mutation owns a compiler source and edit inventory.
use super::*;
pub struct PreparedStoredPersonalInfoMaskMutation{request:Request,candidate:PreparedStoredPersonalInfoMaskCandidate<'static>,receipt:PersonalInfoMaskProductReceipt,maximum_metadata_bytes:usize}
compiler_product!(PreparedStoredPersonalInfoMaskMutation,request,plain);
impl fmt::Debug for PreparedStoredPersonalInfoMaskMutation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoMaskMutation(<redacted>; route_unqualified)")}}
pub struct PreparedStoredPersonalInfoMaskPreviewProduct{product:PreparedStoredPersonalInfoMaskProduct}
impl fmt::Debug for PreparedStoredPersonalInfoMaskPreviewProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoMaskPreviewProduct(<redacted>; no_output_or_compiler)")}}
#[derive(Debug)]pub struct StoredPersonalInfoMaskMutationRequest;
pub(crate) fn preview_mode(raw:&[u8])->Result<bool,M>{Ok(Request::parse(raw)?.operation.preview_only)}
impl StoredPersonalInfoMaskProductRequest{
    pub(crate) fn prepare_preview_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskPreviewProduct,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=Request::parse(raw)?;if !r.operation.preview_only{return Err(M::Request);}
        Ok(PreparedStoredPersonalInfoMaskPreviewProduct{product:Self::prepare_parsed(provider,raw,r,limits,writer,now)?})
    }
}
impl StoredPersonalInfoMaskMutationRequest{
    /// # Errors
    /// Preview is rejected by strict parsing before any source or artifact access.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskMutation,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=Request::parse(raw)?;if r.operation.preview_only{return Err(M::PreviewOnly);}
        let p=StoredPersonalInfoMaskProductRequest::prepare_parsed(provider,raw,r,limits,writer,now)?;
        let PreparedStoredPersonalInfoMaskProduct{request,prepared,receipt,maximum_metadata_bytes}=p;let Prepared::Candidate(candidate)=prepared else{return Err(M::Binding)};
        Ok(PreparedStoredPersonalInfoMaskMutation{request,candidate,receipt,maximum_metadata_bytes})
    }
}
impl PreparedStoredPersonalInfoMaskMutation{
    pub(crate) fn compiler_mask_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory{self.candidate.compiler_mask_inventory()}
    #[must_use]pub const fn receipt(&self)->&PersonalInfoMaskProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if self.request.operation.preview_only{return Err(M::Binding);}check_binding(&self.request,&self.receipt,self.candidate.receipt(),provider)
    }
    /// # Errors
    /// Current source/access/head/writer checks without masking or lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<PersonalInfoMaskProductReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(M::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Only the original fresh writer callback exposes bytes after its final head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// Bounded metadata retains the original current access and consumer-final head boundary.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let b=bounded(&self.receipt,self.maximum_metadata_bytes).map_err(|_|M::Limit)?;Ok(self.candidate.with_verified_bytes(provider,now,|_|consume(&b))?)
    }
    /// # Errors
    /// A compilable mutation is not a qualified execution/commit/publication route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
impl PreparedStoredPersonalInfoMaskPreviewProduct{
    #[must_use]pub const fn receipt(&self)->&PersonalInfoMaskProductReceipt{self.product.receipt()}
    /// # Errors
    /// Current original source/access, never a retained output artifact or compiled plan.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<PersonalInfoMaskProductReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.verify(provider,now)}
    /// # Errors
    /// Only metadata can be delivered; this type has no byte/inventory/compiler API or reverse conversion.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.with_verified_json(provider,now,consume)}
    /// # Errors
    /// A preview can never execute, commit or publish.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.product.require_current_product_route(provider,now)}
}
