"""Run the P17-08 confirmed Git effect through the real local MCP bridge."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/mcp-approval-effect-runs"
MCP_PROTOCOL = "2025-11-25"
TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136"
PREPARE_TOOL = "local_companion_prepare_git_commit_approval"
EXECUTE_TOOL = "local_companion_execute_git_commit"
TOOLS = (
    "local_companion_health",
    "local_companion_materialize",
    "local_companion_diff",
    "local_companion_publish",
    "local_companion_prepare_git_commit",
    PREPARE_TOOL,
    EXECUTE_TOOL,
)
CHECKS = (
    "clean_tracked_source",
    "locked_offline_rust_and_node_builds",
    "modern_stdio_mcp_initialized",
    "exact_seven_tool_catalog",
    "closed_path_free_public_input_schemas",
    "approval_prepare_read_only_annotation",
    "effect_destructive_non_idempotent_annotation",
    "real_git_repository_disposable",
    "exact_target_and_plan_digests_prepared",
    "trusted_host_test_authority_separate_from_mcp",
    "signed_confirmation_exactly_bound",
    "actual_mcp_daemon_git_commit_executed",
    "committed_bytes_and_parent_verified",
    "unrelated_staged_entry_preserved",
    "durable_same_token_replay_rejected",
    "token_secret_paths_and_content_absent_from_responses",
    "graceful_shutdown_and_cleanup",
    "no_hangul_user_repository_or_network_used",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def canonical(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compact(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def command(
    arguments: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(arguments[0])
    if executable is None:
        raise AcceptanceError("build_tool_missing")
    completed = subprocess.run(
        [executable, *arguments[1:]],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise AcceptanceError("command_failed")
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
    process: subprocess.Popen[str],
    request_id: int,
    name: str,
    arguments: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    send(process, request(request_id, "tools/call", {"name": name, "arguments": arguments}))
    response = read_response(process, request_id)
    result = response.get("result")
    require(
        isinstance(result, dict)
        and result.get("isError") is False
        and isinstance(result.get("structuredContent"), dict),
        "tool_call_failed",
    )
    return result["structuredContent"], response


def call_rejected(
    process: subprocess.Popen[str],
    request_id: int,
    name: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    send(process, request(request_id, "tools/call", {"name": name, "arguments": arguments}))
    response = read_response(process, request_id)
    result = response.get("result")
    require(
        isinstance(result, dict)
        and result.get("isError") is True
        and "structuredContent" not in result,
        "negative_call_admitted",
    )
    return response


def mint_test_confirmation(
    *,
    secret: bytes,
    token_id: str,
    operation_id: str,
    actor_sha256: str,
    tenant_sha256: str,
    target_sha256: str,
    plan_sha256: str,
    issued_at_unix_seconds: int,
) -> str:
    """Model the trusted host authority; this helper is not part of the MCP server."""
    payload = {
        "schema_version": "hwpx-agent.confirmation/v1",
        "token_id": token_id,
        "operation_id": operation_id,
        "actor_sha256": actor_sha256,
        "tenant_sha256": tenant_sha256,
        "effect": "git_commit",
        "target_sha256": target_sha256,
        "plan_sha256": plan_sha256,
        "issued_at_unix_seconds": issued_at_unix_seconds,
        "expires_at_unix_seconds": issued_at_unix_seconds + 60,
        "user_confirmed": True,
    }
    encoded_payload = compact(payload)
    signature = hmac.new(secret, encoded_payload, hashlib.sha256).digest()
    return f"confirm_v1.{base64url(encoded_payload)}.{base64url(signature)}"


def run() -> dict[str, object]:
    source_commit, clean = tracked_identity()
    require(clean, "tracked_source_dirty")
    command(["cargo", "build", "-p", "local-companion-daemon", "--locked", "--offline"])
    command(["pnpm", "install", "--offline", "--frozen-lockfile"])
    command(["pnpm", "--filter", "@hwpx-agent/local-companion-mcp", "build"])
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    temporary_path: Path | None = None
    process: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="effect-", dir=run_dir) as temporary:
            temporary_path = Path(temporary).resolve()
            workspace = temporary_path / "workspace"
            workspace.mkdir()
            git = shutil.which("git")
            node = shutil.which("node")
            require(git is not None and Path(git).is_absolute(), "git_missing")
            require(node is not None and Path(node).is_file(), "node_missing")
            command([git, "init", "-b", "main"], cwd=workspace, timeout=30)
            command([git, "config", "user.name", "P17 Disposable Test"], cwd=workspace)
            command([git, "config", "user.email", "p17-test@example.invalid"], cwd=workspace)
            (workspace / "README.md").write_text("disposable\n", encoding="utf-8", newline="\n")
            command([git, "add", "--", "README.md"], cwd=workspace)
            command([git, "commit", "--no-gpg-sign", "-m", "initial"], cwd=workspace)
            initial_head = command([git, "rev-parse", "HEAD"], cwd=workspace).stdout.strip()
            (workspace / "output").mkdir()
            output_bytes = b"P17_MCP_APPROVED_SYNTHETIC_HWPX"
            (workspace / "output/result-01.hwpx").write_bytes(output_bytes)
            output_sha256 = sha256_bytes(output_bytes)
            (workspace / "unrelated.txt").write_text(
                "preserve staged entry\n", encoding="utf-8", newline="\n"
            )
            command([git, "add", "--", "unrelated.txt"], cwd=workspace)

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
            approval_state = temporary_path / "approval-state"
            secret = secrets.token_bytes(32)
            encoded_secret = base64url(secret)
            environment = {
                name: value
                for name in ("SystemRoot", "WINDIR")
                if (value := os.environ.get(name)) is not None
            }
            environment.update(
                {
                    "HWPX_AGENT_GIT_PROGRAM": str(Path(git).resolve()),
                    "HWPX_AGENT_APPROVAL_STATE_ROOT": str(approval_state),
                    "HWPX_AGENT_APPROVAL_SECRET": encoded_secret,
                }
            )
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
                        "clientInfo": {"name": "p17-approval-effect", "version": "1.0.0"},
                    },
                ),
            )
            initialized = read_response(process, 1)
            initialized_result = initialized.get("result")
            require(
                isinstance(initialized_result, dict)
                and initialized_result.get("protocolVersion") == MCP_PROTOCOL
                and initialized_result.get("serverInfo")
                == {"name": "hwpx-agent-local-companion", "version": "0.3.0"},
                "initialize",
            )
            send(process, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            send(process, request(2, "tools/list", {}))
            listed_response = read_response(process, 2)
            listed = listed_response.get("result")
            require(isinstance(listed, dict), "tools_list")
            tools = listed.get("tools")
            require(isinstance(tools, list) and len(tools) == 7, "tool_count")
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
                    "public_input_schema",
                )
            require(tuple(sorted(catalog)) == tuple(sorted(TOOLS)), "tool_names")
            require(
                catalog[PREPARE_TOOL].get("annotations")
                == {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "prepare_annotations",
            )
            require(
                catalog[EXECUTE_TOOL].get("annotations")
                == {
                    "readOnlyHint": False,
                    "destructiveHint": True,
                    "idempotentHint": False,
                    "openWorldHint": False,
                },
                "effect_annotations",
            )

            operation_id = "op_mcpapproved01"
            message = "Publish approved HWPX"
            prepare_arguments = {
                "workspace_id": "primary",
                "operation_id": operation_id,
                "output_id": "result-01",
                "expected_sha256": output_sha256,
                "message": message,
            }
            plan, plan_response = call_tool(process, 3, PREPARE_TOOL, prepare_arguments)
            approval = plan.get("approval")
            require(
                plan.get("executed") is False
                and plan.get("expected_head") == initial_head
                and plan.get("expected_head_reference") == "refs/heads/main"
                and isinstance(approval, dict)
                and approval.get("effect") == "git_commit"
                and isinstance(approval.get("target_sha256"), str)
                and isinstance(approval.get("plan_sha256"), str),
                "approval_plan",
            )
            actor_sha256 = sha256_bytes(b"p17 trusted test actor")
            tenant_sha256 = sha256_bytes(b"p17 trusted test tenant")
            requested_at = int(time.time())
            confirmation = mint_test_confirmation(
                secret=secret,
                token_id="cnf_mcpapproved01",
                operation_id=operation_id,
                actor_sha256=actor_sha256,
                tenant_sha256=tenant_sha256,
                target_sha256=approval["target_sha256"],
                plan_sha256=approval["plan_sha256"],
                issued_at_unix_seconds=requested_at,
            )
            effect_arguments = {
                **prepare_arguments,
                "actor_sha256": actor_sha256,
                "tenant_sha256": tenant_sha256,
                "requested_at_unix_seconds": requested_at,
                "confirmation_token": confirmation,
            }
            effect, effect_response = call_tool(process, 4, EXECUTE_TOOL, effect_arguments)
            require(
                effect.get("executed") is True
                and effect.get("previous_head") == initial_head
                and effect.get("updated_reference") == "refs/heads/main"
                and effect.get("output_sha256") == output_sha256
                and effect.get("target_sha256") == approval["target_sha256"]
                and effect.get("plan_sha256") == approval["plan_sha256"]
                and effect.get("index_synchronized") is True,
                "effect_receipt",
            )
            current_head = command([git, "rev-parse", "HEAD"], cwd=workspace).stdout.strip()
            require(current_head == effect.get("commit_oid") and current_head != initial_head, "head")
            parent = command([git, "rev-parse", "HEAD^"], cwd=workspace).stdout.strip()
            require(parent == initial_head, "parent")
            committed_output = subprocess.run(
                [git, "-C", str(workspace), "show", "HEAD:output/result-01.hwpx"],
                check=False,
                capture_output=True,
                timeout=30,
            )
            require(
                committed_output.returncode == 0 and committed_output.stdout == output_bytes,
                "committed_output",
            )
            staged = command(
                [git, "diff", "--cached", "--name-only"], cwd=workspace
            ).stdout.splitlines()
            require(staged == ["unrelated.txt"], "unrelated_index")
            replay_response = call_rejected(process, 5, EXECUTE_TOOL, effect_arguments)

            transcript = canonical(
                [initialized, listed_response, plan_response, effect_response, replay_response]
            )
            require(
                str(temporary_path) not in transcript
                and str(workspace) not in transcript
                and confirmation not in transcript
                and encoded_secret not in transcript
                and "P17_MCP_APPROVED_SYNTHETIC_HWPX" not in transcript
                and "session_token" not in transcript,
                "private_data_exposed",
            )
            require(process.stdin is not None, "stdin_missing")
            process.stdin.close()
            process.wait(timeout=10)
            require(process.returncode == 0, "bridge_exit")
            require(process.stderr is not None and process.stderr.read() == "", "bridge_stderr")
            process = None
            secret = b"\x00" * len(secret)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if temporary_path is not None and temporary_path.exists():
            shutil.rmtree(temporary_path)
    require(temporary_path is not None and not temporary_path.exists(), "cleanup")
    require(tracked_identity()[1], "tracked_source_changed")
    receipt = {
        "schema_version": "hwpx-agent.p17-mcp-approval-effect-check/v1",
        "run_id": run_id,
        "scope": "current_pc_disposable_local_stdio_mcp_confirmed_git_effect",
        "source_commit": source_commit,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "resources_cleaned": True,
        "actual_mcp_stdio": True,
        "actual_git_commit": True,
        "actual_trusted_host_ui": False,
        "actual_codex_client": False,
        "actual_personal_plugin": False,
        "actual_user_repository": False,
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
