#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::collections::btree_map::Entry;
use std::fmt;
use std::sync::{Arc, Mutex};

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use job_service::{
    AgentInstanceId, ExecutionId, JobError, JobId, JobRecord, JobRepository, JobRequestContext,
    JobService, JobState, LeaseGrant, TargetProfileId,
};
use revision_service::ProjectId;
use thiserror::Error;

const MAX_WORKER_HEARTBEAT_SECONDS: u64 = 300;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum SchedulerError {
    #[error("scheduler request is invalid")]
    InvalidRequest,
    #[error("worker identity already exists")]
    DuplicateWorker,
    #[error("worker was not found")]
    WorkerNotFound,
    #[error("worker identity is stale or mismatched")]
    WorkerIdentityMismatch,
    #[error("worker is unavailable")]
    WorkerUnavailable,
    #[error("worker target profile does not match the job")]
    TargetProfileMismatch,
    #[error("worker capability set does not match the job")]
    CapabilitySetMismatch,
    #[error("job lease would outlive the worker heartbeat")]
    LeaseOutlivesWorker,
    #[error("scheduler state repository failed")]
    RepositoryFailure,
    #[error(transparent)]
    Job(#[from] JobError),
}

impl SchedulerError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidRequest => "SCHEDULER_REQUEST_INVALID",
            Self::DuplicateWorker => "SCHEDULER_WORKER_ALREADY_EXISTS",
            Self::WorkerNotFound => "SCHEDULER_WORKER_NOT_FOUND",
            Self::WorkerIdentityMismatch => "SCHEDULER_WORKER_IDENTITY_MISMATCH",
            Self::WorkerUnavailable => "SCHEDULER_WORKER_UNAVAILABLE",
            Self::TargetProfileMismatch => "SCHEDULER_TARGET_PROFILE_MISMATCH",
            Self::CapabilitySetMismatch => "SCHEDULER_CAPABILITY_SET_MISMATCH",
            Self::LeaseOutlivesWorker => "SCHEDULER_LEASE_OUTLIVES_WORKER",
            Self::RepositoryFailure => "SCHEDULER_REPOSITORY_FAILED",
            Self::Job(error) => error.code(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WorkerState {
    Ready,
    Draining,
}

#[derive(Clone, Eq, PartialEq)]
pub struct WorkerRegistration {
    tenant_id: TenantId,
    subject: SubjectDigest,
    agent_instance_id: AgentInstanceId,
    target_profile_id: TargetProfileId,
    capability_set_sha256: ContentDigest,
    state: WorkerState,
    last_heartbeat_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

impl fmt::Debug for WorkerRegistration {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WorkerRegistration")
            .field("tenant_id", &self.tenant_id)
            .field("subject", &"<redacted>")
            .field("agent_instance_id", &"<redacted>")
            .field("target_profile_id", &self.target_profile_id)
            .field("capability_set_sha256", &"<redacted>")
            .field("state", &self.state)
            .field(
                "last_heartbeat_unix_seconds",
                &self.last_heartbeat_unix_seconds,
            )
            .field("expires_at_unix_seconds", &self.expires_at_unix_seconds)
            .finish()
    }
}

impl WorkerRegistration {
    #[must_use]
    pub const fn agent_instance_id(&self) -> AgentInstanceId {
        self.agent_instance_id
    }

    #[must_use]
    pub const fn target_profile_id(&self) -> &TargetProfileId {
        &self.target_profile_id
    }

    #[must_use]
    pub const fn capability_set_sha256(&self) -> ContentDigest {
        self.capability_set_sha256
    }

    #[must_use]
    pub const fn state(&self) -> WorkerState {
        self.state
    }

    #[must_use]
    pub const fn expires_at_unix_seconds(&self) -> u64 {
        self.expires_at_unix_seconds
    }

    fn require_owner(&self, context: &JobRequestContext) -> Result<(), SchedulerError> {
        if self.tenant_id != context.tenant_id() || self.subject != context.subject() {
            return Err(SchedulerError::WorkerIdentityMismatch);
        }
        Ok(())
    }

    fn require_live(&self, context: &JobRequestContext) -> Result<(), SchedulerError> {
        self.require_owner(context)?;
        if context.now_unix_seconds() < self.last_heartbeat_unix_seconds
            || context.now_unix_seconds() >= self.expires_at_unix_seconds
        {
            return Err(SchedulerError::WorkerUnavailable);
        }
        Ok(())
    }
}

type WorkerKey = (TenantId, AgentInstanceId);

#[derive(Default)]
struct SchedulerState {
    workers: BTreeMap<WorkerKey, WorkerRegistration>,
}

#[derive(Clone)]
pub struct SchedulerService<R: JobRepository> {
    jobs: JobService<R>,
    state: Arc<Mutex<SchedulerState>>,
}

impl<R: JobRepository> fmt::Debug for SchedulerService<R> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SchedulerService")
            .finish_non_exhaustive()
    }
}

impl<R: JobRepository> SchedulerService<R> {
    #[must_use]
    pub fn new(repository: Arc<R>) -> Self {
        Self {
            jobs: JobService::new(repository),
            state: Arc::new(Mutex::new(SchedulerState::default())),
        }
    }

    /// Registers one fresh worker identity for an exact profile and capability set.
    ///
    /// # Errors
    ///
    /// Rejects duplicate identities and heartbeat windows outside five minutes.
    #[allow(clippy::too_many_arguments)]
    pub fn register_worker(
        &self,
        context: &JobRequestContext,
        agent_instance_id: AgentInstanceId,
        target_profile_id: TargetProfileId,
        capability_set_sha256: ContentDigest,
        state: WorkerState,
        expires_at_unix_seconds: u64,
    ) -> Result<WorkerRegistration, SchedulerError> {
        validate_worker_expiry(context.now_unix_seconds(), expires_at_unix_seconds)?;
        let registration = WorkerRegistration {
            tenant_id: context.tenant_id(),
            subject: context.subject(),
            agent_instance_id,
            target_profile_id,
            capability_set_sha256,
            state,
            last_heartbeat_unix_seconds: context.now_unix_seconds(),
            expires_at_unix_seconds,
        };
        let mut scheduler = self.lock()?;
        match scheduler
            .workers
            .entry((context.tenant_id(), agent_instance_id))
        {
            Entry::Vacant(entry) => {
                entry.insert(registration.clone());
                Ok(registration)
            }
            Entry::Occupied(_) => Err(SchedulerError::DuplicateWorker),
        }
    }

    /// Refreshes an existing live worker without allowing profile/capability drift.
    ///
    /// # Errors
    ///
    /// Rejects stale ownership, expired workers, identity drift and non-increasing expiry.
    #[allow(clippy::too_many_arguments)]
    pub fn heartbeat_worker(
        &self,
        context: &JobRequestContext,
        agent_instance_id: AgentInstanceId,
        target_profile_id: &TargetProfileId,
        capability_set_sha256: ContentDigest,
        state: WorkerState,
        expires_at_unix_seconds: u64,
    ) -> Result<WorkerRegistration, SchedulerError> {
        validate_worker_expiry(context.now_unix_seconds(), expires_at_unix_seconds)?;
        let mut scheduler = self.lock()?;
        let worker = scheduler
            .workers
            .get_mut(&(context.tenant_id(), agent_instance_id))
            .ok_or(SchedulerError::WorkerNotFound)?;
        worker.require_live(context)?;
        if worker.target_profile_id != *target_profile_id
            || worker.capability_set_sha256 != capability_set_sha256
        {
            return Err(SchedulerError::WorkerIdentityMismatch);
        }
        if worker.state == WorkerState::Draining && state == WorkerState::Ready {
            return Err(SchedulerError::WorkerUnavailable);
        }
        if expires_at_unix_seconds <= worker.expires_at_unix_seconds {
            return Err(SchedulerError::InvalidRequest);
        }
        worker.state = state;
        worker.last_heartbeat_unix_seconds = context.now_unix_seconds();
        worker.expires_at_unix_seconds = expires_at_unix_seconds;
        Ok(worker.clone())
    }

    /// Leases one queued job to a live, ready worker with exact profile/capability match.
    ///
    /// # Errors
    ///
    /// Rejects stale workers, mismatches and leases that outlive worker health.
    pub fn lease_job(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        agent_instance_id: AgentInstanceId,
        execution_id: ExecutionId,
        expires_at_unix_seconds: u64,
    ) -> Result<JobRecord, SchedulerError> {
        let scheduler = self.lock()?;
        let worker = scheduler
            .workers
            .get(&(context.tenant_id(), agent_instance_id))
            .ok_or(SchedulerError::WorkerNotFound)?;
        worker.require_live(context)?;
        if worker.state != WorkerState::Ready {
            return Err(SchedulerError::WorkerUnavailable);
        }
        if expires_at_unix_seconds > worker.expires_at_unix_seconds {
            return Err(SchedulerError::LeaseOutlivesWorker);
        }
        let job = self.jobs.get(context, project_id, job_id)?;
        if job.state() != JobState::Queued {
            return Err(SchedulerError::Job(JobError::InvalidTransition));
        }
        if job.spec().required_target_profile_id() != &worker.target_profile_id {
            return Err(SchedulerError::TargetProfileMismatch);
        }
        if job.spec().required_capability_set_sha256() != worker.capability_set_sha256 {
            return Err(SchedulerError::CapabilitySetMismatch);
        }
        let lease = LeaseGrant::new(
            agent_instance_id,
            execution_id,
            1,
            1,
            context.now_unix_seconds(),
            expires_at_unix_seconds,
        )?;
        Ok(self.jobs.lease(context, project_id, job_id, &lease)?)
    }

    /// Extends the current job lease after validating the same live worker identity.
    ///
    /// # Errors
    ///
    /// Rejects late/stale workers, mismatched job requirements and unbounded renewal.
    pub fn heartbeat_job(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        expires_at_unix_seconds: u64,
    ) -> Result<JobRecord, SchedulerError> {
        let scheduler = self.lock()?;
        let worker = scheduler
            .workers
            .get(&(context.tenant_id(), lease.agent_instance_id()))
            .ok_or(SchedulerError::WorkerNotFound)?;
        worker.require_live(context)?;
        if expires_at_unix_seconds > worker.expires_at_unix_seconds {
            return Err(SchedulerError::LeaseOutlivesWorker);
        }
        let job = self.jobs.get(context, project_id, job_id)?;
        if job.spec().required_target_profile_id() != &worker.target_profile_id
            || job.spec().required_capability_set_sha256() != worker.capability_set_sha256
        {
            return Err(SchedulerError::WorkerIdentityMismatch);
        }
        let renewed = lease.renewed(context.now_unix_seconds(), expires_at_unix_seconds)?;
        Ok(self
            .jobs
            .heartbeat(context, project_id, job_id, lease, &renewed)?)
    }

    /// Converts one expired active lease into deterministic terminal failure.
    ///
    /// # Errors
    ///
    /// Rejects still-live/stale leases and unqualified receipts without mutation.
    pub fn expire_job(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, SchedulerError> {
        Ok(self
            .jobs
            .expire(context, project_id, job_id, lease, receipt_artifact_id)?)
    }

    /// Reads one exact worker owned by the current tenant and subject.
    ///
    /// # Errors
    ///
    /// Returns a masked not-found for absent workers and rejects subject drift.
    pub fn get_worker(
        &self,
        context: &JobRequestContext,
        agent_instance_id: AgentInstanceId,
    ) -> Result<WorkerRegistration, SchedulerError> {
        let scheduler = self.lock()?;
        let worker = scheduler
            .workers
            .get(&(context.tenant_id(), agent_instance_id))
            .ok_or(SchedulerError::WorkerNotFound)?;
        worker.require_owner(context)?;
        Ok(worker.clone())
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, SchedulerState>, SchedulerError> {
        self.state
            .lock()
            .map_err(|_| SchedulerError::RepositoryFailure)
    }
}

fn validate_worker_expiry(now: u64, expires_at: u64) -> Result<(), SchedulerError> {
    let lifetime = expires_at
        .checked_sub(now)
        .ok_or(SchedulerError::InvalidRequest)?;
    if !(1..=MAX_WORKER_HEARTBEAT_SECONDS).contains(&lifetime) {
        return Err(SchedulerError::InvalidRequest);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::fmt::Debug;
    use std::sync::Arc;

    use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
    use job_service::{
        AgentInstanceId, ExecutionId, InMemoryJobRepository, JobError, JobId, JobRequestContext,
        JobService, JobSpec, JobStage, JobState, LeaseGrant, ProjectRole, QualifiedArtifactKind,
        RequestId, TargetProfileId,
    };
    use revision_service::{ProjectId, RevisionId};
    use uuid::Uuid;

    use super::{SchedulerError, SchedulerService, WorkerState};

    fn uuid(value: u128) -> Uuid {
        Uuid::from_u128(value)
    }

    fn tenant_id(value: u128) -> TenantId {
        TenantId::new(uuid(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn id<T, E: Debug>(prefix: &str, value: u128, parse: impl FnOnce(&str) -> Result<T, E>) -> T {
        parse(&format!("{prefix}{}", uuid(value).simple()))
            .unwrap_or_else(|error| panic!("identifier: {error:?}"))
    }

    fn artifact(value: u128) -> ArtifactId {
        ArtifactId::parse(&format!("art_{}", uuid(value).simple()))
            .unwrap_or_else(|error| panic!("artifact: {error}"))
    }

    struct Fixture {
        jobs: JobService<InMemoryJobRepository>,
        scheduler: SchedulerService<InMemoryJobRepository>,
        tenant: TenantId,
        other_tenant: TenantId,
        project: ProjectId,
        owner: SubjectDigest,
        other_subject: SubjectDigest,
        job: JobId,
        input: ArtifactId,
        receipt: ArtifactId,
        result: RevisionId,
        agent: AgentInstanceId,
        execution: ExecutionId,
        profile: TargetProfileId,
        capabilities: ContentDigest,
    }

    impl Fixture {
        fn new() -> Self {
            let repository = Arc::new(InMemoryJobRepository::default());
            let tenant = tenant_id(1);
            let other_tenant = tenant_id(2);
            let project = id("prj_", 3, ProjectId::parse);
            let owner = SubjectDigest::from_authenticated_subject("scheduler-owner")
                .unwrap_or_else(|error| panic!("owner: {error}"));
            let other_subject = SubjectDigest::from_authenticated_subject("scheduler-other")
                .unwrap_or_else(|error| panic!("other: {error}"));
            repository
                .provision_project(
                    tenant,
                    project,
                    [
                        (owner, ProjectRole::Owner),
                        (other_subject, ProjectRole::Editor),
                    ],
                )
                .unwrap_or_else(|error| panic!("project: {error}"));
            let input = artifact(10);
            let receipt = artifact(11);
            for (artifact_id, kind) in [
                (input, QualifiedArtifactKind::Input),
                (receipt, QualifiedArtifactKind::Receipt),
            ] {
                repository
                    .register_qualified_artifact(tenant, artifact_id, kind, [owner])
                    .unwrap_or_else(|error| panic!("artifact: {error}"));
            }
            let result = id("rev_", 20, RevisionId::parse);
            repository
                .register_qualified_revision(tenant, project, result)
                .unwrap_or_else(|error| panic!("revision: {error}"));
            let profile = TargetProfileId::parse("hancom-hangul-2020-current-pc")
                .unwrap_or_else(|error| panic!("profile: {error}"));
            let capabilities = ContentDigest::of(b"scheduler-capabilities");
            let jobs = JobService::new(Arc::clone(&repository));
            let scheduler = SchedulerService::new(Arc::clone(&repository));
            Self {
                jobs,
                scheduler,
                tenant,
                other_tenant,
                project,
                owner,
                other_subject,
                job: id("job_", 30, JobId::parse),
                input,
                receipt,
                result,
                agent: id("agt_", 40, AgentInstanceId::parse),
                execution: id("exe_", 41, ExecutionId::parse),
                profile,
                capabilities,
            }
        }

        fn context(&self, subject: SubjectDigest, now: u64) -> JobRequestContext {
            JobRequestContext::new(self.tenant, subject, now)
        }

        fn enqueue(&self, profile: TargetProfileId, capabilities: ContentDigest) {
            let spec = JobSpec::new(
                self.project,
                self.job,
                id("req_", 31, RequestId::parse),
                self.input,
                None,
                ContentDigest::of(b"scheduler-plan"),
                profile,
                capabilities,
            );
            self.jobs
                .enqueue(&self.context(self.owner, 100), &spec)
                .unwrap_or_else(|error| panic!("enqueue: {error}"));
        }

        fn register(&self, state: WorkerState, expires_at: u64) {
            self.scheduler
                .register_worker(
                    &self.context(self.owner, 100),
                    self.agent,
                    self.profile.clone(),
                    self.capabilities,
                    state,
                    expires_at,
                )
                .unwrap_or_else(|error| panic!("register: {error}"));
        }

        fn lease(&self, expires_at: u64) -> LeaseGrant {
            self.scheduler
                .lease_job(
                    &self.context(self.owner, 101),
                    self.project,
                    self.job,
                    self.agent,
                    self.execution,
                    expires_at,
                )
                .unwrap_or_else(|error| panic!("lease: {error}"));
            LeaseGrant::new(self.agent, self.execution, 1, 1, 101, expires_at)
                .unwrap_or_else(|error| panic!("lease value: {error}"))
        }
    }

    #[test]
    fn exact_worker_profile_and_capabilities_receive_one_lease() {
        let fixture = Fixture::new();
        fixture.enqueue(fixture.profile.clone(), fixture.capabilities);
        fixture.register(WorkerState::Ready, 250);
        let lease = fixture.lease(200);
        let record = fixture
            .jobs
            .get(
                &fixture.context(fixture.owner, 102),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("job: {error}"));
        assert_eq!(record.state(), JobState::Leased);
        assert_eq!(record.active_lease(), Some(&lease));
    }

    #[test]
    fn profile_and_capability_mismatch_are_side_effect_free() {
        for mismatch_profile in [true, false] {
            let fixture = Fixture::new();
            let required_profile = if mismatch_profile {
                TargetProfileId::parse("hancom-hangul-2024-other")
                    .unwrap_or_else(|error| panic!("profile: {error}"))
            } else {
                fixture.profile.clone()
            };
            let required_capabilities = if mismatch_profile {
                fixture.capabilities
            } else {
                ContentDigest::of(b"different-capabilities")
            };
            fixture.enqueue(required_profile, required_capabilities);
            fixture.register(WorkerState::Ready, 250);
            let expected = if mismatch_profile {
                SchedulerError::TargetProfileMismatch
            } else {
                SchedulerError::CapabilitySetMismatch
            };
            assert_eq!(
                fixture.scheduler.lease_job(
                    &fixture.context(fixture.owner, 101),
                    fixture.project,
                    fixture.job,
                    fixture.agent,
                    fixture.execution,
                    200,
                ),
                Err(expected)
            );
            let unchanged = fixture
                .jobs
                .get(
                    &fixture.context(fixture.owner, 102),
                    fixture.project,
                    fixture.job,
                )
                .unwrap_or_else(|error| panic!("job: {error}"));
            assert_eq!(unchanged.state(), JobState::Queued);
            assert_eq!(unchanged.attempt_count(), 0);
        }
    }

    #[test]
    fn stale_draining_and_short_heartbeat_workers_cannot_receive_work() {
        for (state, lease_time, expected) in [
            (
                WorkerState::Draining,
                101,
                SchedulerError::WorkerUnavailable,
            ),
            (WorkerState::Ready, 251, SchedulerError::WorkerUnavailable),
            (WorkerState::Ready, 101, SchedulerError::LeaseOutlivesWorker),
        ] {
            let fixture = Fixture::new();
            fixture.enqueue(fixture.profile.clone(), fixture.capabilities);
            fixture.register(state, 250);
            assert_eq!(
                fixture.scheduler.lease_job(
                    &fixture.context(fixture.owner, lease_time),
                    fixture.project,
                    fixture.job,
                    fixture.agent,
                    fixture.execution,
                    251,
                ),
                Err(expected)
            );
        }
    }

    #[test]
    fn worker_and_job_heartbeats_extend_only_the_same_live_fence() {
        let fixture = Fixture::new();
        fixture.enqueue(fixture.profile.clone(), fixture.capabilities);
        fixture.register(WorkerState::Ready, 200);
        let lease = fixture.lease(180);
        fixture
            .scheduler
            .heartbeat_worker(
                &fixture.context(fixture.owner, 150),
                fixture.agent,
                &fixture.profile,
                fixture.capabilities,
                WorkerState::Ready,
                300,
            )
            .unwrap_or_else(|error| panic!("worker heartbeat: {error}"));
        let renewed = lease
            .renewed(150, 280)
            .unwrap_or_else(|error| panic!("renewed: {error}"));
        let record = fixture
            .scheduler
            .heartbeat_job(
                &fixture.context(fixture.owner, 150),
                fixture.project,
                fixture.job,
                &lease,
                280,
            )
            .unwrap_or_else(|error| panic!("job heartbeat: {error}"));
        assert_eq!(record.active_lease(), Some(&renewed));
        let staged = fixture
            .jobs
            .advance(
                &fixture.context(fixture.owner, 250),
                fixture.project,
                fixture.job,
                &renewed,
                JobStage::Staged,
            )
            .unwrap_or_else(|error| panic!("stage: {error}"));
        assert_eq!(staged.state(), JobState::Staged);
        let stale_fence = LeaseGrant::new(
            fixture.agent,
            fixture.execution,
            1,
            2,
            lease.issued_at_unix_seconds(),
            renewed.expires_at_unix_seconds(),
        )
        .unwrap_or_else(|error| panic!("stale fence: {error}"));
        assert_eq!(
            fixture.scheduler.heartbeat_job(
                &fixture.context(fixture.owner, 251),
                fixture.project,
                fixture.job,
                &stale_fence,
                290,
            ),
            Err(SchedulerError::Job(JobError::LeaseMismatch))
        );
    }

    #[test]
    fn late_worker_commit_is_rejected_then_expiry_receipt_closes_attempt() {
        let fixture = Fixture::new();
        fixture.enqueue(fixture.profile.clone(), fixture.capabilities);
        fixture.register(WorkerState::Ready, 200);
        let lease = fixture.lease(120);
        for (time, stage) in [
            (110, JobStage::Staged),
            (111, JobStage::Executing),
            (112, JobStage::Validating),
        ] {
            fixture
                .jobs
                .advance(
                    &fixture.context(fixture.owner, time),
                    fixture.project,
                    fixture.job,
                    &lease,
                    stage,
                )
                .unwrap_or_else(|error| panic!("advance: {error}"));
        }
        assert_eq!(
            fixture.jobs.succeed(
                &fixture.context(fixture.owner, 120),
                fixture.project,
                fixture.job,
                &lease,
                fixture.result,
                fixture.receipt,
            ),
            Err(JobError::LeaseExpired)
        );
        let before_expiry = fixture
            .jobs
            .get(
                &fixture.context(fixture.owner, 120),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("job: {error}"));
        assert_eq!(before_expiry.state(), JobState::Validating);
        assert!(before_expiry.result_revision_id().is_none());
        let expired = fixture
            .scheduler
            .expire_job(
                &fixture.context(fixture.owner, 120),
                fixture.project,
                fixture.job,
                &lease,
                fixture.receipt,
            )
            .unwrap_or_else(|error| panic!("expire: {error}"));
        assert_eq!(expired.state(), JobState::Failed);
        assert_eq!(
            expired
                .terminal_error_code()
                .map(job_service::TerminalErrorCode::as_str),
            Some("LEASE_EXPIRED")
        );
        assert_eq!(
            expired.terminal_receipt_artifact_id(),
            Some(fixture.receipt)
        );
        assert!(expired.result_revision_id().is_none());
    }

    #[test]
    fn expiry_before_deadline_and_unqualified_receipt_do_not_mutate() {
        let fixture = Fixture::new();
        fixture.enqueue(fixture.profile.clone(), fixture.capabilities);
        fixture.register(WorkerState::Ready, 200);
        let lease = fixture.lease(120);
        assert_eq!(
            fixture.scheduler.expire_job(
                &fixture.context(fixture.owner, 119),
                fixture.project,
                fixture.job,
                &lease,
                fixture.receipt,
            ),
            Err(SchedulerError::Job(JobError::LeaseStillActive))
        );
        assert_eq!(
            fixture.scheduler.expire_job(
                &fixture.context(fixture.owner, 120),
                fixture.project,
                fixture.job,
                &lease,
                artifact(999),
            ),
            Err(SchedulerError::Job(JobError::ArtifactNotQualified))
        );
        let unchanged = fixture
            .jobs
            .get(
                &fixture.context(fixture.owner, 121),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("job: {error}"));
        assert_eq!(unchanged.state(), JobState::Leased);
        assert_eq!(unchanged.active_lease(), Some(&lease));
    }

    #[test]
    fn worker_identity_drift_cross_subject_and_cross_tenant_are_rejected() {
        let fixture = Fixture::new();
        fixture.register(WorkerState::Ready, 200);
        assert_eq!(
            fixture.scheduler.register_worker(
                &fixture.context(fixture.owner, 101),
                fixture.agent,
                fixture.profile.clone(),
                fixture.capabilities,
                WorkerState::Ready,
                201,
            ),
            Err(SchedulerError::DuplicateWorker)
        );
        assert_eq!(
            fixture.scheduler.heartbeat_worker(
                &fixture.context(fixture.owner, 150),
                fixture.agent,
                &fixture.profile,
                ContentDigest::of(b"drift"),
                WorkerState::Ready,
                250,
            ),
            Err(SchedulerError::WorkerIdentityMismatch)
        );
        assert_eq!(
            fixture
                .scheduler
                .get_worker(&fixture.context(fixture.other_subject, 150), fixture.agent,),
            Err(SchedulerError::WorkerIdentityMismatch)
        );
        let other_context = JobRequestContext::new(fixture.other_tenant, fixture.owner, 150);
        assert_eq!(
            fixture.scheduler.get_worker(&other_context, fixture.agent),
            Err(SchedulerError::WorkerNotFound)
        );
    }

    #[test]
    fn bounded_worker_and_lease_renewal_contracts_are_enforced() {
        let fixture = Fixture::new();
        assert_eq!(
            fixture.scheduler.register_worker(
                &fixture.context(fixture.owner, 100),
                fixture.agent,
                fixture.profile.clone(),
                fixture.capabilities,
                WorkerState::Ready,
                401,
            ),
            Err(SchedulerError::InvalidRequest)
        );
        let lease = LeaseGrant::new(fixture.agent, fixture.execution, 1, 1, 100, 200)
            .unwrap_or_else(|error| panic!("lease: {error}"));
        assert_eq!(lease.renewed(200, 250), Err(JobError::LeaseExpired));
        assert_eq!(lease.renewed(150, 3_701), Err(JobError::InvalidRequest));
    }

    #[test]
    fn debug_output_redacts_worker_subject_agent_and_capability_digest() {
        let fixture = Fixture::new();
        fixture.register(WorkerState::Ready, 200);
        let worker = fixture
            .scheduler
            .get_worker(&fixture.context(fixture.owner, 101), fixture.agent)
            .unwrap_or_else(|error| panic!("worker: {error}"));
        let debug = format!("{worker:?}");
        assert!(!debug.contains(&fixture.owner.hex()));
        assert!(!debug.contains(&fixture.agent.public_id()));
        assert!(!debug.contains(&fixture.capabilities.hex()));
    }
}
