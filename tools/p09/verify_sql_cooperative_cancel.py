"""Scoped cancel mocks and actual admission/runtime-watcher cancellation, no SQL."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import sql_cooperative_cancel as subject
from bounded_process_progress import BoundedProcessCapture, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_sql_call_accounting import SOURCES as ACCOUNTING_SOURCES, fixture_paths, MISSING_BUILD, FIXTURE_RECEIPTS
from sql_call_accounting import account_driver_call

SELF = "tools/p09/verify_sql_cooperative_cancel.py"
READY = b"P149_CANCEL_READY:runtime_watcher\n"
SOURCES = list(dict.fromkeys(ACCOUNTING_SOURCES+[SELF, "tools/p09/sql_cooperative_cancel.py",
    "tools/p09/tests/test_sql_cooperative_cancel.py",
    "implementation/p09/source-archive/p09-149-pre-cooperative-cancel-authority-redaction-repair/source-preimages.v1.json"]))


def runtime_fixture(event):
    resources = subject.cancellable_resource_type(SQLRuntimeResources, event)()
    row = {"reason": None, "resource_watcher_cleanup_confirmed": False,
        "original_resource_type_inherited": isinstance(resources, SQLRuntimeResources),
        "cancel_observer": "original_watcher_sample",
        "actual_SQL_or_native_executed": False, "container_cleanup_qualified": False}
    try:
        resources.start()
        print(READY.decode().strip(), flush=True)
        deadline = time.monotonic()+10
        while True:
            if resources.stop.wait(.05):
                c.require(resources.reason == subject.CANCEL_REASON, "SQL_CANCEL_RUNTIME_UNEXPECTED_STOP")
                row["reason"] = resources.reason
                break
            c.require(time.monotonic() < deadline, "SQL_CANCEL_RUNTIME_SIGNAL_NOT_RECEIVED")
    finally:
        finish_watcher(resources, row)
    c.require(row["reason"] == subject.CANCEL_REASON and row["resource_watcher_cleanup_confirmed"] is True,
        "SQL_CANCEL_RUNTIME_NOT_ACCEPTED")
    return row


def worker(mode, name):
    c.require(Path.cwd().resolve() == c.ROOT and mode in {"approval-admission", "trust-admission", "runtime"},
        "SQL_CANCEL_WORKER_SCOPE")
    event, closed, result = subject.CancelEvent.open(name), False, None
    try:
        with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CANCEL_WORKER_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("SQL_CANCEL_WORKER_CHILD_FORBIDDEN")):
            if mode == "runtime":
                result = runtime_fixture(event)
            else:
                case = mode.split("-", 1)[0]
                fixture_paths(case)
                if case == "approval":
                    import run_formula_issuer_live_sql_probe as driver
                else:
                    import run_formula_issuer_authority_sql_probe as driver
                original = driver.IdleResources
                derived = subject.cancellable_resource_type(original, event)
                constructed = []
                class TrackedResources(derived):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        constructed.append(self)
                with patch.object(driver, "IdleResources", TrackedResources), \
                        patch("threading.Thread.start", side_effect=AssertionError("SQL_CANCEL_ADMISSION_THREAD_FORBIDDEN")):
                    result = account_driver_call(driver,
                        (MISSING_BUILD, FIXTURE_RECEIPTS[case], 0, "original", "unchanged", case))
                # trust admission은 새 stop code를 원래 allowlist로 redacted한다.
                # 이 오류를 바꾸지 않고 owned resource의 실제 stop 원인을 별도로 결합한다.
                expected_error = subject.CANCEL_REASON if case == "approval" else "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE"
                c.require(len(constructed) == 1 and constructed[0].reason == subject.CANCEL_REASON
                    and constructed[0].stop.is_set() and constructed[0].thread.ident is None,
                    "SQL_CANCEL_ADMISSION_RESOURCE_NOT_STOPPED")
                result["cooperative_resource_stop_reason"] = constructed[0].reason
                result["original_admission_redaction_preserved"] = case == "trust"
                c.require(driver.IdleResources is original and result["driver_error_code"] == expected_error
                    and result["state"] == "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS"
                    and result["reader_count"] == 0 and result["reader_IO"] is None
                    and result["source_final_hash_completed"] is False
                    and not (c.ROOT/FIXTURE_RECEIPTS[case]).exists(), "SQL_CANCEL_ADMISSION_NOT_ACCEPTED")
    finally:
        event.close()
        closed = event.closed
    print(json.dumps({"mode": mode, "state": "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE",
        "child_event_read_only": True, "child_event_closed": closed, "result": result}))
    return 0


def readiness_seen(capture):
    with capture.lock:
        raw = bytes(capture.buffers["stdout"])
    c.require(len(raw) <= MAX_OUTPUT, "SQL_CANCEL_OUTPUT_BUDGET")
    # exact control marker only; no raw output is persisted.
    return READY in raw.replace(b"\r\n", b"\n").splitlines(keepends=True)


def actual_fixture(mode, resources):
    event = owned = capture = None
    row = {"mode": mode, "state": "FAILED_NOT_ACCEPTED", "signal_sent": False,
        "parent_event_closed": False, "worker_result": None, "owned_job_profile": None,
        "pipe_cleanup_confirmed": False, "forced_termination_before_worker_terminal": None,
        "container_cleanup_qualified": False}
    try:
        event = subject.CancelEvent.create()
        if mode.endswith("-admission"):
            event.request()
            row["signal_sent"] = True
        owned = OwnedSQLJobProcess([sys.executable, "-B", str(c.ROOT/SELF), "--worker", mode, event.name],
            windows=resources.windows, allowed_executables=[sys.executable], cwd=c.ROOT,
            checkpoint=resources.checkpoint_io)
        capture = BoundedProcessCapture(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        deadline = time.monotonic()+15
        while True:
            resources.checkpoint_io()
            c.require(time.monotonic() < deadline, "STOP_SQL_CANCEL_FIXTURE_TIME")
            if mode == "runtime" and not row["signal_sent"] and readiness_seen(capture):
                event.request()
                row["signal_sent"] = True
            try:
                output, errors = capture.communicate(timeout=.25)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        c.require(not errors and row["signal_sent"], "SQL_CANCEL_OUTPUT_OR_SIGNAL_SCOPE")
        lines = output.replace("\r\n", "\n").splitlines()
        c.require(len(lines) == (2 if mode == "runtime" else 1)
            and (mode != "runtime" or lines[0] == READY.decode().strip()), "SQL_CANCEL_WORKER_PROTOCOL")
        result = json.loads(lines[-1])
        c.require(owned.returncode == 0 and set(result) == {"mode", "state", "child_event_read_only", "child_event_closed", "result"}
            and result["mode"] == mode and result["state"] == "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE"
            and result["child_event_read_only"] is True and result["child_event_closed"] is True,
            "SQL_CANCEL_WORKER_NOT_ACCEPTED")
        row["worker_result"] = result
        row["state"] = "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        value = str(error) if isinstance(error, ValueError) else "SQL_CANCEL_FIXTURE_OPERATION_FAILED"
        row["error_code"] = value if re.fullmatch(r"SQL_CANCEL_[A-Z_]+|STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+", value) \
            else "SQL_CANCEL_FIXTURE_REDACTED_FAILURE"
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_job_profile"] = dict(error.owned_sql_job_profile)
    finally:
        if owned is not None:
            row["forced_termination_before_worker_terminal"] = owned.poll() is None
            try:
                owned.kill()
                owned.wait(timeout=2)
                if capture is not None:
                    capture.close()
                    row["pipe_cleanup_confirmed"] = True
            except (ValueError, OSError, subprocess.SubprocessError):
                row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCEL_PIPE_OR_TERMINATE_FAILED"
            finally:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError):
                    row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCEL_JOB_CLOSE_FAILED"
                row["owned_job_profile"] = dict(owned.profile)
        if event is not None:
            try:
                event.close()
                row["parent_event_closed"] = event.closed
            except (ValueError, OSError):
                row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCEL_EVENT_CLOSE_FAILED"
        profile = row["owned_job_profile"] or {}
        if not row["parent_event_closed"] or not all(profile.get(key) is True
                for key in ("owned_tree_empty", "cleanup_confirmed", "job_handle_closed")) \
                or row["forced_termination_before_worker_terminal"] is not False:
            row["state"] = "FAILED_NOT_ACCEPTED"
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    kind = "actual" if args.actual else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-cooperative-cancel.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "SQL_CANCEL_FRESH_RECEIPT")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-SQL-cooperative-cancel-verification/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_cancel_fixtures": [],
        "actual_SQL_Docker_Cargo_or_native_executed": False, "original_driver_source_modified": False,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.actual:
            resources.start()
            for mode in ("approval-admission", "trust-admission", "runtime"):
                result = actual_fixture(mode, resources)
                row["actual_cancel_fixtures"].append(result)
                c.require(result["state"] == "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE", "SQL_CANCEL_ACTUAL_FIXTURE_FAILED")
            row["state"] = "PASS_THREE_ACTUAL_SCOPED_CANCEL_FIXTURES_NOT_SQL_OR_GATE"
        else:
            from tests.test_sql_cooperative_cancel import SQLCooperativeCancelTests
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CANCEL_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_CANCEL_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(
                    unittest.defaultTestLoader.loadTestsFromTestCase(SQLCooperativeCancelTests))
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 15 and checked.wasSuccessful() and not checked.skipped, "SQL_CANCEL_LIGHT_TEST_FAILED")
            row["state"] = "PASS_SQL_COOPERATIVE_CANCEL_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        value = str(error) if isinstance(error, ValueError) else "SQL_CANCEL_OPERATION_FAILED"
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", value if re.fullmatch(r"SQL_CANCEL_[A-Z_]+|STOP_[A-Z_]+", value) \
            else "SQL_CANCEL_REDACTED_FAILURE"
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCEL_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["wrapper_wall_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({"state": row["state"], "tests_run": row["tests_run"], "tests_passed": row["tests_passed"],
            "failed_tests": row["failed_tests"], "actual_cancel_fixtures": len(row["actual_cancel_fixtures"]),
            "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        raise SystemExit(worker(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
