//! Strict source paragraph sort request with current scope and retained immutable candidate.
use super::*;
compiler_product!(PreparedStoredParagraphSortProduct, request, plain);
search_lookup_product!(StoredParagraphSortProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::sort::{PreparedStoredParagraphSortCandidate,StoredParagraphSortReceipt,
    StoredParagraphSortError,STORED_PARAGRAPH_SORT_PROFILE,sort_receipt_matches};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::sort::SourceParagraphSortSpec};
pub const PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-paragraph-sort-request/v1";
pub const PARAGRAPH_SORT_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-paragraph-sort-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {SortSiblingParagraphs}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,sort_spec:SourceParagraphSortSpec,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum ParagraphSortProductError {
    #[error("PARAGRAPH_SORT_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("PARAGRAPH_SORT_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("PARAGRAPH_SORT_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("PARAGRAPH_SORT_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("PARAGRAPH_SORT_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("PARAGRAPH_SORT_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredParagraphSortError),
    #[error("PARAGRAPH_SORT_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=ParagraphSortProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,C> {
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision
            ||request.operation.sort_spec.max_comparison_bytes==0||request.operation.sort_spec.max_comparison_bytes>32*1024*1024{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ParagraphSortProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredParagraphSortReceipt,
    pub idempotency_key_claimed:bool,pub full_sort_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredParagraphSortProduct {request:Request,candidate:PreparedStoredParagraphSortCandidate<'static>,receipt:ParagraphSortProductReceipt}
impl fmt::Debug for PreparedStoredParagraphSortProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.write_str("PreparedStoredParagraphSortProduct(<redacted>; explicit_source_candidate_not_full_transaction)")}}
#[derive(Debug)]
pub struct StoredParagraphSortProductRequest;
impl StoredParagraphSortProductRequest {
    /// # Errors
    /// Closed unique JSON, selector and explicit sort policy before any source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_paragraph_sort_candidate(provider,request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,request.operation.sort_spec,limits,writer,now)?;
        let receipt=ParagraphSortProductReceipt {profile:PARAGRAPH_SORT_PRODUCT_PREPARATION_PROFILE,capability_id:"search.sort_text",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_sort_native_cas_execution_publication_authority:false};
        let result=PreparedStoredParagraphSortProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredParagraphSortProduct {
    pub(crate) fn compiler_sort_splices(&self)->&hwpx_package::document_import::search::replacement::atoms::sort::intents::SourceParagraphSortSpliceInventory {self.candidate.compiler_sort_splices()}
    #[must_use] pub const fn receipt(&self)->&ParagraphSortProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=PARAGRAPH_SORT_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.sort_text"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_PARAGRAPH_SORT_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.spec!=request.operation.sort_spec||output.body_policy!=request.operation.review_policy
            ||!sort_receipt_matches(output,output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_sort_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without another sort or source import.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<ParagraphSortProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained receipts never bypass current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No dispatcher, durable idempotency, CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
