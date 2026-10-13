//! Repository-selected immutable policy artifact -> actual ACL/AEAD -> strict source binding.
//! The repository must authorize every read. No `PostgreSQL` adapter or external issuer is implied.
mod wire;
pub mod postgres;
pub mod registration;
pub mod product;

use super::{StoredActualFormImportReceipt, StoredImportedDocumentForms};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactId, ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ContentDigest,
    EncryptedBlobStore, StorageState, SubjectDigest, TenantId, ValidationState,
};
use domain_ir::{DocumentGraph, DocumentId, FormDocumentState};
use hwpx_package::document_import::forms::policies::{
    FormPolicyBindingReceipt, FormPolicySourceBinding, PolicyBoundDocumentForms, SourceFormPolicy,
};
use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId, RevisionRepository};
use serde::{Deserialize, Serialize};
use std::fmt;
use thiserror::Error;
use uuid::Uuid;

pub const SOURCE_POLICY_MEDIA_TYPE: &str = "application/vnd.hwpx-agent.source-form-policy+json";
pub const SOURCE_POLICY_PAYLOAD_SCHEMA: &str = "hwpx-agent.source-form-policy/v1";
const MAX_POLICY_BYTES: usize = 1024 * 1024;

/// Content-bound immutable metadata; deserialization does NOT confer authority.
/// This must exactly match the repository row and the fresh actual imported source.
#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourcePolicyBinding {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub branch: BranchId,
    pub document: DocumentId,
    pub source_revision: RevisionId,
    pub source_head_generation: u64,
    pub source_result_artifact: ArtifactId,
    pub source_package_sha256: ContentDigest,
    pub source_provenance_sha256: ContentDigest,
    pub observed_graph_sha256: ContentDigest,
    pub policy_version: Uuid,
    pub policy_generation: u64,
    pub creator_subject: SubjectDigest,
}
impl fmt::Debug for SourcePolicyBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourcePolicyBinding(<redacted>)")
    }
}
/// Server repository output only; not a public artifact selector or approval bit.
#[derive(Clone, Eq, PartialEq)]
pub struct SourcePolicyVersion {
    pub binding: SourcePolicyBinding,
    pub artifact: ArtifactId,
    pub digest: ContentDigest,
}
impl fmt::Debug for SourcePolicyVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourcePolicyVersion(<redacted>)")
    }
}
/// Constructed only from the authenticated provider and fresh imported source.
#[derive(Clone, Eq, PartialEq)]
pub struct PolicyReadScope {
    tenant: TenantId,
    subject: SubjectDigest,
    project: ProjectId,
    branch: BranchId,
    document: DocumentId,
    head: RevisionHead,
}
impl fmt::Debug for PolicyReadScope {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PolicyReadScope(<redacted>)")
    }
}
impl PolicyReadScope {
    #[must_use]
    pub const fn tenant(&self) -> TenantId {
        self.tenant
    }
    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }
    #[must_use]
    pub const fn project(&self) -> ProjectId {
        self.project
    }
    #[must_use]
    pub const fn branch(&self) -> BranchId {
        self.branch
    }
    #[must_use]
    pub const fn document(&self) -> &DocumentId {
        &self.document
    }
    #[must_use]
    pub const fn head(&self) -> RevisionHead {
        self.head
    }
}
/// Every call MUST authorize current project membership, both artifact ACLs, head,
/// latest policy and revocation. No revoked/latest-to-old fallback is permitted.
/// Implementations are trusted server components, not caller JSON. SQL20 adapter pending.
pub trait SourcePolicyRepository: Send + Sync {
    /// # Errors
    /// Closed failure for absent, revoked, stale, unauthorized or unavailable policy.
    fn read_current(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredSourcePolicyError>;
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredSourcePolicyReceipt {
    pub profile: &'static str,
    pub policy_version: Uuid,
    pub policy_generation: u64,
    pub policy_artifact: ArtifactId,
    pub policy_raw_sha256: ContentDigest,
    pub imported: StoredActualFormImportReceipt,
    pub policy: FormPolicyBindingReceipt,
    pub qualification: &'static str,
}
/// Non-deserializable validated policy component. No publication/route capability.
pub struct StoredSourceFormPolicies<'a> {
    imported: &'a StoredImportedDocumentForms,
    version: SourcePolicyVersion,
    bytes: Vec<u8>,
    policies: Vec<SourceFormPolicy>,
    bound: PolicyBoundDocumentForms<'a>,
    receipt: StoredSourcePolicyReceipt,
}
impl fmt::Debug for StoredSourceFormPolicies<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredSourceFormPolicies(<redacted>)")
    }
}
impl StoredImportedDocumentForms {
    /// Reads a repository-selected policy, decrypts through the unchanged artifact service,
    /// decodes only explicit policy fields and merges against actual original observations.
    /// # Errors
    /// Rejects scope/source/head/ACL/AEAD/media/digest, malformed payload or domain policy failure.
    pub fn bind_stored_policies<'a, R, B, S, V, P>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<StoredSourceFormPolicies<'a>, StoredSourcePolicyError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRepository,
    {
        self.fresh_source(provider, now)
            .map_err(|_| StoredSourcePolicyError::Source)?;
        let scope = read_scope(self);
        let version = repository.read_current(&scope)?;
        validate_version(self, &version)?;
        let bytes = read_artifact(provider, &version, now)?;
        let policies = wire::decode(&bytes, &version.binding)?;
        let binding = FormPolicySourceBinding::for_imported(&self.imported);
        let bound = PolicyBoundDocumentForms::bind(&self.imported, &binding, &policies)
            .map_err(|_| StoredSourcePolicyError::Policy)?;
        // Fresh repository/source reads bound the observation interval; NOT an atomic lease.
        if repository.read_current(&scope)? != version {
            return Err(StoredSourcePolicyError::Drift);
        }
        self.fresh_source(provider, now)
            .map_err(|_| StoredSourcePolicyError::Source)?;
        let receipt = StoredSourcePolicyReceipt {
            profile: "hwpx-agent.stored-source-form-policy/partial-v1",
            policy_version: version.binding.policy_version,
            policy_generation: version.binding.policy_generation,
            policy_artifact: version.artifact,
            policy_raw_sha256: version.digest,
            imported: self.receipt.clone(),
            policy: bound.receipt().clone(),
            qualification: "repository_selected_actual_aead_strict_payload_component_not_sql_adapter_issuer_atomic_lease_full_import_execution_native_or_gate",
        };
        Ok(StoredSourceFormPolicies {
            imported: self,
            version,
            bytes,
            policies,
            bound,
            receipt,
        })
    }
}
impl StoredSourceFormPolicies<'_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.bound.graph()
    }
    #[must_use]
    pub const fn state(&self) -> &FormDocumentState {
        self.bound.state()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredSourcePolicyReceipt {
        &self.receipt
    }
    /// Re-authorizes current repository and both artifacts, downloads/decodes again and
    /// rebuilds complete actual policy graph/state. Cached receipts never authorize access.
    /// # Errors
    /// Rejects any revocation, latest version, scope/head/ACL/AEAD/raw payload or state drift.
    pub fn verify<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<StoredSourcePolicyReceipt, StoredSourcePolicyError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRepository,
    {
        let rebuilt = self
            .imported
            .bind_stored_policies(provider, repository, now)?;
        if self.version != rebuilt.version
            || self.bytes != rebuilt.bytes
            || self.policies != rebuilt.policies
            || self.bound.graph() != rebuilt.bound.graph()
            || self.bound.state() != rebuilt.bound.state()
            || self.bound.native_binding() != rebuilt.bound.native_binding()
            || self.receipt != rebuilt.receipt
        {
            return Err(StoredSourcePolicyError::Drift);
        }
        Ok(rebuilt.receipt)
    }
}
fn read_scope(imported: &StoredImportedDocumentForms) -> PolicyReadScope {
    let source = &imported.source;
    PolicyReadScope {
        tenant: source.scope.tenant,
        subject: source.scope.subject,
        project: source.scope.project,
        branch: source.scope.branch,
        document: source.scope.document.clone(),
        head: source.head,
    }
}
fn validate_version(
    imported: &StoredImportedDocumentForms,
    version: &SourcePolicyVersion,
) -> Result<(), StoredSourcePolicyError> {
    let b = &version.binding;
    let s = &imported.source;
    let actual = &imported.receipt.imported;
    let id = b.document.as_str().as_bytes();
    if b.tenant != s.scope.tenant
        || b.project != s.scope.project
        || b.branch != s.scope.branch
        || b.document != s.scope.document
        || Some(b.source_revision) != s.head.revision_id()
        || b.source_head_generation != s.head.generation()
        || b.source_result_artifact != s.artifact
        || b.source_package_sha256 != s.digest
        || b.source_provenance_sha256.as_bytes() != &actual.source_provenance_sha256
        || b.observed_graph_sha256.as_bytes() != &actual.graph_sha256
        || b.policy_version.is_nil()
        || b.policy_generation == 0
        || b.policy_generation > i64::MAX as u64
        || version.artifact == s.artifact
        || id.is_empty()
        || id.len() > 128
        || !id[0].is_ascii_alphanumeric()
        || !id
            .iter()
            .all(|x| x.is_ascii_alphanumeric() || b"._:-".contains(x))
    {
        return Err(StoredSourcePolicyError::Binding);
    }
    Ok(())
}
fn read_artifact<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    version: &SourcePolicyVersion,
    now: u64,
) -> Result<Vec<u8>, StoredSourcePolicyError>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    let d = provider
        .artifacts
        .get_descriptor(provider.artifact_context, version.artifact, now)
        .map_err(|_| StoredSourcePolicyError::Artifact)?;
    if d.artifact_id != version.artifact
        || d.sha256 != version.digest
        || d.kind != ArtifactKind::Evidence
        || d.media_type.as_str() != SOURCE_POLICY_MEDIA_TYPE
        || d.storage_state != StorageState::Available
        || d.validation_state != ValidationState::Verified
        || d.quarantine_reason.is_some()
        || d.size_bytes == 0
        || d.size_bytes > MAX_POLICY_BYTES as u64
    {
        return Err(StoredSourcePolicyError::Artifact);
    }
    let bytes = provider
        .artifacts
        .download(provider.artifact_context, version.artifact, now)
        .map_err(|_| StoredSourcePolicyError::Artifact)?;
    if bytes.is_empty()
        || bytes.len() > MAX_POLICY_BYTES
        || bytes.len() as u64 != d.size_bytes
        || ContentDigest::of(&bytes) != version.digest
    {
        return Err(StoredSourcePolicyError::Artifact);
    }
    Ok(bytes)
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredSourcePolicyError {
    #[error("stored_source_policy_repository_denied")]
    Repository,
    #[error("stored_source_policy_source_denied")]
    Source,
    #[error("stored_source_policy_binding_invalid")]
    Binding,
    #[error("stored_source_policy_artifact_denied")]
    Artifact,
    #[error("stored_source_policy_payload_invalid")]
    Payload,
    #[error("stored_source_policy_domain_invalid")]
    Policy,
    #[error("stored_source_policy_fresh_state_changed")]
    Drift,
}
