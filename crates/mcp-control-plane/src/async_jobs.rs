use std::collections::BTreeMap;
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead as _, BufReader, Write as _};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, MutexGuard};

use artifact_service::{ContentDigest, TenantId};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use uuid::Uuid;

use crate::ToolKind;
use crate::handler::{AuthorizedToolCall, GatewayError, ToolServiceGateway, ToolServiceOutput};
use crate::strict_json::parse_unique_value;

const JOURNAL_SCHEMA_VERSION: &str = "hwpx-agent.p15-job-journal/v1";
const JOURNAL_FILE_NAME: &str = "p15-job-journal-v1.jsonl";
const MAX_JOBS: usize = 4_096;
const MAX_JOURNAL_ENTRIES: u64 = 65_536;
const MAX_JOURNAL_BYTES: u64 = 67_108_864;
const MAX_JOURNAL_ENTRY_BYTES: usize = 1_048_576;
const MAX_EVENTS_PER_JOB: usize = 256;
const MAX_PROGRESS_EVENTS_PER_JOB: usize = 248;
const MAX_EVENT_PAGE: usize = 200;
const MAX_RESULT_ARTIFACTS: usize = 128;

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum AsyncJobError {
    #[error("the durable job store configuration is invalid")]
    InvalidConfiguration,
    #[error("the durable job store is corrupt")]
    StoreCorrupt,
    #[error("the durable job store reached a bounded capacity")]
    CapacityExceeded,
    #[error("the requested job was not found")]
    NotFound,
    #[error("the job request conflicts with durable state")]
    Conflict,
    #[error("the requested job transition is invalid")]
    InvalidTransition,
    #[error("the worker must acknowledge the pending cancellation")]
    CancellationPending,
    #[error("the durable job store is unavailable")]
    StorageUnavailable,
}

impl From<AsyncJobError> for GatewayError {
    fn from(error: AsyncJobError) -> Self {
        match error {
            AsyncJobError::NotFound => Self::NotFound,
            AsyncJobError::Conflict
            | AsyncJobError::InvalidTransition
            | AsyncJobError::CancellationPending => Self::Conflict,
            AsyncJobError::InvalidConfiguration | AsyncJobError::StoreCorrupt => Self::Rejected,
            AsyncJobError::CapacityExceeded | AsyncJobError::StorageUnavailable => {
                Self::Unavailable
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum JobProgressStage {
    Preflight,
    Materialize,
    Execute,
    Reopen,
    Validate,
    Render,
    VisualDiff,
    Export,
    Commit,
}

impl JobProgressStage {
    const fn name(self) -> &'static str {
        match self {
            Self::Preflight => "preflight",
            Self::Materialize => "materialize",
            Self::Execute => "execute",
            Self::Reopen => "reopen",
            Self::Validate => "validate",
            Self::Render => "render",
            Self::VisualDiff => "visual_diff",
            Self::Export => "export",
            Self::Commit => "commit",
        }
    }

    const fn public_state(self) -> PublicJobState {
        match self {
            Self::Validate => PublicJobState::Validating,
            Self::Commit => PublicJobState::Committing,
            Self::Preflight
            | Self::Materialize
            | Self::Execute
            | Self::Reopen
            | Self::Render
            | Self::VisualDiff
            | Self::Export => PublicJobState::Running,
        }
    }

    fn parse(value: &str) -> Option<Self> {
        [
            Self::Preflight,
            Self::Materialize,
            Self::Execute,
            Self::Reopen,
            Self::Validate,
            Self::Render,
            Self::VisualDiff,
            Self::Export,
            Self::Commit,
        ]
        .into_iter()
        .find(|stage| stage.name() == value)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum PublicJobState {
    Queued,
    Leasing,
    Running,
    Validating,
    Committing,
    Succeeded,
    Failed,
    Cancelled,
    Expired,
    Quarantined,
}

impl PublicJobState {
    const fn name(self) -> &'static str {
        match self {
            Self::Queued => "queued",
            Self::Leasing => "leasing",
            Self::Running => "running",
            Self::Validating => "validating",
            Self::Committing => "committing",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
            Self::Expired => "expired",
            Self::Quarantined => "quarantined",
        }
    }

    const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Succeeded | Self::Failed | Self::Cancelled | Self::Expired | Self::Quarantined
        )
    }

    const fn progress_rank(self) -> Option<u8> {
        match self {
            Self::Queued => Some(0),
            Self::Leasing => Some(1),
            Self::Running => Some(2),
            Self::Validating => Some(3),
            Self::Committing => Some(4),
            Self::Succeeded
            | Self::Failed
            | Self::Cancelled
            | Self::Expired
            | Self::Quarantined => None,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum EventKind {
    Accepted,
    Progress,
    CancellationRequested,
    CancellationRejected,
    Terminal,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredJobEvent {
    sequence: u64,
    kind: EventKind,
    state: PublicJobState,
    stage: String,
    completed_units: u64,
    total_units: Option<u64>,
    message: String,
    receipt_id: Option<String>,
    updated_at_unix_seconds: u64,
}

#[derive(Clone)]
pub struct JobEventPage {
    events: Vec<StoredJobEvent>,
    truncated_before_sequence: Option<u64>,
}

impl JobEventPage {
    pub(crate) fn append_to_meta(self, meta: &mut Map<String, Value>) {
        let events = serde_json::to_value(self.events).unwrap_or_else(|_| Value::Array(Vec::new()));
        meta.insert("hwpx/jobEvents".to_owned(), events);
        if let Some(sequence) = self.truncated_before_sequence {
            meta.insert(
                "hwpx/jobEventsTruncatedBeforeSequence".to_owned(),
                Value::from(sequence),
            );
        }
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.events.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.events.is_empty()
    }
}

impl fmt::Debug for JobEventPage {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("JobEventPage")
            .field("event_count", &self.events.len())
            .field("truncated", &self.truncated_before_sequence.is_some())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
#[allow(clippy::struct_field_names)]
pub struct JobLocator {
    tenant_id: TenantId,
    project_id: String,
    job_id: String,
}

impl JobLocator {
    /// Creates one exact internal worker locator without retaining a user token.
    ///
    /// # Errors
    ///
    /// Rejects identifiers outside the frozen P15 public shape.
    pub fn new(
        tenant_id: TenantId,
        project_id: impl Into<String>,
        job_id: impl Into<String>,
    ) -> Result<Self, AsyncJobError> {
        let project_id = project_id.into();
        let job_id = job_id.into();
        if !valid_prefixed_id(&project_id, "prj_") || !valid_prefixed_id(&job_id, "job_") {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        Ok(Self {
            tenant_id,
            project_id,
            job_id,
        })
    }

    #[must_use]
    pub fn job_id(&self) -> &str {
        &self.job_id
    }
}

impl fmt::Debug for JobLocator {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("JobLocator")
            .field("tenant_id", &"<redacted>")
            .field("project_id", &"<redacted>")
            .field("job_id", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct TerminalReceipt {
    receipt_id: String,
    terminal_state: PublicJobState,
    terminal_sequence: u64,
    created_at_unix_seconds: u64,
    result_sha256: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CancelState {
    Requested,
    Cancelled,
    AlreadyTerminal,
    NotCancellable,
}

impl CancelState {
    const fn name(self) -> &'static str {
        match self {
            Self::Requested => "requested",
            Self::Cancelled => "cancelled",
            Self::AlreadyTerminal => "already_terminal",
            Self::NotCancellable => "not_cancellable",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CancellationRecord {
    idempotency_key: String,
    reason_sha256: String,
    receipt_id: String,
    response_state: CancelState,
    requested_at_unix_seconds: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredJob {
    tenant_id: String,
    project_id: String,
    subject_sha256: String,
    job_id: String,
    submit_request_id: String,
    idempotency_key: String,
    tool_name: String,
    arguments_sha256: String,
    state: PublicJobState,
    stage: String,
    completed_units: u64,
    total_units: Option<u64>,
    result_artifact_ids: Vec<String>,
    cancellation: Option<CancellationRecord>,
    cancellation_requested: bool,
    terminal_error_code: Option<String>,
    terminal_receipt: Option<TerminalReceipt>,
    events: Vec<StoredJobEvent>,
    created_at_unix_seconds: u64,
    updated_at_unix_seconds: u64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct JournalEntry {
    schema_version: String,
    sequence: u64,
    job: StoredJob,
    checksum_sha256: String,
}

#[derive(Serialize)]
struct JournalChecksum<'a> {
    schema_version: &'static str,
    sequence: u64,
    job: &'a StoredJob,
}

#[derive(Default)]
struct StoreState {
    journal_sequence: u64,
    jobs: BTreeMap<String, StoredJob>,
    request_index: BTreeMap<String, String>,
}

#[derive(Clone)]
pub struct DurableJobStore {
    journal_path: Arc<PathBuf>,
    state: Arc<Mutex<StoreState>>,
}

impl fmt::Debug for DurableJobStore {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let job_count = self.state.lock().map_or(0, |state| state.jobs.len());
        formatter
            .debug_struct("DurableJobStore")
            .field("journal_path", &"<redacted>")
            .field("job_count", &job_count)
            .finish()
    }
}

impl DurableJobStore {
    /// Opens or creates one bounded append-only local reference journal.
    ///
    /// # Errors
    ///
    /// Fails closed on links, malformed history, checksum drift, invalid evolution or I/O failure.
    pub fn open(root: impl AsRef<Path>) -> Result<Self, AsyncJobError> {
        let root = root.as_ref();
        if root.as_os_str().is_empty() {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        fs::create_dir_all(root).map_err(|_| AsyncJobError::StorageUnavailable)?;
        let metadata = fs::symlink_metadata(root).map_err(|_| AsyncJobError::StorageUnavailable)?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let canonical_root =
            fs::canonicalize(root).map_err(|_| AsyncJobError::StorageUnavailable)?;
        let journal_path = canonical_root.join(JOURNAL_FILE_NAME);
        if journal_path.exists() {
            let journal_metadata = fs::symlink_metadata(&journal_path)
                .map_err(|_| AsyncJobError::StorageUnavailable)?;
            if journal_metadata.file_type().is_symlink() || !journal_metadata.is_file() {
                return Err(AsyncJobError::InvalidConfiguration);
            }
            if journal_metadata.len() > MAX_JOURNAL_BYTES {
                return Err(AsyncJobError::CapacityExceeded);
            }
        }
        let state = replay_journal(&journal_path)?;
        Ok(Self {
            journal_path: Arc::new(journal_path),
            state: Arc::new(Mutex::new(state)),
        })
    }

    /// Appends one monotonic, bounded worker progress snapshot.
    ///
    /// # Errors
    ///
    /// Rejects stale time, backward stages, invalid units, terminal jobs and pending cancellation.
    pub fn record_progress(
        &self,
        locator: &JobLocator,
        now_unix_seconds: u64,
        stage: JobProgressStage,
        completed_units: u64,
        total_units: Option<u64>,
    ) -> Result<(), AsyncJobError> {
        if total_units.is_some_and(|total| total == 0 || completed_units > total) {
            return Err(AsyncJobError::InvalidTransition);
        }
        let mut store = self.lock()?;
        let key = locator_key(locator);
        let current = store
            .jobs
            .get(&key)
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        if current.cancellation_requested {
            return Err(AsyncJobError::CancellationPending);
        }
        if current.state.is_terminal() || now_unix_seconds < current.updated_at_unix_seconds {
            return Err(AsyncJobError::InvalidTransition);
        }
        let next_state = stage.public_state();
        let current_rank = current
            .state
            .progress_rank()
            .ok_or(AsyncJobError::InvalidTransition)?;
        let next_rank = next_state
            .progress_rank()
            .ok_or(AsyncJobError::InvalidTransition)?;
        if next_rank < current_rank {
            return Err(AsyncJobError::InvalidTransition);
        }
        if next_rank == current_rank
            && current.state != PublicJobState::Queued
            && JobProgressStage::parse(&current.stage)
                .is_none_or(|current_stage| stage < current_stage)
        {
            return Err(AsyncJobError::InvalidTransition);
        }
        if current.stage == stage.name()
            && (completed_units < current.completed_units || total_units != current.total_units)
        {
            return Err(AsyncJobError::InvalidTransition);
        }
        if current.events.len() >= MAX_PROGRESS_EVENTS_PER_JOB {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let mut candidate = current;
        candidate.state = next_state;
        stage.name().clone_into(&mut candidate.stage);
        candidate.completed_units = completed_units;
        candidate.total_units = total_units;
        candidate.updated_at_unix_seconds = now_unix_seconds;
        push_event(
            &mut candidate,
            EventKind::Progress,
            "Job progress advanced.",
            now_unix_seconds,
        )?;
        self.persist_locked(&mut store, candidate)?;
        Ok(())
    }

    /// Commits the only successful terminal receipt after the commit safe point.
    ///
    /// # Errors
    ///
    /// Rejects non-committing, cancelled, repeated or malformed completion.
    pub fn complete_success(
        &self,
        locator: &JobLocator,
        now_unix_seconds: u64,
        result_artifact_ids: impl IntoIterator<Item = String>,
    ) -> Result<String, AsyncJobError> {
        let artifacts: Vec<String> = result_artifact_ids.into_iter().collect();
        if artifacts.len() > MAX_RESULT_ARTIFACTS
            || artifacts
                .iter()
                .any(|artifact| !valid_prefixed_id(artifact, "art_"))
        {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let mut state = self.lock()?;
        let current = state
            .jobs
            .get(&locator_key(locator))
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        if current.state != PublicJobState::Committing
            || current.cancellation_requested
            || now_unix_seconds < current.updated_at_unix_seconds
        {
            return Err(AsyncJobError::InvalidTransition);
        }
        let mut candidate = current;
        candidate.state = PublicJobState::Succeeded;
        "completed".clone_into(&mut candidate.stage);
        candidate.result_artifact_ids = artifacts;
        candidate.updated_at_unix_seconds = now_unix_seconds;
        let receipt = terminal_receipt(&candidate, PublicJobState::Succeeded, now_unix_seconds)?;
        candidate.terminal_receipt = Some(receipt.clone());
        push_event(
            &mut candidate,
            EventKind::Terminal,
            "Job completed successfully.",
            now_unix_seconds,
        )?;
        sync_terminal_sequence(&mut candidate)?;
        self.persist_locked(&mut state, candidate)?;
        Ok(receipt.receipt_id)
    }

    /// Commits the only failure receipt for a nonterminal job.
    ///
    /// # Errors
    ///
    /// Rejects malformed public error codes, stale time and repeated terminalization.
    pub fn complete_failure(
        &self,
        locator: &JobLocator,
        now_unix_seconds: u64,
        error_code: &str,
    ) -> Result<String, AsyncJobError> {
        if !valid_error_code(error_code) {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let mut state = self.lock()?;
        let current = state
            .jobs
            .get(&locator_key(locator))
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        if current.cancellation_requested {
            return Err(AsyncJobError::CancellationPending);
        }
        if current.state.is_terminal() || now_unix_seconds < current.updated_at_unix_seconds {
            return Err(AsyncJobError::InvalidTransition);
        }
        let mut candidate = current;
        candidate.state = PublicJobState::Failed;
        "failed".clone_into(&mut candidate.stage);
        candidate.terminal_error_code = Some(error_code.to_owned());
        candidate.updated_at_unix_seconds = now_unix_seconds;
        let receipt = terminal_receipt(&candidate, PublicJobState::Failed, now_unix_seconds)?;
        candidate.terminal_receipt = Some(receipt.clone());
        push_event(
            &mut candidate,
            EventKind::Terminal,
            "Job ended without a committed result.",
            now_unix_seconds,
        )?;
        sync_terminal_sequence(&mut candidate)?;
        self.persist_locked(&mut state, candidate)?;
        Ok(receipt.receipt_id)
    }

    /// Acknowledges a requested cancellation at a worker safe point.
    ///
    /// # Errors
    ///
    /// Rejects jobs without a pending request, committing jobs and repeated terminalization.
    pub fn acknowledge_cancellation(
        &self,
        locator: &JobLocator,
        now_unix_seconds: u64,
    ) -> Result<String, AsyncJobError> {
        let mut state = self.lock()?;
        let current = state
            .jobs
            .get(&locator_key(locator))
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        let cancellation = current
            .cancellation
            .clone()
            .filter(|_| current.cancellation_requested)
            .ok_or(AsyncJobError::InvalidTransition)?;
        if current.state == PublicJobState::Committing
            || current.state.is_terminal()
            || now_unix_seconds < current.updated_at_unix_seconds
        {
            return Err(AsyncJobError::InvalidTransition);
        }
        let mut candidate = current;
        candidate.state = PublicJobState::Cancelled;
        "cancelled".clone_into(&mut candidate.stage);
        candidate.cancellation_requested = false;
        candidate.updated_at_unix_seconds = now_unix_seconds;
        candidate.terminal_receipt = Some(TerminalReceipt {
            receipt_id: cancellation.receipt_id.clone(),
            terminal_state: PublicJobState::Cancelled,
            terminal_sequence: 0,
            created_at_unix_seconds: now_unix_seconds,
            result_sha256: terminal_result_digest(&candidate, PublicJobState::Cancelled),
        });
        push_event(
            &mut candidate,
            EventKind::Terminal,
            "Job cancellation completed at a safe point.",
            now_unix_seconds,
        )?;
        sync_terminal_sequence(&mut candidate)?;
        self.persist_locked(&mut state, candidate)?;
        Ok(cancellation.receipt_id)
    }

    fn submit(&self, call: &AuthorizedToolCall) -> Result<SubmitOutcome, AsyncJobError> {
        if !is_async_submission(call.tool()) {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let project_id = call
            .project_id()
            .ok_or(AsyncJobError::InvalidConfiguration)?;
        let idempotency_key = required_string(call.arguments(), "idempotency_key")?;
        if !valid_idempotency_key(idempotency_key) {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let subject_sha256 = call.subject().hex();
        let tenant_id = call.tenant_id().canonical();
        let request_key = request_key(&tenant_id, project_id, &subject_sha256, idempotency_key);
        let job_id = derive_id("job_", request_key.as_bytes());
        let key = record_key(&tenant_id, project_id, &job_id);
        let arguments_sha256 = idempotent_arguments_digest(call.arguments())?;
        let mut state = self.lock()?;
        if let Some(existing_key) = state.request_index.get(&request_key) {
            let existing = state
                .jobs
                .get(existing_key)
                .cloned()
                .ok_or(AsyncJobError::StoreCorrupt)?;
            if existing.tool_name != call.tool().name()
                || existing.arguments_sha256 != arguments_sha256
            {
                return Err(AsyncJobError::Conflict);
            }
            return Ok(SubmitOutcome {
                job: existing,
                replayed: true,
            });
        }
        if state.jobs.len() >= MAX_JOBS || state.jobs.contains_key(&key) {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let total_units = initial_total_units(call.tool(), call.arguments());
        let now = call.now_unix_seconds();
        let mut job = StoredJob {
            tenant_id,
            project_id: project_id.to_owned(),
            subject_sha256,
            job_id,
            submit_request_id: call.request_id().to_owned(),
            idempotency_key: idempotency_key.to_owned(),
            tool_name: call.tool().name().to_owned(),
            arguments_sha256,
            state: PublicJobState::Queued,
            stage: "queued".to_owned(),
            completed_units: 0,
            total_units,
            result_artifact_ids: Vec::new(),
            cancellation: None,
            cancellation_requested: false,
            terminal_error_code: None,
            terminal_receipt: None,
            events: Vec::new(),
            created_at_unix_seconds: now,
            updated_at_unix_seconds: now,
        };
        push_event(&mut job, EventKind::Accepted, "Job accepted.", now)?;
        self.persist_locked(&mut state, job.clone())?;
        state.request_index.insert(request_key, key);
        Ok(SubmitOutcome {
            job,
            replayed: false,
        })
    }

    fn poll(
        &self,
        locator: &JobLocator,
        include_events: bool,
        cursor: Option<&str>,
        event_limit: usize,
    ) -> Result<PollOutcome, AsyncJobError> {
        if event_limit == 0 || event_limit > MAX_EVENT_PAGE {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let state = self.lock()?;
        let job = state
            .jobs
            .get(&locator_key(locator))
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        if !include_events {
            return Ok(PollOutcome {
                job,
                event_page: None,
                next_cursor: None,
            });
        }
        let after_sequence = cursor.map_or(Ok(0), |value| parse_cursor(value, &job.job_id))?;
        let last_sequence = job.events.last().map_or(0, |event| event.sequence);
        if after_sequence > last_sequence {
            return Err(AsyncJobError::Conflict);
        }
        let events: Vec<StoredJobEvent> = job
            .events
            .iter()
            .filter(|event| event.sequence > after_sequence)
            .take(event_limit)
            .cloned()
            .collect();
        let next_sequence = events.last().map_or(after_sequence, |event| event.sequence);
        let next_cursor = (next_sequence > 0).then(|| make_cursor(&job.job_id, next_sequence));
        let first_available = job.events.first().map_or(1, |event| event.sequence);
        let truncated_before_sequence =
            (after_sequence.saturating_add(1) < first_available).then_some(first_available);
        Ok(PollOutcome {
            job,
            event_page: Some(JobEventPage {
                events,
                truncated_before_sequence,
            }),
            next_cursor,
        })
    }

    fn cancel(
        &self,
        locator: &JobLocator,
        idempotency_key: &str,
        reason: &str,
        now_unix_seconds: u64,
    ) -> Result<CancelOutcome, AsyncJobError> {
        if !valid_idempotency_key(idempotency_key) || reason.is_empty() || reason.len() > 500 {
            return Err(AsyncJobError::InvalidConfiguration);
        }
        let reason_sha256 = ContentDigest::of(reason.as_bytes()).hex();
        let mut state = self.lock()?;
        let current = state
            .jobs
            .get(&locator_key(locator))
            .cloned()
            .ok_or(AsyncJobError::NotFound)?;
        if let Some(existing) = &current.cancellation {
            if existing.idempotency_key != idempotency_key
                || existing.reason_sha256 != reason_sha256
            {
                return Err(AsyncJobError::Conflict);
            }
            return Ok(CancelOutcome {
                state: existing.response_state,
                receipt_id: existing.receipt_id.clone(),
                replayed: true,
            });
        }
        if now_unix_seconds < current.updated_at_unix_seconds {
            return Err(AsyncJobError::Conflict);
        }
        let request_material = format!("{}\0{idempotency_key}", current.job_id);
        let request_receipt_id = derive_id("rcp_", request_material.as_bytes());
        let (cancel_state, receipt_id) = if current.state.is_terminal() {
            let receipt = current
                .terminal_receipt
                .as_ref()
                .ok_or(AsyncJobError::StoreCorrupt)?;
            (CancelState::AlreadyTerminal, receipt.receipt_id.clone())
        } else if current.state == PublicJobState::Committing {
            (CancelState::NotCancellable, request_receipt_id)
        } else if current.state == PublicJobState::Queued {
            (CancelState::Cancelled, request_receipt_id)
        } else {
            (CancelState::Requested, request_receipt_id)
        };
        let mut candidate = current;
        candidate.cancellation = Some(CancellationRecord {
            idempotency_key: idempotency_key.to_owned(),
            reason_sha256,
            receipt_id: receipt_id.clone(),
            response_state: cancel_state,
            requested_at_unix_seconds: now_unix_seconds,
        });
        match cancel_state {
            CancelState::Requested => {
                candidate.cancellation_requested = true;
                candidate.updated_at_unix_seconds = now_unix_seconds;
                push_event(
                    &mut candidate,
                    EventKind::CancellationRequested,
                    "Cancellation requested; waiting for a safe point.",
                    now_unix_seconds,
                )?;
            }
            CancelState::Cancelled => {
                candidate.state = PublicJobState::Cancelled;
                "cancelled".clone_into(&mut candidate.stage);
                candidate.updated_at_unix_seconds = now_unix_seconds;
                candidate.terminal_receipt = Some(TerminalReceipt {
                    receipt_id: receipt_id.clone(),
                    terminal_state: PublicJobState::Cancelled,
                    terminal_sequence: 0,
                    created_at_unix_seconds: now_unix_seconds,
                    result_sha256: terminal_result_digest(&candidate, PublicJobState::Cancelled),
                });
                push_event(
                    &mut candidate,
                    EventKind::Terminal,
                    "Queued job cancelled before execution.",
                    now_unix_seconds,
                )?;
                sync_terminal_sequence(&mut candidate)?;
            }
            CancelState::NotCancellable => {
                candidate.updated_at_unix_seconds = now_unix_seconds;
                push_event(
                    &mut candidate,
                    EventKind::CancellationRejected,
                    "Job is past its final cancellation safe point.",
                    now_unix_seconds,
                )?;
            }
            CancelState::AlreadyTerminal => {}
        }
        self.persist_locked(&mut state, candidate)?;
        Ok(CancelOutcome {
            state: cancel_state,
            receipt_id,
            replayed: false,
        })
    }

    fn lock(&self) -> Result<MutexGuard<'_, StoreState>, AsyncJobError> {
        self.state
            .lock()
            .map_err(|_| AsyncJobError::StorageUnavailable)
    }

    fn persist_locked(&self, state: &mut StoreState, job: StoredJob) -> Result<(), AsyncJobError> {
        validate_job(&job)?;
        if state.journal_sequence >= MAX_JOURNAL_ENTRIES {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let key = record_key(&job.tenant_id, &job.project_id, &job.job_id);
        if let Some(previous) = state.jobs.get(&key) {
            validate_evolution(previous, &job)?;
        }
        let sequence = state
            .journal_sequence
            .checked_add(1)
            .ok_or(AsyncJobError::CapacityExceeded)?;
        let checksum_sha256 = journal_checksum(sequence, &job)?;
        let entry = JournalEntry {
            schema_version: JOURNAL_SCHEMA_VERSION.to_owned(),
            sequence,
            job: job.clone(),
            checksum_sha256,
        };
        let mut encoded = serde_json::to_vec(&entry).map_err(|_| AsyncJobError::StoreCorrupt)?;
        encoded.push(b'\n');
        if encoded.len() > MAX_JOURNAL_ENTRY_BYTES {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let current_bytes = self
            .journal_path
            .metadata()
            .map_or(0, |metadata| metadata.len());
        if current_bytes.saturating_add(encoded.len() as u64) > MAX_JOURNAL_BYTES {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let mut stream = OpenOptions::new()
            .create(true)
            .append(true)
            .open(self.journal_path.as_ref())
            .map_err(|_| AsyncJobError::StorageUnavailable)?;
        stream
            .write_all(&encoded)
            .and_then(|()| stream.sync_all())
            .map_err(|_| AsyncJobError::StorageUnavailable)?;
        state.journal_sequence = sequence;
        state.jobs.insert(key, job);
        Ok(())
    }
}

#[derive(Debug)]
pub struct DurableAsyncJobGateway<G> {
    store: DurableJobStore,
    delegate: G,
}

impl<G> DurableAsyncJobGateway<G> {
    #[must_use]
    pub const fn new(store: DurableJobStore, delegate: G) -> Self {
        Self { store, delegate }
    }

    #[must_use]
    pub const fn store(&self) -> &DurableJobStore {
        &self.store
    }
}

impl<G> ToolServiceGateway for DurableAsyncJobGateway<G>
where
    G: ToolServiceGateway,
{
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        match call.tool() {
            ToolKind::DocumentCreate
            | ToolKind::DocumentEdit
            | ToolKind::DocumentTransform
            | ToolKind::DocumentValidate
            | ToolKind::DocumentRender
            | ToolKind::DocumentExport => {
                let outcome = self.store.submit(&call).map_err(GatewayError::from)?;
                let output = submission_output(
                    call.tool(),
                    call.request_id(),
                    &outcome.job.job_id,
                    call.arguments(),
                    outcome.replayed,
                );
                Ok(ToolServiceOutput::new(output))
            }
            ToolKind::JobGet => {
                let locator = locator_from_call(&call)?;
                let include_events = call
                    .arguments()
                    .get("include_events")
                    .and_then(Value::as_bool)
                    .ok_or(GatewayError::Rejected)?;
                let cursor = call.arguments().get("event_cursor").and_then(Value::as_str);
                let limit = call
                    .arguments()
                    .get("event_limit")
                    .and_then(Value::as_u64)
                    .map_or(Ok(50), usize::try_from)
                    .map_err(|_| GatewayError::Rejected)?;
                let poll = self
                    .store
                    .poll(&locator, include_events, cursor, limit)
                    .map_err(GatewayError::from)?;
                let output =
                    job_get_output(call.request_id(), &poll.job, poll.next_cursor.as_deref());
                Ok(match poll.event_page {
                    Some(page) => ToolServiceOutput::with_job_event_page(output, page),
                    None => ToolServiceOutput::new(output),
                })
            }
            ToolKind::JobCancel => {
                let locator = locator_from_call(&call)?;
                let idempotency_key = required_string(call.arguments(), "idempotency_key")
                    .map_err(GatewayError::from)?;
                let reason =
                    required_string(call.arguments(), "reason").map_err(GatewayError::from)?;
                let cancelled = self
                    .store
                    .cancel(&locator, idempotency_key, reason, call.now_unix_seconds())
                    .map_err(GatewayError::from)?;
                Ok(ToolServiceOutput::new(cancel_output(
                    call.request_id(),
                    locator.job_id(),
                    &cancelled,
                )))
            }
            _ => self.delegate.dispatch(call),
        }
    }
}

#[derive(Clone)]
struct SubmitOutcome {
    job: StoredJob,
    replayed: bool,
}

struct PollOutcome {
    job: StoredJob,
    event_page: Option<JobEventPage>,
    next_cursor: Option<String>,
}

struct CancelOutcome {
    state: CancelState,
    receipt_id: String,
    replayed: bool,
}

fn replay_journal(path: &Path) -> Result<StoreState, AsyncJobError> {
    if !path.exists() {
        return Ok(StoreState::default());
    }
    let stream = File::open(path).map_err(|_| AsyncJobError::StorageUnavailable)?;
    let mut reader = BufReader::new(stream);
    let mut state = StoreState::default();
    let mut buffer = Vec::new();
    loop {
        buffer.clear();
        let read = reader
            .read_until(b'\n', &mut buffer)
            .map_err(|_| AsyncJobError::StorageUnavailable)?;
        if read == 0 {
            break;
        }
        if buffer.len() > MAX_JOURNAL_ENTRY_BYTES
            || !buffer.ends_with(b"\n")
            || state.journal_sequence >= MAX_JOURNAL_ENTRIES
        {
            return Err(AsyncJobError::StoreCorrupt);
        }
        buffer.pop();
        if buffer.last() == Some(&b'\r') {
            buffer.pop();
        }
        let value = parse_unique_value(&buffer).map_err(|()| AsyncJobError::StoreCorrupt)?;
        let entry: JournalEntry =
            serde_json::from_value(value).map_err(|_| AsyncJobError::StoreCorrupt)?;
        let expected_sequence = state
            .journal_sequence
            .checked_add(1)
            .ok_or(AsyncJobError::StoreCorrupt)?;
        if entry.schema_version != JOURNAL_SCHEMA_VERSION
            || entry.sequence != expected_sequence
            || entry.checksum_sha256 != journal_checksum(entry.sequence, &entry.job)?
        {
            return Err(AsyncJobError::StoreCorrupt);
        }
        validate_job(&entry.job)?;
        let key = record_key(
            &entry.job.tenant_id,
            &entry.job.project_id,
            &entry.job.job_id,
        );
        if let Some(previous) = state.jobs.get(&key) {
            validate_evolution(previous, &entry.job)?;
        } else if state.jobs.len() >= MAX_JOBS {
            return Err(AsyncJobError::CapacityExceeded);
        }
        let request = request_key(
            &entry.job.tenant_id,
            &entry.job.project_id,
            &entry.job.subject_sha256,
            &entry.job.idempotency_key,
        );
        if let Some(existing_key) = state.request_index.get(&request)
            && existing_key != &key
        {
            return Err(AsyncJobError::StoreCorrupt);
        }
        state.request_index.insert(request, key.clone());
        state.jobs.insert(key, entry.job);
        state.journal_sequence = entry.sequence;
    }
    Ok(state)
}

#[allow(clippy::too_many_lines)]
fn validate_job(job: &StoredJob) -> Result<(), AsyncJobError> {
    if job.tenant_id.len() != 32
        || !lower_hex(&job.tenant_id)
        || !valid_prefixed_id(&job.project_id, "prj_")
        || !valid_prefixed_id(&job.job_id, "job_")
        || !valid_prefixed_id(&job.submit_request_id, "req_")
        || !valid_idempotency_key(&job.idempotency_key)
        || ToolKind::parse(&job.tool_name).is_none_or(|tool| !is_async_submission(tool))
        || job.arguments_sha256.len() != 64
        || !lower_hex(&job.arguments_sha256)
        || job.subject_sha256.len() != 64
        || !lower_hex(&job.subject_sha256)
        || job.stage.is_empty()
        || job.stage.len() > 64
        || !valid_stage(&job.stage)
        || job
            .total_units
            .is_some_and(|total| total == 0 || job.completed_units > total)
        || job.result_artifact_ids.len() > MAX_RESULT_ARTIFACTS
        || job
            .result_artifact_ids
            .iter()
            .any(|artifact| !valid_prefixed_id(artifact, "art_"))
        || job.events.is_empty()
        || job.events.len() > MAX_EVENTS_PER_JOB
        || job.updated_at_unix_seconds < job.created_at_unix_seconds
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    let first = &job.events[0];
    if first.sequence != 1
        || first.kind != EventKind::Accepted
        || first.state != PublicJobState::Queued
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    let mut previous_time = job.created_at_unix_seconds;
    for (index, event) in job.events.iter().enumerate() {
        if event.sequence != (index as u64).saturating_add(1)
            || event.updated_at_unix_seconds < previous_time
            || event.message.is_empty()
            || event.message.len() > 256
            || event.message.chars().any(char::is_control)
            || !valid_stage(&event.stage)
            || event
                .total_units
                .is_some_and(|total| total == 0 || event.completed_units > total)
            || (event.kind == EventKind::Terminal)
                != event
                    .receipt_id
                    .as_deref()
                    .is_some_and(|receipt| valid_prefixed_id(receipt, "rcp_"))
        {
            return Err(AsyncJobError::StoreCorrupt);
        }
        previous_time = event.updated_at_unix_seconds;
    }
    let last = job.events.last().ok_or(AsyncJobError::StoreCorrupt)?;
    if last.state != job.state
        || last.stage != job.stage
        || last.completed_units != job.completed_units
        || last.total_units != job.total_units
        || last.updated_at_unix_seconds != job.updated_at_unix_seconds
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    let terminal_events = job
        .events
        .iter()
        .filter(|event| event.kind == EventKind::Terminal)
        .count();
    if job.state.is_terminal() {
        let receipt = job
            .terminal_receipt
            .as_ref()
            .ok_or(AsyncJobError::StoreCorrupt)?;
        if terminal_events != 1
            || receipt.terminal_state != job.state
            || receipt.terminal_sequence != last.sequence
            || !valid_prefixed_id(&receipt.receipt_id, "rcp_")
            || receipt.result_sha256.len() != 64
            || !lower_hex(&receipt.result_sha256)
            || receipt.result_sha256 != terminal_result_digest(job, job.state)
            || receipt.created_at_unix_seconds != last.updated_at_unix_seconds
            || last.receipt_id.as_deref() != Some(&receipt.receipt_id)
        {
            return Err(AsyncJobError::StoreCorrupt);
        }
        let expected_receipt_id = if job.state == PublicJobState::Cancelled {
            job.cancellation
                .as_ref()
                .map(|cancellation| cancellation.receipt_id.as_str())
                .ok_or(AsyncJobError::StoreCorrupt)?
                .to_owned()
        } else {
            terminal_receipt_id(job, job.state)
        };
        if receipt.receipt_id != expected_receipt_id {
            return Err(AsyncJobError::StoreCorrupt);
        }
    } else if terminal_events != 0 || job.terminal_receipt.is_some() {
        return Err(AsyncJobError::StoreCorrupt);
    }
    if job.cancellation_requested
        && (job.cancellation.is_none()
            || job.state.is_terminal()
            || job.state == PublicJobState::Committing)
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    if let Some(cancellation) = &job.cancellation
        && (!valid_idempotency_key(&cancellation.idempotency_key)
            || cancellation.reason_sha256.len() != 64
            || !lower_hex(&cancellation.reason_sha256)
            || !valid_prefixed_id(&cancellation.receipt_id, "rcp_"))
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    Ok(())
}

fn validate_evolution(previous: &StoredJob, next: &StoredJob) -> Result<(), AsyncJobError> {
    if previous.tenant_id != next.tenant_id
        || previous.project_id != next.project_id
        || previous.subject_sha256 != next.subject_sha256
        || previous.job_id != next.job_id
        || previous.submit_request_id != next.submit_request_id
        || previous.idempotency_key != next.idempotency_key
        || previous.tool_name != next.tool_name
        || previous.arguments_sha256 != next.arguments_sha256
        || previous.created_at_unix_seconds != next.created_at_unix_seconds
        || previous.events.len() > next.events.len()
        || previous.events != next.events[..previous.events.len()]
        || previous.updated_at_unix_seconds > next.updated_at_unix_seconds
        || previous
            .terminal_receipt
            .as_ref()
            .is_some_and(|receipt| next.terminal_receipt.as_ref() != Some(receipt))
        || previous
            .cancellation
            .as_ref()
            .is_some_and(|cancel| next.cancellation.as_ref() != Some(cancel))
    {
        return Err(AsyncJobError::StoreCorrupt);
    }
    Ok(())
}

fn push_event(
    job: &mut StoredJob,
    kind: EventKind,
    message: &str,
    now_unix_seconds: u64,
) -> Result<(), AsyncJobError> {
    if job.events.len() >= MAX_EVENTS_PER_JOB {
        return Err(AsyncJobError::CapacityExceeded);
    }
    let sequence = (job.events.len() as u64)
        .checked_add(1)
        .ok_or(AsyncJobError::CapacityExceeded)?;
    job.events.push(StoredJobEvent {
        sequence,
        kind,
        state: job.state,
        stage: job.stage.clone(),
        completed_units: job.completed_units,
        total_units: job.total_units,
        message: message.to_owned(),
        receipt_id: (kind == EventKind::Terminal)
            .then(|| {
                job.terminal_receipt
                    .as_ref()
                    .map(|receipt| receipt.receipt_id.clone())
            })
            .flatten(),
        updated_at_unix_seconds: now_unix_seconds,
    });
    Ok(())
}

fn sync_terminal_sequence(job: &mut StoredJob) -> Result<(), AsyncJobError> {
    let sequence = job
        .events
        .last()
        .filter(|event| event.kind == EventKind::Terminal)
        .map(|event| event.sequence)
        .ok_or(AsyncJobError::StoreCorrupt)?;
    let receipt = job
        .terminal_receipt
        .as_mut()
        .ok_or(AsyncJobError::StoreCorrupt)?;
    receipt.terminal_sequence = sequence;
    Ok(())
}

fn terminal_receipt(
    job: &StoredJob,
    terminal_state: PublicJobState,
    now_unix_seconds: u64,
) -> Result<TerminalReceipt, AsyncJobError> {
    if job.terminal_receipt.is_some() || !terminal_state.is_terminal() {
        return Err(AsyncJobError::InvalidTransition);
    }
    Ok(TerminalReceipt {
        receipt_id: terminal_receipt_id(job, terminal_state),
        terminal_state,
        terminal_sequence: 0,
        created_at_unix_seconds: now_unix_seconds,
        result_sha256: terminal_result_digest(job, terminal_state),
    })
}

fn terminal_result_digest(job: &StoredJob, state: PublicJobState) -> String {
    let mut hasher = Sha256::new();
    hasher.update(JOURNAL_SCHEMA_VERSION.as_bytes());
    hasher.update([0]);
    hasher.update(job.job_id.as_bytes());
    hasher.update([0]);
    hasher.update(job.arguments_sha256.as_bytes());
    hasher.update([0]);
    hasher.update(state.name().as_bytes());
    hasher.update([0]);
    hasher.update(job.stage.as_bytes());
    hasher.update([0]);
    hasher.update(job.completed_units.to_le_bytes());
    hasher.update(job.total_units.unwrap_or(0).to_le_bytes());
    hasher.update([u8::from(job.total_units.is_some())]);
    for artifact in &job.result_artifact_ids {
        hasher.update(artifact.as_bytes());
        hasher.update([0]);
    }
    if let Some(error_code) = &job.terminal_error_code {
        hasher.update(error_code.as_bytes());
    }
    hasher.update([0]);
    if state == PublicJobState::Cancelled
        && let Some(cancellation) = &job.cancellation
    {
        hasher.update(cancellation.reason_sha256.as_bytes());
        hasher.update([0]);
        hasher.update(cancellation.receipt_id.as_bytes());
    }
    hex::encode(hasher.finalize())
}

fn terminal_receipt_id(job: &StoredJob, terminal_state: PublicJobState) -> String {
    let material = format!(
        "{}\0{}\0{}\0{}",
        job.tenant_id,
        job.project_id,
        job.job_id,
        terminal_state.name()
    );
    derive_id("rcp_", material.as_bytes())
}

fn idempotent_arguments_digest(arguments: &Value) -> Result<String, AsyncJobError> {
    let mut semantic = arguments.clone();
    semantic
        .as_object_mut()
        .ok_or(AsyncJobError::InvalidConfiguration)?
        .remove("request_id");
    let encoded = serde_json::to_vec(&semantic).map_err(|_| AsyncJobError::InvalidConfiguration)?;
    Ok(ContentDigest::of(&encoded).hex())
}

fn journal_checksum(sequence: u64, job: &StoredJob) -> Result<String, AsyncJobError> {
    let encoded = serde_json::to_vec(&JournalChecksum {
        schema_version: JOURNAL_SCHEMA_VERSION,
        sequence,
        job,
    })
    .map_err(|_| AsyncJobError::StoreCorrupt)?;
    Ok(hex::encode(Sha256::digest(encoded)))
}

fn locator_from_call(call: &AuthorizedToolCall) -> Result<JobLocator, GatewayError> {
    let project_id = call.project_id().ok_or(GatewayError::Rejected)?;
    let job_id = required_string(call.arguments(), "job_id").map_err(GatewayError::from)?;
    JobLocator::new(call.tenant_id(), project_id, job_id).map_err(GatewayError::from)
}

fn submission_output(
    tool: ToolKind,
    request_id: &str,
    job_id: &str,
    arguments: &Value,
    replayed: bool,
) -> Value {
    let safe_summary = if replayed {
        "The existing durable job was returned for this idempotent request."
    } else {
        "The request was accepted as a durable asynchronous job."
    };
    let base = json!({
        "schema_version": "hwpx-agent.tool-result/v1",
        "request_id": request_id,
        "outcome": "accepted",
        "safe_summary": safe_summary,
        "warnings": [],
        "job_id": job_id,
    });
    let mut output = base.as_object().cloned().unwrap_or_default();
    match tool {
        ToolKind::DocumentCreate | ToolKind::DocumentEdit | ToolKind::DocumentTransform => {
            output.insert("revision_id".to_owned(), Value::Null);
            output.insert("artifact".to_owned(), Value::Null);
            output.insert(
                "commit_state".to_owned(),
                Value::String("pending".to_owned()),
            );
            output.insert(
                "validation_state".to_owned(),
                Value::String("not_run".to_owned()),
            );
        }
        ToolKind::DocumentValidate => {
            output.insert(
                "validation_state".to_owned(),
                Value::String("queued".to_owned()),
            );
            output.insert("level_results".to_owned(), Value::Array(Vec::new()));
        }
        ToolKind::DocumentRender => {
            output.insert(
                "render_state".to_owned(),
                Value::String("queued".to_owned()),
            );
            output.insert("page_count".to_owned(), Value::from(0));
            output.insert("preview_artifact_id".to_owned(), Value::Null);
            let renderer = arguments
                .get("backend")
                .and_then(Value::as_str)
                .unwrap_or("auto");
            output.insert("renderer".to_owned(), Value::String(renderer.to_owned()));
            output.insert("font_substitutions".to_owned(), Value::from(0));
        }
        ToolKind::DocumentExport => {
            output.insert("artifact".to_owned(), Value::Null);
            output.insert("loss_report_artifact_id".to_owned(), Value::Null);
            output.insert(
                "export_state".to_owned(),
                Value::String("queued".to_owned()),
            );
        }
        _ => {}
    }
    Value::Object(output)
}

fn job_get_output(request_id: &str, job: &StoredJob, next_cursor: Option<&str>) -> Value {
    let outcome = match job.state {
        PublicJobState::Succeeded => "succeeded",
        PublicJobState::Failed
        | PublicJobState::Cancelled
        | PublicJobState::Expired
        | PublicJobState::Quarantined => "partial",
        PublicJobState::Queued
        | PublicJobState::Leasing
        | PublicJobState::Running
        | PublicJobState::Validating
        | PublicJobState::Committing => "accepted",
    };
    let summary = match job.state {
        PublicJobState::Succeeded => "The job completed successfully.",
        PublicJobState::Failed => "The job ended without a committed result.",
        PublicJobState::Cancelled => "The job was cancelled at a safe point.",
        PublicJobState::Expired => "The job expired before completion.",
        PublicJobState::Quarantined => "The job result is quarantined.",
        PublicJobState::Queued
        | PublicJobState::Leasing
        | PublicJobState::Running
        | PublicJobState::Validating
        | PublicJobState::Committing => "The job is still in progress.",
    };
    json!({
        "schema_version": "hwpx-agent.tool-result/v1",
        "request_id": request_id,
        "outcome": outcome,
        "safe_summary": summary,
        "warnings": [],
        "job_id": job.job_id,
        "state": job.state.name(),
        "stage": job.stage,
        "completed_units": job.completed_units,
        "total_units": job.total_units,
        "result_artifact_ids": job.result_artifact_ids,
        "next_event_cursor": next_cursor,
    })
}

fn cancel_output(request_id: &str, job_id: &str, outcome: &CancelOutcome) -> Value {
    let (public_outcome, summary) = match outcome.state {
        CancelState::Requested => (
            "accepted",
            "Cancellation was recorded and will apply at the next safe point.",
        ),
        CancelState::Cancelled => ("succeeded", "The queued job was cancelled."),
        CancelState::AlreadyTerminal => ("succeeded", "The job was already terminal."),
        CancelState::NotCancellable => (
            "partial",
            "The job is past its final cancellation safe point.",
        ),
    };
    json!({
        "schema_version": "hwpx-agent.tool-result/v1",
        "request_id": request_id,
        "outcome": public_outcome,
        "safe_summary": summary,
        "warnings": [],
        "job_id": job_id,
        "cancel_state": outcome.state.name(),
        "receipt_id": outcome.receipt_id,
        "replayed": outcome.replayed,
    })
}

fn initial_total_units(tool: ToolKind, arguments: &Value) -> Option<u64> {
    match tool {
        ToolKind::DocumentRender => {
            arguments
                .get("pages")
                .and_then(Value::as_object)
                .and_then(|pages| {
                    let first = pages.get("first")?.as_u64()?;
                    let last = pages.get("last")?.as_u64()?;
                    last.checked_sub(first)?.checked_add(1)
                })
        }
        ToolKind::DocumentValidate => arguments
            .get("levels")
            .and_then(Value::as_array)
            .and_then(|levels| u64::try_from(levels.len()).ok()),
        ToolKind::DocumentTransform => arguments
            .get("source_revision_ids")
            .and_then(Value::as_array)
            .and_then(|sources| u64::try_from(sources.len()).ok()),
        _ => None,
    }
}

fn is_async_submission(tool: ToolKind) -> bool {
    matches!(
        tool,
        ToolKind::DocumentCreate
            | ToolKind::DocumentEdit
            | ToolKind::DocumentTransform
            | ToolKind::DocumentValidate
            | ToolKind::DocumentRender
            | ToolKind::DocumentExport
    )
}

fn required_string<'a>(value: &'a Value, key: &str) -> Result<&'a str, AsyncJobError> {
    value
        .get(key)
        .and_then(Value::as_str)
        .ok_or(AsyncJobError::InvalidConfiguration)
}

fn valid_prefixed_id(value: &str, prefix: &str) -> bool {
    value.strip_prefix(prefix).is_some_and(|body| {
        (8..=120).contains(&body.len())
            && body
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
    })
}

fn valid_stage(value: &str) -> bool {
    let bytes = value.as_bytes();
    (2..=64).contains(&bytes.len())
        && bytes[0].is_ascii_lowercase()
        && bytes[1..]
            .iter()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || *byte == b'_')
}

fn valid_error_code(value: &str) -> bool {
    let bytes = value.as_bytes();
    (3..=64).contains(&bytes.len())
        && bytes[0].is_ascii_uppercase()
        && bytes[1..]
            .iter()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || *byte == b'_')
}

fn valid_idempotency_key(value: &str) -> bool {
    Uuid::parse_str(value).is_ok_and(|parsed| {
        !parsed.is_nil()
            && parsed.hyphenated().to_string() == value
            && (1..=5).contains(&parsed.get_version_num())
    })
}

fn lower_hex(value: &str) -> bool {
    value
        .bytes()
        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn derive_id(prefix: &str, material: &[u8]) -> String {
    let digest = hex::encode(Sha256::digest(material));
    format!("{prefix}{}", &digest[..32])
}

fn record_key(tenant_id: &str, project_id: &str, job_id: &str) -> String {
    format!("{tenant_id}\0{project_id}\0{job_id}")
}

fn request_key(
    tenant_id: &str,
    project_id: &str,
    subject_sha256: &str,
    idempotency_key: &str,
) -> String {
    format!("{tenant_id}\0{project_id}\0{subject_sha256}\0{idempotency_key}")
}

fn locator_key(locator: &JobLocator) -> String {
    record_key(
        &locator.tenant_id.canonical(),
        &locator.project_id,
        &locator.job_id,
    )
}

fn make_cursor(job_id: &str, sequence: u64) -> String {
    let material = format!("{job_id}\0{sequence}");
    let tag = hex::encode(Sha256::digest(material.as_bytes()));
    format!("cur_{sequence}_{}", &tag[..16])
}

fn parse_cursor(value: &str, job_id: &str) -> Result<u64, AsyncJobError> {
    let mut parts = value.split('_');
    if parts.next() != Some("cur") {
        return Err(AsyncJobError::Conflict);
    }
    let sequence = parts
        .next()
        .and_then(|part| part.parse::<u64>().ok())
        .filter(|sequence| *sequence > 0)
        .ok_or(AsyncJobError::Conflict)?;
    let tag = parts.next().ok_or(AsyncJobError::Conflict)?;
    if parts.next().is_some() || value != make_cursor(job_id, sequence) || tag.len() != 16 {
        return Err(AsyncJobError::Conflict);
    }
    Ok(sequence)
}
