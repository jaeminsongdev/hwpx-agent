"""Run the P17-04 local stdio MCP to Rust-daemon acceptance."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/local-mcp-runs"
PROTOCOL_VERSION = "2025-11-25"
TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136"
TOOL_NAME = "local_companion_health"
CHECKS = (
    "clean_tracked_source",
    "locked_offline_rust_and_node_builds",
    "modern_stdio_mcp_initialized",
    "exactly_one_health_tool_discovered",
    "strict_empty_input_schema",
    "authenticated_daemon_health_called",
    "bounded_redacted_health_returned",
    "unknown_tool_argument_rejected",
    "private_paths_and_document_content_absent",
    "graceful_stdio_shutdown",
    "temporary_resources_cleaned",
    "no_hangul_or_network_used",
)
SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "protocol/private/p17-local-daemon-v1.json",
    "protocol/private/p17-local-mcp-v1.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/tsconfig.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "tools/p17/run_local_mcp_checks.py",
    "tools/p17/tests/test_local_mcp_checks.py",
    "implementation/p17/P17-04_LOCAL_MCP_BRIDGE_V1.md",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def canonical(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def command(arguments: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise AcceptanceError("build_failed")
    return completed


def tracked_identity() -> tuple[str, bool]:
    commit = command(["git", "rev-parse", "HEAD"], timeout=15).stdout.strip()
    require(len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), "commit")
    status = command(
        ["git", "status", "--porcelain", "--untracked-files=no"], timeout=15
    ).stdout
    return commit, status == ""


def binary_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    path = ROOT / "target" / "debug" / f"local-companion-daemon{suffix}"
    require(path.is_file(), "daemon_binary_missing")
    return path.resolve()


def bridge_path() -> Path:
    path = ROOT / "web/local-companion-mcp/dist/server.js"
    require(path.is_file(), "bridge_missing")
    return path.resolve()


def request(request_id: int, method: str, params: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def read_response(
    process: subprocess.Popen[str], request_id: int
) -> dict[str, object]:
    require(process.stdout is not None, "stdout_missing")
    line = process.stdout.readline(262_145)
    require(line != "" and len(line.encode("utf-8")) <= 262_144, "response_missing")
    require(line.endswith("\n") and "\r" not in line, "response_framing")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as error:
        raise AcceptanceError("response_json") from error
    require(
        isinstance(value, dict)
        and value.get("jsonrpc") == "2.0"
        and value.get("id") == request_id
        and set(value).issubset({"jsonrpc", "id", "result", "error"}),
        "response_identity",
    )
    return value


def send(process: subprocess.Popen[str], value: object) -> None:
    require(process.stdin is not None, "stdin_missing")
    process.stdin.write(canonical(value) + "\n")
    process.stdin.flush()


def run() -> dict[str, object]:
    commit, clean = tracked_identity()
    require(clean, "tracked_source_dirty")
    command(
        ["cargo", "build", "-p", "local-companion-daemon", "--locked", "--offline"]
    )
    command(["pnpm", "install", "--offline", "--frozen-lockfile"])
    command(["pnpm", "--filter", "@hwpx-agent/local-companion-mcp", "build"])
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    temporary_path: Path | None = None
    process: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="fixture-", dir=run_dir) as temporary:
            temporary_path = Path(temporary).resolve()
            workspace = temporary_path / "workspace"
            (workspace / "input").mkdir(parents=True)
            (workspace / "output").mkdir()
            fixture_marker = "MCP_PRIVATE_FIXTURE_MARKER"
            (workspace / "input" / "fixture.hwpx").write_bytes(
                fixture_marker.encode("ascii")
            )
            config_path = temporary_path / "config.json"
            config_path.write_bytes(
                canonical(
                    {
                        "schema_version": "hwpx-agent.local-companion-config/v1",
                        "target_profile": TARGET_PROFILE,
                        "automation_mode": "disabled",
                        "network_mode": "disabled",
                        "max_file_bytes": 1_048_576,
                        "workspaces": [{"id": "primary", "root": str(workspace)}],
                    }
                ).encode("utf-8")
            )
            node = shutil.which("node")
            require(node is not None and Path(node).is_file(), "node_missing")
            environment = {
                name: value
                for name in ("SystemRoot", "WINDIR")
                if (value := os.environ.get(name)) is not None
            }
            process = subprocess.Popen(
                [
                    node,
                    str(bridge_path()),
                    "--daemon",
                    str(binary_path()),
                    "--config",
                    str(config_path),
                ],
                cwd=ROOT,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="strict",
                bufsize=1,
            )
            send(
                process,
                request(
                    1,
                    "initialize",
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "p17-acceptance", "version": "1.0.0"},
                    },
                ),
            )
            initialized = read_response(process, 1)
            result = initialized.get("result")
            require(
                isinstance(result, dict)
                and result.get("protocolVersion") == PROTOCOL_VERSION
                and result.get("serverInfo")
                == {"name": "hwpx-agent-local-companion", "version": "0.1.0"},
                "initialize",
            )
            send(
                process,
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                },
            )
            send(process, request(2, "tools/list", {}))
            listed = read_response(process, 2).get("result")
            require(isinstance(listed, dict), "tools_list")
            tools = listed.get("tools")
            require(isinstance(tools, list) and len(tools) == 1, "tool_count")
            tool = tools[0]
            require(
                isinstance(tool, dict)
                and tool.get("name") == TOOL_NAME
                and tool.get("inputSchema")
                == {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                }
                and tool.get("annotations")
                == {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "tool_contract",
            )
            send(
                process,
                request(3, "tools/call", {"name": TOOL_NAME, "arguments": {}}),
            )
            called = read_response(process, 3).get("result")
            require(isinstance(called, dict), "health_result")
            require(called.get("isError") is False, "health_error")
            health = called.get("structuredContent")
            require(
                isinstance(health, dict)
                and health.get("status") == "ready"
                and health.get("target_profile") == TARGET_PROFILE
                and health.get("automation_enabled") is False
                and health.get("network_enabled") is False
                and health.get("workspace_count") == 1
                and isinstance(health.get("config_sha256"), str)
                and len(health["config_sha256"]) == 64,
                "health_contract",
            )
            send(
                process,
                request(
                    4,
                    "tools/call",
                    {"name": TOOL_NAME, "arguments": {"path": str(workspace)}},
                ),
            )
            rejected = read_response(process, 4)
            require("error" in rejected, "unknown_argument_admitted")
            transcript = canonical([initialized, listed, called, rejected])
            require(
                str(temporary_path) not in transcript
                and fixture_marker not in transcript
                and "session_token" not in transcript,
                "private_data_exposed",
            )
            require(process.stdin is not None, "stdin_missing")
            process.stdin.close()
            process.wait(timeout=10)
            require(process.returncode == 0, "bridge_exit")
            require(process.stderr is not None, "stderr_missing")
            require(process.stderr.read() == "", "bridge_stderr")
            process = None
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if temporary_path is not None and temporary_path.exists():
            shutil.rmtree(temporary_path)
    resources_cleaned = temporary_path is not None and not temporary_path.exists()
    require(resources_cleaned, "cleanup")
    require(tracked_identity()[1], "tracked_source_changed")
    receipt = {
        "schema_version": "hwpx-agent.p17-local-mcp-check/v1",
        "run_id": run_id,
        "scope": "current_pc_local_stdio_mcp_health_only",
        "source_commit": commit,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "resources_cleaned": True,
        "actual_codex_mcp": True,
        "actual_personal_plugin": False,
        "actual_hangul": False,
        "network_used": False,
    }
    (run_dir / "receipt.json").write_bytes(
        (canonical(receipt) + "\n").encode("utf-8")
    )
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
