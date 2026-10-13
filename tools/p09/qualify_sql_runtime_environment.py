"""Bounded read-only local Docker readiness; never starts/pulls a container or SQL."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

import conservative_maintenance as c
from bounded_process_progress import bounded_observation_run
from owned_sql_job import OwnedSQLJobProcess
from run_formula_issuer_registry_sql_checks import IMAGE
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher, LOCAL_DOCKER_HOST, local_docker_environment
from live_sql_evidence_reader import LiveSQLReader
from verify_issuer_sql_build_contract import SOURCES as CONTRACT_SOURCES
from sql_container_ownership import unique_object

HOST = LOCAL_DOCKER_HOST
SOURCES = CONTRACT_SOURCES+["tools/p09/qualify_sql_runtime_environment.py",
    "implementation/p09/source-archive/p09-149-pre-SQL-readiness-closed-image-failure/source-preimages.v1.json",
    "implementation/p09/evidence/p09-149-SQL-runtime-environment.run01.v1.json",
    "tools/p09/sql_container_ownership.py", "tools/p09/tests/test_sql_runtime_readiness.py",
    "implementation/p09/source-archive/p09-149-pre-server-version-readiness/source-preimages.v1.json"]

SERVER_FORMAT = '{"version":{{json .Server.Version}},"os":{{json .Server.Os}}}'


def commands(docker):
    # version uses ServerVersion; Linux 엔진 확인에 무거운 info/plugin 목록은 필요 없다.
    return [("server", [docker, "--host", HOST, "version", "--format", SERVER_FORMAT]),
        ("image", [docker, "--host", HOST, "image", "inspect", IMAGE, "--format", "{{json .Id}}"])]


def observation(result, kind):
    c.require(type(result.returncode) is int and isinstance(result.stdout, str) and isinstance(result.stderr, str)
        and len(result.stdout.encode("utf-8")) <= 16384 and len(result.stderr.encode("utf-8")) <= 16384,
        "SQL_ENVIRONMENT_OUTPUT_SCOPE")
    if kind == "image" and result.returncode != 0 and re.search(r"no such image", result.stderr, re.IGNORECASE):
        raise ValueError("SQL_ENVIRONMENT_FIXED_IMAGE_MISSING")
    c.require(result.returncode == 0, "SQL_ENVIRONMENT_READONLY_QUERY_FAILED")
    c.require(isinstance(result.stdout, str) and len(result.stdout.encode("utf-8")) <= 16384,
        "SQL_ENVIRONMENT_OUTPUT_SCOPE")
    try:
        value = json.loads(result.stdout, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        raise ValueError("SQL_ENVIRONMENT_JSON_INVALID") from None
    if kind == "server":
        c.require(isinstance(value, dict) and set(value) == {"version", "os"}
            and isinstance(value["version"], str)
            and re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?:[-+][A-Za-z0-9.-]{1,40})?", value["version"]),
            "SQL_ENVIRONMENT_SERVER_VERSION_SCOPE")
        c.require(value["os"] == "linux", "SQL_ENVIRONMENT_NOT_LOCAL_LINUX")
        return True  # Do not retain arbitrary daemon text or raw output.
    c.require(kind == "image" and isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value),
        "SQL_ENVIRONMENT_IMAGE_ID_SCOPE")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-runtime-environment.run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists()
        and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "SQL_ENVIRONMENT_FRESH_RECEIPT_REQUIRED")
    resources, started, reader = SQLRuntimeResources(), time.monotonic(), None
    row = {"schema_version": "hwpx-agent.p09-SQL-runtime-environment/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "local_linux_engine_only": True, "server_responded": False, "linux_engine_confirmed": False,
        "fixed_image_present": False, "image_id": None, "owned_host_job_profiles": [],
        "last_query_kind": None, "last_query_exit_code": None,
        "image_presence_state": "NOT_QUERIED", "query_observations": [],
        "container_created_or_pulled": False, "actual_SQL_or_native_product_executed": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "product_complete": False, "P09_gate": "OPEN"}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        docker = shutil.which("docker")
        c.require(docker is not None and Path(docker).is_absolute() and Path(docker).is_file()
            and not Path(docker).is_symlink() and not Path(docker).is_junction(), "SQL_ENVIRONMENT_DOCKER_MISSING_OR_LINK")
        resources.start()
        for kind, command in commands(docker):
            row["last_query_kind"] = kind
            row["last_query_exit_code"] = None
            query_started = time.monotonic()
            query = {"kind": kind, "outcome": "UNKNOWN", "exit_code": None, "error_code": None, "wall_seconds": None}
            row["query_observations"].append(query)
            if kind == "image":
                row["image_presence_state"] = "UNKNOWN"
            holders = []
            def checkpoint():
                c.require(time.monotonic()-started <= 30, "STOP_SQL_ENVIRONMENT_SCOPE_TIME")
                resources.checkpoint_io()
            def factory(actual, **kwargs):
                c.require(actual == command and kwargs.get("cwd") == c.ROOT
                    and kwargs.get("stdin") == kwargs.get("stdout") == kwargs.get("stderr") == subprocess.PIPE
                    and kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,
                    "SQL_ENVIRONMENT_LAUNCH_SCOPE")
                owned = OwnedSQLJobProcess(actual, windows=resources.windows, allowed_executables=[docker],
                    cwd=c.ROOT, checkpoint=checkpoint, env=local_docker_environment())
                holders.append(owned)
                return owned
            try:
                result = bounded_observation_run(command, cwd=c.ROOT, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS, process_factory=factory)
            except subprocess.TimeoutExpired:
                query.update(outcome="TIMED_OUT", error_code="SQL_ENVIRONMENT_QUERY_TIMEOUT")
                raise ValueError("SQL_ENVIRONMENT_QUERY_TIMEOUT") from None
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                query.update(outcome="FAILED", error_code="SQL_ENVIRONMENT_QUERY_OPERATION_FAILED")
                if hasattr(error, "owned_sql_job_profile") and not holders:
                    row["owned_host_job_profiles"].append(dict(error.owned_sql_job_profile))
                raise ValueError("SQL_ENVIRONMENT_QUERY_OPERATION_FAILED") from None
            finally:
                query["wall_seconds"] = round(time.monotonic()-query_started, 4)
                row["owned_host_job_profiles"].extend(dict(owned.profile) for owned in holders)
            c.require(len(holders) == 1 and holders[0].profile.get("cleanup_confirmed") is True
                and holders[0].profile.get("owned_tree_empty") is True and holders[0].profile.get("job_handle_closed") is True,
                "SQL_ENVIRONMENT_OWNED_CLEANUP_NOT_CONFIRMED")
            row["last_query_exit_code"] = result.returncode
            query["exit_code"] = result.returncode
            try:
                value = observation(result, kind)
            except ValueError as error:
                query.update(outcome="FAILED", error_code=str(error))
                if kind == "image" and str(error) == "SQL_ENVIRONMENT_FIXED_IMAGE_MISSING":
                    row["image_presence_state"] = "MISSING"
                    query["outcome"] = "MISSING"
                raise
            query["outcome"] = "ACCEPTED"
            if kind == "server":
                row["server_responded"] = value
                row["linux_engine_confirmed"] = value
            else:
                row["fixed_image_present"], row["image_id"] = True, value
                row["image_presence_state"] = "PRESENT"
        reader.finish()
        row["source_freeze_exact_after"] = True
        row["state"] = "PASS_LOCAL_SQL_RUNTIME_READINESS_ONLY_NOT_SQL_PRODUCT_OR_GATE"
    except (ValueError, OSError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "SQL_ENVIRONMENT_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_ENVIRONMENT_REDACTED_FAILURE"
        if row["error_code"] == "SQL_ENVIRONMENT_FIXED_IMAGE_MISSING":
            row["state"] = "INPUT_BLOCKED_FIXED_SQL_IMAGE_MISSING_NOT_SQL_OR_GATE"
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_host_job_profiles"].append(dict(error.owned_sql_job_profile))
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"] = "FAILED_NOT_ACCEPTED"
                row["final_freshness_error_code"] = "SQL_ENVIRONMENT_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "server_responded", "linux_engine_confirmed",
            "fixed_image_present", "resource_watcher_cleanup_confirmed", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
