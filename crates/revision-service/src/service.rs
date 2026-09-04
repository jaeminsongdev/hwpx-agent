use crate::store::RevisionRepository;
use crate::types::{
    BranchId, CommitOutcome, ProjectId, RevisionCommitRequest, RevisionError, RevisionHead,
    RevisionId, RevisionNode, RevisionRequestContext,
};

#[derive(Clone, Debug)]
pub struct RevisionService<R> {
    repository: R,
}

impl<R> RevisionService<R>
where
    R: RevisionRepository,
{
    #[must_use]
    pub const fn new(repository: R) -> Self {
        Self { repository }
    }

    /// Atomically commits one sealed revision node if and only if the expected branch head matches.
    ///
    /// # Errors
    ///
    /// Returns a repository/invariant error. A stale head is a typed non-error conflict outcome.
    pub fn commit(
        &self,
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        self.repository.compare_and_swap(context, request)
    }

    /// Reads the exact tenant/project/branch head.
    ///
    /// # Errors
    ///
    /// Cross-tenant and absent streams both return [`RevisionError::NotFound`].
    pub fn head(
        &self,
        context: &RevisionRequestContext,
        project_id: ProjectId,
        branch_id: BranchId,
    ) -> Result<RevisionHead, RevisionError> {
        self.repository
            .head(context.tenant_id(), project_id, branch_id)
    }

    /// Reads one immutable sealed revision node.
    ///
    /// # Errors
    ///
    /// Cross-tenant and absent nodes both return [`RevisionError::NotFound`].
    pub fn node(
        &self,
        context: &RevisionRequestContext,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.repository
            .node(context.tenant_id(), project_id, revision_id)
    }

    #[must_use]
    pub const fn repository(&self) -> &R {
        &self.repository
    }
}

#[cfg(test)]
mod tests {
    use std::sync::{Arc, Barrier};
    use std::thread;

    use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
    use uuid::Uuid;

    use super::*;
    use crate::{
        BranchId, CommitId, InMemoryRevisionRepository, RevisionConflict, RevisionValidationState,
    };

    struct Fixture {
        tenant: TenantId,
        other_tenant: TenantId,
        context: RevisionRequestContext,
        other_context: RevisionRequestContext,
        project: ProjectId,
        branch: BranchId,
        repository: InMemoryRevisionRepository,
        service: RevisionService<InMemoryRevisionRepository>,
    }

    impl Fixture {
        fn new() -> Self {
            let tenant =
                TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("tenant: {error}"));
            let other_tenant = TenantId::new(Uuid::from_u128(2))
                .unwrap_or_else(|error| panic!("other tenant: {error}"));
            let subject = SubjectDigest::from_authenticated_subject("revision-test-subject")
                .unwrap_or_else(|error| panic!("subject: {error}"));
            let project = ProjectId::parse("prj_10000000000000000000000000000001")
                .unwrap_or_else(|error| panic!("project: {error}"));
            let branch = BranchId::parse("brn_20000000000000000000000000000001")
                .unwrap_or_else(|error| panic!("branch: {error}"));
            let repository = InMemoryRevisionRepository::default();
            repository
                .provision_stream(tenant, project, branch)
                .unwrap_or_else(|error| panic!("stream: {error}"));
            let service = RevisionService::new(repository.clone());
            Self {
                tenant,
                other_tenant,
                context: RevisionRequestContext::new(tenant, subject),
                other_context: RevisionRequestContext::new(other_tenant, subject),
                project,
                branch,
                repository,
                service,
            }
        }

        fn request(
            &self,
            ordinal: u128,
            expected_head: RevisionHead,
            parents: Vec<RevisionId>,
        ) -> RevisionCommitRequest {
            request(self.project, self.branch, ordinal, expected_head, parents)
        }

        fn commit_root(&self) -> RevisionId {
            let request = self.request(1, RevisionHead::empty(), Vec::new());
            let revision = request.new_revision_id();
            match self
                .service
                .commit(&self.context, &request)
                .unwrap_or_else(|error| panic!("root commit: {error}"))
            {
                CommitOutcome::Committed(receipt) => {
                    assert_eq!(receipt.committed_head().generation(), 1);
                }
                CommitOutcome::Conflict(_) => panic!("root unexpectedly conflicted"),
            }
            revision
        }
    }

    fn id<T>(
        prefix: &str,
        ordinal: u128,
        parse: impl FnOnce(&str) -> Result<T, RevisionError>,
    ) -> T {
        parse(&format!("{prefix}{ordinal:032x}"))
            .unwrap_or_else(|error| panic!("identifier: {error}"))
    }

    fn artifact(ordinal: u128) -> ArtifactId {
        ArtifactId::parse(&format!("art_{ordinal:032x}"))
            .unwrap_or_else(|error| panic!("artifact: {error}"))
    }

    fn request(
        project: ProjectId,
        branch: BranchId,
        ordinal: u128,
        expected_head: RevisionHead,
        parents: Vec<RevisionId>,
    ) -> RevisionCommitRequest {
        RevisionCommitRequest::new(
            id("cmt_", ordinal, CommitId::parse),
            project,
            branch,
            expected_head,
            id("rev_", ordinal, RevisionId::parse),
            parents,
            artifact(ordinal * 10 + 1),
            artifact(ordinal * 10 + 2),
            Some(artifact(ordinal * 10 + 3)),
            ContentDigest::of(format!("plan-{ordinal}").as_bytes()),
            RevisionValidationState::Verified,
            ContentDigest::of(format!("validation-{ordinal}").as_bytes()),
            ContentDigest::of(format!("transaction-{ordinal}").as_bytes()),
        )
        .unwrap_or_else(|error| panic!("request: {error}"))
    }

    #[test]
    fn root_and_child_commit_form_a_sealed_immutable_chain() {
        let fixture = Fixture::new();
        let root = fixture.commit_root();
        let child_request = fixture.request(
            2,
            RevisionHead::new(Some(root), 1).unwrap_or_else(|error| panic!("head: {error}")),
            vec![root],
        );
        let child = child_request.new_revision_id();
        let outcome = fixture
            .service
            .commit(&fixture.context, &child_request)
            .unwrap_or_else(|error| panic!("child: {error}"));
        let CommitOutcome::Committed(receipt) = outcome else {
            panic!("child unexpectedly conflicted");
        };
        assert_eq!(receipt.committed_head().revision_id(), Some(child));
        assert_eq!(receipt.committed_head().generation(), 2);
        let node = fixture
            .service
            .node(&fixture.context, fixture.project, child)
            .unwrap_or_else(|error| panic!("node: {error}"));
        assert_eq!(node.parents(), &[root]);
        assert!(node.sealed());
        assert_eq!(node.committed_generation(), 2);
    }

    #[test]
    fn two_simultaneous_commits_have_exactly_one_winner() {
        let fixture = Fixture::new();
        let root = fixture.commit_root();
        let expected =
            RevisionHead::new(Some(root), 1).unwrap_or_else(|error| panic!("head: {error}"));
        let request_a = fixture.request(2, expected, vec![root]);
        let request_b = fixture.request(3, expected, vec![root]);
        let loser_candidates = [request_a.new_revision_id(), request_b.new_revision_id()];
        let service = Arc::new(fixture.service.clone());
        let context = fixture.context.clone();
        let barrier = Arc::new(Barrier::new(3));
        let handles = [request_a, request_b].map(|request| {
            let service = Arc::clone(&service);
            let context = context.clone();
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                barrier.wait();
                service.commit(&context, &request)
            })
        });
        barrier.wait();
        let outcomes = handles.map(|handle| {
            handle
                .join()
                .unwrap_or_else(|_| panic!("race thread panicked"))
                .unwrap_or_else(|error| panic!("race commit: {error}"))
        });
        assert_eq!(
            outcomes
                .iter()
                .filter(|outcome| matches!(outcome, CommitOutcome::Committed(_)))
                .count(),
            1
        );
        assert_eq!(
            outcomes
                .iter()
                .filter(|outcome| matches!(outcome, CommitOutcome::Conflict(_)))
                .count(),
            1
        );
        assert_eq!(
            fixture
                .repository
                .node_count(fixture.tenant, fixture.project),
            2
        );
        let final_head = fixture
            .service
            .head(&fixture.context, fixture.project, fixture.branch)
            .unwrap_or_else(|error| panic!("head: {error}"));
        assert_eq!(final_head.generation(), 2);
        assert!(loser_candidates.contains(&final_head.revision_id().unwrap_or(root)));
    }

    #[test]
    fn stale_conflict_is_side_effect_free_and_reports_observed_head() {
        let fixture = Fixture::new();
        let root = fixture.commit_root();
        let expected =
            RevisionHead::new(Some(root), 1).unwrap_or_else(|error| panic!("head: {error}"));
        let winner = fixture.request(2, expected, vec![root]);
        let loser = fixture.request(3, expected, vec![root]);
        assert!(matches!(
            fixture.service.commit(&fixture.context, &winner),
            Ok(CommitOutcome::Committed(_))
        ));
        let conflict = fixture
            .service
            .commit(&fixture.context, &loser)
            .unwrap_or_else(|error| panic!("conflict: {error}"));
        let CommitOutcome::Conflict(conflict) = conflict else {
            panic!("stale commit unexpectedly succeeded");
        };
        assert_eq!(conflict.observed_head().generation(), 2);
        assert!(matches!(
            fixture
                .service
                .node(&fixture.context, fixture.project, loser.new_revision_id()),
            Err(RevisionError::NotFound)
        ));
    }

    #[test]
    fn cross_tenant_reads_and_commits_are_indistinguishable_from_absence() {
        let fixture = Fixture::new();
        let root_request = fixture.request(1, RevisionHead::empty(), Vec::new());
        assert!(matches!(
            fixture
                .service
                .commit(&fixture.other_context, &root_request),
            Err(RevisionError::NotFound)
        ));
        let root = fixture.commit_root();
        assert!(matches!(
            fixture
                .service
                .node(&fixture.other_context, fixture.project, root),
            Err(RevisionError::NotFound)
        ));
        assert!(matches!(
            fixture
                .service
                .head(&fixture.other_context, fixture.project, fixture.branch),
            Err(RevisionError::NotFound)
        ));
    }

    #[test]
    fn missing_duplicate_and_self_parents_fail_closed() {
        let fixture = Fixture::new();
        let root = fixture.commit_root();
        let expected =
            RevisionHead::new(Some(root), 1).unwrap_or_else(|error| panic!("head: {error}"));
        let missing = id("rev_", 99, RevisionId::parse);
        let request = fixture.request(2, expected, vec![root, missing]);
        assert!(matches!(
            fixture.service.commit(&fixture.context, &request),
            Err(RevisionError::ParentUnavailable)
        ));
        assert_eq!(
            fixture
                .repository
                .node_count(fixture.tenant, fixture.project),
            1
        );

        let new_revision = id("rev_", 3, RevisionId::parse);
        let invalid = RevisionCommitRequest::new(
            id("cmt_", 3, CommitId::parse),
            fixture.project,
            fixture.branch,
            expected,
            new_revision,
            vec![root, root],
            artifact(31),
            artifact(32),
            None,
            ContentDigest::of(b"plan"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"validation"),
            ContentDigest::of(b"transaction"),
        );
        assert!(matches!(invalid, Err(RevisionError::InvalidRequest)));
        assert!(
            RevisionCommitRequest::new(
                id("cmt_", 4, CommitId::parse),
                fixture.project,
                fixture.branch,
                expected,
                new_revision,
                vec![root, new_revision],
                artifact(41),
                artifact(42),
                None,
                ContentDigest::of(b"plan"),
                RevisionValidationState::Verified,
                ContentDigest::of(b"validation"),
                ContentDigest::of(b"transaction"),
            )
            .is_err()
        );
    }

    #[test]
    fn only_verified_output_can_advance_a_head() {
        let fixture = Fixture::new();
        let result = RevisionCommitRequest::new(
            id("cmt_", 1, CommitId::parse),
            fixture.project,
            fixture.branch,
            RevisionHead::empty(),
            id("rev_", 1, RevisionId::parse),
            Vec::new(),
            artifact(11),
            artifact(12),
            None,
            ContentDigest::of(b"plan"),
            RevisionValidationState::Unverified,
            ContentDigest::of(b"validation"),
            ContentDigest::of(b"transaction"),
        );
        assert!(matches!(result, Err(RevisionError::InvalidRequest)));
    }

    #[test]
    fn request_deserialization_revalidates_topology() {
        let fixture = Fixture::new();
        let request = fixture.request(1, RevisionHead::empty(), Vec::new());
        let mut value = serde_json::to_value(&request)
            .unwrap_or_else(|error| panic!("serialize request: {error}"));
        value["expected_head"]["generation"] = serde_json::json!(2);
        let decoded = serde_json::from_value::<RevisionCommitRequest>(value);
        assert!(decoded.is_err());
    }

    #[test]
    fn debug_shapes_do_not_expose_subject_or_digest_values() {
        let fixture = Fixture::new();
        let request = fixture.request(1, RevisionHead::empty(), Vec::new());
        let text = format!("{:?} {:?}", fixture.context, request);
        assert!(!text.contains("revision-test-subject"));
        assert!(!text.contains(&ContentDigest::of(b"plan-1").hex()));
    }

    #[test]
    fn independent_branches_do_not_share_head_state() {
        let fixture = Fixture::new();
        let branch_b = id("brn_", 2, BranchId::parse);
        fixture
            .repository
            .provision_stream(fixture.tenant, fixture.project, branch_b)
            .unwrap_or_else(|error| panic!("stream b: {error}"));
        fixture.commit_root();
        let root_b = request(
            fixture.project,
            branch_b,
            50,
            RevisionHead::empty(),
            Vec::new(),
        );
        assert!(matches!(
            fixture.service.commit(&fixture.context, &root_b),
            Ok(CommitOutcome::Committed(_))
        ));
        assert_eq!(
            fixture
                .service
                .head(&fixture.context, fixture.project, branch_b)
                .unwrap_or_else(|error| panic!("head b: {error}"))
                .generation(),
            1
        );
    }

    #[test]
    fn duplicate_commit_and_revision_id_are_rejected_without_head_change() {
        let fixture = Fixture::new();
        let root_request = fixture.request(1, RevisionHead::empty(), Vec::new());
        let root_revision = root_request.new_revision_id();
        assert!(matches!(
            fixture.service.commit(&fixture.context, &root_request),
            Ok(CommitOutcome::Committed(_))
        ));

        let child_request = fixture.request(
            2,
            RevisionHead::new(Some(root_revision), 1)
                .unwrap_or_else(|error| panic!("root head: {error}")),
            vec![root_revision],
        );
        let child_revision = child_request.new_revision_id();
        assert!(matches!(
            fixture.service.commit(&fixture.context, &child_request),
            Ok(CommitOutcome::Committed(_))
        ));

        let current_head = RevisionHead::new(Some(child_revision), 2)
            .unwrap_or_else(|error| panic!("current head: {error}"));
        let duplicate_revision = RevisionCommitRequest::new(
            id("cmt_", 3, CommitId::parse),
            fixture.project,
            fixture.branch,
            current_head,
            root_revision,
            vec![child_revision],
            artifact(31),
            artifact(32),
            None,
            ContentDigest::of(b"duplicate revision plan"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"duplicate revision validation"),
            ContentDigest::of(b"duplicate revision transaction"),
        )
        .unwrap_or_else(|error| panic!("duplicate revision request: {error}"));
        assert!(matches!(
            fixture
                .service
                .commit(&fixture.context, &duplicate_revision),
            Err(RevisionError::DuplicateRevision)
        ));

        let duplicate_commit = RevisionCommitRequest::new(
            root_request.commit_id(),
            fixture.project,
            fixture.branch,
            current_head,
            id("rev_", 3, RevisionId::parse),
            vec![child_revision],
            artifact(41),
            artifact(42),
            None,
            ContentDigest::of(b"duplicate commit plan"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"duplicate commit validation"),
            ContentDigest::of(b"duplicate commit transaction"),
        )
        .unwrap_or_else(|error| panic!("duplicate commit request: {error}"));
        assert!(matches!(
            fixture.service.commit(&fixture.context, &duplicate_commit),
            Err(RevisionError::DuplicateCommit)
        ));
        assert_eq!(
            fixture
                .service
                .head(&fixture.context, fixture.project, fixture.branch)
                .unwrap_or_else(|error| panic!("head: {error}"))
                .generation(),
            2
        );
        assert_eq!(
            fixture
                .repository
                .node_count(fixture.tenant, fixture.project),
            2
        );
        assert!(matches!(
            fixture
                .repository
                .provision_stream(fixture.tenant, fixture.project, fixture.branch),
            Err(RevisionError::DuplicateStream)
        ));
        assert_eq!(
            fixture
                .service
                .head(&fixture.context, fixture.project, fixture.branch)
                .unwrap_or_else(|error| panic!("head after duplicate stream: {error}"))
                .generation(),
            2
        );
    }

    #[test]
    fn fixture_keeps_distinct_tenant_ids() {
        let fixture = Fixture::new();
        assert_ne!(fixture.tenant, fixture.other_tenant);
    }

    fn conflict_generation(conflict: &RevisionConflict) -> u64 {
        conflict.observed_head().generation()
    }

    #[test]
    fn conflict_helper_observes_generation() {
        let fixture = Fixture::new();
        let root = fixture.commit_root();
        let stale = fixture.request(2, RevisionHead::empty(), Vec::new());
        let CommitOutcome::Conflict(conflict) = fixture
            .service
            .commit(&fixture.context, &stale)
            .unwrap_or_else(|error| panic!("conflict: {error}"))
        else {
            panic!("expected conflict");
        };
        assert_eq!(conflict_generation(&conflict), 1);
        assert_eq!(
            fixture
                .service
                .head(&fixture.context, fixture.project, fixture.branch)
                .unwrap_or_else(|error| panic!("head: {error}"))
                .revision_id(),
            Some(root)
        );
    }

    fn _tenant_type_marker(_tenant: TenantId) {}
}
