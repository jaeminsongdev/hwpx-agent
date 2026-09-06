use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

use approval_policy::ConfirmationAuthority;
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use git_effect_host::{GitCommitEffectInput, GitEffectHost};
use local_companion_daemon::{
    APPROVAL_SECRET_ENV, APPROVAL_STATE_ROOT_ENV, ApprovalRuntime, CONFIG_VERSION,
    EFFECT_PROTOCOL_VERSION, GIT_PROGRAM_ENV, PROTOCOL_VERSION, TARGET_PROFILE,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};

const TOKEN: &str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
const APPROVAL_SECRET: &[u8] = b"daemon-binary-approval-secret-key-0001";

#[test]
fn binary_serves_one_authenticated_health_request_and_exits_on_eof() {
    let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let workspace = temporary.path().join("workspace");
    fs::create_dir_all(workspace.join("output"))
        .unwrap_or_else(|error| panic!("workspace: {error}"));
    let config_path = temporary.path().join("config.json");
    let config = json!({
        "schema_version": CONFIG_VERSION,
        "target_profile": TARGET_PROFILE,
        "automation_mode": "disabled",
        "network_mode": "disabled",
        "max_file_bytes": 1_048_576,
        "workspaces": [{"id": "primary", "root": workspace}],
    });
    fs::write(&config_path, config.to_string()).unwrap_or_else(|error| panic!("config: {error}"));

    let mut child = Command::new(env!("CARGO_BIN_EXE_local-companion-daemon"))
        .args(["--config"])
        .arg(&config_path)
        .env("HWPX_AGENT_LOCAL_SESSION_TOKEN", TOKEN)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap_or_else(|error| panic!("spawn: {error}"));
    let request = json!({
        "protocol_version": PROTOCOL_VERSION,
        "request_id": "smoke-01",
        "session_token": TOKEN,
        "method": "health",
        "params": {},
    });
    let mut stdin = child
        .stdin
        .take()
        .unwrap_or_else(|| panic!("child stdin missing"));
    writeln!(stdin, "{request}").unwrap_or_else(|error| panic!("write: {error}"));
    drop(stdin);
    let output = child
        .wait_with_output()
        .unwrap_or_else(|error| panic!("wait: {error}"));
    assert!(output.status.success());
    assert!(output.stderr.is_empty());
    let response: Value =
        serde_json::from_slice(&output.stdout).unwrap_or_else(|error| panic!("response: {error}"));
    assert_eq!(response["ok"], true);
    assert_eq!(response["request_id"], "smoke-01");
    assert_eq!(response["result"]["status"], "ready");
    let text = String::from_utf8_lossy(&output.stdout);
    assert!(!text.contains(TOKEN));
    assert!(!text.contains(&temporary.path().to_string_lossy().to_string()));
}

#[test]
#[allow(
    clippy::too_many_lines,
    reason = "keeps one complete process-boundary approval scenario readable"
)]
fn binary_executes_one_exact_confirmed_git_commit_and_rejects_reuse() {
    let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let workspace = temporary.path().join("workspace");
    fs::create_dir_all(workspace.join("input")).unwrap_or_else(|error| panic!("input: {error}"));
    fs::create_dir(workspace.join("output")).unwrap_or_else(|error| panic!("output: {error}"));
    let git = find_git().unwrap_or_else(|error| panic!("git: {error}"));
    run_git(&git, &workspace, &["init", "-b", "main"]);
    run_git(
        &git,
        &workspace,
        &["config", "user.name", "HWPX Agent Test"],
    );
    run_git(
        &git,
        &workspace,
        &["config", "user.email", "hwpx-agent-test@example.invalid"],
    );
    fs::write(workspace.join("README.md"), b"fixture\n")
        .unwrap_or_else(|error| panic!("readme: {error}"));
    run_git(&git, &workspace, &["add", "--", "README.md"]);
    run_git(
        &git,
        &workspace,
        &["commit", "--no-gpg-sign", "-m", "initial"],
    );
    let initial_head = git_line(&git, &workspace, &["rev-parse", "HEAD"]);
    let output = b"daemon-approved synthetic hwpx";
    fs::write(workspace.join("output/result-01.hwpx"), output)
        .unwrap_or_else(|error| panic!("result: {error}"));

    let config_path = temporary.path().join("config.json");
    let config = json!({
        "schema_version": CONFIG_VERSION,
        "target_profile": TARGET_PROFILE,
        "automation_mode": "disabled",
        "network_mode": "disabled",
        "max_file_bytes": 1_048_576,
        "workspaces": [{"id": "primary", "root": workspace}],
    });
    fs::write(&config_path, config.to_string()).unwrap_or_else(|error| panic!("config: {error}"));
    let daemon_config = local_companion_daemon::LocalCompanionConfig::load(&config_path)
        .unwrap_or_else(|error| panic!("daemon config: {error}"));
    let host = GitEffectHost::open(&workspace, &git, 1_048_576, 30)
        .unwrap_or_else(|error| panic!("host: {error}"));
    let effect = GitCommitEffectInput::new(
        "op_binarycommit01".to_owned(),
        "result-01.hwpx".to_owned(),
        Sha256::digest(output).into(),
        "Publish approved HWPX".to_owned(),
    )
    .unwrap_or_else(|error| panic!("effect: {error}"));
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_else(|error| panic!("clock: {error}"))
        .as_secs();
    let actor_sha256 = digest(b"binary actor");
    let tenant_sha256 = digest(b"binary tenant");
    let approval_request = host
        .prepare_approval_request(&effect, actor_sha256.clone(), tenant_sha256.clone(), now)
        .unwrap_or_else(|error| panic!("approval request: {error}"));
    let authority = ConfirmationAuthority::new(APPROVAL_SECRET)
        .unwrap_or_else(|error| panic!("authority: {error}"));
    let confirmation = authority
        .mint(
            "cnf_binarycommit01".to_owned(),
            &approval_request,
            true,
            now,
            now + 60,
        )
        .unwrap_or_else(|error| panic!("confirmation: {error}"));
    let request = json!({
        "protocol_version": EFFECT_PROTOCOL_VERSION,
        "request_id": "effect-01",
        "session_token": TOKEN,
        "method": "execute_git_commit",
        "params": {
            "workspace_id": "primary",
            "operation_id": "op_binarycommit01",
            "output_id": "result-01",
            "expected_sha256": digest(output),
            "message": "Publish approved HWPX",
            "actor_sha256": actor_sha256,
            "tenant_sha256": tenant_sha256,
            "requested_at_unix_seconds": now,
            "confirmation_token": confirmation.encoded(),
        },
    });
    let approval_state = temporary.path().join("approval-state");
    let runtime_probe =
        ApprovalRuntime::new(&daemon_config, &git, &approval_state, APPROVAL_SECRET)
            .unwrap_or_else(|error| panic!("runtime probe: {error}"));
    drop(runtime_probe);
    let mut child = Command::new(env!("CARGO_BIN_EXE_local-companion-daemon"))
        .args(["--config"])
        .arg(&config_path)
        .env("HWPX_AGENT_LOCAL_SESSION_TOKEN", TOKEN)
        .env(GIT_PROGRAM_ENV, &git)
        .env(APPROVAL_STATE_ROOT_ENV, &approval_state)
        .env(APPROVAL_SECRET_ENV, URL_SAFE_NO_PAD.encode(APPROVAL_SECRET))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap_or_else(|error| panic!("spawn: {error}"));
    let mut stdin = child
        .stdin
        .take()
        .unwrap_or_else(|| panic!("child stdin missing"));
    writeln!(stdin, "{request}").unwrap_or_else(|error| panic!("first write: {error}"));
    writeln!(stdin, "{request}").unwrap_or_else(|error| panic!("second write: {error}"));
    drop(stdin);
    let process = child
        .wait_with_output()
        .unwrap_or_else(|error| panic!("wait: {error}"));
    assert!(
        process.status.success(),
        "daemon failed: {}",
        String::from_utf8_lossy(&process.stderr)
    );
    assert!(process.stderr.is_empty());
    let responses: Vec<Value> = String::from_utf8(process.stdout)
        .unwrap_or_else(|error| panic!("utf8: {error}"))
        .lines()
        .map(|line| serde_json::from_str(line).unwrap_or_else(|error| panic!("json: {error}")))
        .collect();
    assert_eq!(responses.len(), 2);
    assert_eq!(responses[0]["ok"], true);
    assert_eq!(responses[0]["result"]["executed"], true);
    assert_eq!(responses[0]["result"]["previous_head"], initial_head);
    assert_eq!(responses[0]["result"]["index_synchronized"], true);
    assert_eq!(responses[1]["ok"], false);
    let response_text =
        serde_json::to_string(&responses).unwrap_or_else(|error| panic!("response text: {error}"));
    assert!(!response_text.contains(confirmation.encoded()));
    assert!(!response_text.contains(&URL_SAFE_NO_PAD.encode(APPROVAL_SECRET)));
    assert!(!response_text.contains(workspace.to_string_lossy().as_ref()));
    assert_eq!(
        git_bytes(&git, &workspace, &["show", "HEAD:output/result-01.hwpx"]),
        output
    );
    assert!(approval_state.join("p17-approval-replay-v1").is_dir());
}

fn find_git() -> Result<PathBuf, String> {
    let executable = if cfg!(windows) { "git.exe" } else { "git" };
    let path = std::env::var_os("PATH").ok_or_else(|| "PATH missing".to_owned())?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(executable);
        if fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            return candidate.canonicalize().map_err(|error| error.to_string());
        }
    }
    Err("Git executable not found".to_owned())
}

fn run_git(git: &Path, root: &Path, arguments: &[&str]) {
    let output = Command::new(git)
        .arg("-C")
        .arg(root)
        .args(arguments)
        .output()
        .unwrap_or_else(|error| panic!("git spawn: {error}"));
    assert!(
        output.status.success(),
        "git failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn git_line(git: &Path, root: &Path, arguments: &[&str]) -> String {
    let output = git_bytes(git, root, arguments);
    String::from_utf8(output)
        .unwrap_or_else(|error| panic!("git utf8: {error}"))
        .trim_end_matches(['\r', '\n'])
        .to_owned()
}

fn git_bytes(git: &Path, root: &Path, arguments: &[&str]) -> Vec<u8> {
    let output = Command::new(git)
        .arg("-C")
        .arg(root)
        .args(arguments)
        .output()
        .unwrap_or_else(|error| panic!("git spawn: {error}"));
    assert!(
        output.status.success(),
        "git failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    output.stdout
}

fn digest(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}
