"""Bounded ownership/fallback contracts and actual exclusive fsync files only.

actual worker도 Docker 실행은 금지한다. 파일 기록 뒤 mock delegate 순서만 실제
검증하며, 모든 intent 파일/실패 evidence를 보존한다. full SQL CLI 모드는 없다.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid

import conservative_maintenance as c
import sql_container_ownership as subject
from sql_cooperative_cancel import CancelEvent
from sql_call_supervisor import supervise_owned_call
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_sql_call_supervisor import SOURCES as SUPERVISOR_SOURCES

SELF = "tools/p09/verify_sql_container_ownership.py"
SOURCES = list(dict.fromkeys(SUPERVISOR_SOURCES+[SELF, "tools/p09/sql_container_ownership.py",
    "tools/p09/tests/test_sql_container_ownership.py", "tools/p09/sql_parent_cleanup.py",
    "tools/p09/tests/test_sql_parent_cleanup.py",
    "implementation/p09/source-archive/p09-149-pre-parent-cleanup-post-query-checkpoint/source-preimages.v1.json"]))


def worker(case, nonce, run_id, event_name):
    c.require(Path.cwd().resolve() == c.ROOT and case in subject.CASES, "SQL_OWNED_INTENT_WORKER_SCOPE")
    row, delegated, event = subject.make_intent(nonce, case, run_id), [], CancelEvent.open(event_name)
    try:
        with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_OWNED_INTENT_WORKER_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("SQL_OWNED_INTENT_WORKER_CHILD_FORBIDDEN")), \
                patch("threading.Thread.start", side_effect=AssertionError("SQL_OWNED_INTENT_WORKER_THREAD_FORBIDDEN")):
            class OriginalMockFactory:
                def __init__(self):
                    self.docker = "fixture-docker"
                def __call__(self, args, **kwargs):
                    # This delegate is NOT Docker. Read same intent file before accepting fixture GO.
                    checked = subject.load_intent(nonce, case)
                    c.require(checked["intent"] == row, "SQL_OWNED_INTENT_FIXTURE_BEFORE_GO_BINDING")
                    delegated.append(checked["journal_pin"])
                    return "fixture-delegate"
            factory = subject.journalled_factory_type(OriginalMockFactory, nonce, case)()
            c.require(factory(subject.run_arguments("fixture-docker", row)) == "fixture-delegate"
                and len(delegated) == 1, "SQL_OWNED_INTENT_FIXTURE_DELEGATE_FAILED")
            # Exclusive retry must fail and must not reach even the mock launcher a second time.
            try:
                factory(subject.run_arguments("fixture-docker", row))
            except ValueError as error:
                c.require(str(error) == "SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED", "SQL_OWNED_INTENT_FIXTURE_RETRY_SCOPE")
            else:
                raise ValueError("SQL_OWNED_INTENT_FIXTURE_OVERWRITE_ALLOWED")
            c.require(len(delegated) == 1, "SQL_OWNED_INTENT_FIXTURE_DUPLICATE_GO")
    finally:
        event.close()
    print(json.dumps({"case": case, "parent_nonce": nonce, "run_id": run_id,
        "journal_pin": delegated[0], "child_event_closed": event.closed, "mock_delegate_count": len(delegated),
        "exclusive_retry_rejected": True, "journal_fsync_before_mock_delegate_completed": True,
        "actual_SQL_Docker_executed": False}))
    return 0


def actual_fixture(case, resources, reader):
    nonce, run_id, event = str(uuid.uuid4()), str(uuid.uuid4()), CancelEvent.create()
    row = None
    try:
        c.require(not subject.journal_path(nonce).exists(), "SQL_OWNED_INTENT_FRESH_FIXTURE_REQUIRED")
        row = supervise_owned_call([sys.executable, "-B", str(c.ROOT/SELF), "--worker", case, nonce, run_id, event.name],
            resources, event, json.loads, maximum_seconds=15, grace_seconds=5)
        row["case"] = case
    finally:
        event.close()
        if row is not None:
            row["parent_event_closed"] = event.closed
    try:
        result = row["worker_result"]
        c.require(row["state"] == "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
            and row["forced_termination"] is False and row["pre_teardown_job_accounting"]["active_processes"] == 0
            and row["parent_event_closed"] is True and isinstance(result, dict)
            and result["case"] == case and result["parent_nonce"] == nonce and result["run_id"] == run_id
            and result["mock_delegate_count"] == 1 and result["exclusive_retry_rejected"] is True
            and result["journal_fsync_before_mock_delegate_completed"] is True
            and result["child_event_closed"] is True and result["actual_SQL_Docker_executed"] is False,
            "SQL_OWNED_INTENT_ACTUAL_FIXTURE_NOT_ACCEPTED")
        checked = subject.load_intent(nonce, case)
        bound = reader.pin(checked["journal_pin"]["path"])
        c.require(bound == checked["journal_pin"] == result["journal_pin"]
            and reader.json(bound["path"]) == subject.make_intent(nonce, case, run_id), "SQL_OWNED_INTENT_ACTUAL_BYTE_BINDING")
        row["fixture_contract_accepted_not_SQL_or_backend_cleanup"] = True
        return row
    except (ValueError, OSError, KeyError, TypeError) as error:
        error.sql_owned_intent_fixture_result = row
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    kind = "actual" if args.actual else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-container-ownership.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and not destination.is_symlink()
        and not destination.is_junction() and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "SQL_OWNED_INTENT_FRESH_RECEIPT_REQUIRED")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-SQL-container-ownership-verification/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_journal_fixtures": [],
        "actual_SQL_Docker_Cargo_or_native_executed": False, "original_driver_source_modified": False,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "backend_container_cleanup_confirmed": None, "power_loss_recovery_qualified": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.actual:
            resources.start()
            for case in subject.CASES:
                row["actual_journal_fixtures"].append(actual_fixture(case, resources, reader))
            row["state"] = "PASS_THREE_ACTUAL_FSYNC_INTENT_FILES_NOT_SQL_OR_BACKEND_CLEANUP"
        else:
            from tests.test_sql_call_accounting import SQLCallAccountingTests
            from tests.test_sql_cooperative_cancel import SQLCooperativeCancelTests
            from tests.test_sql_cancelled_call import SQLCancelledCallTests, SQLCancelledCleanupTests
            from tests.test_sql_call_supervisor import SQLCallSupervisorTests
            from tests.test_sql_container_ownership import SQLContainerOwnershipTests
            from tests.test_sql_parent_cleanup import SQLParentCleanupTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in
                (SQLCallAccountingTests, SQLCooperativeCancelTests, SQLCancelledCallTests, SQLCancelledCleanupTests,
                    SQLCallSupervisorTests, SQLContainerOwnershipTests, SQLParentCleanupTests))
            with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_OWNED_INTENT_LIGHT_CHILD_FORBIDDEN")), \
                    patch.object(subprocess, "run", side_effect=AssertionError("SQL_OWNED_INTENT_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_OWNED_INTENT_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 93 and checked.wasSuccessful() and not checked.skipped,
                "SQL_OWNED_INTENT_LIGHT_TEST_FAILED")
            row["state"] = "PASS_SQL_INTENT_AND_PARENT_CLEANUP_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        from sql_parent_cleanup import closed_error
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
        if hasattr(error, "sql_owned_intent_fixture_result"):
            row["actual_journal_fixtures"].append(error.sql_owned_intent_fixture_result)
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_OWNED_INTENT_FINAL_FRESHNESS_FAILED"
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
            "failed_tests": row["failed_tests"], "actual_journal_fixtures": len(row["actual_journal_fixtures"]),
            "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    return 0 if row["state"].startswith("PASS_") and row["source_freeze_exact_after"] \
        and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None else 2


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--worker":
        raise SystemExit(worker(*sys.argv[2:]))
    raise SystemExit(main())
