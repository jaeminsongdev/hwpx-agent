use std::error::Error;
use std::fs;
use std::path::Path;
use std::process::{Command, Output};

use local_sync::{
    CheckpointRequest, Connectivity, DurableMirrorStore, LocalMirror, PullRequest, PushRequest,
    RemoteCheckpointReceipt, RemoteFailure, RemoteHead, RemotePushReceipt, RemoteSnapshot,
    RemoteSyncPort,
};
use serde_json::Value;
use tempfile::tempdir;

type TestResult = Result<(), Box<dyn Error>>;

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn run(root: &Path, command: &[&str]) -> Result<Output, std::io::Error> {
    let mut process = Command::new(env!("CARGO_BIN_EXE_local-sync"));
    process.arg(command[0]).arg(root);
    process.args(&command[1..]);
    process.output()
}

fn json(output: &Output) -> Result<Value, Box<dyn Error>> {
    Ok(serde_json::from_slice(&output.stdout)?)
}

#[derive(Debug)]
struct ConflictPort;

impl RemoteSyncPort for ConflictPort {
    fn pull(&mut self, _request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        Ok(RemoteSnapshot {
            head: RemoteHead::new(Some("rev_00000002".to_owned()), 2)
                .map_err(|_| RemoteFailure::InvalidResponse)?,
            snapshot_sha256: digest('d'),
        })
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

fn prepare_conflict(root: &Path) -> Result<DurableMirrorStore, Box<dyn Error>> {
    let mirror = LocalMirror::new(
        "prj_project01".to_owned(),
        "brn_branch001".to_owned(),
        "mir_mirror001".to_owned(),
        RemoteHead::new(Some("rev_00000001".to_owned()), 1)?,
        digest('a'),
        Connectivity::Online,
    )?;
    let store = DurableMirrorStore::open(root)?;
    let first = store.initialize(&mirror)?;
    store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    let mut port = ConflictPort;
    assert!(store.pull_remote(&mut port).is_err());
    Ok(store)
}

#[test]
fn cli_persists_offline_queue_then_online_transition_without_private_output() -> TestResult {
    let temporary = tempdir()?;
    let root_text = temporary.path().display().to_string();
    let initial = run(
        temporary.path(),
        &[
            "init",
            "prj_project01",
            "brn_branch001",
            "mir_mirror001",
            &digest('a'),
            "offline",
            "rev_00000001",
            "1",
        ],
    )?;
    assert!(initial.status.success());
    assert_eq!(json(&initial)?["sequence"], 1);

    let queued = run(temporary.path(), &["queue", &digest('b'), &digest('c')])?;
    assert!(queued.status.success());
    let queued_json = json(&queued)?;
    assert_eq!(queued_json["sequence"], 2);
    assert_eq!(queued_json["connectivity"], "offline");
    assert_eq!(queued_json["phase"], "ahead");
    assert_eq!(queued_json["pending"]["plan"], true);

    let online = run(temporary.path(), &["set-connectivity", "online"])?;
    assert!(online.status.success());
    assert_eq!(json(&online)?["connectivity"], "online");
    let status = run(temporary.path(), &["status"])?;
    assert!(status.status.success());
    assert_eq!(json(&status)?["sequence"], 3);

    for output in [&initial, &queued, &online, &status] {
        let public = String::from_utf8_lossy(&output.stdout);
        assert!(!public.contains("prj_project01"));
        assert!(!public.contains("brn_branch001"));
        assert!(!public.contains("mir_mirror001"));
        assert!(!public.contains(&digest('a')));
        assert!(!public.contains(&root_text));
    }
    Ok(())
}

#[test]
fn status_does_not_create_a_missing_store_and_errors_are_coded() -> TestResult {
    let temporary = tempdir()?;
    let missing = temporary.path().join("missing");
    let output = run(&missing, &["status"])?;
    assert!(!output.status.success());
    assert_eq!(
        String::from_utf8_lossy(&output.stderr),
        "STORE_UNAVAILABLE\n"
    );
    assert!(!missing.exists());

    let invalid = run(temporary.path(), &["not-a-command"])?;
    assert!(!invalid.status.success());
    assert_eq!(
        String::from_utf8_lossy(&invalid.stderr),
        "INVALID_REQUEST\n"
    );
    Ok(())
}

#[test]
fn offline_remote_commands_fail_before_appending_an_intent() -> TestResult {
    let temporary = tempdir()?;
    let initial = run(
        temporary.path(),
        &[
            "init",
            "prj_project01",
            "brn_branch001",
            "mir_mirror001",
            &digest('a'),
            "offline",
            "rev_00000001",
            "1",
        ],
    )?;
    assert!(initial.status.success());
    let queued = run(temporary.path(), &["queue", &digest('b'), &digest('c')])?;
    assert!(queued.status.success());

    let push = run(temporary.path(), &["push", "push-key-0001"])?;
    assert!(!push.status.success());
    assert_eq!(String::from_utf8_lossy(&push.stderr), "STATE_REJECTED\n");
    let pull = run(temporary.path(), &["pull"])?;
    assert!(!pull.status.success());
    assert_eq!(String::from_utf8_lossy(&pull.stderr), "STATE_REJECTED\n");

    let status = run(temporary.path(), &["status"])?;
    assert!(status.status.success());
    let status = json(&status)?;
    assert_eq!(status["sequence"], 2);
    assert_eq!(status["pending"]["uncertain_push"], false);
    assert_eq!(status["pending"]["uncertain_checkpoint"], false);
    Ok(())
}

#[test]
fn unavailable_host_adapter_leaves_exact_push_key_for_replay() -> TestResult {
    let temporary = tempdir()?;
    assert!(
        run(
            temporary.path(),
            &[
                "init",
                "prj_project01",
                "brn_branch001",
                "mir_mirror001",
                &digest('a'),
                "online",
                "rev_00000001",
                "1",
            ],
        )?
        .status
        .success()
    );
    assert!(
        run(temporary.path(), &["queue", &digest('b'), &digest('c')])?
            .status
            .success()
    );

    let first = run(temporary.path(), &["push", "push-key-0001"])?;
    assert!(!first.status.success());
    assert_eq!(
        String::from_utf8_lossy(&first.stderr),
        "REMOTE_UNAVAILABLE\n"
    );
    let status = json(&run(temporary.path(), &["status"])?)?;
    assert_eq!(status["sequence"], 3);
    assert_eq!(status["pending"]["uncertain_push"], true);

    let wrong_key = run(temporary.path(), &["push", "push-key-0002"])?;
    assert!(!wrong_key.status.success());
    assert_eq!(
        String::from_utf8_lossy(&wrong_key.stderr),
        "STATE_REJECTED\n"
    );
    assert_eq!(json(&run(temporary.path(), &["status"])?)?["sequence"], 3);
    Ok(())
}

#[test]
fn unavailable_host_adapter_leaves_exact_checkpoint_key_for_replay() -> TestResult {
    let temporary = tempdir()?;
    assert!(
        run(
            temporary.path(),
            &[
                "init",
                "prj_project01",
                "brn_branch001",
                "mir_mirror001",
                &digest('a'),
                "online",
                "rev_00000001",
                "1",
            ],
        )?
        .status
        .success()
    );

    let missing_label = run(temporary.path(), &["checkpoint", "checkpoint-key-0001"])?;
    assert!(!missing_label.status.success());
    assert_eq!(
        String::from_utf8_lossy(&missing_label.stderr),
        "INVALID_REQUEST\n"
    );
    assert_eq!(json(&run(temporary.path(), &["status"])?)?["sequence"], 1);

    let first = run(
        temporary.path(),
        &[
            "checkpoint",
            "checkpoint-key-0001",
            "Milestone 1",
            "Operator note",
        ],
    )?;
    assert!(!first.status.success());
    assert_eq!(
        String::from_utf8_lossy(&first.stderr),
        "REMOTE_UNAVAILABLE\n"
    );
    let status = json(&run(temporary.path(), &["status"])?)?;
    assert_eq!(status["sequence"], 2);
    assert_eq!(status["pending"]["uncertain_checkpoint"], true);

    for entry in fs::read_dir(temporary.path().join("p17-local-sync-journal-v1"))? {
        let persisted = fs::read_to_string(entry?.path())?;
        assert!(!persisted.contains("Milestone 1"));
        assert!(!persisted.contains("Operator note"));
    }
    assert!(!String::from_utf8_lossy(&first.stdout).contains("Milestone 1"));
    assert!(!String::from_utf8_lossy(&first.stderr).contains("Operator note"));

    let wrong_key = run(
        temporary.path(),
        &[
            "checkpoint",
            "checkpoint-key-0002",
            "Milestone 1",
            "Operator note",
        ],
    )?;
    assert!(!wrong_key.status.success());
    assert_eq!(
        String::from_utf8_lossy(&wrong_key.stderr),
        "STATE_REJECTED\n"
    );
    assert_eq!(json(&run(temporary.path(), &["status"])?)?["sequence"], 2);

    let changed_label = run(
        temporary.path(),
        &[
            "checkpoint",
            "checkpoint-key-0001",
            "Milestone 2",
            "Operator note",
        ],
    )?;
    assert!(!changed_label.status.success());
    assert_eq!(
        String::from_utf8_lossy(&changed_label.stderr),
        "STATE_REJECTED\n"
    );
    assert_eq!(json(&run(temporary.path(), &["status"])?)?["sequence"], 2);
    Ok(())
}

#[test]
fn stale_head_surface_and_rebase_command_are_bounded_and_durable() -> TestResult {
    let temporary = tempdir()?;
    let store = prepare_conflict(temporary.path())?;
    let status = run(temporary.path(), &["status"])?;
    assert!(status.status.success());
    let status_json = json(&status)?;
    assert_eq!(
        status_json["schema_version"],
        "hwpx-agent.local-sync-cli-output/v2"
    );
    assert_eq!(status_json["sequence"], 3);
    assert_eq!(status_json["phase"], "conflict");
    assert_eq!(status_json["stale_head"]["active"], true);
    assert_eq!(status_json["stale_head"]["current_generation"], 2);
    assert_eq!(status_json["stale_head"]["delta"], 1);
    assert_eq!(
        status_json["stale_head"]["allowed_resolutions"],
        serde_json::json!(["rebase_operation_plan", "branch", "manual_merge"])
    );
    assert!(status_json["last_resolution"].is_null());

    let wrong = run(
        temporary.path(),
        &[
            "resolve-rebase",
            "rev_00000003",
            "3",
            &digest('d'),
            &digest('e'),
            &digest('f'),
        ],
    )?;
    assert!(!wrong.status.success());
    assert_eq!(String::from_utf8_lossy(&wrong.stderr), "STATE_REJECTED\n");
    assert_eq!(
        store
            .load()?
            .ok_or("missing conflict")?
            .revision()
            .sequence(),
        3
    );

    let resolved = run(
        temporary.path(),
        &[
            "resolve-rebase",
            "rev_00000002",
            "2",
            &digest('d'),
            &digest('e'),
            &digest('f'),
        ],
    )?;
    assert!(resolved.status.success());
    let resolved_json = json(&resolved)?;
    assert_eq!(resolved_json["sequence"], 4);
    assert_eq!(resolved_json["phase"], "ahead");
    assert_eq!(resolved_json["last_resolution"], "rebase_operation_plan");
    assert_eq!(resolved_json["stale_head"]["active"], false);
    assert_eq!(
        resolved_json["stale_head"]["allowed_resolutions"],
        serde_json::json!([])
    );
    let public = String::from_utf8_lossy(&resolved.stdout);
    for private in [
        temporary.path().display().to_string(),
        "rev_00000002".to_owned(),
        digest('d'),
        digest('e'),
        digest('f'),
    ] {
        assert!(!public.contains(&private));
    }
    Ok(())
}

#[test]
fn branch_and_manual_resolution_commands_preserve_exact_local_work() -> TestResult {
    let branch_root = tempdir()?;
    let branch_store = prepare_conflict(branch_root.path())?;
    let branch = run(
        branch_root.path(),
        &[
            "resolve-branch",
            "brn_branch002",
            "rev_00000001",
            "1",
            &digest('a'),
        ],
    )?;
    assert!(branch.status.success());
    let branch_json = json(&branch)?;
    assert_eq!(branch_json["phase"], "ahead");
    assert_eq!(branch_json["last_resolution"], "branch");
    let branch_snapshot = branch_store
        .load()?
        .ok_or("missing branch resolution")?
        .mirror()
        .snapshot();
    assert_eq!(branch_snapshot.branch_id, "brn_branch002");
    assert_eq!(branch_snapshot.snapshot_sha256, digest('b'));
    assert_eq!(branch_snapshot.pending_plan_sha256, Some(digest('c')));

    let manual_root = tempdir()?;
    let manual_store = prepare_conflict(manual_root.path())?;
    let manual = run(
        manual_root.path(),
        &[
            "resolve-manual",
            "rev_00000002",
            "2",
            &digest('d'),
            &digest('e'),
            &digest('f'),
        ],
    )?;
    assert!(manual.status.success());
    let manual_json = json(&manual)?;
    assert_eq!(manual_json["phase"], "ahead");
    assert_eq!(manual_json["last_resolution"], "manual_merge");
    let manual_snapshot = manual_store
        .load()?
        .ok_or("missing manual resolution")?
        .mirror()
        .snapshot();
    assert_eq!(manual_snapshot.observed_generation, 2);
    assert_eq!(manual_snapshot.snapshot_sha256, digest('e'));
    assert_eq!(manual_snapshot.pending_plan_sha256, Some(digest('f')));

    for output in [&branch, &manual] {
        let public = String::from_utf8_lossy(&output.stdout);
        assert!(!public.contains("brn_branch002"));
        assert!(!public.contains("rev_00000002"));
        assert!(!public.contains(&digest('e')));
    }
    Ok(())
}
