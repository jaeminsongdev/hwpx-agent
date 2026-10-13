"""Bounded combined-call tests and original admission cancellation, no SQL.

cleanup 증거는 원래 AST + mock Docker 응답의 계약검사다. 실제 DB 컨테이너
정리나 full wrapper qualification을 대신하지 않는다. 원래 driver 파일은 수정하지 않는다.
"""
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
import sql_cancelled_call as subject
import sql_cooperative_cancel as cancellation
import verify_sql_cooperative_cancel as previous
from live_sql_evidence_reader import LiveSQLReader
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from verify_sql_call_accounting import fixture_paths, MISSING_BUILD, FIXTURE_RECEIPTS

SELF = "tools/p09/verify_sql_cancelled_call.py"
SOURCES = list(dict.fromkeys(previous.SOURCES + [SELF, "tools/p09/sql_cancelled_call.py",
    "tools/p09/tests/test_sql_cancelled_call.py"]))


def worker(mode, name):
    c.require(Path.cwd().resolve() == c.ROOT and mode in {"approval-admission", "trust-admission"},
        "SQL_CANCELLED_CALL_WORKER_SCOPE")
    case = mode.split("-", 1)[0]
    fixture_paths(case)
    if case == "approval":
        import run_formula_issuer_live_sql_probe as driver
    else:
        import run_formula_issuer_authority_sql_probe as driver
    original_resource, original_reader = driver.IdleResources, driver.LiveSQLReader
    event = cancellation.CancelEvent.open(name)
    result = None
    try:
        with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CANCELLED_CALL_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("SQL_CANCELLED_CALL_CHILD_FORBIDDEN")), \
                patch("threading.Thread.start", side_effect=AssertionError("SQL_CANCELLED_CALL_THREAD_FORBIDDEN")):
            result = subject.account_cancellable_driver_call(driver,
                (MISSING_BUILD, FIXTURE_RECEIPTS[case], 0, "original", "unchanged", case), event)
        expected = cancellation.CANCEL_REASON if case == "approval" else "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE"
        c.require(result["state"] == "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS"
            and result["driver_error_code"] == expected and result["cooperative_resource_count"] == 1
            and result["cooperative_resource_stop_reason"] == cancellation.CANCEL_REASON
            and result["cooperative_resource_stop_latched"] is True
            and result["original_resource_type_inherited"] is True
            and result["original_driver_dependencies_restored"] is True
            and result["reader_count"] == 0 and result["reader_IO"] is None
            and result["source_final_hash_completed"] is False
            and driver.IdleResources is original_resource and driver.LiveSQLReader is original_reader
            and not (c.ROOT/FIXTURE_RECEIPTS[case]).exists(), "SQL_CANCELLED_CALL_ADMISSION_NOT_ACCEPTED")
    finally:
        event.close()
    print(json.dumps({"mode": mode, "state": "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE",
        "child_event_read_only": True, "child_event_closed": event.closed, "result": result}))
    return 0


def accepted(row):
    return row["state"] in {"PASS_SQL_CANCELLED_CALL_AND_CLEANUP_AST_CONTRACT_NOT_SQL_OR_GATE",
        "PASS_TWO_ACTUAL_ACCOUNTED_ADMISSION_CANCEL_FIXTURES_NOT_SQL_OR_GATE"} \
        and row["source_freeze_exact_after"] is True \
        and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    kind = "actual" if args.actual else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-cancelled-call.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists()
        and not destination.is_symlink() and not destination.is_junction() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "SQL_CANCELLED_CALL_FRESH_RECEIPT")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-SQL-cancelled-call-verification/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_cancel_fixtures": [],
        "cleanup_contract_scope": "ORIGINAL_INSPECT_AND_THREE_FINALLY_NODES_WITH_MOCK_COMMAND_ONLY",
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
            # 같은 bounded Event/Job/pipe supervisor, child entry만 새 연결부 검증기로 지정.
            with patch.object(previous, "SELF", SELF):
                for mode in ("approval-admission", "trust-admission"):
                    result = previous.actual_fixture(mode, resources)
                    row["actual_cancel_fixtures"].append(result)
                    c.require(result["state"] == "PASS_SCOPED_CANCEL_FIXTURE_ONLY_NOT_SQL_OR_GATE",
                        "SQL_CANCELLED_CALL_ACTUAL_FIXTURE_FAILED")
            row["state"] = "PASS_TWO_ACTUAL_ACCOUNTED_ADMISSION_CANCEL_FIXTURES_NOT_SQL_OR_GATE"
        else:
            from tests.test_sql_call_accounting import SQLCallAccountingTests
            from tests.test_sql_cooperative_cancel import SQLCooperativeCancelTests
            from tests.test_sql_cancelled_call import SQLCancelledCallTests, SQLCancelledCleanupTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind)
                for kind in (SQLCallAccountingTests, SQLCooperativeCancelTests, SQLCancelledCallTests, SQLCancelledCleanupTests))
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_CANCELLED_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch.object(subprocess, "run", side_effect=AssertionError("SQL_CANCELLED_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_CANCELLED_CALL_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 44 and checked.wasSuccessful() and not checked.skipped,
                "SQL_CANCELLED_CALL_LIGHT_TEST_FAILED")
            row["state"] = "PASS_SQL_CANCELLED_CALL_AND_CLEANUP_AST_CONTRACT_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        value = str(error) if isinstance(error, ValueError) else "SQL_CANCELLED_CALL_OPERATION_FAILED"
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", value if re.fullmatch(r"SQL_CANCELLED_CALL_[A-Z_]+|STOP_[A-Z_]+", value) \
            else "SQL_CANCELLED_CALL_REDACTED_FAILURE"
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCELLED_CALL_FINAL_FRESHNESS_FAILED"
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
    return 0 if accepted(row) else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        raise SystemExit(worker(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
