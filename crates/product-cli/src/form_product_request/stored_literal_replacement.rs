//! Strict literal replacement preparation; no public graph, commit or execution verdict.
#[macro_use] mod compiler_view;
pub mod atoms;
pub mod review;
pub mod selector;
pub mod regex;
pub mod styles;
pub mod text_styles;
pub mod paragraph_styles;
pub mod named_styles;
pub mod unicode;
pub mod case;
pub mod width;
pub mod fonts;
pub mod whitespace;
pub mod controls;
pub mod number_controls;
pub mod sort;
pub mod sort_groups;
pub mod personal_info;
use super::{UniqueJson,bounded,digest};
compiler_product!(PreparedStoredLiteralReplacementProduct, request, plain);
search_lookup_product!(StoredLiteralReplacementProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,
    literal_search_output::{PreparedStoredLiteralSearchCandidate,StoredLiteralSearchError,StoredLiteralSearchOutputReceipt},
    source_search::StoredSourceSearchError}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore};
use domain_ir::{DocumentId,IdempotencyKey,LogicalId,PlanId,ProjectId,RevisionId};
use hwpx_package::{WriterLimits,document_import::search::{SourceSearchLimits,SourceSearchMode,SourceSearchQuery,scope::SourceSearchScope,
    replacement::{SourceReplacementRunPolicy,validate_literal_replacement}}};
use revision_service::{RevisionHead,RevisionRepository};
use serde::{Deserialize,Serialize};
use std::{collections::BTreeSet,fmt};
use thiserror::Error;
pub const LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-literal-replacement-request/v1";
pub const LITERAL_REPLACEMENT_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-literal-replacement-preparation/v1";
pub const LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES:usize=16*1024;
#[derive(Clone,Copy,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum RunPolicy {FirstOriginalRunRetainAllRuns}
impl RunPolicy {fn native(self)->SourceReplacementRunPolicy {match self {Self::FirstOriginalRunRetainAllRuns=>SourceReplacementRunPolicy::FirstOriginalRunRetainAllRuns}}}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {ReplaceLiteral}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,query:String,replacement:String,case_sensitive:bool,whole_word:bool,max_replacements:usize,run_policy:RunPolicy}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum ScopeKind {MappedDocument,Paragraphs}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Scope {kind:ScopeKind,paragraph_handles:Vec<LogicalId>}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,
    base_revision:RevisionId,expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,scope:Scope,operation:Operation}
impl Request {
    fn parse(raw:&[u8])->Result<Self,E> {
        Self::parse_profile(raw,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)
    }
    fn parse_profile(raw:&[u8],schema:&str)->Result<Self,E> {
        Self::parse_value(Self::parse_object(raw)?,schema)
    }
    fn parse_object(raw:&[u8])->Result<serde_json::Value,E> {
        if raw.is_empty()||raw.len()>LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);
        let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!["scope","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}
        Ok(value)
    }
    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,E> {
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        let scope_valid=match request.scope.kind {ScopeKind::MappedDocument=>request.scope.paragraph_handles.is_empty(),
            ScopeKind::Paragraphs=>!request.scope.paragraph_handles.is_empty()&&request.scope.paragraph_handles.len()<=50_000
                &&request.scope.paragraph_handles.iter().collect::<BTreeSet<_>>().len()==request.scope.paragraph_handles.len()};
        if request.schema_version!=schema||request.expected_head_generation==0
            ||request.document_id.as_str().len()>1024||request.expected_source_package_sha256.len()!=64
            ||!request.expected_source_package_sha256.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c))||!scope_valid
            ||request.operation.query.is_empty()||request.operation.query.len()>4096||request.operation.max_replacements==0
            ||request.operation.max_replacements>10_000 {return Err(E::Request);}
        validate_literal_replacement(&request.operation.replacement).map_err(|_|E::Request)?;request.head()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn query(&self)->SourceSearchQuery<'_> {SourceSearchQuery {query:&self.operation.query,mode:SourceSearchMode::Literal,
        case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,max_results:self.operation.max_replacements}}
    fn scope(&self)->SourceSearchScope<'_> {match self.scope.kind {ScopeKind::MappedDocument=>SourceSearchScope::MappedDocument,ScopeKind::Paragraphs=>SourceSearchScope::Paragraphs(&self.scope.paragraph_handles)}}
    fn canonical_sha(&self)->Result<String,E> {Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {self.scoped_sha_profile(scope,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)}
    fn scoped_sha_profile(&self,scope:[u8;32],schema:&str)->Result<String,E> {Ok(digest(&bounded(&(schema,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct LiteralReplacementProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredLiteralSearchOutputReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredLiteralReplacementProduct {request:Request,candidate:PreparedStoredLiteralSearchCandidate<'static>,receipt:LiteralReplacementProductReceipt}
impl fmt::Debug for PreparedStoredLiteralReplacementProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredLiteralReplacementProduct(<redacted>; candidate_only)")}}
#[derive(Debug,Error)]
pub enum LiteralReplacementProductError {
    #[error("LITERAL_REPLACEMENT_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("LITERAL_REPLACEMENT_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("LITERAL_REPLACEMENT_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("LITERAL_REPLACEMENT_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("LITERAL_REPLACEMENT_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("LITERAL_REPLACEMENT_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredLiteralSearchError),
    #[error("LITERAL_REPLACEMENT_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type E=LiteralReplacementProductError;
#[derive(Debug)]
pub struct StoredLiteralReplacementProductRequest;
impl StoredLiteralReplacementProductRequest {
    /// # Errors
    /// Strict JSON and shared pure value policy before any original artifact read.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralReplacementProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_literal_search_candidate(provider,request.query(),request.scope(),&request.operation.replacement,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=LiteralReplacementProductReceipt {profile:LITERAL_REPLACEMENT_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_literal",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredLiteralReplacementProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredLiteralReplacementProduct {
    #[must_use] pub const fn receipt(&self)->&LiteralReplacementProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.receipt.profile!=LITERAL_REPLACEMENT_PRODUCT_PREPARATION_PROFILE||self.receipt.capability_id!="search.replace_literal"
            ||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||hex::encode(self.receipt.stored.output.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.stored.output.replacement_bytes!=self.request.operation.replacement.len()
            ||hex::encode(self.receipt.stored.output.replacement_sha256)!=digest(self.request.operation.replacement.as_bytes())
            ||self.receipt.stored.output.run_policy!=self.request.operation.run_policy.native()
            ||self.receipt.stored.output.matched_occurrences>self.request.operation.max_replacements||self.receipt.idempotency_key_claimed
            ||self.receipt.full_search_native_cas_execution_publication_authority {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current source/access/writer/head checks, not query replay or a commit grant.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<LiteralReplacementProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// The retained request/candidate never bypasses the final fresh consumer boundary.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// No dispatcher, CAS, durable key claim or Native qualification is manufactured.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
