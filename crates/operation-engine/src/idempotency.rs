use std::collections::BTreeMap;
use std::fmt;
use std::sync::{Mutex, MutexGuard};

use domain_ir::{ArtifactId, DocumentId, IdempotencyKey, ProjectId, RevisionId, TransactionId};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const IDEMPOTENCY_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.idempotency-receipt/v1";

const MAX_RECORDS_CEILING: usize = 1_000_000;
const MAX_STREAMS_CEILING: usize = 1_000_000;
const MAX_RECEIPT_BYTES_CEILING: usize = 16 * 1024 * 1024;
const MAX_ARTIFACT_BYTES_CEILING: u64 = 4 * 1024 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IdempotencyLimits {
    pub max_records: usize,
    pub max_streams: usize,
    pub max_receipt_bytes: usize,
    pub max_artifact_bytes: u64,
}

impl Default for IdempotencyLimits {
    fn default() -> Self {
        Self {
            max_records: 100_000,
            max_streams: 100_000,
            max_receipt_bytes: 4 * 1024 * 1024,
            max_artifact_bytes: 512 * 1024 * 1024,
        }
    }
}

impl IdempotencyLimits {
    fn validate(self) -> Result<(), IdempotencyError> {
        if self.max_records == 0
            || self.max_records > MAX_RECORDS_CEILING
            || self.max_streams == 0
            || self.max_streams > MAX_STREAMS_CEILING
            || self.max_receipt_bytes == 0
            || self.max_receipt_bytes > MAX_RECEIPT_BYTES_CEILING
            || self.max_artifact_bytes == 0
            || self.max_artifact_bytes > MAX_ARTIFACT_BYTES_CEILING
        {
            return Err(IdempotencyError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionStreamKey {
    project_id: ProjectId,
    document_id: DocumentId,
}

impl RevisionStreamKey {
    #[must_use]
    pub const fn new(project_id: ProjectId, document_id: DocumentId) -> Self {
        Self {
            project_id,
            document_id,
        }
    }
}

impl fmt::Debug for RevisionStreamKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("RevisionStreamKey(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct OwnerToken([u8; 32]);

impl OwnerToken {
    /// Creates one nonzero secret owner token.
    ///
    /// # Errors
    ///
    /// Rejects an all-zero token.
    pub fn new(value: [u8; 32]) -> Result<Self, IdempotencyError> {
        if value == [0; 32] {
            return Err(IdempotencyError::InvalidOwnerToken);
        }
        Ok(Self(value))
    }

    fn sha256(&self) -> [u8; 32] {
        Sha256::digest(self.0).into()
    }
}

impl fmt::Debug for OwnerToken {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OwnerToken(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IdempotencyBinding {
    key: IdempotencyKey,
    request_sha256: [u8; 32],
    manifest_sha256: [u8; 32],
    stream: RevisionStreamKey,
    expected_revision: RevisionId,
    expected_head_generation: u64,
    transaction_id: TransactionId,
}

impl IdempotencyBinding {
    /// Binds a key to one exact request, manifest, stream head and transaction.
    ///
    /// # Errors
    ///
    /// Rejects zero digests or generation zero.
    pub fn new(
        key: IdempotencyKey,
        request_sha256: [u8; 32],
        manifest_sha256: [u8; 32],
        stream: RevisionStreamKey,
        expected_revision: RevisionId,
        expected_head_generation: u64,
        transaction_id: TransactionId,
    ) -> Result<Self, IdempotencyError> {
        if request_sha256 == [0; 32] || manifest_sha256 == [0; 32] || expected_head_generation == 0
        {
            return Err(IdempotencyError::InvalidBinding);
        }
        Ok(Self {
            key,
            request_sha256,
            manifest_sha256,
            stream,
            expected_revision,
            expected_head_generation,
            transaction_id,
        })
    }

    #[must_use]
    pub const fn key(&self) -> &IdempotencyKey {
        &self.key
    }

    #[must_use]
    pub const fn expected_revision(&self) -> &RevisionId {
        &self.expected_revision
    }

    #[must_use]
    pub const fn expected_head_generation(&self) -> u64 {
        self.expected_head_generation
    }

    fn canonical_sha256(&self) -> Result<[u8; 32], IdempotencyError> {
        canonical_sha256(self)
    }
}

impl fmt::Debug for IdempotencyBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("IdempotencyBinding(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum IdempotencyState {
    Claimed,
    InProgress,
    OutcomeUnknown,
    Succeeded,
    FailedTerminal,
}

#[derive(Clone, Eq, PartialEq)]
pub struct ClaimLease {
    key: IdempotencyKey,
    binding_sha256: [u8; 32],
    fencing_generation: u64,
    owner_sha256: [u8; 32],
}

impl ClaimLease {
    #[must_use]
    pub const fn key(&self) -> &IdempotencyKey {
        &self.key
    }

    #[must_use]
    pub const fn fencing_generation(&self) -> u64 {
        self.fencing_generation
    }

    #[must_use]
    pub const fn binding_sha256(&self) -> [u8; 32] {
        self.binding_sha256
    }
}

impl fmt::Debug for ClaimLease {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ClaimLease")
            .field("fencing_generation", &self.fencing_generation)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum ClaimOutcome {
    Acquired(ClaimLease),
    Duplicate(IdempotencyState),
    Replayed(IdempotencyReceipt),
}

impl fmt::Debug for ClaimOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Acquired(lease) => formatter.debug_tuple("Acquired").field(lease).finish(),
            Self::Duplicate(state) => formatter.debug_tuple("Duplicate").field(state).finish(),
            Self::Replayed(receipt) => formatter.debug_tuple("Replayed").field(receipt).finish(),
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionCommit {
    new_revision: RevisionId,
    result_artifact_id: ArtifactId,
    result_sha256: [u8; 32],
    result_size: u64,
    transaction_receipt_sha256: [u8; 32],
}

impl RevisionCommit {
    /// Creates one exact immutable revision result.
    ///
    /// # Errors
    ///
    /// Rejects zero digests or an empty/oversized result.
    pub fn new(
        new_revision: RevisionId,
        result_artifact_id: ArtifactId,
        result_sha256: [u8; 32],
        result_size: u64,
        transaction_receipt_sha256: [u8; 32],
        limits: IdempotencyLimits,
    ) -> Result<Self, IdempotencyError> {
        limits.validate()?;
        if result_sha256 == [0; 32]
            || transaction_receipt_sha256 == [0; 32]
            || result_size == 0
            || result_size > limits.max_artifact_bytes
            || !artifact_matches_digest(&result_artifact_id, result_sha256)
        {
            return Err(IdempotencyError::InvalidCommit);
        }
        Ok(Self {
            new_revision,
            result_artifact_id,
            result_sha256,
            result_size,
            transaction_receipt_sha256,
        })
    }

    #[must_use]
    pub const fn new_revision(&self) -> &RevisionId {
        &self.new_revision
    }

    #[must_use]
    pub const fn result_artifact_id(&self) -> &ArtifactId {
        &self.result_artifact_id
    }

    fn canonical_sha256(&self) -> Result<[u8; 32], IdempotencyError> {
        canonical_sha256(self)
    }
}

impl fmt::Debug for RevisionCommit {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionCommit")
            .field("result_size", &self.result_size)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommittedResult {
    artifact_id: ArtifactId,
    artifact_sha256: [u8; 32],
    artifact_size: u64,
    revision_id: RevisionId,
    transaction_receipt_sha256: [u8; 32],
}

impl CommittedResult {
    #[must_use]
    pub const fn artifact_id(&self) -> &ArtifactId {
        &self.artifact_id
    }

    #[must_use]
    pub const fn revision_id(&self) -> &RevisionId {
        &self.revision_id
    }
}

impl fmt::Debug for CommittedResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommittedResult")
            .field("artifact_size", &self.artifact_size)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TerminalFailure {
    OperationFailed,
    OutcomeNotCommitted,
    RevisionConflict,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IdempotencyReceipt {
    schema_version: String,
    key_ref_sha256: [u8; 32],
    binding_sha256: [u8; 32],
    fencing_generation: u64,
    state: IdempotencyState,
    result: Option<CommittedResult>,
    failure: Option<TerminalFailure>,
}

impl IdempotencyReceipt {
    #[must_use]
    pub const fn state(&self) -> IdempotencyState {
        self.state
    }

    #[must_use]
    pub const fn result(&self) -> Option<&CommittedResult> {
        self.result.as_ref()
    }

    #[must_use]
    pub const fn failure(&self) -> Option<TerminalFailure> {
        self.failure
    }

    /// Emits deterministic terminal replay bytes.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization failure.
    pub fn canonical_json(&self) -> Result<Vec<u8>, IdempotencyError> {
        serde_json::to_vec(self).map_err(|_| IdempotencyError::SerializationFailed)
    }

    /// Hashes the exact terminal replay receipt.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization failure.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], IdempotencyError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for IdempotencyReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdempotencyReceipt")
            .field("fencing_generation", &self.fencing_generation)
            .field("state", &self.state)
            .field("has_result", &self.result.is_some())
            .field("failure", &self.failure)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct RevisionHead {
    revision_id: RevisionId,
    generation: u64,
    last_commit: Option<HeadCommit>,
}

impl RevisionHead {
    #[must_use]
    pub const fn revision_id(&self) -> &RevisionId {
        &self.revision_id
    }

    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }
}

impl fmt::Debug for RevisionHead {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionHead")
            .field("generation", &self.generation)
            .field("has_commit", &self.last_commit.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
struct HeadCommit {
    commit: RevisionCommit,
    binding_sha256: [u8; 32],
    key_ref_sha256: [u8; 32],
    fencing_generation: u64,
}

#[derive(Clone, Eq, PartialEq)]
pub enum ReconcileObservation {
    NoEffect,
    Committed(RevisionCommit),
}

impl fmt::Debug for ReconcileObservation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NoEffect => formatter.write_str("ReconcileObservation::NoEffect"),
            Self::Committed(commit) => formatter.debug_tuple("Committed").field(commit).finish(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum IdempotencyError {
    #[error("idempotency limit is invalid")]
    InvalidLimit,
    #[error("idempotency binding is invalid")]
    InvalidBinding,
    #[error("idempotency owner token is invalid")]
    InvalidOwnerToken,
    #[error("idempotency revision commit is invalid")]
    InvalidCommit,
    #[error("idempotency key was reused with a different binding")]
    KeyReuseConflict,
    #[error("idempotency record limit exceeded")]
    RecordLimitExceeded,
    #[error("revision stream limit exceeded")]
    StreamLimitExceeded,
    #[error("revision stream is missing")]
    RevisionStreamMissing,
    #[error("revision stream already exists with another head")]
    RevisionStreamConflict,
    #[error("revision compare-and-swap conflicted")]
    RevisionConflict,
    #[error("idempotency claim lease is stale")]
    StaleLease,
    #[error("idempotency state transition is invalid")]
    InvalidState,
    #[error("idempotency outcome observation does not match")]
    ReconciliationMismatch,
    #[error("idempotency checked counter overflowed")]
    CounterOverflow,
    #[error("idempotency service lock failed")]
    LockFailed,
    #[error("idempotency receipt serialization failed")]
    SerializationFailed,
}

impl IdempotencyError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "idempotency_invalid_limit",
            Self::InvalidBinding => "idempotency_invalid_binding",
            Self::InvalidOwnerToken => "idempotency_invalid_owner_token",
            Self::InvalidCommit => "idempotency_invalid_commit",
            Self::KeyReuseConflict => "idempotency_key_reuse_conflict",
            Self::RecordLimitExceeded => "idempotency_record_limit_exceeded",
            Self::StreamLimitExceeded => "idempotency_stream_limit_exceeded",
            Self::RevisionStreamMissing => "idempotency_revision_stream_missing",
            Self::RevisionStreamConflict => "idempotency_revision_stream_conflict",
            Self::RevisionConflict => "idempotency_revision_conflict",
            Self::StaleLease => "idempotency_stale_lease",
            Self::InvalidState => "idempotency_invalid_state",
            Self::ReconciliationMismatch => "idempotency_reconciliation_mismatch",
            Self::CounterOverflow => "idempotency_counter_overflow",
            Self::LockFailed => "idempotency_lock_failed",
            Self::SerializationFailed => "idempotency_serialization_failed",
        }
    }
}

/// Atomic persistence boundary for idempotency records and revision heads.
///
/// P04 provides [`IdempotencyService`] as an in-memory reference implementation. P14 may implement
/// this object-safe contract with durable multi-process storage, but must preserve each method's
/// atomicity, fencing, replay and no-effect failure semantics.
pub trait IdempotencyStore: Send + Sync {
    /// Creates or verifies one initial stream head.
    ///
    /// # Errors
    ///
    /// Returns a typed conflict, limit or storage failure.
    fn initialize_stream(
        &self,
        stream: RevisionStreamKey,
        revision_id: RevisionId,
    ) -> Result<RevisionHead, IdempotencyError>;

    /// Acquires or observes one exact idempotency binding.
    ///
    /// # Errors
    ///
    /// Returns a typed binding, head, capacity, counter or storage failure.
    fn claim(
        &self,
        binding: IdempotencyBinding,
        owner_token: &OwnerToken,
    ) -> Result<ClaimOutcome, IdempotencyError>;

    /// Advances an acquired claim into execution.
    ///
    /// # Errors
    ///
    /// Returns a typed stale-lease, state or storage failure.
    fn start(&self, lease: &ClaimLease) -> Result<(), IdempotencyError>;

    /// Advances the current live owner's heartbeat sequence.
    ///
    /// # Errors
    ///
    /// Returns a typed stale-lease, state, counter or storage failure.
    fn heartbeat(&self, lease: &ClaimLease) -> Result<u64, IdempotencyError>;

    /// Atomically commits a revision head and immutable success replay.
    ///
    /// # Errors
    ///
    /// Returns a typed lease, state, validation, CAS or storage failure without an effect.
    fn commit_success(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<IdempotencyReceipt, IdempotencyError>;

    /// Atomically commits a revision head and records an unknown response boundary.
    ///
    /// # Errors
    ///
    /// Returns a typed lease, state, validation, CAS or storage failure without an effect.
    fn commit_outcome_unknown(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<(), IdempotencyError>;

    /// Records an unknown outcome before a confirmed revision effect.
    ///
    /// # Errors
    ///
    /// Returns a typed stale-lease, state or storage failure.
    fn mark_outcome_unknown(&self, lease: &ClaimLease) -> Result<(), IdempotencyError>;

    /// Resolves an unknown outcome from exact observed evidence.
    ///
    /// # Errors
    ///
    /// Returns a typed lease, state, evidence, receipt or storage failure.
    fn reconcile_unknown(
        &self,
        lease: &ClaimLease,
        observation: ReconcileObservation,
    ) -> Result<IdempotencyReceipt, IdempotencyError>;

    /// Records an immutable terminal failure replay.
    ///
    /// # Errors
    ///
    /// Returns a typed stale-lease, state, receipt or storage failure.
    fn fail_terminal(
        &self,
        lease: &ClaimLease,
        failure: TerminalFailure,
    ) -> Result<IdempotencyReceipt, IdempotencyError>;

    /// Reads one exact immutable stream head.
    ///
    /// # Errors
    ///
    /// Returns a typed missing-stream or storage failure.
    fn head(&self, stream: &RevisionStreamKey) -> Result<RevisionHead, IdempotencyError>;

    /// Reads the bounded number of retained records.
    ///
    /// # Errors
    ///
    /// Returns a typed storage failure.
    fn record_count(&self) -> Result<usize, IdempotencyError>;
}

pub struct IdempotencyService {
    limits: IdempotencyLimits,
    inner: Mutex<ServiceState>,
}

impl IdempotencyService {
    /// Creates a finite in-memory reference service.
    ///
    /// # Errors
    ///
    /// Rejects invalid finite limits.
    pub fn new(limits: IdempotencyLimits) -> Result<Self, IdempotencyError> {
        limits.validate()?;
        Ok(Self {
            limits,
            inner: Mutex::new(ServiceState::default()),
        })
    }

    /// Initializes one revision stream at generation one.
    ///
    /// # Errors
    ///
    /// Rejects stream limit overflow or a different existing head.
    pub fn initialize_stream(
        &self,
        stream: RevisionStreamKey,
        revision_id: RevisionId,
    ) -> Result<RevisionHead, IdempotencyError> {
        let mut state = self.lock()?;
        if let Some(existing) = state.streams.get(&stream) {
            return if existing.revision_id == revision_id && existing.generation == 1 {
                Ok(existing.clone())
            } else {
                Err(IdempotencyError::RevisionStreamConflict)
            };
        }
        if state.streams.len() >= self.limits.max_streams {
            return Err(IdempotencyError::StreamLimitExceeded);
        }
        let head = RevisionHead {
            revision_id,
            generation: 1,
            last_commit: None,
        };
        let _ = state.streams.insert(stream, head.clone());
        Ok(head)
    }

    /// Claims one exact binding or returns duplicate/terminal replay state.
    ///
    /// # Errors
    ///
    /// Fails closed on missing/stale stream, key reuse, record limits or checked fencing overflow.
    pub fn claim(
        &self,
        binding: IdempotencyBinding,
        owner_token: &OwnerToken,
    ) -> Result<ClaimOutcome, IdempotencyError> {
        let binding_sha256 = binding.canonical_sha256()?;
        let mut state = self.lock()?;
        if let Some(record) = state.records.get(binding.key()) {
            if record.binding != binding || record.binding_sha256 != binding_sha256 {
                return Err(IdempotencyError::KeyReuseConflict);
            }
            return Ok(match &record.state {
                StoredState::Succeeded(receipt) | StoredState::FailedTerminal(receipt) => {
                    ClaimOutcome::Replayed(receipt.clone())
                }
                StoredState::Claimed => ClaimOutcome::Duplicate(IdempotencyState::Claimed),
                StoredState::InProgress => ClaimOutcome::Duplicate(IdempotencyState::InProgress),
                StoredState::OutcomeUnknown { .. } => {
                    ClaimOutcome::Duplicate(IdempotencyState::OutcomeUnknown)
                }
            });
        }
        verify_expected_head(&state, &binding)?;
        if state.records.len() >= self.limits.max_records {
            return Err(IdempotencyError::RecordLimitExceeded);
        }
        let fencing_generation = state.next_fencing_generation;
        state.next_fencing_generation = state
            .next_fencing_generation
            .checked_add(1)
            .ok_or(IdempotencyError::CounterOverflow)?;
        let lease = ClaimLease {
            key: binding.key.clone(),
            binding_sha256,
            fencing_generation,
            owner_sha256: owner_token.sha256(),
        };
        let record = IdempotencyRecord {
            binding,
            binding_sha256,
            fencing_generation,
            owner_sha256: lease.owner_sha256,
            heartbeat_sequence: 0,
            state: StoredState::Claimed,
        };
        let _ = state.records.insert(lease.key.clone(), record);
        Ok(ClaimOutcome::Acquired(lease))
    }

    /// Moves one current owner from claimed to in-progress.
    ///
    /// # Errors
    ///
    /// Rejects stale leases and every other state.
    pub fn start(&self, lease: &ClaimLease) -> Result<(), IdempotencyError> {
        let mut state = self.lock()?;
        let record = current_record_mut(&mut state, lease)?;
        if record.state != StoredState::Claimed {
            return Err(IdempotencyError::InvalidState);
        }
        record.state = StoredState::InProgress;
        Ok(())
    }

    /// Advances a checked heartbeat sequence for the current live owner.
    ///
    /// # Errors
    ///
    /// Rejects stale/terminal/unknown leases or counter overflow.
    pub fn heartbeat(&self, lease: &ClaimLease) -> Result<u64, IdempotencyError> {
        let mut state = self.lock()?;
        let record = current_record_mut(&mut state, lease)?;
        if !matches!(record.state, StoredState::Claimed | StoredState::InProgress) {
            return Err(IdempotencyError::InvalidState);
        }
        record.heartbeat_sequence = record
            .heartbeat_sequence
            .checked_add(1)
            .ok_or(IdempotencyError::CounterOverflow)?;
        Ok(record.heartbeat_sequence)
    }

    /// Atomically CAS-commits a revision and terminal success receipt.
    ///
    /// # Errors
    ///
    /// Rejects stale lease/state/head or invalid commit without changing the stream or record.
    pub fn commit_success(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        self.commit(lease, commit, CommitDisposition::Terminal)
    }

    /// CAS-commits a revision but records an outcome-unknown response boundary for reconciliation.
    ///
    /// # Errors
    ///
    /// Rejects stale lease/state/head or invalid commit without a partial update.
    pub fn commit_outcome_unknown(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<(), IdempotencyError> {
        let _ = self.commit(lease, commit, CommitDisposition::OutcomeUnknown)?;
        Ok(())
    }

    /// Marks an in-progress attempt unknown before any confirmed revision effect.
    ///
    /// # Errors
    ///
    /// Rejects stale leases or non-running states.
    pub fn mark_outcome_unknown(&self, lease: &ClaimLease) -> Result<(), IdempotencyError> {
        let mut state = self.lock()?;
        let record = current_record_mut(&mut state, lease)?;
        if record.state != StoredState::InProgress {
            return Err(IdempotencyError::InvalidState);
        }
        record.state = StoredState::OutcomeUnknown {
            expected_commit_sha256: None,
        };
        Ok(())
    }

    /// Reconciles unknown state against an exact no-effect or committed observation.
    ///
    /// # Errors
    ///
    /// Rejects stale leases, non-unknown state or an observation that does not exactly match the
    /// current revision head and expected commit digest.
    pub fn reconcile_unknown(
        &self,
        lease: &ClaimLease,
        observation: ReconcileObservation,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        let mut state = self.lock()?;
        let (binding, expected_commit_sha256) = {
            let record = current_record(&state, lease)?;
            let StoredState::OutcomeUnknown {
                expected_commit_sha256,
            } = record.state
            else {
                return Err(IdempotencyError::InvalidState);
            };
            (record.binding.clone(), expected_commit_sha256)
        };
        let receipt = match observation {
            ReconcileObservation::NoEffect => {
                if expected_commit_sha256.is_some() {
                    return Err(IdempotencyError::ReconciliationMismatch);
                }
                verify_expected_head(&state, &binding)
                    .map_err(|_| IdempotencyError::ReconciliationMismatch)?;
                terminal_failure_receipt(lease, TerminalFailure::OutcomeNotCommitted)
            }
            ReconcileObservation::Committed(commit) => {
                let digest = commit.canonical_sha256()?;
                if expected_commit_sha256 != Some(digest)
                    || !head_matches_commit(&state, &binding, lease, &commit)
                {
                    return Err(IdempotencyError::ReconciliationMismatch);
                }
                terminal_success_receipt(lease, &commit)
            }
        };
        ensure_receipt_size(&receipt, self.limits)?;
        let record = current_record_mut(&mut state, lease)?;
        record.state = if receipt.state == IdempotencyState::Succeeded {
            StoredState::Succeeded(receipt.clone())
        } else {
            StoredState::FailedTerminal(receipt.clone())
        };
        Ok(receipt)
    }

    /// Records a terminal non-unknown failure for exact replay.
    ///
    /// # Errors
    ///
    /// Rejects stale leases, terminal/unknown states or oversized receipt output.
    pub fn fail_terminal(
        &self,
        lease: &ClaimLease,
        failure: TerminalFailure,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        let mut state = self.lock()?;
        let record = current_record_mut(&mut state, lease)?;
        if !matches!(record.state, StoredState::Claimed | StoredState::InProgress) {
            return Err(IdempotencyError::InvalidState);
        }
        let receipt = terminal_failure_receipt(lease, failure);
        ensure_receipt_size(&receipt, self.limits)?;
        record.state = StoredState::FailedTerminal(receipt.clone());
        Ok(receipt)
    }

    /// Returns one current immutable stream head.
    ///
    /// # Errors
    ///
    /// Returns a stable missing-stream or lock failure.
    pub fn head(&self, stream: &RevisionStreamKey) -> Result<RevisionHead, IdempotencyError> {
        self.lock()?
            .streams
            .get(stream)
            .cloned()
            .ok_or(IdempotencyError::RevisionStreamMissing)
    }

    /// Returns the current bounded record count.
    ///
    /// # Errors
    ///
    /// Returns a stable service lock failure.
    pub fn record_count(&self) -> Result<usize, IdempotencyError> {
        Ok(self.lock()?.records.len())
    }

    fn commit(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
        disposition: CommitDisposition,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        validate_commit(commit, self.limits)?;
        let mut state = self.lock()?;
        let binding = {
            let record = current_record(&state, lease)?;
            if record.state != StoredState::InProgress {
                return Err(IdempotencyError::InvalidState);
            }
            record.binding.clone()
        };
        let next_head = checked_next_head(&state, &binding, lease, commit)?;
        let receipt = terminal_success_receipt(lease, commit);
        ensure_receipt_size(&receipt, self.limits)?;
        let stored_state = match disposition {
            CommitDisposition::Terminal => StoredState::Succeeded(receipt.clone()),
            CommitDisposition::OutcomeUnknown => StoredState::OutcomeUnknown {
                expected_commit_sha256: Some(commit.canonical_sha256()?),
            },
        };
        let ServiceState {
            records, streams, ..
        } = &mut *state;
        let stream = streams
            .get_mut(&binding.stream)
            .ok_or(IdempotencyError::RevisionStreamMissing)?;
        let record = records
            .get_mut(lease.key())
            .ok_or(IdempotencyError::StaleLease)?;
        validate_lease(record, lease)?;
        *stream = next_head;
        record.state = stored_state;
        Ok(receipt)
    }

    fn lock(&self) -> Result<MutexGuard<'_, ServiceState>, IdempotencyError> {
        self.inner.lock().map_err(|_| IdempotencyError::LockFailed)
    }
}

impl fmt::Debug for IdempotencyService {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdempotencyService")
            .field("limits", &self.limits)
            .finish_non_exhaustive()
    }
}

impl IdempotencyStore for IdempotencyService {
    fn initialize_stream(
        &self,
        stream: RevisionStreamKey,
        revision_id: RevisionId,
    ) -> Result<RevisionHead, IdempotencyError> {
        Self::initialize_stream(self, stream, revision_id)
    }

    fn claim(
        &self,
        binding: IdempotencyBinding,
        owner_token: &OwnerToken,
    ) -> Result<ClaimOutcome, IdempotencyError> {
        Self::claim(self, binding, owner_token)
    }

    fn start(&self, lease: &ClaimLease) -> Result<(), IdempotencyError> {
        Self::start(self, lease)
    }

    fn heartbeat(&self, lease: &ClaimLease) -> Result<u64, IdempotencyError> {
        Self::heartbeat(self, lease)
    }

    fn commit_success(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        Self::commit_success(self, lease, commit)
    }

    fn commit_outcome_unknown(
        &self,
        lease: &ClaimLease,
        commit: &RevisionCommit,
    ) -> Result<(), IdempotencyError> {
        Self::commit_outcome_unknown(self, lease, commit)
    }

    fn mark_outcome_unknown(&self, lease: &ClaimLease) -> Result<(), IdempotencyError> {
        Self::mark_outcome_unknown(self, lease)
    }

    fn reconcile_unknown(
        &self,
        lease: &ClaimLease,
        observation: ReconcileObservation,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        Self::reconcile_unknown(self, lease, observation)
    }

    fn fail_terminal(
        &self,
        lease: &ClaimLease,
        failure: TerminalFailure,
    ) -> Result<IdempotencyReceipt, IdempotencyError> {
        Self::fail_terminal(self, lease, failure)
    }

    fn head(&self, stream: &RevisionStreamKey) -> Result<RevisionHead, IdempotencyError> {
        Self::head(self, stream)
    }

    fn record_count(&self) -> Result<usize, IdempotencyError> {
        Self::record_count(self)
    }
}

#[derive(Clone, Copy)]
enum CommitDisposition {
    Terminal,
    OutcomeUnknown,
}

struct IdempotencyRecord {
    binding: IdempotencyBinding,
    binding_sha256: [u8; 32],
    fencing_generation: u64,
    owner_sha256: [u8; 32],
    heartbeat_sequence: u64,
    state: StoredState,
}

#[derive(Clone, Eq, PartialEq)]
enum StoredState {
    Claimed,
    InProgress,
    OutcomeUnknown {
        expected_commit_sha256: Option<[u8; 32]>,
    },
    Succeeded(IdempotencyReceipt),
    FailedTerminal(IdempotencyReceipt),
}

struct ServiceState {
    next_fencing_generation: u64,
    records: BTreeMap<IdempotencyKey, IdempotencyRecord>,
    streams: BTreeMap<RevisionStreamKey, RevisionHead>,
}

impl Default for ServiceState {
    fn default() -> Self {
        Self {
            next_fencing_generation: 1,
            records: BTreeMap::new(),
            streams: BTreeMap::new(),
        }
    }
}

fn current_record<'a>(
    state: &'a ServiceState,
    lease: &ClaimLease,
) -> Result<&'a IdempotencyRecord, IdempotencyError> {
    let record = state
        .records
        .get(lease.key())
        .ok_or(IdempotencyError::StaleLease)?;
    validate_lease(record, lease)?;
    Ok(record)
}

fn current_record_mut<'a>(
    state: &'a mut ServiceState,
    lease: &ClaimLease,
) -> Result<&'a mut IdempotencyRecord, IdempotencyError> {
    let record = state
        .records
        .get_mut(lease.key())
        .ok_or(IdempotencyError::StaleLease)?;
    validate_lease(record, lease)?;
    Ok(record)
}

fn validate_lease(record: &IdempotencyRecord, lease: &ClaimLease) -> Result<(), IdempotencyError> {
    if record.binding_sha256 != lease.binding_sha256
        || record.fencing_generation != lease.fencing_generation
        || record.owner_sha256 != lease.owner_sha256
    {
        return Err(IdempotencyError::StaleLease);
    }
    Ok(())
}

fn verify_expected_head(
    state: &ServiceState,
    binding: &IdempotencyBinding,
) -> Result<(), IdempotencyError> {
    let head = state
        .streams
        .get(&binding.stream)
        .ok_or(IdempotencyError::RevisionStreamMissing)?;
    if head.revision_id != binding.expected_revision
        || head.generation != binding.expected_head_generation
    {
        return Err(IdempotencyError::RevisionConflict);
    }
    Ok(())
}

fn checked_next_head(
    state: &ServiceState,
    binding: &IdempotencyBinding,
    lease: &ClaimLease,
    commit: &RevisionCommit,
) -> Result<RevisionHead, IdempotencyError> {
    verify_expected_head(state, binding)?;
    if commit.new_revision == binding.expected_revision {
        return Err(IdempotencyError::InvalidCommit);
    }
    let generation = binding
        .expected_head_generation
        .checked_add(1)
        .ok_or(IdempotencyError::CounterOverflow)?;
    Ok(RevisionHead {
        revision_id: commit.new_revision.clone(),
        generation,
        last_commit: Some(HeadCommit {
            commit: commit.clone(),
            binding_sha256: lease.binding_sha256,
            key_ref_sha256: key_ref(lease.key()),
            fencing_generation: lease.fencing_generation,
        }),
    })
}

fn head_matches_commit(
    state: &ServiceState,
    binding: &IdempotencyBinding,
    lease: &ClaimLease,
    commit: &RevisionCommit,
) -> bool {
    let Some(head) = state.streams.get(&binding.stream) else {
        return false;
    };
    let Some(expected_generation) = binding.expected_head_generation.checked_add(1) else {
        return false;
    };
    head.revision_id == commit.new_revision
        && head.generation == expected_generation
        && head.last_commit.as_ref().is_some_and(|evidence| {
            evidence.commit == *commit
                && evidence.binding_sha256 == lease.binding_sha256
                && evidence.key_ref_sha256 == key_ref(lease.key())
                && evidence.fencing_generation == lease.fencing_generation
        })
}

fn validate_commit(
    commit: &RevisionCommit,
    limits: IdempotencyLimits,
) -> Result<(), IdempotencyError> {
    if commit.result_sha256 == [0; 32]
        || commit.transaction_receipt_sha256 == [0; 32]
        || commit.result_size == 0
        || commit.result_size > limits.max_artifact_bytes
        || !artifact_matches_digest(&commit.result_artifact_id, commit.result_sha256)
    {
        return Err(IdempotencyError::InvalidCommit);
    }
    Ok(())
}

fn terminal_success_receipt(lease: &ClaimLease, commit: &RevisionCommit) -> IdempotencyReceipt {
    IdempotencyReceipt {
        schema_version: IDEMPOTENCY_RECEIPT_SCHEMA_VERSION.to_owned(),
        key_ref_sha256: key_ref(lease.key()),
        binding_sha256: lease.binding_sha256,
        fencing_generation: lease.fencing_generation,
        state: IdempotencyState::Succeeded,
        result: Some(CommittedResult {
            artifact_id: commit.result_artifact_id.clone(),
            artifact_sha256: commit.result_sha256,
            artifact_size: commit.result_size,
            revision_id: commit.new_revision.clone(),
            transaction_receipt_sha256: commit.transaction_receipt_sha256,
        }),
        failure: None,
    }
}

fn terminal_failure_receipt(lease: &ClaimLease, failure: TerminalFailure) -> IdempotencyReceipt {
    IdempotencyReceipt {
        schema_version: IDEMPOTENCY_RECEIPT_SCHEMA_VERSION.to_owned(),
        key_ref_sha256: key_ref(lease.key()),
        binding_sha256: lease.binding_sha256,
        fencing_generation: lease.fencing_generation,
        state: IdempotencyState::FailedTerminal,
        result: None,
        failure: Some(failure),
    }
}

fn ensure_receipt_size(
    receipt: &IdempotencyReceipt,
    limits: IdempotencyLimits,
) -> Result<(), IdempotencyError> {
    if receipt.canonical_json()?.len() > limits.max_receipt_bytes {
        return Err(IdempotencyError::InvalidCommit);
    }
    Ok(())
}

fn canonical_sha256<T: Serialize>(value: &T) -> Result<[u8; 32], IdempotencyError> {
    let bytes = serde_json::to_vec(value).map_err(|_| IdempotencyError::SerializationFailed)?;
    Ok(Sha256::digest(bytes).into())
}

fn key_ref(key: &IdempotencyKey) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"idempotency-key");
    hasher.update([0]);
    hasher.update(key.as_str().as_bytes());
    hasher.finalize().into()
}

fn artifact_matches_digest(artifact_id: &ArtifactId, digest: [u8; 32]) -> bool {
    artifact_id.as_str() == format!("sha256-{}", hex::encode(digest))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn owner_and_fencing_tamper_are_stale() -> Result<(), Box<dyn std::error::Error>> {
        let service = IdempotencyService::new(IdempotencyLimits::default())?;
        let stream =
            RevisionStreamKey::new(ProjectId::parse("project")?, DocumentId::parse("document")?);
        let revision = RevisionId::parse("revision-1")?;
        service.initialize_stream(stream.clone(), revision.clone())?;
        let binding = IdempotencyBinding::new(
            IdempotencyKey::parse("key")?,
            [1; 32],
            [2; 32],
            stream,
            revision,
            1,
            TransactionId::parse("transaction")?,
        )?;
        let ClaimOutcome::Acquired(lease) = service.claim(binding, &OwnerToken::new([3; 32])?)?
        else {
            return Err("expected lease".into());
        };
        let mut wrong_owner = lease.clone();
        wrong_owner.owner_sha256 = [8; 32];
        assert_eq!(
            service.heartbeat(&wrong_owner),
            Err(IdempotencyError::StaleLease)
        );
        let mut wrong_fence = lease;
        wrong_fence.fencing_generation += 1;
        assert_eq!(
            service.heartbeat(&wrong_fence),
            Err(IdempotencyError::StaleLease)
        );
        Ok(())
    }
}
