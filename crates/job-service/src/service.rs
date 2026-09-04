use std::sync::Arc;

use artifact_service::ArtifactId;
use revision_service::{ProjectId, RevisionId};

use crate::store::JobRepository;
use crate::types::{
    JobError, JobId, JobRecord, JobRequestContext, JobSpec, JobStage, LeaseGrant, TerminalErrorCode,
};

#[derive(Clone, Debug)]
pub struct JobService<R: JobRepository> {
    repository: Arc<R>,
}

impl<R: JobRepository> JobService<R> {
    #[must_use]
    pub const fn new(repository: Arc<R>) -> Self {
        Self { repository }
    }

    /// Enqueues one already validated job specification.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, qualification or identity failures.
    pub fn enqueue(
        &self,
        context: &JobRequestContext,
        spec: &JobSpec,
    ) -> Result<JobRecord, JobError> {
        self.repository.enqueue(context, spec)
    }

    /// Applies the initial structural lease transition.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, lease or transition failures.
    pub fn lease(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError> {
        self.repository.lease(context, project_id, job_id, lease)
    }

    /// Advances leased -> staged -> executing -> validating one edge at a time.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, lease or invalid-transition failures.
    pub fn advance(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        next: JobStage,
    ) -> Result<JobRecord, JobError> {
        self.repository
            .advance(context, project_id, job_id, lease, next)
    }

    /// Renews one live lease without changing its execution or fencing identity.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, stale/expired lease or time failures.
    pub fn heartbeat(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        renewed_lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError> {
        self.repository
            .heartbeat(context, project_id, job_id, lease, renewed_lease)
    }

    /// Commits a validating job to a qualified revision and terminal success.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, lease, qualification or transition failures.
    pub fn succeed(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        result_revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        self.repository.succeed(
            context,
            project_id,
            job_id,
            lease,
            result_revision_id,
            receipt_artifact_id,
        )
    }

    /// Commits an active attempt to deterministic terminal failure.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, lease, qualification or transition failures.
    pub fn fail(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        error_code: &TerminalErrorCode,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        self.repository.fail(
            context,
            project_id,
            job_id,
            lease,
            error_code,
            receipt_artifact_id,
        )
    }

    /// Finalizes one expired active attempt with a qualified receipt.
    ///
    /// # Errors
    ///
    /// Returns repository authorization, lease, qualification or still-active failures.
    pub fn expire(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        self.repository
            .expire(context, project_id, job_id, lease, receipt_artifact_id)
    }

    /// Reads one authorized job projection.
    ///
    /// # Errors
    ///
    /// Returns not-found across tenant/project boundaries.
    pub fn get(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
    ) -> Result<JobRecord, JobError> {
        self.repository.get(context, project_id, job_id)
    }
}

#[cfg(test)]
mod tests {
    use std::fmt::Debug;
    use std::sync::Arc;

    use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
    use revision_service::{ProjectId, RevisionId};
    use uuid::Uuid;

    use crate::{
        AgentInstanceId, ExecutionId, InMemoryJobRepository, JobError, JobId, JobRecord,
        JobRequestContext, JobService, JobSpec, JobStage, JobState, LeaseGrant, ProjectRole,
        QualifiedArtifactKind, RequestId, TargetProfileId, TerminalErrorCode,
    };

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
        repository: Arc<InMemoryJobRepository>,
        service: JobService<InMemoryJobRepository>,
        tenant: TenantId,
        other_tenant: TenantId,
        project: ProjectId,
        job: JobId,
        owner: SubjectDigest,
        editor: SubjectDigest,
        reader: SubjectDigest,
        input: ArtifactId,
        receipt: ArtifactId,
        expected: RevisionId,
        result: RevisionId,
        lease: LeaseGrant,
        spec: JobSpec,
    }

    impl Fixture {
        fn new() -> Self {
            let repository = Arc::new(InMemoryJobRepository::default());
            let tenant = tenant_id(1);
            let other_tenant = tenant_id(2);
            let project = id("prj_", 3, ProjectId::parse);
            let owner = SubjectDigest::from_authenticated_subject("job-owner")
                .unwrap_or_else(|error| panic!("owner: {error}"));
            let reader = SubjectDigest::from_authenticated_subject("job-reader")
                .unwrap_or_else(|error| panic!("reader: {error}"));
            let editor = SubjectDigest::from_authenticated_subject("job-editor")
                .unwrap_or_else(|error| panic!("editor: {error}"));
            repository
                .provision_project(
                    tenant,
                    project,
                    [
                        (owner, ProjectRole::Owner),
                        (editor, ProjectRole::Editor),
                        (reader, ProjectRole::Reader),
                    ],
                )
                .unwrap_or_else(|error| panic!("project: {error}"));
            let input = artifact(10);
            let receipt = artifact(11);
            repository
                .register_qualified_artifact(tenant, input, QualifiedArtifactKind::Input, [owner])
                .unwrap_or_else(|error| panic!("input: {error}"));
            repository
                .register_qualified_artifact(
                    tenant,
                    receipt,
                    QualifiedArtifactKind::Receipt,
                    [owner],
                )
                .unwrap_or_else(|error| panic!("receipt: {error}"));
            let expected = id("rev_", 20, RevisionId::parse);
            let result = id("rev_", 21, RevisionId::parse);
            for revision in [expected, result] {
                repository
                    .register_qualified_revision(tenant, project, revision)
                    .unwrap_or_else(|error| panic!("revision: {error}"));
            }
            let job = id("job_", 30, JobId::parse);
            let spec = JobSpec::new(
                project,
                job,
                id("req_", 31, RequestId::parse),
                input,
                Some(expected),
                ContentDigest::of(b"job-operation-plan"),
                TargetProfileId::parse("hancom-hangul-2020-secondary")
                    .unwrap_or_else(|error| panic!("profile: {error}")),
                ContentDigest::of(b"job-capability-set"),
            );
            let lease = LeaseGrant::new(
                id("agt_", 40, AgentInstanceId::parse),
                id("exe_", 41, ExecutionId::parse),
                1,
                1,
                101,
                401,
            )
            .unwrap_or_else(|error| panic!("lease: {error}"));
            let service = JobService::new(Arc::clone(&repository));
            Self {
                repository,
                service,
                tenant,
                other_tenant,
                project,
                job,
                owner,
                editor,
                reader,
                input,
                receipt,
                expected,
                result,
                lease,
                spec,
            }
        }

        fn context(&self, subject: SubjectDigest, now: u64) -> JobRequestContext {
            JobRequestContext::new(self.tenant, subject, now)
        }

        fn enqueue_and_lease(&self) -> JobRecord {
            self.service
                .enqueue(&self.context(self.owner, 100), &self.spec)
                .unwrap_or_else(|error| panic!("enqueue: {error}"));
            self.service
                .lease(
                    &self.context(self.owner, 101),
                    self.project,
                    self.job,
                    &self.lease,
                )
                .unwrap_or_else(|error| panic!("lease: {error}"))
        }
    }

    #[test]
    fn exact_stage_chain_commits_one_terminal_success() {
        let fixture = Fixture::new();
        let leased = fixture.enqueue_and_lease();
        assert_eq!(leased.state(), JobState::Leased);
        assert_eq!(leased.attempt_count(), 1);
        for (time, stage, expected) in [
            (102, JobStage::Staged, JobState::Staged),
            (103, JobStage::Executing, JobState::Executing),
            (104, JobStage::Validating, JobState::Validating),
        ] {
            let record = fixture
                .service
                .advance(
                    &fixture.context(fixture.owner, time),
                    fixture.project,
                    fixture.job,
                    &fixture.lease,
                    stage,
                )
                .unwrap_or_else(|error| panic!("advance: {error}"));
            assert_eq!(record.state(), expected);
        }
        let succeeded = fixture
            .service
            .succeed(
                &fixture.context(fixture.owner, 105),
                fixture.project,
                fixture.job,
                &fixture.lease,
                fixture.result,
                fixture.receipt,
            )
            .unwrap_or_else(|error| panic!("succeed: {error}"));
        assert_eq!(succeeded.state(), JobState::Succeeded);
        assert_eq!(succeeded.result_revision_id(), Some(fixture.result));
        assert_eq!(
            succeeded.terminal_receipt_artifact_id(),
            Some(fixture.receipt)
        );
        assert!(succeeded.active_lease().is_none());
        assert_eq!(succeeded.completed_at_unix_seconds(), Some(105));
    }

    #[test]
    fn skipped_repeated_and_backward_transitions_do_not_mutate() {
        let fixture = Fixture::new();
        fixture.enqueue_and_lease();
        assert_eq!(
            fixture.service.advance(
                &fixture.context(fixture.owner, 102),
                fixture.project,
                fixture.job,
                &fixture.lease,
                JobStage::Executing,
            ),
            Err(JobError::InvalidTransition)
        );
        let current = fixture
            .service
            .get(
                &fixture.context(fixture.reader, 103),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("get: {error}"));
        assert_eq!(current.state(), JobState::Leased);
        fixture
            .service
            .advance(
                &fixture.context(fixture.owner, 104),
                fixture.project,
                fixture.job,
                &fixture.lease,
                JobStage::Staged,
            )
            .unwrap_or_else(|error| panic!("stage: {error}"));
        for invalid in [JobStage::Staged, JobStage::Validating] {
            assert_eq!(
                fixture.service.advance(
                    &fixture.context(fixture.owner, 105),
                    fixture.project,
                    fixture.job,
                    &fixture.lease,
                    invalid,
                ),
                Err(JobError::InvalidTransition)
            );
        }
    }

    #[test]
    fn terminal_success_is_immutable() {
        let fixture = Fixture::new();
        fixture.enqueue_and_lease();
        for (time, stage) in [
            (102, JobStage::Staged),
            (103, JobStage::Executing),
            (104, JobStage::Validating),
        ] {
            fixture
                .service
                .advance(
                    &fixture.context(fixture.owner, time),
                    fixture.project,
                    fixture.job,
                    &fixture.lease,
                    stage,
                )
                .unwrap_or_else(|error| panic!("advance: {error}"));
        }
        fixture
            .service
            .succeed(
                &fixture.context(fixture.owner, 105),
                fixture.project,
                fixture.job,
                &fixture.lease,
                fixture.result,
                fixture.receipt,
            )
            .unwrap_or_else(|error| panic!("succeed: {error}"));
        assert_eq!(
            fixture.service.fail(
                &fixture.context(fixture.owner, 106),
                fixture.project,
                fixture.job,
                &fixture.lease,
                &TerminalErrorCode::parse("LATE_FAILURE")
                    .unwrap_or_else(|error| panic!("error: {error}")),
                fixture.receipt,
            ),
            Err(JobError::InvalidTransition)
        );
        assert_eq!(
            fixture
                .service
                .get(
                    &fixture.context(fixture.reader, 107),
                    fixture.project,
                    fixture.job
                )
                .unwrap_or_else(|error| panic!("get: {error}"))
                .state(),
            JobState::Succeeded
        );
    }

    #[test]
    fn active_failure_is_terminal_and_clears_lease() {
        let fixture = Fixture::new();
        fixture.enqueue_and_lease();
        let failed = fixture
            .service
            .fail(
                &fixture.context(fixture.owner, 102),
                fixture.project,
                fixture.job,
                &fixture.lease,
                &TerminalErrorCode::parse("STAGING_FAILED")
                    .unwrap_or_else(|error| panic!("error: {error}")),
                fixture.receipt,
            )
            .unwrap_or_else(|error| panic!("fail: {error}"));
        assert_eq!(failed.state(), JobState::Failed);
        assert!(failed.active_lease().is_none());
        assert_eq!(failed.terminal_receipt_artifact_id(), Some(fixture.receipt));
        assert_eq!(
            failed.terminal_error_code().map(TerminalErrorCode::as_str),
            Some("STAGING_FAILED")
        );
    }

    #[test]
    fn lease_binding_drift_and_time_regression_fail_closed() {
        let fixture = Fixture::new();
        fixture.enqueue_and_lease();
        let wrong = LeaseGrant::new(
            id("agt_", 42, AgentInstanceId::parse),
            fixture.lease.execution_id(),
            1,
            1,
            101,
            401,
        )
        .unwrap_or_else(|error| panic!("lease: {error}"));
        assert_eq!(
            fixture.service.advance(
                &fixture.context(fixture.owner, 102),
                fixture.project,
                fixture.job,
                &wrong,
                JobStage::Staged,
            ),
            Err(JobError::LeaseMismatch)
        );
        assert_eq!(
            fixture.service.advance(
                &fixture.context(fixture.owner, 99),
                fixture.project,
                fixture.job,
                &fixture.lease,
                JobStage::Staged,
            ),
            Err(JobError::InvalidRequest)
        );
    }

    #[test]
    fn cross_tenant_and_reader_mutation_are_denied() {
        let fixture = Fixture::new();
        assert_eq!(
            fixture.service.enqueue(
                &JobRequestContext::new(fixture.other_tenant, fixture.owner, 100),
                &fixture.spec,
            ),
            Err(JobError::NotFound)
        );
        assert_eq!(
            fixture
                .service
                .enqueue(&fixture.context(fixture.reader, 100), &fixture.spec),
            Err(JobError::AccessDenied)
        );
    }

    #[test]
    fn project_editor_without_artifact_acl_cannot_consume_input_or_receipt() {
        let fixture = Fixture::new();
        assert_eq!(
            fixture
                .service
                .enqueue(&fixture.context(fixture.editor, 100), &fixture.spec),
            Err(JobError::ArtifactNotQualified)
        );

        fixture.enqueue_and_lease();
        for (time, stage) in [
            (102, JobStage::Staged),
            (103, JobStage::Executing),
            (104, JobStage::Validating),
        ] {
            fixture
                .service
                .advance(
                    &fixture.context(fixture.owner, time),
                    fixture.project,
                    fixture.job,
                    &fixture.lease,
                    stage,
                )
                .unwrap_or_else(|error| panic!("advance: {error}"));
        }
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.editor, 105),
                fixture.project,
                fixture.job,
                &fixture.lease,
                fixture.result,
                fixture.receipt,
            ),
            Err(JobError::ArtifactNotQualified)
        );
        let unchanged = fixture
            .service
            .get(
                &fixture.context(fixture.reader, 106),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("get: {error}"));
        assert_eq!(unchanged.state(), JobState::Validating);
        assert!(unchanged.result_revision_id().is_none());
        assert!(unchanged.terminal_receipt_artifact_id().is_none());
    }

    #[test]
    fn duplicate_job_or_request_is_side_effect_free() {
        let fixture = Fixture::new();
        fixture
            .service
            .enqueue(&fixture.context(fixture.owner, 100), &fixture.spec)
            .unwrap_or_else(|error| panic!("enqueue: {error}"));
        assert_eq!(
            fixture
                .service
                .enqueue(&fixture.context(fixture.owner, 101), &fixture.spec),
            Err(JobError::DuplicateIdentity)
        );
        let record = fixture
            .service
            .get(
                &fixture.context(fixture.reader, 102),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("get: {error}"));
        assert_eq!(record.state(), JobState::Queued);
        assert_eq!(record.attempt_count(), 0);
    }

    #[test]
    fn unqualified_input_expected_result_and_receipt_are_rejected() {
        let fixture = Fixture::new();
        let bad_input = JobSpec::new(
            fixture.project,
            id("job_", 50, JobId::parse),
            id("req_", 51, RequestId::parse),
            artifact(99),
            Some(fixture.expected),
            ContentDigest::of(b"plan"),
            TargetProfileId::parse("profile-1").unwrap_or_else(|error| panic!("profile: {error}")),
            ContentDigest::of(b"caps"),
        );
        assert_eq!(
            fixture
                .service
                .enqueue(&fixture.context(fixture.owner, 100), &bad_input),
            Err(JobError::ArtifactNotQualified)
        );
        fixture.enqueue_and_lease();
        for (time, stage) in [
            (102, JobStage::Staged),
            (103, JobStage::Executing),
            (104, JobStage::Validating),
        ] {
            fixture
                .service
                .advance(
                    &fixture.context(fixture.owner, time),
                    fixture.project,
                    fixture.job,
                    &fixture.lease,
                    stage,
                )
                .unwrap_or_else(|error| panic!("advance: {error}"));
        }
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.owner, 105),
                fixture.project,
                fixture.job,
                &fixture.lease,
                id("rev_", 999, RevisionId::parse),
                fixture.receipt,
            ),
            Err(JobError::RevisionNotQualified)
        );
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.owner, 105),
                fixture.project,
                fixture.job,
                &fixture.lease,
                fixture.result,
                fixture.input,
            ),
            Err(JobError::ArtifactNotQualified)
        );
        let unchanged = fixture
            .service
            .get(
                &fixture.context(fixture.reader, 106),
                fixture.project,
                fixture.job,
            )
            .unwrap_or_else(|error| panic!("get: {error}"));
        assert_eq!(unchanged.state(), JobState::Validating);
        assert!(unchanged.result_revision_id().is_none());
        assert!(unchanged.terminal_receipt_artifact_id().is_none());
    }

    #[test]
    fn bounded_input_contracts_reject_invalid_values() {
        for invalid in ["", "x", "bad/profile", "한글"] {
            assert!(TargetProfileId::parse(invalid).is_err());
        }
        for invalid in ["", "AB", "lower_case", "HAS-DASH"] {
            assert!(TerminalErrorCode::parse(invalid).is_err());
        }
        assert!(
            LeaseGrant::new(
                id("agt_", 60, AgentInstanceId::parse),
                id("exe_", 61, ExecutionId::parse),
                0,
                1,
                1,
                2,
            )
            .is_err()
        );
        assert!(
            LeaseGrant::new(
                id("agt_", 60, AgentInstanceId::parse),
                id("exe_", 61, ExecutionId::parse),
                1,
                1,
                1,
                3_602,
            )
            .is_err()
        );
    }

    #[test]
    fn debug_output_redacts_subject_digests_and_agent_identity() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let text = format!("{context:?} {:?} {:?}", fixture.spec, fixture.lease);
        assert!(!text.contains(&fixture.owner.hex()));
        assert!(!text.contains(&ContentDigest::of(b"job-operation-plan").hex()));
        assert!(!text.contains(&fixture.lease.agent_instance_id().public_id()));
    }

    #[test]
    fn reserved_later_phase_states_are_terminal_and_not_stage_targets() {
        assert!(JobState::Cancelled.is_terminal());
        assert!(JobState::UnknownOutcome.is_terminal());
        assert!(!JobState::Validating.is_terminal());
        assert_eq!(JobStage::Validating.state(), JobState::Validating);
    }

    #[test]
    fn repository_qualification_registration_is_exact_and_unique() {
        let fixture = Fixture::new();
        assert_eq!(
            fixture.repository.register_qualified_artifact(
                fixture.tenant,
                fixture.input,
                QualifiedArtifactKind::Input,
                [fixture.owner],
            ),
            Err(JobError::DuplicateIdentity)
        );
        assert_eq!(
            fixture.repository.register_qualified_artifact(
                fixture.tenant,
                artifact(70),
                QualifiedArtifactKind::Input,
                [],
            ),
            Err(JobError::InvalidRequest)
        );
        assert_eq!(
            fixture.repository.register_qualified_artifact(
                fixture.tenant,
                artifact(71),
                QualifiedArtifactKind::Input,
                [fixture.owner, fixture.owner],
            ),
            Err(JobError::InvalidRequest)
        );
        assert_eq!(
            fixture.repository.register_qualified_revision(
                fixture.tenant,
                fixture.project,
                fixture.expected,
            ),
            Err(JobError::DuplicateIdentity)
        );
    }
}
