//! Source-derived field-policy DATA registration, not an issuer or execution capability.
mod generation;
pub mod postgres;

use super::super::{
    MAX_POLICY_BYTES, PolicyReadScope, SourcePolicyBinding, SourcePolicyVersion, read_scope,
    validate_version,
};
use super::{FORMULA_POLICY_MEDIA_TYPE, StoredImportedDocumentForms, targets, wire};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactId, ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, AuthScope,
    ContentDigest, EncryptedBlobStore, FileName, IngestRequest, MediaType,
};
use domain_ir::LogicalId;
use revision_service::{
    RevisionRepository, postgres::source_formula_policy::SourceFormulaPolicyReadRequest,
};
use serde::Serialize;
use std::fmt;
use thiserror::Error;
use uuid::Uuid;

/// Explicit server-side DATA decision. No serde, default allowance, supplied anchor or AST.
/// Callers must not expose this as a public approval/issuer endpoint.
#[derive(Clone)]
pub struct FormulaPolicyDecision {
    reference_id: LogicalId,
    allow_recalculation: bool,
}
impl FormulaPolicyDecision {
    #[must_use]
    pub const fn new(reference_id: LogicalId, allow_recalculation: bool) -> Self {
        Self {
            reference_id,
            allow_recalculation,
        }
    }
}
impl fmt::Debug for FormulaPolicyDecision {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaPolicyDecision(<redacted>)")
    }
}

/// Only the actual validated source/ingest path constructs the complete request.
pub struct FormulaPolicyRegistrationRecord {
    version: SourcePolicyVersion,
    expected_generation: u64,
}
impl FormulaPolicyRegistrationRecord {
    #[must_use]
    pub const fn version(&self) -> &SourcePolicyVersion {
        &self.version
    }
    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.expected_generation
    }
}
impl fmt::Debug for FormulaPolicyRegistrationRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaPolicyRegistrationRecord(<redacted>)")
    }
}
/// Trusted server component enforcing membership, current source, ACLs, CAS and whole readback.
pub trait FormulaPolicyRegistrationRepository: Send + Sync {
    /// # Errors
    /// Denies stale/unauthorized requests; lost commit acknowledgement must stay `OutcomeUnknown`.
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, FormulaPolicyRegistrationError>;
}

pub struct PreparedFormulaPolicyRegistration<'a> {
    source: &'a StoredImportedDocumentForms,
    binding: SourcePolicyBinding,
    bytes: Vec<u8>,
    targets: (ContentDigest, ContentDigest, usize),
    target_count: usize,
    expected_generation: u64,
}
impl fmt::Debug for PreparedFormulaPolicyRegistration<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFormulaPolicyRegistration(<redacted>)")
    }
}
/// Metadata receipt only; excludes raw decisions, document identifiers and creator identity.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct RegisteredFormulaPolicyReceipt {
    pub profile: &'static str,
    pub version: Uuid,
    pub generation: u64,
    pub artifact: ArtifactId,
    pub digest: ContentDigest,
    pub field_meaning_graph_sha256: ContentDigest,
    pub target_bindings_sha256: ContentDigest,
    pub formula_targets: usize,
    pub qualification: &'static str,
}
impl fmt::Debug for RegisteredFormulaPolicyReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RegisteredFormulaPolicyReceipt(<redacted>)")
    }
}

impl StoredImportedDocumentForms {
    /// Generates all target identities, anchors, AST/graph hashes from fresh original source.
    /// # Errors
    /// Requires write scope, complete unique decisions, bounded generation/payload and actual source.
    pub fn prepare_formula_policy_registration<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        decisions: &[FormulaPolicyDecision],
        expected_generation: u64,
        now: u64,
    ) -> Result<PreparedFormulaPolicyRegistration<'_>, FormulaPolicyRegistrationError>
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
            return Err(FormulaPolicyRegistrationError::Scope);
        }
        if expected_generation >= i64::MAX as u64 {
            return Err(FormulaPolicyRegistrationError::Binding);
        }
        self.fresh_source(provider, now)
            .map_err(|_| FormulaPolicyRegistrationError::Source)?;
        let source = &self.source;
        let receipt = &self.receipt.imported;
        let binding = SourcePolicyBinding {
            tenant: source.scope.tenant,
            project: source.scope.project,
            branch: source.scope.branch,
            document: source.scope.document.clone(),
            source_revision: source
                .head
                .revision_id()
                .ok_or(FormulaPolicyRegistrationError::Binding)?,
            source_head_generation: source.head.generation(),
            source_result_artifact: source.artifact,
            source_package_sha256: source.digest,
            source_provenance_sha256: ContentDigest::parse(&hex::encode(
                receipt.source_provenance_sha256,
            ))
            .map_err(|_| FormulaPolicyRegistrationError::Binding)?,
            observed_graph_sha256: ContentDigest::parse(&hex::encode(receipt.graph_sha256))
                .map_err(|_| FormulaPolicyRegistrationError::Binding)?,
            policy_version: Uuid::new_v4(),
            policy_generation: expected_generation + 1,
            creator_subject: source.scope.subject,
        };
        SourceFormulaPolicyReadRequest::new(
            binding.project,
            binding.branch,
            binding.document.as_str().into(),
            source.head,
        )
        .map_err(|_| FormulaPolicyRegistrationError::Binding)?;
        let bytes = generation::generate(self, provider, &binding, decisions, now)?;
        if bytes.is_empty() || bytes.len() > MAX_POLICY_BYTES {
            return Err(FormulaPolicyRegistrationError::Payload);
        }
        let payload =
            wire::decode(&bytes, &binding).map_err(|_| FormulaPolicyRegistrationError::Payload)?;
        let targets = targets::bind(self, provider, &payload, now)
            .map_err(|_| FormulaPolicyRegistrationError::Policy)?;
        self.fresh_source(provider, now)
            .map_err(|_| FormulaPolicyRegistrationError::Source)?;
        Ok(PreparedFormulaPolicyRegistration {
            source: self,
            binding,
            bytes,
            targets,
            target_count: payload.targets.len(),
            expected_generation,
        })
    }
}
impl PreparedFormulaPolicyRegistration<'_> {
    /// Rebinds generated policy before ingest; reads actual ACL/AEAD/scanner bytes, rebinds again,
    /// then calls server registration once. Unregistered/ambiguous Evidence is retained, never deleted.
    /// # Errors
    /// Denies scope/source/artifact/target/registration failures. Ambiguous commit is not retry-safe.
    pub fn register<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<RegisteredFormulaPolicyReceipt, FormulaPolicyRegistrationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRegistrationRepository,
    {
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(FormulaPolicyRegistrationError::Scope);
        }
        self.verify_payload(provider, &self.bytes, now)?;
        let descriptor = provider
            .artifacts
            .ingest(
                provider.artifact_context,
                IngestRequest {
                    bytes: self.bytes.clone(),
                    kind: ArtifactKind::Evidence,
                    media_type: MediaType::parse(FORMULA_POLICY_MEDIA_TYPE)
                        .map_err(|_| FormulaPolicyRegistrationError::Artifact)?,
                    file_name: FileName::parse("source-formula-policy.json")
                        .map_err(|_| FormulaPolicyRegistrationError::Artifact)?,
                },
                now,
            )
            .map_err(|_| FormulaPolicyRegistrationError::Artifact)?;
        let version = SourcePolicyVersion {
            binding: self.binding.clone(),
            artifact: descriptor.artifact_id,
            digest: ContentDigest::of(&self.bytes),
        };
        validate_version(self.source, &version)
            .map_err(|_| FormulaPolicyRegistrationError::Binding)?;
        let bytes = wire::read_artifact(provider, &version, now)
            .map_err(|_| FormulaPolicyRegistrationError::Artifact)?;
        if bytes != self.bytes {
            return Err(FormulaPolicyRegistrationError::Artifact);
        }
        self.verify_payload(provider, &bytes, now)?;
        let record = FormulaPolicyRegistrationRecord {
            version: version.clone(),
            expected_generation: self.expected_generation,
        };
        let committed = repository.register_formula_policy(&read_scope(self.source), &record)?;
        // The server may already have committed: any reply mismatch is an unknown outcome.
        if committed != version {
            return Err(FormulaPolicyRegistrationError::OutcomeUnknown);
        }
        Ok(RegisteredFormulaPolicyReceipt {
            profile: "hwpx-agent.registered-source-formula-policy/partial-v1",
            version: self.binding.policy_version,
            generation: self.binding.policy_generation,
            artifact: version.artifact,
            digest: version.digest,
            field_meaning_graph_sha256: self.targets.0,
            target_bindings_sha256: self.targets.1,
            formula_targets: self.target_count,
            qualification: "source_derived_generated_payload_actual_aead_metadata_registration_NOT_trusted_issuer_actual_SQL_atomic_execution_native_or_Gate",
        })
    }
    fn verify_payload<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bytes: &[u8],
        now: u64,
    ) -> Result<(), FormulaPolicyRegistrationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.source
            .fresh_source(provider, now)
            .map_err(|_| FormulaPolicyRegistrationError::Source)?;
        let payload = wire::decode(bytes, &self.binding)
            .map_err(|_| FormulaPolicyRegistrationError::Payload)?;
        if payload.targets.len() != self.target_count
            || targets::bind(self.source, provider, &payload, now)
                .map_err(|_| FormulaPolicyRegistrationError::Policy)?
                != self.targets
        {
            return Err(FormulaPolicyRegistrationError::Policy);
        }
        self.source
            .fresh_source(provider, now)
            .map_err(|_| FormulaPolicyRegistrationError::Source)?;
        Ok(())
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormulaPolicyRegistrationError {
    #[error("formula_policy_registration_scope_denied")]
    Scope,
    #[error("formula_policy_registration_source_denied")]
    Source,
    #[error("formula_policy_registration_binding_invalid")]
    Binding,
    #[error("formula_policy_registration_complete_target_decisions_invalid")]
    Policy,
    #[error("formula_policy_registration_generated_payload_invalid")]
    Payload,
    #[error("formula_policy_registration_original_artifact_denied")]
    Artifact,
    #[error("formula_policy_registration_repository_denied")]
    Repository,
    #[error("formula_policy_registration_outcome_unknown_do_not_retry_blindly")]
    OutcomeUnknown,
}
