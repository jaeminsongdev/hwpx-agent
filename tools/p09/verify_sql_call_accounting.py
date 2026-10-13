"""Accounting tests and actual pre-container missing-input failures only.

full SQL 실행/컨테이너 생성 모드는 없다. 실제 fixture는 기존 main의 manifest/source
읽기 후 존재하지 않는 build 입력에서 실패하며 subprocess/thread 시작을 금지한다.
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
import sql_call_accounting as subject
from bounded_process_progress import BoundedProcessCapture, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_issuer_sql_build_contract import SOURCES as CONTRACT_SOURCES

SELF = "tools/p09/verify_sql_call_accounting.py"
DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")
MISSING_BUILD = "target/p09-121-resource-optimized/p149-sql-accounting-known-missing-input.json"
FIXTURE_RECEIPTS = {"approval": "implementation/p09/evidence/p09-146-corpus-consumer-run91.v1.json",
    "trust": "implementation/p09/evidence/p09-148-authority-consumer-run91.v1.json"}
SOURCES = list(dict.fromkeys(CONTRACT_SOURCES+[SELF, "tools/p09/sql_call_accounting.py",
    "tools/p09/tests/test_sql_call_accounting.py", *DRIVERS,
    "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"]))


def fixture_paths(case):
    c.require(case in FIXTURE_RECEIPTS, "SQL_ACCOUNTING_FIXTURE_CASE")
    missing, receipt = c.ROOT/MISSING_BUILD, c.ROOT/FIXTURE_RECEIPTS[case]
    for path in (missing, receipt):
        c.require(not path.exists() and not path.is_symlink() and not path.is_junction(), "SQL_ACCOUNTING_FIXTURE_INPUT_NOT_MISSING")
        for ancestor in path.parents:
            if ancestor == c.ROOT.parent:
                break
            c.require(not ancestor.is_symlink() and not ancestor.is_junction(), "SQL_ACCOUNTING_FIXTURE_PATH_LINK")
    return missing, receipt


def worker(case):
    c.require(Path.cwd().resolve() == c.ROOT, "SQL_ACCOUNTING_WORKER_ROOT")
    fixture_paths(case)
    if case == "approval":
        import run_formula_issuer_live_sql_probe as driver
    else:
        import run_formula_issuer_authority_sql_probe as driver
    with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_ACCOUNTING_FIXTURE_CHILD_FORBIDDEN")), \
            patch.object(subprocess, "run", side_effect=AssertionError("SQL_ACCOUNTING_FIXTURE_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("SQL_ACCOUNTING_FIXTURE_THREAD_FORBIDDEN")):
        result = subject.account_driver_call(driver,
            (MISSING_BUILD, FIXTURE_RECEIPTS[case], 0, "original", "unchanged", case))
    accepted = result["state"] == "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS" \
        and result["driver_error_code"] == "sql_source_link_or_missing" and result["reader_count"] == 1 \
        and result["reader_IO"] is not None and result["reader_IO"]["read_passes"] >= 3 \
        and result["reader_IO"]["bytes_read"] > 0 and result["reader_IO"]["finished"] is False \
        and result["source_final_hash_completed"] is False and result["driver_call_wall_seconds"] > 0 \
        and not (c.ROOT/FIXTURE_RECEIPTS[case]).exists()
    print(json.dumps({"case": case, "accepted_failure_accounting_fixture": accepted, "accounting": result}))
    return 0 if accepted else 2


def actual_fixture(case, resources, *, process_factory=OwnedSQLJobProcess):
    fixture_paths(case)
    owned = capture = None
    result = None
    row = {"case": case, "state": "FAILED_NOT_ACCEPTED", "worker_result": None,
        "owned_job_profile": None, "pipe_cleanup_confirmed": False}
    try:
        owned = process_factory([sys.executable, "-B", str(c.ROOT/SELF), "--worker", case],
            windows=resources.windows, allowed_executables=[sys.executable], cwd=c.ROOT,
            checkpoint=resources.checkpoint_io)
        capture = BoundedProcessCapture(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        deadline = time.monotonic()+30
        while True:
            resources.checkpoint_io()
            c.require(time.monotonic() < deadline, "STOP_SQL_ACCOUNTING_FIXTURE_TIME")
            try:
                output, errors = capture.communicate(timeout=.25)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        c.require(not errors, "SQL_ACCOUNTING_FIXTURE_OUTPUT_SCOPE")
        result = json.loads(output)
        c.require(owned.returncode == 0 and set(result) == {"case", "accepted_failure_accounting_fixture", "accounting"}
            and result["case"] == case and result["accepted_failure_accounting_fixture"] is True,
            "SQL_ACCOUNTING_FIXTURE_NOT_ACCEPTED")
        row["worker_result"] = result
        row["state"] = "PASS_PRE_CONTAINER_FAILURE_ACCOUNTING_FIXTURE_ONLY"
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["error_code"] = subject.closed_code(error)
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_job_profile"] = dict(error.owned_sql_job_profile)
    finally:
        if owned is not None:
            try:
                owned.kill()
                owned.wait(timeout=2)
                if capture is not None:
                    capture.close()
                    row["pipe_cleanup_confirmed"] = True
            except (ValueError, OSError, subprocess.SubprocessError):
                row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_ACCOUNTING_FIXTURE_PIPE_OR_TERMINATE_FAILED"
            finally:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError):
                    row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_ACCOUNTING_FIXTURE_JOB_CLOSE_FAILED"
                row["owned_job_profile"] = dict(owned.profile)
        profile = row["owned_job_profile"] or {}
        if not all(profile.get(key) is True for key in ("owned_tree_empty", "cleanup_confirmed", "job_handle_closed")):
            row["state"] = "FAILED_NOT_ACCEPTED"
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual-failures", action="store_true")
    args = parser.parse_args()
    kind = "actual-failures" if args.actual_failures else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-call-accounting.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "SQL_ACCOUNTING_FRESH_RECEIPT")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-SQL-call-accounting-verification/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_failure_fixtures": [],
        "actual_SQL_Docker_Cargo_or_native_executed": False, "original_driver_source_modified": False,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.actual_failures:
            resources.start()
            for case in FIXTURE_RECEIPTS:
                fixture = actual_fixture(case, resources)
                row["actual_failure_fixtures"].append(fixture)
                c.require(fixture["state"] == "PASS_PRE_CONTAINER_FAILURE_ACCOUNTING_FIXTURE_ONLY",
                    "SQL_ACCOUNTING_ACTUAL_FIXTURE_FAILED")
            row["state"] = "PASS_TWO_ACTUAL_PRE_CONTAINER_FAILURE_ACCOUNTING_FIXTURES_NOT_SQL_OR_GATE"
        else:
            from tests.test_sql_call_accounting import SQLCallAccountingTests
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_ACCOUNTING_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_ACCOUNTING_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(
                    unittest.defaultTestLoader.loadTestsFromTestCase(SQLCallAccountingTests))
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 10 and checked.wasSuccessful() and not checked.skipped,
                "SQL_ACCOUNTING_LIGHT_TEST_FAILED")
            row["state"] = "PASS_SQL_CALL_ACCOUNTING_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", subject.closed_code(error)
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_ACCOUNTING_FINAL_FRESHNESS_FAILED"
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
            "failed_tests": row["failed_tests"], "actual_failure_fixtures": len(row["actual_failure_fixtures"]),
            "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        raise SystemExit(worker(sys.argv[2]))
    raise SystemExit(main())
