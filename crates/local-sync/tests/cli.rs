use std::error::Error;
use std::path::Path;
use std::process::{Command, Output};

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

    let first = run(temporary.path(), &["checkpoint", "checkpoint-key-0001"])?;
    assert!(!first.status.success());
    assert_eq!(
        String::from_utf8_lossy(&first.stderr),
        "REMOTE_UNAVAILABLE\n"
    );
    let status = json(&run(temporary.path(), &["status"])?)?;
    assert_eq!(status["sequence"], 2);
    assert_eq!(status["pending"]["uncertain_checkpoint"], true);

    let wrong_key = run(temporary.path(), &["checkpoint", "checkpoint-key-0002"])?;
    assert!(!wrong_key.status.success());
    assert_eq!(
        String::from_utf8_lossy(&wrong_key.stderr),
        "STATE_REJECTED\n"
    );
    assert_eq!(json(&run(temporary.path(), &["status"])?)?["sequence"], 2);
    Ok(())
}
