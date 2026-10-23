//! Strict full-catalog matched masking, retaining current config/source checks. No execution grant.
use super::*;
use crate::form_stored_provider::actual_import::source_search::personal_info_catalog::{CurrentPersonalInfoCatalogSource,PersonalInfoCatalogSourceError,
    mask::{PreparedStoredPersonalInfoCatalogMaskCandidate,PreparedStoredPersonalInfoCatalogMaskPreview,StoredPersonalInfoCatalogMaskReceipt,
        StoredPersonalInfoCatalogMaskError,catalog_mask_receipt_matches}};
use hwpx_package::document_import::search::personal_info::catalog::PersonalInfoCatalogFamily;
// A single borrowed loader type avoids duplicating the large stored/provider
// monomorphizations for synthetic and installed loaders. No bytes are cached.
struct CatalogBorrow<'a>(&'a dyn CurrentPersonalInfoCatalogSource);
impl CurrentPersonalInfoCatalogSource for CatalogBorrow<'_>{
    fn read_current_catalog(&self)->Result<Vec<u8>,PersonalInfoCatalogSourceError>{self.0.read_current_catalog()}
}
pub const PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA:&str="hwpx-agent.product-personal-info-catalog-mask-request/v1";
pub const PERSONAL_INFO_CATALOG_MASK_PRODUCT_PROFILE:&str="hwpx-agent.product-personal-info-catalog-mask-preparation/v1";
pub mod request_lookup;
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{MaskPersonalInfoCatalog}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,families:Vec<PersonalInfoCatalogFamily>,mask_policy:SourcePersonalInfoMaskPolicy,max_matches:usize,
    max_changed_components:usize,review_policy:SourceReviewTextPolicy,preview_only:bool}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,expected_catalog_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]pub enum PersonalInfoCatalogMaskProductError{
    #[error("CATALOG_MASK_PRODUCT_REQUEST_REJECTED")]Request,#[error("CATALOG_MASK_PRODUCT_LIMIT")]Limit,
    #[error("CATALOG_MASK_PRODUCT_BINDING_REJECTED")]Binding,#[error("CATALOG_MASK_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("CATALOG_MASK_PRODUCT_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("CATALOG_MASK_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredPersonalInfoCatalogMaskError),
    #[error("CATALOG_MASK_PRODUCT_PREVIEW_HAS_NO_OUTPUT")]PreviewOnly,#[error("CATALOG_MASK_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type P=PersonalInfoCatalogMaskProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,P>{
        let value=super::super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){P::Limit}else{P::Request})?;
        if !["kind","mask_policy"].iter().all(|k|value["operation"].get(k).is_some_and(serde_json::Value::is_string))
            ||!value["selector"].get("scope").is_some_and(serde_json::Value::is_string)
            ||!value["operation"].get("families").and_then(serde_json::Value::as_array).is_some_and(|v|v.iter().all(serde_json::Value::is_string)){return Err(P::Request);}
        let(sections,range)=Scope::shape(&value["selector"]).map_err(|_|P::Request)?;let r:Self=serde_json::from_value(value).map_err(|_|P::Request)?;
        let f=&r.operation.families;
        if r.schema_version!=PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA||r.expected_head_generation==0||r.document_id.as_str().len()>1024
            ||!valid_sha(&r.expected_source_package_sha256)||!valid_sha(&r.expected_catalog_sha256)||r.selector.revision_id!=r.base_revision
            ||f.is_empty()||f.len()>11||f.iter().collect::<BTreeSet<_>>().len()!=f.len()
            ||r.operation.max_matches==0||r.operation.max_matches>10_000||r.operation.max_changed_components==0||r.operation.max_changed_components>10_000{return Err(P::Request);}
        r.selector.validate_shape(sections,range).map_err(|_|P::Request)?;r.head()?;r.catalog_sha()?;r.canonical_sha()?;Ok(r)
    }
    fn head(&self)->Result<RevisionHead,P>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|P::Request)?),self.expected_head_generation).map_err(|_|P::Request)}
    fn catalog_sha(&self)->Result<[u8;32],P>{hex::decode(&self.expected_catalog_sha256).map_err(|_|P::Request)?.try_into().map_err(|_|P::Request)}
    fn canonical_sha(&self)->Result<String,P>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,P>{Ok(digest(&bounded(&(PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct PersonalInfoCatalogMaskProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredPersonalInfoCatalogMaskReceipt,pub preview_only:bool,
    pub idempotency_key_claimed:bool,pub native_cas_execution_publication_authority:bool}
enum Prepared{Candidate(PreparedStoredPersonalInfoCatalogMaskCandidate),Preview(PreparedStoredPersonalInfoCatalogMaskPreview)}
pub struct PreparedStoredPersonalInfoCatalogMaskProduct{request:Request,prepared:Prepared,receipt:PersonalInfoCatalogMaskProductReceipt,maximum:usize}
impl fmt::Debug for PreparedStoredPersonalInfoCatalogMaskProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoCatalogMaskProduct(<redacted>; current_catalog_not_execution)")}}
#[derive(Debug)]pub struct StoredPersonalInfoCatalogMaskProductRequest;
impl StoredPersonalInfoCatalogMaskProductRequest{
    /// # Errors
    /// Strict16KiB, duplicate-free request before source/config access. Catalog loader is host-owned, never a request path.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredPersonalInfoCatalogMaskProduct,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        Self::prepare_parsed(provider,catalog,raw,Request::parse(raw)?,limits,writer,now)
    }
    pub(crate) fn prepare_mutation_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredPersonalInfoCatalogMaskProduct,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if request.operation.preview_only{return Err(P::PreviewOnly);}
        Self::prepare_parsed(provider,catalog,raw,request,limits,writer,now)
    }
    fn prepare_parsed<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredPersonalInfoCatalogMaskProduct,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let maximum=limits.maximum_result_bytes();
        // The validated server budget also bounds edit components. A request
        // match maximum must not shrink that independent component budget.
        // Both requested maxima are checked against the immutable output below.
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(P::Binding);}
        let candidate=source.into_personal_info_catalog_mask_candidate(provider,&CatalogBorrow(catalog),request.catalog_sha()?,&request.operation.families,
            request.selector.native().map_err(|_|P::Request)?,request.operation.review_policy,request.operation.mask_policy,limits,writer,now)?;
        let prepared=if request.operation.preview_only{Prepared::Preview(candidate.into_preview()?)}else{Prepared::Candidate(candidate)};
        let stored=match &prepared{Prepared::Candidate(c)=>c.receipt(),Prepared::Preview(c)=>c.receipt()}.clone();
        let receipt=PersonalInfoCatalogMaskProductReceipt{profile:PERSONAL_INFO_CATALOG_MASK_PRODUCT_PROFILE,capability_id:"search.personal_info_find_replace",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored,
            preview_only:request.operation.preview_only,idempotency_key_claimed:false,native_cas_execution_publication_authority:false};
        bounded(&receipt,maximum).map_err(|_|P::Limit)?;let out=PreparedStoredPersonalInfoCatalogMaskProduct{request,prepared,receipt,maximum};
        out.check_final_inputs(provider,catalog)?;Ok(out)
    }
}
impl PreparedStoredPersonalInfoCatalogMaskProduct{
    pub(crate) fn server_job_identity<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)
        ->Result<crate::stored_revision_commit::job::identity::StoredRequestJobIdentity,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if self.receipt.preview_only{return Err(P::PreviewOnly);}self.check(provider)?;
        Ok(provider.source_search_job_identity(&self.request.project_id,&self.request.document_id,&self.request.idempotency_key,
            &self.receipt.canonical_request_sha256,&self.receipt.scoped_request_sha256)?)
    }
    #[must_use]pub const fn receipt(&self)->&PersonalInfoCatalogMaskProductReceipt{&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;let p=&self.receipt;let s=&p.stored;let o=&s.output;
        let expected=match &self.prepared{Prepared::Candidate(c)=>c.receipt(),Prepared::Preview(c)=>c.receipt()};
        let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
        if p.profile!=PERSONAL_INFO_CATALOG_MASK_PRODUCT_PROFILE||p.capability_id!="search.personal_info_find_replace"||s!=expected
            ||p.canonical_request_sha256!=r.canonical_sha()?||p.scoped_request_sha256!=r.scoped_sha(scope)?||p.preview_only!=r.operation.preview_only
            ||s.preview_only!=p.preview_only||s.candidate_output_retained==p.preview_only||s.source.head_generation!=r.expected_head_generation
            ||hex::encode(o.source_package_sha256)!=r.expected_source_package_sha256||o.catalog.source_sha256!=r.catalog_sha()?
            ||o.mask_policy!=r.operation.mask_policy||o.body_policy!=r.operation.review_policy||o.matched_formats>r.operation.max_matches
            ||o.changed_components>r.operation.max_changed_components||!catalog_mask_receipt_matches(o,o.source_package_sha256)
            ||s.issuer_execution_publication_authority||p.idempotency_key_claimed||p.native_cas_execution_publication_authority{return Err(P::Binding);}Ok(())
    }
    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;match &self.prepared{Prepared::Candidate(c)=>c.check_final_inputs(provider,&CatalogBorrow(catalog))?,Prepared::Preview(c)=>c.check_final_inputs(provider,&CatalogBorrow(catalog))?};Ok(())
    }
    pub(crate) fn compiler_view(&self)->Result<crate::form_product_request::stored_operations::compiled_search::CompilationView<'_>,P>{
        let Prepared::Candidate(c)=&self.prepared else{return Err(P::PreviewOnly)};let r=&self.request;let p=&self.receipt;
        Ok(crate::form_product_request::stored_operations::compiled_search::CompilationView{source:c.compiler_source(),plan_id:&r.plan_id,revision:&r.base_revision,
            project:&r.project_id,key:&r.idempotency_key,
            document:&r.document_id,generation:r.expected_head_generation,capability:p.capability_id,raw:&p.raw_request_sha256,canonical:&p.canonical_request_sha256,scoped:&p.scoped_request_sha256,splices:None})
    }
    pub(crate) fn compiler_mask_inventory(&self)->Result<&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory,P>{
        let Prepared::Candidate(c)=&self.prepared else{return Err(P::PreviewOnly)};Ok(c.compiler_mask_inventory())
    }
    /// # Errors
    /// Current source/config/access and immutable output integrity, without search/masking replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64)->Result<PersonalInfoCatalogMaskProductReceipt,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let receipt=match &self.prepared{Prepared::Candidate(c)=>c.verify(provider,&CatalogBorrow(catalog),now)?,Prepared::Preview(c)=>c.verify(provider,&CatalogBorrow(catalog),now)?};
        if receipt!=self.receipt.stored{return Err(P::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Preview never reaches a byte consumer. Fresh catalog and final head remain in the original candidate callback.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let Prepared::Candidate(c)=&self.prepared else{return Err(P::PreviewOnly)};Ok(c.with_verified_bytes(provider,&CatalogBorrow(catalog),now,consume)?)
    }
    /// # Errors
    /// Serialize the entire bounded outer envelope BEFORE current source/config and consumer-final head verification.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let bytes=bounded(&self.receipt,self.maximum).map_err(|_|P::Limit)?;
        match &self.prepared{Prepared::Candidate(c)=>Ok(c.with_verified_bytes(provider,&CatalogBorrow(catalog),now,|_|consume(&bytes))?),
            Prepared::Preview(c)=>Ok(c.with_verified_json(provider,&CatalogBorrow(catalog),now,|_|consume(&bytes))?)}
    }
    /// # Errors
    /// Neither retained receipts nor compiled plans grant a registry/Native/CAS/ingest/publication route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,now:u64)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,catalog,now)?;Err(P::RouteUnqualified)}
}
