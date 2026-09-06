"""Qualify installed v0.4 plugin health and read-only Git approval preparation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
from typing import Any

import run_personal_plugin_checks as base


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/widget-plugin-prepare-runs"
PLUGIN_VERSION = "0.4.0+codex.20260906130036"
PREPARE_TOOL = "local_companion_prepare_git_commit_approval"
WORKSPACE = Path("D:/개발/hwpx-agent-local-workspace")
OUTPUT_ID = "widget-check-01"
OUTPUT_PATH = WORKSPACE / "output/widget-check-01.hwpx"
EXPECTED_OUTPUT_SHA256 = (
    "a3d6a1a5749256577be7a3f13662271a048023da26b8789322cb06f69561b0ba"
)
EXPECTED_HEAD = "111ad2b6bf291f85b0e61cf537d063fdbc007d3c"
OPERATION_ID = "op_widgetqual01"
MESSAGE = "Approve widget qualification HWPX"
APPROVAL_STATE = base.PLUGIN_ROOT / "runtime/approval-state"
CHECKS = (
    "clean_tracked_source",
    "plugin_source_validated",
    "installed_v04_plugin_enabled_exact",
    "mcp_runtime_arguments_exact",
    "mcp_config_contains_no_secret_environment",
    "ignored_runtime_artifacts_hash_bound",
    "runtime_config_is_current_2020_disabled_mode",
    "approval_secret_not_persisted",
    "disposable_git_fixture_identity_exact",
    "fresh_health_session_completed",
    "exactly_one_health_tool_called",
    "fresh_prepare_session_completed",
    "exactly_one_read_only_prepare_tool_called",
    "bounded_plan_matches_fixture",
    "challenge_absent_from_model_structured_content",
    "no_confirm_shell_hangul_or_document_tool_called",
    "git_head_index_and_status_unchanged",
    "canonical_receipt_written",
)
SOURCES = (
    "protocol/private/p17-local-mcp-v4.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "web/plugin-widget/package.json",
    "web/plugin-widget/src/git-approval-mcp-app-port.ts",
    "web/plugin-widget/src/git-approval-controller.ts",
    "web/plugin-widget/src/git-approval-controller.test.ts",
    "tools/p17/run_personal_plugin_checks.py",
    "tools/p17/run_widget_plugin_prepare_checks.py",
    "tools/p17/tests/test_widget_plugin_prepare_checks.py",
    "implementation/p17/P17-08_TRUSTED_WIDGET_V7.md",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise base.AcceptanceError(code)


def path_entries(root: Path) -> tuple[str, ...]:
    if not root.exists():
        return ()
    require(root.is_dir() and not root.is_symlink(), "approval_state.root")
    return tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    )


def expected_runtime_paths() -> dict[str, Path]:
    return {
        "node": Path("C:/Program Files/nodejs/node.exe").resolve(),
        "server": (ROOT / "web/local-companion-mcp/dist/server.js").resolve(),
        "daemon": (ROOT / "target/debug/local-companion-daemon.exe").resolve(),
        "runtime": (base.PLUGIN_ROOT / "runtime/config.json").resolve(),
        "widget": (ROOT / "web/plugin-widget/dist/git-approval-widget-v1.html").resolve(),
        "git": Path("C:/Program Files/Git/cmd/git.exe").resolve(),
        "approval_state": APPROVAL_STATE.resolve(),
    }


def validate_widget_binding() -> dict[str, str]:
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

    paths = expected_runtime_paths()
    require(all(path.is_file() for key, path in paths.items() if key != "approval_state"), "runtime_files")
    registration = base.parse_json_output(
        base.command(["codex", "mcp", "get", base.SERVER_NAME, "--json"]),
        "mcp_registration",
    )
    transport = registration.get("transport")
    expected_args = [
        str(paths["server"]),
        "--daemon",
        str(paths["daemon"]),
        "--config",
        str(paths["runtime"]),
        "--widget",
        str(paths["widget"]),
        "--git",
        str(paths["git"]),
        "--approval-state",
        str(paths["approval_state"]),
    ]
    require(
        registration.get("name") == base.SERVER_NAME
        and registration.get("enabled") is True
        and registration.get("disabled_reason") is None
        and isinstance(transport, dict)
        and transport.get("type") == "stdio"
        and transport.get("command") == str(paths["node"])
        and transport.get("args") == expected_args
        and transport.get("env") is None
        and transport.get("env_vars") == []
        and transport.get("cwd") is None,
        "mcp_registration",
    )

    manifest_path = base.PLUGIN_ROOT / ".codex-plugin/plugin.json"
    mcp_path = base.PLUGIN_ROOT / ".mcp.json"
    manifest = base.load_json(manifest_path, "manifest")
    mcp = base.load_json(mcp_path, "mcp")
    runtime = base.load_json(paths["runtime"], "runtime")
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
        runtime
        == {
            "schema_version": "hwpx-agent.local-companion-config/v1",
            "target_profile": base.TARGET_PROFILE,
            "automation_mode": "disabled",
            "network_mode": "disabled",
            "max_file_bytes": 1_073_741_824,
            "workspaces": [{"id": "primary", "root": str(WORKSPACE)}],
        },
        "runtime_config",
    )
    require(path_entries(APPROVAL_STATE) == (), "approval_state.before")
    return {
        "manifest_sha256": base.digest(manifest_path),
        "mcp_sha256": base.digest(mcp_path),
        "runtime_sha256": base.digest(paths["runtime"]),
        "node_sha256": base.digest(paths["node"]),
        "server_sha256": base.digest(paths["server"]),
        "daemon_sha256": base.digest(paths["daemon"]),
        "widget_sha256": base.digest(paths["widget"]),
        "git_sha256": base.digest(paths["git"]),
    }


def git_output(arguments: list[str]) -> bytes:
    completed = subprocess.run(
        [base.executable("git"), *arguments],
        cwd=WORKSPACE,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        timeout=30,
    )
    require(completed.returncode == 0, "git_command")
    return completed.stdout


def git_snapshot() -> dict[str, str]:
    require(WORKSPACE.is_dir() and OUTPUT_PATH.is_file(), "workspace_fixture")
    head = git_output(["rev-parse", "HEAD"]).decode("ascii").strip()
    output_sha256 = base.digest(OUTPUT_PATH)
    require(head == EXPECTED_HEAD, "workspace_head")
    require(output_sha256 == EXPECTED_OUTPUT_SHA256, "workspace_output")
    return {
        "head": head,
        "status_sha256": hashlib.sha256(
            git_output(["status", "--porcelain=v1", "-z"])
        ).hexdigest(),
        "index_sha256": hashlib.sha256(
            git_output(["ls-files", "-s", "-z"])
        ).hexdigest(),
        "output_sha256": output_sha256,
    }


def load_events(completed: subprocess.CompletedProcess[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise base.AcceptanceError("codex_event_json") from error
        require(isinstance(event, dict), "codex_event_type")
        events.append(event)
    return events


def completed_items(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event["item"]
        for event in events
        if event.get("type") == "item.completed" and isinstance(event.get("item"), dict)
    ]


def thread_id(events: list[dict[str, Any]]) -> str:
    started = [event for event in events if event.get("type") == "thread.started"]
    require(
        len(started) == 1
        and isinstance(started[0].get("thread_id"), str)
        and bool(re.fullmatch(r"[0-9a-f-]{36}", started[0]["thread_id"])),
        "codex_thread",
    )
    return started[0]["thread_id"]


def validate_prepare_plan(value: object) -> dict[str, Any]:
    require(isinstance(value, dict), "prepare.structured")
    plan = value
    require(
        set(plan)
        == {
            "approval",
            "executed",
            "expected_head",
            "expected_head_reference",
            "expected_output_sha256",
            "message",
            "operation_id",
            "output_id",
            "output_pathspec",
            "workspace_id",
        },
        "prepare.fields",
    )
    approval = plan.get("approval")
    require(
        plan.get("workspace_id") == "primary"
        and plan.get("operation_id") == OPERATION_ID
        and plan.get("output_id") == OUTPUT_ID
        and plan.get("output_pathspec") == f"output/{OUTPUT_ID}.hwpx"
        and plan.get("expected_output_sha256") == EXPECTED_OUTPUT_SHA256
        and plan.get("message") == MESSAGE
        and plan.get("expected_head") == EXPECTED_HEAD
        and plan.get("expected_head_reference") == "refs/heads/main"
        and plan.get("executed") is False
        and isinstance(approval, dict)
        and set(approval) == {"effect", "plan_sha256", "target_sha256"}
        and approval.get("effect") == "git_commit"
        and isinstance(approval.get("plan_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", approval["plan_sha256"]))
        and isinstance(approval.get("target_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", approval["target_sha256"])),
        "prepare.plan",
    )
    forbidden = ("approval_challenge", "confirmation_token", "session_token", "secret")
    serialized = base.canonical(plan).lower()
    require(all(word not in serialized for word in forbidden), "prepare.model_secret")
    return plan


def fresh_prepare_call() -> tuple[str, dict[str, Any]]:
    arguments = {
        "workspace_id": "primary",
        "operation_id": OPERATION_ID,
        "output_id": OUTPUT_ID,
        "expected_sha256": EXPECTED_OUTPUT_SHA256,
        "message": MESSAGE,
    }
    completed = base.command(
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
                f"Call the MCP tool {PREPARE_TOOL} exactly once with this exact JSON: "
                f"{base.canonical(arguments)}. Do not call any other tool, do not confirm or "
                "execute the plan, do not run shell commands, and do not open Hangul or inspect "
                "files. Return only the structured result and PASS or FAIL."
            ),
        ],
        cwd=WORKSPACE,
        timeout=180,
    )
    events = load_events(completed)
    items = completed_items(events)
    tool_items = [item for item in items if item.get("type") == "mcp_tool_call"]
    require(
        len(tool_items) == 1
        and tool_items[0].get("server") == base.SERVER_NAME
        and tool_items[0].get("tool") == PREPARE_TOOL
        and tool_items[0].get("arguments") == arguments
        and tool_items[0].get("error") is None
        and tool_items[0].get("status") == "completed",
        "prepare.tool_call",
    )
    require(
        not any(item.get("type") == "command_execution" for item in items),
        "prepare.unexpected_command",
    )
    result = tool_items[0].get("result")
    require(isinstance(result, dict), "prepare.result")
    return thread_id(events), validate_prepare_plan(result.get("structured_content"))


def run() -> dict[str, object]:
    commit, clean = base.tracked_identity()
    require(clean, "tracked_source_dirty")
    require(ROOT.resolve() == Path("D:/개발/hwpx-agent").resolve(), "main_root")
    external_hashes = validate_widget_binding()
    before = git_snapshot()
    health_thread_id, health = base.fresh_codex_call()
    prepare_thread_id, plan = fresh_prepare_call()
    after = git_snapshot()
    require(before == after, "workspace_changed")
    require(path_entries(APPROVAL_STATE) == (), "approval_state.after")
    require(base.tracked_identity()[1], "tracked_source_changed")

    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    receipt = {
        "schema_version": "hwpx-agent.p17-widget-plugin-prepare-check/v1",
        "run_id": run_id,
        "scope": "current_pc_installed_v04_health_and_read_only_prepare_only",
        "source_commit": commit,
        "plugin_id": base.PLUGIN_ID,
        "plugin_version": PLUGIN_VERSION,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "health_thread_id": health_thread_id,
        "prepare_thread_id": prepare_thread_id,
        "external_hashes": external_hashes,
        "health_config_sha256": health["config_sha256"],
        "workspace_snapshot": after,
        "plan_binding": {
            "expected_head": plan["expected_head"],
            "expected_head_reference": plan["expected_head_reference"],
            "target_sha256": plan["approval"]["target_sha256"],
            "plan_sha256": plan["approval"]["plan_sha256"],
        },
        "actual_codex_plugin": True,
        "actual_health_call": True,
        "actual_read_only_prepare": True,
        "actual_trusted_ui": False,
        "actual_git_effect": False,
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
