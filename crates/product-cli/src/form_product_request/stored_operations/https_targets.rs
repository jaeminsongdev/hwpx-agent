//! Strict HTTPS request + common scoped lookup + owned original candidate/compiler.
//! Digests/observations are not claims, execution permits, operating policy issuers or commit authority.
pub mod routing;
pub mod admission;
pub mod dispatch;
use super::{StoredProductRequest,compiled_search::request_lookup::{PreparedSearchRequestLookup,SearchRequestLookupError}};
use super::super::{UniqueJson,bounded,digest};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,
    source_search::StoredSourceSearchError,https_target_output::{HttpsTargetPolicyRepository,StoredHttpsTargetError,
        compiled::{PreparedCompiledHttpsTargetCandidate,CompiledHttpsTargetReceipt,HttpsTargetCompileError}}}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,ContentDigest,EncryptedBlobStore};
use domain_ir::{CompiledOperationPlan,DocumentId,HyperlinkTarget,IdempotencyKey,LinkReferenceLimits,LogicalId,PlanId,ProjectId,ReferenceAuxiliaryLimits,RevisionId};
use hwpx_package::{WriterLimits,document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetChange};
use revision_service::{RevisionHead,RevisionRepository,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    request_lookup::{StoredRequestLookupRepository,StoredRequestObservation},lifecycle::StoredJobObservation}};
use serde::{Deserialize,Serialize};
use std::{collections::BTreeSet,fmt};
use thiserror::Error;
pub const HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-https-target-request/v1";
const PROFILE:&str="hwpx-agent.product-https-target-preparation/v1";
const MAX_REQUEST_BYTES:usize=2*1024*1024;
const MAX_CHANGES:usize=4096;
#[derive(Clone,Copy,Debug)]
pub struct HttpsTargetProductLimits{pub auxiliary:ReferenceAuxiliaryLimits,pub targets:LinkReferenceLimits,pub writer:WriterLimits}
impl HttpsTargetProductLimits{
    /// # Errors
    /// Original finite source/target budgets, not caller-supplied policy values.
    pub fn standard()->Result<Self,HttpsTargetProductError>{Ok(Self{auxiliary:ReferenceAuxiliaryLimits::new(Default::default()).map_err(|_|E::Limit)?,
        targets:LinkReferenceLimits::new(Default::default()).map_err(|_|E::Limit)?,writer:WriterLimits::default()})}
}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind{ChangeHttpsTargets}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Change{reference_id:LogicalId,expected_source_field_sha256:String,expected_meaning_sha256:String,target:HyperlinkTarget}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,changes:Vec<Change>}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,operation:Operation}
fn valid_sha(value:&str)->bool{value.len()==64&&value.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b))}
impl Request{
    fn parse(raw:&[u8],limits:HttpsTargetProductLimits)->Result<Self,E>{
        if raw.is_empty()||raw.len()>MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!value.get("operation").is_some_and(serde_json::Value::is_object){return Err(E::Request);}
        let changes=value["operation"]["changes"].as_array().ok_or(E::Request)?;
        if changes.is_empty()||changes.len()>MAX_CHANGES||changes.len()>limits.auxiliary.config().items_per_kind
            ||changes.len()>limits.targets.config().hyperlinks{return Err(E::Limit);}
        if changes.iter().any(|v|!v.is_object()||!v.get("target").is_some_and(serde_json::Value::is_object)){return Err(E::Request);}
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        if request.schema_version!=HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.expected_head_generation>i64::MAX as u64
            ||request.document_id.as_str().len()>1024||!valid_sha(&request.expected_source_package_sha256){return Err(E::Request);}
        let mut seen=BTreeSet::new();
        for change in &request.operation.changes{
            if !seen.insert(&change.reference_id)||!valid_sha(&change.expected_source_field_sha256)||!valid_sha(&change.expected_meaning_sha256)
                ||!matches!(change.target,HyperlinkTarget::Https{..}){return Err(E::Request);}
            change.target.external_approval_sha256(limits.targets).map_err(|_|E::Request)?;
        }
        request.head()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),
        self.expected_head_generation).map_err(|_|E::Request)}
    fn canonical(&self)->Result<String,E>{Ok(digest(&bounded(self,MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped(&self,scope:[u8;32],canonical:&str)->Result<String,E>{Ok(digest(&bounded(&(HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA,scope,canonical),MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn lookup<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<PreparedHttpsTargetLookup,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let scope=provider.source_search_product_scope(&self.project_id,&self.document_id)?;let canonical=self.canonical()?;let scoped=self.scoped(scope,&canonical)?;
        Ok(PreparedHttpsTargetLookup{shared:PreparedSearchRequestLookup::bind(provider,&self.project_id,&self.document_id,&self.idempotency_key,&canonical,&scoped,
            ContentDigest::parse(&self.expected_source_package_sha256).map_err(|_|E::Request)?,self.head()?,scope)?})
    }
}
pub(super) fn validate_request(raw:&[u8])->Result<(),E>{Request::parse(raw,HttpsTargetProductLimits::standard()?).map(|_|())}
#[derive(Debug,Error)]
pub enum HttpsTargetProductError{
    #[error("HTTPS_TARGET_PRODUCT_REQUEST_REJECTED")]Request,
    #[error("HTTPS_TARGET_PRODUCT_LIMIT")]Limit,
    #[error("HTTPS_TARGET_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("HTTPS_TARGET_PRODUCT_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("HTTPS_TARGET_PRODUCT_STORED_CANDIDATE_REJECTED")]Stored(#[from]StoredHttpsTargetError),
    #[error("HTTPS_TARGET_PRODUCT_COMPILER_REJECTED")]Compiler(#[from]HttpsTargetCompileError),
    #[error("HTTPS_TARGET_PRODUCT_LOOKUP_REJECTED")]Lookup(#[from]SearchRequestLookupError),
    #[error("HTTPS_TARGET_PRODUCT_BINDING_REJECTED")]Binding,
}
type E=HttpsTargetProductError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct HttpsTargetProductReceipt{pub profile:&'static str,pub request_schema:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub compiled:CompiledHttpsTargetReceipt,
    pub idempotency_key_claimed:bool,pub execution_or_publication_authority:bool}
pub struct PreparedHttpsTargetProduct{request:Request,candidate:PreparedCompiledHttpsTargetCandidate<'static>,receipt:HttpsTargetProductReceipt}
impl fmt::Debug for PreparedHttpsTargetProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedHttpsTargetProduct(<redacted>; no_claim_or_execution_authority)")}}
pub struct PreparedHttpsTargetLookup{shared:PreparedSearchRequestLookup}
impl fmt::Debug for PreparedHttpsTargetLookup{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedHttpsTargetLookup(<redacted>; observation_only)")}}
impl PreparedHttpsTargetLookup{
    #[must_use]pub fn canonical_request_sha256(&self)->[u8;32]{self.shared.canonical_request_sha256()}
    #[must_use]pub fn scoped_request_sha256(&self)->[u8;32]{self.shared.scoped_request_sha256()}
    /// # Errors
    /// Reuses the common current scoped lookup. No claim, source, policy, compiler or retry fallback.
    pub fn observe<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<StoredRequestObservation,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository{Ok(self.shared.observe(provider)?)}
    /// Read-only existing-effect recovery, not a new policy approval, claim or replay permit.
    /// # Errors
    /// Uses the unchanged common scoped SQL lookup, registered archives, current ACL/AEAD
    /// and a second observation. Missing or uncertain evidence never falls back to execution.
    pub fn recover_registered<R,B,S,V,F>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,clock:F)
        ->Result<crate::form_stored_provider::actual_import::source_search::request_recovery::StoredRequestRecoveryObservation,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,
        V:StoredRequestLookupRepository+revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredRevisionJobRepository,
        F:FnMut()->u64{Ok(self.shared.recover_registered(provider,clock)?)}
}
pub enum HttpsTargetRequestEntry{Existing(StoredJobObservation),Prepared(Box<PreparedHttpsTargetProduct>)}
impl fmt::Debug for HttpsTargetRequestEntry{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str(match self{Self::Existing(_)=>"HttpsTargetRequestEntry::Existing(<redacted>; observation_only)",Self::Prepared(_)=>"HttpsTargetRequestEntry::Prepared(<redacted>; route_unqualified)"})}}
impl StoredProductRequest{
    /// # Errors
    /// Strict request and pure target validation before any source read; explicit trusted repository required.
    pub fn prepare_https_targets_json<R,B,S,V,P>(provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,raw:&[u8],limits:HttpsTargetProductLimits,now:u64)->Result<PreparedHttpsTargetProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        prepare(provider,repository,Request::parse(raw,limits)?,raw,limits,now)
    }
    /// # Errors
    /// Pure parsing/scope binding, without head/source reads or execution authority.
    pub fn prepare_https_targets_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:HttpsTargetProductLimits)->Result<PreparedHttpsTargetLookup,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{Request::parse(raw,limits)?.lookup(provider)}
    /// # Errors
    /// Existing observations and repository errors never fall back to source/policy/compiler work.
    /// NotObserved is not a claim or absence lease; future durable claim/CAS must still resolve races.
    pub fn prepare_https_targets_or_observe_json<R,B,S,V,P>(provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,raw:&[u8],limits:HttpsTargetProductLimits,now:u64)->Result<HttpsTargetRequestEntry,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository,P:HttpsTargetPolicyRepository{
        let request=Request::parse(raw,limits)?;
        match request.lookup(provider)?.observe(provider)?{
            StoredRequestObservation::Existing(job)=>Ok(HttpsTargetRequestEntry::Existing(job)),
            StoredRequestObservation::NotObserved=>Ok(HttpsTargetRequestEntry::Prepared(Box::new(prepare(provider,repository,request,raw,limits,now)?))),
        }
    }
}
fn prepare<R,B,S,V,P>(provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,request:Request,raw:&[u8],limits:HttpsTargetProductLimits,now:u64)->Result<PreparedHttpsTargetProduct,E>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
    let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let canonical=request.canonical()?;let scoped=request.scoped(scope,&canonical)?;
    let source=provider.import_actual_forms(request.head()?,now)?;
    if hex::encode(source.receipt().imported.source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
    let mut changes=Vec::new();changes.try_reserve_exact(request.operation.changes.len()).map_err(|_|E::Limit)?;
    for change in &request.operation.changes{changes.push(SourceHttpsTargetChange{reference_id:&change.reference_id,
        expected_source_field_sha256:*ContentDigest::parse(&change.expected_source_field_sha256).map_err(|_|E::Request)?.as_bytes(),
        expected_meaning_sha256:*ContentDigest::parse(&change.expected_meaning_sha256).map_err(|_|E::Request)?.as_bytes(),target:&change.target});}
    let candidate=source.into_https_target_candidate(provider,repository,&changes,limits.auxiliary,limits.targets,limits.writer,now)?;
    drop(changes);let candidate=candidate.compile(provider,repository,request.plan_id.clone(),now)?;
    let receipt=HttpsTargetProductReceipt{profile:PROFILE,request_schema:HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA,raw_request_sha256:digest(raw),canonical_request_sha256:canonical,
        scoped_request_sha256:scoped,compiled:candidate.receipt().clone(),idempotency_key_claimed:false,execution_or_publication_authority:false};
    let prepared=PreparedHttpsTargetProduct{request,candidate,receipt};prepared.check(provider)?;Ok(prepared)
}
impl PreparedHttpsTargetProduct{
    #[must_use]pub const fn receipt(&self)->&HttpsTargetProductReceipt{&self.receipt}
    #[must_use]pub const fn compiled(&self)->&CompiledOperationPlan{self.candidate.compiled()}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let canonical=request.canonical()?;
        if self.receipt.profile!=PROFILE||self.receipt.request_schema!=HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA||self.receipt.canonical_request_sha256!=canonical
            ||self.receipt.scoped_request_sha256!=request.scoped(scope,&canonical)?||&self.receipt.compiled!=self.candidate.receipt()
            ||self.compiled().plan_id()!=&request.plan_id||self.compiled().base_revision()!=&request.base_revision
            ||self.receipt.compiled.head_generation!=request.expected_head_generation||hex::encode(self.receipt.compiled.source_package_sha256)!=request.expected_source_package_sha256
            ||self.receipt.idempotency_key_claimed||self.receipt.execution_or_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Rechecks scoped request/plan binding and original fresh source/policy; never regenerates the candidate.
    pub fn verify<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<&HttpsTargetProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check(provider)?;self.candidate.verify(provider,repository,now)?;Ok(&self.receipt)
    }
    /// # Errors
    /// Original consumer-final source/head/current-policy/AEAD path, not a public output selector.
    pub fn with_verified_bytes<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,repository,now,consume)?)
    }
    /// # Errors
    /// Plan/request hashes and idempotency lookup do not permit registration, durable execution or publication.
    pub fn require_current_product_route<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.check(provider)?;Ok(self.candidate.require_current_product_route(provider,repository,now)?)
    }
}
