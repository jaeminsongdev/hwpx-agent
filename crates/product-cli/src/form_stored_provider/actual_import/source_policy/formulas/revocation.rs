//! Exact validated formula DATA revocation; not a public approval or source mutation endpoint.
pub mod postgres;
use super::super::read_scope;
use super::{
    FormulaPolicyRepository, PolicyReadScope, SourcePolicyVersion, StoredFormulaPolicy,
    StoredImportedDocumentForms,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, AuthScope, ContentDigest, EncryptedBlobStore,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
use uuid::Uuid;

/// Only an authenticated, freshly verified stored policy constructs this write record.
pub struct FormulaPolicyRevocationRecord {
    version: SourcePolicyVersion,
}
impl FormulaPolicyRevocationRecord {
    #[must_use]
    pub const fn version(&self) -> &SourcePolicyVersion {
        &self.version
    }
}
impl fmt::Debug for FormulaPolicyRevocationRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaPolicyRevocationRecord(<redacted>)")
    }
}
/// Trusted server implementation must authorize the current writer independently of policy creator.
pub trait FormulaPolicyRevocationRepository: Send + Sync {
    /// # Errors
    /// Denies scope/role/latest version/CAS failures; lost commit acknowledgement stays unknown.
    fn revoke_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRevocationRecord,
    ) -> Result<SourcePolicyVersion, FormulaPolicyRevocationError>;
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct RevokedFormulaPolicyReceipt {
    pub profile: &'static str,
    pub version: Uuid,
    pub generation: u64,
    pub policy_sha256: ContentDigest,
    pub qualification: &'static str,
}
impl fmt::Debug for RevokedFormulaPolicyReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RevokedFormulaPolicyReceipt(<redacted>)")
    }
}
impl StoredFormulaPolicy {
    /// Rechecks write scope and all original current policy/source/ACL/AEAD/target checks, then
    /// revokes the exact server-selected version once. Artifacts and original source remain intact.
    /// # Errors
    /// Denies stale/read-only calls before the write. Inexact successful replies are outcome unknown.
    /// Fresh preflight is not an atomic source lease; actual SQL/native/issuer acceptance is separate.
    pub fn revoke<R, B, S, V, P>(
        &self,
        source: &StoredImportedDocumentForms,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<RevokedFormulaPolicyReceipt, FormulaPolicyRevocationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository + FormulaPolicyRevocationRepository,
    {
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(FormulaPolicyRevocationError::Scope);
        }
        self.verify(source, provider, repository, now)
            .map_err(|_| FormulaPolicyRevocationError::Policy)?;
        let record = FormulaPolicyRevocationRecord {
            version: self.version.clone(),
        };
        let committed = repository.revoke_formula_policy(&read_scope(source), &record)?;
        if committed != self.version {
            return Err(FormulaPolicyRevocationError::OutcomeUnknown);
        }
        // Do not turn a post-commit read failure into a retryable write: the policy is now revoked.
        Ok(RevokedFormulaPolicyReceipt {
            profile: "hwpx-agent.source-formula-policy-revocation/component-v1",
            version: self.version.binding.policy_version,
            generation: self.version.binding.policy_generation,
            policy_sha256: self.version.digest,
            qualification: "exact_current_formula_policy_DATA_revocation_component_NOT_actual_SQL_production_issuer_atomic_source_lease_native_or_Gate",
        })
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormulaPolicyRevocationError {
    #[error("formula_policy_revocation_write_scope_denied")]
    Scope,
    #[error("formula_policy_revocation_fresh_policy_denied")]
    Policy,
    #[error("formula_policy_revocation_binding_invalid")]
    Binding,
    #[error("formula_policy_revocation_repository_denied")]
    Repository,
    #[error("formula_policy_revocation_outcome_unknown_do_not_retry_blindly")]
    OutcomeUnknown,
}
