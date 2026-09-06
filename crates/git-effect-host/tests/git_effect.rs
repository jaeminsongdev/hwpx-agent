use std::collections::BTreeSet;
use std::error::Error;
use std::ffi::OsStr;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

use approval_policy::{
    ApprovalError, ApprovalEvaluator, ApprovalPolicy, ApprovalScope, ConfirmationAuthority,
    DurableReplayLedger, EffectKind,
};
use git_effect_host::{GitCommitEffectInput, GitEffectError, GitEffectHost};
use sha2::{Digest as _, Sha256};
use tempfile::TempDir;

type TestResult<T = ()> = Result<T, Box<dyn Error>>;

const SECRET: &[u8] = b"git-effect-host-test-secret-key-0001";
const NOW: u64 = 2_000_000_000;

struct Fixture {
    _temporary: TempDir,
    root: PathBuf,
    git: PathBuf,
    host: GitEffectHost,
    input: GitCommitEffectInput,
    initial_head: String,
}

fn fixture() -> TestResult<Fixture> {
    let temporary = tempfile::tempdir()?;
    let root = temporary.path().join("workspace");
    fs::create_dir_all(root.join("input"))?;
    fs::create_dir(root.join("output"))?;
    let git = find_git()?;
    require_success(run_git(&git, &root, &["init", "-b", "main"])?)?;
    require_success(run_git(
        &git,
        &root,
        &["config", "user.name", "HWPX Agent Test"],
    )?)?;
    require_success(run_git(
        &git,
        &root,
        &["config", "user.email", "hwpx-agent-test@example.invalid"],
    )?)?;
    fs::write(root.join("README.md"), b"fixture\n")?;
    require_success(run_git(&git, &root, &["add", "--", "README.md"])?)?;
    require_success(run_git(
        &git,
        &root,
        &["commit", "--no-gpg-sign", "-m", "initial"],
    )?)?;
    let initial_head = line(&run_git(&git, &root, &["rev-parse", "HEAD"])?)?;
    let output = b"approved synthetic hwpx bytes";
    fs::write(root.join("output/result.hwpx"), output)?;
    let input = GitCommitEffectInput::new(
        "op_commit0001".to_owned(),
        "result.hwpx".to_owned(),
        Sha256::digest(output).into(),
        "Publish approved HWPX".to_owned(),
    )?;
    let host = GitEffectHost::open(&root, &git, 1_048_576, 30)?;
    Ok(Fixture {
        _temporary: temporary,
        root,
        git,
        host,
        input,
        initial_head,
    })
}

fn authorize(
    fixture: &Fixture,
    input: &GitCommitEffectInput,
    token_suffix: &str,
) -> TestResult<approval_policy::AuthorizedEffect> {
    let request =
        fixture
            .host
            .prepare_approval_request(input, digest(b"actor"), digest(b"tenant"), NOW)?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint(
        format!("cnf_gitcommit{token_suffix}"),
        &request,
        true,
        NOW,
        NOW + 60,
    )?;
    let policy = ApprovalPolicy::new([EffectKind::GitCommit], 120, 32)?;
    let ledger = DurableReplayLedger::open(fixture.root.join(".hwpx-agent/approval-tests"))?;
    let mut evaluator = ApprovalEvaluator::with_replay_ledger(policy, SECRET, Box::new(ledger))?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    Ok(evaluator.authorize(&request, &scopes, Some(&token), NOW + 1)?)
}

#[test]
fn approved_commit_is_exact_and_preserves_unrelated_staging() -> TestResult {
    let fixture = fixture()?;
    let hook = fixture.root.join(".git/hooks/reference-transaction");
    fs::write(
        &hook,
        b"#!/bin/sh\nprintf invoked > ../hook-invoked\nexit 1\n",
    )?;
    make_executable(&hook)?;
    fs::write(fixture.root.join("notes.txt"), b"keep staged\n")?;
    require_success(run_git(
        &fixture.git,
        &fixture.root,
        &["add", "--", "notes.txt"],
    )?)?;
    let authorization = authorize(&fixture, &fixture.input, "0001")?;
    let receipt = fixture
        .host
        .execute_git_commit(&fixture.input, authorization, NOW + 2)?;
    assert_ne!(receipt.commit_oid, fixture.initial_head);
    assert_eq!(receipt.previous_head, fixture.initial_head);
    assert_eq!(
        receipt.updated_reference.as_deref(),
        Some("refs/heads/main")
    );
    assert!(receipt.index_synchronized);
    assert_eq!(
        run_git_bytes(
            &fixture.git,
            &fixture.root,
            &["show", "HEAD:output/result.hwpx"]
        )?,
        b"approved synthetic hwpx bytes"
    );
    let parent = line(&run_git(
        &fixture.git,
        &fixture.root,
        &["rev-parse", "HEAD^"],
    )?)?;
    assert_eq!(parent, fixture.initial_head);
    let staged = line(&run_git(
        &fixture.git,
        &fixture.root,
        &["diff", "--cached", "--name-only"],
    )?)?;
    assert_eq!(staged, "notes.txt");
    let target_status = run_git(
        &fixture.git,
        &fixture.root,
        &["status", "--porcelain", "--", "output/result.hwpx"],
    )?;
    assert!(target_status.status.success());
    assert!(target_status.stdout.is_empty());
    assert!(!fixture.root.join(".git/hook-invoked").exists());
    let debug = format!("{:?} {:?}", fixture.host, receipt);
    assert!(!debug.contains(fixture.root.to_string_lossy().as_ref()));
    assert!(!debug.contains("Publish approved HWPX"));
    assert!(!debug.contains("git-effect-host-test-secret"));
    Ok(())
}

#[test]
fn default_deny_never_produces_executable_authorization() -> TestResult {
    let fixture = fixture()?;
    let request = fixture.host.prepare_approval_request(
        &fixture.input,
        digest(b"actor"),
        digest(b"tenant"),
        NOW,
    )?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint(
        "cnf_gitcommit0001".to_owned(),
        &request,
        true,
        NOW,
        NOW + 60,
    )?;
    let mut evaluator = ApprovalEvaluator::new(ApprovalPolicy::deny_all()?, SECRET)?;
    assert_eq!(
        evaluator.authorize(
            &request,
            &BTreeSet::from([ApprovalScope::WorkstationControl]),
            Some(&token),
            NOW + 1,
        ),
        Err(ApprovalError::DeniedByPolicy)
    );
    assert_eq!(
        line(&run_git(
            &fixture.git,
            &fixture.root,
            &["rev-parse", "HEAD"]
        )?)?,
        fixture.initial_head
    );
    Ok(())
}

#[test]
fn stale_or_drifted_authorization_fails_before_git_mutation() -> TestResult {
    let stale = fixture()?;
    let authorization = authorize(&stale, &stale.input, "0001")?;
    assert_eq!(
        stale
            .host
            .execute_git_commit(&stale.input, authorization, NOW + 40),
        Err(GitEffectError::AuthorizationStale)
    );
    assert_eq!(
        line(&run_git(&stale.git, &stale.root, &["rev-parse", "HEAD"])?)?,
        stale.initial_head
    );

    let drifted = fixture()?;
    let authorization = authorize(&drifted, &drifted.input, "0002")?;
    fs::write(drifted.root.join("output/result.hwpx"), b"drifted")?;
    assert_eq!(
        drifted
            .host
            .execute_git_commit(&drifted.input, authorization, NOW + 2),
        Err(GitEffectError::WorkflowRejected)
    );
    assert_eq!(
        line(&run_git(
            &drifted.git,
            &drifted.root,
            &["rev-parse", "HEAD"]
        )?)?,
        drifted.initial_head
    );
    Ok(())
}

#[test]
fn authorization_for_another_exact_plan_is_rejected() -> TestResult {
    let fixture = fixture()?;
    let other = GitCommitEffectInput::new(
        "op_commit0002".to_owned(),
        "result.hwpx".to_owned(),
        Sha256::digest(b"approved synthetic hwpx bytes").into(),
        "Different message".to_owned(),
    )?;
    let authorization = authorize(&fixture, &other, "0002")?;
    assert_eq!(
        fixture
            .host
            .execute_git_commit(&fixture.input, authorization, NOW + 2),
        Err(GitEffectError::AuthorizationRejected)
    );
    assert_eq!(
        line(&run_git(
            &fixture.git,
            &fixture.root,
            &["rev-parse", "HEAD"]
        )?)?,
        fixture.initial_head
    );
    Ok(())
}

#[test]
fn staged_target_is_rejected_without_discarding_the_stage() -> TestResult {
    let fixture = fixture()?;
    require_success(run_git(
        &fixture.git,
        &fixture.root,
        &["add", "--", "output/result.hwpx"],
    )?)?;
    let authorization = authorize(&fixture, &fixture.input, "0001")?;
    assert_eq!(
        fixture
            .host
            .execute_git_commit(&fixture.input, authorization, NOW + 2),
        Err(GitEffectError::GitStateRejected)
    );
    let staged = line(&run_git(
        &fixture.git,
        &fixture.root,
        &["diff", "--cached", "--name-only"],
    )?)?;
    assert_eq!(staged, "output/result.hwpx");
    assert_eq!(
        line(&run_git(
            &fixture.git,
            &fixture.root,
            &["rev-parse", "HEAD"]
        )?)?,
        fixture.initial_head
    );
    Ok(())
}

#[test]
fn detached_head_is_updated_without_moving_the_original_branch() -> TestResult {
    let fixture = fixture()?;
    require_success(run_git(
        &fixture.git,
        &fixture.root,
        &["checkout", "--detach", "--quiet"],
    )?)?;
    let main_before = line(&run_git(
        &fixture.git,
        &fixture.root,
        &["rev-parse", "refs/heads/main"],
    )?)?;
    let authorization = authorize(&fixture, &fixture.input, "0001")?;
    let receipt = fixture
        .host
        .execute_git_commit(&fixture.input, authorization, NOW + 2)?;
    assert_eq!(receipt.updated_reference, None);
    assert_eq!(
        line(&run_git(
            &fixture.git,
            &fixture.root,
            &["rev-parse", "refs/heads/main"]
        )?)?,
        main_before
    );
    assert_eq!(
        line(&run_git(
            &fixture.git,
            &fixture.root,
            &["rev-parse", "HEAD"]
        )?)?,
        receipt.commit_oid
    );
    Ok(())
}

fn find_git() -> TestResult<PathBuf> {
    let executable = if cfg!(windows) { "git.exe" } else { "git" };
    let path = std::env::var_os("PATH").ok_or("PATH missing")?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(executable);
        if fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            return Ok(candidate.canonicalize()?);
        }
    }
    Err("Git executable not found".into())
}

fn run_git(git: &Path, root: &Path, arguments: &[&str]) -> TestResult<Output> {
    Ok(Command::new(git)
        .arg("-C")
        .arg(root)
        .args(arguments)
        .output()?)
}

fn run_git_bytes(git: &Path, root: &Path, arguments: &[&str]) -> TestResult<Vec<u8>> {
    let output = run_git(git, root, arguments)?;
    require_success(output).map_err(Into::into)
}

fn require_success(output: Output) -> Result<Vec<u8>, String> {
    if output.status.success() {
        Ok(output.stdout)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).into_owned())
    }
}

fn line(output: &Output) -> TestResult<String> {
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).into_owned().into());
    }
    let value = std::str::from_utf8(&output.stdout)?;
    Ok(value.trim_end_matches(['\r', '\n']).to_owned())
}

fn digest(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}

#[cfg(unix)]
fn make_executable(path: &Path) -> TestResult {
    use std::os::unix::fs::PermissionsExt as _;

    let mut permissions = fs::metadata(path)?.permissions();
    permissions.set_mode(0o700);
    fs::set_permissions(path, permissions)?;
    Ok(())
}

#[cfg(windows)]
#[allow(clippy::unnecessary_wraps)]
fn make_executable(_path: &Path) -> TestResult {
    Ok(())
}

#[test]
fn malformed_inputs_and_debug_output_are_bounded() -> TestResult {
    let fixture = fixture()?;
    assert!(
        GitCommitEffectInput::new(
            "shell command".to_owned(),
            "result.hwpx".to_owned(),
            [1; 32],
            "message".to_owned(),
        )
        .is_err()
    );
    assert!(GitEffectHost::open(&fixture.root, Path::new("git"), 1_048_576, 30).is_err());
    let debug = format!("{:?}", fixture.host);
    assert!(!debug.contains(fixture.root.to_string_lossy().as_ref()));
    assert!(!debug.contains(fixture.git.to_string_lossy().as_ref()));
    assert!(GitEffectError::AuthorizationRejected.to_string().len() < 128);
    assert!(!OsStr::new(&debug).is_empty());
    Ok(())
}
