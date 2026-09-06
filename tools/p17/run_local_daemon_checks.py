"""Run the current-PC P17-03 local daemon acceptance without Hangul or user files."""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/local-daemon-runs"
PROTOCOL_VERSION = "hwpx-agent.local-companion-private/v1"
CONFIG_VERSION = "hwpx-agent.local-companion-config/v1"
TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136"
CHECKS = (
    "clean_tracked_source",
    "locked_offline_binary_build",
    "authenticated_health_redacted",
    "wrong_session_rejected",
    "bounded_existing_file_admitted",
    "traversal_rejected",
    "new_output_name_admitted",
    "overwrite_rejected",
    "unknown_request_field_rejected",
    "graceful_eof_shutdown",
    "temporary_resources_cleaned",
)
SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "crates/local-companion-daemon/tests/binary_smoke.rs",
    "crates/local-companion-daemon/tests/sandbox.rs",
    "protocol/private/p17-local-daemon-v1.json",
    "implementation/p17/P17-03_LOCAL_DAEMON_V1.md",
    "tools/p17/run_local_daemon_checks.py",
    "tools/p17/tests/test_local_daemon_checks.py",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def command(arguments: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
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
        raise AcceptanceError("command_failed")
    return completed


def tracked_identity() -> tuple[str, bool]:
    commit = command(["git", "rev-parse", "HEAD"], timeout=15).stdout.strip()
    require(len(commit) == 40 and all(character in "0123456789abcdef" for character in commit), "commit")
    status = command(
        ["git", "status", "--porcelain", "--untracked-files=no"], timeout=15
    ).stdout
    return commit, status == ""


def request(request_id: str, token: str, method: str, params: object, **extra: object) -> dict[str, object]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "session_token": token,
        "method": method,
        "params": params,
        **extra,
    }


def canonical(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_response(value: object, request_id: str, ok: bool) -> dict[str, object]:
    require(isinstance(value, dict), "response_type")
    required = {"protocol_version", "request_id", "ok", "result" if ok else "error"}
    require(set(value) == required, "response_fields")
    require(
        value.get("protocol_version") == PROTOCOL_VERSION
        and value.get("request_id") == request_id
        and value.get("ok") is ok,
        "response_identity",
    )
    if ok:
        require(isinstance(value.get("result"), dict), "response_result")
    else:
        require(value.get("error") == "request_rejected", "response_error")
    return value


def binary_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    path = ROOT / "target" / "debug" / f"local-companion-daemon{suffix}"
    require(path.is_file(), "binary_missing")
    return path


def run() -> dict[str, object]:
    commit, clean = tracked_identity()
    require(clean, "tracked_source_dirty")
    command(
        [
            "cargo",
            "build",
            "-p",
            "local-companion-daemon",
            "--locked",
            "--offline",
        ]
    )
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "run_exists")
    run_dir.mkdir(parents=True)
    token = secrets.token_urlsafe(32)
    require(len(token) == 43, "token_shape")
    temporary_path: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="fixture-", dir=run_dir) as temporary:
            temporary_path = Path(temporary).resolve()
            workspace = temporary_path / "workspace"
            (workspace / "input").mkdir(parents=True)
            (workspace / "output").mkdir()
            (workspace / "input" / "fixture.hwpx").write_bytes(b"bounded")
            (workspace / "output" / "existing.hwpx").write_bytes(b"existing")
            config_path = temporary_path / "config.json"
            config_path.write_text(
                canonical(
                    {
                        "schema_version": CONFIG_VERSION,
                        "target_profile": TARGET_PROFILE,
                        "automation_mode": "disabled",
                        "network_mode": "disabled",
                        "max_file_bytes": 1_048_576,
                        "workspaces": [{"id": "primary", "root": str(workspace)}],
                    }
                ),
                encoding="utf-8",
            )
            wrong_token = ("B" if token[0] != "B" else "A") + token[1:]
            requests = [
                request("health", token, "health", {}),
                request("wrong-session", wrong_token, "health", {}),
                request(
                    "read-existing",
                    token,
                    "authorize_path",
                    {
                        "workspace_id": "primary",
                        "relative_path": "input/fixture.hwpx",
                        "access": "read_existing",
                    },
                ),
                request(
                    "traversal",
                    token,
                    "authorize_path",
                    {
                        "workspace_id": "primary",
                        "relative_path": "../escape.hwpx",
                        "access": "read_existing",
                    },
                ),
                request(
                    "create-output",
                    token,
                    "authorize_path",
                    {
                        "workspace_id": "primary",
                        "relative_path": "output/new.hwpx",
                        "access": "create_output",
                    },
                ),
                request(
                    "overwrite",
                    token,
                    "authorize_path",
                    {
                        "workspace_id": "primary",
                        "relative_path": "output/existing.hwpx",
                        "access": "create_output",
                    },
                ),
                request("unknown-field", token, "health", {}, extra=True),
            ]
            environment = {
                "HWPX_AGENT_LOCAL_SESSION_TOKEN": token,
                **{
                    name: value
                    for name in ("SystemRoot", "WINDIR")
                    if (value := os.environ.get(name)) is not None
                },
            }
            process = subprocess.run(
                [str(binary_path()), "--config", str(config_path)],
                cwd=ROOT,
                env=environment,
                input="".join(f"{canonical(value)}\n" for value in requests),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=15,
                check=False,
            )
            require(process.returncode == 0 and process.stderr == "", "daemon_exit")
            lines = process.stdout.splitlines()
            require(len(lines) == len(requests), "response_count")
            responses = [json.loads(line) for line in lines]
            health = validate_response(responses[0], "health", True)
            require(
                health["result"]
                == {
                    "status": "ready",
                    "target_profile": TARGET_PROFILE,
                    "automation_enabled": False,
                    "network_enabled": False,
                    "workspace_count": 1,
                    "config_sha256": health["result"].get("config_sha256"),
                }
                and isinstance(health["result"].get("config_sha256"), str)
                and len(health["result"]["config_sha256"]) == 64,
                "health",
            )
            validate_response(responses[1], "wrong-session", False)
            read = validate_response(responses[2], "read-existing", True)
            require(read["result"].get("size_bytes") == 7, "read_existing")
            validate_response(responses[3], "traversal", False)
            output = validate_response(responses[4], "create-output", True)
            require(output["result"].get("path_kind") == "creatable_output", "create_output")
            validate_response(responses[5], "overwrite", False)
            validate_response(responses[6], "invalid", False)
            combined = process.stdout + process.stderr
            require(token not in combined and str(temporary_path) not in combined, "redaction")
    finally:
        if temporary_path is not None and temporary_path.exists():
            shutil.rmtree(temporary_path)
    resources_cleaned = temporary_path is not None and not temporary_path.exists()
    require(resources_cleaned, "cleanup")
    final_clean = tracked_identity()[1]
    require(final_clean, "tracked_source_changed")
    receipt = {
        "schema_version": "hwpx-agent.p17-local-daemon-check/v1",
        "run_id": run_id,
        "scope": "current_pc_synthetic_workspace_local_daemon_only",
        "source_commit": commit,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "tracked_clean": True,
        "resources_cleaned": True,
        "actual_hangul": False,
        "actual_codex_plugin": False,
        "network_used": False,
    }
    # Write the evidence bytes explicitly. Path.write_text translates newlines on
    # Windows, which would turn the canonical LF terminator into CRLF.
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
