//! Server-owned storage primitive, NOT a P09 execution/route/validation authorization.
//! The caller must retain its qualified manifest, validated output and validation summary.
//! No CLI/MCP/JSON action is exposed here. Existing denied P09 execution routes stay denied.
//! Artifact ingest and revision CAS are not a distributed transaction. A returned descriptor
//! is retained even on failure/conflict; it may be deduplicated/shared and is NEVER deleted or
//! quarantined here. An ingest error can also follow a storage side effect: retain the bound
//! output digest for reconciliation. The immutable intent is stored before CAS; a durable
//! job must retain its identity. This adapter is single-use, not complete durable idempotency.
mod intent;
mod registered;
pub mod job;
pub use intent::{RecoveredResult, StoredCommitRecoveryBinding, StoredCommitRecoveryOutcome, reconcile_stored_commit};
pub use intent::{RegisteredStoredCommitRecoveryOutcome, reconcile_registered_stored_commit};
pub use intent::archive::{ArchivedRegisteredStoredCommitRecoveryOutcome,reconcile_archived_registered_stored_commit};
use std::fmt;

use artifact_service::{
    ArtifactDescriptor, ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ArtifactService,
    AuthScope, ContentDigest, EncryptedBlobStore, FileName, IngestRequest, MediaType, RequestContext,
    StorageState, ValidationState,
};
use operation_engine::{ExecutionManifest, RevisionCas, RevisionCasOutcome, RevisionCommitRequest};
use revision_service::{
    BranchId, CommitId, CommitOutcome, ProjectId, RevisionCommitRequest as ServiceRequest,
    RevisionError, RevisionHead, RevisionId, RevisionReceipt, RevisionRepository,
    RevisionRequestContext, RevisionService, RevisionValidationState,
};
use thiserror::Error;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    StoredJobLease,StoredCommitIntentRecord,StoredRevisionJobRepository,
};

const MAX_BYTES: u64 = 32 * 1024 * 1024;
const HWPX_MEDIA: &str = "application/vnd.hancom.hwpx+zip";

/// Additional current-state restriction, never a replacement for source/ACL/CAS checks or execution authority.
pub trait StoredPrecommitGuard{
    /// # Errors
    /// Must refresh its server-owned dependencies; failure stops this one-shot attempt.
    fn check(&mut self)->Result<(),StoredCommitError>;
}
impl<F:FnMut()->Result<(),StoredCommitError>> StoredPrecommitGuard for F{
    fn check(&mut self)->Result<(),StoredCommitError>{self()}
}

/// Values retained by the authenticated server, never deserialized as an execution permit.
pub struct StoredCommitBinding<'a> {
    pub manifest: &'a ExecutionManifest,
    pub output: &'a [u8],
    pub project: ProjectId,
    pub branch: BranchId,
    pub expected_head: RevisionHead,
    pub commit: CommitId,
    pub new_revision: RevisionId,
    pub validation_summary: ContentDigest,
}

impl fmt::Debug for StoredCommitBinding<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("StoredCommitBinding")
            .field("output_bytes", &self.output.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum StoredCommitError {
    #[error("stored commit binding is invalid")]
    Binding,
    #[error("stored commit authenticated scopes differ or are insufficient")]
    Scope,
    #[error("stored commit source/head is unavailable or changed")]
    Source,
    #[error("stored commit result ingest/readback is unavailable or invalid")]
    Artifact,
    #[error("stored commit source head conflicted")]
    Conflict,
    #[error("stored commit revision failed")]
    Revision,
    #[error("stored commit revision outcome is unknown; reconcile without blind retry")]
    Unknown,
    #[error("stored commit additional current-state guard rejected")]
    CurrentGuard,
}

pub struct StoredResultRevisionCas<'a, R, B, S, V, F> {
    artifacts: &'a ArtifactService<R, B, S>,
    revisions: &'a RevisionService<V>,
    context: &'a RequestContext,
    revision_context: &'a RevisionRequestContext,
    binding: StoredCommitBinding<'a>,
    manifest_sha256: [u8; 32],
    output_sha256: ContentDigest,
    clock: F,
    attempted: bool,
    outcome: Option<RevisionCasOutcome>,
    error: Option<StoredCommitError>,
    retained_result: Option<ArtifactDescriptor>,
    retained_intent: Option<ArtifactDescriptor>,
    retained_precommit: Option<ArtifactDescriptor>,
    intent_sha256: Option<ContentDigest>,
    service_request: Option<ServiceRequest>,
    service_receipt: Option<RevisionReceipt>,
    job_registration: Option<(&'a dyn StoredRevisionJobRepository,StoredJobLease)>,
    registered_job_intent: Option<StoredCommitIntentRecord>,
    registration_response: Option<StoredCommitIntentRecord>,
    precommit_guard:Option<Box<dyn StoredPrecommitGuard+'a>>,
    manifest_archive:Option<operation_engine::ArchivedExecutionManifest>,
}

impl<R, B, S, V, F> fmt::Debug for StoredResultRevisionCas<'_, R, B, S, V, F> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("StoredResultRevisionCas")
            .field("attempted", &self.attempted)
            .field("outcome", &self.outcome)
            .field("error", &self.error)
            .field("result_retained", &self.retained_result.is_some())
            .field("intent_retained", &self.retained_intent.is_some())
            .field("precommit_retained", &self.retained_precommit.is_some())
            .field("job_registered", &self.registered_job_intent.is_some())
            .field("registration_response_received", &self.registration_response.is_some())
            .finish_non_exhaustive()
    }
}

impl<'a, R, B, S, V, F> StoredResultRevisionCas<'a, R, B, S, V, F>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
    F: FnMut() -> u64,
{
    /// Binds immutable server inputs; actual current source/ACL/head is read at callback time.
    /// # Errors
    /// Rejects cross-scope contexts, missing read/write scope, source/revision mismatch,
    /// empty/oversized/unchanged output or an empty validation-summary digest.
    pub fn bind(
        artifacts: &'a ArtifactService<R, B, S>,
        revisions: &'a RevisionService<V>,
        context: &'a RequestContext,
        revision_context: &'a RevisionRequestContext,
        binding: StoredCommitBinding<'a>,
        clock: F,
    ) -> Result<Self, StoredCommitError> {
        if context.tenant_id() != revision_context.tenant_id()
            || context.subject() != revision_context.subject()
            || !context.has_scope(AuthScope::DocumentRead)
            || !context.has_scope(AuthScope::DocumentWrite)
        {
            return Err(StoredCommitError::Scope);
        }
        let base = binding.expected_head.revision_id().ok_or(StoredCommitError::Binding)?;
        if binding.expected_head.generation() == 0
            || binding.manifest.base_revision().as_str() != base.public_id()
            || binding.new_revision == base
            || binding.output.is_empty()
            || binding.output.len() as u64 > MAX_BYTES
            || binding.manifest.expected_source_size() > MAX_BYTES
            || binding.validation_summary.as_bytes() == &[0; 32]
        {
            return Err(StoredCommitError::Binding);
        }
        let output_sha256 = ContentDigest::of(binding.output);
        if output_sha256.as_bytes() == &binding.manifest.expected_source_sha256() {
            return Err(StoredCommitError::Binding);
        }
        let manifest_sha256 = binding.manifest.canonical_sha256().map_err(|_| StoredCommitError::Binding)?;
        Ok(Self {
            artifacts, revisions, context, revision_context, binding, manifest_sha256,
            output_sha256, clock, attempted: false, outcome: None, error: None,
            retained_result: None, retained_intent: None, retained_precommit: None, intent_sha256: None, service_request: None, service_receipt: None,
            job_registration: None, registered_job_intent: None,
            registration_response: None,precommit_guard:None,manifest_archive:None,
        })
    }

    /// Adds a restriction once, before execution. Existing guards cannot be replaced after failure or success.
    /// # Errors
    /// Leaves this CAS and retained recovery descriptors intact on rejection.
    pub fn require_precommit_guard(&mut self,guard:Box<dyn StoredPrecommitGuard+'a>)->Result<(),StoredCommitError>{
        if self.attempted||self.precommit_guard.is_some(){return Err(StoredCommitError::CurrentGuard);}
        self.precommit_guard=Some(guard);Ok(())
    }
    fn check_precommit_guard(&mut self)->Result<(),StoredCommitError>{
        if let Some(guard)=self.precommit_guard.as_mut(){guard.check()?;}Ok(())
    }

    #[must_use]
    pub const fn error(&self) -> Option<StoredCommitError> { self.error }
    /// Recovery identity even when ingest returned an error after a possible side effect.
    #[must_use]
    pub const fn output_sha256(&self) -> ContentDigest { self.output_sha256 }
    #[must_use]
    pub const fn retained_result(&self) -> Option<&ArtifactDescriptor> { self.retained_result.as_ref() }
    #[must_use]
    pub const fn retained_intent(&self) -> Option<&ArtifactDescriptor> { self.retained_intent.as_ref() }
    #[must_use]
    pub const fn retained_precommit(&self) -> Option<&ArtifactDescriptor> { self.retained_precommit.as_ref() }
    #[must_use]
    pub const fn intent_sha256(&self) -> Option<ContentDigest> { self.intent_sha256 }
    #[must_use]
    pub const fn service_request(&self) -> Option<&ServiceRequest> { self.service_request.as_ref() }
    #[must_use]
    pub const fn service_receipt(&self) -> Option<&RevisionReceipt> { self.service_receipt.as_ref() }
    #[must_use]
    pub const fn registered_job_intent(&self) -> Option<&StoredCommitIntentRecord> { self.registered_job_intent.as_ref() }
    /// Diagnostic response, including a rejected foreign row. Not a confirmed registration.
    #[must_use]
    pub const fn registration_response(&self) -> Option<&StoredCommitIntentRecord> { self.registration_response.as_ref() }

    fn fresh_source(&mut self) -> Result<artifact_service::ArtifactId, StoredCommitError> {
        let now = (self.clock)();
        let head = self.revisions.head(self.revision_context, self.binding.project, self.binding.branch)
            .map_err(|_| StoredCommitError::Source)?;
        if head != self.binding.expected_head { return Err(StoredCommitError::Conflict); }
        let revision = head.revision_id().ok_or(StoredCommitError::Source)?;
        let node = self.revisions.node(self.revision_context, self.binding.project, revision)
            .map_err(|_| StoredCommitError::Source)?;
        if !node.sealed() || node.project_id() != self.binding.project || node.revision_id() != revision
            || node.committed_generation() != head.generation()
            || node.result_artifact_id().public_id() != self.binding.manifest.source_artifact_id().as_str()
        { return Err(StoredCommitError::Source); }
        let source = node.result_artifact_id();
        let descriptor = self.artifacts.get_descriptor(self.context, source, now)
            .map_err(|_| StoredCommitError::Source)?;
        if !available(&descriptor) || descriptor.artifact_id != source
            || descriptor.size_bytes != self.binding.manifest.expected_source_size()
            || descriptor.sha256.as_bytes() != &self.binding.manifest.expected_source_sha256()
        { return Err(StoredCommitError::Source); }
        let bytes = self.artifacts.download(self.context, source, now).map_err(|_| StoredCommitError::Source)?;
        if bytes.len() as u64 != descriptor.size_bytes || ContentDigest::of(&bytes) != descriptor.sha256 {
            return Err(StoredCommitError::Source);
        }
        // The eventual service CAS, not these observations, arbitrates the head race.
        if self.revisions.head(self.revision_context, self.binding.project, self.binding.branch)
            .map_err(|_| StoredCommitError::Source)? != head
        { return Err(StoredCommitError::Conflict); }
        Ok(source)
    }

    fn commit_once(&mut self, request: &RevisionCommitRequest) -> Result<RevisionCasOutcome, StoredCommitError> {
        if request.transaction_id() != self.binding.manifest.transaction_id()
            || request.base_revision() != self.binding.manifest.base_revision()
            || request.source_artifact_id() != self.binding.manifest.source_artifact_id()
            || request.manifest_sha256() != self.manifest_sha256
            || &request.result_sha256() != self.output_sha256.as_bytes()
            || request.result_size() != self.binding.output.len() as u64
        { return Err(StoredCommitError::Binding); }
        let source = self.fresh_source()?;
        self.check_precommit_guard()?;
        let now = (self.clock)();
        let result = self.artifacts.ingest(self.context, IngestRequest {
            bytes: self.binding.output.to_vec(), media_type: MediaType::parse(HWPX_MEDIA).map_err(|_| StoredCommitError::Artifact)?,
            file_name: FileName::parse("result.hwpx").map_err(|_| StoredCommitError::Artifact)?, kind: ArtifactKind::Result,
        }, now).map_err(|_| StoredCommitError::Artifact)?;
        self.retained_result = Some(result.clone());
        if !available(&result) || result.artifact_id == source || result.sha256 != self.output_sha256
            || result.size_bytes != request.result_size()
        { return Err(StoredCommitError::Artifact); }
        {
            let readback = self.artifacts.download(self.context, result.artifact_id, (self.clock)())
                .map_err(|_| StoredCommitError::Artifact)?;
            if readback != self.binding.output { return Err(StoredCommitError::Artifact); }
        }
        if self.fresh_source()? != source { return Err(StoredCommitError::Source); }
        let current_result = self.artifacts.get_descriptor(self.context, result.artifact_id, (self.clock)())
            .map_err(|_| StoredCommitError::Artifact)?;
        if !available(&current_result) || current_result.sha256 != result.sha256
            || current_result.size_bytes != result.size_bytes
        { return Err(StoredCommitError::Artifact); }
        let base = self.binding.expected_head.revision_id().ok_or(StoredCommitError::Binding)?;
        let service_request = ServiceRequest::new(
            self.binding.commit, self.binding.project, self.binding.branch, self.binding.expected_head,
            self.binding.new_revision, vec![base], source, result.artifact_id, None,
            ContentDigest::parse(&hex::encode(self.binding.manifest.compiled_plan_sha256())).map_err(|_| StoredCommitError::Binding)?,
            RevisionValidationState::Verified, self.binding.validation_summary,
            ContentDigest::parse(&hex::encode(request.canonical_sha256().map_err(|_| StoredCommitError::Binding)?))
                .map_err(|_| StoredCommitError::Binding)?,
        ).map_err(|_| StoredCommitError::Binding)?;
        self.service_request = Some(service_request.clone());
        self.persist_precommit(request)?;
        self.persist_intent(&service_request)?;
        self.register_job_intent(&service_request)?;
        // Intent storage itself crosses service boundaries: recheck before the only CAS.
        if self.fresh_source()? != source { return Err(StoredCommitError::Source); }
        let final_result = self.artifacts.get_descriptor(self.context, result.artifact_id, (self.clock)())
            .map_err(|_| StoredCommitError::Artifact)?;
        if !available(&final_result) || final_result.sha256 != result.sha256 || final_result.size_bytes != result.size_bytes {
            return Err(StoredCommitError::Artifact);
        }
        self.check_precommit_guard()?;
        match self.revisions.commit(self.revision_context, &service_request) {
            Ok(CommitOutcome::Committed(receipt)) => {
                let valid = receipt.request_sha256() == service_request.canonical_sha256().map_err(|_| StoredCommitError::Unknown)?
                    && receipt.committed_head().revision_id() == Some(self.binding.new_revision)
                    && receipt.committed_head().generation() == self.binding.expected_head.generation().saturating_add(1);
                self.service_receipt = Some(receipt);
                if !valid { return Err(StoredCommitError::Unknown); }
                Ok(RevisionCasOutcome::Committed)
            }
            Ok(CommitOutcome::Conflict(_)) => Err(StoredCommitError::Conflict),
            Err(RevisionError::CommitOutcomeUnknown) => Err(StoredCommitError::Unknown),
            Err(_) => Err(StoredCommitError::Revision),
        }
    }
}

fn available(d: &ArtifactDescriptor) -> bool {
    d.kind == ArtifactKind::Result && d.storage_state == StorageState::Available
        && d.validation_state == ValidationState::Verified && d.quarantine_reason.is_none()
        && d.media_type.as_str() == HWPX_MEDIA && d.size_bytes > 0 && d.size_bytes <= MAX_BYTES
}

impl<R, B, S, V, F> RevisionCas for StoredResultRevisionCas<'_, R, B, S, V, F>
where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner,
    V: RevisionRepository, F: FnMut() -> u64,
{
    fn compare_and_swap(&mut self, request: &RevisionCommitRequest) -> RevisionCasOutcome {
        if self.attempted {
            return if matches!(self.outcome, Some(RevisionCasOutcome::Committed | RevisionCasOutcome::Unknown)) {
                RevisionCasOutcome::Unknown
            } else { RevisionCasOutcome::Failed };
        }
        self.attempted = true;
        let outcome = match self.commit_once(request) {
            Ok(outcome) => outcome,
            Err(error) => {
                self.error = Some(error);
                match error { StoredCommitError::Unknown => RevisionCasOutcome::Unknown,
                    StoredCommitError::Conflict => RevisionCasOutcome::Conflict, _ => RevisionCasOutcome::Failed }
            }
        };
        self.outcome = Some(outcome);
        outcome
    }
}
