//! Current stored source + repository-selected AEAD policy -> HTTPS candidate.
//! Observation intervals are not a policy lease, revision CAS or execution route.
pub mod compiled;
use super::{StoredActualFormImportError,StoredActualFormImportReceipt,StoredImportedDocumentForms};
use super::source_policy::SourcePolicyBinding;
use crate::form_stored_provider::{Scope,StoredFormProvider};
use artifact_service::{ArtifactId,ArtifactKind,ArtifactMetadataRepository,ArtifactScanner,AuthScope,
    ContentDigest,EncryptedBlobStore,StorageState,SubjectDigest,TenantId,ValidationState};
use domain_ir::{DocumentId,ExternalLinkPolicy,LinkReferenceLimits,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::fields::{ImportedDocumentFields,semantics::source_index::{SourceFieldMeaningIndex,
    https_targets::{SourceHttpsTargetCandidate,SourceHttpsTargetChange,SourceHttpsTargetError,SourceHttpsTargetReceipt}}}};
use revision_service::{BranchId,ProjectId,RevisionHead,RevisionRepository};
use serde::{Deserialize,Serialize};
use std::fmt;
use thiserror::Error;

pub const HTTPS_TARGET_POLICY_MEDIA_TYPE:&str="application/vnd.hwpx-agent.source-https-target-policy+json";
pub const HTTPS_TARGET_POLICY_SCHEMA:&str="hwpx-agent.source-https-target-policy/v1";
const MAX_POLICY_BYTES:usize=1024*1024;
const PROFILE:&str="hwpx-agent.stored-source-https-target-candidate/v1";

/// SourcePolicyBinding is shared content-binding data only, never a form-policy authority.
#[derive(Clone,Eq,PartialEq)]
pub struct HttpsTargetPolicyVersion{pub binding:SourcePolicyBinding,pub artifact:ArtifactId,pub digest:ContentDigest}
impl fmt::Debug for HttpsTargetPolicyVersion{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsTargetPolicyVersion(<redacted>)")}}
/// Constructed only from authenticated provider-owned source, not public request fields.
pub struct HttpsTargetPolicyScope{scope:Scope,head:RevisionHead,source:ArtifactId,digest:ContentDigest}
impl fmt::Debug for HttpsTargetPolicyScope{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsTargetPolicyScope(<redacted>)")}}
impl HttpsTargetPolicyScope{
    #[must_use]pub const fn tenant(&self)->TenantId{self.scope.tenant}
    #[must_use]pub const fn subject(&self)->SubjectDigest{self.scope.subject}
    #[must_use]pub const fn project(&self)->ProjectId{self.scope.project}
    #[must_use]pub const fn branch(&self)->BranchId{self.scope.branch}
    #[must_use]pub const fn document(&self)->&DocumentId{&self.scope.document}
    #[must_use]pub const fn head(&self)->RevisionHead{self.head}
    #[must_use]pub const fn source_artifact(&self)->ArtifactId{self.source}
    #[must_use]pub const fn source_sha256(&self)->ContentDigest{self.digest}
}
/// Trusted server repository, NOT a caller approval or artifact selector.
/// Every read must authorize current project write membership, source/policy ACLs,
/// latest version and revocation. No stale fallback. An SQL/issuer adapter is not supplied here.
pub trait HttpsTargetPolicyRepository:Send+Sync{
    /// # Errors
    /// Deny absent, revoked, foreign, unauthorized or unavailable current policy.
    fn read_current(&self,scope:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,StoredHttpsTargetError>;
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope{schema_version:String,binding:SourcePolicyBinding,policy:ExternalLinkPolicy}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredHttpsTargetReceipt{
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,
    pub policy_version:uuid::Uuid,pub policy_generation:u64,pub policy_artifact:ArtifactId,pub policy_raw_sha256:ContentDigest,
    pub output:SourceHttpsTargetReceipt,pub execution_or_publication_authority:bool,
}
pub struct PreparedStoredHttpsTargetCandidate<'a>{source:&'a StoredImportedDocumentForms,version:HttpsTargetPolicyVersion,
    output:SourceHttpsTargetCandidate,receipt:StoredHttpsTargetReceipt,anchors:Vec<domain_ir::SourceAnchorHandle>}
impl fmt::Debug for PreparedStoredHttpsTargetCandidate<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredHttpsTargetCandidate(<redacted>; no_CAS_or_execution_authority)")}}
#[derive(Debug,Error)]
pub enum StoredHttpsTargetError{
    #[error("STORED_HTTPS_TARGET_SOURCE_DENIED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_HTTPS_TARGET_WRITE_DENIED")]Permission,
    #[error("STORED_HTTPS_TARGET_REPOSITORY_DENIED")]Repository,
    #[error("STORED_HTTPS_TARGET_BINDING_DENIED")]Binding,
    #[error("STORED_HTTPS_TARGET_POLICY_ARTIFACT_DENIED")]Artifact,
    #[error("STORED_HTTPS_TARGET_POLICY_PAYLOAD_DENIED")]Payload,
    #[error("STORED_HTTPS_TARGET_CURRENT_POLICY_CHANGED")]Drift,
    #[error("STORED_HTTPS_TARGET_SOURCE_MEANINGS_DENIED")]Meanings,
    #[error("STORED_HTTPS_TARGET_LOWER_DENIED")]Lower(#[from]SourceHttpsTargetError),
    #[error("STORED_HTTPS_TARGET_OUTPUT_INTEGRITY_DENIED")]Integrity,
    #[error("STORED_HTTPS_TARGET_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type E=StoredHttpsTargetError;
fn scope(source:&StoredImportedDocumentForms)->HttpsTargetPolicyScope{
    HttpsTargetPolicyScope{scope:source.source.scope.clone(),head:source.source.head,source:source.source.artifact,digest:source.source.digest}
}
fn require_binding(source:&StoredImportedDocumentForms,version:&HttpsTargetPolicyVersion)->Result<(),E>{
    let b=&version.binding;let s=&source.source;let actual=&source.receipt.imported;
    if b.tenant!=s.scope.tenant||b.project!=s.scope.project||b.branch!=s.scope.branch||b.document!=s.scope.document
        ||Some(b.source_revision)!=s.head.revision_id()||b.source_head_generation!=s.head.generation()
        ||b.source_result_artifact!=s.artifact||b.source_package_sha256!=s.digest
        ||b.source_provenance_sha256.as_bytes()!=&actual.source_provenance_sha256||b.observed_graph_sha256.as_bytes()!=&actual.graph_sha256
        ||b.policy_version.is_nil()||b.policy_generation==0||b.policy_generation>i64::MAX as u64||version.artifact==s.artifact{return Err(E::Binding);}
    Ok(())
}
fn policy<R,B,S,V>(source:&StoredImportedDocumentForms,provider:&StoredFormProvider<'_,R,B,S,V>,
    version:&HttpsTargetPolicyVersion,now:u64)->Result<ExternalLinkPolicy,E>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    require_binding(source,version)?;
    let d=provider.artifacts.get_descriptor(provider.artifact_context,version.artifact,now).map_err(|_|E::Artifact)?;
    if d.artifact_id!=version.artifact||d.sha256!=version.digest||d.kind!=ArtifactKind::Evidence
        ||d.media_type.as_str()!=HTTPS_TARGET_POLICY_MEDIA_TYPE||d.storage_state!=StorageState::Available
        ||d.validation_state!=ValidationState::Verified||d.quarantine_reason.is_some()||d.size_bytes==0||d.size_bytes>MAX_POLICY_BYTES as u64{return Err(E::Artifact);}
    let bytes=provider.artifacts.download(provider.artifact_context,version.artifact,now).map_err(|_|E::Artifact)?;
    if bytes.is_empty()||bytes.len()>MAX_POLICY_BYTES||bytes.len()as u64!=d.size_bytes||ContentDigest::of(&bytes)!=version.digest{return Err(E::Artifact);}
    let e:Envelope=serde_json::from_slice(&bytes).map_err(|_|E::Payload)?;
    if e.schema_version!=HTTPS_TARGET_POLICY_SCHEMA||e.binding!=version.binding{return Err(E::Payload);}
    Ok(e.policy)
}
impl StoredImportedDocumentForms{
    /// One fresh original source proof and one whole-batch lowering, no caller-supplied policy.
    /// # Errors
    /// Requires write scope and current server-selected policy with actual artifact ACL/AEAD.
    /// Denies source/head/repository/payload/selection/protection changes without publishing output.
    pub fn prepare_https_target_candidate<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,
        requests:&[SourceHttpsTargetChange<'_>],limits:ReferenceAuxiliaryLimits,targets:LinkReferenceLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredHttpsTargetCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let scope=scope(self);let version=repository.read_current(&scope)?;let selected=policy(self,provider,&version,now)?;
        let fields=ImportedDocumentFields::import(&self.imported).map_err(|_|E::Meanings)?;
        let index=SourceFieldMeaningIndex::import(&fields,limits).map_err(|_|E::Meanings)?;
        let output=index.lower_https_target_candidates(&proof,requests,&selected,targets,writer)?;
        let anchors=compiled::selected_anchors(&fields,output.receipt())?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        if repository.read_current(&scope)?!=version{return Err(E::Drift);}
        if policy(self,provider,&version,now)?!=selected{return Err(E::Drift);}
        self.fresh_source(provider,now)?;
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        let receipt=StoredHttpsTargetReceipt{profile:PROFILE,source:self.receipt.clone(),policy_version:version.binding.policy_version,
            policy_generation:version.binding.policy_generation,policy_artifact:version.artifact,policy_raw_sha256:version.digest,
            output:output.receipt().clone(),execution_or_publication_authority:false};
        Ok(PreparedStoredHttpsTargetCandidate{source:self,version,output,receipt,anchors})
    }
}
impl PreparedStoredHttpsTargetCandidate<'_>{
    #[must_use]pub const fn receipt(&self)->&StoredHttpsTargetReceipt{&self.receipt}
    fn fresh<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        self.source.fresh_source(provider,now)?;
        let scope=scope(self.source);
        if repository.read_current(&scope)?!=self.version{return Err(E::Drift);}
        // Read the immutable policy again through real artifact authorization and AEAD.
        // No lowering, writer, search, original graph clone or global policy cache is replayed.
        policy(self.source,provider,&self.version,now)?;
        if repository.read_current(&scope)?!=self.version{return Err(E::Drift);}
        if self.receipt.profile!=PROFILE||self.receipt.source!=self.source.receipt||self.receipt.output!=*self.output.receipt()
            ||self.receipt.policy_version!=self.version.binding.policy_version||self.receipt.policy_generation!=self.version.binding.policy_generation
            ||self.receipt.policy_artifact!=self.version.artifact||self.receipt.policy_raw_sha256!=self.version.digest
            ||self.receipt.execution_or_publication_authority{return Err(E::Binding);}
        self.source.check_compiler_head(provider)?;Ok(())
    }
    /// # Errors
    /// Rechecks fresh source authorization, latest policy/revocation/ACL/AEAD and immutable output.
    pub fn verify<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<&StoredHttpsTargetReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.fresh(provider,repository,now)?;self.output.with_verified_bytes(|_|()).map_err(|_|E::Integrity)?;
        self.source.check_compiler_head(provider)?;Ok(&self.receipt)
    }
    /// # Errors
    /// Sole byte-delivery path; current checks plus final policy/head inside writer integrity callback.
    /// This is an observation boundary, NOT an atomic policy lease or authorization to publish.
    pub fn with_verified_bytes<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.fresh(provider,repository,now)?;
        self.output.with_verified_bytes(|bytes|{
            if repository.read_current(&scope(self.source))?!=self.version{return Err(E::Drift);}
            self.source.check_compiler_head(provider)?;Ok(consume(bytes))
        }).map_err(|_|E::Integrity)?
    }
    /// # Errors
    /// Fresh verification does not qualify a registry/compiler/job/commit or Native route.
    pub fn require_current_product_route<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.verify(provider,repository,now)?;Err(E::RouteUnqualified)
    }
}
