use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, BinaryHeap};
use std::sync::Arc;

use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId};

use crate::cursor::{CursorClaims, CursorCodec};
use crate::store::HistoryRepository;
use crate::types::{
    BranchCreateRequest, BranchRecord, CheckpointLabel, CheckpointOutcome, CheckpointRequest,
    CommittedRevisionProjection, HistoryEntry, HistoryError, HistoryPage, HistoryQuery,
    HistoryRequestContext, MAX_HISTORY_NODES, MAX_HISTORY_PAGE_SIZE, SemanticDiffReference,
};

#[derive(Clone, Debug)]
pub struct HistoryService<R: HistoryRepository> {
    repository: Arc<R>,
    cursor_codec: CursorCodec,
}

#[derive(Clone, Copy, Debug)]
struct HistoryReadPlan {
    project_id: ProjectId,
    branch_id: BranchId,
    requested_head: Option<RevisionHead>,
    start: usize,
    page_size: u16,
    expires_at: u64,
}

impl<R: HistoryRepository> HistoryService<R> {
    #[must_use]
    pub fn new(repository: Arc<R>, cursor_codec: CursorCodec) -> Self {
        Self {
            repository,
            cursor_codec,
        }
    }

    fn decode_history_query(
        &self,
        context: &HistoryRequestContext,
        query: HistoryQuery,
    ) -> Result<HistoryReadPlan, HistoryError> {
        match query {
            HistoryQuery::First {
                project_id,
                branch_id,
                page_size,
            } => {
                if !(1..=MAX_HISTORY_PAGE_SIZE).contains(&page_size) {
                    return Err(HistoryError::InvalidRequest);
                }
                Ok(HistoryReadPlan {
                    project_id,
                    branch_id,
                    requested_head: None,
                    start: 0,
                    page_size,
                    expires_at: self.cursor_codec.expiration(context.now_unix_seconds())?,
                })
            }
            HistoryQuery::Continue { cursor } => {
                let CursorClaims::History {
                    project_id,
                    branch_id,
                    snapshot_head,
                    next_index,
                    page_size,
                    expires_at_unix_seconds,
                    ..
                } = self.cursor_codec.decode(context, &cursor)?
                else {
                    return Err(HistoryError::InvalidCursor);
                };
                Ok(HistoryReadPlan {
                    project_id,
                    branch_id,
                    requested_head: Some(snapshot_head),
                    start: usize::try_from(next_index).map_err(|_| HistoryError::InvalidCursor)?,
                    page_size,
                    expires_at: expires_at_unix_seconds,
                })
            }
        }
    }

    /// Reads one stable, bounded DAG page.
    ///
    /// # Errors
    ///
    /// Fails on authorization, cursor, snapshot, graph or repository violations.
    pub fn history(
        &self,
        context: &HistoryRequestContext,
        query: HistoryQuery,
    ) -> Result<HistoryPage, HistoryError> {
        let HistoryReadPlan {
            project_id,
            branch_id,
            requested_head,
            start,
            page_size,
            expires_at,
        } = self.decode_history_query(context, query)?;

        let snapshot = self
            .repository
            .snapshot(context, project_id, branch_id, requested_head)?;
        if snapshot.branch.project_id() != project_id || snapshot.branch.branch_id() != branch_id {
            return Err(HistoryError::InvalidGraph);
        }
        let snapshot_head = snapshot.branch.head();
        if snapshot
            .revisions
            .iter()
            .any(|revision| revision.project_id() != project_id)
            || snapshot
                .checkpoints
                .iter()
                .any(|checkpoint| checkpoint.project_id() != project_id)
        {
            return Err(HistoryError::InvalidGraph);
        }
        let ordered = order_reachable(snapshot_head, snapshot.revisions)?;
        if let Some(head_revision) = ordered.first()
            && head_revision.committed_generation() != snapshot_head.generation()
        {
            return Err(HistoryError::InvalidGraph);
        }
        if start > ordered.len() {
            return Err(HistoryError::InvalidCursor);
        }
        let end = start
            .saturating_add(usize::from(page_size))
            .min(ordered.len());
        let labels = labels_by_revision(&snapshot.checkpoints);
        let entries = ordered[start..end]
            .iter()
            .map(|revision| {
                let semantic_diff_cursor = revision
                    .semantic_diff_artifact_id()
                    .map(|artifact_id| {
                        self.cursor_codec.encode(&CursorClaims::SemanticDiff {
                            tenant_id: context.tenant_id(),
                            subject_sha256: context.subject(),
                            project_id,
                            revision_id: revision.revision_id(),
                            artifact_id,
                            expires_at_unix_seconds: expires_at,
                        })
                    })
                    .transpose()?;
                Ok(HistoryEntry::new(
                    revision,
                    labels
                        .get(&revision.revision_id())
                        .cloned()
                        .unwrap_or_default(),
                    semantic_diff_cursor,
                ))
            })
            .collect::<Result<Vec<_>, HistoryError>>()?;
        let next_cursor = if end < ordered.len() {
            Some(self.cursor_codec.encode(&CursorClaims::History {
                tenant_id: context.tenant_id(),
                subject_sha256: context.subject(),
                project_id,
                branch_id,
                snapshot_head,
                next_index: u32::try_from(end).map_err(|_| HistoryError::GraphLimitExceeded)?,
                page_size,
                expires_at_unix_seconds: expires_at,
            })?)
        } else {
            None
        };
        Ok(HistoryPage::new(
            project_id,
            branch_id,
            snapshot_head,
            entries,
            next_cursor,
        ))
    }

    /// Creates or idempotently replays an immutable checkpoint.
    ///
    /// # Errors
    ///
    /// Returns authorization, target, identity, serialization or repository failures.
    pub fn checkpoint(
        &self,
        context: &HistoryRequestContext,
        request: &CheckpointRequest,
    ) -> Result<CheckpointOutcome, HistoryError> {
        let request_sha256 = request.canonical_sha256()?;
        self.repository.checkpoint(context, request, request_sha256)
    }

    /// Creates a non-default branch from a qualified sealed revision.
    ///
    /// # Errors
    ///
    /// Returns authorization, target, identity or repository failures.
    pub fn create_branch(
        &self,
        context: &HistoryRequestContext,
        request: &BranchCreateRequest,
    ) -> Result<BranchRecord, HistoryError> {
        self.repository.create_branch(context, request)
    }

    /// Resolves a signed semantic-diff cursor to an authorized artifact reference.
    ///
    /// # Errors
    ///
    /// Rejects expired, tampered, wrong-kind, cross-subject or stale bindings.
    pub fn resolve_semantic_diff(
        &self,
        context: &HistoryRequestContext,
        cursor: &str,
    ) -> Result<SemanticDiffReference, HistoryError> {
        let CursorClaims::SemanticDiff {
            project_id,
            revision_id,
            artifact_id,
            ..
        } = self.cursor_codec.decode(context, cursor)?
        else {
            return Err(HistoryError::InvalidCursor);
        };
        let current = self
            .repository
            .semantic_diff(context, project_id, revision_id)?;
        if current != artifact_id {
            return Err(HistoryError::InvalidCursor);
        }
        Ok(SemanticDiffReference::new(
            project_id,
            revision_id,
            artifact_id,
        ))
    }
}

fn order_reachable(
    head: RevisionHead,
    revisions: Vec<CommittedRevisionProjection>,
) -> Result<Vec<CommittedRevisionProjection>, HistoryError> {
    let Some(head_id) = head.revision_id() else {
        return if revisions.is_empty() {
            Ok(Vec::new())
        } else {
            // Unrelated qualified roots may exist for other branches; an empty branch still has
            // an empty reachable history.
            Ok(Vec::new())
        };
    };
    let revision_count = revisions.len();
    let by_id = revisions
        .into_iter()
        .map(|revision| (revision.revision_id(), revision))
        .collect::<BTreeMap<_, _>>();
    if by_id.len() != revision_count {
        return Err(HistoryError::InvalidGraph);
    }
    let mut reachable = BTreeSet::new();
    let mut pending = vec![head_id];
    while let Some(revision_id) = pending.pop() {
        if !reachable.insert(revision_id) {
            continue;
        }
        if reachable.len() > MAX_HISTORY_NODES {
            return Err(HistoryError::GraphLimitExceeded);
        }
        let revision = by_id.get(&revision_id).ok_or(HistoryError::InvalidGraph)?;
        pending.extend_from_slice(revision.parents());
    }

    let mut remaining_children = reachable
        .iter()
        .copied()
        .map(|revision_id| (revision_id, 0_u16))
        .collect::<BTreeMap<_, _>>();
    for revision_id in &reachable {
        let revision = by_id.get(revision_id).ok_or(HistoryError::InvalidGraph)?;
        for parent in revision.parents() {
            if !reachable.contains(parent) {
                return Err(HistoryError::InvalidGraph);
            }
            let count = remaining_children
                .get_mut(parent)
                .ok_or(HistoryError::InvalidGraph)?;
            *count = count.checked_add(1).ok_or(HistoryError::InvalidGraph)?;
        }
    }

    let mut ready = BinaryHeap::new();
    for (revision_id, child_count) in &remaining_children {
        if *child_count == 0 {
            let generation = by_id
                .get(revision_id)
                .ok_or(HistoryError::InvalidGraph)?
                .committed_generation();
            ready.push((generation, Reverse(*revision_id)));
        }
    }
    let mut ordered = Vec::with_capacity(reachable.len());
    while let Some((_, Reverse(revision_id))) = ready.pop() {
        let revision = by_id.get(&revision_id).ok_or(HistoryError::InvalidGraph)?;
        ordered.push(revision.clone());
        for parent in revision.parents() {
            let count = remaining_children
                .get_mut(parent)
                .ok_or(HistoryError::InvalidGraph)?;
            *count = count.checked_sub(1).ok_or(HistoryError::InvalidGraph)?;
            if *count == 0 {
                let generation = by_id
                    .get(parent)
                    .ok_or(HistoryError::InvalidGraph)?
                    .committed_generation();
                ready.push((generation, Reverse(*parent)));
            }
        }
    }
    if ordered.len() != reachable.len()
        || ordered
            .first()
            .map(CommittedRevisionProjection::revision_id)
            != Some(head_id)
    {
        return Err(HistoryError::InvalidGraph);
    }
    Ok(ordered)
}

fn labels_by_revision(
    checkpoints: &[crate::types::CheckpointRecord],
) -> BTreeMap<RevisionId, Vec<CheckpointLabel>> {
    let mut labels = BTreeMap::<RevisionId, Vec<CheckpointLabel>>::new();
    for checkpoint in checkpoints {
        labels
            .entry(checkpoint.revision_id())
            .or_default()
            .push(checkpoint.label().clone());
    }
    for values in labels.values_mut() {
        values.sort();
    }
    labels
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;
    use std::fmt::Debug;
    use std::sync::{Arc, Barrier};
    use std::thread;

    use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
    use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId};
    use uuid::Uuid;

    use super::{HistoryService, order_reachable};
    use crate::types::MAX_HISTORY_NODES;
    use crate::{
        BranchCreateRequest, BranchName, BranchRecord, CheckpointId, CheckpointLabel,
        CheckpointNote, CheckpointOutcome, CheckpointRecord, CheckpointRequest,
        CommittedRevisionProjection, CursorCodec, HistoryError, HistoryQuery, HistoryRepository,
        HistoryRequestContext, HistorySnapshot, InMemoryHistoryRepository, ProjectRole, RequestId,
    };

    #[derive(Clone, Debug)]
    struct FixedSnapshotRepository {
        snapshot: HistorySnapshot,
    }

    impl HistoryRepository for FixedSnapshotRepository {
        fn snapshot(
            &self,
            _context: &HistoryRequestContext,
            _project_id: ProjectId,
            _branch_id: BranchId,
            _requested_head: Option<RevisionHead>,
        ) -> Result<HistorySnapshot, HistoryError> {
            Ok(self.snapshot.clone())
        }

        fn checkpoint(
            &self,
            _context: &HistoryRequestContext,
            _request: &CheckpointRequest,
            _request_sha256: ContentDigest,
        ) -> Result<CheckpointOutcome, HistoryError> {
            Err(HistoryError::RepositoryFailure)
        }

        fn create_branch(
            &self,
            _context: &HistoryRequestContext,
            _request: &BranchCreateRequest,
        ) -> Result<BranchRecord, HistoryError> {
            Err(HistoryError::RepositoryFailure)
        }

        fn semantic_diff(
            &self,
            _context: &HistoryRequestContext,
            _project_id: ProjectId,
            _revision_id: RevisionId,
        ) -> Result<ArtifactId, HistoryError> {
            Err(HistoryError::RepositoryFailure)
        }
    }

    fn uuid(value: u128) -> Uuid {
        Uuid::from_u128(value)
    }

    fn tenant_id(value: u128) -> TenantId {
        TenantId::new(uuid(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn id<T, E: Debug>(prefix: &str, value: u128, parse: impl FnOnce(&str) -> Result<T, E>) -> T {
        parse(&format!("{prefix}{}", uuid(value).simple()))
            .unwrap_or_else(|error| panic!("id: {error:?}"))
    }

    fn artifact(value: u128) -> ArtifactId {
        ArtifactId::parse(&format!("art_{}", uuid(value).simple()))
            .unwrap_or_else(|error| panic!("artifact: {error}"))
    }

    struct Fixture {
        repository: Arc<InMemoryHistoryRepository>,
        service: HistoryService<InMemoryHistoryRepository>,
        tenant: TenantId,
        other_tenant: TenantId,
        project: ProjectId,
        branch: BranchId,
        root: RevisionId,
        child: RevisionId,
        merge: RevisionId,
        owner: SubjectDigest,
        editor: SubjectDigest,
        reader: SubjectDigest,
    }

    impl Fixture {
        fn new() -> Self {
            let repository = Arc::new(InMemoryHistoryRepository::default());
            let tenant = tenant_id(1);
            let other_tenant = tenant_id(2);
            let project = id("prj_", 3, ProjectId::parse);
            let branch = id("brn_", 4, BranchId::parse);
            let owner = SubjectDigest::from_authenticated_subject("owner")
                .unwrap_or_else(|error| panic!("owner: {error}"));
            let reader = SubjectDigest::from_authenticated_subject("reader")
                .unwrap_or_else(|error| panic!("reader: {error}"));
            let editor = SubjectDigest::from_authenticated_subject("editor")
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
            let root = id("rev_", 10, RevisionId::parse);
            let child = id("rev_", 11, RevisionId::parse);
            let side = id("rev_", 12, RevisionId::parse);
            let merge = id("rev_", 13, RevisionId::parse);
            for revision in [
                CommittedRevisionProjection::new(project, root, vec![], artifact(20), None, 1),
                CommittedRevisionProjection::new(
                    project,
                    child,
                    vec![root],
                    artifact(21),
                    Some(artifact(31)),
                    2,
                ),
                CommittedRevisionProjection::new(project, side, vec![root], artifact(22), None, 2),
                CommittedRevisionProjection::new(
                    project,
                    merge,
                    vec![child, side],
                    artifact(23),
                    Some(artifact(33)),
                    3,
                ),
            ] {
                repository
                    .record_committed_revision(
                        tenant,
                        revision.unwrap_or_else(|error| panic!("projection: {error}")),
                    )
                    .unwrap_or_else(|error| panic!("record: {error}"));
            }
            repository
                .provision_branch(
                    tenant,
                    project,
                    branch,
                    BranchName::parse("main").unwrap_or_else(|error| panic!("name: {error}")),
                    RevisionHead::new(Some(merge), 3)
                        .unwrap_or_else(|error| panic!("head: {error}")),
                    true,
                )
                .unwrap_or_else(|error| panic!("branch: {error}"));
            let codec = CursorCodec::new(b"0123456789abcdef0123456789abcdef".to_vec(), 300)
                .unwrap_or_else(|error| panic!("codec: {error}"));
            let service = HistoryService::new(Arc::clone(&repository), codec);
            Self {
                repository,
                service,
                tenant,
                other_tenant,
                project,
                branch,
                root,
                child,
                merge,
                owner,
                editor,
                reader,
            }
        }

        fn context(&self, subject: SubjectDigest, now: u64) -> HistoryRequestContext {
            HistoryRequestContext::new(self.tenant, subject, now)
        }

        fn checkpoint_request(&self) -> CheckpointRequest {
            CheckpointRequest::new(
                id("req_", 40, RequestId::parse),
                self.project,
                id("chk_", 41, CheckpointId::parse),
                self.child,
                CheckpointLabel::parse("Reviewed baseline")
                    .unwrap_or_else(|error| panic!("label: {error}")),
            )
        }
    }

    #[test]
    fn history_pages_are_stable_head_first_and_complete() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.reader, 100);
        let first = fixture
            .service
            .history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 2,
                },
            )
            .unwrap_or_else(|error| panic!("first: {error}"));
        assert_eq!(first.entries().len(), 2);
        assert_eq!(first.entries()[0].revision_id(), fixture.merge);
        let cursor = first
            .next_cursor()
            .unwrap_or_else(|| panic!("missing cursor"));
        let second = fixture
            .service
            .history(
                &context,
                HistoryQuery::Continue {
                    cursor: cursor.to_owned(),
                },
            )
            .unwrap_or_else(|error| panic!("second: {error}"));
        assert_eq!(second.entries().len(), 2);
        assert!(second.next_cursor().is_none());
        let all = first
            .entries()
            .iter()
            .chain(second.entries())
            .map(crate::HistoryEntry::revision_id)
            .collect::<BTreeSet<_>>();
        assert_eq!(all.len(), 4);
        assert!(all.contains(&fixture.root));
    }

    #[test]
    fn checkpoint_is_immutable_idempotent_and_visible_in_history() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let request = fixture.checkpoint_request();
        let created = fixture
            .service
            .checkpoint(&context, &request)
            .unwrap_or_else(|error| panic!("checkpoint: {error}"));
        let replayed = fixture
            .service
            .checkpoint(&context, &request)
            .unwrap_or_else(|error| panic!("replay: {error}"));
        let (CheckpointOutcome::Created(first), CheckpointOutcome::Replayed(second)) =
            (created, replayed)
        else {
            panic!("unexpected checkpoint outcomes");
        };
        assert_eq!(first, second);
        let page = fixture
            .service
            .history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 100,
                },
            )
            .unwrap_or_else(|error| panic!("history: {error}"));
        let child = page
            .entries()
            .iter()
            .find(|entry| entry.revision_id() == fixture.child)
            .unwrap_or_else(|| panic!("child missing"));
        assert_eq!(child.checkpoint_labels(), &[request.label().clone()]);
    }

    #[test]
    fn checkpoint_note_is_exact_immutable_and_redacted_from_debug() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let note = CheckpointNote::parse("한글 2020 검토 메모")
            .unwrap_or_else(|error| panic!("note: {error}"));
        let request = CheckpointRequest::new_with_note(
            id("req_", 43, RequestId::parse),
            fixture.project,
            id("chk_", 44, CheckpointId::parse),
            fixture.child,
            CheckpointLabel::parse("Noted baseline")
                .unwrap_or_else(|error| panic!("label: {error}")),
            Some(note.clone()),
        );
        let created = fixture
            .service
            .checkpoint(&context, &request)
            .unwrap_or_else(|error| panic!("checkpoint: {error}"));
        let CheckpointOutcome::Created(record) = created else {
            panic!("expected created checkpoint");
        };
        assert_eq!(record.note(), Some(&note));
        assert!(!format!("{record:?}").contains(note.as_str()));

        let drifted = CheckpointRequest::new_with_note(
            request.request_id(),
            request.project_id(),
            request.checkpoint_id(),
            request.revision_id(),
            request.label().clone(),
            Some(
                CheckpointNote::parse("다른 메모")
                    .unwrap_or_else(|error| panic!("drifted note: {error}")),
            ),
        );
        assert_eq!(
            fixture.service.checkpoint(&context, &drifted),
            Err(HistoryError::IdempotencyConflict)
        );
        assert_eq!(CheckpointNote::parse(""), Err(HistoryError::InvalidRequest));
        assert_eq!(
            CheckpointNote::parse("가".repeat(1_001)),
            Err(HistoryError::InvalidRequest)
        );
    }

    #[test]
    fn idempotency_key_drift_is_rejected_without_second_checkpoint() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let request = fixture.checkpoint_request();
        fixture
            .service
            .checkpoint(&context, &request)
            .unwrap_or_else(|error| panic!("checkpoint: {error}"));
        let drifted = CheckpointRequest::new(
            request.request_id(),
            fixture.project,
            id("chk_", 42, CheckpointId::parse),
            fixture.root,
            CheckpointLabel::parse("Different").unwrap_or_else(|error| panic!("label: {error}")),
        );
        assert!(matches!(
            fixture.service.checkpoint(&context, &drifted),
            Err(HistoryError::IdempotencyConflict)
        ));
    }

    #[test]
    fn reader_can_read_but_cannot_mutate() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.reader, 100);
        assert!(
            fixture
                .service
                .history(
                    &context,
                    HistoryQuery::First {
                        project_id: fixture.project,
                        branch_id: fixture.branch,
                        page_size: 1,
                    },
                )
                .is_ok()
        );
        assert!(matches!(
            fixture
                .service
                .checkpoint(&context, &fixture.checkpoint_request()),
            Err(HistoryError::AccessDenied)
        ));
    }

    #[test]
    fn cross_tenant_access_is_indistinguishable_from_absence() {
        let fixture = Fixture::new();
        let context = HistoryRequestContext::new(fixture.other_tenant, fixture.owner, 100);
        assert!(matches!(
            fixture.service.history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 1,
                }
            ),
            Err(HistoryError::NotFound)
        ));
    }

    #[test]
    fn semantic_diff_cursor_is_subject_bound_tamperproof_and_expiring() {
        let fixture = Fixture::new();
        let owner_context = fixture.context(fixture.owner, 100);
        let page = fixture
            .service
            .history(
                &owner_context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 1,
                },
            )
            .unwrap_or_else(|error| panic!("history: {error}"));
        let cursor = page.entries()[0]
            .semantic_diff_cursor()
            .unwrap_or_else(|| panic!("diff cursor"));
        let reference = fixture
            .service
            .resolve_semantic_diff(&owner_context, cursor)
            .unwrap_or_else(|error| panic!("diff: {error}"));
        assert_eq!(reference.revision_id(), fixture.merge);
        assert_eq!(reference.artifact_id(), artifact(33));

        let reader_context = fixture.context(fixture.reader, 100);
        assert!(matches!(
            fixture
                .service
                .resolve_semantic_diff(&reader_context, cursor),
            Err(HistoryError::InvalidCursor)
        ));
        let mut tampered = cursor.to_owned();
        tampered.push('a');
        assert!(matches!(
            fixture
                .service
                .resolve_semantic_diff(&owner_context, &tampered),
            Err(HistoryError::InvalidCursor)
        ));
        let expired_context = fixture.context(fixture.owner, 400);
        assert!(matches!(
            fixture
                .service
                .resolve_semantic_diff(&expired_context, cursor),
            Err(HistoryError::CursorExpired)
        ));
    }

    #[test]
    fn history_cursor_wrong_kind_and_page_bounds_fail_closed() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        assert!(matches!(
            fixture.service.history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 0,
                }
            ),
            Err(HistoryError::InvalidRequest)
        ));
        let page = fixture
            .service
            .history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 1,
                },
            )
            .unwrap_or_else(|error| panic!("history: {error}"));
        let diff_cursor = page.entries()[0]
            .semantic_diff_cursor()
            .unwrap_or_else(|| panic!("diff cursor"));
        assert!(matches!(
            fixture.service.history(
                &context,
                HistoryQuery::Continue {
                    cursor: diff_cursor.to_owned(),
                }
            ),
            Err(HistoryError::InvalidCursor)
        ));
    }

    #[test]
    fn continuation_keeps_original_snapshot_after_branch_head_advances() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let first = fixture
            .service
            .history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 1,
                },
            )
            .unwrap_or_else(|error| panic!("first: {error}"));
        let advanced = id("rev_", 50, RevisionId::parse);
        fixture
            .repository
            .record_committed_revision(
                fixture.tenant,
                CommittedRevisionProjection::new(
                    fixture.project,
                    advanced,
                    vec![fixture.merge],
                    artifact(51),
                    None,
                    4,
                )
                .unwrap_or_else(|error| panic!("projection: {error}")),
            )
            .unwrap_or_else(|error| panic!("record: {error}"));
        fixture
            .repository
            .record_branch_advance(
                fixture.tenant,
                fixture.project,
                fixture.branch,
                RevisionHead::new(Some(fixture.merge), 3)
                    .unwrap_or_else(|error| panic!("old head: {error}")),
                RevisionHead::new(Some(advanced), 4)
                    .unwrap_or_else(|error| panic!("new head: {error}")),
            )
            .unwrap_or_else(|error| panic!("advance: {error}"));
        let second = fixture
            .service
            .history(
                &context,
                HistoryQuery::Continue {
                    cursor: first
                        .next_cursor()
                        .unwrap_or_else(|| panic!("cursor"))
                        .to_owned(),
                },
            )
            .unwrap_or_else(|error| panic!("continue: {error}"));
        assert_eq!(second.snapshot_head(), first.snapshot_head());
        assert!(
            second
                .entries()
                .iter()
                .all(|entry| entry.revision_id() != advanced)
        );
    }

    #[test]
    fn concurrent_checkpoint_retries_have_one_creator_and_one_replay() {
        let fixture = Fixture::new();
        let service = Arc::new(fixture.service.clone());
        let request = Arc::new(fixture.checkpoint_request());
        let context = fixture.context(fixture.owner, 100);
        let barrier = Arc::new(Barrier::new(3));
        let handles = [(), ()].map(|()| {
            let service = Arc::clone(&service);
            let request = Arc::clone(&request);
            let context = context.clone();
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                barrier.wait();
                service.checkpoint(&context, &request)
            })
        });
        barrier.wait();
        let outcomes = handles.map(|handle| {
            handle
                .join()
                .unwrap_or_else(|_| panic!("checkpoint thread panicked"))
                .unwrap_or_else(|error| panic!("checkpoint race: {error}"))
        });
        assert_eq!(
            outcomes
                .iter()
                .filter(|outcome| matches!(outcome, CheckpointOutcome::Created(_)))
                .count(),
            1
        );
        assert_eq!(
            outcomes
                .iter()
                .filter(|outcome| matches!(outcome, CheckpointOutcome::Replayed(_)))
                .count(),
            1
        );
    }

    #[test]
    fn idempotency_replay_is_bound_to_the_creating_subject() {
        let fixture = Fixture::new();
        let request = fixture.checkpoint_request();
        fixture
            .service
            .checkpoint(&fixture.context(fixture.owner, 100), &request)
            .unwrap_or_else(|error| panic!("checkpoint: {error}"));
        assert!(matches!(
            fixture
                .service
                .checkpoint(&fixture.context(fixture.editor, 100), &request),
            Err(HistoryError::IdempotencyConflict)
        ));
    }

    #[test]
    fn branch_requires_mutator_unique_name_and_qualified_revision() {
        let fixture = Fixture::new();
        let owner_context = fixture.context(fixture.owner, 100);
        let request = BranchCreateRequest::new(
            fixture.project,
            id("brn_", 60, BranchId::parse),
            BranchName::parse("release/one").unwrap_or_else(|error| panic!("name: {error}")),
            fixture.child,
        );
        let branch = fixture
            .service
            .create_branch(&owner_context, &request)
            .unwrap_or_else(|error| panic!("branch: {error}"));
        assert_eq!(branch.head().revision_id(), Some(fixture.child));
        assert!(matches!(
            fixture.service.create_branch(&owner_context, &request),
            Err(HistoryError::DuplicateIdentity)
        ));

        let missing = BranchCreateRequest::new(
            fixture.project,
            id("brn_", 61, BranchId::parse),
            BranchName::parse("release/two").unwrap_or_else(|error| panic!("name: {error}")),
            id("rev_", 999, RevisionId::parse),
        );
        assert!(matches!(
            fixture.service.create_branch(&owner_context, &missing),
            Err(HistoryError::NotFound)
        ));
    }

    #[test]
    fn input_contracts_reject_unsafe_names_labels_and_weak_keys() {
        for invalid in ["", "/main", "a//b", "a/../b", "한글"] {
            assert!(BranchName::parse(invalid).is_err(), "accepted {invalid:?}");
        }
        for invalid in ["", " padded", "trailing ", "control\n"] {
            assert!(
                CheckpointLabel::parse(invalid).is_err(),
                "accepted {invalid:?}"
            );
        }
        assert!(CursorCodec::new(vec![0; 31], 300).is_err());
        assert!(CursorCodec::new(vec![0; 32], 0).is_err());
        assert!(CursorCodec::new(vec![0; 32], 901).is_err());
    }

    #[test]
    fn bad_generation_and_missing_parent_projections_fail_closed() {
        let fixture = Fixture::new();
        let missing_parent = CommittedRevisionProjection::new(
            fixture.project,
            id("rev_", 70, RevisionId::parse),
            vec![id("rev_", 71, RevisionId::parse)],
            artifact(72),
            None,
            2,
        )
        .unwrap_or_else(|error| panic!("projection: {error}"));
        assert!(matches!(
            fixture
                .repository
                .record_committed_revision(fixture.tenant, missing_parent),
            Err(HistoryError::InvalidGraph)
        ));
        let bad_step = CommittedRevisionProjection::new(
            fixture.project,
            id("rev_", 73, RevisionId::parse),
            vec![fixture.merge],
            artifact(74),
            None,
            5,
        )
        .unwrap_or_else(|error| panic!("projection: {error}"));
        assert!(matches!(
            fixture
                .repository
                .record_committed_revision(fixture.tenant, bad_step),
            Err(HistoryError::InvalidGraph)
        ));

        let future_second_parent = CommittedRevisionProjection::new(
            fixture.project,
            id("rev_", 75, RevisionId::parse),
            vec![fixture.root, fixture.merge],
            artifact(76),
            None,
            2,
        )
        .unwrap_or_else(|error| panic!("projection: {error}"));
        assert!(matches!(
            fixture
                .repository
                .record_committed_revision(fixture.tenant, future_second_parent),
            Err(HistoryError::InvalidGraph)
        ));
    }

    #[test]
    fn snapshot_adapter_cannot_mix_checkpoint_projects() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let snapshot = fixture
            .repository
            .snapshot(&context, fixture.project, fixture.branch, None)
            .unwrap_or_else(|error| panic!("snapshot: {error}"));
        let malformed = CheckpointRecord::new(
            id("prj_", 80, ProjectId::parse),
            id("chk_", 81, CheckpointId::parse),
            fixture.root,
            CheckpointLabel::parse("Wrong project")
                .unwrap_or_else(|error| panic!("label: {error}")),
            None,
            id("req_", 82, RequestId::parse),
            ContentDigest::of(b"wrong-project-checkpoint"),
        );
        let repository = Arc::new(FixedSnapshotRepository {
            snapshot: HistorySnapshot::new(snapshot.branch, snapshot.revisions, vec![malformed]),
        });
        let codec = CursorCodec::new(b"abcdef0123456789abcdef0123456789".to_vec(), 300)
            .unwrap_or_else(|error| panic!("codec: {error}"));
        let service = HistoryService::new(repository, codec);
        assert!(matches!(
            service.history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 10,
                }
            ),
            Err(HistoryError::InvalidGraph)
        ));
    }

    #[test]
    fn reachable_history_above_the_node_limit_fails_closed() {
        let project = id("prj_", 90, ProjectId::parse);
        let mut revisions = Vec::with_capacity(MAX_HISTORY_NODES + 1);
        let mut parent = None;
        for index in 0..=MAX_HISTORY_NODES {
            let revision_id = id("rev_", 1_000 + index as u128, RevisionId::parse);
            revisions.push(
                CommittedRevisionProjection::new(
                    project,
                    revision_id,
                    parent.into_iter().collect(),
                    artifact(20_000 + index as u128),
                    None,
                    index as u64 + 1,
                )
                .unwrap_or_else(|error| panic!("projection: {error}")),
            );
            parent = Some(revision_id);
        }
        let head = RevisionHead::new(parent, MAX_HISTORY_NODES as u64 + 1)
            .unwrap_or_else(|error| panic!("head: {error}"));
        assert!(matches!(
            order_reachable(head, revisions),
            Err(HistoryError::GraphLimitExceeded)
        ));
    }

    #[test]
    fn debug_output_redacts_subject_and_cursor_key() {
        let fixture = Fixture::new();
        let context = fixture.context(fixture.owner, 100);
        let page = fixture
            .service
            .history(
                &context,
                HistoryQuery::First {
                    project_id: fixture.project,
                    branch_id: fixture.branch,
                    page_size: 1,
                },
            )
            .unwrap_or_else(|error| panic!("history: {error}"));
        let cursor = page
            .next_cursor()
            .unwrap_or_else(|| panic!("next cursor"))
            .to_owned();
        let text = format!(
            "{context:?} {:?} {page:?} {:?}",
            fixture.service,
            HistoryQuery::Continue {
                cursor: cursor.clone()
            }
        );
        assert!(!text.contains(&fixture.owner.hex()));
        assert!(!text.contains("0123456789abcdef"));
        assert!(!text.contains(&cursor));
    }
}
