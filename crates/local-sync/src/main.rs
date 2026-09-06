#![forbid(unsafe_code)]

use std::env;
use std::ffi::OsString;
use std::path::PathBuf;
use std::process::ExitCode;

use local_sync::{
    CheckpointRequest, ConflictResolution, Connectivity, DurableMirrorStore, DurableSyncError,
    LocalMirror, MirrorSnapshot, PullRequest, PushRequest, RemoteCheckpointReceipt, RemoteFailure,
    RemoteHead, RemotePushReceipt, RemoteSnapshot, RemoteSyncPort, StoreError, SyncError,
};
use serde::Serialize;
use thiserror::Error;

fn main() -> ExitCode {
    let mut remote = HostAdapterRequiredPort;
    match run(env::args_os().skip(1).collect(), &mut remote) {
        Ok(output) => {
            if let Ok(json) = serde_json::to_string(&output) {
                println!("{json}");
                ExitCode::SUCCESS
            } else {
                eprintln!("SERIALIZATION_FAILED");
                ExitCode::from(2)
            }
        }
        Err(error) => {
            eprintln!("{}", error.code());
            ExitCode::from(2)
        }
    }
}

#[derive(Debug, Error)]
enum CliError {
    #[error("invalid CLI request")]
    InvalidRequest,
    #[error("local sync state is absent")]
    StateAbsent,
    #[error("local sync state rejected the transition")]
    StateRejected,
    #[error("remote sync transport is unavailable")]
    RemoteUnavailable,
    #[error("remote sync request was rejected")]
    RemoteRejected,
    #[error("remote sync head conflicts with local state")]
    RemoteConflict,
    #[error("remote sync response was invalid")]
    RemoteInvalid,
    #[error("local sync store is invalid")]
    StoreInvalid,
    #[error("local sync store is unavailable")]
    StoreUnavailable,
    #[error("local sync store is corrupt")]
    StoreCorrupt,
    #[error("local sync store capacity is exhausted")]
    StoreCapacity,
    #[error("local sync store was changed concurrently")]
    StoreConflict,
}

impl CliError {
    const fn code(&self) -> &'static str {
        match self {
            Self::InvalidRequest => "INVALID_REQUEST",
            Self::StateAbsent => "STATE_ABSENT",
            Self::StateRejected => "STATE_REJECTED",
            Self::RemoteUnavailable => "REMOTE_UNAVAILABLE",
            Self::RemoteRejected => "REMOTE_REJECTED",
            Self::RemoteConflict => "REMOTE_CONFLICT",
            Self::RemoteInvalid => "REMOTE_INVALID",
            Self::StoreInvalid => "STORE_INVALID",
            Self::StoreUnavailable => "STORE_UNAVAILABLE",
            Self::StoreCorrupt => "STORE_CORRUPT",
            Self::StoreCapacity => "STORE_CAPACITY",
            Self::StoreConflict => "STORE_CONFLICT",
        }
    }
}

impl From<StoreError> for CliError {
    fn from(error: StoreError) -> Self {
        match error {
            StoreError::InvalidConfiguration => Self::StoreInvalid,
            StoreError::Unavailable => Self::StoreUnavailable,
            StoreError::Corrupt => Self::StoreCorrupt,
            StoreError::CapacityExceeded => Self::StoreCapacity,
            StoreError::Conflict => Self::StoreConflict,
            StoreError::TransitionRejected => Self::StateRejected,
        }
    }
}

impl From<DurableSyncError> for CliError {
    fn from(error: DurableSyncError) -> Self {
        match error {
            DurableSyncError::Store(error) => Self::from(error),
            DurableSyncError::Sync(error) => map_sync_error(&error),
        }
    }
}

#[derive(Serialize)]
struct PublicOutput {
    schema_version: &'static str,
    command: &'static str,
    sequence: u64,
    connectivity: Connectivity,
    phase: local_sync::MirrorPhase,
    observed_generation: u64,
    pending: PublicPending,
    remote: PublicRemote,
    last_resolution: Option<ConflictResolution>,
    stale_head: PublicStaleHead,
}

#[derive(Serialize)]
struct PublicPending {
    plan: bool,
    uncertain_push: bool,
    uncertain_checkpoint: bool,
}

#[derive(Serialize)]
struct PublicRemote {
    conflict: bool,
    checkpoint: bool,
}

#[derive(Serialize)]
struct PublicStaleHead {
    active: bool,
    current_generation: Option<u64>,
    delta: Option<u64>,
    allowed_resolutions: Vec<ConflictResolution>,
}

fn run(
    arguments: Vec<OsString>,
    remote: &mut impl RemoteSyncPort,
) -> Result<PublicOutput, CliError> {
    let mut arguments = arguments.into_iter();
    let command = text(arguments.next())?;
    match command.as_str() {
        "init" => initialize(arguments),
        "status" => {
            let root = path(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
            Ok(public_output(
                "status",
                loaded.revision().sequence(),
                &loaded.mirror().snapshot(),
            ))
        }
        "set-connectivity" => {
            let root = path(arguments.next())?;
            let connectivity = connectivity(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
            let (revision, snapshot) = store.update(loaded.revision(), |mirror| {
                mirror.set_connectivity(connectivity);
                Ok(mirror.snapshot())
            })?;
            Ok(public_output(
                "set-connectivity",
                revision.sequence(),
                &snapshot,
            ))
        }
        "queue" => {
            let root = path(arguments.next())?;
            let snapshot_sha256 = text(arguments.next())?;
            let operation_plan_sha256 = text(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
            let (revision, snapshot) = store.update(loaded.revision(), |mirror| {
                mirror.queue_local_change(snapshot_sha256, operation_plan_sha256)?;
                Ok(mirror.snapshot())
            })?;
            Ok(public_output("queue", revision.sequence(), &snapshot))
        }
        "pull" => {
            let root = path(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let (revision, _) = store.pull_remote(remote)?;
            let snapshot = store
                .load()?
                .ok_or(CliError::StateAbsent)?
                .mirror()
                .snapshot();
            Ok(public_output("pull", revision.sequence(), &snapshot))
        }
        "push" => {
            let root = path(arguments.next())?;
            let idempotency_key = text(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let (revision, _) = store.push_remote(remote, idempotency_key)?;
            let snapshot = store
                .load()?
                .ok_or(CliError::StateAbsent)?
                .mirror()
                .snapshot();
            Ok(public_output("push", revision.sequence(), &snapshot))
        }
        "checkpoint" => {
            let root = path(arguments.next())?;
            let idempotency_key = text(arguments.next())?;
            no_more(arguments)?;
            let store = DurableMirrorStore::open_existing(root)?;
            let (revision, _) = store.checkpoint_remote(remote, idempotency_key)?;
            let snapshot = store
                .load()?
                .ok_or(CliError::StateAbsent)?
                .mirror()
                .snapshot();
            Ok(public_output("checkpoint", revision.sequence(), &snapshot))
        }
        "resolve-rebase" => resolve_rebase_command(arguments),
        "resolve-branch" => resolve_branch_command(arguments),
        "resolve-manual" => resolve_manual_command(arguments),
        _ => Err(CliError::InvalidRequest),
    }
}

fn initialize(mut arguments: impl Iterator<Item = OsString>) -> Result<PublicOutput, CliError> {
    let root = path(arguments.next())?;
    let project_id = text(arguments.next())?;
    let branch_id = text(arguments.next())?;
    let mirror_id = text(arguments.next())?;
    let snapshot_sha256 = text(arguments.next())?;
    let connectivity = connectivity(arguments.next())?;
    let remaining: Vec<_> = arguments.collect();
    let observed_head = match remaining.as_slice() {
        [] => RemoteHead::new(None, 0).map_err(|error| map_sync_error(&error))?,
        [revision, generation] => RemoteHead::new(
            Some(text(Some(revision.clone()))?),
            text(Some(generation.clone()))?
                .parse()
                .map_err(|_| CliError::InvalidRequest)?,
        )
        .map_err(|error| map_sync_error(&error))?,
        _ => return Err(CliError::InvalidRequest),
    };
    let mirror = LocalMirror::new(
        project_id,
        branch_id,
        mirror_id,
        observed_head,
        snapshot_sha256,
        connectivity,
    )
    .map_err(|error| map_sync_error(&error))?;
    let store = DurableMirrorStore::open(root)?;
    let revision = store.initialize(&mirror)?;
    Ok(public_output(
        "init",
        revision.sequence(),
        &mirror.snapshot(),
    ))
}

fn public_output(command: &'static str, sequence: u64, snapshot: &MirrorSnapshot) -> PublicOutput {
    PublicOutput {
        schema_version: "hwpx-agent.local-sync-cli-output/v2",
        command,
        sequence,
        connectivity: snapshot.connectivity,
        phase: snapshot.phase,
        observed_generation: snapshot.observed_generation,
        pending: PublicPending {
            plan: snapshot.pending_plan_sha256.is_some(),
            uncertain_push: snapshot.pending_push_idempotency_key.is_some(),
            uncertain_checkpoint: snapshot.pending_checkpoint_idempotency_key.is_some(),
        },
        remote: PublicRemote {
            conflict: snapshot.conflict_generation.is_some(),
            checkpoint: snapshot.last_checkpoint_id.is_some(),
        },
        last_resolution: snapshot.last_conflict_resolution,
        stale_head: PublicStaleHead {
            active: snapshot.conflict_generation.is_some(),
            current_generation: snapshot.conflict_generation,
            delta: snapshot
                .conflict_generation
                .and_then(|generation| generation.checked_sub(snapshot.observed_generation)),
            allowed_resolutions: if snapshot.conflict_generation.is_some() {
                vec![
                    ConflictResolution::RebaseOperationPlan,
                    ConflictResolution::Branch,
                    ConflictResolution::ManualMerge,
                ]
            } else {
                Vec::new()
            },
        },
    }
}

fn resolve_rebase_command(
    mut arguments: impl Iterator<Item = OsString>,
) -> Result<PublicOutput, CliError> {
    let root = path(arguments.next())?;
    let remaining: Vec<_> = arguments.collect();
    let (remote, rebased) = match remaining.as_slice() {
        [revision_id, generation, remote_snapshot] => (
            remote_snapshot_from(revision_id, generation, remote_snapshot)?,
            None,
        ),
        [
            revision_id,
            generation,
            remote_snapshot,
            rebased_snapshot,
            rebased_plan,
        ] => (
            remote_snapshot_from(revision_id, generation, remote_snapshot)?,
            Some((
                text(Some(rebased_snapshot.clone()))?,
                text(Some(rebased_plan.clone()))?,
            )),
        ),
        _ => return Err(CliError::InvalidRequest),
    };
    let store = DurableMirrorStore::open_existing(root)?;
    let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
    let (revision, snapshot) = store.update(loaded.revision(), |mirror| {
        mirror.resolve_rebase(remote, rebased)?;
        Ok(mirror.snapshot())
    })?;
    Ok(public_output(
        "resolve-rebase",
        revision.sequence(),
        &snapshot,
    ))
}

fn resolve_branch_command(
    mut arguments: impl Iterator<Item = OsString>,
) -> Result<PublicOutput, CliError> {
    let root = path(arguments.next())?;
    let branch_id = text(arguments.next())?;
    let base = remote_snapshot_from(
        &arguments.next().ok_or(CliError::InvalidRequest)?,
        &arguments.next().ok_or(CliError::InvalidRequest)?,
        &arguments.next().ok_or(CliError::InvalidRequest)?,
    )?;
    no_more(arguments)?;
    let store = DurableMirrorStore::open_existing(root)?;
    let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
    let (revision, snapshot) = store.update(loaded.revision(), |mirror| {
        mirror.resolve_branch(branch_id, base)?;
        Ok(mirror.snapshot())
    })?;
    Ok(public_output(
        "resolve-branch",
        revision.sequence(),
        &snapshot,
    ))
}

fn resolve_manual_command(
    mut arguments: impl Iterator<Item = OsString>,
) -> Result<PublicOutput, CliError> {
    let root = path(arguments.next())?;
    let remote = remote_snapshot_from(
        &arguments.next().ok_or(CliError::InvalidRequest)?,
        &arguments.next().ok_or(CliError::InvalidRequest)?,
        &arguments.next().ok_or(CliError::InvalidRequest)?,
    )?;
    let merged_snapshot = text(arguments.next())?;
    let merged_plan = text(arguments.next())?;
    no_more(arguments)?;
    let store = DurableMirrorStore::open_existing(root)?;
    let loaded = store.load()?.ok_or(CliError::StateAbsent)?;
    let (revision, snapshot) = store.update(loaded.revision(), |mirror| {
        mirror.resolve_manual_merge(remote, merged_snapshot, merged_plan)?;
        Ok(mirror.snapshot())
    })?;
    Ok(public_output(
        "resolve-manual",
        revision.sequence(),
        &snapshot,
    ))
}

fn remote_snapshot_from(
    revision_id: &OsString,
    generation: &OsString,
    snapshot_sha256: &OsString,
) -> Result<RemoteSnapshot, CliError> {
    let revision_id = text(Some(revision_id.clone()))?;
    let generation = text(Some(generation.clone()))?
        .parse()
        .map_err(|_| CliError::InvalidRequest)?;
    let revision_id = if revision_id == "none" {
        None
    } else {
        Some(revision_id)
    };
    let head = RemoteHead::new(revision_id, generation).map_err(|error| map_sync_error(&error))?;
    Ok(RemoteSnapshot {
        head,
        snapshot_sha256: text(Some(snapshot_sha256.clone()))?,
    })
}

fn text(value: Option<OsString>) -> Result<String, CliError> {
    value
        .ok_or(CliError::InvalidRequest)?
        .into_string()
        .map_err(|_| CliError::InvalidRequest)
}

fn path(value: Option<OsString>) -> Result<PathBuf, CliError> {
    value.map(PathBuf::from).ok_or(CliError::InvalidRequest)
}

fn connectivity(value: Option<OsString>) -> Result<Connectivity, CliError> {
    match text(value)?.as_str() {
        "offline" => Ok(Connectivity::Offline),
        "online" => Ok(Connectivity::Online),
        _ => Err(CliError::InvalidRequest),
    }
}

fn no_more(mut arguments: impl Iterator<Item = OsString>) -> Result<(), CliError> {
    if arguments.next().is_none() {
        Ok(())
    } else {
        Err(CliError::InvalidRequest)
    }
}

const fn map_sync_error(error: &SyncError) -> CliError {
    match error {
        SyncError::InvalidRequest => CliError::InvalidRequest,
        SyncError::Offline | SyncError::InvalidState => CliError::StateRejected,
        SyncError::RemoteUnavailable => CliError::RemoteUnavailable,
        SyncError::RemoteRejected => CliError::RemoteRejected,
        SyncError::Conflict => CliError::RemoteConflict,
        SyncError::InvalidResponse => CliError::RemoteInvalid,
    }
}

#[derive(Debug)]
struct HostAdapterRequiredPort;

impl RemoteSyncPort for HostAdapterRequiredPort {
    fn pull(&mut self, _request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }

    fn push(&mut self, _request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }

    fn checkpoint(
        &mut self,
        _request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }
}
