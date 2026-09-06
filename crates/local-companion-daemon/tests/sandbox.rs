use std::fs;
use std::path::Path;

use local_companion_daemon::{
    APPROVAL_PROTOCOL_VERSION, CONFIG_VERSION, LocalCompanionConfig, LocalCompanionDaemon,
    PROTOCOL_VERSION, SessionToken, TARGET_PROFILE, WORKFLOW_PROTOCOL_VERSION,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use tempfile::TempDir;

const TOKEN: &str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

fn fixture() -> (TempDir, LocalCompanionConfig) {
    let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let workspace = temporary.path().join("workspace");
    fs::create_dir_all(workspace.join("input")).unwrap_or_else(|error| panic!("input: {error}"));
    fs::create_dir_all(workspace.join("output")).unwrap_or_else(|error| panic!("output: {error}"));
    fs::write(workspace.join("input").join("fixture.hwpx"), b"bounded")
        .unwrap_or_else(|error| panic!("fixture: {error}"));
    let config_path = temporary.path().join("config.json");
    write_config(&config_path, &workspace, 128);
    let config =
        LocalCompanionConfig::load(&config_path).unwrap_or_else(|error| panic!("config: {error}"));
    (temporary, config)
}

fn write_config(path: &Path, workspace: &Path, max_file_bytes: u64) {
    let document = json!({
        "schema_version": CONFIG_VERSION,
        "target_profile": TARGET_PROFILE,
        "automation_mode": "disabled",
        "network_mode": "disabled",
        "max_file_bytes": max_file_bytes,
        "workspaces": [{"id": "primary", "root": workspace}],
    });
    fs::write(
        path,
        serde_json::to_vec(&document).unwrap_or_else(|error| panic!("json: {error}")),
    )
    .unwrap_or_else(|error| panic!("config write: {error}"));
}

fn token() -> SessionToken {
    SessionToken::new(TOKEN.to_owned()).unwrap_or_else(|error| panic!("token: {error}"))
}

fn request(method: &str, params: &Value) -> Vec<u8> {
    request_with_protocol(PROTOCOL_VERSION, method, params)
}

fn workflow_request(method: &str, params: &Value) -> Vec<u8> {
    request_with_protocol(WORKFLOW_PROTOCOL_VERSION, method, params)
}

fn approval_request(method: &str, params: &Value) -> Vec<u8> {
    request_with_protocol(APPROVAL_PROTOCOL_VERSION, method, params)
}

fn request_with_protocol(protocol: &str, method: &str, params: &Value) -> Vec<u8> {
    serde_json::to_vec(&json!({
        "protocol_version": protocol,
        "request_id": "request-01",
        "session_token": TOKEN,
        "method": method,
        "params": params,
    }))
    .unwrap_or_else(|error| panic!("request: {error}"))
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

#[test]
fn health_is_bounded_and_redacts_paths_and_token() {
    let (temporary, config) = fixture();
    let daemon = LocalCompanionDaemon::new(config);
    let response = daemon.handle(&request("health", &json!({})), &token());
    assert_eq!(response["ok"], true);
    assert_eq!(response["result"]["status"], "ready");
    assert_eq!(response["result"]["workspace_count"], 1);
    let text = response.to_string();
    assert!(!text.contains(TOKEN));
    assert!(!text.contains(&temporary.path().to_string_lossy().to_string()));
}

#[test]
fn session_and_request_shape_fail_before_any_operation() {
    let (_temporary, config) = fixture();
    let daemon = LocalCompanionDaemon::new(config);
    let mut wrong = request("health", &json!({}));
    let token_offset = wrong
        .windows(TOKEN.len())
        .position(|window| window == TOKEN.as_bytes())
        .unwrap_or_else(|| panic!("token fixture missing"));
    wrong[token_offset] = b'B';
    assert_eq!(daemon.handle(&wrong, &token())["ok"], false);

    let unknown = json!({
        "protocol_version": PROTOCOL_VERSION,
        "request_id": "request-01",
        "session_token": TOKEN,
        "method": "health",
        "params": {},
        "extra": true,
    });
    assert_eq!(
        daemon.handle(unknown.to_string().as_bytes(), &token())["ok"],
        false
    );
    assert_eq!(
        daemon.handle(&request("health", &json!({"extra": true})), &token())["ok"],
        false
    );
}

#[test]
fn existing_file_authorization_is_relative_regular_and_size_bounded() {
    let (_temporary, config) = fixture();
    let daemon = LocalCompanionDaemon::new(config);
    let response = daemon.handle(
        &request(
            "authorize_path",
            &json!({
                "workspace_id": "primary",
                "relative_path": "input/fixture.hwpx",
                "access": "read_existing",
            }),
        ),
        &token(),
    );
    assert_eq!(response["ok"], true);
    assert_eq!(response["result"]["size_bytes"], 7);
    assert!(response.to_string().find("fixture.hwpx").is_none());
}

#[test]
fn traversal_absolute_ads_reserved_and_directory_paths_are_rejected() {
    let (temporary, config) = fixture();
    let daemon = LocalCompanionDaemon::new(config);
    let absolute = temporary
        .path()
        .join("workspace")
        .join("input")
        .join("fixture.hwpx");
    for relative in [
        "../escape.hwpx".to_owned(),
        absolute.to_string_lossy().to_string(),
        "input/fixture.hwpx:stream".to_owned(),
        "input/CON.txt".to_owned(),
        "input".to_owned(),
    ] {
        let response = daemon.handle(
            &request(
                "authorize_path",
                &json!({
                    "workspace_id": "primary",
                    "relative_path": relative,
                    "access": "read_existing",
                }),
            ),
            &token(),
        );
        assert_eq!(response["ok"], false);
    }
}

#[test]
fn output_creation_requires_output_namespace_existing_parent_and_no_overwrite() {
    let (temporary, config) = fixture();
    let daemon = LocalCompanionDaemon::new(config);
    let accepted = daemon.handle(
        &request(
            "authorize_path",
            &json!({
                "workspace_id": "primary",
                "relative_path": "output/new.hwpx",
                "access": "create_output",
            }),
        ),
        &token(),
    );
    assert_eq!(accepted["ok"], true);
    for relative in ["input/new.hwpx", "output/missing/new.hwpx"] {
        let rejected = daemon.handle(
            &request(
                "authorize_path",
                &json!({
                    "workspace_id": "primary",
                    "relative_path": relative,
                    "access": "create_output",
                }),
            ),
            &token(),
        );
        assert_eq!(rejected["ok"], false);
    }
    fs::write(
        temporary.path().join("workspace/output/existing.hwpx"),
        b"existing",
    )
    .unwrap_or_else(|error| panic!("existing: {error}"));
    let overwrite = daemon.handle(
        &request(
            "authorize_path",
            &json!({
                "workspace_id": "primary",
                "relative_path": "output/existing.hwpx",
                "access": "create_output",
            }),
        ),
        &token(),
    );
    assert_eq!(overwrite["ok"], false);
}

#[test]
fn malformed_config_and_duplicate_root_are_rejected() {
    let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let workspace = temporary.path().join("workspace");
    fs::create_dir(&workspace).unwrap_or_else(|error| panic!("workspace: {error}"));
    let config_path = temporary.path().join("config.json");
    let invalid = json!({
        "schema_version": CONFIG_VERSION,
        "target_profile": TARGET_PROFILE,
        "automation_mode": "disabled",
        "network_mode": "disabled",
        "max_file_bytes": 128,
        "workspaces": [
            {"id": "one", "root": workspace},
            {"id": "two", "root": workspace},
        ],
    });
    fs::write(&config_path, invalid.to_string()).unwrap_or_else(|error| panic!("config: {error}"));
    assert!(LocalCompanionConfig::load(&config_path).is_err());
    write_config(&config_path, &workspace, 0);
    assert!(LocalCompanionConfig::load(&config_path).is_err());
}

#[test]
fn workflow_v2_is_path_free_identity_bound_and_preserves_inputs() {
    let (temporary, config) = fixture();
    let workspace = temporary.path().join("workspace");
    let source = b"bounded";
    let candidate = b"candidate";
    fs::write(workspace.join("input/candidate.hwpx"), candidate)
        .unwrap_or_else(|error| panic!("candidate: {error}"));
    fs::create_dir_all(workspace.join(".git/refs/heads"))
        .unwrap_or_else(|error| panic!("git refs: {error}"));
    fs::write(workspace.join(".git/HEAD"), b"ref: refs/heads/main\n")
        .unwrap_or_else(|error| panic!("git head: {error}"));
    fs::write(
        workspace.join(".git/refs/heads/main"),
        format!("{}\n", "a".repeat(40)),
    )
    .unwrap_or_else(|error| panic!("git ref: {error}"));
    let daemon = LocalCompanionDaemon::new(config);

    for (slot, fixture_id, expected) in [
        ("source", "fixture", digest(source)),
        ("candidate", "candidate", digest(candidate)),
    ] {
        let response = daemon.handle(
            &workflow_request(
                "materialize",
                &json!({
                    "workspace_id": "primary",
                    "operation_id": "operation-01",
                    "slot": slot,
                    "fixture_id": fixture_id,
                    "expected_sha256": expected,
                }),
            ),
            &token(),
        );
        assert_eq!(response["protocol_version"], WORKFLOW_PROTOCOL_VERSION);
        assert_eq!(response["ok"], true);
        assert!(response.to_string().find("input/").is_none());
    }

    let difference = daemon.handle(
        &workflow_request(
            "diff",
            &json!({
                "workspace_id": "primary",
                "operation_id": "operation-01",
            }),
        ),
        &token(),
    );
    assert_eq!(difference["ok"], true);
    assert_eq!(difference["result"]["identical"], false);
    assert_eq!(difference["result"]["source"]["size_bytes"], source.len());

    let published = daemon.handle(
        &workflow_request(
            "publish",
            &json!({
                "workspace_id": "primary",
                "operation_id": "operation-01",
                "output_id": "result-01",
                "expected_sha256": digest(candidate),
            }),
        ),
        &token(),
    );
    assert_eq!(published["ok"], true);
    assert_eq!(published["result"]["output_id"], "result-01");
    assert_eq!(
        fs::read(workspace.join("output/result-01.hwpx"))
            .unwrap_or_else(|error| panic!("output: {error}")),
        candidate
    );
    assert_eq!(
        fs::read(workspace.join("input/fixture.hwpx"))
            .unwrap_or_else(|error| panic!("source: {error}")),
        source
    );

    let plan = daemon.handle(
        &workflow_request(
            "prepare_git_commit",
            &json!({
                "workspace_id": "primary",
                "output_id": "result-01",
                "expected_sha256": digest(candidate),
                "message": "Publish verified HWPX",
            }),
        ),
        &token(),
    );
    assert_eq!(plan["ok"], true);
    assert_eq!(plan["result"]["expected_head"], "a".repeat(40));
    assert_eq!(plan["result"]["output_pathspec"], "output/result-01.hwpx");
    assert_eq!(plan["result"]["executed"], false);
    assert!(
        !plan
            .to_string()
            .contains(&workspace.to_string_lossy().to_string())
    );
}

#[test]
fn protocol_versions_and_workflow_negatives_fail_closed() {
    let (temporary, config) = fixture();
    let workspace = temporary.path().join("workspace");
    let large = vec![7_u8; 129];
    fs::write(workspace.join("input/large.hwpx"), &large)
        .unwrap_or_else(|error| panic!("large: {error}"));
    let daemon = LocalCompanionDaemon::new(config);
    let params = json!({
        "workspace_id": "primary",
        "operation_id": "operation-bad",
        "slot": "source",
        "fixture_id": "large",
        "expected_sha256": digest(&large),
    });
    assert_eq!(
        daemon.handle(&request("materialize", &params), &token())["ok"],
        false
    );
    assert_eq!(
        daemon.handle(
            &workflow_request(
                "authorize_path",
                &json!({
                    "workspace_id": "primary",
                    "relative_path": "input/fixture.hwpx",
                    "access": "read_existing",
                }),
            ),
            &token(),
        )["ok"],
        false
    );
    assert_eq!(
        daemon.handle(&workflow_request("materialize", &params), &token())["ok"],
        false
    );
    assert!(
        !workspace
            .join(".hwpx-agent/work/operation-bad/source.hwpx")
            .exists()
    );

    for invalid in [
        json!({ "fixture_id": "../large" }),
        json!({ "expected_sha256": "A".repeat(64) }),
        json!({ "expected_sha256": "0".repeat(64) }),
        json!({ "extra": true }),
    ] {
        let mut value = params.clone();
        let object = value
            .as_object_mut()
            .unwrap_or_else(|| panic!("fixture params must be an object"));
        for (key, replacement) in invalid
            .as_object()
            .unwrap_or_else(|| panic!("invalid fixture must be an object"))
        {
            object.insert(key.clone(), replacement.clone());
        }
        assert_eq!(
            daemon.handle(&workflow_request("materialize", &value), &token())["ok"],
            false
        );
    }
}

#[test]
fn approval_v3_prepares_exact_git_target_and_plan_without_execution() {
    let (temporary, config) = fixture();
    let workspace = temporary.path().join("workspace");
    let output = b"approval-bound output";
    fs::write(workspace.join("output/result-01.hwpx"), output)
        .unwrap_or_else(|error| panic!("output: {error}"));
    fs::create_dir_all(workspace.join(".git/refs/heads"))
        .unwrap_or_else(|error| panic!("git refs: {error}"));
    fs::write(workspace.join(".git/HEAD"), b"ref: refs/heads/main\n")
        .unwrap_or_else(|error| panic!("git head: {error}"));
    fs::write(
        workspace.join(".git/refs/heads/main"),
        format!("{}\n", "d".repeat(40)),
    )
    .unwrap_or_else(|error| panic!("git ref: {error}"));
    let daemon = LocalCompanionDaemon::new(config);
    let params = json!({
        "workspace_id": "primary",
        "operation_id": "operation-approval-01",
        "output_id": "result-01",
        "expected_sha256": digest(output),
        "message": "Publish approved HWPX",
    });
    let prepared = daemon.handle(
        &approval_request("prepare_git_commit_approval", &params),
        &token(),
    );
    assert_eq!(prepared["protocol_version"], APPROVAL_PROTOCOL_VERSION);
    assert_eq!(prepared["ok"], true);
    assert_eq!(prepared["result"]["operation_id"], "operation-approval-01");
    assert_eq!(prepared["result"]["expected_head"], "d".repeat(40));
    assert_eq!(
        prepared["result"]["expected_head_reference"],
        "refs/heads/main"
    );
    assert_eq!(prepared["result"]["approval"]["effect"], "git_commit");
    for field in ["target_sha256", "plan_sha256"] {
        let value = prepared["result"]["approval"][field]
            .as_str()
            .unwrap_or_else(|| panic!("missing approval digest: {field}"));
        assert_eq!(value.len(), 64);
        assert!(value.bytes().all(|byte| byte.is_ascii_hexdigit()));
    }
    assert_eq!(prepared["result"]["executed"], false);
    assert!(
        !prepared
            .to_string()
            .contains(workspace.to_string_lossy().as_ref())
    );
    assert_eq!(
        daemon.handle(
            &workflow_request("prepare_git_commit_approval", &params),
            &token()
        )["ok"],
        false
    );
    assert_eq!(
        daemon.handle(&approval_request("prepare_git_commit", &params), &token())["ok"],
        false
    );

    fs::write(workspace.join("output/result-01.hwpx"), b"drift")
        .unwrap_or_else(|error| panic!("drift: {error}"));
    assert_eq!(
        daemon.handle(
            &approval_request("prepare_git_commit_approval", &params),
            &token()
        )["ok"],
        false
    );
}

#[test]
fn checked_in_private_contract_matches_runtime_constants() {
    let contract: Value = serde_json::from_str(include_str!(
        "../../../protocol/private/p17-local-daemon-v1.json"
    ))
    .unwrap_or_else(|error| panic!("contract: {error}"));
    assert_eq!(contract["protocol_version"], PROTOCOL_VERSION);
    assert_eq!(contract["configuration"]["schema_version"], CONFIG_VERSION);
    assert_eq!(contract["configuration"]["target_profile"], TARGET_PROFILE);
    assert_eq!(contract["configuration"]["max_workspaces"], 8);
    assert_eq!(contract["authentication"]["decoded_bytes"], 32);
    assert_eq!(contract["public_data"]["absolute_paths"], false);
    assert_eq!(contract["write_policy"]["overwrite"], false);
}

#[test]
fn checked_in_workflow_contract_matches_runtime_constants() {
    let contract: Value = serde_json::from_str(include_str!(
        "../../../protocol/private/p17-local-daemon-v2.json"
    ))
    .unwrap_or_else(|error| panic!("contract: {error}"));
    assert_eq!(contract["protocol_version"], WORKFLOW_PROTOCOL_VERSION);
    assert_eq!(contract["migration"]["v1_health_preserved"], true);
    assert_eq!(contract["public_identifiers"]["accepts_paths"], false);
    assert_eq!(contract["git"]["executes_process"], false);
    assert_eq!(contract["write_policy"]["overwrite"], false);
}

#[test]
fn checked_in_approval_binding_contract_matches_runtime_constants() {
    let contract: Value = serde_json::from_str(include_str!(
        "../../../protocol/private/p17-local-daemon-v3.json"
    ))
    .unwrap_or_else(|error| panic!("contract: {error}"));
    assert_eq!(contract["protocol_version"], APPROVAL_PROTOCOL_VERSION);
    assert_eq!(contract["migration"]["v2_workflow_preserved"], true);
    assert_eq!(contract["approval"]["effect"], "git_commit");
    assert_eq!(contract["approval"]["executes_process"], false);
    assert_eq!(contract["public_identifiers"]["accepts_paths"], false);
}

#[cfg(windows)]
#[test]
fn windows_junction_escape_is_rejected() {
    use std::process::{Command, Stdio};

    let (temporary, config) = fixture();
    let outside = temporary.path().join("outside");
    fs::create_dir(&outside).unwrap_or_else(|error| panic!("outside: {error}"));
    fs::write(outside.join("secret.hwpx"), b"private")
        .unwrap_or_else(|error| panic!("outside file: {error}"));
    let link = temporary
        .path()
        .join("workspace")
        .join("input")
        .join("link");
    let status = Command::new("cmd.exe")
        .args(["/d", "/c", "mklink", "/J"])
        .arg(&link)
        .arg(&outside)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .unwrap_or_else(|error| panic!("junction command: {error}"));
    assert!(status.success(), "junction fixture failed");
    let daemon = LocalCompanionDaemon::new(config);
    let response = daemon.handle(
        &request(
            "authorize_path",
            &json!({
                "workspace_id": "primary",
                "relative_path": "input/link/secret.hwpx",
                "access": "read_existing",
            }),
        ),
        &token(),
    );
    assert_eq!(response["ok"], false);
    fs::remove_dir(&link).unwrap_or_else(|error| panic!("junction cleanup: {error}"));
}

#[cfg(unix)]
#[test]
fn symlink_escape_is_rejected() {
    use std::os::unix::fs::symlink;

    let (temporary, config) = fixture();
    let outside = temporary.path().join("outside");
    fs::create_dir(&outside).unwrap_or_else(|error| panic!("outside: {error}"));
    fs::write(outside.join("secret.hwpx"), b"private")
        .unwrap_or_else(|error| panic!("outside file: {error}"));
    symlink(
        &outside,
        temporary
            .path()
            .join("workspace")
            .join("input")
            .join("link"),
    )
    .unwrap_or_else(|error| panic!("symlink: {error}"));
    let daemon = LocalCompanionDaemon::new(config);
    let response = daemon.handle(
        &request(
            "authorize_path",
            &json!({
                "workspace_id": "primary",
                "relative_path": "input/link/secret.hwpx",
                "access": "read_existing",
            }),
        ),
        &token(),
    );
    assert_eq!(response["ok"], false);
}
