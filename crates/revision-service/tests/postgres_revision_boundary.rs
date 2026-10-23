//! Pure boundary tests; real SQL/driver/restart evidence comes from the separate owned probe.
use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{
    BranchId, CommitId, CommitOutcome, ProjectId, RevisionCommitRequest, RevisionError,
    RevisionHead, RevisionId, RevisionNode, RevisionRepository, RevisionRequestContext,
    RevisionService, RevisionValidationState,
    postgres::{LocalPostgresRevisionConfig, RevisionCommitLease, RevisionLeaseIdentity},
};
use std::sync::{
    Arc,
    atomic::{AtomicUsize, Ordering},
};
use uuid::Uuid;
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn request() -> Result<RevisionCommitRequest, RevisionError> {
    RevisionCommitRequest::new(
        CommitId::parse("cmt_00000000000000000000000000000006")?,
        ProjectId::parse("prj_00000000000000000000000000000002")?,
        BranchId::parse("brn_00000000000000000000000000000003")?,
        RevisionHead::empty(),
        RevisionId::parse("rev_00000000000000000000000000000007")?,
        Vec::new(),
        ArtifactId::parse("art_0000000000000000000000000000000b")
            .map_err(|_| RevisionError::InvalidRequest)?,
        ArtifactId::parse("art_0000000000000000000000000000000c")
            .map_err(|_| RevisionError::InvalidRequest)?,
        None,
        ContentDigest::of(b"plan"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"validation"),
        ContentDigest::of(b"transaction"),
    )
}
fn identity() -> RevisionLeaseIdentity {
    RevisionLeaseIdentity {
        idempotency_key: Uuid::from_u128(20),
        job_id: Uuid::from_u128(21),
        agent_instance_id: Uuid::from_u128(23),
        execution_id: Uuid::from_u128(24),
        attempt_no: 1,
        fencing_token: 1,
        authorization_id: Uuid::from_u128(25),
    }
}
#[test]
fn local_config_is_bounded_loopback_only_and_redacted() -> TestResult {
    let good = LocalPostgresRevisionConfig::new(
        5432,
        "postgres".into(),
        "probe_user".into(),
        "synthetic-only-secret".into(),
    )?;
    assert!(!format!("{good:?}").contains("synthetic-only-secret"));
    for (port, db, user, password) in [
        (0, "postgres", "user", "x"),
        (5432, "postgres?host=example.com", "user", "x"),
        (5432, "postgres", "user;DROP", "x"),
        (5432, "postgres", "user", ""),
        (5432, "postgres", "user", "x\0y"),
    ] {
        assert!(matches!(
            LocalPostgresRevisionConfig::new(port, db.into(), user.into(), password.into()),
            Err(RevisionError::InvalidRequest)
        ));
    }
    Ok(())
}
#[test]
fn every_nil_lease_identity_and_invalid_attempt_fence_rejects() -> TestResult {
    let request = request()?;
    for field in 0..5 {
        let mut i = identity();
        match field {
            0 => i.idempotency_key = Uuid::nil(),
            1 => i.job_id = Uuid::nil(),
            2 => i.agent_instance_id = Uuid::nil(),
            3 => i.execution_id = Uuid::nil(),
            _ => i.authorization_id = Uuid::nil(),
        }
        assert!(matches!(
            RevisionCommitLease::bind(i, &request),
            Err(RevisionError::InvalidRequest)
        ));
    }
    for (attempt, fence) in [(0, 0), (11, 11), (1, 2), (10, 9)] {
        let mut i = identity();
        i.attempt_no = attempt;
        i.fencing_token = fence;
        assert!(matches!(
            RevisionCommitLease::bind(i, &request),
            Err(RevisionError::InvalidRequest)
        ));
    }
    Ok(())
}
#[test]
fn lease_debug_is_redacted_and_binding_is_not_authorization() -> TestResult {
    let lease = RevisionCommitLease::bind(identity(), &request()?)?;
    assert_eq!(format!("{lease:?}"), "RevisionCommitLease(<redacted>)");
    assert_eq!(
        format!("{:?}", identity()),
        "RevisionLeaseIdentity(<redacted>)"
    );
    // Well-shaped UUIDs are permitted here; the actual DB probe proves they grant NO authority.
    Ok(())
}
#[derive(Clone, Debug)]
struct ContextDenied(Arc<AtomicUsize>);
impl RevisionRepository for ContextDenied {
    fn authorize_context(&self, _: &RevisionRequestContext) -> Result<(), RevisionError> {
        Err(RevisionError::NotFound)
    }
    fn compare_and_swap(
        &self,
        _: &RevisionRequestContext,
        _: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Err(RevisionError::RepositoryFailure)
    }
    fn head(&self, _: TenantId, _: ProjectId, _: BranchId) -> Result<RevisionHead, RevisionError> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Err(RevisionError::RepositoryFailure)
    }
    fn node(
        &self,
        _: TenantId,
        _: ProjectId,
        _: RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Err(RevisionError::RepositoryFailure)
    }
}
#[test]
fn service_checks_context_before_all_repository_reads_and_writes() -> TestResult {
    let calls = Arc::new(AtomicUsize::new(0));
    let service = RevisionService::new(ContextDenied(calls.clone()));
    let context = RevisionRequestContext::new(
        TenantId::new(Uuid::from_u128(1))?,
        SubjectDigest::from_authenticated_subject("test-principal")?,
    );
    let request = request()?;
    assert!(matches!(
        service.commit(&context, &request),
        Err(RevisionError::NotFound)
    ));
    assert!(matches!(
        service.head(&context, request.project_id(), request.branch_id()),
        Err(RevisionError::NotFound)
    ));
    assert!(matches!(
        service.node(&context, request.project_id(), request.new_revision_id()),
        Err(RevisionError::NotFound)
    ));
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    Ok(())
}
#[test]
fn uncertain_commit_has_distinct_non_success_non_retry_category() {
    assert_eq!(
        RevisionError::CommitOutcomeUnknown.code(),
        "REVISION_COMMIT_OUTCOME_UNKNOWN"
    );
    assert_ne!(
        RevisionError::CommitOutcomeUnknown,
        RevisionError::RepositoryFailure
    );
}
