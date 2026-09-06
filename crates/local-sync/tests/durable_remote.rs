use std::error::Error;

use local_sync::{
    CheckpointRequest, Connectivity, DurableMirrorStore, DurableSyncError, LocalMirror,
    MirrorPhase, PullRequest, PushRequest, RemoteCheckpointReceipt, RemoteFailure, RemoteHead,
    RemotePushReceipt, RemoteSnapshot, RemoteSyncPort, StoreError, SyncError,
};
use tempfile::tempdir;

type TestResult = Result<(), Box<dyn Error>>;

#[derive(Debug, Default)]
struct FakePort {
    pull_calls: usize,
    push_calls: usize,
    checkpoint_calls: usize,
    pull_result: Option<Result<RemoteSnapshot, RemoteFailure>>,
    push_result: Option<Result<RemotePushReceipt, RemoteFailure>>,
    checkpoint_result: Option<Result<RemoteCheckpointReceipt, RemoteFailure>>,
}

impl RemoteSyncPort for FakePort {
    fn pull(&mut self, _request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        self.pull_calls += 1;
        self.pull_result
            .take()
            .unwrap_or(Err(RemoteFailure::Unavailable))
    }

    fn push(&mut self, _request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure> {
        self.push_calls += 1;
        self.push_result
            .take()
            .unwrap_or(Err(RemoteFailure::Unavailable))
    }

    fn checkpoint(
        &mut self,
        _request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure> {
        self.checkpoint_calls += 1;
        self.checkpoint_result
            .take()
            .unwrap_or(Err(RemoteFailure::Unavailable))
    }
}

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn head(number: u64, generation: u64) -> Result<RemoteHead, SyncError> {
    RemoteHead::new(Some(format!("rev_{number:08}")), generation)
}

fn mirror(connectivity: Connectivity) -> Result<LocalMirror, SyncError> {
    LocalMirror::new(
        "prj_project01".to_owned(),
        "brn_branch001".to_owned(),
        "mir_mirror001".to_owned(),
        head(1, 1)?,
        digest('a'),
        connectivity,
    )
}

#[test]
fn offline_remote_commands_never_call_the_port_or_append_intent() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let first = store.initialize(&mirror(Connectivity::Offline)?)?;
    let (second, ()) = store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut port = FakePort::default();

    assert_eq!(
        store.push_remote(&mut port, "push-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::Offline))
    );
    assert_eq!(
        store.pull_remote(&mut port),
        Err(DurableSyncError::Sync(SyncError::Offline))
    );
    assert_eq!(
        store.checkpoint_remote(&mut port, "checkpoint-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::Offline))
    );
    assert_eq!(
        (port.pull_calls, port.push_calls, port.checkpoint_calls),
        (0, 0, 0)
    );
    let loaded = store.load()?.ok_or("missing mirror")?;
    assert_eq!(loaded.revision(), &second);
    assert!(
        loaded
            .mirror()
            .snapshot()
            .pending_push_idempotency_key
            .is_none()
    );
    Ok(())
}

#[test]
fn unavailable_push_persists_first_key_and_same_key_recovers_after_reopen() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let first = store.initialize(&mirror(Connectivity::Online)?)?;
    store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;

    let mut unavailable = FakePort::default();
    assert_eq!(
        store.push_remote(&mut unavailable, "push-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::RemoteUnavailable))
    );
    let pending = DurableMirrorStore::open(temporary.path())?
        .load()?
        .ok_or("missing pending mirror")?;
    assert_eq!(pending.revision().sequence(), 3);
    assert_eq!(
        pending
            .mirror()
            .snapshot()
            .pending_push_idempotency_key
            .as_deref(),
        Some("push-key-0001")
    );

    let mut wrong_key = FakePort::default();
    assert_eq!(
        store.push_remote(&mut wrong_key, "push-key-0002".to_owned()),
        Err(DurableSyncError::Sync(SyncError::InvalidState))
    );
    assert_eq!(wrong_key.push_calls, 0);

    let mut recovered = FakePort {
        push_result: Some(Ok(RemotePushReceipt {
            head: head(2, 2)?,
            snapshot_sha256: digest('b'),
        })),
        ..FakePort::default()
    };
    let (revision, outcome) = store.push_remote(&mut recovered, "push-key-0001".to_owned())?;
    assert_eq!(revision.sequence(), 4);
    assert_eq!(outcome.head.generation(), 2);
    let clean = store
        .load()?
        .ok_or("missing clean mirror")?
        .mirror()
        .snapshot();
    assert_eq!(clean.phase, MirrorPhase::Clean);
    assert!(clean.pending_push_idempotency_key.is_none());
    assert_eq!(clean.observed_generation, 2);
    Ok(())
}

#[test]
fn unavailable_checkpoint_persists_key_and_replay_records_receipt() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    store.initialize(&mirror(Connectivity::Online)?)?;
    let mut unavailable = FakePort::default();
    assert_eq!(
        store.checkpoint_remote(&mut unavailable, "checkpoint-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::RemoteUnavailable))
    );
    let pending = store.load()?.ok_or("missing pending mirror")?;
    assert_eq!(pending.revision().sequence(), 2);
    assert_eq!(
        pending
            .mirror()
            .snapshot()
            .pending_checkpoint_idempotency_key
            .as_deref(),
        Some("checkpoint-key-0001")
    );

    let mut wrong_key = FakePort::default();
    assert_eq!(
        store.checkpoint_remote(&mut wrong_key, "checkpoint-key-0002".to_owned()),
        Err(DurableSyncError::Sync(SyncError::InvalidState))
    );
    assert_eq!(wrong_key.checkpoint_calls, 0);

    let mut replay = FakePort {
        checkpoint_result: Some(Ok(RemoteCheckpointReceipt {
            checkpoint_id: "chk_checkpoint01".to_owned(),
            revision_id: "rev_00000001".to_owned(),
            replayed: true,
        })),
        ..FakePort::default()
    };
    let (revision, outcome) =
        store.checkpoint_remote(&mut replay, "checkpoint-key-0001".to_owned())?;
    assert_eq!(revision.sequence(), 3);
    assert!(outcome.replayed);
    let complete = store
        .load()?
        .ok_or("missing complete mirror")?
        .mirror()
        .snapshot();
    assert!(complete.pending_checkpoint_idempotency_key.is_none());
    assert_eq!(
        complete.last_checkpoint_id.as_deref(),
        Some("chk_checkpoint01")
    );
    Ok(())
}

#[test]
fn malformed_receipts_keep_push_and_checkpoint_keys_durable() -> TestResult {
    let push_root = tempdir()?;
    let push_store = DurableMirrorStore::open(push_root.path())?;
    let first = push_store.initialize(&mirror(Connectivity::Online)?)?;
    push_store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut invalid_push = FakePort {
        push_result: Some(Ok(RemotePushReceipt {
            head: head(9, 9)?,
            snapshot_sha256: digest('b'),
        })),
        ..FakePort::default()
    };
    assert_eq!(
        push_store.push_remote(&mut invalid_push, "push-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::InvalidResponse))
    );
    assert_eq!(
        DurableMirrorStore::open(push_root.path())?
            .load()?
            .ok_or("missing invalid push mirror")?
            .mirror()
            .snapshot()
            .pending_push_idempotency_key
            .as_deref(),
        Some("push-key-0001")
    );

    let checkpoint_root = tempdir()?;
    let checkpoint_store = DurableMirrorStore::open(checkpoint_root.path())?;
    checkpoint_store.initialize(&mirror(Connectivity::Online)?)?;
    let mut invalid_checkpoint = FakePort {
        checkpoint_result: Some(Ok(RemoteCheckpointReceipt {
            checkpoint_id: "chk_checkpoint01".to_owned(),
            revision_id: "rev_99999999".to_owned(),
            replayed: false,
        })),
        ..FakePort::default()
    };
    assert_eq!(
        checkpoint_store
            .checkpoint_remote(&mut invalid_checkpoint, "checkpoint-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::InvalidResponse))
    );
    assert_eq!(
        DurableMirrorStore::open(checkpoint_root.path())?
            .load()?
            .ok_or("missing invalid checkpoint mirror")?
            .mirror()
            .snapshot()
            .pending_checkpoint_idempotency_key
            .as_deref(),
        Some("checkpoint-key-0001")
    );
    Ok(())
}

#[test]
fn definitive_rejection_clears_pending_keys_durably() -> TestResult {
    let push_root = tempdir()?;
    let push_store = DurableMirrorStore::open(push_root.path())?;
    let first = push_store.initialize(&mirror(Connectivity::Online)?)?;
    push_store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut rejected_push = FakePort {
        push_result: Some(Err(RemoteFailure::Rejected)),
        ..FakePort::default()
    };
    assert_eq!(
        push_store.push_remote(&mut rejected_push, "push-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::RemoteRejected))
    );
    let rejected_push = push_store.load()?.ok_or("missing rejected push mirror")?;
    assert_eq!(rejected_push.revision().sequence(), 4);
    assert!(
        rejected_push
            .mirror()
            .snapshot()
            .pending_push_idempotency_key
            .is_none()
    );

    let checkpoint_root = tempdir()?;
    let checkpoint_store = DurableMirrorStore::open(checkpoint_root.path())?;
    checkpoint_store.initialize(&mirror(Connectivity::Online)?)?;
    let mut rejected_checkpoint = FakePort {
        checkpoint_result: Some(Err(RemoteFailure::Rejected)),
        ..FakePort::default()
    };
    assert_eq!(
        checkpoint_store
            .checkpoint_remote(&mut rejected_checkpoint, "checkpoint-key-0001".to_owned()),
        Err(DurableSyncError::Sync(SyncError::RemoteRejected))
    );
    let rejected_checkpoint = checkpoint_store
        .load()?
        .ok_or("missing rejected checkpoint mirror")?;
    assert_eq!(rejected_checkpoint.revision().sequence(), 3);
    assert!(
        rejected_checkpoint
            .mirror()
            .snapshot()
            .pending_checkpoint_idempotency_key
            .is_none()
    );
    Ok(())
}

#[test]
fn pull_conflict_is_durably_recorded_without_overwriting_local_work() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let first = store.initialize(&mirror(Connectivity::Online)?)?;
    store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(
        store.pull_remote(&mut port),
        Err(DurableSyncError::Sync(SyncError::Conflict))
    );
    let conflict = store.load()?.ok_or("missing conflict")?;
    assert_eq!(conflict.revision().sequence(), 3);
    let snapshot = conflict.mirror().snapshot();
    assert_eq!(snapshot.phase, MirrorPhase::Conflict);
    assert_eq!(snapshot.snapshot_sha256, digest('b'));
    assert_eq!(snapshot.pending_plan_sha256, Some(digest('c')));
    assert_eq!(snapshot.conflict_generation, Some(2));
    Ok(())
}

#[derive(Debug)]
struct RacingPushPort {
    store: DurableMirrorStore,
    calls: usize,
}

impl RemoteSyncPort for RacingPushPort {
    fn pull(&mut self, _request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }

    fn push(&mut self, request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure> {
        self.calls += 1;
        let loaded = self.store.load().map_err(|_| RemoteFailure::Unavailable)?;
        let loaded = loaded.ok_or(RemoteFailure::Unavailable)?;
        self.store
            .update(loaded.revision(), |mirror| {
                mirror.set_connectivity(Connectivity::Offline);
                Ok(())
            })
            .map_err(|_| RemoteFailure::Unavailable)?;
        Ok(RemotePushReceipt {
            head: RemoteHead::new(Some("rev_00000002".to_owned()), 2)
                .map_err(|_| RemoteFailure::InvalidResponse)?,
            snapshot_sha256: request.snapshot_sha256().to_owned(),
        })
    }

    fn checkpoint(
        &mut self,
        _request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }
}

#[test]
fn concurrent_writer_after_remote_effect_cannot_overwrite_and_leaves_replay_key() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let first = store.initialize(&mirror(Connectivity::Online)?)?;
    store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut racing = RacingPushPort {
        store: store.clone(),
        calls: 0,
    };
    assert_eq!(
        store.push_remote(&mut racing, "push-key-0001".to_owned()),
        Err(DurableSyncError::Store(StoreError::Conflict))
    );
    assert_eq!(racing.calls, 1);
    let recovered = store.load()?.ok_or("missing raced mirror")?;
    assert_eq!(recovered.revision().sequence(), 4);
    let snapshot = recovered.mirror().snapshot();
    assert_eq!(snapshot.connectivity, Connectivity::Offline);
    assert_eq!(
        snapshot.pending_push_idempotency_key.as_deref(),
        Some("push-key-0001")
    );
    assert_eq!(snapshot.phase, MirrorPhase::Ahead);
    Ok(())
}
