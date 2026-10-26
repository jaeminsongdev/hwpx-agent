//! Strict owned first-insertion requests through the original current-source compiler.
//! Request/plan identities do not grant registry, durable output, CAS or Native authority.
pub mod local_stage718;
pub mod local_host723;
use super::super::{bounded,digest,UniqueJson,MAX_ENVELOPE_BYTES};
use super::{PreparedStoredProductOperation,StoredProductRequest};
use super::compiled_search::request_lookup::{PreparedSearchRequestLookup,SearchRequestLookupError};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,
    source_search::StoredSourceSearchError,bookmark_insertion_output::{StoredBookmarkInsertionError,
        compiled707::{PreparedCompiledBookmarkInsertionCandidate,CompiledBookmarkInsertionReceipt,BookmarkInsertionCompileError}}}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore,ContentDigest};
use domain_ir::{CompiledOperationPlan,DocumentId,IdempotencyKey,LogicalId,PlanId,ProjectId,ReferenceAuxiliaryLimits,
    RevisionId,SourceAnchorHandle,CanonicalArgumentValue};
use hwpx_package::{WriterLimits,cross_reference_sdk::SdkCrossReferenceDisplay,document_import::fields::bookmark_insertion::SourceBookmarkInsertion};
use revision_service::{RevisionHead,RevisionRepository,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    lifecycle::StoredJobObservation,request_lookup::{StoredRequestLookupRepository,StoredRequestObservation}}};
use serde::{Deserialize,Serialize};
use std::fmt;
use thiserror::Error;
pub const BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-bookmark-insertion-request/v1";
const PROFILE:&str="hwpx-agent.product-bookmark-insertion-preparation/v1";
#[derive(Clone,Copy,Debug)]
pub struct BookmarkInsertionProductLimits{pub auxiliary:ReferenceAuxiliaryLimits,pub writer:WriterLimits}
impl BookmarkInsertionProductLimits{
    /// # Errors
    /// Validated finite server budgets, never request-selected policy or trust.
    pub fn standard()->Result<Self,E>{Ok(Self{auxiliary:ReferenceAuxiliaryLimits::new(Default::default()).map_err(|_|E::Limit)?,writer:WriterLimits::default()})}
}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind{InsertBookmarkCrossref}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Display{Page,BookmarkName,Content,RelativePosition}
impl Display{fn sdk(&self)->SdkCrossReferenceDisplay{match self{Self::Page=>SdkCrossReferenceDisplay::Page,
    Self::BookmarkName=>SdkCrossReferenceDisplay::BookmarkName,Self::Content=>SdkCrossReferenceDisplay::Content,
    Self::RelativePosition=>SdkCrossReferenceDisplay::RelativePosition}}}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,run:SourceAnchorHandle,target_id:LogicalId,display:Display,hyperlink:bool}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ParsedBookmarkInsertionRequest{
    schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,
    base_revision:RevisionId,expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,operation:Operation,
}
type E=BookmarkInsertionProductError;
impl ParsedBookmarkInsertionRequest{
    pub(super) fn parse(raw:&[u8],limits:BookmarkInsertionProductLimits)->Result<Self,E>{
        if raw.is_empty()||raw.len()>MAX_ENVELOPE_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;
        parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!value.get("operation").is_some_and(serde_json::Value::is_object)
            ||!value["operation"].get("run").is_some_and(serde_json::Value::is_object){return Err(E::Request);}
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        let sha=&request.expected_source_package_sha256;
        if request.schema_version!=BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0
            ||request.expected_head_generation>i64::MAX as u64||sha.len()!=64
            ||!sha.bytes().all(|v|v.is_ascii_digit()||(b'a'..=b'f').contains(&v)){return Err(E::Request);}
        if request.document_id.as_str().len()>1024||request.operation.run.opaque_handle.as_str().len()>1024
            ||request.operation.target_id.as_str().len()>1024||limits.auxiliary.config().items_per_kind<1
            ||request.operation.run.opaque_handle.as_str().len()>limits.auxiliary.config().text_bytes
            ||request.operation.target_id.as_str().len()>limits.auxiliary.config().text_bytes{return Err(E::Limit);}
        request.head()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E>{
        RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),
            self.expected_head_generation).map_err(|_|E::Request)
    }
    fn canonical(&self)->Result<String,E>{Ok(digest(&bounded(self,MAX_ENVELOPE_BYTES).map_err(|_|E::Limit)?))}
    fn scoped(&self,scope:[u8;32],canonical:&str)->Result<String,E>{
        Ok(digest(&bounded(&(BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA,scope,canonical),MAX_ENVELOPE_BYTES).map_err(|_|E::Limit)?))
    }
    fn lookup<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<PreparedBookmarkInsertionLookup,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let scope=provider.source_search_product_scope(&self.project_id,&self.document_id)?;let canonical=self.canonical()?;
        Ok(PreparedBookmarkInsertionLookup{shared:PreparedSearchRequestLookup::bind(provider,&self.project_id,&self.document_id,
            &self.idempotency_key,&canonical,&self.scoped(scope,&canonical)?,
            ContentDigest::parse(&self.expected_source_package_sha256).map_err(|_|E::Request)?,self.head()?,scope)?})
    }
}
#[derive(Debug,Error)]
pub enum BookmarkInsertionProductError{
    #[error("BOOKMARK_INSERTION_PRODUCT_REQUEST_REJECTED")]Request,
    #[error("BOOKMARK_INSERTION_PRODUCT_LIMIT")]Limit,
    #[error("BOOKMARK_INSERTION_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("BOOKMARK_INSERTION_PRODUCT_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("BOOKMARK_INSERTION_PRODUCT_CANDIDATE_REJECTED")]Stored(#[from]StoredBookmarkInsertionError),
    #[error("BOOKMARK_INSERTION_PRODUCT_COMPILER_REJECTED")]Compiler(#[from]BookmarkInsertionCompileError),
    #[error("BOOKMARK_INSERTION_PRODUCT_LOOKUP_REJECTED")]Lookup(#[from]SearchRequestLookupError),
    #[error("BOOKMARK_INSERTION_PRODUCT_BINDING_REJECTED")]Binding,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct BookmarkInsertionProductReceipt{
    pub profile:&'static str,pub request_schema:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub compiled:CompiledBookmarkInsertionReceipt,
    pub idempotency_key_claimed:bool,pub execution_or_publication_authority:bool,
}
pub struct PreparedBookmarkInsertionProduct{
    request:ParsedBookmarkInsertionRequest,candidate:PreparedCompiledBookmarkInsertionCandidate,receipt:BookmarkInsertionProductReceipt,
}
impl fmt::Debug for PreparedBookmarkInsertionProduct{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedBookmarkInsertionProduct(<redacted>; no_claim_CAS_or_execution_authority)")}
}
pub struct PreparedBookmarkInsertionLookup{shared:PreparedSearchRequestLookup}
impl fmt::Debug for PreparedBookmarkInsertionLookup{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedBookmarkInsertionLookup(<redacted>; observation_only)")}
}
impl PreparedBookmarkInsertionLookup{
    #[must_use]pub fn canonical_request_sha256(&self)->[u8;32]{self.shared.canonical_request_sha256()}
    #[must_use]pub fn scoped_request_sha256(&self)->[u8;32]{self.shared.scoped_request_sha256()}
    /// # Errors
    /// Original current scoped observer, no source/compiler/claim fallback.
    pub fn observe<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<StoredRequestObservation,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository{Ok(self.shared.observe(provider)?)}
}
pub enum BookmarkInsertionRequestEntry{Existing(StoredJobObservation),Prepared(Box<PreparedBookmarkInsertionProduct>)}
impl fmt::Debug for BookmarkInsertionRequestEntry{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str(match self{
        Self::Existing(_)=>"BookmarkInsertionRequestEntry::Existing(<redacted>; no_retry_grant)",
        Self::Prepared(_)=>"BookmarkInsertionRequestEntry::Prepared(<redacted>; route_unqualified)"})}
}
impl StoredProductRequest{
    /// # Errors
    /// Closed request before source access. No raw XML/Command/output/permit input.
    pub fn prepare_bookmark_insertion_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],
        limits:BookmarkInsertionProductLimits,now:u64)->Result<PreparedBookmarkInsertionProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        prepare(provider,ParsedBookmarkInsertionRequest::parse(raw,limits)?,raw,limits,now)
    }
    /// # Errors
    /// Pure scope/request binding, no head/source reads, preparation or key claim.
    pub fn prepare_bookmark_insertion_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],
        limits:BookmarkInsertionProductLimits)->Result<PreparedBookmarkInsertionLookup,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        ParsedBookmarkInsertionRequest::parse(raw,limits)?.lookup(provider)
    }
    /// # Errors
    /// Existing or uncertain lookups never fall back to source or compiler work.
    pub fn prepare_bookmark_insertion_or_observe_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],
        limits:BookmarkInsertionProductLimits,now:u64)->Result<BookmarkInsertionRequestEntry,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository{
        let request=ParsedBookmarkInsertionRequest::parse(raw,limits)?;
        match request.lookup(provider)?.observe(provider)?{
            StoredRequestObservation::Existing(job)=>Ok(BookmarkInsertionRequestEntry::Existing(job)),
            StoredRequestObservation::NotObserved=>Ok(BookmarkInsertionRequestEntry::Prepared(Box::new(prepare(provider,request,raw,limits,now)?))),
        }
    }
}
pub(super) fn prepare<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,request:ParsedBookmarkInsertionRequest,
    raw:&[u8],limits:BookmarkInsertionProductLimits,now:u64)->Result<PreparedBookmarkInsertionProduct,E>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
    let canonical=request.canonical()?;let scoped=request.scoped(scope,&canonical)?;
    let source=provider.import_actual_forms(request.head()?,now)?;
    if hex::encode(source.receipt().imported.source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
    let candidate=source.into_bookmark_insertion_candidate(provider,SourceBookmarkInsertion{run:&request.operation.run,
        target_id:&request.operation.target_id,display:request.operation.display.sdk(),hyperlink:request.operation.hyperlink},
        limits.auxiliary,limits.writer,now)?.compile(provider,request.plan_id.clone(),now)?;
    let receipt=BookmarkInsertionProductReceipt{profile:PROFILE,request_schema:BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA,
        raw_request_sha256:digest(raw),canonical_request_sha256:canonical,scoped_request_sha256:scoped,compiled:candidate.receipt().clone(),
        idempotency_key_claimed:false,execution_or_publication_authority:false};
    let product=PreparedBookmarkInsertionProduct{request,candidate,receipt};product.check(provider)?;Ok(product)
}
impl PreparedBookmarkInsertionProduct{
    #[must_use]pub const fn receipt(&self)->&BookmarkInsertionProductReceipt{&self.receipt}
    #[must_use]pub const fn compiled(&self)->&CompiledOperationPlan{self.candidate.compiled()}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;let canonical=r.canonical()?;
        if self.receipt.profile!=PROFILE||self.receipt.request_schema!=BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA
            ||self.receipt.canonical_request_sha256!=canonical||self.receipt.scoped_request_sha256!=r.scoped(scope,&canonical)?
            ||&self.receipt.compiled!=self.candidate.receipt()||self.compiled().plan_id()!=&r.plan_id
            ||self.compiled().base_revision()!=&r.base_revision||self.receipt.compiled.head_generation!=r.expected_head_generation
            ||hex::encode(self.receipt.compiled.source_package_sha256)!=r.expected_source_package_sha256
            ||self.compiled().operations().len()!=1||self.receipt.idempotency_key_claimed||self.receipt.execution_or_publication_authority{return Err(E::Binding);}
        let op=&self.compiled().operations()[0];
        for(key,expected)in[("source_run_anchor_json",serde_json::to_string(&r.operation.run).map_err(|_|E::Limit)?),
            ("selected_target_id_sha256",digest(r.operation.target_id.as_str().as_bytes()))]{
            if !op.arguments().get(key).is_some_and(|a|matches!(a.value(),CanonicalArgumentValue::Text(v)if v==&expected)){return Err(E::Binding);}
        }Ok(())
    }
    /// # Errors
    /// Request/plan identity and original current source authorization only.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<&BookmarkInsertionProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;self.candidate.verify(provider,now)?;Ok(&self.receipt)
    }
    /// # Errors
    /// The original callback performs its final source/ACL/head check before any delivery.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// Requests and plans do not register or authorize an execution route.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.require_current_product_route(provider,now)?)
    }
}
impl PreparedStoredProductOperation{
    #[must_use]pub fn as_bookmark_insertion(&self)->Option<&PreparedBookmarkInsertionProduct>{
        match self{Self::BookmarkInsertion(v)=>Some(v),_=>None}
    }
}
