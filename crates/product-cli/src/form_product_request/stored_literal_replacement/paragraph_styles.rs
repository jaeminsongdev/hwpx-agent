//! Required paragraph axis/whole-paragraph extent, not arbitrary or effective-style execution.
use super::*;
compiler_product!(PreparedStoredParagraphStyleProduct, request, plain);
search_lookup_product!(StoredParagraphStyleProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::paragraph_styles::{PreparedStoredParagraphStyleCandidate,StoredParagraphStyleReceipt,
    StoredParagraphStyleError,STORED_PARAGRAPH_STYLE_PROFILE,source_receipt_matches};
use hwpx_package::document_import::search::{reviews::{SourceReviewTextPolicy,selector::styles::SourceReviewStyleFilter},
    replacement::atoms::styles::paragraphs::{SourceParagraphStyleTarget,SourceParagraphStyleExtent}};
pub const PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-paragraph-style-replacement-request/v1";
pub const PARAGRAPH_STYLE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-paragraph-style-replacement-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {ReplaceParagraphStyleReference}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,query:String,regex:bool,case_sensitive:bool,whole_word:bool,max_replacements:usize,
    style_filter:SourceReviewStyleFilter,replacement:SourceParagraphStyleTarget,extent:SourceParagraphStyleExtent,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum ParagraphStyleProductError {
    #[error("PARAGRAPH_STYLE_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("PARAGRAPH_STYLE_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("PARAGRAPH_STYLE_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("PARAGRAPH_STYLE_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("PARAGRAPH_STYLE_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("PARAGRAPH_STYLE_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredParagraphStyleError),
    #[error("PARAGRAPH_STYLE_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=ParagraphStyleProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,R> {
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){R::Limit}else{R::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(R::Request)?).map_err(|_|R::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|R::Request)?;
        if request.schema_version!=PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision||request.operation.query.is_empty()
            ||request.operation.query.len()>4096||request.operation.max_replacements==0||request.operation.max_replacements>10_000{return Err(R::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|R::Request)?;request.operation.style_filter.validate().map_err(|_|R::Request)?;
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,R> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|R::Request)?),self.expected_head_generation).map_err(|_|R::Request)}
    fn query(&self)->SourceSearchQuery<'_>{SourceSearchQuery {query:&self.operation.query,mode:if self.operation.regex{SourceSearchMode::Regex}else{SourceSearchMode::Literal},
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_replacements}}
    fn canonical_sha(&self)->Result<String,R>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,R>{Ok(digest(&bounded(&(PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ParagraphStyleProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredParagraphStyleReceipt,
    pub idempotency_key_claimed:bool,pub full_style_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredParagraphStyleProduct {request:Request,candidate:PreparedStoredParagraphStyleCandidate<'static>,receipt:ParagraphStyleProductReceipt}
impl fmt::Debug for PreparedStoredParagraphStyleProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredParagraphStyleProduct(<redacted>; paragraph_candidate_not_full_style_transaction)")}}
#[derive(Debug)]
pub struct StoredParagraphStyleProductRequest;
impl StoredParagraphStyleProductRequest {
    /// # Errors
    /// Required paragraph target/extent/filter/policy and bounded unique JSON/selector before reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphStyleProduct,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(R::Binding);}
        let candidate=source.into_paragraph_style_candidate(provider,request.query(),request.selector.native().map_err(|_|R::Request)?,request.operation.review_policy,
            request.operation.style_filter.clone(),request.operation.replacement,request.operation.extent,limits,writer,now)?;
        let receipt=ParagraphStyleProductReceipt {profile:PARAGRAPH_STYLE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_style",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_style_native_cas_execution_publication_authority:false};
        let result=PreparedStoredParagraphStyleProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredParagraphStyleProduct {
    #[must_use] pub const fn receipt(&self)->&ParagraphStyleProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=PARAGRAPH_STYLE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_style"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_PARAGRAPH_STYLE_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.target!=request.operation.replacement||output.extent!=request.operation.extent||output.filter!=request.operation.style_filter||output.body_policy!=request.operation.review_policy
            ||output.matched_occurrences>request.operation.max_replacements||!source_receipt_matches(output,output.source_package_sha256)
            ||self.receipt.stored.issuer_execution_publication_authority||self.receipt.idempotency_key_claimed||self.receipt.full_style_native_cas_execution_publication_authority{return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without repeating paragraph query or lowering.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<ParagraphStyleProductReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(R::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained receipt metadata never bypasses current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication route.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
