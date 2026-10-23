//! SQL22 registry adapters to the unchanged live Ed25519 consumer; no runtime configuration/default keys.
mod trust_wire;
pub mod provision;
use super::{
    FormulaApprovalRepository, FormulaApprovalVersion, FormulaIssuerClock,
    FormulaIssuerError as Error, FormulaIssuerTrust, FormulaIssuerTrustRepository, PolicyReadScope,
    SourcePolicyVersion,
};
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ArtifactService, AuthScope,
    ContentDigest, EncryptedBlobStore, RequestContext, StorageState, ValidationState,
};
use revision_service::{
    RevisionRequestContext,
    postgres::source_formula_policy::{
        SourceFormulaPolicyReadRequest,
        issuer_registry::{
            FormulaApprovalReadRequest, FormulaIssuerRegistryRepository, FormulaIssuerTrustRecord,
        },
    },
};
use std::fmt;

pub const FORMULA_ISSUER_TRUST_MEDIA_TYPE: &str =
    "application/vnd.hwpx-agent.source-formula-issuer-trust+json";
pub const FORMULA_ISSUER_TRUST_SCHEMA: &str = "hwpx-agent.source-formula-issuer-trust/v1";
const MAX_TRUST_BYTES: usize = 32768;

/// Uses only repository-selected approval/root identities, never an artifact selector in product JSON.
pub struct RegistryFormulaApprovalProvider<'a, G> {
    registry: &'a G,
}
impl<'a, G> RegistryFormulaApprovalProvider<'a, G> {
    #[must_use]
    pub const fn new(registry: &'a G) -> Self {
        Self { registry }
    }
}
impl<G> fmt::Debug for RegistryFormulaApprovalProvider<'_, G> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RegistryFormulaApprovalProvider(<redacted>)")
    }
}
impl<G: FormulaIssuerRegistryRepository> FormulaApprovalRepository
    for RegistryFormulaApprovalProvider<'_, G>
{
    fn read_current_approval(
        &self,
        scope: &PolicyReadScope,
        policy: &SourcePolicyVersion,
    ) -> Result<FormulaApprovalVersion, Error> {
        let binding = &policy.binding;
        if binding.tenant != scope.tenant()
            || binding.project != scope.project()
            || binding.branch != scope.branch()
            || &binding.document != scope.document()
            || Some(binding.source_revision) != scope.head().revision_id()
            || binding.source_head_generation != scope.head().generation()
            || policy.artifact == binding.source_result_artifact
        {
            return Err(Error::Binding);
        }
        let ctx = RevisionRequestContext::new(scope.tenant(), scope.subject());
        let req = FormulaApprovalReadRequest::new(
            SourceFormulaPolicyReadRequest::new(
                scope.project(),
                scope.branch(),
                scope.document().as_str().to_owned(),
                scope.head(),
            )
            .map_err(|_| Error::Binding)?,
            binding.policy_version,
            binding.policy_generation,
        )
        .map_err(|_| Error::Binding)?;
        let root = self
            .registry
            .read_trust(&ctx, scope.project())
            .map_err(|_| Error::Repository)?;
        root.validate_for(&ctx, scope.project())
            .map_err(|_| Error::Binding)?;
        let row = self
            .registry
            .read_approval(&ctx, &req)
            .map_err(|_| Error::Repository)?;
        row.validate_for(&ctx, &req).map_err(|_| Error::Binding)?;
        if row.trust_version != root.version
            || row.trust_generation != root.generation
            || [
                policy.artifact,
                binding.source_result_artifact,
                root.artifact,
            ]
            .contains(&row.artifact)
            || [policy.artifact, binding.source_result_artifact].contains(&root.artifact)
        {
            return Err(Error::Binding);
        }
        if self
            .registry
            .read_trust(&ctx, scope.project())
            .map_err(|_| Error::Repository)?
            != root
        {
            return Err(Error::Drift);
        }
        Ok(FormulaApprovalVersion {
            artifact: row.artifact,
            digest: row.digest,
        })
    }
}

/// Explicit owner-provisioned trust DATA from the admitted registry, decrypted by original `ArtifactService`.
/// This is not private-key custody, a root signature verifier or a production issuer installation.
pub struct RegistryFormulaTrustProvider<'a, G, R, B, S, C> {
    registry: &'a G,
    artifacts: &'a ArtifactService<R, B, S>,
    context: &'a RequestContext,
    clock: &'a C,
}
impl<'a, G, R, B, S, C> RegistryFormulaTrustProvider<'a, G, R, B, S, C> {
    #[must_use]
    pub const fn new(
        registry: &'a G,
        artifacts: &'a ArtifactService<R, B, S>,
        context: &'a RequestContext,
        clock: &'a C,
    ) -> Self {
        Self {
            registry,
            artifacts,
            context,
            clock,
        }
    }
}
impl<G, R, B, S, C> fmt::Debug for RegistryFormulaTrustProvider<'_, G, R, B, S, C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RegistryFormulaTrustProvider(<redacted>)")
    }
}
impl<G, R, B, S, C> FormulaIssuerTrustRepository for RegistryFormulaTrustProvider<'_, G, R, B, S, C>
where
    G: FormulaIssuerRegistryRepository,
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    C: FormulaIssuerClock,
{
    fn read_formula_issuer_trust(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<FormulaIssuerTrust, Error> {
        if self.context.tenant_id() != scope.tenant()
            || self.context.subject() != scope.subject()
            || !self.context.has_scope(AuthScope::DocumentRead)
        {
            return Err(Error::Binding);
        }
        let ctx = RevisionRequestContext::new(scope.tenant(), scope.subject());
        let row = self
            .registry
            .read_trust(&ctx, scope.project())
            .map_err(|_| Error::Repository)?;
        row.validate_for(&ctx, scope.project())
            .map_err(|_| Error::Binding)?;
        let before = self.clock.now()?;
        live(&row, before)?;
        let d = self
            .artifacts
            .get_descriptor(self.context, row.artifact, before)
            .map_err(|_| Error::Artifact)?;
        if d.artifact_id != row.artifact
            || d.sha256 != row.digest
            || d.kind != ArtifactKind::Evidence
            || d.media_type.as_str() != FORMULA_ISSUER_TRUST_MEDIA_TYPE
            || d.storage_state != StorageState::Available
            || d.validation_state != ValidationState::Verified
            || d.quarantine_reason.is_some()
            || d.size_bytes == 0
            || d.size_bytes > MAX_TRUST_BYTES as u64
        {
            return Err(Error::Artifact);
        }
        let raw = self
            .artifacts
            .download(self.context, row.artifact, before)
            .map_err(|_| Error::Artifact)?;
        if raw.len() as u64 != d.size_bytes || ContentDigest::of(&raw) != row.digest {
            return Err(Error::Artifact);
        }
        let trust = trust_wire::decode(&raw, &row)?;
        if self
            .registry
            .read_trust(&ctx, scope.project())
            .map_err(|_| Error::Repository)?
            != row
        {
            return Err(Error::Drift);
        }
        let after = self.clock.now()?;
        if after < before {
            return Err(Error::Clock);
        }
        live(&row, after)?;
        Ok(trust)
    }
}
fn live(row: &FormulaIssuerTrustRecord, now: u64) -> Result<(), Error> {
    if now < row.valid_from || now >= row.valid_until {
        return Err(Error::Time);
    }
    Ok(())
}
