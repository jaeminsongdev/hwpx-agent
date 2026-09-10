use std::env;
use std::ffi::OsStr;
use std::io::Write as _;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use remote_sync_host::{
    GitMirrorEffectError, GitMirrorEffectHost, GitMirrorEffectObservation, GitMirrorPushInput,
    GitMirrorPushPlan,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const PROJECT: &str = "prj_00000000000000000000000000000011";
const BRANCH: &str = "brn_00000000000000000000000000000022";
const REVISION_1: &str = "rev_00000000000000000000000000000031";
const REVISION_2: &str = "rev_00000000000000000000000000000032";
const REVISION_3: &str = "rev_00000000000000000000000000000033";

fn digest(byte: char) -> String {
    byte.to_string().repeat(64)
}

fn genesis(revision: &str, snapshot: char, request: char) -> GitMirrorPushInput {
    GitMirrorPushInput::new(
        PROJECT.to_owned(),
        BRANCH.to_owned(),
        None,
        0,
        None,
        revision.to_owned(),
        digest(snapshot),
        digest('c'),
        digest(request),
    )
    .unwrap_or_else(|error| panic!("genesis input: {error}"))
}

fn next(
    expected_revision: &str,
    expected_generation: u64,
    expected_snapshot: char,
    result_revision: &str,
    result_snapshot: char,
    request: char,
) -> GitMirrorPushInput {
    GitMirrorPushInput::new(
        PROJECT.to_owned(),
        BRANCH.to_owned(),
        Some(expected_revision.to_owned()),
        expected_generation,
        Some(digest(expected_snapshot)),
        result_revision.to_owned(),
        digest(result_snapshot),
        digest('d'),
        digest(request),
    )
    .unwrap_or_else(|error| panic!("next input: {error}"))
}

fn fixture() -> Result<(tempfile::TempDir, PathBuf, GitMirrorEffectHost), String> {
    let git = find_git()?;
    let temporary = tempfile::tempdir().map_err(|error| format!("temporary: {error}"))?;
    let repository = temporary.path().join("remote.git");
    let output = Command::new(&git)
        .args(["init", "--bare", "--quiet"])
        .arg(&repository)
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", null_device())
        .output()
        .map_err(|error| format!("git init: {error}"))?;
    if !output.status.success() {
        return Err("git init failed".to_owned());
    }
    let host = GitMirrorEffectHost::open(&repository, &git)
        .map_err(|error| format!("open host: {error}"))?;
    Ok((temporary, git, host))
}

#[test]
fn exact_genesis_and_forward_push_are_deterministic_and_replayable() -> TestResult {
    let (_temporary, _git, host) = fixture()?;
    let first = genesis(REVISION_1, 'a', '1');
    assert!(host.read_branch(PROJECT, BRANCH)?.is_none());
    let first_plan = host.prepare_push(&first)?;
    assert_eq!(first_plan, host.prepare_push(&first)?);
    assert_eq!(first_plan.expected_oid(), None);
    assert_eq!(
        host.observe_push(&first, &first_plan)?,
        GitMirrorEffectObservation::NoEffect
    );

    let receipt = host.execute_push(&first, &first_plan)?;
    assert!(!receipt.replayed);
    assert_eq!(receipt.result_oid, first_plan.result_oid());
    assert_eq!(receipt.state_sha256, first_plan.state_sha256());
    assert_eq!(
        host.observe_push(&first, &first_plan)?,
        GitMirrorEffectObservation::Committed
    );
    assert!(host.execute_push(&first, &first_plan)?.replayed);
    let first_snapshot = host
        .read_branch(PROJECT, BRANCH)?
        .ok_or("first branch snapshot missing")?;
    assert_eq!(first_snapshot.revision_id(), REVISION_1);
    assert_eq!(first_snapshot.generation(), 1);
    assert_eq!(first_snapshot.snapshot_sha256(), digest('a'));
    assert_eq!(first_snapshot.commit_oid(), first_plan.result_oid());
    assert_eq!(first_snapshot.state_sha256(), first_plan.state_sha256());
    assert!(!format!("{first_snapshot:?}").contains(REVISION_1));

    let second = next(REVISION_1, 1, 'a', REVISION_2, 'b', '2');
    let second_plan = host.prepare_push(&second)?;
    assert_eq!(second_plan.expected_oid(), Some(first_plan.result_oid()));
    assert!(!host.execute_push(&second, &second_plan)?.replayed);
    assert_eq!(
        host.observe_push(&second, &second_plan)?,
        GitMirrorEffectObservation::Committed
    );
    let second_snapshot = host
        .read_branch(PROJECT, BRANCH)?
        .ok_or("second branch snapshot missing")?;
    assert_eq!(second_snapshot.revision_id(), REVISION_2);
    assert_eq!(second_snapshot.generation(), 2);
    assert_eq!(second_snapshot.snapshot_sha256(), digest('b'));
    Ok(())
}

#[test]
fn canonical_plan_survives_restart_and_classifies_committed_crash_window() -> TestResult {
    let (temporary, git, host) = fixture()?;
    let input = genesis(REVISION_1, 'a', '1');
    let plan = host.prepare_push(&input)?;
    let encoded = plan.encode()?;
    assert_eq!(GitMirrorPushPlan::decode(&encoded)?, plan);
    host.execute_push(&input, &plan)?;
    drop(host);

    let reopened = GitMirrorEffectHost::open(&temporary.path().join("remote.git"), &git)?;
    let recovered = GitMirrorPushPlan::decode(&encoded)?;
    assert_eq!(
        reopened.observe_push(&input, &recovered)?,
        GitMirrorEffectObservation::Committed
    );
    assert!(reopened.execute_push(&input, &recovered)?.replayed);

    let mut whitespace = encoded.clone();
    whitespace.push(b'\n');
    assert_eq!(
        GitMirrorPushPlan::decode(&whitespace),
        Err(GitMirrorEffectError::PlanRejected)
    );
    let mut extra: serde_json::Value = serde_json::from_slice(&encoded)?;
    extra["unexpected"] = serde_json::Value::Bool(true);
    assert_eq!(
        GitMirrorPushPlan::decode(&serde_json::to_vec(&extra)?),
        Err(GitMirrorEffectError::PlanRejected)
    );
    Ok(())
}

#[test]
fn concurrent_ref_change_is_diverged_and_never_overwritten() -> TestResult {
    let (_temporary, _git, host) = fixture()?;
    let first = genesis(REVISION_1, 'a', '1');
    let first_plan = host.prepare_push(&first)?;
    host.execute_push(&first, &first_plan)?;

    let intended = next(REVISION_1, 1, 'a', REVISION_2, 'b', '2');
    let competing = next(REVISION_1, 1, 'a', REVISION_3, 'e', '3');
    let intended_plan = host.prepare_push(&intended)?;
    let competing_plan = host.prepare_push(&competing)?;
    host.execute_push(&competing, &competing_plan)?;

    assert_eq!(
        host.observe_push(&intended, &intended_plan)?,
        GitMirrorEffectObservation::Diverged
    );
    assert_eq!(
        host.execute_push(&intended, &intended_plan),
        Err(GitMirrorEffectError::ReferenceConflict)
    );
    assert_eq!(
        host.observe_push(&competing, &competing_plan)?,
        GitMirrorEffectObservation::Committed
    );
    Ok(())
}

#[test]
fn plan_request_and_repository_drift_fail_closed_with_redacted_debug() -> TestResult {
    let (temporary, git, host) = fixture()?;
    let first = genesis(REVISION_1, 'a', '1');
    let plan = host.prepare_push(&first)?;
    let different = genesis(REVISION_2, 'b', '2');
    assert_eq!(
        host.observe_push(&different, &plan),
        Err(GitMirrorEffectError::PlanRejected)
    );

    for debug in [
        format!("{host:?}"),
        format!("{first:?}"),
        format!("{plan:?}"),
    ] {
        assert!(!debug.contains(PROJECT));
        assert!(!debug.contains(BRANCH));
        assert!(!debug.contains(&digest('a')));
        assert!(!debug.contains(temporary.path().to_string_lossy().as_ref()));
    }

    let ordinary = temporary.path().join("ordinary");
    let output = Command::new(&git)
        .args(["init", "--quiet"])
        .arg(&ordinary)
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", null_device())
        .output()?;
    assert!(output.status.success());
    assert!(matches!(
        GitMirrorEffectHost::open(&ordinary, &git),
        Err(GitMirrorEffectError::ConfigurationRejected)
    ));
    Ok(())
}

#[test]
fn extra_tree_entry_is_not_accepted_as_a_semantic_branch_snapshot() -> TestResult {
    let (temporary, git, host) = fixture()?;
    let repository = temporary.path().join("remote.git");
    let input = genesis(REVISION_1, 'a', '1');
    let plan = host.prepare_push(&input)?;
    host.execute_push(&input, &plan)?;

    let state_specification = format!("{}:mirror-state.json", plan.result_oid());
    let state_blob = git_line(
        &git,
        &repository,
        &["rev-parse", &state_specification],
        None,
    )?;
    let extra_blob = git_line(
        &git,
        &repository,
        &["hash-object", "-w", "--stdin"],
        Some(b"unexpected\n"),
    )?;
    let tree_input = format!(
        "100644 blob {extra_blob}\textra.txt\n100644 blob {state_blob}\tmirror-state.json\n"
    );
    let tree = git_line(&git, &repository, &["mktree"], Some(tree_input.as_bytes()))?;
    let tampered = git_line(
        &git,
        &repository,
        &["commit-tree", &tree, "-p", plan.result_oid()],
        Some(b"extra tree entry\n"),
    )?;
    let reference = "refs/heads/hwpx-agent/00000000000000000000000000000022";
    let status = Command::new(&git)
        .arg("-C")
        .arg(&repository)
        .args(["update-ref", reference, &tampered, plan.result_oid()])
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", null_device())
        .status()?;
    assert!(status.success());
    assert_eq!(
        host.read_branch(PROJECT, BRANCH),
        Err(GitMirrorEffectError::GitStateRejected)
    );
    Ok(())
}

#[test]
fn invalid_identity_digest_and_empty_head_shapes_are_rejected() {
    let valid = || {
        GitMirrorPushInput::new(
            PROJECT.to_owned(),
            BRANCH.to_owned(),
            None,
            0,
            None,
            REVISION_1.to_owned(),
            digest('a'),
            digest('b'),
            digest('c'),
        )
    };
    assert!(valid().is_ok());
    assert_eq!(
        GitMirrorPushInput::new(
            "project-private".to_owned(),
            BRANCH.to_owned(),
            None,
            0,
            None,
            REVISION_1.to_owned(),
            digest('a'),
            digest('b'),
            digest('c'),
        ),
        Err(GitMirrorEffectError::RequestRejected)
    );
    assert_eq!(
        GitMirrorPushInput::new(
            PROJECT.to_owned(),
            BRANCH.to_owned(),
            Some(REVISION_1.to_owned()),
            0,
            None,
            REVISION_2.to_owned(),
            digest('a'),
            digest('b'),
            digest('c'),
        ),
        Err(GitMirrorEffectError::RequestRejected)
    );
    assert_eq!(
        GitMirrorPushInput::new(
            PROJECT.to_owned(),
            BRANCH.to_owned(),
            None,
            0,
            None,
            REVISION_1.to_owned(),
            "A".repeat(64),
            digest('b'),
            digest('c'),
        ),
        Err(GitMirrorEffectError::RequestRejected)
    );

    let (_temporary, _git, host) = fixture().unwrap_or_else(|error| panic!("fixture: {error}"));
    assert_eq!(
        host.read_branch("project-private", BRANCH),
        Err(GitMirrorEffectError::RequestRejected)
    );
}

fn find_git() -> Result<PathBuf, String> {
    let executable = if cfg!(windows) { "git.exe" } else { "git" };
    let path = env::var_os("PATH").ok_or_else(|| "PATH unavailable".to_owned())?;
    for directory in env::split_paths(&path) {
        let candidate = directory.join(executable);
        if candidate.is_file() {
            return candidate
                .canonicalize()
                .map_err(|error| format!("canonical git: {error}"));
        }
    }
    Err("git executable unavailable".to_owned())
}

fn git_line(
    git: &std::path::Path,
    repository: &std::path::Path,
    arguments: &[&str],
    input: Option<&[u8]>,
) -> Result<String, String> {
    let mut command = Command::new(git);
    command
        .arg("-C")
        .arg(repository)
        .args(arguments.iter().map(OsStr::new))
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", null_device())
        .env("GIT_AUTHOR_NAME", "hwpx-agent mirror")
        .env("GIT_AUTHOR_EMAIL", "mirror@invalid")
        .env("GIT_COMMITTER_NAME", "hwpx-agent mirror")
        .env("GIT_COMMITTER_EMAIL", "mirror@invalid")
        .env("GIT_AUTHOR_DATE", "@1 +0000")
        .env("GIT_COMMITTER_DATE", "@1 +0000")
        .stdin(if input.is_some() {
            Stdio::piped()
        } else {
            Stdio::null()
        })
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    let mut child = command.spawn().map_err(|error| format!("spawn: {error}"))?;
    if let Some(input) = input {
        child
            .stdin
            .take()
            .ok_or_else(|| "stdin missing".to_owned())?
            .write_all(input)
            .map_err(|error| format!("stdin: {error}"))?;
    }
    let output = child
        .wait_with_output()
        .map_err(|error| format!("wait: {error}"))?;
    if !output.status.success() {
        return Err("git command failed".to_owned());
    }
    let raw = std::str::from_utf8(&output.stdout).map_err(|error| format!("utf8: {error}"))?;
    let value = raw
        .strip_suffix("\r\n")
        .or_else(|| raw.strip_suffix('\n'))
        .unwrap_or(raw);
    if value.is_empty() || value.contains('\r') || value.contains('\n') {
        return Err("git line invalid".to_owned());
    }
    Ok(value.to_owned())
}

#[cfg(windows)]
fn null_device() -> &'static str {
    "NUL"
}

#[cfg(not(windows))]
fn null_device() -> &'static str {
    "/dev/null"
}
