"""Owned supervisor contracts and controlled non-SQL lifecycle fixtures.

actual 모드는 missing-input original main / cooperative wait / forced fixture만
허용한다. Docker·SQL 실행이나 backend fallback 정리는 이 검증기의 범위가 아니다.
"""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import sql_call_supervisor as subject
import sql_cooperative_cancel as cancellation
from sql_cancelled_call import account_cancellable_driver_call
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from bounded_process_progress import BoundedProcessCapture
from verify_sql_cancelled_call import SOURCES as CALL_SOURCES
from verify_sql_call_accounting import fixture_paths, MISSING_BUILD, FIXTURE_RECEIPTS

SELF = "tools/p09/verify_sql_call_supervisor.py"
MODES = ("missing-approval", "cooperative-wait", "ignore-cancel")
READY = "P149_CALL_READY:controlled_non_SQL_fixture"
SOURCES = list(dict.fromkeys(CALL_SOURCES+[SELF, "tools/p09/sql_call_supervisor.py",
    "tools/p09/tests/test_sql_call_supervisor.py",
    "implementation/p09/source-archive/p09-149-pre-call-supervisor-tree-terminal-repair/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-call-supervisor-terminal-settle-repair/source-preimages.v1.json"]))


def worker(mode, name):
    c.require(Path.cwd().resolve() == c.ROOT and mode in MODES, "SQL_CALL_WORKER_SCOPE")
    event = cancellation.CancelEvent.open(name)
    result, resources = None, None
    try:
        with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CALL_FIXTURE_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("SQL_CALL_FIXTURE_CHILD_FORBIDDEN")):
            if mode == "missing-approval":
                fixture_paths("approval")
                import run_formula_issuer_live_sql_probe as driver
                with patch("threading.Thread.start", side_effect=AssertionError("SQL_CALL_MISSING_THREAD_FORBIDDEN")):
                    result = account_cancellable_driver_call(driver,
                        (MISSING_BUILD, FIXTURE_RECEIPTS["approval"], 0, "original", "unchanged", "approval"), event)
                c.require(result["state"] == "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS"
                    and result["driver_error_code"] == "sql_source_link_or_missing"
                    and result["reader_count"] == 1 and result["reader_IO"]["finished"] is False
                    and result["source_final_hash_completed"] is False
                    and result["original_driver_dependencies_restored"] is True
                    and result["cooperative_resource_stop_latched"] is False
                    and not (c.ROOT/FIXTURE_RECEIPTS["approval"]).exists(), "SQL_CALL_MISSING_FAILURE_NOT_PRESERVED")
            else:
                if mode == "cooperative-wait":
                    resources = cancellation.cancellable_resource_type(SQLRuntimeResources, event)()
                    resources.start()
                print(READY, flush=True)
                deadline, waiting = time.monotonic()+10, threading.Event()
                while time.monotonic() < deadline:
                    if resources is not None and resources.stop.wait(.05):
                        c.require(resources.reason == cancellation.CANCEL_REASON, "SQL_CALL_FIXTURE_UNEXPECTED_STOP")
                        result = {"cooperative_resource_stop_reason": resources.reason,
                            "controlled_wait_completed": True, "actual_SQL_Docker_executed": False,
                            "backend_container_cleanup_confirmed": None}
                        break
                    if resources is None:
                        waiting.wait(.05)  # 의도적으로 취소를 무시하는 작은 own-only 실패 fixture.
                c.require(result is not None, "SQL_CALL_FIXTURE_WAIT_EXPIRED")
    finally:
        if resources is not None:
            if result is None:
                result = {}
            finish_watcher(resources, result)
        event.close()
    print(json.dumps({"mode": mode, "child_event_closed": event.closed, "result": result}))
    return 0


def decode(mode, output):
    lines = output.replace("\r\n", "\n").splitlines()
    c.require(len(lines) == (1 if mode == "missing-approval" else 2)
        and (mode == "missing-approval" or lines[0] == READY), "SQL_CALL_FIXTURE_PROTOCOL")
    row = json.loads(lines[-1])
    c.require(set(row) == {"mode", "child_event_closed", "result"} and row["mode"] == mode
        and row["child_event_closed"] is True and isinstance(row["result"], dict), "SQL_CALL_FIXTURE_PROTOCOL")
    return row


def fixture_require(row, ok, code):
    if not ok:
        row["fixture_contract_accepted_not_SQL_or_backend_cleanup"] = False
        error = ValueError(code)
        error.sql_call_fixture_result = row
        raise error


def actual_fixture(mode, resources):
    c.require(mode in MODES, "SQL_CALL_FIXTURE_SCOPE")
    event, captures, triggered = cancellation.CancelEvent.create(), [], False
    row = None
    def capture_factory(*args, **kwargs):
        capture = BoundedProcessCapture(*args, **kwargs)
        captures.append(capture)
        return capture
    class ControlledRequest:
        def __getattr__(self, name):
            return getattr(resources, name)
        def checkpoint_io(self):
            nonlocal triggered
            resources.checkpoint_io()
            if mode != "missing-approval" and captures and not triggered:
                capture = captures[0]
                with capture.lock:
                    lines = bytes(capture.buffers["stdout"]).replace(b"\r\n", b"\n").splitlines()
                if READY.encode() in lines:
                    triggered = True
                    raise ValueError("STOP_SQL_CALL_CONTROLLED_FIXTURE_REQUEST")
    try:
        row = subject.supervise_owned_call([sys.executable, "-B", str(c.ROOT/SELF), "--worker", mode, event.name],
            ControlledRequest(), event, lambda output: decode(mode, output), maximum_seconds=15,
            grace_seconds=.75 if mode == "ignore-cancel" else 5, capture_factory=capture_factory)
        row["mode"], row["controlled_request_triggered"] = mode, triggered
    finally:
        event.close()
        if row is not None:
            row["parent_event_closed"] = event.closed
    profile = row["owned_job_profile"] or {}
    fixture_require(row, all(profile.get(key) is True for key in ("owned_tree_empty", "cleanup_confirmed", "job_handle_closed"))
        and row["pipe_cleanup_confirmed"] is True and row["parent_event_closed"] is True
        and row["pre_teardown_tree_observed"] is True
        and row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"] is False
        and row["backend_container_cleanup_confirmed"] is None, "SQL_CALL_FIXTURE_HOST_CLEANUP_FAILED")
    if mode == "ignore-cancel":
        fixture_require(row, row["state"] == "FAILED_NOT_ACCEPTED" and row["forced_termination"] is True
            and row["worker_terminal_before_forced_termination"] is False
            and row["pre_teardown_job_accounting"]["active_processes"] > 0
            and row["signal_sent"] is True and triggered
            and row["cancel_reason"] == "STOP_SQL_CALL_CONTROLLED_FIXTURE_REQUEST"
            and row["grace_abort_reason"] == "STOP_SQL_CALL_GRACE_TIME"
            and row["worker_result"] is None, "SQL_CALL_FIXTURE_FORCE_NOT_PRESERVED")
    else:
        expected = "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE" if mode == "missing-approval" \
            else "CANCELLED_OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
        fixture_require(row, row["state"] == expected and row["forced_termination"] is False
            and row["worker_terminal_before_forced_termination"] is True
            and row["pre_teardown_job_accounting"]["active_processes"] == 0
            and row["signal_sent"] is (mode != "missing-approval"), "SQL_CALL_FIXTURE_TERMINAL_NOT_ACCEPTED")
    row["fixture_contract_accepted_not_SQL_or_backend_cleanup"] = True
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    kind = "actual" if args.actual else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-call-supervisor.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and not destination.is_symlink()
        and not destination.is_junction() and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "SQL_CALL_FRESH_RECEIPT")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-SQL-call-supervisor-verification/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_lifecycle_fixtures": [],
        "actual_SQL_Docker_Cargo_or_native_executed": False, "original_driver_source_modified": False,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "backend_container_cleanup_confirmed": None, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.actual:
            resources.start()
            for mode in MODES:
                row["actual_lifecycle_fixtures"].append(actual_fixture(mode, resources))
            row["state"] = "PASS_THREE_ACTUAL_CONTROLLED_OWNED_CALL_FIXTURES_NOT_SQL_OR_GATE"
        else:
            from tests.test_sql_call_accounting import SQLCallAccountingTests
            from tests.test_sql_cooperative_cancel import SQLCooperativeCancelTests
            from tests.test_sql_cancelled_call import SQLCancelledCallTests, SQLCancelledCleanupTests
            from tests.test_sql_call_supervisor import SQLCallSupervisorTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in
                (SQLCallAccountingTests, SQLCooperativeCancelTests, SQLCancelledCallTests, SQLCancelledCleanupTests, SQLCallSupervisorTests))
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch.object(subprocess, "run", side_effect=AssertionError("SQL_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_CALL_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 65 and checked.wasSuccessful() and not checked.skipped, "SQL_CALL_LIGHT_TEST_FAILED")
            row["state"] = "PASS_SQL_CALL_SUPERVISOR_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", subject.closed_error(error)
        if hasattr(error, "sql_call_fixture_result"):
            row["actual_lifecycle_fixtures"].append(error.sql_call_fixture_result)
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CALL_FINAL_FRESHNESS_FAILED"
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
            "failed_tests": row["failed_tests"], "actual_lifecycle_fixtures": len(row["actual_lifecycle_fixtures"]),
            "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    return 0 if row["state"].startswith("PASS_") and row["source_freeze_exact_after"] \
        and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        raise SystemExit(worker(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
