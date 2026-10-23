//! Strict v2 original-match normalization; v1 remains whole-selected-scope only.
use super::*;
compiler_product!(PreparedStoredUnicodeMatchProduct, request, plain);
use crate::form_stored_provider::actual_import::literal_search_output::unicode::matches::{PreparedStoredUnicodeMatchCandidate,StoredUnicodeMatchReceipt,
    StoredUnicodeMatchError,STORED_UNICODE_MATCH_PROFILE,match_receipt_matches};
use hwpx_package::document_import::search::reviews::selector::styles::SourceReviewStyleFilter;
pub const UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-unicode-normalization-request/v2";
pub const UNICODE_MATCH_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-unicode-normalization-preparation/v2";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {NormalizeUnicodeMatches}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,query:String,regex:bool,case_sensitive:bool,whole_word:bool,max_matches:usize,
    #[serde(skip_serializing_if="Option::is_none")] style_filter:Option<SourceReviewStyleFilter>,
    form:SourceUnicodeNormalizationForm,run_policy:RunPolicy,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum UnicodeMatchProductError {
    #[error("UNICODE_MATCH_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("UNICODE_MATCH_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("UNICODE_MATCH_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("UNICODE_MATCH_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("UNICODE_MATCH_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("UNICODE_MATCH_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredUnicodeMatchError),
    #[error("UNICODE_MATCH_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type M=UnicodeMatchProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,M> {
        let value=super::super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){M::Limit}else{M::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(M::Request)?).map_err(|_|M::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|M::Request)?;
        if request.schema_version!=UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision||request.operation.query.is_empty()
            ||request.operation.query.len()>4096||request.operation.max_matches==0||request.operation.max_matches>10_000{return Err(M::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|M::Request)?;
        if let Some(filter)=&request.operation.style_filter{filter.validate().map_err(|_|M::Request)?;}
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,M>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|M::Request)?),self.expected_head_generation).map_err(|_|M::Request)}
    fn query(&self)->SourceSearchQuery<'_>{SourceSearchQuery {query:&self.operation.query,mode:if self.operation.regex{SourceSearchMode::Regex}else{SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_matches}}
    fn canonical_sha(&self)->Result<String,M>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|M::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,M>{Ok(digest(&bounded(&(UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|M::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct UnicodeMatchProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredUnicodeMatchReceipt,
    pub idempotency_key_claimed:bool,pub full_normalization_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredUnicodeMatchProduct {request:Request,candidate:PreparedStoredUnicodeMatchCandidate<'static>,receipt:UnicodeMatchProductReceipt}
impl fmt::Debug for PreparedStoredUnicodeMatchProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredUnicodeMatchProduct(<redacted>; matched_original_candidate_not_full_transaction)")}}
#[derive(Debug)]
pub struct StoredUnicodeMatchProductRequest;
impl StoredUnicodeMatchProductRequest {
    /// # Errors
    /// Unique bounded object/selector, mode/query/filter/form and explicit policies before source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeMatchProduct,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(M::Binding);}
        let candidate=source.into_unicode_match_candidate(provider,request.query(),request.selector.native().map_err(|_|M::Request)?,request.operation.review_policy,
            request.operation.style_filter.clone(),request.operation.form,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=UnicodeMatchProductReceipt {profile:UNICODE_MATCH_PRODUCT_PREPARATION_PROFILE,capability_id:"search.normalize_unicode",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_normalization_native_cas_execution_publication_authority:false};
        let result=PreparedStoredUnicodeMatchProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredUnicodeMatchProduct {
    #[must_use] pub const fn receipt(&self)->&UnicodeMatchProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=UNICODE_MATCH_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.normalize_unicode"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_UNICODE_MATCH_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.output.form!=request.operation.form||output.output.run_policy!=request.operation.run_policy.native()||output.output.body_policy!=request.operation.review_policy
            ||output.filter!=request.operation.style_filter||output.search.search().result().matches().len()>request.operation.max_matches
            ||!match_receipt_matches(output,output.output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_normalization_native_cas_execution_publication_authority{return Err(M::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without another matcher or compiler call.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<UnicodeMatchProductReceipt,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(M::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained metadata never bypasses current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(M::RouteUnqualified)}
}
