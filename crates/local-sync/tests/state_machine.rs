use std::error::Error;

use local_sync::{
    CheckpointRequest, ConflictResolution, Connectivity, LocalMirror, MirrorPhase, PullOutcome,
    PullRequest, PushRequest, RemoteCheckpointReceipt, RemoteFailure, RemoteHead,
    RemotePushReceipt, RemoteSnapshot, RemoteSyncPort, SyncError,
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
        mirror.checkpoint(
            &mut port,
            "checkpoint-key-01".to_owned(),
            "Milestone 1".to_owned(),
            None,
        ),
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
    let checkpoint = mirror.checkpoint(
        &mut port,
        "checkpoint-key-01".to_owned(),
        "Milestone 1".to_owned(),
        Some("Operator note".to_owned()),
    )?;
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
fn conflict_rebase_requires_exact_remote_head_and_rebased_pair() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(mirror.pull(&mut port), Err(SyncError::Conflict));
    let conflict = mirror.snapshot();

    assert_eq!(
        mirror.resolve_rebase(
            RemoteSnapshot {
                head: head(3, 3)?,
                snapshot_sha256: digest('d'),
            },
            Some((digest('e'), digest('f'))),
        ),
        Err(SyncError::InvalidResponse)
    );
    assert_eq!(mirror.snapshot(), conflict);
    assert_eq!(
        mirror.resolve_rebase(
            RemoteSnapshot {
                head: head(2, 2)?,
                snapshot_sha256: digest('d'),
            },
            None,
        ),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(mirror.snapshot(), conflict);

    mirror.resolve_rebase(
        RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        },
        Some((digest('e'), digest('f'))),
    )?;
    let resolved = mirror.snapshot();
    assert_eq!(resolved.phase, MirrorPhase::Ahead);
    assert_eq!(resolved.observed_generation, 2);
    assert_eq!(resolved.observed_snapshot_sha256, Some(digest('d')));
    assert_eq!(resolved.snapshot_sha256, digest('e'));
    assert_eq!(resolved.pending_plan_sha256, Some(digest('f')));
    assert!(resolved.conflict_generation.is_none());
    assert_eq!(
        resolved.last_conflict_resolution,
        Some(ConflictResolution::RebaseOperationPlan)
    );

    let mut push = FakePort {
        push_result: Some(Ok(RemotePushReceipt {
            head: head(3, 3)?,
            snapshot_sha256: digest('e'),
        })),
        ..FakePort::default()
    };
    mirror.push(&mut push, "push-key-01".to_owned())?;
    assert_eq!(mirror.phase(), MirrorPhase::Clean);
    assert_eq!(
        push.seen_push
            .as_ref()
            .ok_or("missing rebased push")?
            .expected_head()
            .generation(),
        2
    );
    Ok(())
}

#[test]
fn conflict_branch_requires_a_new_branch_at_the_exact_old_base() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(mirror.pull(&mut port), Err(SyncError::Conflict));
    let conflict = mirror.snapshot();
    let old_base = RemoteSnapshot {
        head: head(1, 1)?,
        snapshot_sha256: digest('a'),
    };
    assert_eq!(
        mirror.resolve_branch("brn_branch001".to_owned(), old_base.clone()),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(mirror.snapshot(), conflict);
    assert_eq!(
        mirror.resolve_branch(
            "brn_branch002".to_owned(),
            RemoteSnapshot {
                head: head(2, 2)?,
                snapshot_sha256: digest('d'),
            },
        ),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(mirror.snapshot(), conflict);

    mirror.resolve_branch("brn_branch002".to_owned(), old_base)?;
    let resolved = mirror.snapshot();
    assert_eq!(resolved.branch_id, "brn_branch002");
    assert_eq!(resolved.phase, MirrorPhase::Ahead);
    assert_eq!(resolved.snapshot_sha256, digest('b'));
    assert_eq!(resolved.pending_plan_sha256, Some(digest('c')));
    assert_eq!(
        resolved.last_conflict_resolution,
        Some(ConflictResolution::Branch)
    );
    assert!(resolved.conflict_generation.is_none());
    Ok(())
}

#[test]
fn manual_merge_and_clean_checkpoint_rebase_are_explicit() -> TestResult {
    let mut manual = mirror(Connectivity::Online)?;
    manual.queue_local_change(digest('b'), digest('c'))?;
    let mut pull = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(manual.pull(&mut pull), Err(SyncError::Conflict));
    let unresolved = manual.snapshot();
    assert_eq!(
        manual.resolve_manual_merge(
            RemoteSnapshot {
                head: head(2, 2)?,
                snapshot_sha256: digest('d'),
            },
            "A".repeat(64),
            digest('f'),
        ),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(manual.snapshot(), unresolved);
    manual.resolve_manual_merge(
        RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        },
        digest('e'),
        digest('f'),
    )?;
    let merged = manual.snapshot();
    assert_eq!(merged.phase, MirrorPhase::Ahead);
    assert_eq!(merged.snapshot_sha256, digest('e'));
    assert_eq!(merged.pending_plan_sha256, Some(digest('f')));
    assert_eq!(
        merged.last_conflict_resolution,
        Some(ConflictResolution::ManualMerge)
    );

    let mut checkpoint = mirror(Connectivity::Online)?;
    let mut conflict = FakePort {
        checkpoint_result: Some(Err(RemoteFailure::Conflict(head(2, 2)?))),
        ..FakePort::default()
    };
    assert_eq!(
        checkpoint.checkpoint(
            &mut conflict,
            "checkpoint-key-01".to_owned(),
            "Milestone 1".to_owned(),
            None,
        ),
        Err(SyncError::Conflict)
    );
    let conflicted_checkpoint = checkpoint.snapshot();
    assert!(conflicted_checkpoint.pending_plan_sha256.is_none());
    assert!(
        conflicted_checkpoint
            .pending_checkpoint_idempotency_key
            .is_none()
    );
    assert!(
        conflicted_checkpoint
            .pending_checkpoint_request_sha256
            .is_none()
    );
    checkpoint.resolve_rebase(
        RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        },
        None,
    )?;
    let accepted = checkpoint.snapshot();
    assert_eq!(accepted.phase, MirrorPhase::Clean);
    assert_eq!(accepted.snapshot_sha256, digest('d'));
    assert_eq!(accepted.observed_snapshot_sha256, Some(digest('d')));
    assert_eq!(
        accepted.last_conflict_resolution,
        Some(ConflictResolution::RebaseOperationPlan)
    );
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
fn checkpoint_mismatch_is_rejected_and_retains_the_replay_key() -> TestResult {
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
        mirror.checkpoint(
            &mut port,
            "checkpoint-key-01".to_owned(),
            "Milestone 1".to_owned(),
            None,
        ),
        Err(SyncError::InvalidResponse)
    );
    let after = mirror.snapshot();
    assert_eq!(after.phase, before.phase);
    assert_eq!(after.observed_generation, before.observed_generation);
    assert_eq!(after.snapshot_sha256, before.snapshot_sha256);
    assert_eq!(
        after.pending_checkpoint_idempotency_key.as_deref(),
        Some("checkpoint-key-01")
    );
    assert!(after.pending_checkpoint_request_sha256.is_some());
    assert!(after.last_checkpoint_id.is_none());
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
    let mut queued_mirror = mirror(Connectivity::Online)?;
    assert_eq!(
        queued_mirror.queue_local_change("A".repeat(64), digest('b')),
        Err(SyncError::InvalidRequest)
    );
    queued_mirror.queue_local_change(digest('b'), digest('c'))?;
    let mut port = FakePort::default();
    assert_eq!(
        queued_mirror.push(&mut port, "bad key".to_owned()),
        Err(SyncError::InvalidRequest)
    );
    assert_eq!(port.push_calls, 0);

    for (label, note) in [
        (String::new(), None),
        (" leading".to_owned(), None),
        ("bad\nlabel".to_owned(), None),
        ("가".repeat(121), None),
        ("Milestone 1".to_owned(), Some("가".repeat(1_001))),
    ] {
        let mut checkpoint = mirror(Connectivity::Online)?;
        let mut port = FakePort::default();
        assert_eq!(
            checkpoint.checkpoint(&mut port, "checkpoint-key-01".to_owned(), label, note,),
            Err(SyncError::InvalidRequest)
        );
        assert_eq!(port.checkpoint_calls, 0);
        assert!(
            checkpoint
                .snapshot()
                .pending_checkpoint_request_sha256
                .is_none()
        );
    }

    let mut boundary = mirror(Connectivity::Online)?;
    let mut boundary_port = FakePort::default();
    assert_eq!(
        boundary.checkpoint(
            &mut boundary_port,
            "checkpoint-key-01".to_owned(),
            "가".repeat(120),
            Some("나".repeat(1_000)),
        ),
        Err(SyncError::RemoteUnavailable)
    );
    assert_eq!(boundary_port.checkpoint_calls, 1);
    Ok(())
}

#[test]
fn debug_output_redacts_identifiers_digests_and_keys() -> TestResult {
    let mut queued_mirror = mirror(Connectivity::Online)?;
    queued_mirror.queue_local_change(digest('b'), digest('c'))?;
    let mirror_debug = format!("{queued_mirror:?}");
    assert!(!mirror_debug.contains("prj_project01"));
    assert!(!mirror_debug.contains(&digest('b')));
    let mut port = FakePort::default();
    let _ = queued_mirror.push(&mut port, "private-key-01".to_owned());
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

    let mut checkpoint_mirror = mirror(Connectivity::Online)?;
    let mut checkpoint_port = FakePort::default();
    let _ = checkpoint_mirror.checkpoint(
        &mut checkpoint_port,
        "private-checkpoint-key".to_owned(),
        "Private milestone".to_owned(),
        Some("Private operator note".to_owned()),
    );
    let request_debug = format!(
        "{:?}",
        checkpoint_port
            .seen_checkpoint
            .ok_or("missing checkpoint request")?
    );
    for private in [
        "prj_project01",
        "brn_branch001",
        "mir_mirror001",
        "private-checkpoint-key",
        "Private milestone",
        "Private operator note",
    ] {
        assert!(!request_debug.contains(private));
    }
    Ok(())
}

#[test]
fn durable_snapshot_restore_rejects_impossible_combinations() -> TestResult {
    let original = mirror(Connectivity::Offline)?;
    let snapshot = original.snapshot();
    assert_eq!(LocalMirror::restore(snapshot.clone())?.snapshot(), snapshot);

    let mut legacy_clean = snapshot.clone();
    legacy_clean.schema_version = "hwpx-agent.local-mirror/v1".to_owned();
    legacy_clean.observed_snapshot_sha256 = None;
    let migrated = LocalMirror::restore(legacy_clean)?.snapshot();
    assert_eq!(migrated.schema_version, "hwpx-agent.local-mirror/v5");
    assert_eq!(migrated.observed_snapshot_sha256, Some(digest('a')));

    let mut v2 = snapshot.clone();
    v2.schema_version = "hwpx-agent.local-mirror/v2".to_owned();
    assert_eq!(
        LocalMirror::restore(v2)?.snapshot().schema_version,
        "hwpx-agent.local-mirror/v5"
    );

    let mut v3 = snapshot.clone();
    v3.schema_version = "hwpx-agent.local-mirror/v3".to_owned();
    assert_eq!(
        LocalMirror::restore(v3.clone())?.snapshot().schema_version,
        "hwpx-agent.local-mirror/v5"
    );
    v3.last_conflict_resolution = Some(ConflictResolution::Branch);
    assert!(matches!(
        LocalMirror::restore(v3),
        Err(SyncError::InvalidRequest)
    ));

    let mut v4 = snapshot.clone();
    v4.schema_version = "hwpx-agent.local-mirror/v4".to_owned();
    assert_eq!(
        LocalMirror::restore(v4.clone())?.snapshot().schema_version,
        "hwpx-agent.local-mirror/v5"
    );
    v4.pending_checkpoint_idempotency_key = Some("checkpoint-key-01".to_owned());
    assert!(matches!(
        LocalMirror::restore(v4),
        Err(SyncError::InvalidRequest)
    ));

    let mut dangling_digest = snapshot.clone();
    dangling_digest.pending_checkpoint_request_sha256 = Some(digest('b'));
    assert!(matches!(
        LocalMirror::restore(dangling_digest),
        Err(SyncError::InvalidRequest)
    ));

    let mut malformed_digest = snapshot.clone();
    malformed_digest.pending_checkpoint_idempotency_key = Some("checkpoint-key-01".to_owned());
    malformed_digest.pending_checkpoint_request_sha256 = Some("A".repeat(64));
    assert!(matches!(
        LocalMirror::restore(malformed_digest),
        Err(SyncError::InvalidRequest)
    ));

    let mut impossible = snapshot.clone();
    impossible.phase = MirrorPhase::Ahead;
    assert!(matches!(
        LocalMirror::restore(impossible),
        Err(SyncError::InvalidRequest)
    ));

    let mut stale_conflict = snapshot;
    stale_conflict.phase = MirrorPhase::Conflict;
    stale_conflict.conflict_revision_id = Some("rev_00000009".to_owned());
    stale_conflict.conflict_generation = Some(1);
    assert!(matches!(
        LocalMirror::restore(stale_conflict),
        Err(SyncError::InvalidRequest)
    ));

    let mut unresolved_with_resolution = mirror(Connectivity::Online)?;
    unresolved_with_resolution.queue_local_change(digest('b'), digest('c'))?;
    let mut conflict_port = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(2, 2)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(
        unresolved_with_resolution.pull(&mut conflict_port),
        Err(SyncError::Conflict)
    );
    let mut impossible_resolution = unresolved_with_resolution.snapshot();
    impossible_resolution.last_conflict_resolution = Some(ConflictResolution::ManualMerge);
    assert!(matches!(
        LocalMirror::restore(impossible_resolution),
        Err(SyncError::InvalidRequest)
    ));
    Ok(())
}

#[test]
fn pull_and_conflict_responses_cannot_roll_back_or_alias_the_observed_head() -> TestResult {
    let mut mirror = mirror(Connectivity::Online)?;
    let before = mirror.snapshot();
    let mut rollback = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: RemoteHead::new(None, 0)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(mirror.pull(&mut rollback), Err(SyncError::InvalidResponse));
    assert_eq!(mirror.snapshot(), before);

    let mut aliased_conflict = FakePort {
        pull_result: Some(Err(RemoteFailure::Conflict(head(9, 1)?))),
        ..FakePort::default()
    };
    assert_eq!(
        mirror.pull(&mut aliased_conflict),
        Err(SyncError::InvalidResponse)
    );
    assert_eq!(mirror.snapshot(), before);

    mirror.queue_local_change(digest('b'), digest('c'))?;
    let ahead = mirror.snapshot();
    let mut same_head_wrong_digest = FakePort {
        pull_result: Some(Ok(RemoteSnapshot {
            head: head(1, 1)?,
            snapshot_sha256: digest('d'),
        })),
        ..FakePort::default()
    };
    assert_eq!(
        mirror.pull(&mut same_head_wrong_digest),
        Err(SyncError::InvalidResponse)
    );
    assert_eq!(mirror.snapshot(), ahead);
    Ok(())
}
