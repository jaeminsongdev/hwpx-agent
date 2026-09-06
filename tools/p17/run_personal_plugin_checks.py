"""Verify the installed current-PC personal plugin through a fresh Codex session."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/personal-plugin-runs"
PLUGIN_ID = "hwpx-agent-local@personal"
SERVER_NAME = "hwpx-agent-local"
TOOL_NAME = "local_companion_health"
TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136"
PLUGIN_ROOT = Path.home() / "plugins/hwpx-agent-local"
MARKETPLACE = Path.home() / ".agents/plugins/marketplace.json"
VALIDATOR = (
    Path.home()
    / ".codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
)
WORKSPACE = Path("D:/개발/hwpx-agent-local-workspace")
CHECKS = (
    "clean_tracked_source",
    "plugin_source_validated",
    "personal_marketplace_identity_exact",
    "plugin_installed_and_enabled",
    "mcp_registration_enabled_exact",
    "mcp_config_contains_no_secret_environment",
    "runtime_config_is_current_2020_disabled_mode",
    "fresh_ephemeral_codex_session_completed",
    "exactly_one_local_health_tool_called",
    "bounded_redacted_ready_result_returned",
    "no_shell_hangul_or_document_tool_called",
    "canonical_receipt_written",
)
SOURCES = (
    "protocol/private/p17-local-mcp-v1.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/src/server.ts",
    "tools/p17/run_personal_plugin_checks.py",
    "tools/p17/tests/test_personal_plugin_checks.py",
    "implementation/p17/P17-04_LOCAL_MCP_BRIDGE_V1.md",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def canonical(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def executable(name: str) -> str:
    value = shutil.which(name)
    require(value is not None and Path(value).is_file(), "executable_missing")
    return value


def command(
    arguments: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [executable(arguments[0]), *arguments[1:]],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    require(completed.returncode == 0, "command_failed")
    return completed


def tracked_identity() -> tuple[str, bool]:
    commit = command(["git", "rev-parse", "HEAD"], timeout=15).stdout.strip()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "commit")
    status = command(
        ["git", "status", "--porcelain", "--untracked-files=no"], timeout=15
    ).stdout
    return commit, status == ""


def load_json(path: Path, code: str) -> dict[str, object]:
    require(path.is_file() and 0 < path.stat().st_size <= 256_000, f"{code}.file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceError(f"{code}.parse") from error
    require(isinstance(value, dict), f"{code}.type")
    return value


def parse_json_output(completed: subprocess.CompletedProcess[str], code: str) -> dict[str, object]:
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AcceptanceError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.type")
    return value


def validate_external_configuration() -> dict[str, str]:
    require(VALIDATOR.is_file(), "validator_missing")
    command([str(Path(os.sys.executable)), str(VALIDATOR), str(PLUGIN_ROOT)])
    marketplace = load_json(MARKETPLACE, "marketplace")
    require(
        marketplace.get("name") == "personal"
        and isinstance(marketplace.get("plugins"), list)
        and any(
            isinstance(item, dict)
            and item.get("name") == "hwpx-agent-local"
            and item.get("source")
            == {"source": "local", "path": "./plugins/hwpx-agent-local"}
            for item in marketplace["plugins"]
        ),
        "marketplace_identity",
    )
    plugin_list = parse_json_output(
        command(["codex", "plugin", "list", "--marketplace", "personal", "--json"]),
        "plugin_list",
    )
    installed = plugin_list.get("installed")
    require(
        isinstance(installed, list)
        and len(installed) == 1
        and isinstance(installed[0], dict)
        and installed[0].get("pluginId") == PLUGIN_ID
        and installed[0].get("installed") is True
        and installed[0].get("enabled") is True,
        "plugin_install",
    )
    registration = parse_json_output(
        command(["codex", "mcp", "get", SERVER_NAME, "--json"]),
        "mcp_registration",
    )
    transport = registration.get("transport")
    require(
        registration.get("name") == SERVER_NAME
        and registration.get("enabled") is True
        and registration.get("disabled_reason") is None
        and isinstance(transport, dict)
        and transport.get("type") == "stdio"
        and transport.get("env") is None
        and transport.get("env_vars") == [],
        "mcp_registration",
    )
    manifest_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    mcp_path = PLUGIN_ROOT / ".mcp.json"
    runtime_path = PLUGIN_ROOT / "runtime/config.json"
    manifest = load_json(manifest_path, "manifest")
    mcp = load_json(mcp_path, "mcp")
    runtime = load_json(runtime_path, "runtime")
    serialized_mcp = canonical(mcp).lower()
    require(
        manifest.get("name") == "hwpx-agent-local"
        and manifest.get("version") == "0.1.0",
        "manifest_identity",
    )
    require(
        all(word not in serialized_mcp for word in ("password", "secret", "token", "api_key")),
        "mcp_secret",
    )
    require(
        runtime.get("schema_version") == "hwpx-agent.local-companion-config/v1"
        and runtime.get("target_profile") == TARGET_PROFILE
        and runtime.get("automation_mode") == "disabled"
        and runtime.get("network_mode") == "disabled"
        and runtime.get("workspaces")
        == [{"id": "primary", "root": str(WORKSPACE)}],
        "runtime_config",
    )
    return {
        "manifest_sha256": digest(manifest_path),
        "mcp_sha256": digest(mcp_path),
        "runtime_sha256": digest(runtime_path),
    }


def fresh_codex_call() -> tuple[str, dict[str, object]]:
    require(WORKSPACE.is_dir(), "workspace_missing")
    completed = command(
        [
            "codex",
            "exec",
            "--ephemeral",
            "--json",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--ignore-rules",
            "-C",
            str(WORKSPACE),
            (
                "Call the MCP tool local_companion_health exactly once. "
                "Do not run shell commands, open Hangul, or inspect files. "
                "Return only the structured result and PASS or FAIL."
            ),
        ],
        cwd=WORKSPACE,
        timeout=180,
    )
    events: list[dict[str, object]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise AcceptanceError("codex_event_json") from error
        require(isinstance(event, dict), "codex_event_type")
        events.append(event)
    thread_events = [event for event in events if event.get("type") == "thread.started"]
    require(
        len(thread_events) == 1
        and isinstance(thread_events[0].get("thread_id"), str)
        and bool(re.fullmatch(r"[0-9a-f-]{36}", thread_events[0]["thread_id"])),
        "codex_thread",
    )
    completed_items = [
        event.get("item")
        for event in events
        if event.get("type") == "item.completed" and isinstance(event.get("item"), dict)
    ]
    tool_items = [item for item in completed_items if item.get("type") == "mcp_tool_call"]
    require(
        len(tool_items) == 1
        and tool_items[0].get("server") == SERVER_NAME
        and tool_items[0].get("tool") == TOOL_NAME
        and tool_items[0].get("arguments") == {}
        and tool_items[0].get("error") is None
        and tool_items[0].get("status") == "completed",
        "codex_tool_call",
    )
    require(
        not any(item.get("type") == "command_execution" for item in completed_items),
        "unexpected_command",
    )
    result = tool_items[0].get("result")
    require(isinstance(result, dict), "tool_result")
    structured = result.get("structured_content")
    require(
        isinstance(structured, dict)
        and set(structured)
        == {
            "automation_enabled",
            "config_sha256",
            "network_enabled",
            "status",
            "target_profile",
            "workspace_count",
        }
        and structured.get("automation_enabled") is False
        and structured.get("network_enabled") is False
        and structured.get("status") == "ready"
        and structured.get("target_profile") == TARGET_PROFILE
        and structured.get("workspace_count") == 1
        and isinstance(structured.get("config_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", structured["config_sha256"])),
        "tool_health",
    )
    transcript = canonical(events)
    require(
        str(PLUGIN_ROOT) not in transcript
        and str(WORKSPACE) not in transcript
        and "session_token" not in transcript,
        "private_data_exposed",
    )
    return thread_events[0]["thread_id"], structured


def run() -> dict[str, object]:
    commit, clean = tracked_identity()
    require(clean, "tracked_source_dirty")
    source_hashes = validate_external_configuration()
    thread_id, health = fresh_codex_call()
    require(tracked_identity()[1], "tracked_source_changed")
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    receipt = {
        "schema_version": "hwpx-agent.p17-personal-plugin-check/v1",
        "run_id": run_id,
        "scope": "current_pc_personal_plugin_local_health_only",
        "source_commit": commit,
        "plugin_id": PLUGIN_ID,
        "plugin_version": "0.1.0",
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "ephemeral_codex_thread_id": thread_id,
        "external_config_hashes": source_hashes,
        "health_config_sha256": health["config_sha256"],
        "actual_codex_plugin": True,
        "actual_hangul": False,
        "product_network_enabled": False,
        "codex_service_used": True,
    }
    receipt_path = run_dir / "receipt.json"
    receipt_path.write_bytes((canonical(receipt) + "\n").encode("utf-8"))
    require(receipt_path.read_bytes() == (canonical(receipt) + "\n").encode("utf-8"), "receipt")
    return receipt


if __name__ == "__main__":
    try:
        result = run()
    except AcceptanceError as error:
        print(canonical({"decision": "FAIL", "code": str(error)}))
        raise SystemExit(1) from None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        print(canonical({"decision": "FAIL", "code": "acceptance_unavailable"}))
        raise SystemExit(1) from None
    print(
        canonical(
            {
                "decision": result["decision"],
                "run_id": result["run_id"],
                "check_count": result["check_count"],
            }
        )
    )
