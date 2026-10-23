//! Explicit mapped-source search request, not full SEARCH contract/CLI or execution authority.
pub mod navigation;
pub mod selector;
pub mod personal_info;
pub mod personal_info_catalog;
use super::{UniqueJson,bounded,digest};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,
    source_search::{PreparedStoredSourceSearch,StoredSourceSearchError,StoredSourceSearchReceipt,SourceInspectionOperation}}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore};
use domain_ir::{DocumentId,IdempotencyKey,LogicalId,PlanId,ProjectId,RevisionId};
use hwpx_package::document_import::search::{SourceSearchLimits,SourceSearchQuery,SourceSearchMode,scope::SourceSearchScope};
use hwpx_package::document_import::search::inspection::{SourceDeclaredStyleFilter,SourceControlKind};
use hwpx_package::document_import::search::inspection::definitions::SourceDefinitionStyleFilter;
use hwpx_package::document_import::search::reviews::SourceReviewTextPolicy;
use revision_service::{RevisionHead,RevisionRepository};
use serde::{Deserialize,Serialize};
use std::fmt;
use thiserror::Error;

pub const SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v1";
pub const SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v2";
pub const SOURCE_SEARCH_DEFINITION_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v3";
pub const SOURCE_SEARCH_REVIEW_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v4";
pub const SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES:usize=16*1024;
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {FindLiteral,FindRegex,FindDeclaredStyle,FindControl,FindDefinitionStyle,FindReviewLiteral,FindReviewRegex}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,query:String,case_sensitive:bool,whole_word:bool,max_results:usize,
    #[serde(default,skip_serializing_if="Option::is_none")] style_filter:Option<SourceDeclaredStyleFilter>,
    #[serde(default,skip_serializing_if="Option::is_none")] definition_filter:Option<SourceDefinitionStyleFilter>,
    #[serde(default,skip_serializing_if="Option::is_none")] review_policy:Option<SourceReviewTextPolicy>}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum ScopeKind {MappedDocument,Paragraphs}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Scope {kind:ScopeKind,paragraph_handles:Vec<LogicalId>}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,
    base_revision:RevisionId,expected_head_generation:u64,expected_source_package_sha256:String,
    plan_id:PlanId,scope:Scope,operation:Operation}
impl Request {
    fn parse(raw:&[u8])->Result<Self,E> {
        if raw.is_empty()||raw.len()>SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);
        let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!["scope","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}
        let filter=value.get("operation").and_then(|o|o.get("style_filter"));
        let has_filter=filter.is_some();
        if filter.is_some_and(|f|!f.is_object()){return Err(E::Request);}
        let definitions=value.get("operation").and_then(|o|o.get("definition_filter"));
        let has_definitions=definitions.is_some();
        if definitions.is_some_and(|f|!f.is_object()){return Err(E::Request);}
        let review=value.get("operation").and_then(|o|o.get("review_policy"));let has_review=review.is_some();
        if review.is_some_and(|f|!f.is_object()){return Err(E::Request);}
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        let review_schema=request.schema_version==SOURCE_SEARCH_REVIEW_REQUEST_SCHEMA;
        let definition_schema=review_schema||request.schema_version==SOURCE_SEARCH_DEFINITION_REQUEST_SCHEMA;
        let inspection_schema=definition_schema||request.schema_version==SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA;
        if has_review&&(!review_schema||!matches!(request.operation.kind,Kind::FindReviewLiteral|Kind::FindReviewRegex)){return Err(E::Request);}
        if !definition_schema&&has_definitions{return Err(E::Request);}
        if !inspection_schema&&(has_filter||!matches!(request.operation.kind,Kind::FindLiteral|Kind::FindRegex)){return Err(E::Request);}
        if !matches!(request.operation.kind,Kind::FindDefinitionStyle)&&has_definitions{return Err(E::Request);}
        match request.operation.kind {
            Kind::FindReviewLiteral|Kind::FindReviewRegex=>if !review_schema||request.operation.review_policy.is_none()||has_filter||has_definitions{return Err(E::Request);},
            Kind::FindDefinitionStyle=>{
                if !definition_schema||has_filter{return Err(E::Request);}
                request.operation.definition_filter.ok_or(E::Request)?.validate().map_err(|_|E::Request)?;
            },
            Kind::FindDeclaredStyle=>if !inspection_schema||request.operation.style_filter.is_none_or(|f|f.is_empty()){return Err(E::Request);},
            Kind::FindControl=>{
                if !inspection_schema||request.operation.style_filter.is_some()||!request.operation.case_sensitive||request.operation.whole_word{return Err(E::Request);}
                request.control()?;
            },
            _=>if request.operation.style_filter.is_some(){return Err(E::Request);},
        }
        let scope_valid=match request.scope.kind {ScopeKind::MappedDocument=>request.scope.paragraph_handles.is_empty(),
            ScopeKind::Paragraphs=>!request.scope.paragraph_handles.is_empty()&&request.scope.paragraph_handles.len()<=50_000
                &&request.scope.paragraph_handles.iter().collect::<std::collections::BTreeSet<_>>().len()==request.scope.paragraph_handles.len()};
        if (!inspection_schema&&request.schema_version!=SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA)||request.expected_head_generation==0
            ||request.document_id.as_str().len()>1024||request.expected_source_package_sha256.len()!=64
            ||!request.expected_source_package_sha256.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c))
            ||!scope_valid||request.operation.query.is_empty()||request.operation.query.len()>4096
            ||request.operation.max_results==0||request.operation.max_results>10_000{return Err(E::Request);}
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn query(&self)->SourceSearchQuery<'_> {SourceSearchQuery {query:&self.operation.query,mode:match self.operation.kind {Kind::FindRegex|Kind::FindReviewRegex=>SourceSearchMode::Regex,_=>SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_results}}
    fn scope(&self)->SourceSearchScope<'_> {match self.scope.kind {ScopeKind::MappedDocument=>SourceSearchScope::MappedDocument,ScopeKind::Paragraphs=>SourceSearchScope::Paragraphs(&self.scope.paragraph_handles)}}
    fn canonical_sha(&self)->Result<String,E> {Ok(digest(&bounded(self,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {Ok(digest(&bounded(&(&self.schema_version,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn capability(&self)->&'static str {match self.operation.kind {Kind::FindLiteral|Kind::FindReviewLiteral=>"search.find_literal",Kind::FindRegex|Kind::FindReviewRegex=>"search.find_regex",Kind::FindDeclaredStyle|Kind::FindDefinitionStyle=>"search.find_style",Kind::FindControl=>"search.find_control"}}
    fn profile(&self)->&'static str {match self.schema_version.as_str() {SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA=>"hwpx-agent.product-source-search-preparation/v1",
        SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA=>"hwpx-agent.product-source-search-preparation/v2",SOURCE_SEARCH_DEFINITION_REQUEST_SCHEMA=>"hwpx-agent.product-source-search-preparation/v3",_=>"hwpx-agent.product-source-search-preparation/v4"}}
    fn control(&self)->Result<SourceControlKind,E> {serde_json::from_value(serde_json::Value::String(self.operation.query.clone())).map_err(|_|E::Request)}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSearchProductReceipt {
    pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredSourceSearchReceipt,pub idempotency_key_claimed:bool,
    pub full_search_product_native_cas_execution_publication_authority:bool,
}
pub struct PreparedStoredSourceSearchProduct {request:Request,candidate:PreparedStoredSourceSearch,receipt:SourceSearchProductReceipt}
impl fmt::Debug for PreparedStoredSourceSearchProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSourceSearchProduct(<redacted>; mapped_source_only)")}}
#[derive(Debug,Error)]
pub enum SourceSearchProductError {
    #[error("SOURCE_SEARCH_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("SOURCE_SEARCH_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("SOURCE_SEARCH_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("SOURCE_SEARCH_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("SOURCE_SEARCH_PRODUCT_SERVICE_REJECTED")] Stored(#[from] StoredSourceSearchError),
    #[error("SOURCE_SEARCH_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type E=SourceSearchProductError;
#[derive(Debug)]
pub struct StoredSourceSearchProductRequest;
impl StoredSourceSearchProductRequest {
    /// # Errors
    /// Strict source-bound request; requires write scope before reading the sealed source.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearchProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=match request.operation.kind {
            Kind::FindReviewLiteral|Kind::FindReviewRegex=>source.into_review_text_search(provider,request.query(),request.scope(),request.operation.review_policy.ok_or(E::Request)?,limits,now)?,
            Kind::FindDefinitionStyle=>source.into_source_inspection(provider,SourceInspectionOperation::DefinitionStyle {query:request.query(),filter:request.operation.definition_filter.ok_or(E::Request)?},request.scope(),limits,now)?,
            Kind::FindDeclaredStyle=>source.into_source_inspection(provider,SourceInspectionOperation::DeclaredStyle {query:request.query(),filter:request.operation.style_filter.ok_or(E::Request)?},request.scope(),limits,now)?,
            Kind::FindControl=>source.into_source_inspection(provider,SourceInspectionOperation::Control {kind:request.control()?,max_results:request.operation.max_results},request.scope(),limits,now)?,
            _=>source.into_source_search(provider,request.query(),request.scope(),limits,now)?,
        };
        let receipt=SourceSearchProductReceipt {profile:request.profile(),capability_id:request.capability(),
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,full_search_product_native_cas_execution_publication_authority:false};
        let product=PreparedStoredSourceSearchProduct {request,candidate,receipt};product.check(provider)?;Ok(product)
    }
}
impl PreparedStoredSourceSearchProduct {
    #[must_use] pub const fn receipt(&self)->&SourceSearchProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.receipt.profile!=self.request.profile()||self.receipt.capability_id!=self.request.capability()
            ||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||hex::encode(self.receipt.stored.index.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_product_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Fresh service access and final head, without rerunning the search query.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<SourceSearchProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Rechecks current access/head before exposing the immutable bounded match response.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_json(provider,now,consume)?)
    }
    /// # Errors
    /// Full operation/CLI/Native qualification remains unavailable even after verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
