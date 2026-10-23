//! Strict v4 selector windows for explicit review-body literal replacement, not execution.
use super::*;
compiler_product!(PreparedStoredSelectorLiteralProduct, request.base, plain);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::atoms::review::selector::{PreparedStoredSelectorLiteralCandidate,StoredSelectorLiteralReceipt};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,
    replacement::atoms::review::{SOURCE_REVIEW_LITERAL_PROFILE,selector::SOURCE_SELECTOR_LITERAL_PROFILE}};
pub const SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-literal-replacement-request/v4";
pub const SELECTOR_LITERAL_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-literal-replacement-preparation/v4";
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct SelectorRequest {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,
    base_revision:RevisionId,expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
struct RequestWithPolicy {base:SelectorRequest,policy:SourceReviewTextPolicy}
pub(super) fn parse_selector_object(raw:&[u8])->Result<serde_json::Value,E> {
    if raw.is_empty()||raw.len()>LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
    let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
    let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
    if !value.is_object()||!["selector","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}
    Ok(value)
}
impl RequestWithPolicy {
    fn parse(raw:&[u8])->Result<Self,E> {
        let mut value=parse_selector_object(raw)?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(E::Request)?).map_err(|_|E::Request)?;
        let policy=value.get_mut("operation").and_then(serde_json::Value::as_object_mut).ok_or(E::Request)?.remove("review_policy").ok_or(E::Request)?;
        if !policy.is_object(){return Err(E::Request);}let policy=serde_json::from_value(policy).map_err(|_|E::Request)?;
        let base:SelectorRequest=serde_json::from_value(value).map_err(|_|E::Request)?;
        if base.schema_version!=SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA||base.expected_head_generation==0||base.document_id.as_str().len()>1024
            ||!valid_sha(&base.expected_source_package_sha256)||base.selector.revision_id!=base.base_revision
            ||base.operation.query.is_empty()||base.operation.query.len()>4096||base.operation.max_replacements==0||base.operation.max_replacements>10_000{return Err(E::Request);}
        base.selector.validate_shape(has_sections,has_range).map_err(|_|E::Request)?;
        validate_literal_replacement(&base.operation.replacement).map_err(|_|E::Request)?;base.head()?;
        let request=Self {base,policy};request.canonical_sha()?;Ok(request)
    }
    fn canonical_sha(&self)->Result<String,E> {
        let mut value=serde_json::to_value(&self.base).map_err(|_|E::Request)?;
        value.get_mut("operation").and_then(serde_json::Value::as_object_mut).ok_or(E::Request)?
            .insert("review_policy".to_owned(),serde_json::to_value(self.policy).map_err(|_|E::Request)?);
        Ok(digest(&bounded(&value,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))
    }
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {Ok(digest(&bounded(&(SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
impl SelectorRequest {
    fn head(&self)->Result<RevisionHead,E> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn query(&self)->SourceSearchQuery<'_> {SourceSearchQuery {query:&self.operation.query,mode:SourceSearchMode::Literal,
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_replacements}}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SelectorLiteralProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredSelectorLiteralReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredSelectorLiteralProduct {request:RequestWithPolicy,candidate:PreparedStoredSelectorLiteralCandidate<'static>,receipt:SelectorLiteralProductReceipt}
impl fmt::Debug for PreparedStoredSelectorLiteralProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSelectorLiteralProduct(<redacted>; source_candidate_not_transaction)")}}
#[derive(Debug)]
pub struct StoredSelectorLiteralProductRequest;
impl StoredSelectorLiteralProductRequest {
    /// # Errors
    /// Strict selector/revision and body/value checks before any sealed-source read.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredSelectorLiteralProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=RequestWithPolicy::parse(raw)?;let base=&request.base;
        let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        let source=provider.import_actual_forms(base.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=base.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_review_selector_literal_candidate(provider,base.query(),base.selector.native().map_err(|_|E::Request)?,request.policy,
            &base.operation.replacement,base.operation.run_policy.native(),limits,writer,now)?;
        let receipt=SelectorLiteralProductReceipt {profile:SELECTOR_LITERAL_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_literal",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredSelectorLiteralProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredSelectorLiteralProduct {
    #[must_use] pub const fn receipt(&self)->&SelectorLiteralProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let base=&self.request.base;let outer=&self.receipt.stored.output;let body=&outer.body_candidate;let output=&body.output;
        let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        if base.schema_version!=SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=SELECTOR_LITERAL_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_literal"||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!="hwpx-agent.stored-selector-literal-candidate/v1"||self.receipt.stored.source.head_generation!=base.expected_head_generation
            ||base.selector.revision_id!=base.base_revision||hex::encode(output.source_package_sha256)!=base.expected_source_package_sha256
            ||output.replacement_bytes!=base.operation.replacement.len()||hex::encode(output.replacement_sha256)!=digest(base.operation.replacement.as_bytes())
            ||output.run_policy!=base.operation.run_policy.native()||output.matched_occurrences>base.operation.max_replacements
            ||body.body_policy!=self.request.policy||outer.profile!=SOURCE_SELECTOR_LITERAL_PROFILE||body.profile!=SOURCE_REVIEW_LITERAL_PROFILE||output.profile!=SOURCE_REVIEW_LITERAL_PROFILE
            ||outer.selector.index_sha256!=output.source_index_sha256||outer.selector.scope_sha256!=output.scope_sha256||!outer.scope_window_enforced
            ||outer.native_or_execution_authority||outer.selector.whole_document_visibility_native_flow_or_revision_authority
            ||!body.memo_payload_not_cached_result_verified||body.native_author_visibility_resolution_or_execution_qualified
            ||output.field_cached_content_edit_qualified||output.full_protection_native_or_execution_authority||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current stored source/access/writer/head checks without search or lowering replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<SelectorLiteralProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original stored writer callback rechecks final head before consumer access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// A source candidate does not claim a durable key, revision CAS, Native execution or publication.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
