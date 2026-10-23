//! Fresh sealed source -> selected-text mask or output-discarded preview, not sanitized/publication authority.
use super::*;
use super::product::LiteralSource;
compiler_source!(PreparedStoredPersonalInfoMaskCandidate);
use hwpx_package::document_import::search::{selector::SourceIndexScopeSelector,reviews::SourceReviewTextPolicy,
    replacement::atoms::personal_info::{SourcePersonalInfoMaskCandidate,SourcePersonalInfoMaskReceipt,SourcePersonalInfoMaskPolicy,SOURCE_PERSONAL_INFO_MASK_PROFILE}};
pub const STORED_PERSONAL_INFO_MASK_PROFILE:&str="hwpx-agent.stored-personal-info-mask-candidate/v1";
pub const STORED_PERSONAL_INFO_MASK_PREVIEW_PROFILE:&str="hwpx-agent.stored-personal-info-mask-preview/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredPersonalInfoMaskReceipt{pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:SourcePersonalInfoMaskReceipt,
    pub preview_only:bool,pub candidate_output_retained:bool,pub issuer_execution_publication_authority:bool}
pub struct PreparedStoredPersonalInfoMaskCandidate<'a>{source:LiteralSource<'a>,output:SourcePersonalInfoMaskCandidate,receipt:StoredPersonalInfoMaskReceipt,maximum_metadata_bytes:usize}
pub struct PreparedStoredPersonalInfoMaskPreview<'a>{source:LiteralSource<'a>,receipt:StoredPersonalInfoMaskReceipt,maximum_metadata_bytes:usize}
impl fmt::Debug for PreparedStoredPersonalInfoMaskCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoMaskCandidate(<redacted>; selected_text_only_not_sanitized_document)")}}
impl fmt::Debug for PreparedStoredPersonalInfoMaskPreview<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoMaskPreview(<redacted>; output_discarded)")}}
#[derive(Debug,Error)]
pub enum StoredPersonalInfoMaskError{
    #[error("STORED_PERSONAL_INFO_MASK_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_PERSONAL_INFO_MASK_OUTPUT_REJECTED")]Output(#[from]SourceLiteralReplacementError),
    #[error("STORED_PERSONAL_INFO_MASK_WRITE_SCOPE_REQUIRED")]Permission,
    #[error("STORED_PERSONAL_INFO_MASK_BINDING_REJECTED")]Binding,
    #[error("STORED_PERSONAL_INFO_MASK_INTEGRITY_REJECTED")]Integrity,
    #[error("STORED_PERSONAL_INFO_MASK_METADATA_LIMIT")]Limit,
    #[error("STORED_PERSONAL_INFO_MASK_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type M=StoredPersonalInfoMaskError;
pub(crate) fn mask_receipt_matches(r:&SourcePersonalInfoMaskReceipt,source:[u8;32])->bool{
    r.profile==SOURCE_PERSONAL_INFO_MASK_PROFILE&&r.source_package_sha256==source&&source!=[0;32]&&r.source_index_sha256!=[0;32]&&r.request_sha256!=[0;32]
        &&r.selector.index_sha256==r.source_index_sha256&&r.selector.scope_sha256!=[0;32]&&r.selector.selected_blocks>0
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.selected_original_scalars>0&&r.selected_text_groups>0&&r.changed_components>0&&r.changed_scalar_ranges>0&&r.changed_parts>0
        &&r.output_bytes>0&&r.output_package_sha256!=[0;32]&&r.output_package_sha256!=source
        &&r.exact_original_selection_verified&&r.original_run_shells_styles_controls_and_references_preserved&&r.output_spans_and_outside_slots_verified
        &&!r.selector.whole_document_visibility_native_flow_or_revision_authority&&!r.whole_package_personal_data_removed&&!r.native_mask_semantics_or_service_execution_qualified
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Current document.write/source/whole proof and one original masked candidate; no source mutation.
    pub fn prepare_personal_info_mask_candidate<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskCandidate<'_>,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let output=proof.lower_personal_info_mask_candidate(&self.imported,selector,body,policy,limits,writer)?;
        if !mask_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(M::Binding);}
        let receipt=StoredPersonalInfoMaskReceipt{profile:STORED_PERSONAL_INFO_MASK_PROFILE,source:self.receipt.clone(),output:output.receipt().clone(),preview_only:false,
            candidate_output_retained:true,issuer_execution_publication_authority:false};
        metadata_bound(&receipt,limits.maximum_result_bytes())?;provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredPersonalInfoMaskCandidate{source:LiteralSource::Borrowed(self),output,receipt,maximum_metadata_bytes:limits.maximum_result_bytes()})
    }
    /// # Errors
    /// Move the original owner after shared preparation, without a source clone, second index or lowering replay.
    pub fn into_personal_info_mask_candidate<Rp,B,S,V>(self,provider:&StoredFormProvider<'_,Rp,B,S,V>,selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskCandidate<'static>,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(output,receipt,maximum_metadata_bytes)={let prepared=self.prepare_personal_info_mask_candidate(provider,selector,body,policy,limits,writer,now)?;
            (prepared.output,prepared.receipt,prepared.maximum_metadata_bytes)};
        Ok(PreparedStoredPersonalInfoMaskCandidate{source:LiteralSource::Owned(Box::new(self)),output,receipt,maximum_metadata_bytes})
    }
}
fn fresh<Rp,B,S,V>(source:&StoredImportedDocumentForms,r:&StoredPersonalInfoMaskReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,preview:bool,maximum:usize)->Result<(),M>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
    let current=source.fresh_source(provider,now)?;let profile=if preview{STORED_PERSONAL_INFO_MASK_PREVIEW_PROFILE}else{STORED_PERSONAL_INFO_MASK_PROFILE};
    if r.profile!=profile||r.source!=source.receipt||r.preview_only!=preview||r.candidate_output_retained==preview||r.issuer_execution_publication_authority
        ||!mask_receipt_matches(&r.output,*current.digest.as_bytes()){return Err(M::Binding);}metadata_bound(r,maximum)
}
impl<'a> PreparedStoredPersonalInfoMaskCandidate<'a>{
    pub(crate) fn compiler_mask_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory{self.output.edit_inventory()}
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoMaskReceipt{&self.receipt}
    /// # Errors
    /// Drops the artifact and preserves only source owner plus bounded predicted metadata; no reverse conversion.
    pub fn into_preview(self)->Result<PreparedStoredPersonalInfoMaskPreview<'a>,M>{
        let Self{source,output,mut receipt,maximum_metadata_bytes}=self;drop(output);receipt.profile=STORED_PERSONAL_INFO_MASK_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;
        metadata_bound(&receipt,maximum_metadata_bytes)?;Ok(PreparedStoredPersonalInfoMaskPreview{source,receipt,maximum_metadata_bytes})
    }
    pub(crate) fn check_final_head<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())}
    /// # Errors
    /// Current access/source and retained writer integrity without masking/index/writer replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredPersonalInfoMaskReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_bytes(provider,now,|_|())?;Ok(self.receipt.clone())}
    /// # Errors
    /// Fresh ACL/AEAD/head and immutable writer integrity precede the consumer-final head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,false,self.maximum_metadata_bytes)?;if &self.receipt.output!=self.output.receipt(){return Err(M::Binding);}
        self.output.with_verified_bytes(|bytes|{self.check_final_head(provider)?;Ok(consume(bytes))}).map_err(|_|M::Integrity)?
    }
    /// # Errors
    /// Prepared masks never qualify a current execution, CAS, publication or sanitized-output route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
impl PreparedStoredPersonalInfoMaskPreview<'_>{
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoMaskReceipt{&self.receipt}
    pub(crate) fn check_final_head<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())}
    /// # Errors
    /// Predicted bounded metadata only, after current source access and the consumer-final head.
    pub fn with_verified_metadata<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&StoredPersonalInfoMaskReceipt)->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,provider,now,true,self.maximum_metadata_bytes)?;self.check_final_head(provider)?;Ok(consume(&self.receipt))
    }
    /// # Errors
    /// Verifies original source/access, not an output artifact or executed operation.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<StoredPersonalInfoMaskReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_metadata(provider,now,Clone::clone)}
    /// # Errors
    /// No bytes, compiler view, inventory or reverse conversion is available on previews.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
fn metadata_bound(value:&impl Serialize,maximum:usize)->Result<(),M>{
    struct Count{length:usize,maximum:usize}
    impl std::io::Write for Count{fn write(&mut self,b:&[u8])->std::io::Result<usize>{self.length=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum).ok_or_else(||std::io::Error::other("personal_info_mask_metadata_limit"))?;
        Ok(b.len())}fn flush(&mut self)->std::io::Result<()>{Ok(())}}
    let mut out=Count{length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|M::Limit)
}
