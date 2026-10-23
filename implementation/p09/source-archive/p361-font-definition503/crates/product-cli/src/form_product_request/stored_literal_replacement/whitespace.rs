//! Strict original-match whitespace/control normalization; not a full transaction or Native path.
use super::*;
compiler_product!(PreparedStoredWhitespaceProduct, request, plain);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::whitespace::{PreparedStoredWhitespaceCandidate,StoredWhitespaceReceipt,
    StoredWhitespaceError,STORED_WHITESPACE_PROFILE,whitespace_receipt_matches};
use hwpx_package::document_import::search::{reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},replacement::atoms::whitespace::SourceWhitespacePolicy};
pub const WHITESPACE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-whitespace-normalization-request/v1";
pub const WHITESPACE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-whitespace-normalization-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind{NormalizeWhitespaceMatches}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,query:String,regex:bool,case_sensitive:bool,whole_word:bool,max_matches:usize,
    #[serde(skip_serializing_if="Option::is_none")] style_filter:Option<SourceReviewStyleFilter>,
    whitespace_policy:SourceWhitespacePolicy,run_policy:RunPolicy,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum WhitespaceProductError{
    #[error("WHITESPACE_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("WHITESPACE_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("WHITESPACE_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("WHITESPACE_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("WHITESPACE_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("WHITESPACE_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredWhitespaceError),
    #[error("WHITESPACE_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=WhitespaceProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,C>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=WHITESPACE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision||request.operation.query.is_empty()
            ||request.operation.query.len()>4096||request.operation.max_matches==0||request.operation.max_matches>10_000{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;
        request.operation.whitespace_policy.validate().map_err(|_|C::Request)?;
        if let Some(filter)=request.operation.style_filter{filter.validate().map_err(|_|C::Request)?;}
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn query(&self)->SourceSearchQuery<'_>{SourceSearchQuery{query:&self.operation.query,mode:if self.operation.regex{SourceSearchMode::Regex}else{SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_matches}}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(WHITESPACE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct WhitespaceProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredWhitespaceReceipt,
    pub idempotency_key_claimed:bool,pub full_whitespace_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredWhitespaceProduct{request:Request,candidate:PreparedStoredWhitespaceCandidate<'static>,receipt:WhitespaceProductReceipt}
impl fmt::Debug for PreparedStoredWhitespaceProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredWhitespaceProduct(<redacted>; original_whitespace_candidate_not_full_transaction)")}}
#[derive(Debug)]
pub struct StoredWhitespaceProductRequest;
impl StoredWhitespaceProductRequest{
    /// # Errors
    /// Unique bounded JSON, selector and complete normalization policy before any source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredWhitespaceProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_whitespace_candidate(provider,request.query(),request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,
            request.operation.style_filter,request.operation.whitespace_policy,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=WhitespaceProductReceipt{profile:WHITESPACE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.normalize_whitespace",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_whitespace_native_cas_execution_publication_authority:false};
        let result=PreparedStoredWhitespaceProduct{request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredWhitespaceProduct{
    #[must_use] pub const fn receipt(&self)->&WhitespaceProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=WHITESPACE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=WHITESPACE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.normalize_whitespace"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_WHITESPACE_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.policy!=request.operation.whitespace_policy||output.run_policy!=request.operation.run_policy.native()||output.body_policy!=request.operation.review_policy
            ||output.filter!=request.operation.style_filter||output.search.search().result().matches().len()>request.operation.max_matches
            ||!whitespace_receipt_matches(output,output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_whitespace_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without another matcher or compiler call.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<WhitespaceProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained metadata never bypasses current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
