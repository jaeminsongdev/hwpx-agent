"""Reuse a pinned local image; reject downloads without backend containment.

CLI Job 제한은 Docker daemon/WSL 제한이 아니다. 기존 이미지 확인은 허용하지만
백엔드 containment 구현 전 다운로드를 거부한다. 과거 pull supervisor 검사는
보존하며, 이 차단을 준비 완료/프리즈 해결/제품 PASS로 해석하지 않는다.
"""
import argparse
import ctypes
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import owned_probe_build as compiler
from bounded_process_progress import BoundedProcessCapture, bounded_observation_run, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess
from run_formula_issuer_registry_sql_checks import IMAGE
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher, LOCAL_DOCKER_HOST, local_docker_environment
from live_sql_evidence_reader import LiveSQLReader
from verify_issuer_sql_build_contract import SOURCES as CONTRACT_SOURCES

POST_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-image-post-stop-observation/source-preimages.v1.json"
BACKEND_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-uncontained-backend-pull-guard/source-preimages.v1.json"
SOURCES = CONTRACT_SOURCES+["tools/p09/prepare_pinned_sql_image.py", "tools/p09/tests/test_prepare_pinned_sql_image.py", POST_ARCHIVE, BACKEND_ARCHIVE]
MAX_PULL_SECONDS = 120
MAX_RAM_HEADROOM_DROP_POINTS = 3
MAX_COMMIT_GROWTH_POINTS = 2
MAX_POST_PULL_SECONDS = 30
POST_STABLE_SAMPLES = 3
POST_MAX_DELTA_POINTS = 0.25


def observe_post_pull_host(resources, *, clock=time.monotonic, sleep=time.sleep):
    """기존 watcher의 새 완료 표본만 관측한다. backend 종료 증명은 아니다."""
    result = {"host_growth_stabilized": False, "backend_quiescence_confirmed": None,
        "maximum_seconds": MAX_POST_PULL_SECONDS, "samples": [], "error_code": None}
    started, seen, stable, previous = clock(), None, 0, None
    try:
        for _ in range(64):
            now = clock()
            c.require(type(now) in (int, float) and math.isfinite(now) and now >= started,
                "SQL_IMAGE_POST_CLOCK_INVALID")
            c.require(now-started <= MAX_POST_PULL_SECONDS, "SQL_IMAGE_POST_NOT_STABILIZED")
            resources._check_observation_freshness()
            c.require(not resources.stop.is_set(), resources.reason or "SQL_IMAGE_POST_RESOURCE_STOP")
            completed = resources.last_sample_at
            if completed != seen:
                sample = resources.samples[-1]
                row = {key: sample[key] for key in
                    ("system_cpu_percent", "available_ram_percent", "commit_used_percent")}
                c.require(all(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100
                    for value in row.values()), "SQL_IMAGE_POST_SAMPLE_INVALID")
                result["samples"].append(row)
                steady = previous is not None and all(abs(row[key]-previous[key]) <= POST_MAX_DELTA_POINTS
                    for key in ("available_ram_percent", "commit_used_percent"))
                stable = stable+1 if steady else 1
                previous, seen = row, completed
                if stable >= POST_STABLE_SAMPLES:
                    result["host_growth_stabilized"] = True
                    break
            sleep(0.5)
        c.require(result["host_growth_stabilized"], "SQL_IMAGE_POST_NOT_STABILIZED")
    except (ValueError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, ValueError) else "SQL_IMAGE_POST_OBSERVATION_FAILED"
        result["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_IMAGE_POST_REDACTED_FAILURE"
    result["elapsed_seconds"] = round(clock()-started, 4)
    return result


def pull_arguments(docker):
    return [docker, "--host", LOCAL_DOCKER_HOST, "image", "pull", "--platform", "linux/amd64", IMAGE]


def growth_checkpoint(resources, baseline):
    resources.checkpoint_io()
    row = resources.samples[-1]
    c.require(baseline["available_ram_percent"]-row["available_ram_percent"] <= MAX_RAM_HEADROOM_DROP_POINTS,
        "STOP_SQL_IMAGE_HOST_RAM_GROWTH")
    c.require(row["commit_used_percent"]-baseline["commit_used_percent"] <= MAX_COMMIT_GROWTH_POINTS,
        "STOP_SQL_IMAGE_HOST_COMMIT_GROWTH")


def require_backend_pull_containment():
    # 현재 local daemon에 적용되는 검증된 hard limit 계약이 없다. bool/env/CLI
    # opt-in으로 우회하지 않는다. future 구현은 실제 backend readback가 필요하다.
    raise ValueError("SQL_IMAGE_BACKEND_CONTAINMENT_UNAVAILABLE")


def pull_owned(resources, docker, baseline, *, process_factory=OwnedSQLJobProcess,
        capture_factory=BoundedProcessCapture, clock=time.monotonic):
    owned = capture = None
    row = {"exit_code": None, "error_code": None, "owned_job_profile": None,
        "stdout_bytes": None, "stderr_bytes": None, "cleanup_confirmed": False,
        "pull_authorized": False, "backend_pull_guard_rejected": False}
    try:
        require_backend_pull_containment()
        row["pull_authorized"] = True
        owned = process_factory(pull_arguments(docker), windows=resources.windows,
            allowed_executables=[docker], cwd=c.ROOT, env=local_docker_environment(),
            checkpoint=lambda: growth_checkpoint(resources, baseline))
        capture = capture_factory(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        deadline = clock()+MAX_PULL_SECONDS
        while True:
            growth_checkpoint(resources, baseline)
            remaining = deadline-clock()
            c.require(remaining > 0, "STOP_SQL_IMAGE_PULL_DURATION")
            try:
                output, errors = capture.communicate(timeout=min(.25, remaining))
                owned.observe()
                row.update(exit_code=owned.returncode, stdout_bytes=len(output.encode("utf-8")),
                    stderr_bytes=len(errors.encode("utf-8")))
                c.require(owned.returncode == 0, "SQL_IMAGE_PULL_REJECTED")
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
    except (ValueError, OSError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "SQL_IMAGE_PULL_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_IMAGE_PULL_REDACTED_FAILURE"
        row["backend_pull_guard_rejected"] = row["error_code"] == "SQL_IMAGE_BACKEND_CONTAINMENT_UNAVAILABLE"
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_job_profile"] = dict(error.owned_sql_job_profile)
    finally:
        failures = []
        if owned is not None:
            try:
                owned.kill()
                owned.wait(timeout=2)
            except (ValueError, OSError, subprocess.SubprocessError):
                failures.append("SQL_IMAGE_PULL_TERMINATE_FAILED")
        try:
            if capture is not None:
                capture.close()
        except (ValueError, OSError):
            failures.append("SQL_IMAGE_PULL_PIPE_CLOSE_FAILED")
        finally:
            if owned is not None:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError):
                    failures.append("SQL_IMAGE_PULL_JOB_CLOSE_FAILED")
                row["owned_job_profile"] = dict(owned.profile)
        profile = row["owned_job_profile"] or {}
        row["cleanup_confirmed"] = not failures and all(profile.get(key) is True for key in
            ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed"))
        if failures:
            row["error_code"] = failures[0]
    return row


def identity(output):
    c.require(isinstance(output, str) and len(output.encode("utf-8")) <= 16384, "SQL_IMAGE_IDENTITY_OUTPUT_SCOPE")
    try:
        first, second = output.strip().split("|")
        image_id, digests = json.loads(first), json.loads(second)
    except (ValueError, TypeError):
        raise ValueError("SQL_IMAGE_IDENTITY_JSON_INVALID") from None
    digest = IMAGE.split("@", 1)[1]
    c.require(isinstance(image_id, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", image_id)
        and isinstance(digests, list) and len(digests) <= 32 and any(value in
            {"postgres@"+digest, "docker.io/library/postgres@"+digest} for value in digests),
        "SQL_IMAGE_PINNED_DIGEST_MISSING")
    return image_id


def cached_identity(result, profiles):
    c.require(len(profiles) == 1 and all(profiles[0].get(key) is True for key in
        ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed")),
        "SQL_IMAGE_IDENTITY_QUERY_OR_CLEANUP_FAILED")
    if result.returncode == 0:
        return identity(result.stdout)
    c.require(result.returncode == 1 and isinstance(result.stderr, str)
        and len(result.stderr.encode("utf-8")) <= 16384 and re.search(
            r"(?:No such image|image[^\r\n]{0,256}not found)", result.stderr, re.IGNORECASE),
        "SQL_IMAGE_IDENTITY_QUERY_FAILED")
    return None


def inspect_owned_local_image(resources, docker, baseline):
    holders = []
    command = [docker, "--host", LOCAL_DOCKER_HOST, "image", "inspect", IMAGE,
        "--format", "{{json .Id}}|{{json .RepoDigests}}"]
    def factory(actual, **kwargs):
        c.require(actual == command and kwargs.get("cwd") == c.ROOT, "SQL_IMAGE_IDENTITY_COMMAND_SCOPE")
        owned = OwnedSQLJobProcess(actual, windows=resources.windows, allowed_executables=[docker],
            cwd=c.ROOT, env=local_docker_environment(), checkpoint=lambda: growth_checkpoint(resources, baseline))
        holders.append(owned)
        return owned
    try:
        result = bounded_observation_run(command, cwd=c.ROOT, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS, process_factory=factory)
        profiles = [dict(owned.profile) for owned in holders]
        return cached_identity(result, profiles), profiles
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        error.image_query_owned_profiles = [dict(owned.profile) for owned in holders]
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    kind = "light" if args.check else "actual"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-pinned-SQL-image.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "SQL_IMAGE_FRESH_RECEIPT_REQUIRED")
    resources, started, reader, mutex, lock_owned = SQLRuntimeResources(), time.monotonic(), None, None, False
    row = {"schema_version": "hwpx-agent.p09-pinned-SQL-image/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "pull_executed": False,
        "fixed_image_present_after": False, "image_id": None, "owned_host_job_profiles": [],
        "docker_daemon_hard_limits_enforced": False, "RAM_headroom_drop_stop_points": 3,
        "commit_growth_stop_points": 2, "maximum_pull_seconds": MAX_PULL_SECONDS,
        "mutex_cleanup_confirmed": False, "actual_SQL_or_native_product_executed": False,
        "container_created": False, "system_or_Defender_or_WSL_settings_changed": False,
        "new_git_started": False, "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    row["post_pull_host_observation"] = None
    row["cached_image_inspect_executed"] = False
    row["backend_pull_guard_rejected"] = False
    try:
        ctypes.set_last_error(0)
        mutex = resources.windows.k.CreateMutexW(None, True, compiler.MUTEX)
        duplicate = ctypes.get_last_error() == 183
        c.require(mutex, "SQL_IMAGE_MUTEX_FAILED")
        lock_owned = not duplicate
        c.require(lock_owned, "SQL_IMAGE_ALREADY_RUNNING")
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.check:
            from tests.test_prepare_pinned_sql_image import PreparePinnedSQLImageTests
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_IMAGE_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_IMAGE_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(
                    unittest.defaultTestLoader.loadTestsFromTestCase(PreparePinnedSQLImageTests))
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 20 and checked.wasSuccessful() and not checked.skipped, "SQL_IMAGE_LIGHT_TEST_FAILED")
        else:
            c.require(all(shutil.disk_usage(path).free >= 5*1024**3 for path in ("C:\\", "D:\\")), "SQL_IMAGE_DISK_HEADROOM")
            baseline = dict(resources.samples[-1])
            c.require(baseline["available_ram_percent"] >= 20, "SQL_IMAGE_INSUFFICIENT_HOST_HEADROOM")
            row["baseline"] = baseline
            docker = shutil.which("docker")
            c.require(docker and Path(docker).is_absolute() and Path(docker).is_file()
                and not Path(docker).is_symlink() and not Path(docker).is_junction(), "SQL_IMAGE_DOCKER_MISSING_OR_LINK")
            resources.start()
            print("P149_PINNED_SQL_IMAGE_PHASE:bounded_cached_inspect", flush=True)
            row["cached_image_inspect_executed"] = True
            image_id, profiles = inspect_owned_local_image(resources, docker, baseline)
            row["owned_host_job_profiles"].extend(profiles)
            if image_id is None:
                pulled = pull_owned(resources, docker, baseline)
                row["pull_result"] = pulled
                row["pull_executed"] = pulled["pull_authorized"]
                row["backend_pull_guard_rejected"] = pulled["backend_pull_guard_rejected"]
                c.require(False, pulled["error_code"] or "SQL_IMAGE_PREPARATION_UNAVAILABLE")
            row["image_id"] = image_id
            row["fixed_image_present_after"] = True
        reader.finish()
        row["source_freeze_exact_after"] = True
        row["state"] = "PASS_PINNED_SQL_IMAGE_SOURCE_MOCK_ONLY_NOT_PULL_SQL_OR_GATE" if args.check else \
            "PASS_PINNED_LOCAL_SQL_IMAGE_PREPARATION_ONLY_NOT_SQL_PRODUCT_OR_GATE"
    except (ValueError, OSError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["owned_host_job_profiles"].extend(getattr(error, "image_query_owned_profiles", []))
        code = str(error) if isinstance(error, ValueError) else "SQL_IMAGE_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_IMAGE_REDACTED_FAILURE"
    finally:
        # 원래 실패를 보존하며 자원이 허용하는 경우만 closing freshness를 확인한다.
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["final_freshness_error_code"] = "SQL_IMAGE_FINAL_FRESHNESS_FAILED"
                row["state"] = "FAILED_NOT_ACCEPTED"
        finish_watcher(resources, row)
        clean = True
        if mutex is not None:
            if lock_owned and not resources.windows.k.ReleaseMutex(mutex):
                clean = False
            if not resources.windows.k.CloseHandle(mutex):
                clean = False
        row["mutex_cleanup_confirmed"] = clean
        if not clean or resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests",
            "pull_executed", "fixed_image_present_after", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
