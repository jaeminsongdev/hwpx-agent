//! Strict current-catalog selection and retained-result requests. Not Native defaults, mutations or execution.
use super::*;
use super::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::source_search::{personal_info::{DetectionEnvelope,metadata_json},
    personal_info_catalog::{CurrentPersonalInfoCatalogSource,PreparedStoredPersonalInfoCatalog,StoredPersonalInfoCatalogReceipt,
        StoredPersonalInfoCatalogError,STORED_PERSONAL_INFO_CATALOG_PROFILE}};
use hwpx_package::document_import::search::{personal_info::catalog::PersonalInfoCatalogFamily,navigation::SourceSearchNavigationRequest};
use std::collections::BTreeSet;
pub const PERSONAL_INFO_CATALOG_PRODUCT_SCHEMA:&str="hwpx-agent.product-personal-info-catalog-request/v1";
pub const PERSONAL_INFO_CATALOG_PRODUCT_PROFILE:&str="hwpx-agent.product-personal-info-catalog-preparation/v1";
pub const PERSONAL_INFO_CATALOG_NEXT_SCHEMA:&str="hwpx-agent.product-personal-info-catalog-next-request/v1";
pub const PERSONAL_INFO_CATALOG_SELECTION_SCHEMA:&str="hwpx-agent.product-personal-info-catalog-selection-request/v1";
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{FindPersonalInfoCatalog}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,families:Vec<PersonalInfoCatalogFamily>,max_results:usize,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,expected_catalog_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]pub enum PersonalInfoCatalogProductError{
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_REQUEST_REJECTED")]Request,
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_LIMIT")]Limit,
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_BINDING_REJECTED")]Binding,
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredPersonalInfoCatalogError),
    #[error("PERSONAL_INFO_CATALOG_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type P=PersonalInfoCatalogProductError;
fn object(raw:&[u8])->Result<serde_json::Value,P>{
    if raw.is_empty()||raw.len()>SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES{return Err(P::Limit);}
    let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|P::Request)?;parser.end().map_err(|_|P::Request)?;
    let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|P::Request)?;if !value.is_object(){return Err(P::Request);}Ok(value)
}
impl Request{
    fn parse(raw:&[u8])->Result<Self,P>{
        let value=object(raw)?;
        if !["selector","operation"].iter().all(|k|value.get(k).is_some_and(serde_json::Value::is_object))
            ||!value["operation"].get("kind").is_some_and(serde_json::Value::is_string)||!value["selector"].get("scope").is_some_and(serde_json::Value::is_string)
            ||!value["operation"].get("families").and_then(serde_json::Value::as_array).is_some_and(|v|v.iter().all(serde_json::Value::is_string)){return Err(P::Request);}
        let(sections,range)=Scope::shape(&value["selector"]).map_err(|_|P::Request)?;let request:Self=serde_json::from_value(value).map_err(|_|P::Request)?;
        let families=&request.operation.families;
        if request.schema_version!=PERSONAL_INFO_CATALOG_PRODUCT_SCHEMA||request.expected_head_generation==0
            ||!valid_sha(&request.expected_source_package_sha256)||!valid_sha(&request.expected_catalog_sha256)
            ||request.selector.revision_id!=request.base_revision||request.document_id.as_str().len()>1024
            ||families.is_empty()||families.len()>11||families.iter().collect::<BTreeSet<_>>().len()!=families.len()
            ||request.operation.max_results==0||request.operation.max_results>10_000{return Err(P::Request);}
        request.selector.validate_shape(sections,range).map_err(|_|P::Request)?;request.head()?;request.catalog_sha()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,P>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|P::Request)?),self.expected_head_generation).map_err(|_|P::Request)}
    fn catalog_sha(&self)->Result<[u8;32],P>{hex::decode(&self.expected_catalog_sha256).map_err(|_|P::Request)?.try_into().map_err(|_|P::Request)}
    fn canonical_sha(&self)->Result<String,P>{Ok(digest(&bounded(self,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,P>{Ok(digest(&bounded(&(PERSONAL_INFO_CATALOG_PRODUCT_SCHEMA,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct PersonalInfoCatalogProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredPersonalInfoCatalogReceipt,
    pub idempotency_key_claimed:bool,pub native_identity_cas_execution_publication_authority:bool}
pub struct PreparedStoredPersonalInfoCatalogProduct{request:Request,candidate:PreparedStoredPersonalInfoCatalog,receipt:PersonalInfoCatalogProductReceipt}
impl fmt::Debug for PreparedStoredPersonalInfoCatalogProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoCatalogProduct(<redacted>; source_catalog_not_native_defaults_or_execution)")}}
#[derive(Debug)]pub struct StoredPersonalInfoCatalogProductRequest;
impl StoredPersonalInfoCatalogProductRequest{
    /// # Errors
    /// Strict16KiB selection without patterns/paths/approval fields, before document/config reads. Host supplies current catalog source.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,raw:&[u8],limits:SourceSearchLimits,now:u64)
        ->Result<PreparedStoredPersonalInfoCatalogProduct,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;let limits=limits.restrict_match_limit(request.operation.max_results).map_err(|_|P::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(P::Binding);}
        let candidate=source.into_personal_info_catalog(provider,catalog,request.catalog_sha()?,&request.operation.families,
            request.selector.native().map_err(|_|P::Request)?,request.operation.review_policy,limits,now)?;
        let receipt=PersonalInfoCatalogProductReceipt{profile:PERSONAL_INFO_CATALOG_PRODUCT_PROFILE,capability_id:"search.personal_info_find_replace",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,native_identity_cas_execution_publication_authority:false};
        candidate.check_product_envelope(&receipt)?;let product=PreparedStoredPersonalInfoCatalogProduct{request,candidate,receipt};
        product.check(provider)?;product.candidate.check_final_inputs(provider,catalog)?;Ok(product)
    }
}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]struct Next{schema_version:String,catalog_receipt_sha256:String,navigation:SourceSearchNavigationRequest}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]struct Selection{schema_version:String,catalog_receipt_sha256:String,occurrence_index:usize}
impl PreparedStoredPersonalInfoCatalogProduct{
    #[must_use]pub const fn receipt(&self)->&PersonalInfoCatalogProductReceipt{&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;let p=&self.receipt;let s=&p.stored;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
        if p.profile!=PERSONAL_INFO_CATALOG_PRODUCT_PROFILE||p.capability_id!="search.personal_info_find_replace"||p.canonical_request_sha256!=r.canonical_sha()?
            ||p.scoped_request_sha256!=r.scoped_sha(scope)?||s!=self.candidate.receipt()||s.profile!=STORED_PERSONAL_INFO_CATALOG_PROFILE
            ||s.source.head_generation!=r.expected_head_generation||hex::encode(s.index.source_package_sha256)!=r.expected_source_package_sha256
            ||s.catalog.source_sha256!=r.catalog_sha()?||s.review_policy!=r.operation.review_policy||s.matched_formats>r.operation.max_results
            ||s.whole_package_personal_data_removed||s.native_format_identity_or_execution_qualified
            ||s.catalog.installed_vendor_authenticity_or_native_semantics_qualified||p.idempotency_key_claimed||p.native_identity_cas_execution_publication_authority{return Err(P::Binding);}Ok(())
    }
    /// # Errors
    /// Whole receipt binds raw/canonical/key/plan/provider, catalog/selection, and exact original result. Not an access grant.
    pub fn continuation_receipt_sha256(&self)->Result<String,P>{Ok(digest(&bounded(&self.receipt,4*1024*1024).map_err(|_|P::Limit)?))}
    fn context(&self,received:&str)->Result<[u8;32],P>{
        if !valid_sha(received)||received!=self.continuation_receipt_sha256()?{return Err(P::Binding);}
        hex::decode(received).map_err(|_|P::Binding)?.try_into().map_err(|_|P::Binding)
    }
    /// # Errors
    /// Fresh document/catalog/ACL checks and final head, without recompiling or rematching.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<PersonalInfoCatalogProductReceipt,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,catalog,now)?!=self.receipt.stored{return Err(P::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Bounded outer envelope; current catalog and final head after serialization, before consumer.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_projection(provider,catalog,now,
            |result,max|Ok(metadata_json(&DetectionEnvelope{receipt:&self.receipt,result},max)?),consume)?)
    }
    /// # Errors
    /// Receipt-bound strict navigation of the retained set with current source/config checks; no search replay.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let value=object(raw)?;if !value.get("navigation").is_some_and(serde_json::Value::is_object)
            ||!value["navigation"].get("direction").is_some_and(serde_json::Value::is_string)
            ||value["navigation"].get("cursor").is_some_and(|c|!c.is_null()&&!c.is_object()){return Err(P::Request);}
        let request:Next=serde_json::from_value(value).map_err(|_|P::Request)?;if request.schema_version!=PERSONAL_INFO_CATALOG_NEXT_SCHEMA{return Err(P::Request);}
        let context=self.context(&request.catalog_receipt_sha256)?;self.check(provider)?;
        Ok(self.candidate.with_verified_projection(provider,catalog,now,|result,max|Ok(metadata_json(
            &DetectionEnvelope{receipt:&self.receipt,result:result.navigate(&request.navigation,context)?},max)?),consume)?)
    }
    /// # Errors
    /// Coordinates only, tied to this receipt and current config/document; not mutation or publication authority.
    pub fn with_selection_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,
        raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request:Selection=serde_json::from_value(object(raw)?).map_err(|_|P::Request)?;
        if request.schema_version!=PERSONAL_INFO_CATALOG_SELECTION_SCHEMA||request.occurrence_index>=10_000{return Err(P::Request);}
        self.context(&request.catalog_receipt_sha256)?;self.check(provider)?;
        Ok(self.candidate.with_verified_projection(provider,catalog,now,|result,max|Ok(metadata_json(
            &DetectionEnvelope{receipt:&self.receipt,result:result.selection(request.occurrence_index)?},max)?),consume)?)
    }
    /// # Errors
    /// No mutation/compiler/CAS/publication/Native/default-format route is supplied.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource,now:u64)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(P::RouteUnqualified)}
}
