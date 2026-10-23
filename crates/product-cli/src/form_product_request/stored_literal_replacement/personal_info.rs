//! Strict selected-text mask preparation; not generic PII discovery or a sanitized-document claim.
pub mod catalog;
mod mutation;
pub use mutation::{StoredPersonalInfoMaskMutationRequest,PreparedStoredPersonalInfoMaskMutation,PreparedStoredPersonalInfoMaskPreviewProduct};
pub(crate) use mutation::preview_mode;
use super::*;
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::personal_info::{PreparedStoredPersonalInfoMaskCandidate,PreparedStoredPersonalInfoMaskPreview,
    StoredPersonalInfoMaskReceipt,StoredPersonalInfoMaskError,mask_receipt_matches};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::personal_info::SourcePersonalInfoMaskPolicy};
pub const PERSONAL_INFO_MASK_PRODUCT_SCHEMA:&str="hwpx-agent.product-personal-info-selection-mask-request/v1";
pub const PERSONAL_INFO_MASK_PREPARATION_PROFILE:&str="hwpx-agent.product-personal-info-selection-mask-preparation/v1";
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{MaskSelectedPersonalInfo}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,mask_policy:SourcePersonalInfoMaskPolicy,max_changed_components:usize,review_policy:SourceReviewTextPolicy,preview_only:bool}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum PersonalInfoMaskProductError{
    #[error("PERSONAL_INFO_MASK_PRODUCT_REQUEST_REJECTED")]Request,#[error("PERSONAL_INFO_MASK_PRODUCT_LIMIT")]Limit,
    #[error("PERSONAL_INFO_MASK_PRODUCT_BINDING_REJECTED")]Binding,#[error("PERSONAL_INFO_MASK_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("PERSONAL_INFO_MASK_PRODUCT_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("PERSONAL_INFO_MASK_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredPersonalInfoMaskError),
    #[error("PERSONAL_INFO_MASK_PREVIEW_HAS_NO_OUTPUT")]PreviewOnly,#[error("PERSONAL_INFO_MASK_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type M=PersonalInfoMaskProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,M>{
        let v=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){M::Limit}else{M::Request})?;
        if !["kind","mask_policy"].iter().all(|k|v["operation"].get(k).is_some_and(serde_json::Value::is_string))
            ||!v["selector"].get("scope").is_some_and(serde_json::Value::is_string){return Err(M::Request);}
        let(sections,range)=Scope::shape(&v["selector"]).map_err(|_|M::Request)?;let r:Self=serde_json::from_value(v).map_err(|_|M::Request)?;
        if r.schema_version!=PERSONAL_INFO_MASK_PRODUCT_SCHEMA||r.expected_head_generation==0||r.document_id.as_str().len()>1024
            ||!valid_sha(&r.expected_source_package_sha256)||r.selector.revision_id!=r.base_revision||r.operation.max_changed_components==0||r.operation.max_changed_components>10_000{return Err(M::Request);}
        r.selector.validate_shape(sections,range).map_err(|_|M::Request)?;r.head()?;r.canonical_sha()?;Ok(r)
    }
    fn head(&self)->Result<RevisionHead,M>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|M::Request)?),self.expected_head_generation).map_err(|_|M::Request)}
    fn canonical_sha(&self)->Result<String,M>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|M::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,M>{Ok(digest(&bounded(&(PERSONAL_INFO_MASK_PRODUCT_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|M::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct PersonalInfoMaskProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredPersonalInfoMaskReceipt,pub preview_only:bool,pub idempotency_key_claimed:bool,
    pub full_personal_info_native_cas_execution_publication_authority:bool}
enum Prepared{Candidate(PreparedStoredPersonalInfoMaskCandidate<'static>),Preview(PreparedStoredPersonalInfoMaskPreview<'static>)}
pub struct PreparedStoredPersonalInfoMaskProduct{request:Request,prepared:Prepared,receipt:PersonalInfoMaskProductReceipt,maximum_metadata_bytes:usize}
impl fmt::Debug for PreparedStoredPersonalInfoMaskProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoMaskProduct(<redacted>; selected_text_only_not_sanitized_document)")}}
#[derive(Debug)]pub struct StoredPersonalInfoMaskProductRequest;
impl StoredPersonalInfoMaskProductRequest{
    /// # Errors
    /// Strict16KiB schema/selector/explicit mask and preview policy before sealed current source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskProduct,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskProduct,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let maximum_metadata_bytes=limits.maximum_result_bytes();
        let limits=limits.restrict_match_limit(request.operation.max_changed_components).map_err(|_|M::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(M::Binding);}
        let candidate=source.into_personal_info_mask_candidate(provider,request.selector.native().map_err(|_|M::Request)?,request.operation.review_policy,request.operation.mask_policy,limits,writer,now)?;
        let prepared=if request.operation.preview_only{Prepared::Preview(candidate.into_preview()?)}else{Prepared::Candidate(candidate)};
        let stored=match &prepared{Prepared::Candidate(c)=>c.receipt(),Prepared::Preview(c)=>c.receipt()}.clone();
        let receipt=PersonalInfoMaskProductReceipt{profile:PERSONAL_INFO_MASK_PREPARATION_PROFILE,capability_id:"search.personal_info_replace_direct",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored,preview_only:request.operation.preview_only,idempotency_key_claimed:false,
            full_personal_info_native_cas_execution_publication_authority:false};
        bounded(&receipt,maximum_metadata_bytes).map_err(|_|M::Limit)?;let out=PreparedStoredPersonalInfoMaskProduct{request,prepared,receipt,maximum_metadata_bytes};out.check(provider)?;
        match &out.prepared{Prepared::Candidate(c)=>c.check_final_head(provider)?,Prepared::Preview(c)=>c.check_final_head(provider)?};Ok(out)
    }
}
impl PreparedStoredPersonalInfoMaskProduct{
    #[must_use]pub const fn receipt(&self)->&PersonalInfoMaskProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;
        let expected=match &self.prepared{Prepared::Candidate(c)=>{if r.operation.preview_only{return Err(M::Binding);}c.receipt()},Prepared::Preview(c)=>{if !r.operation.preview_only{return Err(M::Binding);}c.receipt()}};
        check_binding(r,&self.receipt,expected,provider)
    }
    /// # Errors
    /// Current source/access/writer checks without index, masking or writer replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<PersonalInfoMaskProductReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let s=match &self.prepared{Prepared::Candidate(c)=>c.verify(provider,now)?,Prepared::Preview(c)=>c.verify(provider,now)?};if s!=self.receipt.stored{return Err(M::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Preview never invokes a byte consumer and has no output artifact to recover.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        match &self.prepared{Prepared::Preview(_)=>Err(M::PreviewOnly),Prepared::Candidate(c)=>{self.check(provider)?;Ok(c.with_verified_bytes(provider,now,consume)?)}}
    }
    /// # Errors
    /// Entire metadata envelope is bounded; access/writer integrity and consumer-final head stay authoritative.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let bytes=bounded(&self.receipt,self.maximum_metadata_bytes).map_err(|_|M::Limit)?;
        match &self.prepared{Prepared::Candidate(c)=>Ok(c.with_verified_bytes(provider,now,|_|consume(&bytes))?),Prepared::Preview(c)=>Ok(c.with_verified_metadata(provider,now,|_|consume(&bytes))?)}
    }
    /// # Errors
    /// No qualified dispatcher, claim, CAS, execution, publication or sanitized-document route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
fn check_binding<Rp,B,S,V>(r:&Request,p:&PersonalInfoMaskProductReceipt,expected:&StoredPersonalInfoMaskReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let s=&p.stored;let o=&s.output;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
        if p.profile!=PERSONAL_INFO_MASK_PREPARATION_PROFILE||p.capability_id!="search.personal_info_replace_direct"||p.canonical_request_sha256!=r.canonical_sha()?
            ||p.scoped_request_sha256!=r.scoped_sha(scope)?||s!=expected||p.preview_only!=r.operation.preview_only||s.preview_only!=p.preview_only||s.candidate_output_retained==p.preview_only
            ||s.source.head_generation!=r.expected_head_generation||hex::encode(o.source_package_sha256)!=r.expected_source_package_sha256||o.mask_policy!=r.operation.mask_policy
            ||o.body_policy!=r.operation.review_policy||o.changed_components>r.operation.max_changed_components||!mask_receipt_matches(o,o.source_package_sha256)
            ||s.issuer_execution_publication_authority||p.idempotency_key_claimed||p.full_personal_info_native_cas_execution_publication_authority{return Err(M::Binding);}Ok(())
}
