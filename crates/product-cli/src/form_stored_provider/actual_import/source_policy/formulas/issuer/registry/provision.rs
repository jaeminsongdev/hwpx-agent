//! Trusted server issuer workflow. No endpoint, default key, private-key installation or publication.
use super::super::super::super::{PolicyReadScope, SourcePolicyVersion};
use super::super::super::{FormulaPolicyRepository, registration::FormulaPolicyRegistrationRecord};
use super::super::{
    FORMULA_APPROVAL_MEDIA_TYPE, FormulaApprovalIdentity, FormulaIssuerClock, FormulaIssuerError,
    FormulaIssuerTrust, FormulaIssuerTrustDraft, MAX_APPROVAL_BYTES, PreparedFormulaApproval,
    provider, wire,
};
use super::{
    FORMULA_ISSUER_TRUST_MEDIA_TYPE, FORMULA_ISSUER_TRUST_SCHEMA, MAX_TRUST_BYTES, live, trust_wire,
};
use artifact_service::{
    ArtifactDescriptor, ArtifactId, ArtifactKind, ArtifactMetadataRepository, ArtifactScanner,
    ArtifactService, AuthScope, ContentDigest, EncryptedBlobStore, FileName, IngestRequest,
    MediaType, RequestContext, StorageState, ValidationState,
};
use revision_service::{
    ProjectId, RevisionError, RevisionRequestContext,
    postgres::source_formula_policy::{
        SourceFormulaPolicyReadRequest,
        issuer_registry::{
            FormulaApprovalReadRequest, FormulaApprovalRecord, FormulaIssuerRegistryRepository,
            FormulaIssuerTrustRecord,
            management::{
                FormulaApprovalRegistration, FormulaIssuerTrustRegistration,
                FormulaRegistryManagementAction, FormulaRegistryManagementReceipt,
                LocalPostgresFormulaRegistryManagementRepository, RegistryManagementCapability,
            },
        },
    },
};
use ring::signature::{ED25519, UnparsedPublicKey};
use std::fmt;
use uuid::Uuid;

/// Explicit server custody dependency. Do not expose keys/signing bytes via JSON, logs or fallback config.
pub trait FormulaApprovalSigner: Send + Sync {
    fn key_id(&self) -> &str;
    /// # Errors
    /// Denies unavailable/revoked custody or signing failures. The workflow verifies the signature.
    fn sign(&self, domain_separated_claims: &[u8]) -> Result<[u8; 64], FormulaIssuerError>;
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RegistryGatewayError {
    Denied,
    CommitOutcomeUnknown,
    AcknowledgedReceiptMismatch,
}

/// Trusted persistence gateway. Selecting this dependency is not public authorization.
pub trait FormulaIssuerRegistryWriteGateway: Send + Sync {
    /// # Errors
    /// Denies non-owner project role before root artifact creation. Not a lease; writes recheck authority.
    fn authorize_root(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<(), FormulaIssuerError>;
    /// # Errors
    /// Denies non-owner/editor project role before invoking custody. No always-allow default.
    fn authorize_approval(
        &self,
        context: &RevisionRequestContext,
        scope: &PolicyReadScope,
    ) -> Result<(), FormulaIssuerError>;
    /// # Errors
    /// Requires fixed tenant/subject, real owner/CAS/artifact manage checks; no retry on ambiguity.
    fn register_trust(
        &self,
        context: &RevisionRequestContext,
        record: &FormulaIssuerTrustRecord,
        expected_generation: u64,
    ) -> Result<(), RegistryGatewayError>;
    /// # Errors
    /// Requires current policy/head/root, editor/owner, alias and artifact-manage checks.
    fn register_approval(
        &self,
        context: &RevisionRequestContext,
        scope: &PolicyReadScope,
        record: &FormulaApprovalRecord,
        expected_generation: u64,
    ) -> Result<(), RegistryGatewayError>;
}
pub struct PostgresFormulaIssuerWriteGateway<'a> {
    roots: &'a LocalPostgresFormulaRegistryManagementRepository,
    approvals: &'a LocalPostgresFormulaRegistryManagementRepository,
}
impl<'a> PostgresFormulaIssuerWriteGateway<'a> {
    #[must_use]
    pub const fn new(
        roots: &'a LocalPostgresFormulaRegistryManagementRepository,
        approvals: &'a LocalPostgresFormulaRegistryManagementRepository,
    ) -> Self {
        Self { roots, approvals }
    }
}
fn write_error(error: &RevisionError) -> RegistryGatewayError {
    if error == &RevisionError::CommitOutcomeUnknown {
        RegistryGatewayError::CommitOutcomeUnknown
    } else {
        RegistryGatewayError::Denied
    }
}
fn check_ack(
    ack: &FormulaRegistryManagementReceipt,
    context: &RevisionRequestContext,
    project: ProjectId,
    version: Uuid,
    generation: u64,
    action: FormulaRegistryManagementAction,
) -> Result<(), RegistryGatewayError> {
    if ack.tenant() != context.tenant_id()
        || ack.actor() != context.subject()
        || ack.project() != project
        || ack.version() != version
        || ack.generation() != generation
        || ack.action() != action
    {
        return Err(RegistryGatewayError::AcknowledgedReceiptMismatch);
    }
    Ok(())
}
impl FormulaIssuerRegistryWriteGateway for PostgresFormulaIssuerWriteGateway<'_> {
    fn authorize_root(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<(), FormulaIssuerError> {
        self.roots
            .check_project_role(context, project, RegistryManagementCapability::Trust)
            .map_err(|_| FormulaIssuerError::Repository)
    }
    fn authorize_approval(
        &self,
        context: &RevisionRequestContext,
        scope: &PolicyReadScope,
    ) -> Result<(), FormulaIssuerError> {
        if scope.tenant() != context.tenant_id() || scope.subject() != context.subject() {
            return Err(FormulaIssuerError::Binding);
        }
        self.approvals
            .check_project_role(
                context,
                scope.project(),
                RegistryManagementCapability::Approval,
            )
            .map_err(|_| FormulaIssuerError::Repository)
    }
    fn register_trust(
        &self,
        context: &RevisionRequestContext,
        record: &FormulaIssuerTrustRecord,
        expected_generation: u64,
    ) -> Result<(), RegistryGatewayError> {
        let req = FormulaIssuerTrustRegistration::new(record.clone(), expected_generation)
            .map_err(|e| write_error(&e))?;
        let ack = self
            .roots
            .register_trust(context, &req)
            .map_err(|e| write_error(&e))?;
        check_ack(
            &ack,
            context,
            record.project,
            record.version,
            record.generation,
            FormulaRegistryManagementAction::RegisterTrust,
        )
    }
    fn register_approval(
        &self,
        context: &RevisionRequestContext,
        scope: &PolicyReadScope,
        record: &FormulaApprovalRecord,
        expected_generation: u64,
    ) -> Result<(), RegistryGatewayError> {
        let req = approval_request(scope, record.policy_version, record.policy_generation)
            .map_err(|_| RegistryGatewayError::Denied)?;
        let req = FormulaApprovalRegistration::new(req, record.clone(), expected_generation)
            .map_err(|e| write_error(&e))?;
        let ack = self
            .approvals
            .register_approval(context, &req)
            .map_err(|e| write_error(&e))?;
        check_ack(
            &ack,
            context,
            record.project,
            record.version,
            record.generation,
            FormulaRegistryManagementAction::RegisterApproval,
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FormulaIssuerWorkflowStage {
    Preflight,
    ArtifactIngest,
    ArtifactReadback,
    RegistryWrite,
    RegistryReadback,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FormulaIssuerWriteOutcome {
    NotAttempted,
    Denied,
    CommitOutcomeUnknown,
    Acknowledged,
}
#[derive(Debug, Eq, PartialEq, thiserror::Error)]
pub enum FormulaIssuerWorkflowError {
    #[error("formula_issuer_workflow_binding_denied")]
    Binding,
    #[error("formula_issuer_workflow_artifact_denied")]
    Artifact,
    #[error("formula_issuer_workflow_registry_denied")]
    Registry,
    #[error("formula_issuer_workflow_commit_outcome_unknown")]
    CommitOutcomeUnknown,
    #[error("formula_issuer_workflow_live_state_changed")]
    Drift,
    #[error("formula_issuer_workflow_signature_or_clock_denied")]
    Issuer(FormulaIssuerError),
}
/// Evidence survives failure. An ingest error may have partial side effects even without an ID.
/// Acknowledged writes with failed readback must NOT be silently rolled back, retried or called unregistered.
pub struct FormulaIssuerWorkflowFailure {
    cause: FormulaIssuerWorkflowError,
    stage: FormulaIssuerWorkflowStage,
    artifact: Option<ArtifactId>,
    outcome: FormulaIssuerWriteOutcome,
}
impl FormulaIssuerWorkflowFailure {
    #[must_use]
    pub const fn cause(&self) -> &FormulaIssuerWorkflowError {
        &self.cause
    }
    #[must_use]
    pub const fn stage(&self) -> FormulaIssuerWorkflowStage {
        self.stage
    }
    #[must_use]
    pub const fn artifact(&self) -> Option<ArtifactId> {
        self.artifact
    }
    #[must_use]
    pub const fn write_outcome(&self) -> FormulaIssuerWriteOutcome {
        self.outcome
    }
}
impl fmt::Display for FormulaIssuerWorkflowFailure {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.cause, f)
    }
}
impl std::error::Error for FormulaIssuerWorkflowFailure {}

/// Artifact and current registry readback receipt. Not a private-key custody or publication qualification.
pub struct FormulaIssuerProvisioningReceipt {
    action: FormulaRegistryManagementAction,
    version: Uuid,
    generation: u64,
    artifact: ArtifactId,
    digest: ContentDigest,
}
impl FormulaIssuerProvisioningReceipt {
    #[must_use]
    pub const fn action(&self) -> FormulaRegistryManagementAction {
        self.action
    }
    #[must_use]
    pub const fn version(&self) -> Uuid {
        self.version
    }
    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }
    #[must_use]
    pub const fn artifact(&self) -> ArtifactId {
        self.artifact
    }
    #[must_use]
    pub const fn digest(&self) -> ContentDigest {
        self.digest
    }
    #[must_use]
    pub const fn qualification(&self) -> &'static str {
        "issuer_AEAD_artifact_named_registry_write_live_readback_component_NOT_production_key_custody_actual_SQL_atomic_publication_native_or_Gate"
    }
}

struct PreparedRegistryApproval {
    policy: SourcePolicyVersion,
    root: FormulaIssuerTrustRecord,
    trust: FormulaIssuerTrust,
    before: u64,
    claims: wire::Claims,
    raw: Vec<u8>,
}

pub struct RegistryFormulaProvisioner<'a, G, W, P, R, B, S, C> {
    registry: &'a G,
    writes: &'a W,
    policies: &'a P,
    artifacts: &'a ArtifactService<R, B, S>,
    context: &'a RequestContext,
    clock: &'a C,
}
impl<'a, G, W, P, R, B, S, C> RegistryFormulaProvisioner<'a, G, W, P, R, B, S, C> {
    #[must_use]
    pub const fn new(
        registry: &'a G,
        writes: &'a W,
        policies: &'a P,
        artifacts: &'a ArtifactService<R, B, S>,
        context: &'a RequestContext,
        clock: &'a C,
    ) -> Self {
        Self {
            registry,
            writes,
            policies,
            artifacts,
            context,
            clock,
        }
    }
}
fn failure(
    cause: FormulaIssuerWorkflowError,
    stage: FormulaIssuerWorkflowStage,
    artifact: Option<ArtifactId>,
    outcome: FormulaIssuerWriteOutcome,
) -> FormulaIssuerWorkflowFailure {
    FormulaIssuerWorkflowFailure {
        cause,
        stage,
        artifact,
        outcome,
    }
}
fn preflight(cause: FormulaIssuerWorkflowError) -> FormulaIssuerWorkflowFailure {
    failure(
        cause,
        FormulaIssuerWorkflowStage::Preflight,
        None,
        FormulaIssuerWriteOutcome::NotAttempted,
    )
}
fn failed_write(error: RegistryGatewayError, artifact: ArtifactId) -> FormulaIssuerWorkflowFailure {
    let (cause, outcome) = match error {
        RegistryGatewayError::Denied => (
            FormulaIssuerWorkflowError::Registry,
            FormulaIssuerWriteOutcome::Denied,
        ),
        RegistryGatewayError::CommitOutcomeUnknown => (
            FormulaIssuerWorkflowError::CommitOutcomeUnknown,
            FormulaIssuerWriteOutcome::CommitOutcomeUnknown,
        ),
        RegistryGatewayError::AcknowledgedReceiptMismatch => (
            FormulaIssuerWorkflowError::Drift,
            FormulaIssuerWriteOutcome::Acknowledged,
        ),
    };
    failure(
        cause,
        FormulaIssuerWorkflowStage::RegistryWrite,
        Some(artifact),
        outcome,
    )
}
fn approval_request(
    scope: &PolicyReadScope,
    version: Uuid,
    generation: u64,
) -> Result<FormulaApprovalReadRequest, FormulaIssuerWorkflowError> {
    FormulaApprovalReadRequest::new(
        SourceFormulaPolicyReadRequest::new(
            scope.project(),
            scope.branch(),
            scope.document().as_str().into(),
            scope.head(),
        )
        .map_err(|_| FormulaIssuerWorkflowError::Binding)?,
        version,
        generation,
    )
    .map_err(|_| FormulaIssuerWorkflowError::Binding)
}
impl<G, W, P, R, B, S, C> RegistryFormulaProvisioner<'_, G, W, P, R, B, S, C>
where
    G: FormulaIssuerRegistryRepository,
    W: FormulaIssuerRegistryWriteGateway,
    P: FormulaPolicyRepository,
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    C: FormulaIssuerClock,
{
    fn context(&self) -> Result<RevisionRequestContext, FormulaIssuerWorkflowError> {
        if !self.context.has_scope(AuthScope::DocumentRead)
            || !self.context.has_scope(AuthScope::DocumentWrite)
        {
            return Err(FormulaIssuerWorkflowError::Binding);
        }
        Ok(RevisionRequestContext::new(
            self.context.tenant_id(),
            self.context.subject(),
        ))
    }
    fn now(&self) -> Result<u64, FormulaIssuerWorkflowError> {
        self.clock.now().map_err(FormulaIssuerWorkflowError::Issuer)
    }
    fn monotonic(&self, before: u64) -> Result<u64, FormulaIssuerWorkflowError> {
        let now = self.now()?;
        if now < before {
            return Err(FormulaIssuerWorkflowError::Issuer(
                FormulaIssuerError::Clock,
            ));
        }
        Ok(now)
    }
    fn artifact_bytes(
        &self,
        id: ArtifactId,
        digest: ContentDigest,
        media: &str,
        limit: usize,
        now: u64,
    ) -> Result<Vec<u8>, FormulaIssuerWorkflowError> {
        let d = self
            .artifacts
            .get_descriptor(self.context, id, now)
            .map_err(|_| FormulaIssuerWorkflowError::Artifact)?;
        if d.artifact_id != id
            || d.sha256 != digest
            || d.kind != ArtifactKind::Evidence
            || d.media_type.as_str() != media
            || d.storage_state != StorageState::Available
            || d.validation_state != ValidationState::Verified
            || d.quarantine_reason.is_some()
            || d.size_bytes == 0
            || d.size_bytes > limit as u64
        {
            return Err(FormulaIssuerWorkflowError::Artifact);
        }
        let raw = self
            .artifacts
            .download(self.context, id, now)
            .map_err(|_| FormulaIssuerWorkflowError::Artifact)?;
        if raw.len() as u64 != d.size_bytes
            || raw.is_empty()
            || raw.len() > limit
            || ContentDigest::of(&raw) != digest
        {
            return Err(FormulaIssuerWorkflowError::Artifact);
        }
        Ok(raw)
    }
    fn ingest(
        &self,
        raw: &[u8],
        media: &str,
        filename: &str,
        limit: usize,
        before: u64,
    ) -> Result<ArtifactDescriptor, FormulaIssuerWorkflowFailure> {
        if raw.is_empty() || raw.len() > limit {
            return Err(preflight(FormulaIssuerWorkflowError::Binding));
        }
        let req = IngestRequest {
            bytes: raw.to_vec(),
            kind: ArtifactKind::Evidence,
            media_type: MediaType::parse(media)
                .map_err(|_| preflight(FormulaIssuerWorkflowError::Binding))?,
            file_name: FileName::parse(filename)
                .map_err(|_| preflight(FormulaIssuerWorkflowError::Binding))?,
        };
        let d = self
            .artifacts
            .ingest(self.context, req, before)
            .map_err(|_| {
                failure(
                    FormulaIssuerWorkflowError::Artifact,
                    FormulaIssuerWorkflowStage::ArtifactIngest,
                    None,
                    FormulaIssuerWriteOutcome::NotAttempted,
                )
            })?;
        let checked = (|| {
            let now = self.monotonic(before)?;
            let got = self.artifact_bytes(d.artifact_id, d.sha256, media, limit, now)?;
            if got != raw || ContentDigest::of(raw) != d.sha256 {
                return Err(FormulaIssuerWorkflowError::Artifact);
            }
            self.monotonic(now)?;
            Ok(())
        })();
        checked.map_err(|e| {
            failure(
                e,
                FormulaIssuerWorkflowStage::ArtifactReadback,
                Some(d.artifact_id),
                FormulaIssuerWriteOutcome::NotAttempted,
            )
        })?;
        Ok(d)
    }
    fn root(
        &self,
        project: ProjectId,
    ) -> Result<(FormulaIssuerTrustRecord, FormulaIssuerTrust), FormulaIssuerWorkflowError> {
        let ctx = self.context()?;
        let before = self.now()?;
        let row = self
            .registry
            .read_trust(&ctx, project)
            .map_err(|_| FormulaIssuerWorkflowError::Registry)?;
        row.validate_for(&ctx, project)
            .map_err(|_| FormulaIssuerWorkflowError::Binding)?;
        live(&row, before).map_err(FormulaIssuerWorkflowError::Issuer)?;
        let raw = self.artifact_bytes(
            row.artifact,
            row.digest,
            FORMULA_ISSUER_TRUST_MEDIA_TYPE,
            MAX_TRUST_BYTES,
            before,
        )?;
        let trust = trust_wire::decode(&raw, &row).map_err(FormulaIssuerWorkflowError::Issuer)?;
        if self
            .registry
            .read_trust(&ctx, project)
            .map_err(|_| FormulaIssuerWorkflowError::Registry)?
            != row
        {
            return Err(FormulaIssuerWorkflowError::Drift);
        }
        live(&row, self.monotonic(before)?).map_err(FormulaIssuerWorkflowError::Issuer)?;
        Ok((row, trust))
    }
    /// Installs explicitly supplied server trust DATA through AEAD storage and named owner/CAS writes.
    /// # Errors
    /// Requires a currently-live bounded root. Preserves artifacts and acknowledged/unknown writes on failure.
    pub fn install_trust(
        &self,
        draft: FormulaIssuerTrustDraft,
        expected_generation: u64,
    ) -> Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure> {
        let ctx = self.context().map_err(preflight)?;
        let before = self.now().map_err(preflight)?;
        if draft.tenant != ctx.tenant_id()
            || expected_generation >= i64::MAX as u64
            || draft.generation != expected_generation + 1
        {
            return Err(preflight(FormulaIssuerWorkflowError::Binding));
        }
        self.writes
            .authorize_root(&ctx, draft.project)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let trust = FormulaIssuerTrust::new(draft)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let mut row = FormulaIssuerTrustRecord {
            tenant: trust.tenant,
            project: trust.project,
            version: Uuid::new_v4(),
            generation: trust.generation,
            issuer: trust.issuer.clone(),
            valid_from: trust.valid_from,
            valid_until: trust.valid_until,
            max_approval_lifetime: trust.max_approval_lifetime,
            artifact: ArtifactId::generate(),
            digest: ContentDigest::of(b"unassigned"),
            creator: ctx.subject(),
        };
        row.validate_for(&ctx, row.project)
            .map_err(|_| preflight(FormulaIssuerWorkflowError::Binding))?;
        live(&row, before).map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let keys: Vec<_> = trust
            .keys
            .iter()
            .map(|(id, key)| serde_json::json!({"key_id":id,"public_key_hex":hex::encode(key)}))
            .collect();
        let raw = serde_json::to_vec(&serde_json::json!({"schema_version":FORMULA_ISSUER_TRUST_SCHEMA,
            "tenant":row.tenant,"project":row.project,"trust_version":row.version,"generation":row.generation,
            "issuer":row.issuer,"valid_from":row.valid_from,"valid_until":row.valid_until,
            "max_approval_lifetime":row.max_approval_lifetime,"keys":keys})).map_err(|_| preflight(FormulaIssuerWorkflowError::Binding))?;
        if trust_wire::decode(&raw, &row)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?
            != trust
        {
            return Err(preflight(FormulaIssuerWorkflowError::Drift));
        }
        let d = self.ingest(
            &raw,
            FORMULA_ISSUER_TRUST_MEDIA_TYPE,
            "formula-issuer-trust.json",
            MAX_TRUST_BYTES,
            before,
        )?;
        row.artifact = d.artifact_id;
        row.digest = d.sha256;
        let now = self.monotonic(before).map_err(|e| {
            failure(
                e,
                FormulaIssuerWorkflowStage::ArtifactReadback,
                Some(row.artifact),
                FormulaIssuerWriteOutcome::NotAttempted,
            )
        })?;
        live(&row, now).map_err(|e| {
            failure(
                FormulaIssuerWorkflowError::Issuer(e),
                FormulaIssuerWorkflowStage::ArtifactReadback,
                Some(row.artifact),
                FormulaIssuerWriteOutcome::NotAttempted,
            )
        })?;
        self.writes
            .register_trust(&ctx, &row, expected_generation)
            .map_err(|e| failed_write(e, row.artifact))?;
        let checked = (|| {
            let (got, got_trust) = self.root(row.project)?;
            if got != row || got_trust != trust {
                return Err(FormulaIssuerWorkflowError::Drift);
            }
            self.monotonic(now)?;
            Ok(())
        })();
        checked.map_err(|e| {
            failure(
                e,
                FormulaIssuerWorkflowStage::RegistryReadback,
                Some(row.artifact),
                FormulaIssuerWriteOutcome::Acknowledged,
            )
        })?;
        Ok(FormulaIssuerProvisioningReceipt {
            action: FormulaRegistryManagementAction::RegisterTrust,
            version: row.version,
            generation: row.generation,
            artifact: row.artifact,
            digest: row.digest,
        })
    }
    /// Signs only an opaque source-generated record matching current policy; verifies live Ed25519 before storage.
    /// # Errors
    /// Rejects foreign scope, policy/root/key/clock drift, bad signatures or CAS/ACL/commit/readback failures.
    pub fn issue_approval(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
        signer: &impl FormulaApprovalSigner,
        expected_generation: u64,
        lifetime: u64,
    ) -> Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure> {
        let ctx = self.context().map_err(preflight)?;
        if scope.tenant() != ctx.tenant_id()
            || scope.subject() != ctx.subject()
            || expected_generation >= i64::MAX as u64
            || lifetime == 0
        {
            return Err(preflight(FormulaIssuerWorkflowError::Binding));
        }
        self.writes
            .authorize_approval(&ctx, scope)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let prepared = self.prepare_approval(&ctx, scope, record, signer, lifetime)?;
        let d = self.ingest(
            &prepared.raw,
            FORMULA_APPROVAL_MEDIA_TYPE,
            "formula-approval.json",
            MAX_APPROVAL_BYTES,
            prepared.before,
        )?;
        let checked = self.current(
            scope,
            &prepared.policy,
            &prepared.root,
            &prepared.trust,
            &prepared.claims,
            prepared.before,
        );
        checked.map_err(|e| {
            failure(
                e,
                FormulaIssuerWorkflowStage::ArtifactReadback,
                Some(d.artifact_id),
                FormulaIssuerWriteOutcome::NotAttempted,
            )
        })?;
        let row = FormulaApprovalRecord {
            tenant: ctx.tenant_id(),
            project: scope.project(),
            branch: scope.branch(),
            document: scope.document().as_str().into(),
            version: Uuid::new_v4(),
            generation: expected_generation + 1,
            policy_version: prepared.policy.binding.policy_version,
            policy_generation: prepared.policy.binding.policy_generation,
            trust_version: prepared.root.version,
            trust_generation: prepared.root.generation,
            artifact: d.artifact_id,
            digest: d.sha256,
            creator: ctx.subject(),
        };
        if [
            prepared.policy.artifact,
            prepared.policy.binding.source_result_artifact,
            prepared.root.artifact,
        ]
        .contains(&row.artifact)
        {
            return Err(failure(
                FormulaIssuerWorkflowError::Binding,
                FormulaIssuerWorkflowStage::ArtifactReadback,
                Some(d.artifact_id),
                FormulaIssuerWriteOutcome::NotAttempted,
            ));
        }
        self.writes
            .register_approval(&ctx, scope, &row, expected_generation)
            .map_err(|e| failed_write(e, row.artifact))?;
        let checked = self.confirm_approval(scope, &row, &prepared);
        checked.map_err(|e| {
            failure(
                e,
                FormulaIssuerWorkflowStage::RegistryReadback,
                Some(row.artifact),
                FormulaIssuerWriteOutcome::Acknowledged,
            )
        })?;
        Ok(FormulaIssuerProvisioningReceipt {
            action: FormulaRegistryManagementAction::RegisterApproval,
            version: row.version,
            generation: row.generation,
            artifact: row.artifact,
            digest: row.digest,
        })
    }
    fn confirm_approval(
        &self,
        scope: &PolicyReadScope,
        row: &FormulaApprovalRecord,
        prepared: &PreparedRegistryApproval,
    ) -> Result<(), FormulaIssuerWorkflowError> {
        let ctx = self.context()?;
        let PreparedRegistryApproval {
            policy,
            root,
            trust,
            before,
            claims,
            raw,
        } = prepared;
        let before = *before;
        let req = approval_request(scope, row.policy_version, row.policy_generation)?;
        let got = self
            .registry
            .read_approval(&ctx, &req)
            .map_err(|_| FormulaIssuerWorkflowError::Registry)?;
        got.validate_for(&ctx, &req)
            .map_err(|_| FormulaIssuerWorkflowError::Binding)?;
        if got != *row {
            return Err(FormulaIssuerWorkflowError::Drift);
        }
        let now = self.monotonic(before)?;
        let bytes = self.artifact_bytes(
            row.artifact,
            row.digest,
            FORMULA_APPROVAL_MEDIA_TYPE,
            MAX_APPROVAL_BYTES,
            now,
        )?;
        if bytes != *raw {
            return Err(FormulaIssuerWorkflowError::Drift);
        }
        self.current(scope, policy, root, trust, claims, before)?;
        if self
            .registry
            .read_approval(&ctx, &req)
            .map_err(|_| FormulaIssuerWorkflowError::Registry)?
            != *row
        {
            return Err(FormulaIssuerWorkflowError::Drift);
        }
        self.current(scope, policy, root, trust, claims, before)?;
        Ok(())
    }
    fn prepare_approval(
        &self,
        ctx: &RevisionRequestContext,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
        signer: &impl FormulaApprovalSigner,
        lifetime: u64,
    ) -> Result<PreparedRegistryApproval, FormulaIssuerWorkflowFailure> {
        let policy = self
            .policies
            .read_current_formula_policy(scope)
            .map_err(|_| preflight(FormulaIssuerWorkflowError::Registry))?;
        if &policy != record.version() {
            return Err(preflight(FormulaIssuerWorkflowError::Drift));
        }
        let (root, trust) = self.root(scope.project()).map_err(preflight)?;
        let before = self.now().map_err(preflight)?;
        let expires = before
            .checked_add(lifetime)
            .ok_or_else(|| preflight(FormulaIssuerWorkflowError::Binding))?;
        let prepared = PreparedFormulaApproval::from_registration_record(
            record,
            FormulaApprovalIdentity {
                issuer: trust.issuer.clone(),
                key_id: signer.key_id().into(),
                trust_generation: trust.generation,
                issued_at: before,
                not_before: before,
                expires_at: expires,
            },
        )
        .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        prepared
            .validate_for_issuance(scope, &policy, &trust, before)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        self.writes
            .authorize_approval(ctx, scope)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let signing = prepared
            .signing_bytes()
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let signature = signer
            .sign(&signing)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let raw = prepared
            .envelope(signature)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        let (claims, actual_signing, signature) =
            wire::decode(&raw).map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        provider::validate_claims(scope, &policy, &trust, &claims, before)
            .map_err(|e| preflight(FormulaIssuerWorkflowError::Issuer(e)))?;
        if actual_signing != signing {
            return Err(preflight(FormulaIssuerWorkflowError::Drift));
        }
        UnparsedPublicKey::new(
            &ED25519,
            trust.keys.get(&claims.key_id).ok_or_else(|| {
                preflight(FormulaIssuerWorkflowError::Issuer(
                    FormulaIssuerError::Trust,
                ))
            })?,
        )
        .verify(&signing, &signature)
        .map_err(|_| {
            preflight(FormulaIssuerWorkflowError::Issuer(
                FormulaIssuerError::Signature,
            ))
        })?;
        self.current(scope, &policy, &root, &trust, &claims, before)
            .map_err(preflight)?;
        Ok(PreparedRegistryApproval {
            policy,
            root,
            trust,
            before,
            claims,
            raw,
        })
    }
    fn current(
        &self,
        scope: &PolicyReadScope,
        policy: &SourcePolicyVersion,
        root: &FormulaIssuerTrustRecord,
        trust: &FormulaIssuerTrust,
        claims: &wire::Claims,
        before: u64,
    ) -> Result<(), FormulaIssuerWorkflowError> {
        if self
            .policies
            .read_current_formula_policy(scope)
            .map_err(|_| FormulaIssuerWorkflowError::Registry)?
            != *policy
            || self.root(scope.project())? != (root.clone(), trust.clone())
        {
            return Err(FormulaIssuerWorkflowError::Drift);
        }
        provider::validate_claims(scope, policy, trust, claims, self.monotonic(before)?)
            .map_err(FormulaIssuerWorkflowError::Issuer)
    }
}
macro_rules! redacted_debug {
    ($($name:ident),+ $(,)?) => { $(impl fmt::Debug for $name {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str(concat!(stringify!($name), "(<redacted>)")) }
    })+ };
}
redacted_debug!(
    FormulaIssuerWorkflowFailure,
    FormulaIssuerProvisioningReceipt
);
impl fmt::Debug for PostgresFormulaIssuerWriteGateway<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresFormulaIssuerWriteGateway(<redacted>)")
    }
}
impl<G, W, P, R, B, S, C> fmt::Debug for RegistryFormulaProvisioner<'_, G, W, P, R, B, S, C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RegistryFormulaProvisioner(<redacted>)")
    }
}
