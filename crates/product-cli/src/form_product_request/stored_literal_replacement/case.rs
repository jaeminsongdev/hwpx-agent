//! Strict original-match default-case conversion, separate from normalization and casefold search.
use super::*;
compiler_product!(PreparedStoredCaseProduct, request, plain);
search_lookup_product!(StoredCaseProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::case::{PreparedStoredCaseCandidate,StoredCaseReceipt,
    StoredCaseError,STORED_CASE_PROFILE,case_receipt_matches};
use hwpx_package::document_import::search::{reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},
    replacement::atoms::case::{SourceCaseMode,SourceCasePolicy}};
pub const CASE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-case-conversion-request/v1";
pub const CASE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-case-conversion-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {ConvertCaseMatches}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,query:String,regex:bool,case_sensitive:bool,whole_word:bool,max_matches:usize,
    #[serde(skip_serializing_if="Option::is_none")] style_filter:Option<SourceReviewStyleFilter>,
    mode:SourceCaseMode,case_policy:SourceCasePolicy,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum CaseProductError {
    #[error("CASE_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("CASE_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("CASE_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("CASE_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("CASE_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("CASE_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredCaseError),
    #[error("CASE_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=CaseProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,C> {
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=CASE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision||request.operation.query.is_empty()
            ||request.operation.query.len()>4096||request.operation.max_matches==0||request.operation.max_matches>10_000{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;
        if let Some(filter)=&request.operation.style_filter{filter.validate().map_err(|_|C::Request)?;}
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn query(&self)->SourceSearchQuery<'_>{SourceSearchQuery {query:&self.operation.query,mode:if self.operation.regex{SourceSearchMode::Regex}else{SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_matches}}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(CASE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaseProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredCaseReceipt,
    pub idempotency_key_claimed:bool,pub full_case_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredCaseProduct {request:Request,candidate:PreparedStoredCaseCandidate<'static>,receipt:CaseProductReceipt}
impl fmt::Debug for PreparedStoredCaseProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredCaseProduct(<redacted>; original_case_candidate_not_full_transaction)")}}
#[derive(Debug)]
pub struct StoredCaseProductRequest;
impl StoredCaseProductRequest {
    /// # Errors
    /// Unique bounded JSON/selector and explicit query/mode/policy before any source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredCaseProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_case_candidate(provider,request.query(),request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,
            request.operation.style_filter.clone(),request.operation.mode,request.operation.case_policy,limits,writer,now)?;
        let receipt=CaseProductReceipt {profile:CASE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.case_convert",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_case_native_cas_execution_publication_authority:false};
        let result=PreparedStoredCaseProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredCaseProduct {
    #[must_use] pub const fn receipt(&self)->&CaseProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=CASE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=CASE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.case_convert"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_CASE_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.mode!=request.operation.mode||output.policy!=request.operation.case_policy||output.body_policy!=request.operation.review_policy
            ||output.filter!=request.operation.style_filter||output.search.search().result().matches().len()>request.operation.max_matches
            ||!case_receipt_matches(output,output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_case_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without another matcher or compiler call.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<CaseProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained metadata never bypasses current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
