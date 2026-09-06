use std::error::Error;

use local_sync::{
    CheckpointRequest, Connectivity, LocalMirror, MirrorPhase, PullOutcome, PullRequest,
    PushRequest, RemoteCheckpointReceipt, RemoteFailure, RemoteHead, RemotePushReceipt,
    RemoteSnapshot, RemoteSyncPort, SyncError,
};

type TestResult = Result<(), Box<dyn Error>>;

#[derive(Debug, Default)]
struct FakePort {
    pull_calls: usize,
    push_calls: usize,
    checkpoint_calls: usize,
    pull_result: Option<Result<RemoteSnapshot, RemoteFailure>>,
    push_result: Option<Result<RemotePushReceipt, RemoteFailure>>,
    checkpoint_result: Option<Result<RemoteCheckpointReceipt, RemoteFailure>>,
    seen_pull: Option<PullRequest>,
    seen_push: Option<PushRequest>,
    seen_checkpoint: Option<CheckpointRequest>,
}

impl RemoteSyncPort for FakePort {
    fn pull(&mut self, request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        self.pull_calls += 1;
        self.seen_pull = Some(request.clone());
        self.pull_result
            .take()
            .unwrap_or(Err(RemoteFailure::Unavailable))
    }

    fn push(&mut self, request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure> {
        self.push_calls += 1;
        self.seen_push = Some(request.clone());
        self.push_result
            .take()
            .unwrap_or(Err(RemoteFailure::Unavailable))
    }
    fn checkpoint(
        &mut self,
        request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure> {
        self.checkpoint_calls += 1;
        self.seen_checkpoint = Some(request.clone());
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
fn offline_work_is_queued_without_port_calls_then_pushes_after_reconnect() -> TestResult {
    let mut mirror = mirror(Connectivity::Offline)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort::default();
    assert_eq!(mirror.pull(&mut port), Err(SyncError::Offline));
    assert_eq!(
        mirror.push(&mut port, "push-key-01".to_owned()),
        Err(SyncError::Offline)
    );
    assert_eq!(
        mirror.checkpoint(&mut port, "checkpoint-key-01".to_owned()),
        Err(SyncError::Offline)
    );
    assert_eq!(
        (port.pull_calls, port.push_calls, port.checkpoint_calls),
        (0, 0, 0)
    );

    mirror.set_connectivity(Connectivity::Online);
    port.push_result = Some(Ok(RemotePushReceipt {
        head: head(2, 2)?,
        snapshot_sha256: digest('b'),
    }));
    let pushed = mirror.push(&mut port, "push-key-01".to_owned())?;
    assert_eq!(pushed.head.generation(), 2);
    assert_eq!(mirror.phase(), MirrorPhase::Clean);
    let seen = port.seen_push.as_ref().ok_or("missing push request")?;
    assert_eq!(seen.expected_head().generation(), 1);
    assert_eq!(seen.snapshot_sha256(), digest('b'));
    assert_eq!(seen.operation_plan_sha256(), digest('c'));

    port.checkpoint_result = Some(Ok(RemoteCheckpointReceipt {
        checkpoint_id: "chk_checkpoint01".to_owned(),
        revision_id: "rev_00000002".to_owned(),
        replayed: false,
    }));
    let checkpoint = mirror.checkpoint(&mut port, "checkpoint-key-01".to_owned())?;
    assert_eq!(checkpoint.checkpoint_id, "chk_checkpoint01");
    assert!(!checkpoint.replayed);
    assert_eq!(
        (port.pull_calls, port.push_calls, port.checkpoint_calls),
        (0, 1, 1)
    );
    Ok(())
}

#[test]
fn clean_online_pull_adopts_a_valid_remote_snapshot() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    let mut port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('b'),
        })),
        ..FakePort::default()
    };
    assert_eq!(mirror.pull(&mut port)?, PullOutcome::Updated);
    let snapshot = mirror.snapshot();
    assert_eq!(
        snapshot.observed_revision_id.as_deref(),
        Some("rev_00000002")
    );
    assert_eq!(snapshot.observed_generation, 2);
    assert_eq!(snapshot.snapshot_sha256, digest('b'));
    assert_eq!(snapshot.phase, MirrorPhase::Clean);
    let seen = port.seen_pull.as_ref().ok_or("missing pull request")?;
    assert_eq!(seen.observed_head().generation(), 1);
    Ok(())
}

#[test]
fn local_ahead_plus_remote_advance_becomes_conflict_without_overwrite() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let before = mirror.snapshot();
    let mut port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(mirror.pull(&mut port), Err(SyncError::Conflict));
    let after = mirror.snapshot();
    assert_eq!(after.phase, MirrorPhase::Conflict);
    assert_eq!(after.snapshot_sha256, before.snapshot_sha256);
    assert_eq!(after.pending_plan_sha256, before.pending_plan_sha256);
    assert_eq!(after.observed_generation, before.observed_generation);
    assert_eq!(after.conflict_generation, Some(2));
    Ok(())
}

#[test]
fn push_conflict_records_remote_head_and_preserves_local_plan() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort {
        push_result: Some(Err(RemoteFailure::Conflict(head(4, 4)?))),
        ..FakePort::default()
    };
    assert_eq!(
        mirror.push(&mut port, "push-key-01".to_owned()),
        Err(SyncError::Conflict)
    );
    let snapshot = mirror.snapshot();
    assert_eq!(snapshot.phase, MirrorPhase::Conflict);
    assert_eq!(snapshot.pending_plan_sha256, Some(digest('c')));
    assert_eq!(snapshot.conflict_generation, Some(4));
    Ok(())
}

#[test]
fn unavailable_and_invalid_responses_never_advance_local_state() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let before = mirror.snapshot();
    let mut unavailable = FakePort::default();
    assert_eq!(
        mirror.push(&mut unavailable, "push-key-01".to_owned()),
        Err(SyncError::RemoteUnavailable)
    );
    let after_unavailable = mirror.snapshot();
    assert_eq!(after_unavailable.phase, before.phase);
    assert_eq!(
        after_unavailable.observed_generation,
        before.observed_generation
    );
    assert_eq!(after_unavailable.snapshot_sha256, before.snapshot_sha256);
    assert_eq!(
        after_unavailable.pending_plan_sha256,
        before.pending_plan_sha256
    );
    assert_eq!(
        after_unavailable.pending_push_idempotency_key.as_deref(),
        Some("push-key-01")
    );
    assert_eq!(
        mirror.push(&mut unavailable, "push-key-02".to_owned()),
        Err(SyncError::InvalidState)
    );
    assert_eq!(unavailable.push_calls, 1);

    let mut invalid = FakePort {
        push_result: Some(Ok(RemotePushReceipt {
            head: head(9, 9)?,
            snapshot_sha256: digest('b'),
        })),
        ..FakePort::default()
    };
    assert_eq!(
        mirror.push(&mut invalid, "push-key-01".to_owned()),
        Err(SyncError::InvalidResponse)
    );
    assert_eq!(mirror.snapshot(), after_unavailable);
    Ok(())
}

#[test]
fn checkpoint_mismatch_is_rejected_without_recording_it() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    let before = mirror.snapshot();
    let mut port = FakePort {
        checkpoint_result: Some(Ok(RemoteCheckpointReceipt {
            checkpoint_id: "chk_checkpoint01".to_owned(),
            revision_id: "rev_99999999".to_owned(),
            replayed: false,
        })),
        ..FakePort::default()
    };
    assert_eq!(
        mirror.checkpoint(&mut port, "checkpoint-key-01".to_owned()),
        Err(SyncError::InvalidResponse)
    );
    assert_eq!(mirror.snapshot(), before);
    Ok(())
}

#[test]
fn malformed_identifiers_digests_and_keys_fail_closed() -> TestResult {
    assert!(
        LocalMirror::new(
            "project".to_owned(),
            "brn_branch001".to_owned(),
            "mir_mirror001".to_owned(),
            head(1, 1)?,
            digest('a'),
            Connectivity::Offline,
        )
        .is_err()
    );
    let mut mirror = mirror(Connectivity::Online)?;
    assert_eq!(
        mirror.queue_local_change("A".repeat(64), digest('b')),
        Err(SyncError::InvalidRequest)
    );
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort::default();
    assert_eq!(
        mirror.push(&mut port, "bad key".to_owned()),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(port.push_calls, 0);
    Ok(())
}

#[test]
fn debug_output_redacts_identifiers_digests_and_keys() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mirror_debug = format!("{mirror:?}");
    assert!(!mirror_debug.contains("prj_project01"));
    assert!(!mirror_debug.contains(&digest('b')));
    let mut port = FakePort::default();
    let _ = mirror.push(&mut port, "private-key-01".to_owned());
    let request_debug = format!("{:?}", port.seen_push.ok_or("missing push")?);
    assert!(!request_debug.contains("private-key-01"));
    assert!(!request_debug.contains("prj_project01"));
    assert!(!request_debug.contains(&digest('b')));

    let checkpoint_receipt = RemoteCheckpointReceipt {
        checkpoint_id: "chk_checkpoint01".to_owned(),
        revision_id: "rev_remote0001".to_owned(),
        replayed: false,
    };
    let checkpoint_debug = format!("{checkpoint_receipt:?}");
    assert!(!checkpoint_debug.contains("chk_checkpoint01"));
    assert!(!checkpoint_debug.contains("rev_remote0001"));
    Ok(())
}
