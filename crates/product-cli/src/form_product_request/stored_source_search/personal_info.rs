//! Strict read-only format detection and bound next/selection requests. No mutation, preview or compiler API.
use super::*;
use super::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::source_search::personal_info::{PreparedStoredPersonalInfoDetection,StoredPersonalInfoDetectionReceipt,
    StoredPersonalInfoDetectionError,STORED_PERSONAL_INFO_DETECTION_PROFILE,DetectionEnvelope,metadata_json};
use hwpx_package::document_import::search::{personal_info::{SourcePersonalInfoDetectionPolicy,SourcePersonalInfoRule},navigation::SourceSearchNavigationRequest};
pub const PERSONAL_INFO_DETECTION_PRODUCT_SCHEMA:&str="hwpx-agent.product-personal-info-format-detection-request/v1";
pub const PERSONAL_INFO_DETECTION_PRODUCT_PROFILE:&str="hwpx-agent.product-personal-info-format-detection-preparation/v1";
pub const PERSONAL_INFO_DETECTION_NEXT_SCHEMA:&str="hwpx-agent.product-personal-info-format-next-request/v1";
pub const PERSONAL_INFO_DETECTION_SELECTION_SCHEMA:&str="hwpx-agent.product-personal-info-format-selection-request/v1";
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{FindPersonalInfoFormats}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,rules:Vec<SourcePersonalInfoRule>,max_results:usize,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum PersonalInfoDetectionProductError{
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_REQUEST_REJECTED")]Request,#[error("PERSONAL_INFO_DETECTION_PRODUCT_LIMIT")]Limit,
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_BINDING_REJECTED")]Binding,
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredPersonalInfoDetectionError),
    #[error("PERSONAL_INFO_DETECTION_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type P=PersonalInfoDetectionProductError;
fn object(raw:&[u8])->Result<serde_json::Value,P>{
    if raw.is_empty()||raw.len()>SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES{return Err(P::Limit);}
    let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|P::Request)?;parser.end().map_err(|_|P::Request)?;
    let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|P::Request)?;if !value.is_object(){return Err(P::Request);}Ok(value)
}
impl Request{
    fn parse(raw:&[u8])->Result<(Self,SourcePersonalInfoDetectionPolicy),P>{
        let value=object(raw)?;
        if !["selector","operation"].iter().all(|k|value.get(k).is_some_and(serde_json::Value::is_object))
            ||!value["operation"].get("kind").is_some_and(serde_json::Value::is_string)||!value["selector"].get("scope").is_some_and(serde_json::Value::is_string){return Err(P::Request);}
        let rules=value["operation"].get("rules").and_then(serde_json::Value::as_array).ok_or(P::Request)?;
        if !rules.iter().all(|r|r.is_object()&&["kind","rule_id","query"].iter().all(|k|r.get(k).is_some_and(serde_json::Value::is_string))){return Err(P::Request);}
        let(sections,range)=Scope::shape(&value["selector"]).map_err(|_|P::Request)?;let request:Self=serde_json::from_value(value).map_err(|_|P::Request)?;
        if request.schema_version!=PERSONAL_INFO_DETECTION_PRODUCT_SCHEMA||request.expected_head_generation==0||!valid_sha(&request.expected_source_package_sha256)
            ||request.selector.revision_id!=request.base_revision||request.document_id.as_str().len()>1024||request.operation.max_results==0||request.operation.max_results>10_000{return Err(P::Request);}
        request.selector.validate_shape(sections,range).map_err(|_|P::Request)?;request.head()?;request.canonical_sha()?;
        let policy=SourcePersonalInfoDetectionPolicy::new(request.operation.rules.clone()).map_err(|_|P::Request)?;Ok((request,policy))
    }
    fn head(&self)->Result<RevisionHead,P>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|P::Request)?),self.expected_head_generation).map_err(|_|P::Request)}
    fn canonical_sha(&self)->Result<String,P>{Ok(digest(&bounded(self,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,P>{Ok(digest(&bounded(&(PERSONAL_INFO_DETECTION_PRODUCT_SCHEMA,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|P::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct PersonalInfoDetectionProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredPersonalInfoDetectionReceipt,pub idempotency_key_claimed:bool,pub native_identity_cas_execution_publication_authority:bool}
pub struct PreparedStoredPersonalInfoDetectionProduct{request:Request,candidate:PreparedStoredPersonalInfoDetection,receipt:PersonalInfoDetectionProductReceipt}
impl fmt::Debug for PreparedStoredPersonalInfoDetectionProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoDetectionProduct(<redacted>; read_only_not_native_identity_or_execution)")}}
#[derive(Debug)]pub struct StoredPersonalInfoDetectionProductRequest;
impl StoredPersonalInfoDetectionProductRequest{
    /// # Errors
    /// Strict16KiB shape, rule labels/policy and selector revision before current source reads; original source owner is moved.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,now:u64)->Result<PreparedStoredPersonalInfoDetectionProduct,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(request,policy)=Request::parse(raw)?;let limits=limits.restrict_match_limit(request.operation.max_results).map_err(|_|P::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(P::Binding);}
        let candidate=source.into_personal_info_detection(provider,&policy,request.selector.native().map_err(|_|P::Request)?,request.operation.review_policy,limits,now)?;
        let receipt=PersonalInfoDetectionProductReceipt{profile:PERSONAL_INFO_DETECTION_PRODUCT_PROFILE,capability_id:"search.personal_info_find_replace",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),idempotency_key_claimed:false,
            native_identity_cas_execution_publication_authority:false};
        candidate.check_product_envelope(&receipt)?;let product=PreparedStoredPersonalInfoDetectionProduct{request,candidate,receipt};product.check(provider)?;product.candidate.check_final_head(provider)?;Ok(product)
    }
}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]struct Next{schema_version:String,detection_receipt_sha256:String,navigation:SourceSearchNavigationRequest}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]struct Selection{schema_version:String,detection_receipt_sha256:String,occurrence_index:usize}
impl PreparedStoredPersonalInfoDetectionProduct{
    #[must_use]pub const fn receipt(&self)->&PersonalInfoDetectionProductReceipt{&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;let p=&self.receipt;let s=&p.stored;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
        if p.profile!=PERSONAL_INFO_DETECTION_PRODUCT_PROFILE||p.capability_id!="search.personal_info_find_replace"||p.canonical_request_sha256!=r.canonical_sha()?
            ||p.scoped_request_sha256!=r.scoped_sha(scope)?||s!=self.candidate.receipt()||s.profile!=STORED_PERSONAL_INFO_DETECTION_PROFILE
            ||s.source.head_generation!=r.expected_head_generation||hex::encode(s.index.source_package_sha256)!=r.expected_source_package_sha256
            ||s.review_policy!=r.operation.review_policy||s.matched_formats>r.operation.max_results||s.whole_package_personal_data_removed
            ||s.native_format_identity_or_execution_qualified||p.idempotency_key_claimed||p.native_identity_cas_execution_publication_authority{return Err(P::Binding);}Ok(())
    }
    /// # Errors
    /// Receipt identity includes raw request, key/plan/provider, policy and exact original result. Not an access grant.
    pub fn continuation_receipt_sha256(&self)->Result<String,P>{Ok(digest(&bounded(&self.receipt,4*1024*1024).map_err(|_|P::Limit)?))}
    fn context(&self,received:&str)->Result<[u8;32],P>{
        if !valid_sha(received)||received!=self.continuation_receipt_sha256()?{return Err(P::Binding);}
        hex::decode(received).map_err(|_|P::Binding)?.try_into().map_err(|_|P::Binding)
    }
    /// # Errors
    /// Current source/access/integrity and final head; never rebuilds rules, regex or matches.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<PersonalInfoDetectionProductReceipt,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(P::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Whole product metadata envelope is bounded before the consumer-final head check.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_projection(provider,now,|result,max|metadata_json(&DetectionEnvelope{receipt:&self.receipt,result},max),consume)?)
    }
    /// # Errors
    /// Strict bound navigation on the retained set, with fresh source/ACL and final head; no rematching.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let value=object(raw)?;if !value.get("navigation").is_some_and(serde_json::Value::is_object)
            ||!value["navigation"].get("direction").is_some_and(serde_json::Value::is_string)
            ||value["navigation"].get("cursor").is_some_and(|c|!c.is_null()&&!c.is_object()){return Err(P::Request);}
        let request:Next=serde_json::from_value(value).map_err(|_|P::Request)?;if request.schema_version!=PERSONAL_INFO_DETECTION_NEXT_SCHEMA{return Err(P::Request);}
        let context=self.context(&request.detection_receipt_sha256)?;self.check(provider)?;
        Ok(self.candidate.with_verified_projection(provider,now,|result,max|{let next=result.navigate(&request.navigation,context)?;metadata_json(&DetectionEnvelope{receipt:&self.receipt,result:next},max)},consume)?)
    }
    /// # Errors
    /// Coordinates only, bound to this retained result. No bytes or mutation authority; a writer must revalidate source and protection.
    pub fn with_selection_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request:Selection=serde_json::from_value(object(raw)?).map_err(|_|P::Request)?;
        if request.schema_version!=PERSONAL_INFO_DETECTION_SELECTION_SCHEMA||request.occurrence_index>=10_000{return Err(P::Request);}
        self.context(&request.detection_receipt_sha256)?;self.check(provider)?;
        Ok(self.candidate.with_verified_projection(provider,now,|result,max|metadata_json(&DetectionEnvelope{receipt:&self.receipt,result:result.selection(request.occurrence_index)?},max),consume)?)
    }
    /// # Errors
    /// No mutation/compiler/file/CAS/publication route is provided by a read-only preparation.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),P>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(P::RouteUnqualified)}
}
