use super::super::{FormulaPolicyRepository, StoredFormulaPolicyError};
use super::{
    AUDIENCE, FormulaApprovalRepository, FormulaIssuerClock, FormulaIssuerError as Error,
    FormulaIssuerReceipt, FormulaIssuerTrust, FormulaIssuerTrustRepository, MAX_APPROVAL_BYTES,
    OPERATION, PolicyReadScope, SourcePolicyVersion, wire,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
    StorageState, ValidationState,
};
use revision_service::RevisionRepository;
use ring::signature::{ED25519, UnparsedPublicKey};
use std::{fmt, sync::Mutex};

pub(super) struct SignedRepository<'a, 'p, R, B, S, V, P, A, T, C> {
    pub provider: &'a StoredFormProvider<'p, R, B, S, V>,
    pub policies: &'a P,
    pub approvals: &'a A,
    pub trust: &'a T,
    pub clock: &'a C,
    observed: Mutex<Option<FormulaIssuerReceipt>>,
}
impl<R, B, S, V, P, A, T, C> fmt::Debug for SignedRepository<'_, '_, R, B, S, V, P, A, T, C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SignedFormulaPolicyRepository(<redacted>)")
    }
}
impl<'a, 'p, R, B, S, V, P, A, T, C> SignedRepository<'a, 'p, R, B, S, V, P, A, T, C> {
    pub fn new(
        provider: &'a StoredFormProvider<'p, R, B, S, V>,
        deps: &super::product::FormulaIssuerDependencies<'a, P, A, T, C>,
    ) -> Self {
        Self {
            provider,
            policies: deps.policies,
            approvals: deps.approvals,
            trust: deps.trust,
            clock: deps.clock,
            observed: Mutex::new(None),
        }
    }
    pub fn receipt(&self) -> Result<FormulaIssuerReceipt, Error> {
        self.observed
            .lock()
            .map_err(|_| Error::Repository)?
            .clone()
            .ok_or(Error::Repository)
    }
}
impl<R, B, S, V, P, A, T, C> SignedRepository<'_, '_, R, B, S, V, P, A, T, C>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
    P: FormulaPolicyRepository,
    A: FormulaApprovalRepository,
    T: FormulaIssuerTrustRepository,
    C: FormulaIssuerClock,
{
    fn read_signed(&self, scope: &PolicyReadScope) -> Result<SourcePolicyVersion, Error> {
        let ps = &self.provider.scope;
        if ps.tenant != scope.tenant()
            || ps.subject != scope.subject()
            || ps.project != scope.project()
            || ps.branch != scope.branch()
            || &ps.document != scope.document()
        {
            return Err(Error::Binding);
        }
        let before = self.clock.now()?;
        let policy = self
            .policies
            .read_current_formula_policy(scope)
            .map_err(|_| Error::Repository)?;
        let proof = self.approvals.read_current_approval(scope, &policy)?;
        if proof.artifact == policy.artifact
            || proof.artifact == policy.binding.source_result_artifact
        {
            return Err(Error::Artifact);
        }
        let trust = self.trust.read_formula_issuer_trust(scope)?;
        let d = self
            .provider
            .artifacts
            .get_descriptor(self.provider.artifact_context, proof.artifact, before)
            .map_err(|_| Error::Artifact)?;
        if d.artifact_id != proof.artifact
            || d.sha256 != proof.digest
            || d.kind != ArtifactKind::Evidence
            || d.media_type.as_str() != super::FORMULA_APPROVAL_MEDIA_TYPE
            || d.storage_state != StorageState::Available
            || d.validation_state != ValidationState::Verified
            || d.quarantine_reason.is_some()
            || d.size_bytes == 0
            || d.size_bytes > MAX_APPROVAL_BYTES as u64
        {
            return Err(Error::Artifact);
        }
        let raw = self
            .provider
            .artifacts
            .download(self.provider.artifact_context, proof.artifact, before)
            .map_err(|_| Error::Artifact)?;
        if raw.len() as u64 != d.size_bytes
            || raw.is_empty()
            || raw.len() > MAX_APPROVAL_BYTES
            || ContentDigest::of(&raw) != proof.digest
        {
            return Err(Error::Artifact);
        }
        let (claims, signing, signature) = wire::decode(&raw)?;
        validate_claims(scope, &policy, &trust, &claims, before)?;
        let key = trust.keys.get(&claims.key_id).ok_or(Error::Trust)?;
        UnparsedPublicKey::new(&ED25519, key)
            .verify(&signing, &signature)
            .map_err(|_| Error::Signature)?;
        // Re-authorize all live selectors after actual signature work; no old proof/key fallback.
        if self.approvals.read_current_approval(scope, &policy)? != proof
            || self.trust.read_formula_issuer_trust(scope)? != trust
            || self
                .policies
                .read_current_formula_policy(scope)
                .map_err(|_| Error::Repository)?
                != policy
        {
            return Err(Error::Drift);
        }
        let after = self.clock.now()?;
        if after < before {
            return Err(Error::Clock);
        }
        validate_claims(scope, &policy, &trust, &claims, after)?;
        // Bind the entire server trust snapshot, including active keys/lifetime, not just a counter.
        let snapshot = ContentDigest::of(
            &serde_json::to_vec(&(
                trust.tenant,
                trust.project,
                &trust.issuer,
                trust.generation,
                trust.valid_from,
                trust.valid_until,
                trust.max_approval_lifetime,
                &trust.keys,
            ))
            .map_err(|_| Error::Trust)?,
        );
        let receipt = FormulaIssuerReceipt {
            profile: "hwpx-agent.verified-formula-approval/component-v1",
            approval_sha256: proof.digest,
            policy_sha256: policy.digest,
            trust_snapshot_sha256: snapshot,
            trust_generation: trust.generation,
            policy_generation: policy.binding.policy_generation,
            qualification: "live_server_selected_ed25519_exact_formula_policy_DATA_signature_component_NOT_configured_production_issuer_signed_root_SQL_atomic_execution_native_or_Gate",
        };
        let mut observed = self.observed.lock().map_err(|_| Error::Repository)?;
        if observed.as_ref().is_some_and(|old| old != &receipt) {
            return Err(Error::Drift);
        }
        *observed = Some(receipt);
        Ok(policy)
    }
}
pub(super) fn validate_claims(
    scope: &PolicyReadScope,
    policy: &SourcePolicyVersion,
    trust: &FormulaIssuerTrust,
    claims: &wire::Claims,
    now: u64,
) -> Result<(), Error> {
    if trust.tenant != scope.tenant()
        || trust.project != scope.project()
        || trust.issuer != claims.issuer
        || trust.generation != claims.trust_generation
        || !super::identifier(&claims.key_id)
    {
        return Err(Error::Trust);
    }
    let b = &policy.binding;
    if claims.binding != *b
        || claims.policy_artifact != policy.artifact
        || claims.policy_digest != policy.digest
        || claims.audience != AUDIENCE
        || claims.operation != OPERATION
        || b.tenant != scope.tenant()
        || b.project != scope.project()
        || b.branch != scope.branch()
        || &b.document != scope.document()
        || Some(b.source_revision) != scope.head().revision_id()
        || b.source_head_generation != scope.head().generation()
        || b.policy_version.is_nil()
        || b.policy_generation == 0
        || b.policy_generation > i64::MAX as u64
    {
        return Err(Error::Binding);
    }
    if now < trust.valid_from
        || now >= trust.valid_until
        || claims.issued_at < trust.valid_from
        || claims.issued_at > claims.not_before
        || claims.not_before > now
        || claims.issued_at > now
        || claims.expires_at <= claims.not_before
        || now >= claims.expires_at
        || claims.expires_at > trust.valid_until
        || claims.expires_at.saturating_sub(claims.issued_at) > trust.max_approval_lifetime
    {
        return Err(Error::Time);
    }
    Ok(())
}
impl<R, B, S, V, P, A, T, C> FormulaPolicyRepository
    for SignedRepository<'_, '_, R, B, S, V, P, A, T, C>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
    P: FormulaPolicyRepository,
    A: FormulaApprovalRepository,
    T: FormulaIssuerTrustRepository,
    C: FormulaIssuerClock,
{
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        self.read_signed(scope)
            .map_err(|_| StoredFormulaPolicyError::Repository)
    }
}
