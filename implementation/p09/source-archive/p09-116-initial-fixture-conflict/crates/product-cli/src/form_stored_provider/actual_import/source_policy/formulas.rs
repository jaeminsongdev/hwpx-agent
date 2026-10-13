//! Separate source-field policy DATA domain; not form-control policy, issuer or execution authority.
mod targets;
mod wire;
use super::{
    PolicyReadScope, SourcePolicyVersion, StoredImportedDocumentForms, read_scope, validate_version,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
pub const FORMULA_POLICY_MEDIA_TYPE: &str =
    "application/vnd.hwpx-agent.source-table-formula-policy+json";
pub const FORMULA_POLICY_SCHEMA: &str = "hwpx-agent.source-table-formula-policy/v1";
/// Separate repository domain: an existing form policy must NOT become a field grant.
/// Every call must authorize current membership/latest/revocation and both source/policy access.
pub trait FormulaPolicyRepository: Send + Sync {
    /// # Errors
    /// Closed failure for missing/unauthorized/revoked/stale/unavailable field-policy data.
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError>;
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFormulaPolicyReceipt {
    pub profile: &'static str,
    pub source_package_sha256: ContentDigest,
    pub field_meaning_graph_sha256: ContentDigest,
    pub policy_raw_sha256: ContentDigest,
    pub target_bindings_sha256: ContentDigest,
    pub policy_generation: u64,
    pub formula_targets: usize,
    pub allowed_targets: usize,
    pub qualification: &'static str,
}
/// Owned private validated bytes/version, not a caller map or a deserializable grant.
pub struct StoredFormulaPolicy {
    version: SourcePolicyVersion,
    bytes: Vec<u8>,
    receipt: StoredFormulaPolicyReceipt,
}
impl fmt::Debug for StoredFormulaPolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredFormulaPolicy(<redacted>)")
    }
}
impl StoredImportedDocumentForms {
    /// Selects a field-specific repository policy through original service access/source checks.
    /// # Errors
    /// Rejects latest/revocation/binding/media/AEAD/payload/actual-target mismatch.
    pub fn bind_stored_formula_policy<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<StoredFormulaPolicy, StoredFormulaPolicyError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        self.fresh_source(provider, now)
            .map_err(|_| StoredFormulaPolicyError::Source)?;
        let scope = read_scope(self);
        let version = repository.read_current_formula_policy(&scope)?;
        validate_version(self, &version).map_err(|_| StoredFormulaPolicyError::Binding)?;
        let bytes = wire::read_artifact(provider, &version, now)?;
        let payload = wire::decode(&bytes, &version.binding)?;
        let (graph, bindings, allowed) = targets::bind(self, provider, &payload, now)?;
        if repository.read_current_formula_policy(&scope)? != version {
            return Err(StoredFormulaPolicyError::Drift);
        }
        self.fresh_source(provider, now)
            .map_err(|_| StoredFormulaPolicyError::Source)?;
        let receipt = StoredFormulaPolicyReceipt {
            profile: FORMULA_POLICY_SCHEMA,
            source_package_sha256: version.binding.source_package_sha256,
            field_meaning_graph_sha256: graph,
            policy_raw_sha256: version.digest,
            target_bindings_sha256: bindings,
            policy_generation: version.binding.policy_generation,
            formula_targets: payload.targets.len(),
            allowed_targets: allowed,
            qualification: "repository_selected_authenticated_actual_field_formula_policy_data_NOT_trusted_issuer_full_field_policy_SQL_atomic_lease_execution_native_or_Gate",
        };
        Ok(StoredFormulaPolicy {
            version,
            bytes,
            receipt,
        })
    }
}
impl StoredFormulaPolicy {
    #[must_use]
    pub const fn receipt(&self) -> &StoredFormulaPolicyReceipt {
        &self.receipt
    }
    /// Data permission only; source mutation protection remains an independent mandatory guard.
    /// # Errors
    /// Rejects any denied actual target, including targets whose cached results are current.
    pub fn require_recalculation_data_permission(&self) -> Result<(), StoredFormulaPolicyError> {
        if self.receipt.formula_targets == 0
            || self.receipt.allowed_targets != self.receipt.formula_targets
        {
            return Err(StoredFormulaPolicyError::Denied);
        }
        Ok(())
    }
    /// Freshly reselects/re-authorizes/decodes/rebinds the complete original policy and source.
    /// # Errors
    /// Rejects latest/ACL/AEAD/head/scope/version/raw bytes/whole receipt drift; no fallback.
    pub fn verify<R, B, S, V, P>(
        &self,
        source: &StoredImportedDocumentForms,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<StoredFormulaPolicyReceipt, StoredFormulaPolicyError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        let fresh = source.bind_stored_formula_policy(provider, repository, now)?;
        if self.version != fresh.version
            || self.bytes != fresh.bytes
            || self.receipt != fresh.receipt
        {
            return Err(StoredFormulaPolicyError::Drift);
        }
        Ok(fresh.receipt)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFormulaPolicyError {
    #[error("formula_policy_repository_denied")]
    Repository,
    #[error("formula_policy_actual_source_denied")]
    Source,
    #[error("formula_policy_version_binding_rejected")]
    Binding,
    #[error("formula_policy_original_artifact_access_rejected")]
    Artifact,
    #[error("formula_policy_strict_payload_rejected")]
    Payload,
    #[error("formula_policy_actual_target_rejected")]
    Target,
    #[error("formula_policy_recalculation_data_denied")]
    Denied,
    #[error("formula_policy_fresh_state_changed")]
    Drift,
}
