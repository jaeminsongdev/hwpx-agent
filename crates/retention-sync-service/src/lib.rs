#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::sync::{Arc, Mutex, MutexGuard};

use artifact_service::{ArtifactId, ArtifactKind, ContentDigest, SubjectDigest, TenantId};
use revision_service::{BranchId, ProjectId, RevisionId};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use uuid::Uuid;

const MAX_RETENTION_SECONDS: u64 = 10 * 365 * 24 * 60 * 60;
const MAX_PURGE_LEASE_SECONDS: u64 = 300;
const MAX_PURGE_ATTEMPTS: u8 = 3;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProjectRole {
    Reader,
    Editor,
    Owner,
}

impl ProjectRole {
    const fn can_mutate(self) -> bool {
        matches!(self, Self::Editor | Self::Owner)
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RetentionClass {
    Source,
    Result,
    Preview,
    Evidence,
    Trace,
    Diff,
    Receipt,
}

impl From<ArtifactKind> for RetentionClass {
    fn from(value: ArtifactKind) -> Self {
        match value {
            // Authoritative IR uses the existing source retention policy, never preview/diff TTL.
            // This does not itself prove that a revision reference is durably registered.
            ArtifactKind::Source | ArtifactKind::DocumentIr => Self::Source,
            ArtifactKind::Result => Self::Result,
            ArtifactKind::Preview => Self::Preview,
            ArtifactKind::Evidence => Self::Evidence,
            ArtifactKind::Trace => Self::Trace,
            ArtifactKind::Diff => Self::Diff,
            ArtifactKind::Receipt => Self::Receipt,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RetentionPolicy {
    durations: BTreeMap<RetentionClass, u64>,
    tombstone_grace_seconds: u64,
}

impl RetentionPolicy {
    /// Creates one complete policy. Every artifact class must appear exactly once.
    ///
    /// # Errors
    ///
    /// Returns [`RetentionSyncError::InvalidPolicy`] for missing, duplicate, zero, excessive, or
    /// invalid grace values.
    pub fn new(
        durations: impl IntoIterator<Item = (RetentionClass, u64)>,
        tombstone_grace_seconds: u64,
    ) -> Result<Self, RetentionSyncError> {
        let duration_entries = durations.into_iter().collect::<Vec<_>>();
        let durations = duration_entries.iter().copied().collect::<BTreeMap<_, _>>();
        let all = [
            RetentionClass::Source,
            RetentionClass::Result,
            RetentionClass::Preview,
            RetentionClass::Evidence,
            RetentionClass::Trace,
            RetentionClass::Diff,
            RetentionClass::Receipt,
        ];
        if duration_entries.len() != all.len()
            || durations.len() != all.len()
            || all.iter().any(|class| !durations.contains_key(class))
            || durations
                .values()
                .any(|seconds| *seconds == 0 || *seconds > MAX_RETENTION_SECONDS)
            || tombstone_grace_seconds > 7 * 24 * 60 * 60
        {
            return Err(RetentionSyncError::InvalidPolicy);
        }
        Ok(Self {
            durations,
            tombstone_grace_seconds,
        })
    }

    fn duration_for(&self, class: RetentionClass) -> Result<u64, RetentionSyncError> {
        self.durations
            .get(&class)
            .copied()
            .ok_or(RetentionSyncError::InvalidPolicy)
    }
}

macro_rules! opaque_uuid {
    ($name:ident) => {
        #[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name(Uuid);

        impl $name {
            #[must_use]
            pub fn generate() -> Self {
                Self(Uuid::new_v4())
            }

            #[must_use]
            pub const fn from_uuid(value: Uuid) -> Option<Self> {
                if value.is_nil() {
                    None
                } else {
                    Some(Self(value))
                }
            }

            #[must_use]
            pub const fn as_uuid(self) -> Uuid {
                self.0
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("<opaque>")
            }
        }
    };
}

opaque_uuid!(DeletionRequestId);
opaque_uuid!(LegalHoldId);
opaque_uuid!(PurgeExecutionId);
opaque_uuid!(PurgeReceiptId);
opaque_uuid!(PurgeWorkerId);
opaque_uuid!(MirrorId);
opaque_uuid!(MirrorPushId);
opaque_uuid!(MirrorConflictId);

impl MirrorId {
    /// Parses the exact lowercase public mirror identifier form.
    ///
    /// # Errors
    ///
    /// Returns [`RetentionSyncError::InvalidRequest`] for a noncanonical or nil UUID.
    pub fn parse_public(value: &str) -> Result<Self, RetentionSyncError> {
        let encoded = value
            .strip_prefix("mir_")
            .ok_or(RetentionSyncError::InvalidRequest)?;
        if encoded.len() != 32
            || !encoded
                .as_bytes()
                .iter()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
        {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let value = Uuid::parse_str(encoded).map_err(|_| RetentionSyncError::InvalidRequest)?;
        Self::from_uuid(value).ok_or(RetentionSyncError::InvalidRequest)
    }

    #[must_use]
    pub fn public_id(self) -> String {
        format!("mir_{}", self.0.simple())
    }
}

#[derive(Debug, Error, Clone, Eq, PartialEq)]
pub enum RetentionSyncError {
    #[error("identifier or request is invalid")]
    InvalidRequest,
    #[error("retention policy is invalid")]
    InvalidPolicy,
    #[error("resource was not found")]
    NotFound,
    #[error("operation is not authorized")]
    Forbidden,
    #[error("resource conflicts with existing state")]
    Conflict,
    #[error("active legal hold blocks purge")]
    LegalHoldActive,
    #[error("an authorized purge is already in progress")]
    PurgeInProgress,
    #[error("purge exhausted its bounded attempts")]
    PurgeTerminal,
    #[error("artifact is shared by another project")]
    SharedArtifact,
    #[error("retention deadline has not elapsed")]
    NotDue,
    #[error("purge lease is stale")]
    StaleLease,
    #[error("remote head conflicts with the mirror base")]
    RemoteHeadConflict,
    #[error("committed revision does not match the queued operation plan")]
    MirrorPlanMismatch,
    #[error("repository failed")]
    RepositoryFailure,
}

impl RetentionSyncError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidRequest => "RETENTION_REQUEST_INVALID",
            Self::InvalidPolicy => "RETENTION_POLICY_INVALID",
            Self::NotFound => "RETENTION_RESOURCE_NOT_FOUND",
            Self::Forbidden => "RETENTION_FORBIDDEN",
            Self::Conflict => "RETENTION_CONFLICT",
            Self::LegalHoldActive => "RETENTION_LEGAL_HOLD_ACTIVE",
            Self::PurgeInProgress => "RETENTION_PURGE_IN_PROGRESS",
            Self::PurgeTerminal => "RETENTION_PURGE_TERMINAL",
            Self::SharedArtifact => "RETENTION_ARTIFACT_SHARED",
            Self::NotDue => "RETENTION_NOT_DUE",
            Self::StaleLease => "RETENTION_LEASE_STALE",
            Self::RemoteHeadConflict => "MIRROR_REMOTE_HEAD_CONFLICT",
            Self::MirrorPlanMismatch => "MIRROR_PLAN_MISMATCH",
            Self::RepositoryFailure => "RETENTION_REPOSITORY_FAILED",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct RequestContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    now_unix_seconds: u64,
}

impl RequestContext {
    #[must_use]
    pub const fn new(tenant_id: TenantId, subject: SubjectDigest, now_unix_seconds: u64) -> Self {
        Self {
            tenant_id,
            subject,
            now_unix_seconds,
        }
    }
}

impl fmt::Debug for RequestContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RequestContext")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ArtifactRetentionState {
    Available,
    Tombstoned,
    Purged,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PurgeOutcome {
    ObjectDeleted,
    ObjectAlreadyAbsent,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PurgeFailureState {
    Retryable,
    Terminal,
}

impl PurgeOutcome {
    const fn as_str(self) -> &'static str {
        match self {
            Self::ObjectDeleted => "object_deleted",
            Self::ObjectAlreadyAbsent => "object_already_absent",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct PurgeLease {
    artifact_id: ArtifactId,
    deletion_request_id: DeletionRequestId,
    execution_id: PurgeExecutionId,
    worker_id: PurgeWorkerId,
    attempt: u8,
    fencing_token: u64,
    expires_at: u64,
}

impl fmt::Debug for PurgeLease {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PurgeLease")
            .field("artifact_id", &"<redacted>")
            .field("attempt", &self.attempt)
            .field("fencing_token", &self.fencing_token)
            .field("expires_at", &self.expires_at)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct PurgeReceipt {
    pub receipt_id: PurgeReceiptId,
    pub outcome: PurgeOutcome,
    pub proof_sha256: ContentDigest,
}

impl fmt::Debug for PurgeReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PurgeReceipt")
            .field("receipt_id", &self.receipt_id)
            .field("outcome", &self.outcome)
            .field("proof_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RemoteHead {
    pub revision_id: Option<RevisionId>,
    pub generation: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MirrorResolution {
    RebaseOperationPlan,
    Branch,
    ManualMerge,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MirrorState {
    Clean,
    Ahead,
    PushPrepared,
    Conflict,
    ManualMergeRequired,
}

#[derive(Clone, Eq, PartialEq)]
pub struct MirrorRegistration {
    pub project_id: ProjectId,
    pub branch_id: BranchId,
    pub mirror_id: MirrorId,
    pub device_sha256: ContentDigest,
    pub observed_head: RemoteHead,
    pub snapshot_sha256: ContentDigest,
}

impl fmt::Debug for MirrorRegistration {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MirrorRegistration")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("mirror_id", &self.mirror_id)
            .field("device_sha256", &"<redacted>")
            .field("observed_generation", &self.observed_head.generation)
            .field("snapshot_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct MirrorPushLease {
    mirror_id: MirrorId,
    push_id: MirrorPushId,
    branch_id: BranchId,
    expected_head: RemoteHead,
    pending_plan_sha256: ContentDigest,
    subject: SubjectDigest,
    expires_at: u64,
}

impl fmt::Debug for MirrorPushLease {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MirrorPushLease")
            .field("mirror_id", &self.mirror_id)
            .field("push_id", &self.push_id)
            .field("expected_generation", &self.expected_head.generation)
            .field("pending_plan_sha256", &"<redacted>")
            .field("expires_at", &self.expires_at)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PushDecision {
    Prepared,
    Conflict(MirrorConflictId),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MirrorCheckpointDecision {
    Authorized,
    Conflict(RemoteHead),
}

#[derive(Clone)]
struct ProjectRecord {
    policy_id: String,
    roles: BTreeMap<SubjectDigest, ProjectRole>,
}

#[derive(Clone)]
struct ArtifactRecord {
    kind: ArtifactKind,
    projects: BTreeSet<ProjectId>,
    created_at: u64,
    retention_until: Option<u64>,
    state: ArtifactRetentionState,
    authorization_generation: u64,
}

#[derive(Clone)]
struct HoldRecord {
    project_id: ProjectId,
    artifact_id: Option<ArtifactId>,
    active: bool,
}

#[derive(Clone)]
struct PurgeRecord {
    project_id: ProjectId,
    deletion_request_id: DeletionRequestId,
    subject: SubjectDigest,
    policy_expiry: bool,
    tombstoned_at: u64,
    grace_seconds: u64,
    attempt: u8,
    lease: Option<PurgeLease>,
    receipt: Option<PurgeReceipt>,
    terminal_failure: Option<ContentDigest>,
}

#[derive(Clone)]
struct MirrorRecord {
    project_id: ProjectId,
    branch_id: BranchId,
    device_sha256: ContentDigest,
    observed_head: RemoteHead,
    snapshot_sha256: ContentDigest,
    pending_plan_sha256: Option<ContentDigest>,
    state: MirrorState,
    active_push: Option<MirrorPushLease>,
}

#[derive(Clone)]
struct ConflictRecord {
    mirror_id: MirrorId,
    observed: RemoteHead,
    current: RemoteHead,
    resolution: Option<MirrorResolution>,
}

#[derive(Default)]
struct State {
    projects: BTreeMap<(TenantId, ProjectId), ProjectRecord>,
    policies: BTreeMap<(TenantId, String), RetentionPolicy>,
    artifacts: BTreeMap<(TenantId, ArtifactId), ArtifactRecord>,
    holds: BTreeMap<(TenantId, LegalHoldId), HoldRecord>,
    purges: BTreeMap<(TenantId, ArtifactId), PurgeRecord>,
    deletion_requests: BTreeMap<(TenantId, DeletionRequestId), ArtifactId>,
    purge_receipts: BTreeMap<(TenantId, PurgeReceiptId), ArtifactId>,
    branches: BTreeMap<(TenantId, ProjectId, BranchId), RemoteHead>,
    mirrors: BTreeMap<(TenantId, MirrorId), MirrorRecord>,
    conflicts: BTreeMap<(TenantId, MirrorConflictId), ConflictRecord>,
    push_reservations: BTreeSet<(TenantId, ProjectId, BranchId, u64)>,
    active_push_ids: BTreeSet<(TenantId, ProjectId, MirrorPushId)>,
}

fn reclaim_expired_mirror_push(
    state: &mut State,
    context: &RequestContext,
    mirror_id: MirrorId,
    mirror: &mut MirrorRecord,
    requested_push_id: MirrorPushId,
) -> Result<(), RetentionSyncError> {
    if mirror.state != MirrorState::PushPrepared {
        return Ok(());
    }
    let active = mirror
        .active_push
        .clone()
        .ok_or(RetentionSyncError::Conflict)?;
    if active.expires_at > context.now_unix_seconds || active.push_id == requested_push_id {
        return Err(RetentionSyncError::Conflict);
    }
    state.push_reservations.remove(&(
        context.tenant_id,
        mirror.project_id,
        active.branch_id,
        active.expected_head.generation,
    ));
    state
        .active_push_ids
        .remove(&(context.tenant_id, mirror.project_id, active.push_id));
    let stored = state
        .mirrors
        .get_mut(&(context.tenant_id, mirror_id))
        .ok_or(RetentionSyncError::NotFound)?;
    stored.active_push = None;
    stored.state = MirrorState::Ahead;
    mirror.active_push = None;
    mirror.state = MirrorState::Ahead;
    Ok(())
}

#[derive(Clone, Default)]
pub struct RetentionSyncService {
    state: Arc<Mutex<State>>,
}

impl fmt::Debug for RetentionSyncService {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RetentionSyncService")
            .finish_non_exhaustive()
    }
}

#[allow(
    clippy::missing_errors_doc,
    reason = "the local reference exposes one closed typed error enum shared by all repository operations"
)]
impl RetentionSyncService {
    pub fn put_policy(
        &self,
        tenant_id: TenantId,
        policy_id: &str,
        policy: RetentionPolicy,
    ) -> Result<(), RetentionSyncError> {
        if !valid_policy_id(policy_id) {
            return Err(RetentionSyncError::InvalidPolicy);
        }
        let mut state = self.lock()?;
        let key = (tenant_id, policy_id.to_owned());
        if state.policies.contains_key(&key) {
            return Err(RetentionSyncError::Conflict);
        }
        state.policies.insert(key, policy);
        Ok(())
    }

    pub fn provision_project(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        policy_id: &str,
        roles: impl IntoIterator<Item = (SubjectDigest, ProjectRole)>,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        if !state
            .policies
            .contains_key(&(tenant_id, policy_id.to_owned()))
        {
            return Err(RetentionSyncError::InvalidPolicy);
        }
        let role_entries = roles.into_iter().collect::<Vec<_>>();
        let roles = role_entries.iter().copied().collect::<BTreeMap<_, _>>();
        if roles.is_empty()
            || roles.len() != role_entries.len()
            || !roles.values().any(|role| *role == ProjectRole::Owner)
            || state.projects.contains_key(&(tenant_id, project_id))
        {
            return Err(RetentionSyncError::Conflict);
        }
        state.projects.insert(
            (tenant_id, project_id),
            ProjectRecord {
                policy_id: policy_id.to_owned(),
                roles,
            },
        );
        Ok(())
    }

    pub fn register_artifact(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        kind: ArtifactKind,
        projects: impl IntoIterator<Item = ProjectId>,
        created_at: u64,
        retention_until: Option<u64>,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        let projects = projects.into_iter().collect::<BTreeSet<_>>();
        if projects.is_empty()
            || projects
                .iter()
                .any(|project| !state.projects.contains_key(&(tenant_id, *project)))
            || retention_until.is_some_and(|deadline| deadline < created_at)
        {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let key = (tenant_id, artifact_id);
        if state.artifacts.contains_key(&key) {
            return Err(RetentionSyncError::Conflict);
        }
        state.artifacts.insert(
            key,
            ArtifactRecord {
                kind,
                projects,
                created_at,
                retention_until,
                state: ArtifactRetentionState::Available,
                authorization_generation: 1,
            },
        );
        Ok(())
    }

    pub fn create_legal_hold(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        hold_id: LegalHoldId,
        artifact_id: Option<ArtifactId>,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, ProjectRole::Owner)?;
        let purge_in_progress = state.purges.iter().any(|((tenant_id, candidate), purge)| {
            *tenant_id == context.tenant_id
                && purge.project_id == project_id
                && artifact_id.is_none_or(|artifact_id| artifact_id == *candidate)
                && purge
                    .lease
                    .as_ref()
                    .is_some_and(|lease| lease.expires_at > context.now_unix_seconds)
        });
        if purge_in_progress {
            return Err(RetentionSyncError::PurgeInProgress);
        }
        if let Some(artifact_id) = artifact_id {
            let artifact = state
                .artifacts
                .get(&(context.tenant_id, artifact_id))
                .ok_or(RetentionSyncError::NotFound)?;
            if !artifact.projects.contains(&project_id)
                || artifact.state == ArtifactRetentionState::Purged
            {
                return Err(RetentionSyncError::NotFound);
            }
        }
        if state.holds.iter().any(|((tenant_id, _), hold)| {
            *tenant_id == context.tenant_id
                && hold.project_id == project_id
                && hold.artifact_id == artifact_id
                && hold.active
        }) {
            return Err(RetentionSyncError::Conflict);
        }
        let key = (context.tenant_id, hold_id);
        if state.holds.contains_key(&key) {
            return Err(RetentionSyncError::Conflict);
        }
        state.holds.insert(
            key,
            HoldRecord {
                project_id,
                artifact_id,
                active: true,
            },
        );
        Ok(())
    }

    pub fn release_legal_hold(
        &self,
        context: &RequestContext,
        hold_id: LegalHoldId,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        let project_id = state
            .holds
            .get(&(context.tenant_id, hold_id))
            .ok_or(RetentionSyncError::NotFound)?
            .project_id;
        require_role(&state, context, project_id, ProjectRole::Owner)?;
        let hold = state
            .holds
            .get_mut(&(context.tenant_id, hold_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if !hold.active {
            return Err(RetentionSyncError::Conflict);
        }
        hold.active = false;
        Ok(())
    }

    pub fn tombstone_user_delete(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        artifact_id: ArtifactId,
        deletion_request_id: DeletionRequestId,
    ) -> Result<(), RetentionSyncError> {
        self.tombstone(context, project_id, artifact_id, deletion_request_id, false)
    }

    pub fn tombstone_due_artifact(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        artifact_id: ArtifactId,
        deletion_request_id: DeletionRequestId,
    ) -> Result<(), RetentionSyncError> {
        self.tombstone(context, project_id, artifact_id, deletion_request_id, true)
    }

    fn tombstone(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        artifact_id: ArtifactId,
        deletion_request_id: DeletionRequestId,
        enforce_due: bool,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, ProjectRole::Owner)?;
        if let Some(existing_artifact_id) = state
            .deletion_requests
            .get(&(context.tenant_id, deletion_request_id))
        {
            let existing = state
                .purges
                .get(&(context.tenant_id, *existing_artifact_id))
                .ok_or(RetentionSyncError::RepositoryFailure)?;
            return if *existing_artifact_id == artifact_id
                && existing.project_id == project_id
                && existing.subject == context.subject
                && existing.policy_expiry == enforce_due
            {
                Ok(())
            } else {
                Err(RetentionSyncError::Conflict)
            };
        }
        if state.purges.contains_key(&(context.tenant_id, artifact_id)) {
            return Err(RetentionSyncError::Conflict);
        }
        if has_active_hold(&state, context.tenant_id, project_id, artifact_id) {
            return Err(RetentionSyncError::LegalHoldActive);
        }
        let project = state
            .projects
            .get(&(context.tenant_id, project_id))
            .ok_or(RetentionSyncError::NotFound)?;
        let policy = state
            .policies
            .get(&(context.tenant_id, project.policy_id.clone()))
            .ok_or(RetentionSyncError::InvalidPolicy)?;
        let grace_seconds = policy.tombstone_grace_seconds;
        let duration = {
            let artifact = state
                .artifacts
                .get(&(context.tenant_id, artifact_id))
                .ok_or(RetentionSyncError::NotFound)?;
            if !artifact.projects.contains(&project_id) {
                return Err(RetentionSyncError::NotFound);
            }
            if artifact.projects.len() != 1 {
                return Err(RetentionSyncError::SharedArtifact);
            }
            policy.duration_for(artifact.kind.into())?
        };
        let artifact = state
            .artifacts
            .get_mut(&(context.tenant_id, artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if artifact.state != ArtifactRetentionState::Available {
            return Err(RetentionSyncError::Conflict);
        }
        let policy_due_at = artifact.created_at.saturating_add(duration);
        let due_at = artifact
            .retention_until
            .map_or(policy_due_at, |deadline| deadline.max(policy_due_at));
        if enforce_due && context.now_unix_seconds < due_at {
            return Err(RetentionSyncError::NotDue);
        }
        artifact.state = ArtifactRetentionState::Tombstoned;
        artifact.authorization_generation = artifact.authorization_generation.saturating_add(1);
        state.purges.insert(
            (context.tenant_id, artifact_id),
            PurgeRecord {
                project_id,
                deletion_request_id,
                subject: context.subject,
                policy_expiry: enforce_due,
                tombstoned_at: context.now_unix_seconds,
                grace_seconds,
                attempt: 0,
                lease: None,
                receipt: None,
                terminal_failure: None,
            },
        );
        state
            .deletion_requests
            .insert((context.tenant_id, deletion_request_id), artifact_id);
        Ok(())
    }

    pub fn claim_purge(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        worker_id: PurgeWorkerId,
        execution_id: PurgeExecutionId,
        lease_seconds: u64,
    ) -> Result<PurgeLease, RetentionSyncError> {
        if lease_seconds == 0 || lease_seconds > MAX_PURGE_LEASE_SECONDS {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let mut state = self.lock()?;
        let record = state
            .purges
            .get(&(context.tenant_id, artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, record.project_id, ProjectRole::Owner)?;
        if has_active_hold(&state, context.tenant_id, record.project_id, artifact_id) {
            return Err(RetentionSyncError::LegalHoldActive);
        }
        let artifact = state
            .artifacts
            .get(&(context.tenant_id, artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if artifact.projects.len() != 1 || !artifact.projects.contains(&record.project_id) {
            return Err(RetentionSyncError::SharedArtifact);
        }
        if context.now_unix_seconds < record.tombstoned_at.saturating_add(record.grace_seconds) {
            return Err(RetentionSyncError::NotDue);
        }
        if record.terminal_failure.is_some() {
            return Err(RetentionSyncError::PurgeTerminal);
        }
        if record.receipt.is_some() {
            return Err(RetentionSyncError::PurgeTerminal);
        }
        if record
            .lease
            .as_ref()
            .is_some_and(|lease| lease.expires_at > context.now_unix_seconds)
        {
            return Err(RetentionSyncError::PurgeInProgress);
        }
        let record = state
            .purges
            .get_mut(&(context.tenant_id, artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if record.attempt >= MAX_PURGE_ATTEMPTS {
            return Err(RetentionSyncError::PurgeTerminal);
        }
        record.attempt = record.attempt.saturating_add(1);
        let lease = PurgeLease {
            artifact_id,
            deletion_request_id: record.deletion_request_id,
            execution_id,
            worker_id,
            attempt: record.attempt,
            fencing_token: u64::from(record.attempt),
            expires_at: context.now_unix_seconds.saturating_add(lease_seconds),
        };
        record.lease = Some(lease.clone());
        Ok(lease)
    }

    pub fn record_purge_failure(
        &self,
        context: &RequestContext,
        lease: &PurgeLease,
        failure_sha256: ContentDigest,
    ) -> Result<PurgeFailureState, RetentionSyncError> {
        let mut state = self.lock()?;
        let record = state
            .purges
            .get(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, record.project_id, ProjectRole::Owner)?;
        if record.lease.as_ref() != Some(lease) || context.now_unix_seconds >= lease.expires_at {
            return Err(RetentionSyncError::StaleLease);
        }
        let record = state
            .purges
            .get_mut(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        record.lease = None;
        if record.attempt >= MAX_PURGE_ATTEMPTS {
            record.terminal_failure = Some(failure_sha256);
            Ok(PurgeFailureState::Terminal)
        } else {
            Ok(PurgeFailureState::Retryable)
        }
    }

    pub fn complete_purge(
        &self,
        context: &RequestContext,
        lease: &PurgeLease,
        receipt_id: PurgeReceiptId,
        outcome: PurgeOutcome,
    ) -> Result<PurgeReceipt, RetentionSyncError> {
        let mut state = self.lock()?;
        let record = state
            .purges
            .get(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, record.project_id, ProjectRole::Owner)?;
        if has_active_hold(
            &state,
            context.tenant_id,
            record.project_id,
            lease.artifact_id,
        ) {
            return Err(RetentionSyncError::LegalHoldActive);
        }
        let artifact = state
            .artifacts
            .get(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if artifact.projects.len() != 1 || !artifact.projects.contains(&record.project_id) {
            return Err(RetentionSyncError::SharedArtifact);
        }
        if record.lease.as_ref() != Some(lease) || context.now_unix_seconds >= lease.expires_at {
            return Err(RetentionSyncError::StaleLease);
        }
        if state
            .purge_receipts
            .contains_key(&(context.tenant_id, receipt_id))
        {
            return Err(RetentionSyncError::Conflict);
        }
        let mut proof = Vec::with_capacity(16 * 6 + 32);
        proof.extend_from_slice(context.tenant_id.as_uuid().as_bytes());
        proof.extend_from_slice(lease.artifact_id.as_uuid().as_bytes());
        proof.extend_from_slice(lease.deletion_request_id.as_uuid().as_bytes());
        proof.extend_from_slice(lease.execution_id.as_uuid().as_bytes());
        proof.extend_from_slice(lease.worker_id.as_uuid().as_bytes());
        proof.extend_from_slice(receipt_id.as_uuid().as_bytes());
        proof.extend_from_slice(outcome.as_str().as_bytes());
        proof.extend_from_slice(&lease.fencing_token.to_be_bytes());
        let receipt = PurgeReceipt {
            receipt_id,
            outcome,
            proof_sha256: ContentDigest::of(&proof),
        };
        let record = state
            .purges
            .get_mut(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        record.lease = None;
        record.receipt = Some(receipt.clone());
        let artifact = state
            .artifacts
            .get_mut(&(context.tenant_id, lease.artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        artifact.state = ArtifactRetentionState::Purged;
        artifact.authorization_generation = artifact.authorization_generation.saturating_add(1);
        state
            .purge_receipts
            .insert((context.tenant_id, receipt_id), lease.artifact_id);
        Ok(receipt)
    }

    pub fn artifact_state(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        artifact_id: ArtifactId,
    ) -> Result<ArtifactRetentionState, RetentionSyncError> {
        let state = self.lock()?;
        require_role(&state, context, project_id, ProjectRole::Reader)?;
        let artifact = state
            .artifacts
            .get(&(context.tenant_id, artifact_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if !artifact.projects.contains(&project_id) {
            return Err(RetentionSyncError::NotFound);
        }
        Ok(artifact.state)
    }

    pub fn register_branch(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
        head: RemoteHead,
    ) -> Result<(), RetentionSyncError> {
        if head.revision_id.is_none() != (head.generation == 0) {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let mut state = self.lock()?;
        if !state.projects.contains_key(&(tenant_id, project_id)) {
            return Err(RetentionSyncError::NotFound);
        }
        let key = (tenant_id, project_id, branch_id);
        if state.branches.contains_key(&key) {
            return Err(RetentionSyncError::Conflict);
        }
        state.branches.insert(key, head);
        Ok(())
    }

    pub fn register_mirror(
        &self,
        context: &RequestContext,
        registration: &MirrorRegistration,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        require_role(
            &state,
            context,
            registration.project_id,
            ProjectRole::Editor,
        )?;
        if state.branches.get(&(
            context.tenant_id,
            registration.project_id,
            registration.branch_id,
        )) != Some(&registration.observed_head)
        {
            return Err(RetentionSyncError::RemoteHeadConflict);
        }
        let key = (context.tenant_id, registration.mirror_id);
        if state.mirrors.contains_key(&key)
            || state.mirrors.iter().any(|((tenant_id, _), mirror)| {
                *tenant_id == context.tenant_id
                    && mirror.project_id == registration.project_id
                    && mirror.branch_id == registration.branch_id
                    && mirror.device_sha256 == registration.device_sha256
            })
        {
            return Err(RetentionSyncError::Conflict);
        }
        state.mirrors.insert(
            key,
            MirrorRecord {
                project_id: registration.project_id,
                branch_id: registration.branch_id,
                device_sha256: registration.device_sha256,
                observed_head: registration.observed_head,
                snapshot_sha256: registration.snapshot_sha256,
                pending_plan_sha256: None,
                state: MirrorState::Clean,
                active_push: None,
            },
        );
        Ok(())
    }

    pub fn authorize_mirror_checkpoint(
        &self,
        context: &RequestContext,
        project_id: ProjectId,
        branch_id: BranchId,
        mirror_id: MirrorId,
        expected_head: RemoteHead,
    ) -> Result<MirrorCheckpointDecision, RetentionSyncError> {
        if expected_head.revision_id.is_none() != (expected_head.generation == 0) {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let state = self.lock()?;
        let mirror = state
            .mirrors
            .get(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if mirror.project_id != project_id || mirror.branch_id != branch_id {
            return Err(RetentionSyncError::NotFound);
        }
        require_role(&state, context, project_id, ProjectRole::Editor)?;
        let current = *state
            .branches
            .get(&(context.tenant_id, project_id, branch_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if current != expected_head || mirror.observed_head != expected_head {
            return Ok(MirrorCheckpointDecision::Conflict(current));
        }
        if mirror.state != MirrorState::Clean
            || mirror.pending_plan_sha256.is_some()
            || mirror.active_push.is_some()
        {
            return Err(RetentionSyncError::Conflict);
        }
        Ok(MirrorCheckpointDecision::Authorized)
    }

    pub fn queue_local_plan(
        &self,
        context: &RequestContext,
        mirror_id: MirrorId,
        snapshot_sha256: ContentDigest,
        operation_plan_sha256: ContentDigest,
    ) -> Result<(), RetentionSyncError> {
        let mut state = self.lock()?;
        let project_id = state
            .mirrors
            .get(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?
            .project_id;
        require_role(&state, context, project_id, ProjectRole::Editor)?;
        let mirror = state
            .mirrors
            .get_mut(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if mirror.state != MirrorState::Clean || mirror.pending_plan_sha256.is_some() {
            return Err(RetentionSyncError::Conflict);
        }
        mirror.snapshot_sha256 = snapshot_sha256;
        mirror.pending_plan_sha256 = Some(operation_plan_sha256);
        mirror.state = MirrorState::Ahead;
        Ok(())
    }

    pub fn begin_mirror_push(
        &self,
        context: &RequestContext,
        mirror_id: MirrorId,
        push_id: MirrorPushId,
        conflict_id: MirrorConflictId,
        lease_seconds: u64,
    ) -> Result<PushDecision, RetentionSyncError> {
        if lease_seconds == 0 || lease_seconds > MAX_PURGE_LEASE_SECONDS {
            return Err(RetentionSyncError::InvalidRequest);
        }
        let mut state = self.lock()?;
        let mut mirror = state
            .mirrors
            .get(&(context.tenant_id, mirror_id))
            .cloned()
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, mirror.project_id, ProjectRole::Editor)?;
        reclaim_expired_mirror_push(&mut state, context, mirror_id, &mut mirror, push_id)?;
        if mirror.state != MirrorState::Ahead {
            return Err(RetentionSyncError::Conflict);
        }
        let current = *state
            .branches
            .get(&(context.tenant_id, mirror.project_id, mirror.branch_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if current != mirror.observed_head {
            if state
                .conflicts
                .contains_key(&(context.tenant_id, conflict_id))
            {
                return Err(RetentionSyncError::Conflict);
            }
            state.conflicts.insert(
                (context.tenant_id, conflict_id),
                ConflictRecord {
                    mirror_id,
                    observed: mirror.observed_head,
                    current,
                    resolution: None,
                },
            );
            state
                .mirrors
                .get_mut(&(context.tenant_id, mirror_id))
                .ok_or(RetentionSyncError::NotFound)?
                .state = MirrorState::Conflict;
            return Ok(PushDecision::Conflict(conflict_id));
        }
        let reservation = (
            context.tenant_id,
            mirror.project_id,
            mirror.branch_id,
            current.generation,
        );
        let push_identity = (context.tenant_id, mirror.project_id, push_id);
        if state.push_reservations.contains(&reservation)
            || state.active_push_ids.contains(&push_identity)
        {
            return Err(RetentionSyncError::Conflict);
        }
        state.push_reservations.insert(reservation);
        state.active_push_ids.insert(push_identity);
        let lease = MirrorPushLease {
            mirror_id,
            push_id,
            branch_id: mirror.branch_id,
            expected_head: current,
            pending_plan_sha256: mirror
                .pending_plan_sha256
                .ok_or(RetentionSyncError::Conflict)?,
            subject: context.subject,
            expires_at: context.now_unix_seconds.saturating_add(lease_seconds),
        };
        let mirror = state
            .mirrors
            .get_mut(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        mirror.active_push = Some(lease);
        mirror.state = MirrorState::PushPrepared;
        Ok(PushDecision::Prepared)
    }

    pub fn commit_mirror_push(
        &self,
        context: &RequestContext,
        mirror_id: MirrorId,
        push_id: MirrorPushId,
        new_revision_id: RevisionId,
        operation_plan_sha256: ContentDigest,
    ) -> Result<RemoteHead, RetentionSyncError> {
        let mut state = self.lock()?;
        let mirror = state
            .mirrors
            .get(&(context.tenant_id, mirror_id))
            .cloned()
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, mirror.project_id, ProjectRole::Editor)?;
        let lease = mirror.active_push.ok_or(RetentionSyncError::StaleLease)?;
        if lease.push_id != push_id
            || lease.subject != context.subject
            || context.now_unix_seconds >= lease.expires_at
            || mirror.state != MirrorState::PushPrepared
        {
            return Err(RetentionSyncError::StaleLease);
        }
        if lease.pending_plan_sha256 != operation_plan_sha256 {
            return Err(RetentionSyncError::MirrorPlanMismatch);
        }
        let branch_key = (context.tenant_id, mirror.project_id, lease.branch_id);
        let current = state
            .branches
            .get_mut(&branch_key)
            .ok_or(RetentionSyncError::NotFound)?;
        if *current != lease.expected_head {
            return Err(RetentionSyncError::RemoteHeadConflict);
        }
        let next = RemoteHead {
            revision_id: Some(new_revision_id),
            generation: current
                .generation
                .checked_add(1)
                .ok_or(RetentionSyncError::Conflict)?,
        };
        *current = next;
        state.push_reservations.remove(&(
            context.tenant_id,
            mirror.project_id,
            lease.branch_id,
            lease.expected_head.generation,
        ));
        state
            .active_push_ids
            .remove(&(context.tenant_id, mirror.project_id, lease.push_id));
        let mirror = state
            .mirrors
            .get_mut(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        mirror.observed_head = next;
        mirror.pending_plan_sha256 = None;
        mirror.active_push = None;
        mirror.state = MirrorState::Clean;
        Ok(next)
    }

    #[cfg(test)]
    fn advance_remote_for_test(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
        expected: RemoteHead,
        next_revision_id: RevisionId,
    ) -> Result<RemoteHead, RetentionSyncError> {
        let mut state = self.lock()?;
        let head = state
            .branches
            .get_mut(&(tenant_id, project_id, branch_id))
            .ok_or(RetentionSyncError::NotFound)?;
        if *head != expected {
            return Err(RetentionSyncError::RemoteHeadConflict);
        }
        head.revision_id = Some(next_revision_id);
        head.generation = head
            .generation
            .checked_add(1)
            .ok_or(RetentionSyncError::Conflict)?;
        Ok(*head)
    }

    pub fn resolve_mirror_conflict(
        &self,
        context: &RequestContext,
        conflict_id: MirrorConflictId,
        resolution: MirrorResolution,
        branch_id: Option<BranchId>,
    ) -> Result<MirrorState, RetentionSyncError> {
        let mut state = self.lock()?;
        let conflict = state
            .conflicts
            .get(&(context.tenant_id, conflict_id))
            .cloned()
            .ok_or(RetentionSyncError::NotFound)?;
        let mirror = state
            .mirrors
            .get(&(context.tenant_id, conflict.mirror_id))
            .cloned()
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, mirror.project_id, ProjectRole::Editor)?;
        if conflict.resolution.is_some() || mirror.state != MirrorState::Conflict {
            return Err(RetentionSyncError::Conflict);
        }
        let (target_branch, target_head, target_state) = match resolution {
            MirrorResolution::RebaseOperationPlan => {
                if branch_id.is_some() {
                    return Err(RetentionSyncError::InvalidRequest);
                }
                (mirror.branch_id, conflict.current, MirrorState::Ahead)
            }
            MirrorResolution::Branch => {
                let branch_id = branch_id.ok_or(RetentionSyncError::InvalidRequest)?;
                let head = *state
                    .branches
                    .get(&(context.tenant_id, mirror.project_id, branch_id))
                    .ok_or(RetentionSyncError::NotFound)?;
                (branch_id, head, MirrorState::Ahead)
            }
            MirrorResolution::ManualMerge => {
                if branch_id.is_some() {
                    return Err(RetentionSyncError::InvalidRequest);
                }
                (
                    mirror.branch_id,
                    conflict.observed,
                    MirrorState::ManualMergeRequired,
                )
            }
        };
        state
            .conflicts
            .get_mut(&(context.tenant_id, conflict_id))
            .ok_or(RetentionSyncError::NotFound)?
            .resolution = Some(resolution);
        let mirror = state
            .mirrors
            .get_mut(&(context.tenant_id, conflict.mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        mirror.branch_id = target_branch;
        mirror.observed_head = target_head;
        mirror.state = target_state;
        Ok(target_state)
    }

    pub fn mirror_state(
        &self,
        context: &RequestContext,
        mirror_id: MirrorId,
    ) -> Result<MirrorState, RetentionSyncError> {
        let state = self.lock()?;
        let mirror = state
            .mirrors
            .get(&(context.tenant_id, mirror_id))
            .ok_or(RetentionSyncError::NotFound)?;
        require_role(&state, context, mirror.project_id, ProjectRole::Reader)?;
        Ok(mirror.state)
    }

    fn lock(&self) -> Result<MutexGuard<'_, State>, RetentionSyncError> {
        self.state
            .lock()
            .map_err(|_| RetentionSyncError::RepositoryFailure)
    }
}

fn require_role(
    state: &State,
    context: &RequestContext,
    project_id: ProjectId,
    minimum: ProjectRole,
) -> Result<(), RetentionSyncError> {
    let role = state
        .projects
        .get(&(context.tenant_id, project_id))
        .and_then(|project| project.roles.get(&context.subject))
        .copied()
        .ok_or(RetentionSyncError::NotFound)?;
    let allowed = match minimum {
        ProjectRole::Reader => true,
        ProjectRole::Editor => role.can_mutate(),
        ProjectRole::Owner => role == ProjectRole::Owner,
    };
    if allowed {
        Ok(())
    } else {
        Err(RetentionSyncError::Forbidden)
    }
}

fn has_active_hold(
    state: &State,
    tenant_id: TenantId,
    project_id: ProjectId,
    artifact_id: ArtifactId,
) -> bool {
    state.holds.iter().any(|((tenant, _), hold)| {
        *tenant == tenant_id
            && hold.active
            && hold.project_id == project_id
            && hold
                .artifact_id
                .is_none_or(|held_artifact| held_artifact == artifact_id)
    })
}

fn valid_policy_id(value: &str) -> bool {
    let Some((first, suffix)) = value.split_once('.') else {
        return false;
    };
    value.len() <= 128
        && first
            .bytes()
            .next()
            .is_some_and(|byte| byte.is_ascii_lowercase())
        && first
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit())
        && suffix.split('.').all(|segment| {
            !segment.is_empty()
                && segment.bytes().all(|byte| {
                    byte.is_ascii_lowercase()
                        || byte.is_ascii_digit()
                        || matches!(byte, b'_' | b'-')
                })
        })
}

#[must_use]
pub fn mirror_binding_digest(
    tenant_id: TenantId,
    project_id: ProjectId,
    branch_id: BranchId,
    device_sha256: ContentDigest,
    head: RemoteHead,
    snapshot_sha256: ContentDigest,
) -> ContentDigest {
    let mut bytes = Vec::with_capacity(16 * 4 + 72);
    bytes.extend_from_slice(tenant_id.as_uuid().as_bytes());
    bytes.extend_from_slice(project_id.as_uuid().as_bytes());
    bytes.extend_from_slice(branch_id.as_uuid().as_bytes());
    bytes.extend_from_slice(device_sha256.as_bytes());
    if let Some(revision_id) = head.revision_id {
        bytes.extend_from_slice(revision_id.as_uuid().as_bytes());
    }
    bytes.extend_from_slice(&head.generation.to_be_bytes());
    bytes.extend_from_slice(snapshot_sha256.as_bytes());
    ContentDigest::of(&Sha256::digest(bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tenant(value: u128) -> TenantId {
        TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn subject(value: &str) -> SubjectDigest {
        SubjectDigest::from_authenticated_subject(value)
            .unwrap_or_else(|error| panic!("subject: {error}"))
    }

    fn project(value: u128) -> ProjectId {
        ProjectId::parse(&format!("prj_{value:032x}"))
            .unwrap_or_else(|error| panic!("project: {error}"))
    }

    fn branch(value: u128) -> BranchId {
        BranchId::parse(&format!("brn_{value:032x}"))
            .unwrap_or_else(|error| panic!("branch: {error}"))
    }

    fn revision(value: u128) -> RevisionId {
        RevisionId::parse(&format!("rev_{value:032x}"))
            .unwrap_or_else(|error| panic!("revision: {error}"))
    }

    fn artifact(value: u128) -> ArtifactId {
        ArtifactId::parse(&format!("art_{value:032x}"))
            .unwrap_or_else(|error| panic!("artifact: {error}"))
    }

    fn id<T>(value: u128, create: impl FnOnce(Uuid) -> Option<T>) -> T {
        create(Uuid::from_u128(value)).unwrap_or_else(|| panic!("non-nil id"))
    }

    fn policy() -> RetentionPolicy {
        RetentionPolicy::new(
            [
                (RetentionClass::Source, 100),
                (RetentionClass::Result, 90),
                (RetentionClass::Preview, 20),
                (RetentionClass::Evidence, 40),
                (RetentionClass::Trace, 10),
                (RetentionClass::Diff, 60),
                (RetentionClass::Receipt, 80),
            ],
            5,
        )
        .unwrap_or_else(|error| panic!("policy: {error}"))
    }

    struct Fixture {
        service: RetentionSyncService,
        tenant_id: TenantId,
        project_id: ProjectId,
        owner: SubjectDigest,
        artifact_id: ArtifactId,
    }

    impl Fixture {
        fn new(kind: ArtifactKind) -> Self {
            let service = RetentionSyncService::default();
            let tenant_id = tenant(1);
            let project_id = project(2);
            let owner = subject("retention-owner");
            service
                .put_policy(tenant_id, "retention.local", policy())
                .and_then(|()| {
                    service.provision_project(
                        tenant_id,
                        project_id,
                        "retention.local",
                        [(owner, ProjectRole::Owner)],
                    )
                })
                .unwrap_or_else(|error| panic!("project: {error}"));
            let artifact_id = artifact(3);
            service
                .register_artifact(tenant_id, artifact_id, kind, [project_id], 100, None)
                .unwrap_or_else(|error| panic!("artifact: {error}"));
            Self {
                service,
                tenant_id,
                project_id,
                owner,
                artifact_id,
            }
        }

        fn context(&self, now: u64) -> RequestContext {
            RequestContext::new(self.tenant_id, self.owner, now)
        }
    }

    #[test]
    fn policy_requires_every_class_and_finite_bounds() {
        assert_eq!(
            RetentionPolicy::new([(RetentionClass::Source, 1)], 0),
            Err(RetentionSyncError::InvalidPolicy)
        );
        assert_eq!(
            RetentionPolicy::new(
                [
                    (RetentionClass::Source, 1),
                    (RetentionClass::Result, 1),
                    (RetentionClass::Preview, 1),
                    (RetentionClass::Evidence, 1),
                    (RetentionClass::Trace, 1),
                    (RetentionClass::Diff, 1),
                    (RetentionClass::Receipt, MAX_RETENTION_SECONDS + 1),
                ],
                0,
            ),
            Err(RetentionSyncError::InvalidPolicy)
        );
        assert_eq!(
            RetentionPolicy::new(
                [
                    (RetentionClass::Source, 1),
                    (RetentionClass::Source, 2),
                    (RetentionClass::Result, 1),
                    (RetentionClass::Preview, 1),
                    (RetentionClass::Evidence, 1),
                    (RetentionClass::Trace, 1),
                    (RetentionClass::Diff, 1),
                    (RetentionClass::Receipt, 1),
                ],
                0,
            ),
            Err(RetentionSyncError::InvalidPolicy)
        );
        let service = RetentionSyncService::default();
        assert_eq!(
            service.put_policy(tenant(90), "retention_bad.local", policy()),
            Err(RetentionSyncError::InvalidPolicy)
        );
        assert_eq!(
            service.put_policy(tenant(90), &format!("{}.local", "a".repeat(129)), policy(),),
            Err(RetentionSyncError::InvalidPolicy)
        );
    }

    #[test]
    fn duplicate_registration_conflicts_are_side_effect_free() {
        let fixture = Fixture::new(ArtifactKind::Result);
        let replacement = RetentionPolicy::new(
            [
                (RetentionClass::Source, 1),
                (RetentionClass::Result, 1),
                (RetentionClass::Preview, 1),
                (RetentionClass::Evidence, 1),
                (RetentionClass::Trace, 1),
                (RetentionClass::Diff, 1),
                (RetentionClass::Receipt, 1),
            ],
            0,
        )
        .unwrap_or_else(|error| panic!("replacement: {error}"));
        assert_eq!(
            fixture
                .service
                .put_policy(fixture.tenant_id, "retention.local", replacement),
            Err(RetentionSyncError::Conflict)
        );
        let attacker = subject("retention-attacker");
        assert_eq!(
            fixture.service.provision_project(
                fixture.tenant_id,
                fixture.project_id,
                "retention.local",
                [(attacker, ProjectRole::Owner)],
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.register_artifact(
                fixture.tenant_id,
                fixture.artifact_id,
                ArtifactKind::Trace,
                [fixture.project_id],
                0,
                None,
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.artifact_state(
                &RequestContext::new(fixture.tenant_id, attacker, 101),
                fixture.project_id,
                fixture.artifact_id,
            ),
            Err(RetentionSyncError::NotFound)
        );
        assert_eq!(
            fixture.service.tombstone_due_artifact(
                &fixture.context(101),
                fixture.project_id,
                fixture.artifact_id,
                id(150, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::NotDue)
        );
    }

    #[test]
    fn legal_hold_blocks_tombstone_and_purge_until_release() {
        let fixture = Fixture::new(ArtifactKind::Source);
        let hold_id = id(4, LegalHoldId::from_uuid);
        fixture
            .service
            .create_legal_hold(
                &fixture.context(100),
                fixture.project_id,
                hold_id,
                Some(fixture.artifact_id),
            )
            .unwrap_or_else(|error| panic!("hold: {error}"));
        assert_eq!(
            fixture.service.create_legal_hold(
                &fixture.context(100),
                fixture.project_id,
                id(140, LegalHoldId::from_uuid),
                Some(fixture.artifact_id),
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.tombstone_user_delete(
                &fixture.context(100),
                fixture.project_id,
                fixture.artifact_id,
                id(5, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::LegalHoldActive)
        );
        fixture
            .service
            .release_legal_hold(&fixture.context(101), hold_id)
            .and_then(|()| {
                fixture.service.tombstone_user_delete(
                    &fixture.context(101),
                    fixture.project_id,
                    fixture.artifact_id,
                    id(5, DeletionRequestId::from_uuid),
                )
            })
            .unwrap_or_else(|error| panic!("release/delete: {error}"));
        assert_eq!(
            fixture.service.artifact_state(
                &fixture.context(101),
                fixture.project_id,
                fixture.artifact_id,
            ),
            Ok(ArtifactRetentionState::Tombstoned)
        );
    }

    #[test]
    fn policy_due_is_class_specific_and_explicit_deadline_wins() {
        let fixture = Fixture::new(ArtifactKind::Trace);
        assert_eq!(
            fixture.service.tombstone_due_artifact(
                &fixture.context(109),
                fixture.project_id,
                fixture.artifact_id,
                id(10, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::NotDue)
        );
        assert!(
            fixture
                .service
                .tombstone_due_artifact(
                    &fixture.context(110),
                    fixture.project_id,
                    fixture.artifact_id,
                    id(10, DeletionRequestId::from_uuid),
                )
                .is_ok()
        );
        assert_eq!(
            fixture.service.tombstone_user_delete(
                &fixture.context(110),
                fixture.project_id,
                fixture.artifact_id,
                id(10, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::Conflict)
        );
        let delayed = artifact(11);
        fixture
            .service
            .register_artifact(
                fixture.tenant_id,
                delayed,
                ArtifactKind::Result,
                [fixture.project_id],
                100,
                Some(250),
            )
            .unwrap_or_else(|error| panic!("delayed artifact: {error}"));
        assert_eq!(
            fixture.service.tombstone_due_artifact(
                &fixture.context(249),
                fixture.project_id,
                delayed,
                id(12, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::NotDue)
        );
        assert!(
            fixture
                .service
                .tombstone_due_artifact(
                    &fixture.context(250),
                    fixture.project_id,
                    delayed,
                    id(12, DeletionRequestId::from_uuid),
                )
                .is_ok()
        );
        assert_eq!(
            fixture.service.tombstone_user_delete(
                &fixture.context(250),
                fixture.project_id,
                delayed,
                id(10, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::Conflict)
        );
    }

    #[test]
    fn shared_artifact_is_never_deleted_by_one_project() {
        let fixture = Fixture::new(ArtifactKind::Result);
        let second = project(11);
        fixture
            .service
            .provision_project(
                fixture.tenant_id,
                second,
                "retention.local",
                [(fixture.owner, ProjectRole::Owner)],
            )
            .and_then(|()| {
                fixture.service.register_artifact(
                    fixture.tenant_id,
                    artifact(12),
                    ArtifactKind::Result,
                    [fixture.project_id, second],
                    100,
                    None,
                )
            })
            .unwrap_or_else(|error| panic!("shared: {error}"));
        assert_eq!(
            fixture.service.tombstone_user_delete(
                &fixture.context(110),
                fixture.project_id,
                artifact(12),
                id(13, DeletionRequestId::from_uuid),
            ),
            Err(RetentionSyncError::SharedArtifact)
        );
    }

    #[test]
    fn purge_is_fenced_bounded_and_receipted() {
        let fixture = Fixture::new(ArtifactKind::Preview);
        fixture
            .service
            .tombstone_user_delete(
                &fixture.context(100),
                fixture.project_id,
                fixture.artifact_id,
                id(20, DeletionRequestId::from_uuid),
            )
            .unwrap_or_else(|error| panic!("delete: {error}"));
        assert_eq!(
            fixture.service.claim_purge(
                &fixture.context(104),
                fixture.artifact_id,
                id(21, PurgeWorkerId::from_uuid),
                id(22, PurgeExecutionId::from_uuid),
                30,
            ),
            Err(RetentionSyncError::NotDue)
        );
        let first = fixture
            .service
            .claim_purge(
                &fixture.context(105),
                fixture.artifact_id,
                id(21, PurgeWorkerId::from_uuid),
                id(22, PurgeExecutionId::from_uuid),
                5,
            )
            .unwrap_or_else(|error| panic!("first claim: {error}"));
        let second = fixture
            .service
            .claim_purge(
                &fixture.context(111),
                fixture.artifact_id,
                id(23, PurgeWorkerId::from_uuid),
                id(24, PurgeExecutionId::from_uuid),
                30,
            )
            .unwrap_or_else(|error| panic!("second claim: {error}"));
        assert_eq!(
            fixture.service.complete_purge(
                &fixture.context(112),
                &first,
                id(25, PurgeReceiptId::from_uuid),
                PurgeOutcome::ObjectDeleted,
            ),
            Err(RetentionSyncError::StaleLease)
        );
        let receipt = fixture
            .service
            .complete_purge(
                &fixture.context(112),
                &second,
                id(25, PurgeReceiptId::from_uuid),
                PurgeOutcome::ObjectAlreadyAbsent,
            )
            .unwrap_or_else(|error| panic!("complete: {error}"));
        assert_eq!(receipt.outcome, PurgeOutcome::ObjectAlreadyAbsent);
        assert_eq!(
            fixture.service.artifact_state(
                &fixture.context(112),
                fixture.project_id,
                fixture.artifact_id,
            ),
            Ok(ArtifactRetentionState::Purged)
        );
    }

    #[test]
    fn purge_receipt_identity_reuse_is_side_effect_free() {
        let fixture = Fixture::new(ArtifactKind::Preview);
        let second_artifact = artifact(26);
        fixture
            .service
            .register_artifact(
                fixture.tenant_id,
                second_artifact,
                ArtifactKind::Preview,
                [fixture.project_id],
                100,
                None,
            )
            .unwrap_or_else(|error| panic!("second artifact: {error}"));
        let mut leases = Vec::new();
        for (artifact_id, request, worker, execution) in [
            (fixture.artifact_id, 20, 21, 22),
            (second_artifact, 27, 28, 29),
        ] {
            let lease = fixture
                .service
                .tombstone_user_delete(
                    &fixture.context(100),
                    fixture.project_id,
                    artifact_id,
                    id(request, DeletionRequestId::from_uuid),
                )
                .and_then(|()| {
                    fixture.service.claim_purge(
                        &fixture.context(105),
                        artifact_id,
                        id(worker, PurgeWorkerId::from_uuid),
                        id(execution, PurgeExecutionId::from_uuid),
                        30,
                    )
                })
                .unwrap_or_else(|error| panic!("claim: {error}"));
            leases.push(lease);
        }
        fixture
            .service
            .complete_purge(
                &fixture.context(106),
                &leases[0],
                id(25, PurgeReceiptId::from_uuid),
                PurgeOutcome::ObjectDeleted,
            )
            .unwrap_or_else(|error| panic!("first complete: {error}"));
        assert_eq!(
            fixture.service.complete_purge(
                &fixture.context(106),
                &leases[1],
                id(25, PurgeReceiptId::from_uuid),
                PurgeOutcome::ObjectDeleted,
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.artifact_state(
                &fixture.context(106),
                fixture.project_id,
                second_artifact,
            ),
            Ok(ArtifactRetentionState::Tombstoned)
        );
        assert!(
            fixture
                .service
                .complete_purge(
                    &fixture.context(106),
                    &leases[1],
                    id(30, PurgeReceiptId::from_uuid),
                    PurgeOutcome::ObjectDeleted,
                )
                .is_ok()
        );
    }

    fn clean_mirror_fixture() -> (Fixture, BranchId, MirrorId, RemoteHead) {
        let fixture = Fixture::new(ArtifactKind::Receipt);
        let branch_id = branch(30);
        let mirror_id = id(31, MirrorId::from_uuid);
        let head = RemoteHead {
            revision_id: Some(revision(32)),
            generation: 1,
        };
        fixture
            .service
            .register_branch(fixture.tenant_id, fixture.project_id, branch_id, head)
            .and_then(|()| {
                fixture.service.register_mirror(
                    &fixture.context(100),
                    &MirrorRegistration {
                        project_id: fixture.project_id,
                        branch_id,
                        mirror_id,
                        device_sha256: ContentDigest::of(b"device"),
                        observed_head: head,
                        snapshot_sha256: ContentDigest::of(b"snapshot"),
                    },
                )
            })
            .unwrap_or_else(|error| panic!("mirror: {error}"));
        assert_eq!(
            fixture.service.register_branch(
                fixture.tenant_id,
                fixture.project_id,
                branch_id,
                RemoteHead {
                    revision_id: Some(revision(399)),
                    generation: 99,
                },
            ),
            Err(RetentionSyncError::Conflict)
        );
        (fixture, branch_id, mirror_id, head)
    }

    fn mirror_fixture() -> (Fixture, BranchId, MirrorId, RemoteHead) {
        let (fixture, branch_id, mirror_id, head) = clean_mirror_fixture();
        fixture
            .service
            .queue_local_plan(
                &fixture.context(101),
                mirror_id,
                ContentDigest::of(b"local snapshot"),
                ContentDigest::of(b"plan"),
            )
            .unwrap_or_else(|error| panic!("local plan: {error}"));
        (fixture, branch_id, mirror_id, head)
    }

    #[test]
    fn mirror_public_identifier_requires_exact_lowercase_non_nil_form() {
        let mirror_id = id(31, MirrorId::from_uuid);
        let public_id = "mir_0000000000000000000000000000001f";
        assert_eq!(MirrorId::parse_public(public_id), Ok(mirror_id));
        assert_eq!(mirror_id.public_id(), public_id);
        for invalid in [
            "MIR_0000000000000000000000000000001f",
            "mir_0000000000000000000000000000001F",
            "mir_00000000000000000000000000000000",
            "mir_00000000-0000-0000-0000-00000000001f",
            "0000000000000000000000000000001f",
        ] {
            assert_eq!(
                MirrorId::parse_public(invalid),
                Err(RetentionSyncError::InvalidRequest)
            );
        }
    }

    #[test]
    fn checkpoint_authorization_binds_exact_mirror_and_idle_head() {
        let (fixture, branch_id, mirror_id, head) = clean_mirror_fixture();
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(101),
                fixture.project_id,
                branch_id,
                mirror_id,
                head,
            ),
            Ok(MirrorCheckpointDecision::Authorized)
        );
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(101),
                project(98),
                branch_id,
                mirror_id,
                head,
            ),
            Err(RetentionSyncError::NotFound)
        );
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(101),
                fixture.project_id,
                branch(98),
                mirror_id,
                head,
            ),
            Err(RetentionSyncError::NotFound)
        );
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(101),
                fixture.project_id,
                branch_id,
                id(98, MirrorId::from_uuid),
                head,
            ),
            Err(RetentionSyncError::NotFound)
        );
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &RequestContext::new(tenant(98), fixture.owner, 101),
                fixture.project_id,
                branch_id,
                mirror_id,
                head,
            ),
            Err(RetentionSyncError::NotFound)
        );
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &RequestContext::new(fixture.tenant_id, subject("unknown"), 101),
                fixture.project_id,
                branch_id,
                mirror_id,
                head,
            ),
            Err(RetentionSyncError::NotFound)
        );
        fixture
            .service
            .queue_local_plan(
                &fixture.context(102),
                mirror_id,
                ContentDigest::of(b"changed snapshot"),
                ContentDigest::of(b"changed plan"),
            )
            .unwrap_or_else(|error| panic!("queue: {error}"));
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(103),
                fixture.project_id,
                branch_id,
                mirror_id,
                head,
            ),
            Err(RetentionSyncError::Conflict)
        );
    }

    #[test]
    fn checkpoint_authorization_reports_current_head_without_mutation() {
        let (fixture, branch_id, mirror_id, head) = clean_mirror_fixture();
        let current = fixture
            .service
            .advance_remote_for_test(
                fixture.tenant_id,
                fixture.project_id,
                branch_id,
                head,
                revision(99),
            )
            .unwrap_or_else(|error| panic!("advance: {error}"));
        assert_eq!(
            fixture.service.authorize_mirror_checkpoint(
                &fixture.context(102),
                fixture.project_id,
                branch_id,
                mirror_id,
                head,
            ),
            Ok(MirrorCheckpointDecision::Conflict(current))
        );
        assert_eq!(
            fixture
                .service
                .mirror_state(&fixture.context(102), mirror_id),
            Ok(MirrorState::Clean)
        );
    }

    #[test]
    fn exact_head_push_advances_once_without_overwrite() {
        let (fixture, branch_id, mirror_id, head) = mirror_fixture();
        assert_eq!(
            fixture.service.register_mirror(
                &fixture.context(102),
                &MirrorRegistration {
                    project_id: fixture.project_id,
                    branch_id,
                    mirror_id,
                    device_sha256: ContentDigest::of(b"replacement device"),
                    observed_head: head,
                    snapshot_sha256: ContentDigest::of(b"replacement snapshot"),
                },
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(102),
                mirror_id,
                id(33, MirrorPushId::from_uuid),
                id(34, MirrorConflictId::from_uuid),
                30,
            ),
            Ok(PushDecision::Prepared)
        );
        let next = fixture
            .service
            .commit_mirror_push(
                &fixture.context(103),
                mirror_id,
                id(33, MirrorPushId::from_uuid),
                revision(35),
                ContentDigest::of(b"plan"),
            )
            .unwrap_or_else(|error| panic!("commit: {error}"));
        assert_eq!(next.generation, 2);
        assert_eq!(
            fixture
                .service
                .mirror_state(&fixture.context(103), mirror_id),
            Ok(MirrorState::Clean)
        );
    }

    #[test]
    fn active_push_identity_cannot_alias_another_mirror() {
        let (fixture, _branch_id, mirror_id, _head) = mirror_fixture();
        let second_branch = branch(36);
        let second_mirror = id(37, MirrorId::from_uuid);
        let second_head = RemoteHead {
            revision_id: Some(revision(38)),
            generation: 4,
        };
        fixture
            .service
            .register_branch(
                fixture.tenant_id,
                fixture.project_id,
                second_branch,
                second_head,
            )
            .and_then(|()| {
                fixture.service.register_mirror(
                    &fixture.context(101),
                    &MirrorRegistration {
                        project_id: fixture.project_id,
                        branch_id: second_branch,
                        mirror_id: second_mirror,
                        device_sha256: ContentDigest::of(b"second device"),
                        observed_head: second_head,
                        snapshot_sha256: ContentDigest::of(b"second snapshot"),
                    },
                )
            })
            .and_then(|()| {
                fixture.service.queue_local_plan(
                    &fixture.context(101),
                    second_mirror,
                    ContentDigest::of(b"second local snapshot"),
                    ContentDigest::of(b"second plan"),
                )
            })
            .unwrap_or_else(|error| panic!("second mirror: {error}"));
        let push_id = id(39, MirrorPushId::from_uuid);
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(102),
                mirror_id,
                push_id,
                id(40, MirrorConflictId::from_uuid),
                30,
            ),
            Ok(PushDecision::Prepared)
        );
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(102),
                second_mirror,
                push_id,
                id(41, MirrorConflictId::from_uuid),
                30,
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture
                .service
                .mirror_state(&fixture.context(102), second_mirror),
            Ok(MirrorState::Ahead)
        );
    }

    #[test]
    fn remote_advance_creates_conflict_and_never_overwrites() {
        let (fixture, branch_id, mirror_id, head) = mirror_fixture();
        let advanced = fixture
            .service
            .advance_remote_for_test(
                fixture.tenant_id,
                fixture.project_id,
                branch_id,
                head,
                revision(40),
            )
            .unwrap_or_else(|error| panic!("advance: {error}"));
        let conflict_id = id(41, MirrorConflictId::from_uuid);
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(102),
                mirror_id,
                id(42, MirrorPushId::from_uuid),
                conflict_id,
                30,
            ),
            Ok(PushDecision::Conflict(conflict_id))
        );
        assert_eq!(advanced.generation, 2);
        assert_eq!(
            fixture
                .service
                .mirror_state(&fixture.context(102), mirror_id),
            Ok(MirrorState::Conflict)
        );
    }

    #[test]
    fn conflict_resolution_is_explicit_and_single_use() {
        let (fixture, branch_id, mirror_id, head) = mirror_fixture();
        fixture
            .service
            .advance_remote_for_test(
                fixture.tenant_id,
                fixture.project_id,
                branch_id,
                head,
                revision(50),
            )
            .and_then(|_| {
                fixture.service.begin_mirror_push(
                    &fixture.context(102),
                    mirror_id,
                    id(51, MirrorPushId::from_uuid),
                    id(52, MirrorConflictId::from_uuid),
                    30,
                )
            })
            .unwrap_or_else(|error| panic!("conflict: {error}"));
        assert_eq!(
            fixture.service.resolve_mirror_conflict(
                &fixture.context(103),
                id(52, MirrorConflictId::from_uuid),
                MirrorResolution::RebaseOperationPlan,
                None,
            ),
            Ok(MirrorState::Ahead)
        );
        assert_eq!(
            fixture.service.resolve_mirror_conflict(
                &fixture.context(104),
                id(52, MirrorConflictId::from_uuid),
                MirrorResolution::ManualMerge,
                None,
            ),
            Err(RetentionSyncError::Conflict)
        );
    }

    #[test]
    fn purge_failures_are_bounded_and_hold_cannot_overtake_active_effect() {
        let fixture = Fixture::new(ArtifactKind::Result);
        fixture
            .service
            .tombstone_user_delete(
                &fixture.context(100),
                fixture.project_id,
                fixture.artifact_id,
                id(60, DeletionRequestId::from_uuid),
            )
            .unwrap_or_else(|error| panic!("delete: {error}"));
        let first = fixture
            .service
            .claim_purge(
                &fixture.context(105),
                fixture.artifact_id,
                id(61, PurgeWorkerId::from_uuid),
                id(62, PurgeExecutionId::from_uuid),
                30,
            )
            .unwrap_or_else(|error| panic!("first: {error}"));
        assert_eq!(
            fixture.service.create_legal_hold(
                &fixture.context(106),
                fixture.project_id,
                id(63, LegalHoldId::from_uuid),
                Some(fixture.artifact_id),
            ),
            Err(RetentionSyncError::PurgeInProgress)
        );
        assert_eq!(
            fixture.service.record_purge_failure(
                &fixture.context(106),
                &first,
                ContentDigest::of(b"failure one"),
            ),
            Ok(PurgeFailureState::Retryable)
        );
        let second = fixture
            .service
            .claim_purge(
                &fixture.context(107),
                fixture.artifact_id,
                id(61, PurgeWorkerId::from_uuid),
                id(64, PurgeExecutionId::from_uuid),
                30,
            )
            .unwrap_or_else(|error| panic!("second: {error}"));
        assert_eq!(
            fixture.service.record_purge_failure(
                &fixture.context(108),
                &second,
                ContentDigest::of(b"failure two"),
            ),
            Ok(PurgeFailureState::Retryable)
        );
        let third = fixture
            .service
            .claim_purge(
                &fixture.context(109),
                fixture.artifact_id,
                id(61, PurgeWorkerId::from_uuid),
                id(65, PurgeExecutionId::from_uuid),
                30,
            )
            .unwrap_or_else(|error| panic!("third: {error}"));
        assert_eq!(
            fixture.service.record_purge_failure(
                &fixture.context(110),
                &third,
                ContentDigest::of(b"failure three"),
            ),
            Ok(PurgeFailureState::Terminal)
        );
        assert_eq!(
            fixture.service.claim_purge(
                &fixture.context(111),
                fixture.artifact_id,
                id(61, PurgeWorkerId::from_uuid),
                id(66, PurgeExecutionId::from_uuid),
                30,
            ),
            Err(RetentionSyncError::PurgeTerminal)
        );
    }

    #[test]
    fn mirror_plan_binding_and_expired_reservation_recovery_are_fail_closed() {
        let (fixture, _branch_id, mirror_id, _head) = mirror_fixture();
        fixture
            .service
            .begin_mirror_push(
                &fixture.context(102),
                mirror_id,
                id(70, MirrorPushId::from_uuid),
                id(71, MirrorConflictId::from_uuid),
                5,
            )
            .unwrap_or_else(|error| panic!("prepare: {error}"));
        assert_eq!(
            fixture.service.commit_mirror_push(
                &fixture.context(103),
                mirror_id,
                id(70, MirrorPushId::from_uuid),
                revision(72),
                ContentDigest::of(b"different plan"),
            ),
            Err(RetentionSyncError::MirrorPlanMismatch)
        );
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(108),
                mirror_id,
                id(70, MirrorPushId::from_uuid),
                id(74, MirrorConflictId::from_uuid),
                30,
            ),
            Err(RetentionSyncError::Conflict)
        );
        assert_eq!(
            fixture.service.begin_mirror_push(
                &fixture.context(108),
                mirror_id,
                id(73, MirrorPushId::from_uuid),
                id(74, MirrorConflictId::from_uuid),
                30,
            ),
            Ok(PushDecision::Prepared)
        );
        let next = fixture
            .service
            .commit_mirror_push(
                &fixture.context(109),
                mirror_id,
                id(73, MirrorPushId::from_uuid),
                revision(75),
                ContentDigest::of(b"plan"),
            )
            .unwrap_or_else(|error| panic!("recovered commit: {error}"));
        assert_eq!(next.generation, 2);
    }

    #[test]
    fn cross_tenant_access_is_indistinguishable_and_debug_is_redacted() {
        let fixture = Fixture::new(ArtifactKind::Evidence);
        let other = RequestContext::new(tenant(99), subject("other"), 100);
        assert_eq!(
            fixture
                .service
                .artifact_state(&other, fixture.project_id, fixture.artifact_id),
            Err(RetentionSyncError::NotFound)
        );
        let debug = format!("{:?}", fixture.context(100));
        assert!(!debug.contains("retention-owner"));
        assert!(debug.contains("<redacted>"));
    }

    #[test]
    fn mirror_binding_is_deterministic_and_identity_bound() {
        let tenant_id = tenant(70);
        let project_id = project(71);
        let branch_id = branch(72);
        let head = RemoteHead {
            revision_id: Some(revision(73)),
            generation: 9,
        };
        let first = mirror_binding_digest(
            tenant_id,
            project_id,
            branch_id,
            ContentDigest::of(b"device"),
            head,
            ContentDigest::of(b"snapshot"),
        );
        assert_eq!(
            first,
            mirror_binding_digest(
                tenant_id,
                project_id,
                branch_id,
                ContentDigest::of(b"device"),
                head,
                ContentDigest::of(b"snapshot"),
            )
        );
        assert_ne!(
            first,
            mirror_binding_digest(
                tenant_id,
                project_id,
                branch_id,
                ContentDigest::of(b"device"),
                RemoteHead {
                    revision_id: head.revision_id,
                    generation: 10,
                },
                ContentDigest::of(b"snapshot"),
            )
        );
        assert_ne!(
            first,
            mirror_binding_digest(
                tenant_id,
                project_id,
                branch_id,
                ContentDigest::of(b"different device"),
                head,
                ContentDigest::of(b"snapshot"),
            )
        );
    }
}
