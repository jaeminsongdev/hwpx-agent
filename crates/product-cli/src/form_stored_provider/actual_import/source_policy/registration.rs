//! Validated source/policy -> actual encrypted ingest -> trusted SQL registration.
//! Registration is metadata publication, not execution authority or an external issuer.
pub mod postgres;
use super::{
    MAX_POLICY_BYTES, PolicyReadScope, SOURCE_POLICY_MEDIA_TYPE, SOURCE_POLICY_PAYLOAD_SCHEMA,
    SourcePolicyBinding, SourcePolicyVersion, StoredImportedDocumentForms, read_artifact,
    read_scope, wire,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, AuthScope, ContentDigest,
    EncryptedBlobStore, FileName, IngestRequest, MediaType,
};
use hwpx_package::document_import::forms::policies::{
    FormPolicyBindingReceipt, FormPolicySourceBinding, PolicyBoundDocumentForms, SourceFormPolicy,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
use uuid::Uuid;

/// Only the actual validated ingest path constructs this request. Not JSON or an approval bit.
pub struct PolicyRegistrationRecord {
    binding: SourcePolicyBinding,
    expected_generation: u64,
    version: SourcePolicyVersion,
}
impl fmt::Debug for PolicyRegistrationRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PolicyRegistrationRecord(<redacted>)")
    }
}
impl PolicyRegistrationRecord {
    #[must_use]
    pub const fn version(&self) -> &SourcePolicyVersion {
        &self.version
    }
    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.expected_generation
    }
}
/// Trusted server adapter, not caller JSON. Must atomically enforce current membership,
/// source head/artifacts/ACLs/generation CAS and exact immutable row readback.
pub trait SourcePolicyRegistrationRepository: Send + Sync {
    /// # Errors
    /// Denies stale/unauthorized registrations; ambiguous commit must remain `OutcomeUnknown`.
    fn register(
        &self,
        scope: &PolicyReadScope,
        request: &PolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, PolicyRegistrationError>;
}
pub struct PreparedSourcePolicyRegistration<'a> {
    imported: &'a StoredImportedDocumentForms,
    binding: SourcePolicyBinding,
    bytes: Vec<u8>,
    receipt: FormPolicyBindingReceipt,
    expected_generation: u64,
}
impl fmt::Debug for PreparedSourcePolicyRegistration<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedSourcePolicyRegistration(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct RegisteredSourcePolicyReceipt {
    pub profile: &'static str,
    pub version: SourcePolicyBinding,
    pub artifact: artifact_service::ArtifactId,
    pub digest: ContentDigest,
    pub policy: FormPolicyBindingReceipt,
    pub qualification: &'static str,
}
impl fmt::Debug for RegisteredSourcePolicyReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RegisteredSourcePolicyReceipt(<redacted>)")
    }
}
impl StoredImportedDocumentForms {
    /// Validates complete explicit policy against fresh actual source before any write.
    /// # Errors
    /// Requires provider write scope and valid source/domain/generation/bounded payload.
    pub fn prepare_policy_registration<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        policies: &[SourceFormPolicy],
        expected_generation: u64,
        now: u64,
    ) -> Result<PreparedSourcePolicyRegistration<'_>, PolicyRegistrationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(PolicyRegistrationError::Scope);
        }
        if expected_generation >= i64::MAX as u64 {
            return Err(PolicyRegistrationError::Binding);
        }
        self.fresh_source(provider, now)
            .map_err(|_| PolicyRegistrationError::Source)?;
        let domain_binding = FormPolicySourceBinding::for_imported(&self.imported);
        let bound = PolicyBoundDocumentForms::bind(&self.imported, &domain_binding, policies)
            .map_err(|_| PolicyRegistrationError::Policy)?;
        let s = &self.source;
        let binding = SourcePolicyBinding {
            tenant: s.scope.tenant,
            project: s.scope.project,
            branch: s.scope.branch,
            document: s.scope.document.clone(),
            source_revision: s
                .head
                .revision_id()
                .ok_or(PolicyRegistrationError::Binding)?,
            source_head_generation: s.head.generation(),
            source_result_artifact: s.artifact,
            source_package_sha256: s.digest,
            source_provenance_sha256: ContentDigest::parse(&hex::encode(
                domain_binding.source_provenance_sha256,
            ))
            .map_err(|_| PolicyRegistrationError::Binding)?,
            observed_graph_sha256: ContentDigest::parse(&hex::encode(
                domain_binding.observed_graph_sha256,
            ))
            .map_err(|_| PolicyRegistrationError::Binding)?,
            policy_version: Uuid::new_v4(),
            policy_generation: expected_generation + 1,
            creator_subject: s.scope.subject,
        };
        // Validate the existing SQL20 identity/head bounds, without a synthetic artifact.
        revision_service::postgres::source_form_policy::SourcePolicyReadRequest::new(
            binding.project,
            binding.branch,
            binding.document.as_str().into(),
            s.head,
        )
        .map_err(|_| PolicyRegistrationError::Binding)?;
        let bytes=serde_json::to_vec(&serde_json::json!({"schema_version":SOURCE_POLICY_PAYLOAD_SCHEMA,"binding":binding,"policies":policies})).map_err(|_|PolicyRegistrationError::Payload)?;
        if bytes.is_empty()
            || bytes.len() > MAX_POLICY_BYTES
            || wire::decode(&bytes, &binding).map_err(|_| PolicyRegistrationError::Payload)?
                != policies
        {
            return Err(PolicyRegistrationError::Payload);
        }
        Ok(PreparedSourcePolicyRegistration {
            imported: self,
            binding,
            bytes,
            receipt: bound.receipt().clone(),
            expected_generation,
        })
    }
}
impl PreparedSourcePolicyRegistration<'_> {
    /// Ingests only generated validated policy; stale SQL CAS may leave an unregistered
    /// encrypted Evidence artifact. Never erases source, evidence or retries a commit.
    /// # Errors
    /// Denies fresh source/scope/scanner/ACL/AEAD or repository/CAS failures. Unknown
    /// commit acknowledgement remains distinct; a receipt is not an execution capability.
    pub fn register<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<RegisteredSourcePolicyReceipt, PolicyRegistrationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRegistrationRepository,
    {
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(PolicyRegistrationError::Scope);
        }
        self.imported
            .fresh_source(provider, now)
            .map_err(|_| PolicyRegistrationError::Source)?;
        let d = provider
            .artifacts
            .ingest(
                provider.artifact_context,
                IngestRequest {
                    bytes: self.bytes.clone(),
                    kind: ArtifactKind::Evidence,
                    media_type: MediaType::parse(SOURCE_POLICY_MEDIA_TYPE)
                        .map_err(|_| PolicyRegistrationError::Artifact)?,
                    file_name: FileName::parse("source-form-policy.json")
                        .map_err(|_| PolicyRegistrationError::Artifact)?,
                },
                now,
            )
            .map_err(|_| PolicyRegistrationError::Artifact)?;
        let version = SourcePolicyVersion {
            binding: self.binding.clone(),
            artifact: d.artifact_id,
            digest: ContentDigest::of(&self.bytes),
        };
        super::validate_version(self.imported, &version)
            .map_err(|_| PolicyRegistrationError::Binding)?;
        let bytes = read_artifact(provider, &version, now)
            .map_err(|_| PolicyRegistrationError::Artifact)?;
        if bytes != self.bytes {
            return Err(PolicyRegistrationError::Artifact);
        }
        let policies =
            wire::decode(&bytes, &self.binding).map_err(|_| PolicyRegistrationError::Payload)?;
        let bound = PolicyBoundDocumentForms::bind(
            &self.imported.imported,
            &FormPolicySourceBinding::for_imported(&self.imported.imported),
            &policies,
        )
        .map_err(|_| PolicyRegistrationError::Policy)?;
        if *bound.receipt() != self.receipt {
            return Err(PolicyRegistrationError::Policy);
        }
        self.imported
            .fresh_source(provider, now)
            .map_err(|_| PolicyRegistrationError::Source)?;
        let request = PolicyRegistrationRecord {
            binding: self.binding.clone(),
            expected_generation: self.expected_generation,
            version: version.clone(),
        };
        let committed = repository.register(&read_scope(self.imported), &request)?;
        // A server reply mismatch cannot be described as a confirmed no-effect failure.
        if committed != version {
            return Err(PolicyRegistrationError::OutcomeUnknown);
        }
        Ok(RegisteredSourcePolicyReceipt {
            profile: "hwpx-agent.registered-source-policy/partial-v1",
            version: self.binding.clone(),
            artifact: version.artifact,
            digest: version.digest,
            policy: self.receipt.clone(),
            qualification: "validated_source_payload_actual_aead_metadata_registration_not_external_issuer_native_execution_or_gate",
        })
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum PolicyRegistrationError {
    #[error("policy_registration_scope_denied")]
    Scope,
    #[error("policy_registration_source_denied")]
    Source,
    #[error("policy_registration_binding_invalid")]
    Binding,
    #[error("policy_registration_domain_invalid")]
    Policy,
    #[error("policy_registration_payload_invalid")]
    Payload,
    #[error("policy_registration_artifact_denied")]
    Artifact,
    #[error("policy_registration_repository_denied")]
    Repository,
    #[error("policy_registration_commit_outcome_unknown_do_not_retry_blindly")]
    OutcomeUnknown,
}
