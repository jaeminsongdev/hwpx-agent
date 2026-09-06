use std::fs;
use std::io::Write as _;
use std::process::{Command, Stdio};

use local_companion_daemon::{CONFIG_VERSION, PROTOCOL_VERSION, TARGET_PROFILE};
use serde_json::{Value, json};

const TOKEN: &str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

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
