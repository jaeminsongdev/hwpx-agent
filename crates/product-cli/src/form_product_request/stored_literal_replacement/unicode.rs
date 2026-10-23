//! Strict explicit whole-selected-scope normalization request; never ignore query/filter options.
pub mod matches;
use super::*;
compiler_product!(PreparedStoredUnicodeProduct, request, plain);
search_lookup_product!(StoredUnicodeProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::unicode::{PreparedStoredUnicodeCandidate,StoredUnicodeReceipt,
    StoredUnicodeError,STORED_UNICODE_PROFILE,source_receipt_matches};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::unicode::SourceUnicodeNormalizationForm};
pub const UNICODE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-unicode-normalization-request/v1";
pub const UNICODE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-unicode-normalization-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {NormalizeUnicodeScope}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,form:SourceUnicodeNormalizationForm,run_policy:RunPolicy,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum UnicodeProductError {
    #[error("UNICODE_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("UNICODE_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("UNICODE_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("UNICODE_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("UNICODE_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("UNICODE_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredUnicodeError),
    #[error("UNICODE_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=UnicodeProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,R> {
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){R::Limit}else{R::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(R::Request)?).map_err(|_|R::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|R::Request)?;
        if request.schema_version!=UNICODE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision{return Err(R::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|R::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,R> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|R::Request)?),self.expected_head_generation).map_err(|_|R::Request)}
    fn canonical_sha(&self)->Result<String,R>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,R>{Ok(digest(&bounded(&(UNICODE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct UnicodeProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredUnicodeReceipt,
    pub idempotency_key_claimed:bool,pub full_normalization_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredUnicodeProduct {request:Request,candidate:PreparedStoredUnicodeCandidate<'static>,receipt:UnicodeProductReceipt}
impl fmt::Debug for PreparedStoredUnicodeProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredUnicodeProduct(<redacted>; selected_scope_candidate_not_full_contract)")}}
#[derive(Debug)]
pub struct StoredUnicodeProductRequest;
impl StoredUnicodeProductRequest {
    /// # Errors
    /// Explicit form/run/review policy and unique bounded object/selector validation before reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredUnicodeProduct,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(R::Binding);}
        let candidate=source.into_unicode_candidate(provider,request.selector.native().map_err(|_|R::Request)?,request.operation.review_policy,
            request.operation.form,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=UnicodeProductReceipt {profile:UNICODE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.normalize_unicode",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_normalization_native_cas_execution_publication_authority:false};
        let result=PreparedStoredUnicodeProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredUnicodeProduct {
    #[must_use] pub const fn receipt(&self)->&UnicodeProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=UNICODE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=UNICODE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.normalize_unicode"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_UNICODE_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.form!=request.operation.form||output.run_policy!=request.operation.run_policy.native()||output.body_policy!=request.operation.review_policy
            ||!source_receipt_matches(output,output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_normalization_native_cas_execution_publication_authority{return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Retained request/receipt never replaces current access, source and final head checks.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<UnicodeProductReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(R::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final current head is verified before invoking the consumer, without redoing normalization.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// Full operation dispatcher, durable key claim, CAS, Native and publication are not enabled.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
