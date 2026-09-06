"""Verify the personal plugin after rebinding it to the integrated main root."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import uuid

import run_personal_plugin_checks as base


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/main-bound-plugin-runs"
PLUGIN_VERSION = "0.1.0+codex.20260906011622"
CHECKS = (
    "clean_integrated_main_source",
    "plugin_source_validated",
    "cachebuster_version_installed_enabled",
    "mcp_paths_bound_to_integrated_main_root",
    "mcp_config_contains_no_secret_environment",
    "runtime_config_is_current_2020_disabled_mode",
    "fresh_ephemeral_codex_session_completed",
    "exactly_one_local_health_tool_called",
    "bounded_redacted_ready_result_returned",
    "no_shell_hangul_or_document_tool_called",
    "canonical_receipt_written",
)
SOURCES = (
    "tools/p17/run_main_bound_plugin_checks.py",
    "tools/p17/tests/test_main_bound_plugin_checks.py",
    "tools/p17/run_personal_plugin_checks.py",
    "implementation/p17/P17-04_LOCAL_MCP_BRIDGE_V1.md",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise base.AcceptanceError(code)


def validate_main_binding() -> dict[str, str]:
    base.command([sys.executable, str(base.VALIDATOR), str(base.PLUGIN_ROOT)])
    plugin_list = base.parse_json_output(
        base.command(["codex", "plugin", "list", "--marketplace", "personal", "--json"]),
        "plugin_list",
    )
    installed = plugin_list.get("installed")
    require(
        isinstance(installed, list)
        and len(installed) == 1
        and isinstance(installed[0], dict)
        and installed[0].get("pluginId") == base.PLUGIN_ID
        and installed[0].get("version") == PLUGIN_VERSION
        and installed[0].get("installed") is True
        and installed[0].get("enabled") is True,
        "plugin_install",
    )
    registration = base.parse_json_output(
        base.command(["codex", "mcp", "get", base.SERVER_NAME, "--json"]),
        "mcp_registration",
    )
    transport = registration.get("transport")
    bridge = (ROOT / "web/local-companion-mcp/dist/server.js").resolve()
    daemon = (ROOT / "target/debug/local-companion-daemon.exe").resolve()
    runtime = (base.PLUGIN_ROOT / "runtime/config.json").resolve()
    require(bridge.is_file() and daemon.is_file() and runtime.is_file(), "runtime_files")
    require(
        registration.get("name") == base.SERVER_NAME
        and registration.get("enabled") is True
        and isinstance(transport, dict)
        and transport.get("type") == "stdio"
        and transport.get("args")
        == [str(bridge), "--daemon", str(daemon), "--config", str(runtime)]
        and transport.get("env") is None
        and transport.get("env_vars") == [],
        "main_binding",
    )
    manifest_path = base.PLUGIN_ROOT / ".codex-plugin/plugin.json"
    mcp_path = base.PLUGIN_ROOT / ".mcp.json"
    manifest = base.load_json(manifest_path, "manifest")
    mcp = base.load_json(mcp_path, "mcp")
    runtime_config = base.load_json(runtime, "runtime")
    require(
        manifest.get("name") == "hwpx-agent-local"
        and manifest.get("version") == PLUGIN_VERSION,
        "manifest_identity",
    )
    serialized_mcp = base.canonical(mcp).lower()
    require(
        all(word not in serialized_mcp for word in ("password", "secret", "token", "api_key")),
        "mcp_secret",
    )
    require(
        runtime_config.get("target_profile") == base.TARGET_PROFILE
        and runtime_config.get("automation_mode") == "disabled"
        and runtime_config.get("network_mode") == "disabled",
        "runtime_config",
    )
    return {
        "manifest_sha256": base.digest(manifest_path),
        "mcp_sha256": base.digest(mcp_path),
        "runtime_sha256": base.digest(runtime),
    }


def run() -> dict[str, object]:
    commit, clean = base.tracked_identity()
    require(clean, "tracked_source_dirty")
    require(ROOT.resolve() == Path("D:/개발/hwpx-agent").resolve(), "main_root")
    source_hashes = validate_main_binding()
    thread_id, health = base.fresh_codex_call()
    require(base.tracked_identity()[1], "tracked_source_changed")
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    receipt = {
        "schema_version": "hwpx-agent.p17-main-bound-plugin-check/v1",
        "run_id": run_id,
        "scope": "current_pc_integrated_main_personal_plugin_health_only",
        "source_commit": commit,
        "plugin_id": base.PLUGIN_ID,
        "plugin_version": PLUGIN_VERSION,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "ephemeral_codex_thread_id": thread_id,
        "external_config_hashes": source_hashes,
        "health_config_sha256": health["config_sha256"],
        "main_root_bound": True,
        "actual_codex_plugin": True,
        "actual_hangul": False,
        "product_network_enabled": False,
        "codex_service_used": True,
    }
    receipt_path = run_dir / "receipt.json"
    receipt_path.write_bytes((base.canonical(receipt) + "\n").encode("utf-8"))
    require(
        receipt_path.read_bytes() == (base.canonical(receipt) + "\n").encode("utf-8"),
        "receipt",
    )
    return receipt


if __name__ == "__main__":
    try:
        result = run()
    except base.AcceptanceError as error:
        print(base.canonical({"decision": "FAIL", "code": str(error)}))
        raise SystemExit(1) from None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        print(base.canonical({"decision": "FAIL", "code": "acceptance_unavailable"}))
        raise SystemExit(1) from None
    print(
        base.canonical(
            {
                "decision": result["decision"],
                "run_id": result["run_id"],
                "check_count": result["check_count"],
            }
        )
    )
