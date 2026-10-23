//! Current document/config -> retained catalog-matched mask. No ingest, CAS, Native or publication path.
use super::*;
use hwpx_package::document_import::search::replacement::atoms::personal_info::{SourcePersonalInfoMaskPolicy,
    catalog::{SourcePersonalInfoCatalogMaskCandidate,SourcePersonalInfoCatalogMaskReceipt,
        SourcePersonalInfoCatalogMaskError,SOURCE_PERSONAL_INFO_CATALOG_MASK_PROFILE}};
pub const STORED_PERSONAL_INFO_CATALOG_MASK_PROFILE:&str="hwpx-agent.stored-personal-info-catalog-mask/v1";
pub const STORED_PERSONAL_INFO_CATALOG_MASK_PREVIEW_PROFILE:&str="hwpx-agent.stored-personal-info-catalog-mask-preview/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredPersonalInfoCatalogMaskReceipt{
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub output:SourcePersonalInfoCatalogMaskReceipt,
    pub preview_only:bool,pub candidate_output_retained:bool,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredPersonalInfoCatalogMaskCandidate{source:StoredImportedDocumentForms,
    output:SourcePersonalInfoCatalogMaskCandidate,receipt:StoredPersonalInfoCatalogMaskReceipt,maximum:usize}
pub struct PreparedStoredPersonalInfoCatalogMaskPreview{source:StoredImportedDocumentForms,receipt:StoredPersonalInfoCatalogMaskReceipt,maximum:usize}
impl fmt::Debug for PreparedStoredPersonalInfoCatalogMaskCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredPersonalInfoCatalogMaskCandidate(<redacted>; matched_text_not_anonymized_document)")}}
impl fmt::Debug for PreparedStoredPersonalInfoCatalogMaskPreview{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredPersonalInfoCatalogMaskPreview(<redacted>; metadata_only_no_candidate_bytes)")}}
#[derive(Debug,Error)]pub enum StoredPersonalInfoCatalogMaskError{
    #[error("STORED_CATALOG_MASK_ACCESS_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_CATALOG_MASK_CURRENT_FORMAT_REJECTED")]Catalog(#[from]StoredPersonalInfoCatalogError),
    #[error("STORED_CATALOG_MASK_OUTPUT_REJECTED")]Output(#[from]SourcePersonalInfoCatalogMaskError),
    #[error("STORED_CATALOG_MASK_METADATA_REJECTED")]Metadata(#[from]StoredPersonalInfoDetectionError),
    #[error("STORED_CATALOG_MASK_DOCUMENT_WRITE_REQUIRED")]Permission,
    #[error("STORED_CATALOG_MASK_BINDING_REJECTED")]Binding,
    #[error("STORED_CATALOG_MASK_WRITER_INTEGRITY_REJECTED")]Integrity,
    #[error("STORED_CATALOG_MASK_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type M=StoredPersonalInfoCatalogMaskError;
pub(crate) fn catalog_mask_receipt_matches(r:&SourcePersonalInfoCatalogMaskReceipt,source:[u8;32])->bool{
    r.profile==SOURCE_PERSONAL_INFO_CATALOG_MASK_PROFILE&&r.source_package_sha256==source&&source!=[0;32]
        &&r.source_index_sha256!=[0;32]&&r.scope.index_sha256==r.source_index_sha256&&r.scope.scope_sha256!=[0;32]
        &&r.scope.selected_blocks>0&&!r.scope.whole_document_visibility_native_flow_or_revision_authority
        &&r.catalog.source_sha256!=[0;32]&&r.catalog.source_bytes>0&&r.catalog.original_pattern_text_preserved
        &&!r.catalog.installed_vendor_authenticity_or_native_semantics_qualified&&r.catalog_policy_sha256!=[0;32]
        &&r.detection_request_sha256!=[0;32]&&r.detection_result_sha256!=[0;32]&&r.request_sha256!=[0;32]
        &&r.selected_patterns>0&&r.selected_patterns<=r.catalog.total_patterns&&r.matched_formats>0
        &&r.matched_original_scalars>0&&r.matched_text_groups>0&&r.changed_components>0&&r.changed_scalar_ranges>0&&r.changed_parts>0
        &&r.source_review_import.source_package_sha256==source&&r.output_review_import.source_package_sha256==r.output_package_sha256
        &&r.output_package_sha256!=[0;32]&&r.output_package_sha256!=source&&r.output_bytes>0
        &&r.exact_original_match_selections_verified&&r.original_run_shells_styles_controls_and_references_preserved&&r.output_spans_and_outside_slots_verified
        &&!r.whole_package_personal_data_removed&&!r.native_catalog_mask_semantics_or_service_execution_qualified
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Current write/source/proof, all selected catalog patterns and one mask lowering. No source clone, ingest or commit.
    pub fn into_personal_info_catalog_mask_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog_source:&impl CurrentPersonalInfoCatalogSource,
        expected_catalog_sha256:[u8;32],families:&[PersonalInfoCatalogFamily],selector:SourceIndexScopeSelector<'_>,body:SourceReviewTextPolicy,
        policy:SourcePersonalInfoMaskPolicy,limits:SourceSearchLimits,writer:hwpx_package::WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoCatalogMaskCandidate,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let catalog=SourcePersonalInfoCatalog::parse_utf16le(&snapshot(catalog_source)?,expected_catalog_sha256).map_err(D::from)?;
        let output=proof.lower_personal_info_catalog_mask_candidate(&self.imported,&catalog,families,selector,body,policy,limits,writer)?;
        if !catalog_mask_receipt_matches(output.receipt(),*fresh.digest.as_bytes()){return Err(M::Binding);}
        let receipt=StoredPersonalInfoCatalogMaskReceipt{profile:STORED_PERSONAL_INFO_CATALOG_MASK_PROFILE,source:self.receipt.clone(),output:output.receipt().clone(),
            preview_only:false,candidate_output_retained:true,issuer_execution_publication_authority:false};
        metadata_bound(&receipt,limits.maximum_result_bytes())?;
        verify_catalog(catalog_source,&receipt.output.catalog)?;provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredPersonalInfoCatalogMaskCandidate{source:self,output,receipt,maximum:limits.maximum_result_bytes()})
    }
}
fn fresh<R,B,S,V>(source:&StoredImportedDocumentForms,receipt:&StoredPersonalInfoCatalogMaskReceipt,maximum:usize,preview:bool,
    provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),M>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(M::Permission);}
    let current=source.fresh_source(provider,now)?;
    let profile=if preview{STORED_PERSONAL_INFO_CATALOG_MASK_PREVIEW_PROFILE}else{STORED_PERSONAL_INFO_CATALOG_MASK_PROFILE};
    if receipt.profile!=profile||receipt.source!=source.receipt||receipt.preview_only!=preview||receipt.candidate_output_retained==preview
        ||receipt.issuer_execution_publication_authority||!catalog_mask_receipt_matches(&receipt.output,*current.digest.as_bytes()){return Err(M::Binding);}
    metadata_bound(receipt,maximum)?;verify_catalog(catalog,&receipt.output.catalog)?;Ok(())
}
impl PreparedStoredPersonalInfoCatalogMaskCandidate{
    pub(crate) fn compiler_source(&self)->&StoredImportedDocumentForms{&self.source}
    pub(crate) fn compiler_mask_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory{self.output.edit_inventory()}
    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        verify_catalog(catalog,&self.receipt.output.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoCatalogMaskReceipt{&self.receipt}
    /// # Errors
    /// Drop output bytes and compiler inventory. A preview cannot become a candidate or expose bytes again.
    pub fn into_preview(self)->Result<PreparedStoredPersonalInfoCatalogMaskPreview,M>{
        let Self{source,output,mut receipt,maximum}=self;drop(output);
        receipt.profile=STORED_PERSONAL_INFO_CATALOG_MASK_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;
        metadata_bound(&receipt,maximum)?;Ok(PreparedStoredPersonalInfoCatalogMaskPreview{source,receipt,maximum})
    }
    /// # Errors
    /// Retained writer integrity and current source/config/access, followed by fresh config and final head. Never re-searches/masks.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,self.maximum,false,provider,catalog,now)?;
        if self.output.receipt()!=&self.receipt.output{return Err(M::Binding);}
        self.output.with_verified_bytes(|bytes|{
            verify_catalog(catalog,&self.receipt.output.catalog)?;
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        }).map_err(|_|M::Integrity)?
    }
    /// # Errors
    /// Metadata is serialized before the same verified delivery boundary; no raw config/pattern or source text is emitted.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let bytes=metadata_json(&self.receipt,self.maximum)?;self.with_verified_bytes(provider,catalog,now,|_|consume(&bytes))
    }
    /// # Errors
    /// Fresh current authorization and immutable writer integrity, not a source/config receipt replay as authority.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<StoredPersonalInfoCatalogMaskReceipt,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_bytes(provider,catalog,now,|_|())?;Ok(self.receipt.clone())}
    /// # Errors
    /// No Native/CAS/ingest/publication or full sanitization route is qualified by preparing masked text.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(M::RouteUnqualified)}
}
impl PreparedStoredPersonalInfoCatalogMaskPreview{
    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        verify_catalog(catalog,&self.receipt.output.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoCatalogMaskReceipt{&self.receipt}
    /// # Errors
    /// Current access and fresh config before final head. Only predicted metadata survives; no bytes/inventory/reverse conversion.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        fresh(&self.source,&self.receipt,self.maximum,true,provider,catalog,now)?;let bytes=metadata_json(&self.receipt,self.maximum)?;
        verify_catalog(catalog,&self.receipt.output.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(consume(&bytes))
    }
    /// # Errors
    /// Predicted metadata/current source only; the dropped output artifact is not re-created or verified.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<StoredPersonalInfoCatalogMaskReceipt,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.with_verified_json(provider,catalog,now,|_|())?;Ok(self.receipt.clone())}
    /// # Errors
    /// Preview never becomes a mutation/execution/CAS/publication capability.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(M::RouteUnqualified)}
}
