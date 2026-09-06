#![forbid(unsafe_code)]

use std::fmt;

use serde::{Deserialize, Serialize};
use thiserror::Error;

const MAX_ID_BYTES: usize = 120;
const MAX_IDEMPOTENCY_BYTES: usize = 120;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Connectivity {
    Offline,
    Online,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MirrorPhase {
    Clean,
    Ahead,
    Conflict,
}

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum SyncError {
    #[error("local sync request rejected")]
    InvalidRequest,
    #[error("local mirror is offline")]
    Offline,
    #[error("local mirror state rejected the operation")]
    InvalidState,
    #[error("remote sync service is unavailable")]
    RemoteUnavailable,
    #[error("remote sync request was rejected")]
    RemoteRejected,
    #[error("remote head conflicts with the local mirror")]
    Conflict,
    #[error("remote sync response was invalid")]
    InvalidResponse,
}

#[derive(Clone, Eq, PartialEq)]
pub struct RemoteHead {
    revision_id: Option<String>,
    generation: u64,
}

impl fmt::Debug for RemoteHead {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RemoteHead")
            .field(
                "revision_id",
                &self.revision_id.as_ref().map(|_| "<redacted>"),
            )
            .field("generation", &self.generation)
            .finish()
    }
}

impl RemoteHead {
    /// Creates an empty or revision-bound remote head.
    ///
    /// # Errors
    ///
    /// Rejects malformed revision/generation pairs or identifiers.
    pub fn new(revision_id: Option<String>, generation: u64) -> Result<Self, SyncError> {
        if revision_id.is_none() != (generation == 0)
            || revision_id
                .as_deref()
                .is_some_and(|value| !valid_prefixed_identifier(value, "rev_"))
        {
            return Err(SyncError::InvalidRequest);
        }
        Ok(Self {
            revision_id,
            generation,
        })
    }

    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }

    #[must_use]
    pub fn revision_id(&self) -> Option<&str> {
        self.revision_id.as_deref()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RemoteFailure {
    Unavailable,
    Rejected,
    Conflict(RemoteHead),
}

#[derive(Clone, Eq, PartialEq)]
pub struct PullRequest {
    project_id: String,
    branch_id: String,
    observed_head: RemoteHead,
}

impl fmt::Debug for PullRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PullRequest")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("observed_generation", &self.observed_head.generation)
            .finish()
    }
}

impl PullRequest {
    #[must_use]
    pub fn project_id(&self) -> &str {
        &self.project_id
    }

    #[must_use]
    pub fn branch_id(&self) -> &str {
        &self.branch_id
    }

    #[must_use]
    pub const fn observed_head(&self) -> &RemoteHead {
        &self.observed_head
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct PushRequest {
    project_id: String,
    branch_id: String,
    expected_head: RemoteHead,
    snapshot_sha256: String,
    operation_plan_sha256: String,
    idempotency_key: String,
}

impl fmt::Debug for PushRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PushRequest")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("expected_generation", &self.expected_head.generation)
            .field("snapshot_sha256", &"<redacted>")
            .field("operation_plan_sha256", &"<redacted>")
            .field("idempotency_key", &"<redacted>")
            .finish()
    }
}

impl PushRequest {
    #[must_use]
    pub fn project_id(&self) -> &str {
        &self.project_id
    }

    #[must_use]
    pub fn branch_id(&self) -> &str {
        &self.branch_id
    }

    #[must_use]
    pub const fn expected_head(&self) -> &RemoteHead {
        &self.expected_head
    }

    #[must_use]
    pub fn snapshot_sha256(&self) -> &str {
        &self.snapshot_sha256
    }

    #[must_use]
    pub fn operation_plan_sha256(&self) -> &str {
        &self.operation_plan_sha256
    }

    #[must_use]
    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CheckpointRequest {
    project_id: String,
    branch_id: String,
    expected_head: RemoteHead,
    idempotency_key: String,
}

impl fmt::Debug for CheckpointRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointRequest")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("expected_generation", &self.expected_head.generation)
            .field("idempotency_key", &"<redacted>")
            .finish()
    }
}

impl CheckpointRequest {
    #[must_use]
    pub fn project_id(&self) -> &str {
        &self.project_id
    }

    #[must_use]
    pub fn branch_id(&self) -> &str {
        &self.branch_id
    }

    #[must_use]
    pub const fn expected_head(&self) -> &RemoteHead {
        &self.expected_head
    }

    #[must_use]
    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct RemoteSnapshot {
    pub head: RemoteHead,
    pub snapshot_sha256: String,
}

impl fmt::Debug for RemoteSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RemoteSnapshot")
            .field("head", &self.head)
            .field("snapshot_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct RemotePushReceipt {
    pub head: RemoteHead,
    pub snapshot_sha256: String,
}

impl fmt::Debug for RemotePushReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RemotePushReceipt")
            .field("head", &self.head)
            .field("snapshot_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct RemoteCheckpointReceipt {
    pub checkpoint_id: String,
    pub revision_id: String,
    pub replayed: bool,
}

impl fmt::Debug for RemoteCheckpointReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RemoteCheckpointReceipt")
            .field("checkpoint_id", &"<redacted>")
            .field("revision_id", &"<redacted>")
            .field("replayed", &self.replayed)
            .finish()
    }
}

pub trait RemoteSyncPort: fmt::Debug {
    /// Reads the current remote snapshot for an exact observed head.
    ///
    /// # Errors
    ///
    /// Returns a typed unavailable, rejected or conflict result without mutating local state.
    fn pull(&mut self, request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure>;

    /// Pushes a checksum- and expected-head-bound local operation.
    ///
    /// # Errors
    ///
    /// Returns a typed unavailable, rejected or conflict result.
    fn push(&mut self, request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure>;

    /// Creates or replays a checkpoint for the exact expected head.
    ///
    /// # Errors
    ///
    /// Returns a typed unavailable, rejected or conflict result.
    fn checkpoint(
        &mut self,
        request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure>;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PullOutcome {
    Unchanged,
    Updated,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PushOutcome {
    pub head: RemoteHead,
}

#[derive(Clone, Eq, PartialEq)]
pub struct CheckpointOutcome {
    pub checkpoint_id: String,
    pub revision_id: String,
    pub replayed: bool,
}

impl fmt::Debug for CheckpointOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointOutcome")
            .field("checkpoint_id", &"<redacted>")
            .field("revision_id", &"<redacted>")
            .field("replayed", &self.replayed)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
pub struct MirrorSnapshot {
    pub schema_version: String,
    pub project_id: String,
    pub branch_id: String,
    pub mirror_id: String,
    pub connectivity: Connectivity,
    pub phase: MirrorPhase,
    pub observed_revision_id: Option<String>,
    pub observed_generation: u64,
    pub snapshot_sha256: String,
    pub pending_plan_sha256: Option<String>,
    pub pending_push_idempotency_key: Option<String>,
    pub conflict_revision_id: Option<String>,
    pub conflict_generation: Option<u64>,
    pub last_checkpoint_id: Option<String>,
}

impl fmt::Debug for MirrorSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MirrorSnapshot")
            .field("schema_version", &self.schema_version)
            .field("connectivity", &self.connectivity)
            .field("phase", &self.phase)
            .field("observed_generation", &self.observed_generation)
            .field("has_pending_plan", &self.pending_plan_sha256.is_some())
            .field(
                "has_pending_push",
                &self.pending_push_idempotency_key.is_some(),
            )
            .field("has_conflict", &self.conflict_generation.is_some())
            .field("has_checkpoint", &self.last_checkpoint_id.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Clone)]
pub struct LocalMirror {
    project_id: String,
    branch_id: String,
    mirror_id: String,
    connectivity: Connectivity,
    phase: MirrorPhase,
    observed_head: RemoteHead,
    snapshot_sha256: String,
    pending_plan_sha256: Option<String>,
    pending_push_idempotency_key: Option<String>,
    conflict_head: Option<RemoteHead>,
    last_checkpoint_id: Option<String>,
}

impl fmt::Debug for LocalMirror {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalMirror")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("mirror_id", &"<redacted>")
            .field("connectivity", &self.connectivity)
            .field("phase", &self.phase)
            .field("observed_generation", &self.observed_head.generation)
            .field("snapshot_sha256", &"<redacted>")
            .field("has_pending_plan", &self.pending_plan_sha256.is_some())
            .field(
                "has_pending_push",
                &self.pending_push_idempotency_key.is_some(),
            )
            .field("has_conflict", &self.conflict_head.is_some())
            .field("has_checkpoint", &self.last_checkpoint_id.is_some())
            .finish_non_exhaustive()
    }
}

impl LocalMirror {
    /// Creates a path-free local mirror state.
    ///
    /// # Errors
    ///
    /// Rejects malformed identifiers, head pairs or digests.
    pub fn new(
        project_id: String,
        branch_id: String,
        mirror_id: String,
        observed_head: RemoteHead,
        snapshot_sha256: String,
        connectivity: Connectivity,
    ) -> Result<Self, SyncError> {
        if !valid_prefixed_identifier(&project_id, "prj_")
            || !valid_prefixed_identifier(&branch_id, "brn_")
            || !valid_prefixed_identifier(&mirror_id, "mir_")
            || !valid_digest(&snapshot_sha256)
        {
            return Err(SyncError::InvalidRequest);
        }
        Ok(Self {
            project_id,
            branch_id,
            mirror_id,
            connectivity,
            phase: MirrorPhase::Clean,
            observed_head,
            snapshot_sha256,
            pending_plan_sha256: None,
            pending_push_idempotency_key: None,
            conflict_head: None,
            last_checkpoint_id: None,
        })
    }

    #[must_use]
    pub const fn connectivity(&self) -> Connectivity {
        self.connectivity
    }

    #[must_use]
    pub const fn phase(&self) -> MirrorPhase {
        self.phase
    }

    #[must_use]
    pub fn snapshot(&self) -> MirrorSnapshot {
        MirrorSnapshot {
            schema_version: "hwpx-agent.local-mirror/v1".to_owned(),
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            mirror_id: self.mirror_id.clone(),
            connectivity: self.connectivity,
            phase: self.phase,
            observed_revision_id: self.observed_head.revision_id.clone(),
            observed_generation: self.observed_head.generation,
            snapshot_sha256: self.snapshot_sha256.clone(),
            pending_plan_sha256: self.pending_plan_sha256.clone(),
            pending_push_idempotency_key: self.pending_push_idempotency_key.clone(),
            conflict_revision_id: self
                .conflict_head
                .as_ref()
                .and_then(|head| head.revision_id.clone()),
            conflict_generation: self.conflict_head.as_ref().map(|head| head.generation),
            last_checkpoint_id: self.last_checkpoint_id.clone(),
        }
    }

    pub const fn set_connectivity(&mut self, connectivity: Connectivity) {
        self.connectivity = connectivity;
    }

    /// Queues one checksum-bound local change without remote I/O.
    ///
    /// # Errors
    ///
    /// Rejects invalid digests and non-clean mirror state.
    pub fn queue_local_change(
        &mut self,
        snapshot_sha256: String,
        operation_plan_sha256: String,
    ) -> Result<(), SyncError> {
        if !valid_digest(&snapshot_sha256) || !valid_digest(&operation_plan_sha256) {
            return Err(SyncError::InvalidRequest);
        }
        if self.phase != MirrorPhase::Clean || self.pending_plan_sha256.is_some() {
            return Err(SyncError::InvalidState);
        }
        self.snapshot_sha256 = snapshot_sha256;
        self.pending_plan_sha256 = Some(operation_plan_sha256);
        self.pending_push_idempotency_key = None;
        self.phase = MirrorPhase::Ahead;
        Ok(())
    }

    /// Pulls a remote snapshot only through the injected port.
    ///
    /// # Errors
    ///
    /// Rejects offline/conflicted state and malformed or conflicting responses.
    pub fn pull(&mut self, port: &mut impl RemoteSyncPort) -> Result<PullOutcome, SyncError> {
        self.require_online()?;
        if self.phase == MirrorPhase::Conflict || self.pending_push_idempotency_key.is_some() {
            return Err(SyncError::InvalidState);
        }
        let request = PullRequest {
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            observed_head: self.observed_head.clone(),
        };
        let remote = match port.pull(&request) {
            Ok(remote) => remote,
            Err(RemoteFailure::Conflict(head)) => {
                validate_head(&head)?;
                self.conflict_head = Some(head);
                self.phase = MirrorPhase::Conflict;
                return Err(SyncError::Conflict);
            }
            Err(error) => return Err(map_remote_failure(&error)),
        };
        validate_remote_snapshot(&remote)?;
        if remote.head == self.observed_head {
            if self.phase == MirrorPhase::Clean && remote.snapshot_sha256 != self.snapshot_sha256 {
                return Err(SyncError::InvalidResponse);
            }
            return Ok(PullOutcome::Unchanged);
        }
        if self.phase == MirrorPhase::Ahead {
            self.conflict_head = Some(remote.head);
            self.phase = MirrorPhase::Conflict;
            return Err(SyncError::Conflict);
        }
        self.observed_head = remote.head;
        self.snapshot_sha256 = remote.snapshot_sha256;
        self.last_checkpoint_id = None;
        Ok(PullOutcome::Updated)
    }

    /// Pushes one queued local plan with an exact expected head and idempotency key.
    ///
    /// # Errors
    ///
    /// Rejects offline/non-ahead state, invalid keys, conflicts and malformed receipts.
    pub fn push(
        &mut self,
        port: &mut impl RemoteSyncPort,
        idempotency_key: String,
    ) -> Result<PushOutcome, SyncError> {
        self.require_online()?;
        if !valid_idempotency_key(&idempotency_key) {
            return Err(SyncError::InvalidRequest);
        }
        if self.phase != MirrorPhase::Ahead
            || self
                .pending_push_idempotency_key
                .as_ref()
                .is_some_and(|expected| expected != &idempotency_key)
        {
            return Err(SyncError::InvalidState);
        }
        let pending = self
            .pending_plan_sha256
            .clone()
            .ok_or(SyncError::InvalidState)?;
        let request = PushRequest {
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            expected_head: self.observed_head.clone(),
            snapshot_sha256: self.snapshot_sha256.clone(),
            operation_plan_sha256: pending,
            idempotency_key: idempotency_key.clone(),
        };
        self.pending_push_idempotency_key = Some(idempotency_key);
        let receipt = match port.push(&request) {
            Ok(receipt) => receipt,
            Err(RemoteFailure::Conflict(head)) => {
                validate_head(&head)?;
                self.conflict_head = Some(head);
                self.pending_push_idempotency_key = None;
                self.phase = MirrorPhase::Conflict;
                return Err(SyncError::Conflict);
            }
            Err(RemoteFailure::Rejected) => {
                self.pending_push_idempotency_key = None;
                return Err(SyncError::RemoteRejected);
            }
            Err(RemoteFailure::Unavailable) => return Err(SyncError::RemoteUnavailable),
        };
        validate_push_receipt(&request, &receipt)?;
        self.observed_head = receipt.head.clone();
        self.pending_plan_sha256 = None;
        self.pending_push_idempotency_key = None;
        self.conflict_head = None;
        self.phase = MirrorPhase::Clean;
        self.last_checkpoint_id = None;
        Ok(PushOutcome { head: receipt.head })
    }

    /// Creates or replays a remote checkpoint for the exact clean observed head.
    ///
    /// # Errors
    ///
    /// Rejects offline/non-clean state, invalid keys and mismatched receipts.
    pub fn checkpoint(
        &mut self,
        port: &mut impl RemoteSyncPort,
        idempotency_key: String,
    ) -> Result<CheckpointOutcome, SyncError> {
        self.require_online()?;
        if !valid_idempotency_key(&idempotency_key) {
            return Err(SyncError::InvalidRequest);
        }
        if self.phase != MirrorPhase::Clean || self.observed_head.revision_id.is_none() {
            return Err(SyncError::InvalidState);
        }
        let request = CheckpointRequest {
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            expected_head: self.observed_head.clone(),
            idempotency_key,
        };
        let receipt = match port.checkpoint(&request) {
            Ok(receipt) => receipt,
            Err(RemoteFailure::Conflict(head)) => {
                validate_head(&head)?;
                self.conflict_head = Some(head);
                self.phase = MirrorPhase::Conflict;
                return Err(SyncError::Conflict);
            }
            Err(error) => return Err(map_remote_failure(&error)),
        };
        if !valid_prefixed_identifier(&receipt.checkpoint_id, "chk_")
            || Some(receipt.revision_id.as_str()) != self.observed_head.revision_id()
        {
            return Err(SyncError::InvalidResponse);
        }
        self.last_checkpoint_id = Some(receipt.checkpoint_id.clone());
        Ok(CheckpointOutcome {
            checkpoint_id: receipt.checkpoint_id,
            revision_id: receipt.revision_id,
            replayed: receipt.replayed,
        })
    }

    fn require_online(&self) -> Result<(), SyncError> {
        if self.connectivity == Connectivity::Online {
            Ok(())
        } else {
            Err(SyncError::Offline)
        }
    }
}

fn validate_remote_snapshot(remote: &RemoteSnapshot) -> Result<(), SyncError> {
    validate_head(&remote.head)?;
    if valid_digest(&remote.snapshot_sha256) {
        Ok(())
    } else {
        Err(SyncError::InvalidResponse)
    }
}

fn validate_push_receipt(
    request: &PushRequest,
    receipt: &RemotePushReceipt,
) -> Result<(), SyncError> {
    validate_head(&receipt.head)?;
    if receipt.snapshot_sha256 != request.snapshot_sha256
        || receipt.head.generation
            != request
                .expected_head
                .generation
                .checked_add(1)
                .ok_or(SyncError::InvalidResponse)?
        || receipt.head.revision_id.is_none()
        || receipt.head.revision_id == request.expected_head.revision_id
    {
        return Err(SyncError::InvalidResponse);
    }
    Ok(())
}

fn validate_head(head: &RemoteHead) -> Result<(), SyncError> {
    if head.revision_id.is_none() != (head.generation == 0)
        || head
            .revision_id
            .as_deref()
            .is_some_and(|value| !valid_prefixed_identifier(value, "rev_"))
    {
        Err(SyncError::InvalidResponse)
    } else {
        Ok(())
    }
}

fn map_remote_failure(error: &RemoteFailure) -> SyncError {
    match error {
        RemoteFailure::Unavailable => SyncError::RemoteUnavailable,
        RemoteFailure::Rejected => SyncError::RemoteRejected,
        RemoteFailure::Conflict(_) => SyncError::Conflict,
    }
}

fn valid_prefixed_identifier(value: &str, prefix: &str) -> bool {
    (prefix.len() + 8..=MAX_ID_BYTES).contains(&value.len())
        && value.starts_with(prefix)
        && value[prefix.len()..]
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        && value != "0".repeat(64)
}

fn valid_idempotency_key(value: &str) -> bool {
    (8..=MAX_IDEMPOTENCY_BYTES).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}
