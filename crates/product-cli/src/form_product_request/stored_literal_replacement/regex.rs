//! Strict regex candidate preparation; literal request semantics and full execution gates stay separate.
pub mod insertions;
use super::*;
compiler_product!(PreparedStoredRegexReplacementProduct, request, plain);
search_lookup_product!(StoredRegexReplacementProductRequest,|raw|RegexRequest::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::regex::{PreparedStoredSelectorRegexCandidate,StoredSelectorRegexReceipt,StoredRegexReplacementError,STORED_SELECTOR_REGEX_PROFILE};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::regex::{validate_regex_replacement_template,SOURCE_SELECTOR_REGEX_PROFILE,SOURCE_REGEX_TEXT_ATOM_PROFILE}};
pub const REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-regex-replacement-request/v1";
pub const REGEX_REPLACEMENT_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-regex-replacement-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum RegexKind {ReplaceRegex}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct RegexOperation {kind:RegexKind,query:String,replacement:String,regex:bool,case_sensitive:bool,whole_word:bool,max_replacements:usize,
    run_policy:RunPolicy,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct RegexRequest {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:RegexOperation}
impl RegexRequest {
    fn parse(raw:&[u8])->Result<Self,R> {
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){R::Limit}else{R::Request})?;
        Self::parse_value(value,REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)
    }
    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,R> {
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(R::Request)?).map_err(|_|R::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|R::Request)?;
        if request.schema_version!=schema||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision||!request.operation.regex
            ||request.operation.query.is_empty()||request.operation.query.len()>4096||request.operation.max_replacements==0||request.operation.max_replacements>10_000{return Err(R::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|R::Request)?;
        validate_regex_replacement_template(&request.operation.replacement).map_err(|_|R::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,R> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|R::Request)?),self.expected_head_generation).map_err(|_|R::Request)}
    fn query(&self)->SourceSearchQuery<'_> {SourceSearchQuery {query:&self.operation.query,mode:SourceSearchMode::Regex,
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_replacements}}
    fn canonical_sha(&self)->Result<String,R> {Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,R> {Ok(digest(&bounded(&(REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|R::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct RegexReplacementProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredSelectorRegexReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredRegexReplacementProduct {request:RegexRequest,candidate:PreparedStoredSelectorRegexCandidate<'static>,receipt:RegexReplacementProductReceipt}
impl fmt::Debug for PreparedStoredRegexReplacementProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredRegexReplacementProduct(<redacted>; source_candidate_not_transaction)")}}
#[derive(Debug,Error)]
pub enum RegexReplacementProductError {
    #[error("REGEX_REPLACEMENT_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("REGEX_REPLACEMENT_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("REGEX_REPLACEMENT_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("REGEX_REPLACEMENT_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("REGEX_REPLACEMENT_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("REGEX_REPLACEMENT_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredRegexReplacementError),
    #[error("REGEX_REPLACEMENT_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type R=RegexReplacementProductError;
#[derive(Debug)]
pub struct StoredRegexReplacementProductRequest;
impl StoredRegexReplacementProductRequest {
    /// # Errors
    /// Strict selector/revision, explicit body policy and template syntax before any original read.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredRegexReplacementProduct,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=RegexRequest::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(R::Binding);}
        let candidate=source.into_review_selector_regex_candidate(provider,request.query(),request.selector.native().map_err(|_|R::Request)?,request.operation.review_policy,
            &request.operation.replacement,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=RegexReplacementProductReceipt {profile:REGEX_REPLACEMENT_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_regex",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredRegexReplacementProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredRegexReplacementProduct {
    #[must_use] pub const fn receipt(&self)->&RegexReplacementProductReceipt {&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=&self.request;let outer=&self.receipt.stored.output;let output=&outer.output;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA||!request.operation.regex||self.receipt.profile!=REGEX_REPLACEMENT_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_regex"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_SELECTOR_REGEX_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||outer.template_bytes!=request.operation.replacement.len()||hex::encode(outer.template_sha256)!=digest(request.operation.replacement.as_bytes())
            ||outer.body_policy!=request.operation.review_policy||output.run_policy!=request.operation.run_policy.native()||output.matched_occurrences>request.operation.max_replacements
            ||outer.profile!=SOURCE_SELECTOR_REGEX_PROFILE||output.profile!=SOURCE_REGEX_TEXT_ATOM_PROFILE
            ||outer.expansion_sha256!=output.replacement_sha256||outer.expanded_replacement_bytes!=output.replacement_bytes||outer.match_regions.len()!=output.matched_occurrences
            ||outer.expansion_work_limit==0||outer.expansion_work_units>outer.expansion_work_limit||outer.selector.index_sha256!=output.source_index_sha256||outer.selector.scope_sha256!=output.scope_sha256
            ||!outer.captures_from_one_original_match_pass||!outer.capture_values_are_index_nfc_text||!outer.scope_window_enforced||outer.native_or_execution_authority
            ||outer.zero_width_control_or_field_cache_edit_qualified||outer.selector.whole_document_visibility_native_flow_or_revision_authority||self.receipt.stored.issuer_execution_publication_authority
            ||output.field_cached_content_edit_qualified||output.full_protection_native_or_execution_authority||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved
            ||!output.original_selection_contiguity_verified||!output.outside_selected_text_atoms_exact||!output.output_text_span_values_verified
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_native_cas_execution_publication_authority{return Err(R::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/head checks without another search, capture or lowering pass.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<RegexReplacementProductReceipt,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(R::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained metadata never bypasses fresh access and the original final writer callback head.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication is manufactured.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),R>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(R::RouteUnqualified)}
}
