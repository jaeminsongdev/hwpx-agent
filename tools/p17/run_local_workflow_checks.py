"""Run P17-05 path-free local workflow acceptance through the real MCP bridge."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/local-workflow-runs"
MCP_PROTOCOL = "2025-11-25"
TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136"
TOOLS = (
    "local_companion_health",
    "local_companion_materialize",
    "local_companion_diff",
    "local_companion_publish",
    "local_companion_prepare_git_commit",
)
CHECKS = (
    "clean_tracked_source",
    "locked_offline_rust_and_node_builds",
    "modern_stdio_mcp_initialized",
    "exact_five_tool_catalog",
    "path_free_closed_input_schemas",
    "v1_health_preserved",
    "checksum_bound_source_materialized",
    "multi_buffer_candidate_materialized",
    "content_free_identity_diff",
    "create_new_output_published",
    "input_bytes_preserved",
    "git_plan_bound_without_execution",
    "traversal_large_and_unknown_fields_rejected",
    "private_paths_content_and_token_absent",
    "graceful_shutdown_and_cleanup",
    "no_hangul_or_network_used",
)
SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "crates/local-workflow/Cargo.toml",
    "crates/local-workflow/src/lib.rs",
    "crates/local-workflow/tests/workflow.rs",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "crates/local-companion-daemon/tests/binary_smoke.rs",
    "crates/local-companion-daemon/tests/sandbox.rs",
    "protocol/private/p17-local-workflow-v1.json",
    "protocol/private/p17-local-daemon-v1.json",
    "protocol/private/p17-local-daemon-v2.json",
    "protocol/private/p17-local-mcp-v1.json",
    "protocol/private/p17-local-mcp-v2.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/tsconfig.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "tools/p17/run_local_workflow_checks.py",
    "tools/p17/tests/test_local_workflow_checks.py",
    "implementation/p17/P17-05_LOCAL_WORKFLOW_CORE_V1.md",
    "implementation/p17/P17-05_LOCAL_WORKFLOW_MCP_V2.md",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def canonical(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def command(arguments: list[str], *, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(arguments[0])
    if executable is None:
        raise AcceptanceError("build_tool_missing")
    completed = subprocess.run(
        [executable, *arguments[1:]],
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


def send(process: subprocess.Popen[str], value: object) -> None:
    require(process.stdin is not None, "stdin_missing")
    process.stdin.write(canonical(value) + "\n")
    process.stdin.flush()


def read_response(process: subprocess.Popen[str], request_id: int) -> dict[str, object]:
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


def call_tool(
    process: subprocess.Popen[str], request_id: int, name: str, arguments: dict[str, object]
) -> dict[str, object]:
    send(
        process,
        request(request_id, "tools/call", {"name": name, "arguments": arguments}),
    )
    response = read_response(process, request_id)
    result = response.get("result")
    require(
        isinstance(result, dict)
        and result.get("isError") is False
        and isinstance(result.get("structuredContent"), dict),
        "tool_call_failed",
    )
    return result["structuredContent"]


def call_rejected(
    process: subprocess.Popen[str], request_id: int, name: str, arguments: dict[str, object]
) -> dict[str, object]:
    send(
        process,
        request(request_id, "tools/call", {"name": name, "arguments": arguments}),
    )
    response = read_response(process, request_id)
    result = response.get("result")
    require(
        isinstance(result, dict)
        and result.get("isError") is True
        and "structuredContent" not in result,
        "negative_call_admitted",
    )
    return result


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
            source = b"P17_SOURCE_PRIVATE_MARKER"
            candidate = bytes(index % 251 for index in range(196_625))
            oversized = b"L" * 300_001
            fixtures = {
                "source-01": source,
                "candidate-01": candidate,
                "oversized-01": oversized,
            }
            for fixture_id, content in fixtures.items():
                (workspace / "input" / f"{fixture_id}.hwpx").write_bytes(content)
            (workspace / ".git" / "refs" / "heads").mkdir(parents=True)
            (workspace / ".git" / "HEAD").write_text(
                "ref: refs/heads/main\n", encoding="ascii", newline="\n"
            )
            head = "a" * 40
            (workspace / ".git" / "refs" / "heads" / "main").write_text(
                head + "\n", encoding="ascii", newline="\n"
            )
            config_path = temporary_path / "config.json"
            config_path.write_bytes(
                canonical(
                    {
                        "schema_version": "hwpx-agent.local-companion-config/v1",
                        "target_profile": TARGET_PROFILE,
                        "automation_mode": "disabled",
                        "network_mode": "disabled",
                        "max_file_bytes": 300_000,
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
                        "protocolVersion": MCP_PROTOCOL,
                        "capabilities": {},
                        "clientInfo": {"name": "p17-workflow", "version": "1.0.0"},
                    },
                ),
            )
            initialized = read_response(process, 1)
            result = initialized.get("result")
            require(
                isinstance(result, dict)
                and result.get("protocolVersion") == MCP_PROTOCOL
                and result.get("serverInfo")
                == {"name": "hwpx-agent-local-companion", "version": "0.2.0"},
                "initialize",
            )
            send(
                process,
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            )
            send(process, request(2, "tools/list", {}))
            listed = read_response(process, 2).get("result")
            require(isinstance(listed, dict), "tools_list")
            tools = listed.get("tools")
            require(isinstance(tools, list) and len(tools) == 5, "tool_count")
            catalog: dict[str, dict[str, object]] = {}
            for tool in tools:
                require(isinstance(tool, dict) and isinstance(tool.get("name"), str), "tool")
                catalog[tool["name"]] = tool
                schema = tool.get("inputSchema")
                require(
                    isinstance(schema, dict)
                    and schema.get("type") == "object"
                    and schema.get("additionalProperties") is False
                    and all("path" not in name for name in schema.get("properties", {})),
                    "path_input_schema",
                )
            require(tuple(sorted(catalog)) == tuple(sorted(TOOLS)), "tool_names")

            health = call_tool(process, 3, TOOLS[0], {})
            require(
                health.get("status") == "ready"
                and health.get("target_profile") == TARGET_PROFILE,
                "health",
            )
            source_digest = sha256_bytes(source)
            candidate_digest = sha256_bytes(candidate)
            common = {"workspace_id": "primary", "operation_id": "operation-01"}

            materialized_source = call_tool(
                process,
                4,
                TOOLS[1],
                {
                    **common,
                    "slot": "source",
                    "fixture_id": "source-01",
                    "expected_sha256": source_digest,
                },
            )
            require(materialized_source.get("sha256") == source_digest, "source_digest")
            materialized_candidate = call_tool(
                process,
                5,
                TOOLS[1],
                {
                    **common,
                    "slot": "candidate",
                    "fixture_id": "candidate-01",
                    "expected_sha256": candidate_digest,
                },
            )
            require(
                materialized_candidate.get("sha256") == candidate_digest
                and materialized_candidate.get("size_bytes") == len(candidate),
                "candidate_digest",
            )
            difference = call_tool(process, 6, TOOLS[2], common)
            require(
                difference.get("identical") is False
                and isinstance(difference.get("source"), dict)
                and difference["source"].get("sha256") == source_digest
                and isinstance(difference.get("candidate"), dict)
                and difference["candidate"].get("sha256") == candidate_digest,
                "diff",
            )
            published = call_tool(
                process,
                7,
                TOOLS[3],
                {
                    **common,
                    "output_id": "result-01",
                    "expected_sha256": candidate_digest,
                },
            )
            require(published.get("sha256") == candidate_digest, "publish")
            plan = call_tool(
                process,
                8,
                TOOLS[4],
                {
                    "workspace_id": "primary",
                    "output_id": "result-01",
                    "expected_sha256": candidate_digest,
                    "message": "Publish verified HWPX",
                },
            )
            require(
                plan.get("expected_head") == head
                and plan.get("output_pathspec") == "output/result-01.hwpx"
                and plan.get("executed") is False,
                "git_plan",
            )

            rejected_traversal = call_rejected(
                process,
                9,
                TOOLS[1],
                {
                    **common,
                    "operation_id": "operation-traversal",
                    "slot": "source",
                    "fixture_id": "../escape",
                    "expected_sha256": source_digest,
                },
            )
            rejected_large = call_rejected(
                process,
                10,
                TOOLS[1],
                {
                    **common,
                    "operation_id": "operation-large",
                    "slot": "source",
                    "fixture_id": "oversized-01",
                    "expected_sha256": sha256_bytes(oversized),
                },
            )
            rejected_extra = call_rejected(
                process,
                11,
                TOOLS[2],
                {**common, "path": str(workspace)},
            )

            require((workspace / "input/source-01.hwpx").read_bytes() == source, "source_changed")
            require(
                (workspace / "input/candidate-01.hwpx").read_bytes() == candidate,
                "candidate_changed",
            )
            require(
                (workspace / "output/result-01.hwpx").read_bytes() == candidate,
                "output_changed",
            )
            require(
                not (workspace / ".hwpx-agent/work/operation-01/candidate.hwpx").exists()
                and not (workspace / ".hwpx-agent/work/operation-large/source.hwpx").exists()
                and not (workspace / ".hwpx-agent/work/operation-traversal").exists(),
                "partial_output",
            )
            require(
                (workspace / ".git/HEAD").read_text(encoding="ascii")
                == "ref: refs/heads/main\n",
                "git_executed",
            )
            transcript = canonical(
                [
                    initialized,
                    listed,
                    health,
                    materialized_source,
                    materialized_candidate,
                    difference,
                    published,
                    plan,
                    rejected_traversal,
                    rejected_large,
                    rejected_extra,
                ]
            )
            require(
                str(temporary_path) not in transcript
                and "P17_SOURCE_PRIVATE_MARKER" not in transcript
                and "session_token" not in transcript,
                "private_data_exposed",
            )
            require(process.stdin is not None, "stdin_missing")
            process.stdin.close()
            process.wait(timeout=10)
            require(process.returncode == 0, "bridge_exit")
            require(process.stderr is not None and process.stderr.read() == "", "bridge_stderr")
            process = None
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if temporary_path is not None and temporary_path.exists():
            shutil.rmtree(temporary_path)
    require(temporary_path is not None and not temporary_path.exists(), "cleanup")
    require(tracked_identity()[1], "tracked_source_changed")
    receipt = {
        "schema_version": "hwpx-agent.p17-local-workflow-check/v1",
        "run_id": run_id,
        "scope": "current_pc_local_stdio_mcp_path_free_workflow",
        "source_commit": commit,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "resources_cleaned": True,
        "actual_mcp_stdio": True,
        "actual_codex_client": False,
        "actual_personal_plugin": False,
        "actual_git_commit": False,
        "actual_hangul": False,
        "network_used": False,
    }
    (run_dir / "receipt.json").write_bytes((canonical(receipt) + "\n").encode("utf-8"))
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
