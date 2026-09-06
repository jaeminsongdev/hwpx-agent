#![forbid(unsafe_code)]

use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

mod adapter;
mod service_mapping;
mod store;

pub use adapter::{
    AuthenticatedRemoteSyncAdapter, AuthorizationHeader, CredentialFailure,
    RemoteCredentialProvider, RemoteTransport, TransportFailure,
};
pub use service_mapping::{
    CheckpointServiceArguments, CheckpointServiceBinding, CheckpointServiceContext,
    map_checkpoint_to_service,
};
pub use store::{DurableMirrorStore, DurableSyncError, LoadedMirror, StoreError, StoreRevision};

const MAX_ID_BYTES: usize = 120;
const MAX_IDEMPOTENCY_BYTES: usize = 120;
const MAX_CHECKPOINT_LABEL_CHARS: usize = 120;
const MAX_CHECKPOINT_NOTE_CHARS: usize = 1_000;
pub(crate) const REMOTE_SYNC_REQUEST_SCHEMA_VERSION: &str = "hwpx-agent.remote-sync-request/v3";

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

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ConflictResolution {
    RebaseOperationPlan,
    Branch,
    ManualMerge,
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
    InvalidResponse,
}

#[derive(Clone, Eq, PartialEq)]
pub struct PullRequest {
    project_id: String,
    branch_id: String,
    mirror_id: String,
    observed_head: RemoteHead,
}

impl fmt::Debug for PullRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PullRequest")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("mirror_id", &"<redacted>")
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
    pub fn mirror_id(&self) -> &str {
        &self.mirror_id
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
    mirror_id: String,
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
            .field("mirror_id", &"<redacted>")
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
    pub fn mirror_id(&self) -> &str {
        &self.mirror_id
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
    mirror_id: String,
    expected_head: RemoteHead,
    idempotency_key: String,
    label: String,
    note: Option<String>,
}

impl fmt::Debug for CheckpointRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointRequest")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("mirror_id", &"<redacted>")
            .field("expected_generation", &self.expected_head.generation)
            .field("idempotency_key", &"<redacted>")
            .field("label", &"<redacted>")
            .field("has_note", &self.note.is_some())
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
    pub fn mirror_id(&self) -> &str {
        &self.mirror_id
    }

    #[must_use]
    pub const fn expected_head(&self) -> &RemoteHead {
        &self.expected_head
    }

    #[must_use]
    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }

    #[must_use]
    pub fn label(&self) -> &str {
        &self.label
    }

    #[must_use]
    pub fn note(&self) -> Option<&str> {
        self.note.as_deref()
    }

    fn encoded_wire_request(&self) -> Result<Vec<u8>, SyncError> {
        serde_json::to_vec(&CheckpointWireRequest {
            schema_version: REMOTE_SYNC_REQUEST_SCHEMA_VERSION,
            operation: "checkpoint",
            project_id: &self.project_id,
            branch_id: &self.branch_id,
            mirror_id: &self.mirror_id,
            expected_head: CheckpointWireHead {
                revision_id: self.expected_head.revision_id(),
                generation: self.expected_head.generation(),
            },
            idempotency_key: &self.idempotency_key,
            label: &self.label,
            note: self.note.as_deref(),
        })
        .map_err(|_| SyncError::InvalidRequest)
    }

    fn wire_sha256(&self) -> Result<String, SyncError> {
        Ok(hex::encode(Sha256::digest(self.encoded_wire_request()?)))
    }
}

#[derive(Serialize)]
struct CheckpointWireRequest<'a> {
    schema_version: &'static str,
    operation: &'static str,
    project_id: &'a str,
    branch_id: &'a str,
    mirror_id: &'a str,
    expected_head: CheckpointWireHead<'a>,
    idempotency_key: &'a str,
    label: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<&'a str>,
}

#[derive(Serialize)]
struct CheckpointWireHead<'a> {
    revision_id: Option<&'a str>,
    generation: u64,
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
#[serde(deny_unknown_fields)]
pub struct MirrorSnapshot {
    pub schema_version: String,
    pub project_id: String,
    pub branch_id: String,
    pub mirror_id: String,
    pub connectivity: Connectivity,
    pub phase: MirrorPhase,
    pub observed_revision_id: Option<String>,
    pub observed_generation: u64,
    #[serde(default)]
    pub observed_snapshot_sha256: Option<String>,
    pub snapshot_sha256: String,
    pub pending_plan_sha256: Option<String>,
    pub pending_push_idempotency_key: Option<String>,
    #[serde(default)]
    pub pending_checkpoint_idempotency_key: Option<String>,
    #[serde(default)]
    pub pending_checkpoint_request_sha256: Option<String>,
    pub conflict_revision_id: Option<String>,
    pub conflict_generation: Option<u64>,
    #[serde(default)]
    pub last_conflict_resolution: Option<ConflictResolution>,
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
            .field(
                "has_pending_checkpoint",
                &self.pending_checkpoint_idempotency_key.is_some(),
            )
            .field("has_conflict", &self.conflict_generation.is_some())
            .field("last_conflict_resolution", &self.last_conflict_resolution)
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
    observed_snapshot_sha256: String,
    snapshot_sha256: String,
    pending_plan_sha256: Option<String>,
    pending_push_idempotency_key: Option<String>,
    pending_checkpoint_idempotency_key: Option<String>,
    pending_checkpoint_request_sha256: Option<String>,
    conflict_head: Option<RemoteHead>,
    last_conflict_resolution: Option<ConflictResolution>,
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
            .field(
                "has_pending_checkpoint",
                &self.pending_checkpoint_idempotency_key.is_some(),
            )
            .field("has_conflict", &self.conflict_head.is_some())
            .field("last_conflict_resolution", &self.last_conflict_resolution)
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
            observed_snapshot_sha256: snapshot_sha256.clone(),
            snapshot_sha256,
            pending_plan_sha256: None,
            pending_push_idempotency_key: None,
            pending_checkpoint_idempotency_key: None,
            pending_checkpoint_request_sha256: None,
            conflict_head: None,
            last_conflict_resolution: None,
            last_checkpoint_id: None,
        })
    }

    /// Restores one durable mirror snapshot after validating every state invariant.
    ///
    /// # Errors
    ///
    /// Rejects unknown schemas, malformed private fields and impossible state combinations.
    pub fn restore(snapshot: MirrorSnapshot) -> Result<Self, SyncError> {
        validate_snapshot_fields(&snapshot)?;
        let observed_head = RemoteHead::new(
            snapshot.observed_revision_id.clone(),
            snapshot.observed_generation,
        )?;
        let observed_snapshot_sha256 = restore_observed_snapshot(&snapshot)?;
        let conflict_head = restore_conflict_head(&snapshot, &observed_head)?;
        validate_snapshot_state(&snapshot, &observed_head, conflict_head.as_ref())?;
        Ok(Self {
            project_id: snapshot.project_id,
            branch_id: snapshot.branch_id,
            mirror_id: snapshot.mirror_id,
            connectivity: snapshot.connectivity,
            phase: snapshot.phase,
            observed_head,
            observed_snapshot_sha256,
            snapshot_sha256: snapshot.snapshot_sha256,
            pending_plan_sha256: snapshot.pending_plan_sha256,
            pending_push_idempotency_key: snapshot.pending_push_idempotency_key,
            pending_checkpoint_idempotency_key: snapshot.pending_checkpoint_idempotency_key,
            pending_checkpoint_request_sha256: snapshot.pending_checkpoint_request_sha256,
            conflict_head,
            last_conflict_resolution: snapshot.last_conflict_resolution,
            last_checkpoint_id: snapshot.last_checkpoint_id,
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
            schema_version: "hwpx-agent.local-mirror/v5".to_owned(),
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            mirror_id: self.mirror_id.clone(),
            connectivity: self.connectivity,
            phase: self.phase,
            observed_revision_id: self.observed_head.revision_id.clone(),
            observed_generation: self.observed_head.generation,
            observed_snapshot_sha256: Some(self.observed_snapshot_sha256.clone()),
            snapshot_sha256: self.snapshot_sha256.clone(),
            pending_plan_sha256: self.pending_plan_sha256.clone(),
            pending_push_idempotency_key: self.pending_push_idempotency_key.clone(),
            pending_checkpoint_idempotency_key: self.pending_checkpoint_idempotency_key.clone(),
            pending_checkpoint_request_sha256: self.pending_checkpoint_request_sha256.clone(),
            conflict_revision_id: self
                .conflict_head
                .as_ref()
                .and_then(|head| head.revision_id.clone()),
            conflict_generation: self.conflict_head.as_ref().map(|head| head.generation),
            last_conflict_resolution: self.last_conflict_resolution,
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
        if self.phase != MirrorPhase::Clean
            || self.pending_plan_sha256.is_some()
            || self.pending_checkpoint_idempotency_key.is_some()
        {
            return Err(SyncError::InvalidState);
        }
        self.snapshot_sha256 = snapshot_sha256;
        self.pending_plan_sha256 = Some(operation_plan_sha256);
        self.pending_push_idempotency_key = None;
        self.pending_checkpoint_idempotency_key = None;
        self.pending_checkpoint_request_sha256 = None;
        self.phase = MirrorPhase::Ahead;
        self.last_conflict_resolution = None;
        self.last_checkpoint_id = None;
        Ok(())
    }

    /// Resolves an exact stale head by rebasing the pending operation plan onto that head.
    ///
    /// A conflict without local work may omit the rebased pair and adopts the remote snapshot as
    /// clean state. A conflict with local work must supply both the rebased output snapshot and
    /// replacement operation-plan digest.
    ///
    /// # Errors
    ///
    /// Rejects non-conflict state, stale/mismatched remote evidence, malformed digests and partial
    /// rebased pairs without changing the mirror.
    pub fn resolve_rebase(
        &mut self,
        remote: RemoteSnapshot,
        rebased: Option<(String, String)>,
    ) -> Result<(), SyncError> {
        self.validate_resolution_remote(&remote)?;
        let had_local_plan = self.pending_plan_sha256.is_some();
        let (snapshot_sha256, pending_plan_sha256, phase) = match (had_local_plan, rebased) {
            (false, None) => (remote.snapshot_sha256.clone(), None, MirrorPhase::Clean),
            (true, Some((snapshot, plan))) if valid_digest(&snapshot) && valid_digest(&plan) => {
                (snapshot, Some(plan), MirrorPhase::Ahead)
            }
            _ => return Err(SyncError::InvalidRequest),
        };
        self.observed_head = remote.head;
        self.observed_snapshot_sha256 = remote.snapshot_sha256;
        self.snapshot_sha256 = snapshot_sha256;
        self.pending_plan_sha256 = pending_plan_sha256;
        self.conflict_head = None;
        self.phase = phase;
        self.last_conflict_resolution = Some(ConflictResolution::RebaseOperationPlan);
        self.last_checkpoint_id = None;
        Ok(())
    }

    /// Moves the pending local plan to a separately created branch at the exact old base.
    ///
    /// # Errors
    ///
    /// Rejects the current branch, a different base head/snapshot, malformed identity or any
    /// non-conflict state without changing the mirror.
    pub fn resolve_branch(
        &mut self,
        branch_id: String,
        branch_base: RemoteSnapshot,
    ) -> Result<(), SyncError> {
        self.require_resolvable_conflict()?;
        validate_remote_snapshot(&branch_base)?;
        if !valid_prefixed_identifier(&branch_id, "brn_")
            || branch_id == self.branch_id
            || branch_base.head != self.observed_head
            || branch_base.snapshot_sha256 != self.observed_snapshot_sha256
        {
            return Err(SyncError::InvalidRequest);
        }
        self.branch_id = branch_id;
        self.observed_head = branch_base.head;
        self.observed_snapshot_sha256 = branch_base.snapshot_sha256;
        self.conflict_head = None;
        self.phase = if self.pending_plan_sha256.is_some() {
            MirrorPhase::Ahead
        } else {
            MirrorPhase::Clean
        };
        self.last_conflict_resolution = Some(ConflictResolution::Branch);
        self.last_checkpoint_id = None;
        Ok(())
    }

    /// Accepts one externally completed manual merge against the exact conflicting remote head.
    ///
    /// # Errors
    ///
    /// Rejects stale/mismatched remote evidence or malformed merged digests without changing the
    /// mirror. The merged result always remains ahead until a normal push succeeds.
    pub fn resolve_manual_merge(
        &mut self,
        remote: RemoteSnapshot,
        merged_snapshot_sha256: String,
        merged_operation_plan_sha256: String,
    ) -> Result<(), SyncError> {
        self.validate_resolution_remote(&remote)?;
        if !valid_digest(&merged_snapshot_sha256) || !valid_digest(&merged_operation_plan_sha256) {
            return Err(SyncError::InvalidRequest);
        }
        self.observed_head = remote.head;
        self.observed_snapshot_sha256 = remote.snapshot_sha256;
        self.snapshot_sha256 = merged_snapshot_sha256;
        self.pending_plan_sha256 = Some(merged_operation_plan_sha256);
        self.conflict_head = None;
        self.phase = MirrorPhase::Ahead;
        self.last_conflict_resolution = Some(ConflictResolution::ManualMerge);
        self.last_checkpoint_id = None;
        Ok(())
    }

    fn require_resolvable_conflict(&self) -> Result<(), SyncError> {
        if self.phase == MirrorPhase::Conflict
            && self.conflict_head.is_some()
            && self.pending_push_idempotency_key.is_none()
            && self.pending_checkpoint_idempotency_key.is_none()
        {
            Ok(())
        } else {
            Err(SyncError::InvalidState)
        }
    }

    fn validate_resolution_remote(&self, remote: &RemoteSnapshot) -> Result<(), SyncError> {
        self.require_resolvable_conflict()?;
        validate_remote_snapshot(remote)?;
        if self.conflict_head.as_ref() == Some(&remote.head) {
            Ok(())
        } else {
            Err(SyncError::InvalidResponse)
        }
    }

    /// Pulls a remote snapshot only through the injected port.
    ///
    /// # Errors
    ///
    /// Rejects offline/conflicted state and malformed or conflicting responses.
    pub fn pull(&mut self, port: &mut impl RemoteSyncPort) -> Result<PullOutcome, SyncError> {
        self.require_online()?;
        if self.phase == MirrorPhase::Conflict
            || self.pending_push_idempotency_key.is_some()
            || self.pending_checkpoint_idempotency_key.is_some()
        {
            return Err(SyncError::InvalidState);
        }
        let request = PullRequest {
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            mirror_id: self.mirror_id.clone(),
            observed_head: self.observed_head.clone(),
        };
        let remote = match port.pull(&request) {
            Ok(remote) => remote,
            Err(RemoteFailure::Conflict(head)) => {
                validate_conflict_head(&self.observed_head, &head)?;
                self.conflict_head = Some(head);
                self.phase = MirrorPhase::Conflict;
                self.last_conflict_resolution = None;
                return Err(SyncError::Conflict);
            }
            Err(error) => return Err(map_remote_failure(&error)),
        };
        validate_remote_snapshot(&remote)?;
        if remote.head == self.observed_head {
            if remote.snapshot_sha256 != self.observed_snapshot_sha256 {
                return Err(SyncError::InvalidResponse);
            }
            return Ok(PullOutcome::Unchanged);
        }
        validate_forward_head(&self.observed_head, &remote.head)?;
        if self.phase == MirrorPhase::Ahead {
            self.conflict_head = Some(remote.head);
            self.phase = MirrorPhase::Conflict;
            self.last_conflict_resolution = None;
            return Err(SyncError::Conflict);
        }
        self.observed_head = remote.head;
        self.observed_snapshot_sha256
            .clone_from(&remote.snapshot_sha256);
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
        let (request, _) = self.prepare_push(idempotency_key)?;
        let response = port.push(&request);
        self.apply_push_result(&request, response)
    }

    pub(crate) fn prepare_push(
        &mut self,
        idempotency_key: String,
    ) -> Result<(PushRequest, bool), SyncError> {
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
            mirror_id: self.mirror_id.clone(),
            expected_head: self.observed_head.clone(),
            snapshot_sha256: self.snapshot_sha256.clone(),
            operation_plan_sha256: pending,
            idempotency_key: idempotency_key.clone(),
        };
        let changed = self.pending_push_idempotency_key.is_none();
        self.pending_push_idempotency_key = Some(idempotency_key);
        Ok((request, changed))
    }

    pub(crate) fn apply_push_result(
        &mut self,
        request: &PushRequest,
        response: Result<RemotePushReceipt, RemoteFailure>,
    ) -> Result<PushOutcome, SyncError> {
        if self.pending_push_idempotency_key.as_deref() != Some(request.idempotency_key()) {
            return Err(SyncError::InvalidState);
        }
        let receipt = match response {
            Ok(receipt) => receipt,
            Err(RemoteFailure::Conflict(head)) => {
                validate_conflict_head(&self.observed_head, &head)?;
                self.conflict_head = Some(head);
                self.pending_push_idempotency_key = None;
                self.phase = MirrorPhase::Conflict;
                self.last_conflict_resolution = None;
                return Err(SyncError::Conflict);
            }
            Err(RemoteFailure::Rejected) => {
                self.pending_push_idempotency_key = None;
                return Err(SyncError::RemoteRejected);
            }
            Err(RemoteFailure::Unavailable) => return Err(SyncError::RemoteUnavailable),
            Err(RemoteFailure::InvalidResponse) => return Err(SyncError::InvalidResponse),
        };
        validate_push_receipt(request, &receipt)?;
        self.observed_head = receipt.head.clone();
        self.observed_snapshot_sha256
            .clone_from(&receipt.snapshot_sha256);
        self.pending_plan_sha256 = None;
        self.pending_push_idempotency_key = None;
        self.conflict_head = None;
        self.phase = MirrorPhase::Clean;
        self.last_checkpoint_id = None;
        Ok(PushOutcome { head: receipt.head })
    }

    /// Creates or replays a metadata-bound remote checkpoint for the exact clean observed head.
    ///
    /// # Errors
    ///
    /// Rejects offline/non-clean state, invalid keys or metadata and mismatched receipts.
    pub fn checkpoint(
        &mut self,
        port: &mut impl RemoteSyncPort,
        idempotency_key: String,
        label: String,
        note: Option<String>,
    ) -> Result<CheckpointOutcome, SyncError> {
        let (request, _) = self.prepare_checkpoint(idempotency_key, label, note)?;
        let response = port.checkpoint(&request);
        self.apply_checkpoint_result(&request, response)
    }

    pub(crate) fn prepare_checkpoint(
        &mut self,
        idempotency_key: String,
        label: String,
        note: Option<String>,
    ) -> Result<(CheckpointRequest, bool), SyncError> {
        self.require_online()?;
        if !valid_idempotency_key(&idempotency_key)
            || !valid_checkpoint_label(&label)
            || !valid_checkpoint_note(note.as_deref())
        {
            return Err(SyncError::InvalidRequest);
        }
        if self.phase != MirrorPhase::Clean || self.observed_head.revision_id.is_none() {
            return Err(SyncError::InvalidState);
        }
        let request = CheckpointRequest {
            project_id: self.project_id.clone(),
            branch_id: self.branch_id.clone(),
            mirror_id: self.mirror_id.clone(),
            expected_head: self.observed_head.clone(),
            idempotency_key: idempotency_key.clone(),
            label,
            note,
        };
        let request_sha256 = request.wire_sha256()?;
        if self
            .pending_checkpoint_idempotency_key
            .as_ref()
            .is_some_and(|expected| expected != &idempotency_key)
            || self
                .pending_checkpoint_request_sha256
                .as_ref()
                .is_some_and(|expected| expected != &request_sha256)
            || self.pending_checkpoint_idempotency_key.is_some()
                != self.pending_checkpoint_request_sha256.is_some()
        {
            return Err(SyncError::InvalidState);
        }
        let changed = self.pending_checkpoint_idempotency_key.is_none();
        self.pending_checkpoint_idempotency_key = Some(idempotency_key);
        self.pending_checkpoint_request_sha256 = Some(request_sha256);
        Ok((request, changed))
    }

    pub(crate) fn apply_checkpoint_result(
        &mut self,
        request: &CheckpointRequest,
        response: Result<RemoteCheckpointReceipt, RemoteFailure>,
    ) -> Result<CheckpointOutcome, SyncError> {
        let request_sha256 = request.wire_sha256()?;
        if self.pending_checkpoint_idempotency_key.as_deref() != Some(request.idempotency_key())
            || self.pending_checkpoint_request_sha256.as_deref() != Some(request_sha256.as_str())
        {
            return Err(SyncError::InvalidState);
        }
        let receipt = match response {
            Ok(receipt) => receipt,
            Err(RemoteFailure::Conflict(head)) => {
                validate_conflict_head(&self.observed_head, &head)?;
                self.conflict_head = Some(head);
                self.pending_checkpoint_idempotency_key = None;
                self.pending_checkpoint_request_sha256 = None;
                self.phase = MirrorPhase::Conflict;
                self.last_conflict_resolution = None;
                return Err(SyncError::Conflict);
            }
            Err(RemoteFailure::Rejected) => {
                self.pending_checkpoint_idempotency_key = None;
                self.pending_checkpoint_request_sha256 = None;
                return Err(SyncError::RemoteRejected);
            }
            Err(RemoteFailure::Unavailable) => return Err(SyncError::RemoteUnavailable),
            Err(RemoteFailure::InvalidResponse) => return Err(SyncError::InvalidResponse),
        };
        if !valid_prefixed_identifier(&receipt.checkpoint_id, "chk_")
            || Some(receipt.revision_id.as_str()) != self.observed_head.revision_id()
        {
            return Err(SyncError::InvalidResponse);
        }
        self.pending_checkpoint_idempotency_key = None;
        self.pending_checkpoint_request_sha256 = None;
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

fn validate_snapshot_fields(snapshot: &MirrorSnapshot) -> Result<(), SyncError> {
    let checkpoint_binding_is_valid = match snapshot.schema_version.as_str() {
        "hwpx-agent.local-mirror/v5" => {
            snapshot.pending_checkpoint_idempotency_key.is_some()
                == snapshot.pending_checkpoint_request_sha256.is_some()
                && snapshot
                    .pending_checkpoint_request_sha256
                    .as_deref()
                    .is_none_or(valid_digest)
        }
        "hwpx-agent.local-mirror/v1"
        | "hwpx-agent.local-mirror/v2"
        | "hwpx-agent.local-mirror/v3"
        | "hwpx-agent.local-mirror/v4" => {
            snapshot.pending_checkpoint_idempotency_key.is_none()
                && snapshot.pending_checkpoint_request_sha256.is_none()
        }
        _ => false,
    };
    let valid = matches!(
        snapshot.schema_version.as_str(),
        "hwpx-agent.local-mirror/v1"
            | "hwpx-agent.local-mirror/v2"
            | "hwpx-agent.local-mirror/v3"
            | "hwpx-agent.local-mirror/v4"
            | "hwpx-agent.local-mirror/v5"
    ) && valid_prefixed_identifier(&snapshot.project_id, "prj_")
        && valid_prefixed_identifier(&snapshot.branch_id, "brn_")
        && valid_prefixed_identifier(&snapshot.mirror_id, "mir_")
        && valid_digest(&snapshot.snapshot_sha256)
        && snapshot
            .pending_plan_sha256
            .as_deref()
            .is_none_or(valid_digest)
        && snapshot
            .pending_push_idempotency_key
            .as_deref()
            .is_none_or(valid_idempotency_key)
        && snapshot
            .pending_checkpoint_idempotency_key
            .as_deref()
            .is_none_or(valid_idempotency_key)
        && checkpoint_binding_is_valid
        && (snapshot.schema_version == "hwpx-agent.local-mirror/v4"
            || snapshot.schema_version == "hwpx-agent.local-mirror/v5"
            || snapshot.last_conflict_resolution.is_none())
        && snapshot
            .last_checkpoint_id
            .as_deref()
            .is_none_or(|value| valid_prefixed_identifier(value, "chk_"));
    valid.then_some(()).ok_or(SyncError::InvalidRequest)
}

fn restore_observed_snapshot(snapshot: &MirrorSnapshot) -> Result<String, SyncError> {
    match snapshot.schema_version.as_str() {
        "hwpx-agent.local-mirror/v2"
        | "hwpx-agent.local-mirror/v3"
        | "hwpx-agent.local-mirror/v4"
        | "hwpx-agent.local-mirror/v5" => snapshot
            .observed_snapshot_sha256
            .clone()
            .filter(|value| valid_digest(value))
            .ok_or(SyncError::InvalidRequest),
        "hwpx-agent.local-mirror/v1"
            if snapshot.phase == MirrorPhase::Clean
                && snapshot.pending_plan_sha256.is_none()
                && snapshot.observed_snapshot_sha256.is_none()
                && snapshot.conflict_generation.is_none() =>
        {
            Ok(snapshot.snapshot_sha256.clone())
        }
        _ => Err(SyncError::InvalidRequest),
    }
}

fn restore_conflict_head(
    snapshot: &MirrorSnapshot,
    observed: &RemoteHead,
) -> Result<Option<RemoteHead>, SyncError> {
    match (
        snapshot.conflict_revision_id.clone(),
        snapshot.conflict_generation,
    ) {
        (None, None) => Ok(None),
        (revision_id, Some(generation)) => {
            let head = RemoteHead::new(revision_id, generation)?;
            if head.generation <= observed.generation || head.revision_id == observed.revision_id {
                Err(SyncError::InvalidRequest)
            } else {
                Ok(Some(head))
            }
        }
        (Some(_), None) => Err(SyncError::InvalidRequest),
    }
}

fn validate_snapshot_state(
    snapshot: &MirrorSnapshot,
    observed: &RemoteHead,
    conflict: Option<&RemoteHead>,
) -> Result<(), SyncError> {
    let phase_is_valid = match snapshot.phase {
        MirrorPhase::Clean => {
            snapshot.pending_plan_sha256.is_none()
                && snapshot.pending_push_idempotency_key.is_none()
                && conflict.is_none()
        }
        MirrorPhase::Ahead => {
            snapshot.pending_plan_sha256.is_some()
                && snapshot.pending_checkpoint_idempotency_key.is_none()
                && conflict.is_none()
        }
        MirrorPhase::Conflict => {
            conflict.is_some()
                && snapshot.pending_push_idempotency_key.is_none()
                && snapshot.pending_checkpoint_idempotency_key.is_none()
                && snapshot.last_conflict_resolution.is_none()
        }
    };
    let keys_are_valid = !(snapshot.pending_push_idempotency_key.is_some()
        && (snapshot.pending_plan_sha256.is_none()
            || snapshot.pending_checkpoint_idempotency_key.is_some()))
        && !(snapshot.pending_checkpoint_idempotency_key.is_some()
            && observed.revision_id.is_none());
    let checkpoint_is_valid = snapshot.last_checkpoint_id.is_none()
        || (snapshot.phase == MirrorPhase::Clean && observed.revision_id.is_some());
    (phase_is_valid && keys_are_valid && checkpoint_is_valid)
        .then_some(())
        .ok_or(SyncError::InvalidRequest)
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

fn validate_conflict_head(observed: &RemoteHead, conflict: &RemoteHead) -> Result<(), SyncError> {
    validate_head(conflict)?;
    validate_forward_head(observed, conflict)
}

fn validate_forward_head(observed: &RemoteHead, candidate: &RemoteHead) -> Result<(), SyncError> {
    if candidate.generation <= observed.generation || candidate.revision_id == observed.revision_id
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
        RemoteFailure::InvalidResponse => SyncError::InvalidResponse,
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

fn valid_checkpoint_label(value: &str) -> bool {
    (1..=MAX_CHECKPOINT_LABEL_CHARS).contains(&value.chars().count())
        && value.trim_matches(' ') == value
        && !value.chars().any(char::is_control)
}

fn valid_checkpoint_note(value: Option<&str>) -> bool {
    value.is_none_or(|note| (1..=MAX_CHECKPOINT_NOTE_CHARS).contains(&note.chars().count()))
}
