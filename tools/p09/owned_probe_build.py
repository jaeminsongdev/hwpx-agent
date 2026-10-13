"""P149 issuer compiler supervisor; original PS source/protected guards remain authoritative.

출력은 전부 상한 내에서만 수집한다. 초과는 실패이며 잘라낸 로그로 PASS하지 않는다.
SQL/native 제품 검증이나 역사적 source pin의 갱신을 수행하지 않는다.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
from bounded_process_progress import BoundedProcessCapture, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess
from sql_percentage_resources import PercentageResources

TARGET = c.ROOT / "target/p09-121-resource-optimized"
EXAMPLE = "formula_issuer_product_postgres_probe"
MUTEX = "Local\\HwpxAgentP149ConservativeMaintenance"
SOURCES = ["Cargo.toml", "Cargo.lock", "tools/p09/owned_probe_build.py",
    "tools/p09/conservative_maintenance.py", "tools/p09/audit_evidence_io.py",
    "tools/p09/bounded_process_progress.py", "tools/p09/owned_sql_job.py",
    "tools/p09/sql_percentage_resources.py", "tools/p09/build_formula_issuer_product_probe.ps1",
    "tools/p09/tests/test_owned_probe_build.py", "tools/p09/verify_owned_probe_build_light.py",
    "implementation/p09/source-archive/p09-149-pre-compiler-acceptance-cleanup-repair/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-owned-probe-build/source-preimages.v1.json"]


def closed_error(error):
    code = str(error) if isinstance(error, ValueError) else "P149_COMPILER_OPERATION_FAILED"
    return code if re.fullmatch(r"(?:P149_COMPILER_|OWNED_SQL_|STOP_|DEFERRED_|MAINTENANCE_)[A-Z_]+|owned_pipe_[a-z_]+|live_progress_[a-z_]+|resource_stop", code) \
        else "P149_COMPILER_OPERATION_FAILED"


def paths(variant, receipt):
    c.require(isinstance(variant, str) and re.fullmatch(r"r[1-9][0-9]{0,5}", variant), "P149_COMPILER_VARIANT_SCOPE")
    expected = TARGET / f"p149-issuer-product-build-supervisor-{variant}.json"
    destination = c.ROOT / receipt
    c.require(destination.absolute() == expected.absolute(), "P149_COMPILER_RECEIPT_SCOPE")
    for directory in (c.ROOT, c.ROOT / "target", TARGET):
        c.require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(), "P149_COMPILER_TARGET_LINK_OR_MISSING")
    executable = TARGET / f"debug/examples/{EXAMPLE}-p143-{variant}.exe"
    c.require(not destination.exists() and not destination.is_symlink()
        and not executable.exists() and not executable.is_symlink(), "P149_COMPILER_FRESH_OUTPUT_REQUIRED")
    return destination, executable


def build_arguments(cargo, variant):
    return [cargo, "rustc", "-p", "hwpx-agent-cli", "--example", EXAMPLE, "--profile", "dev",
        "--locked", "--offline", "--jobs", "1", "--target-dir", str(TARGET),
        "--message-format=json", "--", "-C", f"extra-filename=-p143-{variant}"]


def build_environment():
    env = dict(os.environ)
    env.update(CARGO_PROFILE_DEV_OPT_LEVEL="1", CARGO_PROFILE_DEV_DEBUG="line-tables-only",
        CARGO_PROFILE_DEV_DEBUG_ASSERTIONS="true", CARGO_PROFILE_DEV_OVERFLOW_CHECKS="true",
        CARGO_PROFILE_DEV_CODEGEN_UNITS="16", CARGO_INCREMENTAL="0", RUSTUP_AUTO_INSTALL="0")
    return env


def parse_cargo(output):
    c.require(isinstance(output, str) and len(output.encode("utf-8")) <= MAX_OUTPUT, "P149_COMPILER_OUTPUT_BUDGET")
    finished, profiles, diagnostics = [], [], []
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError("P149_COMPILER_JSON_INVALID") from None
        c.require(isinstance(item, dict) and item.get("reason") in
            {"build-finished", "compiler-artifact", "compiler-message", "build-script-executed"}, "P149_COMPILER_MESSAGE_SCOPE")
        if item["reason"] == "build-finished":
            c.require(type(item.get("success")) is bool, "P149_COMPILER_FINISH_SCOPE")
            finished.append(item["success"])
        elif item["reason"] == "compiler-artifact" and item.get("target", {}).get("name") == EXAMPLE:
            raw = item.get("profile", {})
            profile = {key: raw.get(key) for key in ("opt_level", "debuginfo", "debug_assertions", "overflow_checks", "test")}
            c.require(profile["opt_level"] == "1" and type(profile["debug_assertions"]) is bool
                and profile["debug_assertions"] and profile["overflow_checks"] is True
                and profile["test"] is False and profile["debuginfo"] in (0, 1, 2, "line-tables-only"), "P149_COMPILER_PROFILE_SCOPE")
            profiles.append(profile)
        elif item["reason"] == "compiler-message":
            message = item.get("message", {})
            if message.get("level") in ("error", "warning"):
                c.require(len(diagnostics) < 32, "P149_COMPILER_DIAGNOSTIC_BUDGET")
                raw_code = (message.get("code") or {}).get("code")
                code = raw_code if isinstance(raw_code, str) and re.fullmatch(r"[A-Za-z_0-9]{1,64}", raw_code) else None
                # No raw message, rendered output, arbitrary span/path, or dependency values.
                diagnostics.append({"level": message["level"], "code": code})
    c.require(len(finished) == 1 and len(profiles) == 1, "P149_COMPILER_TERMINAL_INVENTORY")
    return {"build_finished_success": finished[0], "catalog_profile": profiles[0], "diagnostics": diagnostics}


def compile_owned(resources, cargo, variant, maximum_seconds, *, process_factory=OwnedSQLJobProcess,
        capture_factory=BoundedProcessCapture, clock=time.monotonic):
    c.require(type(maximum_seconds) is int and 30 <= maximum_seconds <= 600, "P149_COMPILER_DURATION_SCOPE")
    result = {"exit_code": None, "build_finished_success": False, "catalog_profile": None,
        "diagnostics": [], "stop_reason": None, "owned_job_profile": None, "compiler_started": False,
        "cleanup_confirmed": False, "stdout_bytes": None, "stderr_bytes": None}
    owned = capture = None
    try:
        owned = process_factory(build_arguments(cargo, variant), windows=resources.windows,
            allowed_executables=[cargo], cwd=c.ROOT, checkpoint=resources.checkpoint_io, env=build_environment())
        result["compiler_started"] = owned.profile["target_authorized"]
        capture = capture_factory(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        deadline = clock() + maximum_seconds
        while True:
            resources.checkpoint_io()
            remaining = deadline-clock()
            c.require(remaining > 0, "STOP_COMPILER_DURATION_LIMIT")
            try:
                output, errors = capture.communicate(timeout=min(.5, remaining))
                owned.observe()  # Fast completion must also check whole-system and Job resources.
                result["exit_code"] = owned.returncode
                result.update(parse_cargo(output))
                result.update(stdout_bytes=len(output.encode("utf-8")), stderr_bytes=len(errors.encode("utf-8")))
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        result["stop_reason"] = closed_error(error)
        if hasattr(error, "owned_sql_job_profile"):
            result["owned_job_profile"] = dict(error.owned_sql_job_profile)
    except KeyboardInterrupt:
        result["stop_reason"] = "P149_COMPILER_INTERRUPTED"
    finally:
        failures = []
        if owned is not None:
            try:
                owned.kill()  # Kill descendants even when the broker itself has already exited.
                owned.wait(timeout=2)
            except (ValueError, OSError, subprocess.SubprocessError):
                failures.append("P149_COMPILER_TERMINATE_OR_WAIT_FAILED")
        try:
            if capture is not None:
                capture.close()
        except (ValueError, OSError):
            failures.append("P149_COMPILER_PIPE_CLEANUP_FAILED")
        finally:
            if owned is not None:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError):
                    failures.append("P149_COMPILER_JOB_CLEANUP_FAILED")
                result["owned_job_profile"] = dict(owned.profile)
        result["cleanup_confirmed"] = not failures and result["owned_job_profile"] is not None \
            and result["owned_job_profile"].get("cleanup_confirmed") is True
        if failures:
            result["stop_reason"] = failures[0]
    return result


def accepted(result):
    profile = result.get("owned_job_profile") or {}
    return result.get("stop_reason") is None and result.get("exit_code") == 0 \
        and result.get("build_finished_success") is True and (result.get("catalog_profile") or {}).get("test") is False \
        and not result.get("diagnostics") and result.get("cleanup_confirmed") is True \
        and profile.get("cleanup_confirmed") is True \
        and profile.get("owned_tree_empty") is True and profile.get("job_handle_closed") is True \
        and (profile.get("limits_readback") or {}).get("verified") is True \
        and profile.get("job_assigned") is True and profile.get("target_authorized") is True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--maximum-seconds", type=int, choices=range(30, 601), default=600)
    args = parser.parse_args()
    c.require(Path.cwd().resolve() == c.ROOT, "P149_COMPILER_WRONG_ROOT")
    destination, _ = paths(args.variant, args.receipt)
    resources = PercentageResources()
    mutex = None
    lock_owned = False
    row = {"schema_version": "hwpx-agent.p09-owned-probe-build/v1", "state": "NOT_ACCEPTED_STOP_OR_FAILURE",
        "helper_source_freeze": [], "helper_source_freeze_exact_after": False,
        "compiler_started": False, "stop_reason": None, "samples": resources.samples,
        "exit_code": None, "build_finished_success": False, "catalog_profile": None,
        "diagnostics": [], "owned_job_profile": None, "cleanup_confirmed": False,
        "logical_cpu_limit": 1, "affinity_mask": resources.windows.mask, "priority": "BelowNormal",
        "cargo_jobs": 1, "output_limit_bytes_per_stream": MAX_OUTPUT, "maximum_seconds": args.maximum_seconds,
        "dev_opt_level": 1, "dev_codegen_units": 16, "debug_assertions": True, "overflow_checks": True,
        "aggregate_job_memory_hard_percent": 8, "aggregate_job_memory_stop_percent": 7,
        "actual_DB_executed": False, "P09_gate": "OPEN", "product_complete": False}
    started = time.monotonic()
    reader = None
    try:
        ctypes.set_last_error(0)
        mutex = resources.windows.k.CreateMutexW(None, True, MUTEX)
        duplicate = ctypes.get_last_error() == 183
        c.require(mutex, "MAINTENANCE_LOCK_FAILED")
        lock_owned = not duplicate
        c.require(lock_owned, "MAINTENANCE_ALREADY_RUNNING")
        resources.admit()
        def checkpoint():
            c.require(time.monotonic()-started <= args.maximum_seconds+60, "STOP_COMPILER_TOTAL_SCOPE_TIME")
            resources.checkpoint_io()
        reader = AuditEvidenceReader(c.ROOT, checkpoint)
        row["helper_source_freeze"] = [reader.pin(name) for name in SOURCES]
        cargo = shutil.which("cargo")
        c.require(cargo is not None, "P149_COMPILER_CARGO_MISSING")
        resources.start()
        row.update(compile_owned(resources, cargo, args.variant, args.maximum_seconds))
        reader.finish()
        row["helper_source_freeze_exact_after"] = True
        row["helper_input_IO"] = {"read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
            "final_fresh_hashes": reader.final_fresh_hashes, "bound_inputs": len(reader.snapshots)}
        if accepted(row):
            row["state"] = "PASS_SUPERVISED_COMPILER_ONLY_NOT_SOURCE_DB_OR_GATE"
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        row["stop_reason"] = closed_error(error)
    except KeyboardInterrupt:
        row["stop_reason"] = "P149_COMPILER_INTERRUPTED"
    finally:
        resources.done.set()
        if resources.thread.ident is not None:
            resources.thread.join(2)
            if resources.thread.is_alive():
                row["stop_reason"] = "P149_COMPILER_WATCHER_CLEANUP_FAILED"
        if resources.stop.is_set():
            row["stop_reason"] = closed_error(ValueError(resources.reason or "resource_stop"))
        if mutex is not None:
            if lock_owned and not resources.windows.k.ReleaseMutex(mutex):
                row["stop_reason"] = "P149_COMPILER_MUTEX_RELEASE_FAILED"
            if not resources.windows.k.CloseHandle(mutex):
                row["stop_reason"] = "P149_COMPILER_MUTEX_CLOSE_FAILED"
        if row["stop_reason"]:
            row["state"] = "NOT_ACCEPTED_STOP_OR_FAILURE"
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, ensure_ascii=False, indent=2)
        print(json.dumps({key: row.get(key) for key in ("state", "stop_reason", "compiler_started", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
