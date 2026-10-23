//! Current sealed document and freshly read complete catalog. No Native/default authenticity or execution grant.
pub mod mask;
use super::*;
use super::personal_info::{DetectionEnvelope,metadata_bound,metadata_json,metadata_sha,StoredPersonalInfoDetectionError};
use hwpx_package::document_import::search::{personal_info::catalog::{SourcePersonalInfoCatalog,PersonalInfoCatalogReceipt,
    PersonalInfoCatalogFamily,PersonalInfoCatalogResult,PersonalInfoCatalogError},selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},
    navigation::SourceSearchNavigationRequest};
pub const STORED_PERSONAL_INFO_CATALOG_PROFILE:&str="hwpx-agent.stored-personal-info-source-catalog/v1";
const MAX_CATALOG_BYTES:usize=64*1024;

/// Trusted host dependency, never a request-selected path or an attestation of vendor defaults.
pub trait CurrentPersonalInfoCatalogSource{
    /// # Errors
    /// A fresh bounded snapshot on every call; no retained snapshot may replace the current source.
    fn read_current_catalog(&self)->Result<Vec<u8>,PersonalInfoCatalogSourceError>;
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
#[error("PERSONAL_INFO_CURRENT_CATALOG_SOURCE_REJECTED")]
pub struct PersonalInfoCatalogSourceError;
/// Read only the fixed installed configuration, not the private USERDEF/user configuration.
#[derive(Debug,Default)]pub struct InstalledPersonalInfoCatalogSource;
impl CurrentPersonalInfoCatalogSource for InstalledPersonalInfoCatalogSource{
    fn read_current_catalog(&self)->Result<Vec<u8>,PersonalInfoCatalogSourceError>{
        use std::io::Read as _;
        let path=std::path::Path::new(r"C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin\PrivateInfo.ini");
        let metadata=std::fs::symlink_metadata(path).map_err(|_|PersonalInfoCatalogSourceError)?;
        if !metadata.is_file()||metadata.file_type().is_symlink()||metadata.len()==0||metadata.len()>MAX_CATALOG_BYTES as u64{return Err(PersonalInfoCatalogSourceError);}
        let mut bytes=Vec::new();std::fs::File::open(path).map_err(|_|PersonalInfoCatalogSourceError)?.take(MAX_CATALOG_BYTES as u64+1)
            .read_to_end(&mut bytes).map_err(|_|PersonalInfoCatalogSourceError)?;
        if bytes.is_empty()||bytes.len()>MAX_CATALOG_BYTES{return Err(PersonalInfoCatalogSourceError);}Ok(bytes)
    }
}

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredPersonalInfoCatalogReceipt{
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub index:SourceSearchIndexReceipt,pub scope:SourceIndexScopeReceipt,
    pub catalog:PersonalInfoCatalogReceipt,pub policy_sha256:[u8;32],pub request_sha256:[u8;32],pub result_sha256:[u8;32],
    pub review_policy:SourceReviewTextPolicy,pub matched_formats:usize,pub selected_patterns:usize,
    pub native_format_identity_or_execution_qualified:bool,pub whole_package_personal_data_removed:bool,
}
pub struct PreparedStoredPersonalInfoCatalog{source:StoredImportedDocumentForms,result:PersonalInfoCatalogResult,receipt:StoredPersonalInfoCatalogReceipt,maximum:usize}
impl fmt::Debug for PreparedStoredPersonalInfoCatalog{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoCatalog(<redacted>; current_source_formats_not_native_defaults)")}}
#[derive(Debug,Error)]pub enum StoredPersonalInfoCatalogError{
    #[error("STORED_PERSONAL_INFO_CATALOG_ACCESS_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_PERSONAL_INFO_CATALOG_SEARCH_REJECTED")]Search(#[from]SourceSearchError),
    #[error("STORED_PERSONAL_INFO_CATALOG_FORMAT_REJECTED")]Catalog(#[from]PersonalInfoCatalogError),
    #[error("STORED_PERSONAL_INFO_CATALOG_CURRENT_SOURCE_REJECTED")]CurrentCatalog(#[from]PersonalInfoCatalogSourceError),
    #[error("STORED_PERSONAL_INFO_CATALOG_METADATA_REJECTED")]Metadata(#[from]StoredPersonalInfoDetectionError),
    #[error("STORED_PERSONAL_INFO_CATALOG_BINDING_REJECTED")]Binding,
    #[error("STORED_PERSONAL_INFO_CATALOG_DOCUMENT_WRITE_REQUIRED")]Permission,
    #[error("STORED_PERSONAL_INFO_CATALOG_METADATA_LIMIT")]Limit,
    #[error("STORED_PERSONAL_INFO_CATALOG_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type D=StoredPersonalInfoCatalogError;
fn snapshot(source:&impl CurrentPersonalInfoCatalogSource)->Result<Vec<u8>,D>{
    let bytes=source.read_current_catalog()?;if bytes.is_empty()||bytes.len()>MAX_CATALOG_BYTES{return Err(D::Limit);}Ok(bytes)
}
fn verify_catalog(source:&impl CurrentPersonalInfoCatalogSource,receipt:&PersonalInfoCatalogReceipt)->Result<(),D>{
    let bytes=snapshot(source)?;
    if bytes.len()!=receipt.source_bytes||<[u8;32]>::from(Sha256::digest(&bytes))!=receipt.source_sha256{return Err(D::Binding);}Ok(())
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// One original Form proof/review index and one catalog scan; all selected source patterns, no truncation to legacy16 rules.
    pub fn into_personal_info_catalog<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog_source:&impl CurrentPersonalInfoCatalogSource,
        expected_catalog_sha256:[u8;32],families:&[PersonalInfoCatalogFamily],selector:SourceIndexScopeSelector<'_>,review_policy:SourceReviewTextPolicy,
        limits:SourceSearchLimits,now:u64)->Result<PreparedStoredPersonalInfoCatalog,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(D::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let catalog=SourcePersonalInfoCatalog::parse_utf16le(&snapshot(catalog_source)?,expected_catalog_sha256)?;
        let policy=catalog.prepare(families,limits)?;let index=proof.source_review_scope_index(&self.imported,limits)?;
        let result=index.find_personal_info_catalog(&policy,selector,review_policy)?;
        if result.search().result().index_receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(D::Binding);}
        let receipt=StoredPersonalInfoCatalogReceipt{profile:STORED_PERSONAL_INFO_CATALOG_PROFILE,source:self.receipt.clone(),
            index:result.search().result().index_receipt().clone(),scope:result.search().scope_receipt().clone(),catalog:policy.catalog_receipt().clone(),
            policy_sha256:policy.request_sha256(),request_sha256:result.search().request_sha256(),result_sha256:metadata_sha(&result,limits.maximum_result_bytes())?,
            review_policy,matched_formats:result.matches().len(),selected_patterns:policy.selected_pattern_count(),
            native_format_identity_or_execution_qualified:false,whole_package_personal_data_removed:false};
        metadata_bound(&DetectionEnvelope{receipt:&receipt,result:&result},limits.maximum_result_bytes())?;
        verify_catalog(catalog_source,&receipt.catalog)?;provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredPersonalInfoCatalog{source:self,result,receipt,maximum:limits.maximum_result_bytes()})
    }
}
impl PreparedStoredPersonalInfoCatalog{
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoCatalogReceipt{&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(D::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;let r=&self.receipt;
        if r.profile!=STORED_PERSONAL_INFO_CATALOG_PROFILE||r.source!=self.source.receipt||&r.index!=self.result.search().result().index_receipt()
            ||&r.scope!=self.result.search().scope_receipt()||&r.catalog!=self.result.catalog_receipt()||r.policy_sha256!=self.result.policy_sha256()
            ||r.index.source_package_sha256!=*fresh.digest.as_bytes()||r.index.graph_sha256!=self.source.imported.receipt().body_graph_sha256
            ||r.request_sha256!=self.result.search().request_sha256()||r.result_sha256!=metadata_sha(&self.result,self.maximum)?
            ||r.matched_formats!=self.result.matches().len()||r.selected_patterns!=self.result.selected_pattern_count()
            ||r.native_format_identity_or_execution_qualified||r.whole_package_personal_data_removed
            ||r.catalog.installed_vendor_authenticity_or_native_semantics_qualified||!r.catalog.original_pattern_text_preserved
            ||r.index.edit_or_service_access_authority||r.index.whole_document_visibility_and_search_qualified
            ||r.scope.whole_document_visibility_native_flow_or_revision_authority{return Err(D::Binding);}
        verify_catalog(catalog,&r.catalog)
    }
    pub(crate) fn check_product_envelope(&self,receipt:&impl Serialize)->Result<(),D>{
        metadata_bound(&DetectionEnvelope{receipt,result:&self.result},self.maximum)?;Ok(())
    }
    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        verify_catalog(catalog,&self.receipt.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
    /// Bytes are built first, then fresh catalog and consumer-final document head; no regex/index/search replay.
    pub(crate) fn with_verified_projection<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        now:u64,project:impl FnOnce(&PersonalInfoCatalogResult,usize)->Result<Vec<u8>,D>,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,catalog,now)?;let bytes=project(&self.result,self.maximum)?;if bytes.len()>self.maximum{return Err(D::Limit);}
        verify_catalog(catalog,&self.receipt.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(&bytes))
    }
    /// # Errors
    /// Current source/config/access and final head. Retains original result without matching again.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<StoredPersonalInfoCatalogReceipt,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,catalog,now)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Bounded metadata only; source values and pattern bodies are not serialized.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check_product_envelope(&self.receipt)?;
        self.with_verified_projection(provider,catalog,now,|result,max|Ok(metadata_json(&DetectionEnvelope{receipt:&self.receipt,result},max)?),consume)
    }
    /// # Errors
    /// Navigation of the retained set, with fresh source/catalog authorization, not a new scan.
    pub fn with_navigation_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        request:&SourceSearchNavigationRequest,context:[u8;32],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_projection(provider,catalog,now,|result,max|Ok(metadata_json(&DetectionEnvelope{receipt:&self.receipt,result:result.navigate(request,context)?},max)?),consume)
    }
    /// # Errors
    /// Coordinates only; any later writer must independently recheck current source, scope and protection.
    pub fn with_selection_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        occurrence:usize,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_projection(provider,catalog,now,|result,max|Ok(metadata_json(&DetectionEnvelope{receipt:&self.receipt,result:result.selection(occurrence)?},max)?),consume)
    }
    /// # Errors
    /// No mutation/compiler/CAS/publication/Native/default-format qualification is granted.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(D::RouteUnqualified)}
}
