//! Strict v7 style search over current review-aware source windows; old request meanings stay closed.
use super::*;
use hwpx_package::document_import::search::reviews::selector::styles::SourceReviewStyleFilter;
pub const SELECTOR_STYLE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v7";
pub const SELECTOR_STYLE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-source-search-preparation/v7";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {FindStyle}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct StyleOperation {kind:Kind,query:String,regex:bool,case_sensitive:bool,whole_word:bool,max_results:usize,
    style_filter:SourceReviewStyleFilter,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct StyleRequest {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:StyleOperation}
impl StyleRequest {
    fn parse(raw:&[u8])->Result<Self,E> {
        let value=Request::parse_object(raw)?;let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(E::Request)?)?;
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        if request.schema_version!=SELECTOR_STYLE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.selector.revision_id!=request.base_revision
            ||request.document_id.as_str().len()>1024||!valid_sha(&request.expected_source_package_sha256)||request.operation.query.is_empty()
            ||request.operation.query.len()>4096||request.operation.max_results==0||request.operation.max_results>10_000{return Err(E::Request);}
        request.selector.validate_shape(has_sections,has_range)?;request.operation.style_filter.validate().map_err(|_|E::Request)?;
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn query(&self)->SourceSearchQuery<'_> {SourceSearchQuery {query:&self.operation.query,mode:if self.operation.regex{SourceSearchMode::Regex}else{SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_results}}
    fn canonical_sha(&self)->Result<String,E> {Ok(digest(&bounded(self,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {Ok(digest(&bounded(&(SELECTOR_STYLE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
pub struct PreparedStoredSelectorStyleProduct {request:StyleRequest,candidate:PreparedStoredSourceSearch,receipt:SourceSearchProductReceipt}
impl fmt::Debug for PreparedStoredSelectorStyleProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSelectorStyleProduct(<redacted>; explicit_source_axes_not_effective_style)")}}
#[derive(Debug)]
pub struct StoredSelectorStyleProductRequest;
impl StoredSelectorStyleProductRequest {
    /// # Errors
    /// Strict bounded request/selector/policy/axis validation before any sealed-source access.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSelectorStyleProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=StyleRequest::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_review_style_search(provider,request.query(),request.selector.native()?,request.operation.review_policy,request.operation.style_filter.clone(),limits,now)?;
        let receipt=SourceSearchProductReceipt {profile:SELECTOR_STYLE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.find_style",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_product_native_cas_execution_publication_authority:false};
        let result=PreparedStoredSelectorStyleProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredSelectorStyleProduct {
    #[must_use] pub const fn receipt(&self)->&SourceSearchProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.request.schema_version!=SELECTOR_STYLE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=SELECTOR_STYLE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.find_style"||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!="hwpx-agent.stored-source-search/v7"||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||self.request.selector.revision_id!=self.request.base_revision||hex::encode(self.receipt.stored.index.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_product_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current source/access/head checks; retained results do not repeat query or definition lookup.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<SourceSearchProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original final consumer head check remains before JSON disclosure.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_json(provider,now,consume)?)
    }
    /// # Errors
    /// Immutable full style receipt context, not a cursor credential or execution grant.
    pub fn navigation_receipt_sha256(&self)->Result<String,E> {Ok(hex::encode(super::super::navigation::receipt_context(&self.receipt)?))}
    /// # Errors
    /// Same strict next parser, current full result/source checks and final head without another search.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(request,context)=super::super::navigation::bound_next(raw,&self.receipt)?;self.check(provider)?;
        Ok(self.candidate.with_next_verified_json(provider,&request,context,now,consume)?)
    }
    /// # Errors
    /// Preparation and cursor selection are not dispatcher, durable claim, revision CAS or Native authority.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
