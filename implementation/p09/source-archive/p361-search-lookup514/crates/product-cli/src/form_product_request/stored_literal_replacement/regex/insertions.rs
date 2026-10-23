//! Required insertion policy and versioned request identities; no widening of v1 or execution gates.
use super::*;
compiler_product!(PreparedStoredRegexInsertionProduct, request.inner, plain);
use crate::form_stored_provider::actual_import::literal_search_output::regex::insertions::{PreparedStoredSelectorRegexInsertionCandidate,
    StoredSelectorRegexInsertionReceipt,STORED_SELECTOR_REGEX_INSERTION_PROFILE};
use hwpx_package::document_import::search::replacement::atoms::regex::{SourceRegexInsertionPolicy,SOURCE_SELECTOR_REGEX_INSERTION_PROFILE};
pub const REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-regex-replacement-request/v2";
pub const REGEX_INSERTION_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-regex-replacement-preparation/v2";
struct InsertionRequest {inner:RegexRequest,policy:SourceRegexInsertionPolicy}
impl InsertionRequest {
    fn parse(raw:&[u8])->Result<Self,R> {
        let mut value=super::super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){R::Limit}else{R::Request})?;
        let policy=value.get_mut("operation").and_then(serde_json::Value::as_object_mut).and_then(|o|o.remove("insertion_policy")).ok_or(R::Request)?;
        let policy=serde_json::from_value(policy).map_err(|_|R::Request)?;
        let inner=RegexRequest::parse_value(value,REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA)?;
        let request=Self {inner,policy};request.canonical_sha()?;Ok(request)
    }
    fn canonical_sha(&self)->Result<String,R> {
        Ok(digest(&bounded(&(REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,self.policy,&self.inner),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))
    }
    fn scoped_sha(&self,scope:[u8;32])->Result<String,R> {
        Ok(digest(&bounded(&(REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct RegexInsertionProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredSelectorRegexInsertionReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredRegexInsertionProduct {request:InsertionRequest,candidate:PreparedStoredSelectorRegexInsertionCandidate<'static>,receipt:RegexInsertionProductReceipt}
impl fmt::Debug for PreparedStoredRegexInsertionProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredRegexInsertionProduct(<redacted>; source_candidate_not_transaction)")}}
#[derive(Debug)]
pub struct StoredRegexInsertionProductRequest;
impl StoredRegexInsertionProductRequest {
    /// # Errors
    /// Strict required v2 policy, selector/revision and template validation before source reads.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredRegexInsertionProduct,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=InsertionRequest::parse(raw)?;let inner=&request.inner;let scope=provider.source_search_product_scope(&inner.project_id,&inner.document_id)?;
        let source=provider.import_actual_forms(inner.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=inner.expected_source_package_sha256{return Err(R::Binding);}
        let candidate=source.into_review_selector_regex_insertion_candidate(provider,inner.query(),inner.selector.native().map_err(|_|R::Request)?,inner.operation.review_policy,
            &inner.operation.replacement,inner.operation.run_policy.native(),request.policy,limits,writer,now)?;
        let receipt=RegexInsertionProductReceipt {profile:REGEX_INSERTION_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_regex",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredRegexInsertionProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredRegexInsertionProduct {
    #[must_use] pub const fn receipt(&self)->&RegexInsertionProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request.inner;let insertion=&self.receipt.stored.output;let outer=&insertion.output;let output=&outer.output;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA||!request.operation.regex||self.receipt.profile!=REGEX_INSERTION_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_regex"||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_SELECTOR_REGEX_INSERTION_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||outer.template_bytes!=request.operation.replacement.len()||hex::encode(outer.template_sha256)!=digest(request.operation.replacement.as_bytes())
            ||outer.body_policy!=request.operation.review_policy||output.run_policy!=request.operation.run_policy.native()||output.matched_occurrences>request.operation.max_replacements
            ||insertion.profile!=SOURCE_SELECTOR_REGEX_INSERTION_PROFILE||insertion.insertion_policy!=self.request.policy||insertion.zero_width_matches>output.matched_occurrences
            ||!insertion.exact_original_cut_verified||!insertion.text_insertion_next_to_controls_qualified||!insertion.original_empty_text_expansion_qualified
            ||insertion.control_replacement_field_cache_native_or_execution_authority||self.receipt.stored.issuer_execution_publication_authority
            ||!crate::form_stored_provider::actual_import::literal_search_output::regex::source_receipt_matches(outer,output.source_package_sha256,
                SOURCE_SELECTOR_REGEX_INSERTION_PROFILE,hwpx_package::document_import::search::replacement::atoms::regex::SOURCE_REGEX_INSERTION_ATOM_PROFILE)
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_native_cas_execution_publication_authority{return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final-head checks, without query/capture/lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<RegexInsertionProductReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(R::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Current source and the final head check inside the original integrity callback precede delivery.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// No dispatcher, durable claim, revision CAS, Native execution or publication is granted.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
