use std::collections::btree_map::Entry;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, Mutex};

use artifact_service::TenantId;

use crate::types::{
    BranchId, CommitId, CommitOutcome, ProjectId, RevisionCommitRequest, RevisionConflict,
    RevisionError, RevisionHead, RevisionId, RevisionNode, RevisionReceipt, RevisionRequestContext,
};

pub trait RevisionRepository: Send + Sync {
    /// Atomically commits a sealed node or returns a typed stale-head conflict.
    ///
    /// # Errors
    ///
    /// Returns an invariant, identity, parent or repository failure.
    fn compare_and_swap(
        &self,
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError>;

    /// Reads one exact tenant/project/branch head.
    ///
    /// # Errors
    ///
    /// Returns not-found for an absent or differently scoped stream.
    fn head(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
    ) -> Result<RevisionHead, RevisionError>;

    /// Reads one exact immutable revision node.
    ///
    /// # Errors
    ///
    /// Returns not-found for an absent or differently scoped node.
    fn node(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<RevisionNode, RevisionError>;
}

type StreamKey = (TenantId, ProjectId, BranchId);
type NodeKey = (TenantId, ProjectId, RevisionId);
type CommitKey = (TenantId, ProjectId, CommitId);

#[derive(Default)]
struct RepositoryState {
    streams: BTreeMap<StreamKey, RevisionHead>,
    nodes: BTreeMap<NodeKey, RevisionNode>,
    commits: BTreeMap<CommitKey, RevisionReceipt>,
}

#[derive(Clone, Default)]
pub struct InMemoryRevisionRepository {
    state: Arc<Mutex<RepositoryState>>,
}

impl std::fmt::Debug for InMemoryRevisionRepository {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("InMemoryRevisionRepository")
            .finish_non_exhaustive()
    }
}

impl InMemoryRevisionRepository {
    /// Provisions an empty branch stream. Project creation is a separate P14 service concern.
    ///
    /// # Errors
    ///
    /// Rejects a duplicate stream or poisoned repository lock.
    pub fn provision_stream(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
    ) -> Result<(), RevisionError> {
        let mut state = self
            .state
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?;
        match state.streams.entry((tenant_id, project_id, branch_id)) {
            Entry::Vacant(entry) => {
                entry.insert(RevisionHead::empty());
                Ok(())
            }
            Entry::Occupied(_) => Err(RevisionError::DuplicateStream),
        }
    }

    #[cfg(test)]
    pub(crate) fn node_count(&self, tenant_id: TenantId, project_id: ProjectId) -> usize {
        self.state.lock().map_or(0, |state| {
            state
                .nodes
                .keys()
                .filter(|(tenant, project, _)| *tenant == tenant_id && *project == project_id)
                .count()
        })
    }
}

impl RevisionRepository for InMemoryRevisionRepository {
    fn compare_and_swap(
        &self,
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        let tenant_id = context.tenant_id();
        let request_sha256 = request.canonical_sha256()?;
        let mut state = self
            .state
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?;
        let stream_key = (tenant_id, request.project_id(), request.branch_id());
        let observed_head = *state
            .streams
            .get(&stream_key)
            .ok_or(RevisionError::NotFound)?;
        if observed_head != request.expected_head() {
            return Ok(CommitOutcome::Conflict(RevisionConflict::new(
                request,
                observed_head,
                request_sha256,
            )));
        }

        let node_key = (tenant_id, request.project_id(), request.new_revision_id());
        if state.nodes.contains_key(&node_key) {
            return Err(RevisionError::DuplicateRevision);
        }
        let commit_key = (tenant_id, request.project_id(), request.commit_id());
        if state.commits.contains_key(&commit_key) {
            return Err(RevisionError::DuplicateCommit);
        }
        for parent in request.parents() {
            let parent_node = state
                .nodes
                .get(&(tenant_id, request.project_id(), *parent))
                .ok_or(RevisionError::ParentUnavailable)?;
            if !parent_node.sealed() {
                return Err(RevisionError::ParentUnavailable);
            }
        }
        ensure_acyclic(&state, tenant_id, request)?;

        let generation = observed_head
            .generation()
            .checked_add(1)
            .ok_or(RevisionError::InvalidHead)?;
        let committed_head = RevisionHead::new(Some(request.new_revision_id()), generation)?;
        let node =
            RevisionNode::sealed_from(request, generation, request_sha256, context.subject());
        let receipt = RevisionReceipt::from_commit(
            request,
            observed_head,
            committed_head,
            request_sha256,
            context.subject(),
        )?;

        state.nodes.insert(node_key, node);
        state.commits.insert(commit_key, receipt.clone());
        state.streams.insert(stream_key, committed_head);
        Ok(CommitOutcome::Committed(receipt))
    }

    fn head(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
    ) -> Result<RevisionHead, RevisionError> {
        self.state
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .streams
            .get(&(tenant_id, project_id, branch_id))
            .copied()
            .ok_or(RevisionError::NotFound)
    }

    fn node(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.state
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .nodes
            .get(&(tenant_id, project_id, revision_id))
            .cloned()
            .ok_or(RevisionError::NotFound)
    }
}

fn ensure_acyclic(
    state: &RepositoryState,
    tenant_id: TenantId,
    request: &RevisionCommitRequest,
) -> Result<(), RevisionError> {
    let mut pending = request.parents().to_vec();
    let mut visited = BTreeSet::new();
    while let Some(revision_id) = pending.pop() {
        if revision_id == request.new_revision_id() {
            return Err(RevisionError::GraphCycle);
        }
        if !visited.insert(revision_id) {
            continue;
        }
        let node = state
            .nodes
            .get(&(tenant_id, request.project_id(), revision_id))
            .ok_or(RevisionError::ParentUnavailable)?;
        pending.extend_from_slice(node.parents());
    }
    Ok(())
}
