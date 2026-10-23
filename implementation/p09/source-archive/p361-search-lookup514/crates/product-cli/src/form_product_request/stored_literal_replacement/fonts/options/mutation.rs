//! Mutation-only owner. A preview cannot construct this type or obtain a compiler view.
use super::*;
pub struct PreparedStoredFontOptionsMutation{request:Request,candidate:PreparedStoredFontOptionsCandidate<'static>,receipt:FontOptionsProductReceipt}
compiler_product!(PreparedStoredFontOptionsMutation,request,plain);
impl fmt::Debug for PreparedStoredFontOptionsMutation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontOptionsMutation(<redacted>; route_unqualified)")}}
#[derive(Debug)]pub struct StoredFontOptionsMutationRequest;
pub(crate) fn preview_mode(raw:&[u8])->Result<bool,X>{Ok(Request::parse(raw)?.operation.preview_only)}
impl StoredFontOptionsProductRequest{
    pub(crate) fn prepare_preview_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontOptionsProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if !request.operation.preview_only{return Err(X::Request);}
        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
}
impl StoredFontOptionsMutationRequest{
    /// # Errors
    /// Full strict v2 request, but preview is rejected before source reads or candidate generation.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontOptionsMutation,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if request.operation.preview_only{return Err(X::PreviewOnly);}
        let product=StoredFontOptionsProductRequest::prepare_parsed(provider,raw,request,limits,writer,now)?;
        let PreparedStoredFontOptionsProduct{request,prepared,receipt}=product;
        let Prepared::Candidate(candidate)=prepared else{return Err(X::Binding)};
        Ok(PreparedStoredFontOptionsMutation{request,candidate,receipt})
    }
}
impl PreparedStoredFontOptionsMutation{
    #[must_use]pub const fn receipt(&self)->&FontOptionsProductReceipt{&self.receipt}
    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{self.candidate.compiler_font_inventory()}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if self.request.operation.preview_only{return Err(X::Binding);}check_binding(&self.request,&self.receipt,self.candidate.receipt(),provider)
    }
    /// # Errors
    /// Current scope/source/writer integrity and final head; never repeats matching or lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<FontOptionsProductReceipt,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(X::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retains the original current-authority and consumer-final head boundary.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// Exact font resource/body inventory, through the same fresh byte-integrity checks.
    pub fn with_verified_edit_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory)->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,now,|_|consume(self.candidate.compiler_font_inventory()))
    }
    /// # Errors
    /// Compilable metadata is not qualified execution/CAS/publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(X::RouteUnqualified)}
}
