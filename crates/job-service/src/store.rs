use std::collections::btree_map::Entry;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, Mutex};

use artifact_service::{ArtifactId, SubjectDigest, TenantId};
use revision_service::{ProjectId, RevisionId};

use crate::types::{
    JobError, JobId, JobRecord, JobRequestContext, JobSpec, JobStage, LeaseGrant, ProjectRole,
    RequestId, TerminalErrorCode,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum QualifiedArtifactKind {
    Input,
    Receipt,
}

pub trait JobRepository: Send + Sync {
    /// Creates one unique queued job.
    ///
    /// # Errors
    ///
    /// Returns authorization, qualification or duplicate failures.
    fn enqueue(&self, context: &JobRequestContext, spec: &JobSpec) -> Result<JobRecord, JobError>;

    /// Binds the first structural lease to a queued job.
    ///
    /// # Errors
    ///
    /// Returns authorization, identity, lease or transition failures.
    fn lease(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError>;

    /// Advances one exact nonterminal execution stage.
    ///
    /// # Errors
    ///
    /// Returns authorization, lease, time or transition failures.
    fn advance(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        next: JobStage,
    ) -> Result<JobRecord, JobError>;

    /// Renews one live lease without changing its fencing identity.
    ///
    /// # Errors
    ///
    /// Returns authorization, stale/expired lease or bounded-time failures.
    fn heartbeat(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        renewed_lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError>;

    /// Commits a validated job to one qualified revision.
    ///
    /// # Errors
    ///
    /// Returns authorization, lease, qualification or transition failures.
    fn succeed(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        result_revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError>;

    /// Terminates an active attempt with a qualified receipt.
    ///
    /// # Errors
    ///
    /// Returns authorization, lease, qualification or transition failures.
    fn fail(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        error_code: &TerminalErrorCode,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError>;

    /// Finalizes one expired active attempt with a qualified receipt.
    ///
    /// # Errors
    ///
    /// Returns authorization, lease, qualification or still-active failures.
    fn expire(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError>;

    /// Gets an authorized job projection.
    ///
    /// # Errors
    ///
    /// Returns not-found across tenant/project boundaries.
    fn get(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
    ) -> Result<JobRecord, JobError>;
}

type ProjectKey = (TenantId, ProjectId);
type JobKey = (TenantId, ProjectId, JobId);
type RequestKey = (TenantId, ProjectId, RequestId);
type ArtifactKey = (TenantId, ArtifactId);
type RevisionKey = (TenantId, ProjectId, RevisionId);

#[derive(Clone, Debug, Eq, PartialEq)]
struct QualifiedArtifact {
    kind: QualifiedArtifactKind,
    readers: BTreeSet<SubjectDigest>,
}

#[derive(Default)]
struct RepositoryState {
    project_acl: BTreeMap<ProjectKey, BTreeMap<SubjectDigest, ProjectRole>>,
    artifacts: BTreeMap<ArtifactKey, QualifiedArtifact>,
    revisions: BTreeSet<RevisionKey>,
    jobs: BTreeMap<JobKey, JobRecord>,
    requests: BTreeSet<RequestKey>,
}

#[derive(Clone, Default)]
pub struct InMemoryJobRepository {
    state: Arc<Mutex<RepositoryState>>,
}

impl std::fmt::Debug for InMemoryJobRepository {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("InMemoryJobRepository")
            .finish_non_exhaustive()
    }
}

impl InMemoryJobRepository {
    /// Provisions a project ACL for adapter and state-machine conformance tests.
    ///
    /// # Errors
    ///
    /// Rejects empty/ownerless ACLs, duplicate subjects and existing projects.
    pub fn provision_project(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        acl: impl IntoIterator<Item = (SubjectDigest, ProjectRole)>,
    ) -> Result<(), JobError> {
        let mut roles = BTreeMap::new();
        for (subject, role) in acl {
            if roles.insert(subject, role).is_some() {
                return Err(JobError::InvalidRequest);
            }
        }
        if roles.is_empty() || !roles.values().any(|role| *role == ProjectRole::Owner) {
            return Err(JobError::InvalidRequest);
        }
        let mut state = self.lock()?;
        match state.project_acl.entry((tenant_id, project_id)) {
            Entry::Vacant(entry) => {
                entry.insert(roles);
                Ok(())
            }
            Entry::Occupied(_) => Err(JobError::DuplicateIdentity),
        }
    }

    /// Registers one already available and verified artifact projection with
    /// the subjects allowed to consume it.
    ///
    /// # Errors
    ///
    /// Rejects empty or duplicate reader lists and duplicate artifact identities.
    pub fn register_qualified_artifact(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        kind: QualifiedArtifactKind,
        readers: impl IntoIterator<Item = SubjectDigest>,
    ) -> Result<(), JobError> {
        let mut reader_set = BTreeSet::new();
        for reader in readers {
            if !reader_set.insert(reader) {
                return Err(JobError::InvalidRequest);
            }
        }
        if reader_set.is_empty() {
            return Err(JobError::InvalidRequest);
        }
        let mut state = self.lock()?;
        match state.artifacts.entry((tenant_id, artifact_id)) {
            Entry::Vacant(entry) => {
                entry.insert(QualifiedArtifact {
                    kind,
                    readers: reader_set,
                });
                Ok(())
            }
            Entry::Occupied(_) => Err(JobError::DuplicateIdentity),
        }
    }

    /// Registers one already sealed service revision projection.
    ///
    /// # Errors
    ///
    /// Rejects absent projects and duplicate revision identities.
    pub fn register_qualified_revision(
        &self,
        tenant_id: TenantId,
        project_id: ProjectId,
        revision_id: RevisionId,
    ) -> Result<(), JobError> {
        let mut state = self.lock()?;
        if !state.project_acl.contains_key(&(tenant_id, project_id)) {
            return Err(JobError::NotFound);
        }
        if !state.revisions.insert((tenant_id, project_id, revision_id)) {
            return Err(JobError::DuplicateIdentity);
        }
        Ok(())
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, RepositoryState>, JobError> {
        self.state.lock().map_err(|_| JobError::RepositoryFailure)
    }
}

impl JobRepository for InMemoryJobRepository {
    fn enqueue(&self, context: &JobRequestContext, spec: &JobSpec) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, spec.project_id(), true)?;
        require_artifact(
            &state,
            context,
            spec.input_artifact_id(),
            QualifiedArtifactKind::Input,
        )?;
        if let Some(revision_id) = spec.expected_revision_id()
            && !state
                .revisions
                .contains(&(context.tenant_id(), spec.project_id(), revision_id))
        {
            return Err(JobError::RevisionNotQualified);
        }
        let key = (context.tenant_id(), spec.project_id(), spec.job_id());
        let request_key = (context.tenant_id(), spec.project_id(), spec.request_id());
        if state.jobs.contains_key(&key) || state.requests.contains(&request_key) {
            return Err(JobError::DuplicateIdentity);
        }
        let record = JobRecord::queued(spec.clone(), context.now_unix_seconds());
        state.requests.insert(request_key);
        state.jobs.insert(key, record.clone());
        Ok(record)
    }

    fn lease(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let record = state
            .jobs
            .get_mut(&(context.tenant_id(), project_id, job_id))
            .ok_or(JobError::NotFound)?;
        record.lease(lease.clone(), context.now_unix_seconds())?;
        Ok(record.clone())
    }

    fn advance(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        next: JobStage,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let record = state
            .jobs
            .get_mut(&(context.tenant_id(), project_id, job_id))
            .ok_or(JobError::NotFound)?;
        record.advance(lease, next, context.now_unix_seconds())?;
        Ok(record.clone())
    }

    fn heartbeat(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        renewed_lease: &LeaseGrant,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let record = state
            .jobs
            .get_mut(&(context.tenant_id(), project_id, job_id))
            .ok_or(JobError::NotFound)?;
        record.heartbeat(lease, renewed_lease.clone(), context.now_unix_seconds())?;
        Ok(record.clone())
    }

    fn succeed(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        result_revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let key = (context.tenant_id(), project_id, job_id);
        let mut candidate = state.jobs.get(&key).cloned().ok_or(JobError::NotFound)?;
        candidate.succeed(
            lease,
            result_revision_id,
            receipt_artifact_id,
            context.now_unix_seconds(),
        )?;
        if !state
            .revisions
            .contains(&(context.tenant_id(), project_id, result_revision_id))
        {
            return Err(JobError::RevisionNotQualified);
        }
        require_artifact(
            &state,
            context,
            receipt_artifact_id,
            QualifiedArtifactKind::Receipt,
        )?;
        state.jobs.insert(key, candidate.clone());
        Ok(candidate)
    }

    fn fail(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        error_code: &TerminalErrorCode,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let key = (context.tenant_id(), project_id, job_id);
        let mut candidate = state.jobs.get(&key).cloned().ok_or(JobError::NotFound)?;
        candidate.fail(
            lease,
            error_code.clone(),
            receipt_artifact_id,
            context.now_unix_seconds(),
        )?;
        require_artifact(
            &state,
            context,
            receipt_artifact_id,
            QualifiedArtifactKind::Receipt,
        )?;
        state.jobs.insert(key, candidate.clone());
        Ok(candidate)
    }

    fn expire(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
        lease: &LeaseGrant,
        receipt_artifact_id: ArtifactId,
    ) -> Result<JobRecord, JobError> {
        let mut state = self.lock()?;
        require_role(&state, context, project_id, true)?;
        let key = (context.tenant_id(), project_id, job_id);
        let mut candidate = state.jobs.get(&key).cloned().ok_or(JobError::NotFound)?;
        candidate.expire(lease, receipt_artifact_id, context.now_unix_seconds())?;
        require_artifact(
            &state,
            context,
            receipt_artifact_id,
            QualifiedArtifactKind::Receipt,
        )?;
        state.jobs.insert(key, candidate.clone());
        Ok(candidate)
    }

    fn get(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        job_id: JobId,
    ) -> Result<JobRecord, JobError> {
        let state = self.lock()?;
        require_role(&state, context, project_id, false)?;
        state
            .jobs
            .get(&(context.tenant_id(), project_id, job_id))
            .cloned()
            .ok_or(JobError::NotFound)
    }
}

fn require_artifact(
    state: &RepositoryState,
    context: &JobRequestContext,
    artifact_id: ArtifactId,
    expected_kind: QualifiedArtifactKind,
) -> Result<(), JobError> {
    let qualified = state
        .artifacts
        .get(&(context.tenant_id(), artifact_id))
        .filter(|artifact| artifact.kind == expected_kind)
        .filter(|artifact| artifact.readers.contains(&context.subject()));
    qualified.map(|_| ()).ok_or(JobError::ArtifactNotQualified)
}

fn require_role(
    state: &RepositoryState,
    context: &JobRequestContext,
    project_id: ProjectId,
    mutation: bool,
) -> Result<ProjectRole, JobError> {
    let role = state
        .project_acl
        .get(&(context.tenant_id(), project_id))
        .and_then(|acl| acl.get(&context.subject()))
        .copied()
        .ok_or(JobError::NotFound)?;
    if mutation && !role.can_mutate() {
        return Err(JobError::AccessDenied);
    }
    Ok(role)
}
