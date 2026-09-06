use std::collections::btree_map::Entry;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, Mutex};

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId};

use crate::types::{
    BranchCreateRequest, BranchName, BranchRecord, CheckpointId, CheckpointOutcome,
    CheckpointRecord, CheckpointRequest, CommittedRevisionProjection, HistoryError,
    HistoryRequestContext, HistorySnapshot, ProjectRole, RequestId,
};

pub trait HistoryRepository: Send + Sync {
    /// Returns one authorized, immutable snapshot projection.
    ///
    /// # Errors
    ///
    /// Returns not-found across tenant/project boundaries and fails closed on graph drift.
    fn snapshot(
        &self,
        context: &HistoryRequestContext,
        project_id: ProjectId,
        branch_id: BranchId,
        requested_head: Option<RevisionHead>,
    ) -> Result<HistorySnapshot, HistoryError>;

    /// Atomically creates or replays an immutable checkpoint.
    ///
    /// # Errors
    ///
    /// Returns access, identity, target or idempotency failures.
    fn checkpoint(
        &self,
        context: &HistoryRequestContext,
        request: &CheckpointRequest,
        request_sha256: ContentDigest,
    ) -> Result<CheckpointOutcome, HistoryError>;

    /// Creates a new branch at one qualified sealed revision.
    ///
    /// # Errors
    ///
    /// Returns access, identity or target failures.
    fn create_branch(
        &self,
        context: &HistoryRequestContext,
        request: &BranchCreateRequest,
    ) -> Result<BranchRecord, HistoryError>;

    /// Resolves an authorized semantic-diff artifact binding.
    ///
    /// # Errors
    ///
    /// Returns not-found for absent or differently scoped data.
    fn semantic_diff(
        &self,
        context: &HistoryRequestContext,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<ArtifactId, HistoryError>;
}

type ProjectKey = (TenantId, ProjectId);
type BranchKey = (TenantId, ProjectId, BranchId);
type RevisionKey = (TenantId, ProjectId, RevisionId);
type CheckpointKey = (TenantId, ProjectId, CheckpointId);
type CheckpointLabelKey = (TenantId, ProjectId, crate::types::CheckpointLabel);
type RequestKey = (TenantId, ProjectId, RequestId);

#[derive(Default)]
struct RepositoryState {
    project_acl: BTreeMap<ProjectKey, BTreeMap<SubjectDigest, ProjectRole>>,
    branches: BTreeMap<BranchKey, BranchRecord>,
    branch_names: BTreeSet<(TenantId, ProjectId, BranchName)>,
    revisions: BTreeMap<RevisionKey, CommittedRevisionProjection>,
    checkpoints: BTreeMap<CheckpointKey, CheckpointRecord>,
    checkpoint_labels: BTreeSet<CheckpointLabelKey>,
    checkpoint_requests: BTreeMap<RequestKey, (ContentDigest, SubjectDigest, CheckpointRecord)>,
}

#[derive(Clone, Default)]
pub struct InMemoryHistoryRepository {
    state: Arc<Mutex<RepositoryState>>,
}

impl std::fmt::Debug for InMemoryHistoryRepository {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("InMemoryHistoryRepository")
            .finish_non_exhaustive()
    }
}

impl InMemoryHistoryRepository {
    /// Provisions an in-memory project ACL for adapter and conformance tests.
    ///
    /// # Errors
    ///
    /// Rejects an empty ACL, duplicate subjects or an existing project.
    pub fn provision_project(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        acl: impl IntoIterator<Item = (SubjectDigest, ProjectRole)>,
    ) -> Result<(), HistoryError> {
        let mut roles = BTreeMap::new();
        for (subject, role) in acl {
            if roles.insert(subject, role).is_some() {
                return Err(HistoryError::InvalidRequest);
            }
        }
        if roles.is_empty() || !roles.values().any(|role| *role == ProjectRole::Owner) {
            return Err(HistoryError::InvalidRequest);
        }
        let mut state = self.lock()?;
        match state.project_acl.entry((tenant_id, project_id)) {
            Entry::Vacant(entry) => {
                entry.insert(roles);
                Ok(())
            }
            Entry::Occupied(_) => Err(HistoryError::DuplicateIdentity),
        }
    }

    /// Imports a projection emitted only after a successful P14-03 service commit.
    ///
    /// # Errors
    ///
    /// Rejects absent projects, missing parents, bad generation steps, cycles or duplicates.
    pub fn record_committed_revision(
        &self,
        tenant_id: TenantId,
        revision: CommittedRevisionProjection,
    ) -> Result<(), HistoryError> {
        let mut state = self.lock()?;
        if !state
            .project_acl
            .contains_key(&(tenant_id, revision.project_id()))
        {
            return Err(HistoryError::NotFound);
        }
        let key = (tenant_id, revision.project_id(), revision.revision_id());
        if state.revisions.contains_key(&key) {
            return Err(HistoryError::DuplicateIdentity);
        }
        match revision.parents().first() {
            None if revision.committed_generation() != 1 => {
                return Err(HistoryError::InvalidGraph);
            }
            Some(first_parent) => {
                let parent = state
                    .revisions
                    .get(&(tenant_id, revision.project_id(), *first_parent))
                    .ok_or(HistoryError::InvalidGraph)?;
                if parent.committed_generation().checked_add(1)
                    != Some(revision.committed_generation())
                {
                    return Err(HistoryError::InvalidGraph);
                }
            }
            None => {}
        }
        for parent in revision.parents() {
            let parent_revision = state
                .revisions
                .get(&(tenant_id, revision.project_id(), *parent))
                .ok_or(HistoryError::InvalidGraph)?;
            if parent_revision.committed_generation() >= revision.committed_generation() {
                return Err(HistoryError::InvalidGraph);
            }
        }
        state.revisions.insert(key, revision);
        Ok(())
    }

    /// Provisions the initial/default stream around a qualified revision projection.
    ///
    /// # Errors
    ///
    /// Rejects absent projects/heads and duplicate branch identities or names.
    pub fn provision_branch(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
        name: BranchName,
        head: RevisionHead,
        is_default: bool,
    ) -> Result<(), HistoryError> {
        let mut state = self.lock()?;
        if !state.project_acl.contains_key(&(tenant_id, project_id)) {
            return Err(HistoryError::NotFound);
        }
        validate_head(&state, tenant_id, project_id, head)?;
        let key = (tenant_id, project_id, branch_id);
        let name_key = (tenant_id, project_id, name.clone());
        if state.branches.contains_key(&key) || state.branch_names.contains(&name_key) {
            return Err(HistoryError::DuplicateIdentity);
        }
        if is_default
            && state.branches.iter().any(|((tenant, project, _), branch)| {
                *tenant == tenant_id && *project == project_id && branch.is_default()
            })
        {
            return Err(HistoryError::DuplicateIdentity);
        }
        state.branch_names.insert(name_key);
        state.branches.insert(
            key,
            BranchRecord::new(project_id, branch_id, name, head, is_default),
        );
        Ok(())
    }

    /// Records a head advance already committed by P14-03 for snapshot-conformance tests.
    ///
    /// # Errors
    ///
    /// Rejects absent streams, stale expected heads and unqualified target projections.
    pub fn record_branch_advance(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
        expected_head: RevisionHead,
        new_head: RevisionHead,
    ) -> Result<(), HistoryError> {
        let mut state = self.lock()?;
        validate_head(&state, tenant_id, project_id, new_head)?;
        let key = (tenant_id, project_id, branch_id);
        let branch = state
            .branches
            .get(&key)
            .cloned()
            .ok_or(HistoryError::NotFound)?;
        if branch.head() != expected_head || new_head.generation() <= expected_head.generation() {
            return Err(HistoryError::InvalidGraph);
        }
        state.branches.insert(
            key,
            BranchRecord::new(
                project_id,
                branch_id,
                branch.name().clone(),
                new_head,
                branch.is_default(),
            ),
        );
        Ok(())
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, RepositoryState>, HistoryError> {
        self.state
            .lock()
            .map_err(|_| HistoryError::RepositoryFailure)
    }
}

impl HistoryRepository for InMemoryHistoryRepository {
    fn snapshot(
        &self,
        context: &HistoryRequestContext,
        project_id: ProjectId,
        branch_id: BranchId,
        requested_head: Option<RevisionHead>,
    ) -> Result<HistorySnapshot, HistoryError> {
        let state = self.lock()?;
        require_role(&state, context, project_id, false)?;
        let branch = state
            .branches
            .get(&(context.tenant_id(), project_id, branch_id))
            .cloned()
            .ok_or(HistoryError::NotFound)?;
        let snapshot_head = requested_head.unwrap_or_else(|| branch.head());
        validate_head(&state, context.tenant_id(), project_id, snapshot_head)?;
        let revisions = state
            .revisions
            .iter()
            .filter(|((tenant, project, _), _)| {
                *tenant == context.tenant_id() && *project == project_id
            })
            .map(|(_, revision)| revision.clone())
            .collect();
        let checkpoints = state
            .checkpoints
            .iter()
            .filter(|((tenant, project, _), _)| {
                *tenant == context.tenant_id() && *project == project_id
            })
            .map(|(_, checkpoint)| checkpoint.clone())
            .collect();
        Ok(HistorySnapshot::new(
            BranchRecord::new(
                branch.project_id(),
                branch.branch_id(),
                branch.name().clone(),
                snapshot_head,
                branch.is_default(),
            ),
            revisions,
            checkpoints,
        ))
    }

    fn checkpoint(
        &self,
        context: &HistoryRequestContext,
        request: &CheckpointRequest,
        request_sha256: ContentDigest,
    ) -> Result<CheckpointOutcome, HistoryError> {
        let mut state = self.lock()?;
        require_role(&state, context, request.project_id(), true)?;
        let request_key = (
            context.tenant_id(),
            request.project_id(),
            request.request_id(),
        );
        if let Some((prior_sha256, prior_subject, record)) =
            state.checkpoint_requests.get(&request_key)
        {
            return if *prior_sha256 == request_sha256 && *prior_subject == context.subject() {
                Ok(CheckpointOutcome::Replayed(record.clone()))
            } else {
                Err(HistoryError::IdempotencyConflict)
            };
        }
        if !state.revisions.contains_key(&(
            context.tenant_id(),
            request.project_id(),
            request.revision_id(),
        )) {
            return Err(HistoryError::NotFound);
        }
        let checkpoint_key = (
            context.tenant_id(),
            request.project_id(),
            request.checkpoint_id(),
        );
        let label_key = (
            context.tenant_id(),
            request.project_id(),
            request.label().clone(),
        );
        if state.checkpoints.contains_key(&checkpoint_key)
            || state.checkpoint_labels.contains(&label_key)
        {
            return Err(HistoryError::DuplicateIdentity);
        }
        let record = CheckpointRecord::new(
            request.project_id(),
            request.checkpoint_id(),
            request.revision_id(),
            request.label().clone(),
            request.note().cloned(),
            request.request_id(),
            request_sha256,
        );
        state.checkpoint_labels.insert(label_key);
        state.checkpoints.insert(checkpoint_key, record.clone());
        state.checkpoint_requests.insert(
            request_key,
            (request_sha256, context.subject(), record.clone()),
        );
        Ok(CheckpointOutcome::Created(record))
    }

    fn create_branch(
        &self,
        context: &HistoryRequestContext,
        request: &BranchCreateRequest,
    ) -> Result<BranchRecord, HistoryError> {
        let mut state = self.lock()?;
        require_role(&state, context, request.project_id(), true)?;
        let revision = state
            .revisions
            .get(&(
                context.tenant_id(),
                request.project_id(),
                request.from_revision_id(),
            ))
            .ok_or(HistoryError::NotFound)?;
        let head = RevisionHead::new(
            Some(revision.revision_id()),
            revision.committed_generation(),
        )
        .map_err(|_| HistoryError::InvalidGraph)?;
        let branch_key = (
            context.tenant_id(),
            request.project_id(),
            request.branch_id(),
        );
        let name_key = (
            context.tenant_id(),
            request.project_id(),
            request.name().clone(),
        );
        if state.branches.contains_key(&branch_key) || state.branch_names.contains(&name_key) {
            return Err(HistoryError::DuplicateIdentity);
        }
        let record = BranchRecord::new(
            request.project_id(),
            request.branch_id(),
            request.name().clone(),
            head,
            false,
        );
        state.branch_names.insert(name_key);
        state.branches.insert(branch_key, record.clone());
        Ok(record)
    }

    fn semantic_diff(
        &self,
        context: &HistoryRequestContext,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<ArtifactId, HistoryError> {
        let state = self.lock()?;
        require_role(&state, context, project_id, false)?;
        state
            .revisions
            .get(&(context.tenant_id(), project_id, revision_id))
            .and_then(CommittedRevisionProjection::semantic_diff_artifact_id)
            .ok_or(HistoryError::NotFound)
    }
}

fn require_role(
    state: &RepositoryState,
    context: &HistoryRequestContext,
    project_id: ProjectId,
    mutation: bool,
) -> Result<ProjectRole, HistoryError> {
    let role = state
        .project_acl
        .get(&(context.tenant_id(), project_id))
        .and_then(|acl| acl.get(&context.subject()))
        .copied()
        .ok_or(HistoryError::NotFound)?;
    if mutation && !role.can_mutate() {
        return Err(HistoryError::AccessDenied);
    }
    Ok(role)
}

fn validate_head(
    state: &RepositoryState,
    tenant_id: TenantId,
    project_id: ProjectId,
    head: RevisionHead,
) -> Result<(), HistoryError> {
    match head.revision_id() {
        None if head.generation() == 0 => Ok(()),
        Some(revision_id) => {
            let revision = state
                .revisions
                .get(&(tenant_id, project_id, revision_id))
                .ok_or(HistoryError::InvalidGraph)?;
            if revision.committed_generation() == head.generation() {
                Ok(())
            } else {
                Err(HistoryError::InvalidGraph)
            }
        }
        None => Err(HistoryError::InvalidGraph),
    }
}
