#![forbid(unsafe_code)]
#![allow(
    clippy::missing_errors_doc,
    reason = "this executable exposes an internal reference core whose stable errors are defined by CleanupError::code"
)]

use std::collections::btree_map::Entry;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::io::Read as _;
use std::path::{Component, Path, PathBuf};
use std::sync::{Arc, Mutex};

use artifact_service::{ArtifactId, ArtifactKind, ContentDigest, SubjectDigest, TenantId};
use hwpx_agent_foundation::workdir::{SecureWorkspace, WorkspaceError};
use thiserror::Error;
use uuid::Uuid;

const MAX_CLEANUP_LEASE_SECONDS: u64 = 300;
const MAX_CLEANUP_ATTEMPTS: u16 = 3;
const MAX_ORPHAN_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum CleanupError {
    #[error("cleanup identifier is invalid")]
    InvalidIdentifier,
    #[error("cleanup request is invalid")]
    InvalidRequest,
    #[error("cleanup object was not found")]
    NotFound,
    #[error("cleanup mutation is forbidden")]
    AccessDenied,
    #[error("cleanup identity is already bound differently")]
    Conflict,
    #[error("cleanup lease is stale, expired, or mismatched")]
    StaleLease,
    #[error("cleanup target is still referenced")]
    TargetReferenced,
    #[error("source artifacts cannot be cleanup targets")]
    SourceArtifactProtected,
    #[error("cleanup target execution failed closed")]
    TargetExecutionFailed,
    #[error("cleanup fault was injected")]
    InjectedFault,
    #[error("cleanup retry budget is exhausted")]
    RetryExhausted,
    #[error("cleanup repository failed")]
    RepositoryFailure,
}

impl CleanupError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "CLEANUP_IDENTIFIER_INVALID",
            Self::InvalidRequest => "CLEANUP_REQUEST_INVALID",
            Self::NotFound => "CLEANUP_NOT_FOUND",
            Self::AccessDenied => "CLEANUP_ACCESS_DENIED",
            Self::Conflict => "CLEANUP_IDENTITY_CONFLICT",
            Self::StaleLease => "CLEANUP_STALE_LEASE",
            Self::TargetReferenced => "CLEANUP_TARGET_REFERENCED",
            Self::SourceArtifactProtected => "CLEANUP_SOURCE_PROTECTED",
            Self::TargetExecutionFailed => "CLEANUP_TARGET_EXECUTION_FAILED",
            Self::InjectedFault => "CLEANUP_INJECTED_FAULT",
            Self::RetryExhausted => "CLEANUP_RETRY_EXHAUSTED",
            Self::RepositoryFailure => "CLEANUP_REPOSITORY_FAILED",
        }
    }
}

macro_rules! opaque_uuid_id {
    ($name:ident, $prefix:literal, $redacted:literal) => {
        #[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name(Uuid);

        impl $name {
            pub fn parse(value: &str) -> Result<Self, CleanupError> {
                let encoded = value
                    .strip_prefix($prefix)
                    .ok_or(CleanupError::InvalidIdentifier)?;
                if encoded.len() != 32
                    || !encoded
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                {
                    return Err(CleanupError::InvalidIdentifier);
                }
                let uuid = Uuid::parse_str(encoded).map_err(|_| CleanupError::InvalidIdentifier)?;
                if uuid.is_nil() {
                    return Err(CleanupError::InvalidIdentifier);
                }
                Ok(Self(uuid))
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

            #[must_use]
            pub fn public_id(self) -> String {
                format!("{}{}", $prefix, self.0.simple())
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str($redacted)
            }
        }
    };
}

opaque_uuid_id!(ProjectId, "prj_", "<redacted-project-id>");
opaque_uuid_id!(JobId, "job_", "<redacted-job-id>");
opaque_uuid_id!(ExecutionId, "exe_", "<redacted-execution-id>");
opaque_uuid_id!(CancellationId, "can_", "<redacted-cancellation-id>");
opaque_uuid_id!(CleanupTaskId, "cln_", "<redacted-cleanup-task-id>");
opaque_uuid_id!(CleanupWorkerId, "cwk_", "<redacted-cleanup-worker-id>");
opaque_uuid_id!(WorkspaceHandle, "wsp_", "<redacted-workspace-handle>");

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

#[derive(Clone, Eq, PartialEq)]
pub struct CleanupContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    now_unix_seconds: u64,
}

impl CleanupContext {
    #[must_use]
    pub const fn new(tenant_id: TenantId, subject: SubjectDigest, now_unix_seconds: u64) -> Self {
        Self {
            tenant_id,
            subject,
            now_unix_seconds,
        }
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn now_unix_seconds(&self) -> u64 {
        self.now_unix_seconds
    }
}

impl fmt::Debug for CleanupContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CleanupContext")
            .field("tenant_id", &self.tenant_id)
            .field("subject", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObservedJobState {
    Queued,
    Active,
    Succeeded,
    Failed,
    Cancelled,
    OutcomeUnknown,
}

impl ObservedJobState {
    #[must_use]
    pub const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Succeeded | Self::Failed | Self::Cancelled | Self::OutcomeUnknown
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExternalEffectPhase {
    Prepared,
    Started,
    Committed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CancellationState {
    Requested,
    Cancelled,
    OutcomeUnknown,
    TooLate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CleanupState {
    Pending,
    Leased,
    Succeeded,
    FailedTerminal,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CleanupOutcome {
    WorkspaceRemoved,
    WorkspaceAlreadyAbsent,
    ArtifactQuarantined,
    ArtifactAlreadyQuarantined,
}

impl CleanupOutcome {
    const fn as_str(self) -> &'static str {
        match self {
            Self::WorkspaceRemoved => "workspace_removed",
            Self::WorkspaceAlreadyAbsent => "workspace_already_absent",
            Self::ArtifactQuarantined => "artifact_quarantined",
            Self::ArtifactAlreadyQuarantined => "artifact_already_quarantined",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FaultPoint {
    None,
    BeforeExternalCleanup,
    AfterExternalCleanupBeforeReceipt,
}

#[derive(Clone, Eq, PartialEq)]
pub struct ActiveExecution {
    execution_id: ExecutionId,
    attempt_no: u16,
    fencing_token: u64,
    lease_expires_at_unix_seconds: u64,
}

impl ActiveExecution {
    pub fn new(
        execution_id: ExecutionId,
        attempt_no: u16,
        fencing_token: u64,
        lease_expires_at_unix_seconds: u64,
    ) -> Result<Self, CleanupError> {
        if attempt_no == 0
            || fencing_token != u64::from(attempt_no)
            || lease_expires_at_unix_seconds == 0
        {
            return Err(CleanupError::InvalidRequest);
        }
        Ok(Self {
            execution_id,
            attempt_no,
            fencing_token,
            lease_expires_at_unix_seconds,
        })
    }
}

impl fmt::Debug for ActiveExecution {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveExecution")
            .field("execution_id", &"<redacted>")
            .field("attempt_no", &self.attempt_no)
            .field("fencing_token", &self.fencing_token)
            .field(
                "lease_expires_at_unix_seconds",
                &self.lease_expires_at_unix_seconds,
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum CleanupTarget {
    Workspace {
        handle: WorkspaceHandle,
        execution_id: ExecutionId,
        attempt_no: u16,
        fencing_token: u64,
    },
    OrphanArtifact {
        artifact_id: ArtifactId,
        content_sha256: ContentDigest,
        artifact_kind: ArtifactKind,
    },
}

impl CleanupTarget {
    fn fingerprint(&self) -> ContentDigest {
        let mut bytes = Vec::with_capacity(128);
        match self {
            Self::Workspace {
                handle,
                execution_id,
                attempt_no,
                fencing_token,
            } => {
                bytes.extend_from_slice(b"workspace\0");
                bytes.extend_from_slice(handle.as_uuid().as_bytes());
                bytes.extend_from_slice(execution_id.as_uuid().as_bytes());
                bytes.extend_from_slice(&attempt_no.to_be_bytes());
                bytes.extend_from_slice(&fencing_token.to_be_bytes());
            }
            Self::OrphanArtifact {
                artifact_id,
                content_sha256,
                artifact_kind,
            } => {
                bytes.extend_from_slice(b"orphan-artifact\0");
                bytes.extend_from_slice(artifact_id.as_uuid().as_bytes());
                bytes.extend_from_slice(content_sha256.as_bytes());
                bytes.extend_from_slice(artifact_kind.as_str().as_bytes());
            }
        }
        ContentDigest::of(&bytes)
    }
}

impl fmt::Debug for CleanupTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Workspace {
                attempt_no,
                fencing_token,
                ..
            } => formatter
                .debug_struct("Workspace")
                .field("handle", &"<redacted>")
                .field("execution_id", &"<redacted>")
                .field("attempt_no", attempt_no)
                .field("fencing_token", fencing_token)
                .finish(),
            Self::OrphanArtifact { artifact_kind, .. } => formatter
                .debug_struct("OrphanArtifact")
                .field("artifact_id", &"<redacted>")
                .field("content_sha256", &"<redacted>")
                .field("artifact_kind", artifact_kind)
                .finish(),
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CleanupLease {
    task_id: CleanupTaskId,
    worker_id: CleanupWorkerId,
    attempt_no: u16,
    fencing_token: u64,
    issued_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

impl CleanupLease {
    #[must_use]
    pub const fn task_id(&self) -> CleanupTaskId {
        self.task_id
    }

    #[must_use]
    pub const fn attempt_no(&self) -> u16 {
        self.attempt_no
    }
}

impl fmt::Debug for CleanupLease {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CleanupLease")
            .field("task_id", &"<redacted>")
            .field("worker_id", &"<redacted>")
            .field("attempt_no", &self.attempt_no)
            .field("fencing_token", &self.fencing_token)
            .field("issued_at_unix_seconds", &self.issued_at_unix_seconds)
            .field("expires_at_unix_seconds", &self.expires_at_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CleanupReceipt {
    task_id: CleanupTaskId,
    target_fingerprint: ContentDigest,
    outcome: CleanupOutcome,
    proof_sha256: ContentDigest,
    completed_at_unix_seconds: u64,
}

impl CleanupReceipt {
    #[must_use]
    pub const fn outcome(&self) -> CleanupOutcome {
        self.outcome
    }
}

impl fmt::Debug for CleanupReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CleanupReceipt")
            .field("task_id", &"<redacted>")
            .field("target_fingerprint", &"<redacted>")
            .field("outcome", &self.outcome)
            .field("proof_sha256", &"<redacted>")
            .field("completed_at_unix_seconds", &self.completed_at_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
struct JobProjection {
    subject: SubjectDigest,
    state: ObservedJobState,
    effect_phase: ExternalEffectPhase,
    active_execution: Option<ActiveExecution>,
    workspace_handle: Option<WorkspaceHandle>,
}

#[derive(Clone, Eq, PartialEq)]
struct CancellationRecord {
    cancellation_id: CancellationId,
    subject: SubjectDigest,
    state: CancellationState,
    requested_at_unix_seconds: u64,
    resolved_at_unix_seconds: Option<u64>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ArtifactProjection {
    content_sha256: ContentDigest,
    artifact_kind: ArtifactKind,
    referenced: bool,
}

#[derive(Clone, Eq, PartialEq)]
pub struct CleanupTask {
    task_id: CleanupTaskId,
    project_id: ProjectId,
    job_id: JobId,
    target: CleanupTarget,
    state: CleanupState,
    attempt_count: u16,
    active_lease: Option<CleanupLease>,
    receipt: Option<CleanupReceipt>,
}

impl CleanupTask {
    #[must_use]
    pub const fn state(&self) -> CleanupState {
        self.state
    }

    #[must_use]
    pub const fn receipt(&self) -> Option<&CleanupReceipt> {
        self.receipt.as_ref()
    }
}

impl fmt::Debug for CleanupTask {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CleanupTask")
            .field("task_id", &"<redacted>")
            .field("project_id", &"<redacted>")
            .field("job_id", &"<redacted>")
            .field("target", &self.target)
            .field("state", &self.state)
            .field("attempt_count", &self.attempt_count)
            .field("active_lease", &self.active_lease)
            .field("receipt", &self.receipt)
            .finish()
    }
}

type ProjectKey = (TenantId, ProjectId);
type JobKey = (TenantId, ProjectId, JobId);
type TaskKey = (TenantId, CleanupTaskId);
type ArtifactKey = (TenantId, ArtifactId);

#[derive(Default)]
struct CleanupStateStore {
    project_acl: BTreeMap<ProjectKey, BTreeMap<SubjectDigest, ProjectRole>>,
    jobs: BTreeMap<JobKey, JobProjection>,
    cancellations: BTreeMap<JobKey, CancellationRecord>,
    tasks: BTreeMap<TaskKey, CleanupTask>,
    task_fingerprints: BTreeSet<(TenantId, ContentDigest)>,
    artifacts: BTreeMap<ArtifactKey, ArtifactProjection>,
}

#[derive(Clone, Default)]
pub struct CleanupRepository {
    state: Arc<Mutex<CleanupStateStore>>,
}

impl fmt::Debug for CleanupRepository {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CleanupRepository")
            .finish_non_exhaustive()
    }
}

impl CleanupRepository {
    pub fn provision_project(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        acl: impl IntoIterator<Item = (SubjectDigest, ProjectRole)>,
    ) -> Result<(), CleanupError> {
        let mut roles = BTreeMap::new();
        for (subject, role) in acl {
            if roles.insert(subject, role).is_some() {
                return Err(CleanupError::InvalidRequest);
            }
        }
        if roles.is_empty() || !roles.values().any(|role| *role == ProjectRole::Owner) {
            return Err(CleanupError::InvalidRequest);
        }
        let mut state = self.lock()?;
        match state.project_acl.entry((tenant_id, project_id)) {
            Entry::Vacant(entry) => {
                entry.insert(roles);
                Ok(())
            }
            Entry::Occupied(_) => Err(CleanupError::Conflict),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn register_job(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        job_id: JobId,
        subject: SubjectDigest,
        state_value: ObservedJobState,
        active_execution: Option<ActiveExecution>,
        workspace_handle: Option<WorkspaceHandle>,
    ) -> Result<(), CleanupError> {
        let active_shape = state_value == ObservedJobState::Active
            && active_execution.is_some()
            && workspace_handle.is_some();
        let inactive_shape = state_value != ObservedJobState::Active
            && active_execution.is_none()
            && workspace_handle.is_none();
        if !active_shape && !inactive_shape {
            return Err(CleanupError::InvalidRequest);
        }
        let mut store = self.lock()?;
        let roles = store
            .project_acl
            .get(&(tenant_id, project_id))
            .ok_or(CleanupError::NotFound)?;
        if !roles.contains_key(&subject) {
            return Err(CleanupError::AccessDenied);
        }
        match store.jobs.entry((tenant_id, project_id, job_id)) {
            Entry::Vacant(entry) => {
                entry.insert(JobProjection {
                    subject,
                    state: state_value,
                    effect_phase: ExternalEffectPhase::Prepared,
                    active_execution,
                    workspace_handle,
                });
                Ok(())
            }
            Entry::Occupied(_) => Err(CleanupError::Conflict),
        }
    }

    pub fn request_cancellation(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        cancellation_id: CancellationId,
    ) -> Result<CancellationState, CleanupError> {
        let mut store = self.lock()?;
        require_editor(&store, context, project_id)?;
        let key = (context.tenant_id, project_id, job_id);
        if let Some(existing) = store.cancellations.get(&key) {
            if existing.cancellation_id == cancellation_id && existing.subject == context.subject {
                return Ok(existing.state);
            }
            return Err(CleanupError::Conflict);
        }
        let job = store.jobs.get_mut(&key).ok_or(CleanupError::NotFound)?;
        if job.subject != context.subject {
            return Err(CleanupError::AccessDenied);
        }
        let (state_value, resolved_at) = match job.state {
            ObservedJobState::Queued => {
                job.state = ObservedJobState::Cancelled;
                (CancellationState::Cancelled, Some(context.now_unix_seconds))
            }
            ObservedJobState::Active => (CancellationState::Requested, None),
            ObservedJobState::OutcomeUnknown => (
                CancellationState::OutcomeUnknown,
                Some(context.now_unix_seconds),
            ),
            ObservedJobState::Cancelled => {
                (CancellationState::Cancelled, Some(context.now_unix_seconds))
            }
            ObservedJobState::Succeeded | ObservedJobState::Failed => {
                (CancellationState::TooLate, Some(context.now_unix_seconds))
            }
        };
        store.cancellations.insert(
            key,
            CancellationRecord {
                cancellation_id,
                subject: context.subject,
                state: state_value,
                requested_at_unix_seconds: context.now_unix_seconds,
                resolved_at_unix_seconds: resolved_at,
            },
        );
        Ok(state_value)
    }

    pub fn start_external_effect(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        execution: &ActiveExecution,
    ) -> Result<(), CleanupError> {
        self.advance_effect(
            context,
            project_id,
            job_id,
            execution,
            ExternalEffectPhase::Prepared,
            ExternalEffectPhase::Started,
        )
    }

    pub fn commit_external_effect(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        execution: &ActiveExecution,
    ) -> Result<(), CleanupError> {
        self.advance_effect(
            context,
            project_id,
            job_id,
            execution,
            ExternalEffectPhase::Started,
            ExternalEffectPhase::Committed,
        )
    }

    fn advance_effect(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        execution: &ActiveExecution,
        expected: ExternalEffectPhase,
        next: ExternalEffectPhase,
    ) -> Result<(), CleanupError> {
        let mut store = self.lock()?;
        require_editor(&store, context, project_id)?;
        let job = store
            .jobs
            .get_mut(&(context.tenant_id, project_id, job_id))
            .ok_or(CleanupError::NotFound)?;
        require_live_execution(job, context, execution)?;
        if job.effect_phase != expected {
            return Err(CleanupError::Conflict);
        }
        job.effect_phase = next;
        Ok(())
    }

    pub fn finalize_cancellation_at_safe_point(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        execution: &ActiveExecution,
        cleanup_task_id: CleanupTaskId,
    ) -> Result<CancellationState, CleanupError> {
        let mut store = self.lock()?;
        require_editor(&store, context, project_id)?;
        let key = (context.tenant_id, project_id, job_id);
        let cancellation = store
            .cancellations
            .get(&key)
            .cloned()
            .ok_or(CleanupError::NotFound)?;
        if cancellation.state != CancellationState::Requested
            || cancellation.subject != context.subject
        {
            return Err(CleanupError::Conflict);
        }
        let job = store
            .jobs
            .get(&key)
            .cloned()
            .ok_or(CleanupError::NotFound)?;
        require_live_execution(&job, context, execution)?;
        let outcome = match job.effect_phase {
            ExternalEffectPhase::Prepared => CancellationState::Cancelled,
            ExternalEffectPhase::Started => CancellationState::OutcomeUnknown,
            ExternalEffectPhase::Committed => CancellationState::TooLate,
        };
        if outcome != CancellationState::TooLate {
            let handle = job.workspace_handle.ok_or(CleanupError::Conflict)?;
            let target = CleanupTarget::Workspace {
                handle,
                execution_id: execution.execution_id,
                attempt_no: execution.attempt_no,
                fencing_token: execution.fencing_token,
            };
            insert_task(
                &mut store,
                context.tenant_id,
                project_id,
                job_id,
                cleanup_task_id,
                target,
            )?;
        }
        let job = store.jobs.get_mut(&key).ok_or(CleanupError::NotFound)?;
        match outcome {
            CancellationState::Cancelled => job.state = ObservedJobState::Cancelled,
            CancellationState::OutcomeUnknown => job.state = ObservedJobState::OutcomeUnknown,
            CancellationState::TooLate => job.state = ObservedJobState::Succeeded,
            CancellationState::Requested => return Err(CleanupError::Conflict),
        }
        job.active_execution = None;
        job.workspace_handle = None;
        let record = store
            .cancellations
            .get_mut(&key)
            .ok_or(CleanupError::NotFound)?;
        record.state = outcome;
        record.resolved_at_unix_seconds = Some(context.now_unix_seconds);
        Ok(outcome)
    }

    pub fn register_artifact_projection(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        content_sha256: ContentDigest,
        artifact_kind: ArtifactKind,
        referenced: bool,
    ) -> Result<(), CleanupError> {
        let mut store = self.lock()?;
        match store.artifacts.entry((tenant_id, artifact_id)) {
            Entry::Vacant(entry) => {
                entry.insert(ArtifactProjection {
                    content_sha256,
                    artifact_kind,
                    referenced,
                });
                Ok(())
            }
            Entry::Occupied(_) => Err(CleanupError::Conflict),
        }
    }

    pub fn queue_orphan_artifact(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        task_id: CleanupTaskId,
        artifact_id: ArtifactId,
    ) -> Result<CleanupTask, CleanupError> {
        let mut store = self.lock()?;
        require_editor(&store, context, project_id)?;
        if !store
            .jobs
            .contains_key(&(context.tenant_id, project_id, job_id))
        {
            return Err(CleanupError::NotFound);
        }
        let artifact = store
            .artifacts
            .get(&(context.tenant_id, artifact_id))
            .copied()
            .ok_or(CleanupError::NotFound)?;
        if artifact.artifact_kind == ArtifactKind::Source {
            return Err(CleanupError::SourceArtifactProtected);
        }
        if artifact.referenced {
            return Err(CleanupError::TargetReferenced);
        }
        insert_task(
            &mut store,
            context.tenant_id,
            project_id,
            job_id,
            task_id,
            CleanupTarget::OrphanArtifact {
                artifact_id,
                content_sha256: artifact.content_sha256,
                artifact_kind: artifact.artifact_kind,
            },
        )
    }

    pub fn set_artifact_referenced(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        referenced: bool,
    ) -> Result<(), CleanupError> {
        let mut store = self.lock()?;
        let artifact = store
            .artifacts
            .get_mut(&(tenant_id, artifact_id))
            .ok_or(CleanupError::NotFound)?;
        artifact.referenced = referenced;
        Ok(())
    }

    pub fn claim_task(
        &self,
        context: &CleanupContext,
        worker_id: CleanupWorkerId,
        lease_seconds: u64,
    ) -> Result<CleanupLease, CleanupError> {
        if lease_seconds == 0 || lease_seconds > MAX_CLEANUP_LEASE_SECONDS {
            return Err(CleanupError::InvalidRequest);
        }
        let expires_at = context
            .now_unix_seconds
            .checked_add(lease_seconds)
            .ok_or(CleanupError::InvalidRequest)?;
        let mut store = self.lock()?;
        let candidate_key = store
            .tasks
            .iter()
            .find_map(|(key, task)| {
                if key.0 != context.tenant_id {
                    return None;
                }
                let claimable = task.state == CleanupState::Pending
                    || (task.state == CleanupState::Leased
                        && task.active_lease.as_ref().is_some_and(|lease| {
                            lease.expires_at_unix_seconds <= context.now_unix_seconds
                        }));
                claimable.then_some(*key)
            })
            .ok_or(CleanupError::NotFound)?;
        let project_id = store
            .tasks
            .get(&candidate_key)
            .ok_or(CleanupError::NotFound)?
            .project_id;
        require_editor(&store, context, project_id)?;
        let task = store
            .tasks
            .get_mut(&candidate_key)
            .ok_or(CleanupError::NotFound)?;
        if task.attempt_count >= MAX_CLEANUP_ATTEMPTS {
            task.state = CleanupState::FailedTerminal;
            task.active_lease = None;
            return Err(CleanupError::RetryExhausted);
        }
        let attempt_no = task
            .attempt_count
            .checked_add(1)
            .ok_or(CleanupError::RetryExhausted)?;
        let lease = CleanupLease {
            task_id: task.task_id,
            worker_id,
            attempt_no,
            fencing_token: u64::from(attempt_no),
            issued_at_unix_seconds: context.now_unix_seconds,
            expires_at_unix_seconds: expires_at,
        };
        task.attempt_count = attempt_no;
        task.state = CleanupState::Leased;
        task.active_lease = Some(lease.clone());
        Ok(lease)
    }

    fn target_for_execution(
        &self,
        context: &CleanupContext,
        lease: &CleanupLease,
    ) -> Result<CleanupTarget, CleanupError> {
        let store = self.lock()?;
        let task = store
            .tasks
            .get(&(context.tenant_id, lease.task_id))
            .ok_or(CleanupError::NotFound)?;
        require_editor(&store, context, task.project_id)?;
        require_live_cleanup_lease(task, context, lease)?;
        recheck_orphan_projection(&store, context.tenant_id, &task.target)?;
        Ok(task.target.clone())
    }

    fn complete_task(
        &self,
        context: &CleanupContext,
        lease: &CleanupLease,
        outcome: CleanupOutcome,
    ) -> Result<CleanupReceipt, CleanupError> {
        let mut store = self.lock()?;
        let task = store
            .tasks
            .get(&(context.tenant_id, lease.task_id))
            .cloned()
            .ok_or(CleanupError::NotFound)?;
        require_editor(&store, context, task.project_id)?;
        require_live_cleanup_lease(&task, context, lease)?;
        recheck_orphan_projection(&store, context.tenant_id, &task.target)?;
        let target_fingerprint = task.target.fingerprint();
        let mut proof = Vec::with_capacity(80);
        proof.extend_from_slice(target_fingerprint.as_bytes());
        proof.extend_from_slice(outcome.as_str().as_bytes());
        proof.extend_from_slice(&context.now_unix_seconds.to_be_bytes());
        let receipt = CleanupReceipt {
            task_id: task.task_id,
            target_fingerprint,
            outcome,
            proof_sha256: ContentDigest::of(&proof),
            completed_at_unix_seconds: context.now_unix_seconds,
        };
        let stored = store
            .tasks
            .get_mut(&(context.tenant_id, lease.task_id))
            .ok_or(CleanupError::NotFound)?;
        stored.state = CleanupState::Succeeded;
        stored.active_lease = None;
        stored.receipt = Some(receipt.clone());
        Ok(receipt)
    }

    pub fn get_task(
        &self,
        context: &CleanupContext,
        task_id: CleanupTaskId,
    ) -> Result<CleanupTask, CleanupError> {
        let store = self.lock()?;
        let task = store
            .tasks
            .get(&(context.tenant_id, task_id))
            .ok_or(CleanupError::NotFound)?;
        require_editor(&store, context, task.project_id)?;
        Ok(task.clone())
    }

    pub fn job_state(
        &self,
        context: &CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
    ) -> Result<ObservedJobState, CleanupError> {
        let store = self.lock()?;
        require_editor(&store, context, project_id)?;
        store
            .jobs
            .get(&(context.tenant_id, project_id, job_id))
            .map(|job| job.state)
            .ok_or(CleanupError::NotFound)
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, CleanupStateStore>, CleanupError> {
        self.state
            .lock()
            .map_err(|_| CleanupError::RepositoryFailure)
    }
}

fn recheck_orphan_projection(
    store: &CleanupStateStore,
    tenant_id: TenantId,
    target: &CleanupTarget,
) -> Result<(), CleanupError> {
    let CleanupTarget::OrphanArtifact {
        artifact_id,
        content_sha256,
        artifact_kind,
    } = target
    else {
        return Ok(());
    };
    let projection = store
        .artifacts
        .get(&(tenant_id, *artifact_id))
        .ok_or(CleanupError::NotFound)?;
    if projection.artifact_kind == ArtifactKind::Source {
        return Err(CleanupError::SourceArtifactProtected);
    }
    if projection.referenced {
        return Err(CleanupError::TargetReferenced);
    }
    if projection.content_sha256 != *content_sha256 || projection.artifact_kind != *artifact_kind {
        return Err(CleanupError::Conflict);
    }
    Ok(())
}

fn insert_task(
    store: &mut CleanupStateStore,
    tenant_id: TenantId,
    project_id: ProjectId,
    job_id: JobId,
    task_id: CleanupTaskId,
    target: CleanupTarget,
) -> Result<CleanupTask, CleanupError> {
    let fingerprint = target.fingerprint();
    if store.tasks.contains_key(&(tenant_id, task_id))
        || store.task_fingerprints.contains(&(tenant_id, fingerprint))
    {
        return Err(CleanupError::Conflict);
    }
    let task = CleanupTask {
        task_id,
        project_id,
        job_id,
        target,
        state: CleanupState::Pending,
        attempt_count: 0,
        active_lease: None,
        receipt: None,
    };
    store.task_fingerprints.insert((tenant_id, fingerprint));
    store.tasks.insert((tenant_id, task_id), task.clone());
    Ok(task)
}

fn require_editor(
    store: &CleanupStateStore,
    context: &CleanupContext,
    project_id: ProjectId,
) -> Result<(), CleanupError> {
    let role = store
        .project_acl
        .get(&(context.tenant_id, project_id))
        .and_then(|roles| roles.get(&context.subject))
        .copied()
        .ok_or(CleanupError::NotFound)?;
    if role.can_mutate() {
        Ok(())
    } else {
        Err(CleanupError::AccessDenied)
    }
}

fn require_live_execution(
    job: &JobProjection,
    context: &CleanupContext,
    execution: &ActiveExecution,
) -> Result<(), CleanupError> {
    if job.subject != context.subject
        || job.state != ObservedJobState::Active
        || job.active_execution.as_ref() != Some(execution)
        || context.now_unix_seconds >= execution.lease_expires_at_unix_seconds
    {
        return Err(CleanupError::StaleLease);
    }
    Ok(())
}

fn require_live_cleanup_lease(
    task: &CleanupTask,
    context: &CleanupContext,
    lease: &CleanupLease,
) -> Result<(), CleanupError> {
    if task.state != CleanupState::Leased
        || task.active_lease.as_ref() != Some(lease)
        || context.now_unix_seconds < lease.issued_at_unix_seconds
        || context.now_unix_seconds >= lease.expires_at_unix_seconds
    {
        return Err(CleanupError::StaleLease);
    }
    Ok(())
}

#[derive(Clone, Debug)]
struct WorkspaceLocation {
    staging_relative: PathBuf,
}

#[derive(Clone, Debug)]
struct OrphanLocation {
    output_relative: PathBuf,
    quarantine_relative: PathBuf,
}

#[derive(Default)]
struct TargetLocations {
    workspaces: BTreeMap<WorkspaceHandle, WorkspaceLocation>,
    orphans: BTreeMap<ArtifactId, OrphanLocation>,
}

#[derive(Clone)]
pub struct LocalCleanupTargets {
    workspace: SecureWorkspace,
    locations: Arc<Mutex<TargetLocations>>,
}

impl fmt::Debug for LocalCleanupTargets {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalCleanupTargets")
            .finish_non_exhaustive()
    }
}

impl LocalCleanupTargets {
    #[must_use]
    pub fn new(workspace: SecureWorkspace) -> Self {
        Self {
            workspace,
            locations: Arc::new(Mutex::new(TargetLocations::default())),
        }
    }

    pub fn register_workspace(
        &self,
        handle: WorkspaceHandle,
        staging_relative: PathBuf,
    ) -> Result<(), CleanupError> {
        validate_internal_relative(&staging_relative)?;
        let mut locations = self.lock()?;
        match locations.workspaces.entry(handle) {
            Entry::Vacant(entry) => {
                entry.insert(WorkspaceLocation { staging_relative });
                Ok(())
            }
            Entry::Occupied(_) => Err(CleanupError::Conflict),
        }
    }

    pub fn register_orphan(
        &self,
        artifact_id: ArtifactId,
        output_relative: PathBuf,
        quarantine_relative: PathBuf,
    ) -> Result<(), CleanupError> {
        validate_internal_relative(&output_relative)?;
        validate_internal_relative(&quarantine_relative)?;
        let mut locations = self.lock()?;
        match locations.orphans.entry(artifact_id) {
            Entry::Vacant(entry) => {
                entry.insert(OrphanLocation {
                    output_relative,
                    quarantine_relative,
                });
                Ok(())
            }
            Entry::Occupied(_) => Err(CleanupError::Conflict),
        }
    }

    fn execute(&self, target: &CleanupTarget) -> Result<CleanupOutcome, CleanupError> {
        match target {
            CleanupTarget::Workspace { handle, .. } => {
                let relative = self
                    .lock()?
                    .workspaces
                    .get(handle)
                    .cloned()
                    .ok_or(CleanupError::NotFound)?
                    .staging_relative;
                match self.workspace.cleanup_staging(&relative) {
                    Ok(()) => Ok(CleanupOutcome::WorkspaceRemoved),
                    Err(WorkspaceError::Io(error))
                        if error.kind() == std::io::ErrorKind::NotFound =>
                    {
                        Ok(CleanupOutcome::WorkspaceAlreadyAbsent)
                    }
                    Err(_) => Err(CleanupError::TargetExecutionFailed),
                }
            }
            CleanupTarget::OrphanArtifact {
                artifact_id,
                content_sha256,
                artifact_kind,
            } => {
                if *artifact_kind == ArtifactKind::Source {
                    return Err(CleanupError::SourceArtifactProtected);
                }
                let location = self
                    .lock()?
                    .orphans
                    .get(artifact_id)
                    .cloned()
                    .ok_or(CleanupError::NotFound)?;
                match self.verify_output(&location.output_relative, *content_sha256) {
                    Ok(()) => {}
                    Err(CleanupError::NotFound) => {
                        self.verify_quarantine(&location.quarantine_relative, *content_sha256)?;
                        return Ok(CleanupOutcome::ArtifactAlreadyQuarantined);
                    }
                    Err(error) => return Err(error),
                }
                match self.verify_quarantine(&location.quarantine_relative, *content_sha256) {
                    Ok(()) => {
                        self.workspace
                            .complete_incomplete_quarantine(
                                &location.output_relative,
                                &location.quarantine_relative,
                                content_sha256.as_bytes(),
                                MAX_ORPHAN_BYTES,
                            )
                            .map_err(|_| CleanupError::TargetExecutionFailed)?;
                        return Ok(CleanupOutcome::ArtifactAlreadyQuarantined);
                    }
                    Err(CleanupError::NotFound) => {}
                    Err(error) => return Err(error),
                }
                match self
                    .workspace
                    .quarantine_published(&location.output_relative, &location.quarantine_relative)
                {
                    Ok(()) => {
                        self.verify_quarantine(&location.quarantine_relative, *content_sha256)?;
                        Ok(CleanupOutcome::ArtifactQuarantined)
                    }
                    Err(_) => Err(CleanupError::TargetExecutionFailed),
                }
            }
        }
    }

    fn verify_output(
        &self,
        relative: &Path,
        expected_sha256: ContentDigest,
    ) -> Result<(), CleanupError> {
        let reader = match self.workspace.open_output(relative) {
            Ok(reader) => reader,
            Err(WorkspaceError::Io(error)) if error.kind() == std::io::ErrorKind::NotFound => {
                return Err(CleanupError::NotFound);
            }
            Err(_) => return Err(CleanupError::TargetExecutionFailed),
        };
        verify_bounded_digest(reader, expected_sha256)
    }

    fn verify_quarantine(
        &self,
        relative: &Path,
        expected_sha256: ContentDigest,
    ) -> Result<(), CleanupError> {
        let reader = self
            .workspace
            .open_quarantined(relative)
            .map_err(|error| match error {
                WorkspaceError::Io(error) if error.kind() == std::io::ErrorKind::NotFound => {
                    CleanupError::NotFound
                }
                _ => CleanupError::TargetExecutionFailed,
            })?;
        verify_bounded_digest(reader, expected_sha256)
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, TargetLocations>, CleanupError> {
        self.locations
            .lock()
            .map_err(|_| CleanupError::RepositoryFailure)
    }
}

fn verify_bounded_digest(
    mut reader: impl std::io::Read,
    expected_sha256: ContentDigest,
) -> Result<(), CleanupError> {
    let mut bounded = Vec::new();
    reader
        .by_ref()
        .take(MAX_ORPHAN_BYTES.saturating_add(1))
        .read_to_end(&mut bounded)
        .map_err(|_| CleanupError::TargetExecutionFailed)?;
    let observed_len =
        u64::try_from(bounded.len()).map_err(|_| CleanupError::TargetExecutionFailed)?;
    if observed_len > MAX_ORPHAN_BYTES || ContentDigest::of(&bounded) != expected_sha256 {
        return Err(CleanupError::TargetExecutionFailed);
    }
    Ok(())
}

fn validate_internal_relative(path: &Path) -> Result<(), CleanupError> {
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || !path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
    {
        return Err(CleanupError::InvalidRequest);
    }
    Ok(())
}

#[derive(Clone, Debug)]
pub struct CleanupWorker {
    repository: CleanupRepository,
    targets: LocalCleanupTargets,
}

impl CleanupWorker {
    #[must_use]
    pub fn new(repository: CleanupRepository, targets: LocalCleanupTargets) -> Self {
        Self {
            repository,
            targets,
        }
    }

    pub fn execute(
        &self,
        context: &CleanupContext,
        lease: &CleanupLease,
        fault: FaultPoint,
    ) -> Result<CleanupReceipt, CleanupError> {
        let target = self.repository.target_for_execution(context, lease)?;
        if fault == FaultPoint::BeforeExternalCleanup {
            return Err(CleanupError::InjectedFault);
        }
        let outcome = self.targets.execute(&target)?;
        if fault == FaultPoint::AfterExternalCleanupBeforeReceipt {
            return Err(CleanupError::InjectedFault);
        }
        self.repository.complete_task(context, lease, outcome)
    }
}

fn main() {
    println!("p14-cleanup-worker core-v1; durable adapter required");
}

#[cfg(test)]
mod tests {
    use std::io::Read as _;
    use std::path::Path;

    use artifact_service::{ArtifactId, ArtifactKind, ContentDigest, SubjectDigest, TenantId};
    use hwpx_agent_foundation::workdir::SecureWorkspace;
    use tempfile::tempdir;
    use uuid::Uuid;

    use super::{
        ActiveExecution, CancellationId, CancellationState, CleanupContext, CleanupError,
        CleanupOutcome, CleanupRepository, CleanupState, CleanupTaskId, CleanupWorker,
        CleanupWorkerId, ExecutionId, FaultPoint, JobId, LocalCleanupTargets, ObservedJobState,
        ProjectId, ProjectRole, WorkspaceHandle,
    };

    #[derive(Clone)]
    struct Fixture {
        repository: CleanupRepository,
        targets: LocalCleanupTargets,
        context: CleanupContext,
        project_id: ProjectId,
        job_id: JobId,
        execution: ActiveExecution,
        workspace_handle: WorkspaceHandle,
    }

    fn tenant(value: u128) -> TenantId {
        TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn subject(value: &str) -> SubjectDigest {
        SubjectDigest::from_authenticated_subject(value)
            .unwrap_or_else(|error| panic!("subject: {error}"))
    }

    fn id<T>(value: u128, make: impl FnOnce(Uuid) -> Option<T>) -> T {
        make(Uuid::from_u128(value)).unwrap_or_else(|| panic!("non-nil id"))
    }

    fn artifact(value: u128) -> ArtifactId {
        ArtifactId::parse(&format!("art_{value:032x}"))
            .unwrap_or_else(|error| panic!("artifact: {error}"))
    }

    fn fixture(state: ObservedJobState) -> (Fixture, tempfile::TempDir) {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace: {error}"));
        let targets = LocalCleanupTargets::new(secure.clone());
        let repository = CleanupRepository::default();
        let tenant_id = tenant(1);
        let owner = subject("p14-cleanup-owner");
        let context = CleanupContext::new(tenant_id, owner, 100);
        let project_id = id(2, ProjectId::from_uuid);
        let job_id = id(3, JobId::from_uuid);
        repository
            .provision_project(tenant_id, project_id, [(owner, ProjectRole::Owner)])
            .unwrap_or_else(|error| panic!("project: {error}"));
        let execution = ActiveExecution::new(id(4, ExecutionId::from_uuid), 1, 1, 200)
            .unwrap_or_else(|error| panic!("execution: {error}"));
        let workspace_handle = id(5, WorkspaceHandle::from_uuid);
        let (active, handle) = if state == ObservedJobState::Active {
            (Some(execution.clone()), Some(workspace_handle))
        } else {
            (None, None)
        };
        repository
            .register_job(tenant_id, project_id, job_id, owner, state, active, handle)
            .unwrap_or_else(|error| panic!("job: {error}"));
        (
            Fixture {
                repository,
                targets,
                context,
                project_id,
                job_id,
                execution,
                workspace_handle,
            },
            temporary,
        )
    }

    #[test]
    fn queued_cancel_is_immediate_and_exact_replay_only() {
        let (fixture, _temporary) = fixture(ObservedJobState::Queued);
        let cancellation_id = id(10, CancellationId::from_uuid);
        assert_eq!(
            fixture.repository.request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                cancellation_id,
            ),
            Ok(CancellationState::Cancelled)
        );
        assert_eq!(
            fixture.repository.request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                cancellation_id,
            ),
            Ok(CancellationState::Cancelled)
        );
        assert_eq!(
            fixture.repository.request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(11, CancellationId::from_uuid),
            ),
            Err(CleanupError::Conflict)
        );
        assert_eq!(
            fixture
                .repository
                .job_state(&fixture.context, fixture.project_id, fixture.job_id,),
            Ok(ObservedJobState::Cancelled)
        );
    }

    #[test]
    fn prepared_cancel_cleans_only_the_exact_workspace() {
        let (fixture, temporary) = fixture(ObservedJobState::Active);
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace reopen: {error}"));
        secure
            .stage_bytes(Path::new("job-active/temp.bin"), b"temporary")
            .unwrap_or_else(|error| panic!("stage temp: {error}"));
        let published_stage = secure
            .stage_bytes(Path::new("job-published/output.bin"), b"published")
            .unwrap_or_else(|error| panic!("stage output: {error}"));
        let published = secure
            .publish(&published_stage, Path::new("stable/output.bin"))
            .unwrap_or_else(|error| panic!("publish: {error}"));
        fixture
            .targets
            .register_workspace(
                fixture.workspace_handle,
                Path::new("job-active").to_path_buf(),
            )
            .unwrap_or_else(|error| panic!("register workspace: {error}"));
        assert_eq!(
            fixture.repository.request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(12, CancellationId::from_uuid),
            ),
            Ok(CancellationState::Requested)
        );
        let task_id = id(13, CleanupTaskId::from_uuid);
        assert_eq!(
            fixture.repository.finalize_cancellation_at_safe_point(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
                task_id,
            ),
            Ok(CancellationState::Cancelled)
        );
        let lease = fixture
            .repository
            .claim_task(&fixture.context, id(14, CleanupWorkerId::from_uuid), 20)
            .unwrap_or_else(|error| panic!("claim: {error}"));
        let receipt = CleanupWorker::new(fixture.repository.clone(), fixture.targets.clone())
            .execute(&fixture.context, &lease, FaultPoint::None)
            .unwrap_or_else(|error| panic!("execute: {error}"));
        assert_eq!(receipt.outcome(), CleanupOutcome::WorkspaceRemoved);
        assert!(
            !temporary
                .path()
                .join("workspace/staging/job-active")
                .exists()
        );
        assert_eq!(
            std::fs::read(published).unwrap_or_else(|error| panic!("read output: {error}")),
            b"published"
        );
        assert_eq!(
            fixture
                .repository
                .get_task(&fixture.context, task_id)
                .unwrap_or_else(|error| panic!("task: {error}"))
                .state(),
            CleanupState::Succeeded
        );
    }

    #[test]
    fn started_effect_cancellation_is_unknown_not_false_success() {
        let (fixture, _temporary) = fixture(ObservedJobState::Active);
        fixture
            .repository
            .start_external_effect(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
            )
            .unwrap_or_else(|error| panic!("start effect: {error}"));
        fixture
            .repository
            .request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(20, CancellationId::from_uuid),
            )
            .unwrap_or_else(|error| panic!("cancel: {error}"));
        assert_eq!(
            fixture.repository.finalize_cancellation_at_safe_point(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
                id(21, CleanupTaskId::from_uuid),
            ),
            Ok(CancellationState::OutcomeUnknown)
        );
        assert_eq!(
            fixture
                .repository
                .job_state(&fixture.context, fixture.project_id, fixture.job_id,),
            Ok(ObservedJobState::OutcomeUnknown)
        );
    }

    #[test]
    fn committed_effect_cancellation_is_too_late_without_cleanup() {
        let (fixture, _temporary) = fixture(ObservedJobState::Active);
        fixture
            .repository
            .start_external_effect(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
            )
            .and_then(|()| {
                fixture.repository.commit_external_effect(
                    &fixture.context,
                    fixture.project_id,
                    fixture.job_id,
                    &fixture.execution,
                )
            })
            .unwrap_or_else(|error| panic!("commit effect: {error}"));
        fixture
            .repository
            .request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(30, CancellationId::from_uuid),
            )
            .unwrap_or_else(|error| panic!("cancel: {error}"));
        assert_eq!(
            fixture.repository.finalize_cancellation_at_safe_point(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
                id(31, CleanupTaskId::from_uuid),
            ),
            Ok(CancellationState::TooLate)
        );
        assert_eq!(
            fixture
                .repository
                .claim_task(&fixture.context, id(32, CleanupWorkerId::from_uuid), 10,),
            Err(CleanupError::NotFound)
        );
    }

    #[test]
    #[allow(
        clippy::too_many_lines,
        reason = "one end-to-end safety test keeps source, referenced, and orphan cases in one fixture"
    )]
    fn orphan_is_quarantined_but_source_and_referenced_artifacts_are_protected() {
        let (fixture, temporary) = fixture(ObservedJobState::Failed);
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace reopen: {error}"));
        let bytes = b"uncommitted complete output";
        let staged = secure
            .stage_bytes(Path::new("orphan-stage/result.bin"), bytes)
            .unwrap_or_else(|error| panic!("stage: {error}"));
        secure
            .publish(&staged, Path::new("orphan/result.bin"))
            .unwrap_or_else(|error| panic!("publish: {error}"));
        let artifact_id = artifact(40);
        fixture
            .targets
            .register_orphan(
                artifact_id,
                Path::new("orphan/result.bin").to_path_buf(),
                Path::new("orphans/result.bin").to_path_buf(),
            )
            .unwrap_or_else(|error| panic!("register orphan: {error}"));
        fixture
            .repository
            .register_artifact_projection(
                fixture.context.tenant_id(),
                artifact(41),
                ContentDigest::of(b"source"),
                ArtifactKind::Source,
                false,
            )
            .unwrap_or_else(|error| panic!("register source: {error}"));
        assert_eq!(
            fixture.repository.queue_orphan_artifact(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(41, CleanupTaskId::from_uuid),
                artifact(41),
            ),
            Err(CleanupError::SourceArtifactProtected)
        );
        fixture
            .repository
            .register_artifact_projection(
                fixture.context.tenant_id(),
                artifact(42),
                ContentDigest::of(b"referenced"),
                ArtifactKind::Result,
                false,
            )
            .and_then(|()| {
                fixture.repository.set_artifact_referenced(
                    fixture.context.tenant_id(),
                    artifact(42),
                    true,
                )
            })
            .unwrap_or_else(|error| panic!("reference: {error}"));
        assert_eq!(
            fixture.repository.queue_orphan_artifact(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(42, CleanupTaskId::from_uuid),
                artifact(42),
            ),
            Err(CleanupError::TargetReferenced)
        );
        fixture
            .repository
            .register_artifact_projection(
                fixture.context.tenant_id(),
                artifact_id,
                ContentDigest::of(bytes),
                ArtifactKind::Result,
                false,
            )
            .unwrap_or_else(|error| panic!("register artifact: {error}"));
        let task_id = id(43, CleanupTaskId::from_uuid);
        fixture
            .repository
            .queue_orphan_artifact(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                task_id,
                artifact_id,
            )
            .unwrap_or_else(|error| panic!("queue orphan: {error}"));
        let lease = fixture
            .repository
            .claim_task(&fixture.context, id(44, CleanupWorkerId::from_uuid), 20)
            .unwrap_or_else(|error| panic!("claim: {error}"));
        let receipt = CleanupWorker::new(fixture.repository.clone(), fixture.targets.clone())
            .execute(&fixture.context, &lease, FaultPoint::None)
            .unwrap_or_else(|error| panic!("cleanup: {error}"));
        assert_eq!(receipt.outcome(), CleanupOutcome::ArtifactQuarantined);
        let mut reader = secure
            .open_quarantined(Path::new("orphans/result.bin"))
            .unwrap_or_else(|error| panic!("open quarantine: {error}"));
        let mut observed = Vec::new();
        reader
            .read_to_end(&mut observed)
            .unwrap_or_else(|error| panic!("read quarantine: {error}"));
        assert_eq!(observed, bytes);
    }

    #[test]
    fn reference_race_fails_before_external_cleanup() {
        let (fixture, temporary) = fixture(ObservedJobState::Failed);
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace reopen: {error}"));
        let artifact_id = artifact(50);
        let bytes = b"becomes referenced";
        let staged = secure
            .stage_bytes(Path::new("race-stage/result.bin"), bytes)
            .unwrap_or_else(|error| panic!("stage: {error}"));
        let output = secure
            .publish(&staged, Path::new("race/result.bin"))
            .unwrap_or_else(|error| panic!("publish: {error}"));
        fixture
            .targets
            .register_orphan(
                artifact_id,
                Path::new("race/result.bin").to_path_buf(),
                Path::new("orphans/race.bin").to_path_buf(),
            )
            .unwrap_or_else(|error| panic!("register: {error}"));
        fixture
            .repository
            .register_artifact_projection(
                fixture.context.tenant_id(),
                artifact_id,
                ContentDigest::of(bytes),
                ArtifactKind::Result,
                false,
            )
            .unwrap_or_else(|error| panic!("register projection: {error}"));
        fixture
            .repository
            .queue_orphan_artifact(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(51, CleanupTaskId::from_uuid),
                artifact_id,
            )
            .unwrap_or_else(|error| panic!("queue: {error}"));
        let lease = fixture
            .repository
            .claim_task(&fixture.context, id(52, CleanupWorkerId::from_uuid), 20)
            .unwrap_or_else(|error| panic!("claim: {error}"));
        fixture
            .repository
            .set_artifact_referenced(fixture.context.tenant_id(), artifact_id, true)
            .unwrap_or_else(|error| panic!("reference: {error}"));
        assert_eq!(
            CleanupWorker::new(fixture.repository, fixture.targets).execute(
                &fixture.context,
                &lease,
                FaultPoint::None,
            ),
            Err(CleanupError::TargetReferenced)
        );
        assert_eq!(
            std::fs::read(output).unwrap_or_else(|error| panic!("read output: {error}")),
            bytes
        );
    }

    #[test]
    fn crash_after_cleanup_replays_as_absent_with_one_receipt() {
        let (fixture, temporary) = fixture(ObservedJobState::Active);
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace reopen: {error}"));
        secure
            .stage_bytes(Path::new("crash-work/temp.bin"), b"temporary")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        fixture
            .targets
            .register_workspace(
                fixture.workspace_handle,
                Path::new("crash-work").to_path_buf(),
            )
            .unwrap_or_else(|error| panic!("register: {error}"));
        fixture
            .repository
            .request_cancellation(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(60, CancellationId::from_uuid),
            )
            .and_then(|_| {
                fixture.repository.finalize_cancellation_at_safe_point(
                    &fixture.context,
                    fixture.project_id,
                    fixture.job_id,
                    &fixture.execution,
                    id(61, CleanupTaskId::from_uuid),
                )
            })
            .unwrap_or_else(|error| panic!("cancel: {error}"));
        let lease_one = fixture
            .repository
            .claim_task(&fixture.context, id(62, CleanupWorkerId::from_uuid), 5)
            .unwrap_or_else(|error| panic!("claim one: {error}"));
        let worker = CleanupWorker::new(fixture.repository.clone(), fixture.targets);
        assert_eq!(
            worker.execute(
                &fixture.context,
                &lease_one,
                FaultPoint::AfterExternalCleanupBeforeReceipt,
            ),
            Err(CleanupError::InjectedFault)
        );
        let retry_context =
            CleanupContext::new(fixture.context.tenant_id(), fixture.context.subject, 106);
        let lease_two = fixture
            .repository
            .claim_task(&retry_context, id(63, CleanupWorkerId::from_uuid), 5)
            .unwrap_or_else(|error| panic!("claim two: {error}"));
        assert_eq!(lease_two.attempt_no(), 2);
        let receipt = worker
            .execute(&retry_context, &lease_two, FaultPoint::None)
            .unwrap_or_else(|error| panic!("retry: {error}"));
        assert_eq!(receipt.outcome(), CleanupOutcome::WorkspaceAlreadyAbsent);
        assert_eq!(
            worker.execute(&retry_context, &lease_one, FaultPoint::None),
            Err(CleanupError::StaleLease)
        );
    }

    #[test]
    fn interrupted_quarantine_move_is_completed_only_for_the_same_file() {
        let (fixture, temporary) = fixture(ObservedJobState::Active);
        let secure = SecureWorkspace::create(temporary.path().join("workspace"))
            .unwrap_or_else(|error| panic!("workspace reopen: {error}"));
        let artifact_id = artifact(62);
        let content = b"orphan ciphertext";
        let content_sha256 = ContentDigest::of(content);
        let output_relative = Path::new("generated/interrupted.bin");
        let quarantine_relative = Path::new("orphans/interrupted.bin");
        let staged = secure
            .stage_bytes(Path::new("interrupted.bin"), content)
            .unwrap_or_else(|error| panic!("stage: {error}"));
        let published = secure
            .publish(&staged, output_relative)
            .unwrap_or_else(|error| panic!("publish: {error}"));
        let quarantine = temporary
            .path()
            .join("workspace/quarantine")
            .join(quarantine_relative);
        std::fs::create_dir_all(
            quarantine
                .parent()
                .unwrap_or_else(|| panic!("quarantine parent")),
        )
        .unwrap_or_else(|error| panic!("create quarantine parent: {error}"));
        std::fs::hard_link(&published, &quarantine)
            .unwrap_or_else(|error| panic!("create interrupted link: {error}"));
        fixture
            .repository
            .register_artifact_projection(
                fixture.context.tenant_id(),
                artifact_id,
                content_sha256,
                ArtifactKind::Result,
                false,
            )
            .unwrap_or_else(|error| panic!("register: {error}"));
        fixture
            .targets
            .register_orphan(
                artifact_id,
                output_relative.to_path_buf(),
                quarantine_relative.to_path_buf(),
            )
            .unwrap_or_else(|error| panic!("register location: {error}"));
        fixture
            .repository
            .queue_orphan_artifact(
                &fixture.context,
                fixture.project_id,
                fixture.job_id,
                id(63, CleanupTaskId::from_uuid),
                artifact_id,
            )
            .unwrap_or_else(|error| panic!("queue: {error}"));
        let lease = fixture
            .repository
            .claim_task(&fixture.context, id(64, CleanupWorkerId::from_uuid), 30)
            .unwrap_or_else(|error| panic!("claim: {error}"));

        let receipt = CleanupWorker::new(fixture.repository.clone(), fixture.targets.clone())
            .execute(&fixture.context, &lease, FaultPoint::None)
            .unwrap_or_else(|error| panic!("execute: {error}"));

        assert_eq!(receipt.outcome, CleanupOutcome::ArtifactAlreadyQuarantined);
        assert!(secure.open_output(output_relative).is_err());
        assert!(secure.open_quarantined(quarantine_relative).is_ok());
    }

    #[test]
    fn cross_tenant_reader_and_expired_execution_are_denied() {
        let (fixture, _temporary) = fixture(ObservedJobState::Active);
        let other_context = CleanupContext::new(tenant(99), subject("other"), 100);
        assert_eq!(
            fixture.repository.request_cancellation(
                &other_context,
                fixture.project_id,
                fixture.job_id,
                id(70, CancellationId::from_uuid),
            ),
            Err(CleanupError::NotFound)
        );
        let late_context =
            CleanupContext::new(fixture.context.tenant_id(), fixture.context.subject, 200);
        assert_eq!(
            fixture.repository.start_external_effect(
                &late_context,
                fixture.project_id,
                fixture.job_id,
                &fixture.execution,
            ),
            Err(CleanupError::StaleLease)
        );
    }

    #[test]
    fn identifiers_bounds_and_debug_output_fail_closed() {
        assert_eq!(
            ProjectId::parse("prj_00000000000000000000000000000000"),
            Err(CleanupError::InvalidIdentifier)
        );
        assert_eq!(
            ActiveExecution::new(id(80, ExecutionId::from_uuid), 2, 1, 200),
            Err(CleanupError::InvalidRequest)
        );
        let (fixture, _temporary) = fixture(ObservedJobState::Active);
        assert_eq!(
            fixture.repository.claim_task(
                &fixture.context,
                id(81, CleanupWorkerId::from_uuid),
                301,
            ),
            Err(CleanupError::InvalidRequest)
        );
        let debug = format!("{:?}", fixture.context);
        assert!(!debug.contains("p14-cleanup-owner"));
        assert!(!format!("{:?}", fixture.execution).contains(&format!("{:032x}", 4)));
        assert!(ObservedJobState::Succeeded.is_terminal());
    }
}
