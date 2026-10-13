"""Single bounded original SQL execution path; light/missing modes never Docker.

product는 고정 r4/기존 driver/pull never/원래 36개 입력 조건을 그대로 사용한다.
missing-input은 실제 원래 main의 컨테이너 전 실패만 검증한다. default 실행 모드는 없다.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid

import conservative_maintenance as c
import sql_owned_execution as subject
from sql_cooperative_cancel import CancelEvent
from sql_call_supervisor import supervise_owned_call
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_sql_container_ownership import SOURCES as OWNERSHIP_SOURCES

SELF = "tools/p09/run_supervised_sql_probe.py"
SOURCES = list(dict.fromkeys(OWNERSHIP_SOURCES+[SELF, "tools/p09/sql_owned_execution.py",
    "tools/p09/tests/test_sql_owned_execution.py",
    "implementation/p09/source-archive/p09-149-pre-owned-execution-protocol-strengthening/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-owned-execution-loaded-intent-binding/source-preimages.v1.json"]))


def worker(mode, case, nonce, event_name, receipt_run, source_index, input_mode, expected):
    c.require(Path.cwd().resolve() == c.ROOT, "SQL_EXECUTION_WORKER_ROOT")
    arguments = subject.call_arguments(case, mode, int(receipt_run), int(source_index), input_mode, expected)
    subject.ownership.uuid_value(nonce)
    c.require(not subject.ownership.journal_path(nonce).exists(), "SQL_EXECUTION_FRESH_INTENT_REQUIRED")
    event, row = CancelEvent.open(event_name), None
    try:
        if case == "approval":
            import run_formula_issuer_live_sql_probe as driver
        else:
            import run_formula_issuer_authority_sql_probe as driver
        # fixture가 실제 실행으로 확장되는 것을 금지한다. product 경로에는 적용하지 않는다.
        with contextlib.ExitStack() as stack:
            if mode == "missing-input":
                for name in ("subprocess.Popen", "subprocess.run", "threading.Thread.start"):
                    stack.enter_context(patch(name, side_effect=AssertionError("SQL_EXECUTION_MISSING_CHILD_FORBIDDEN")))
            row = subject.journalled_driver_call(driver, arguments, event, nonce, case)
    finally:
        event.close()
        if row is not None:
            row["child_event_closed"] = event.closed
    # worker 종료 프로토콜과 원래 driver 성공은 별개다. 실패 원인/partial IO도 전달한다.
    subject.decode_worker(json.dumps(row), nonce, case, arguments[1])
    print(json.dumps(row))
    return 0


def execute_case(mode, case, arguments, resources, reader):
    nonce, event, parent = str(uuid.uuid4()), CancelEvent.create(), None
    try:
        c.require(not subject.ownership.journal_path(nonce).exists(), "SQL_EXECUTION_FRESH_INTENT_REQUIRED")
        prefix = "p09-146-corpus" if case == "approval" else "p09-148-authority"
        receipt_run = int(Path(arguments[1]).name.removeprefix(prefix+"-consumer-run").removesuffix(".v1.json"))
        parent = supervise_owned_call([sys.executable, "-B", str(c.ROOT/SELF), "--worker", mode, case, nonce,
            event.name, str(receipt_run), str(arguments[2]), arguments[3], arguments[4]], resources, event,
            lambda output: subject.decode_worker(output, nonce, case, arguments[1]),
            maximum_seconds=15 if mode == "missing-input" else 690, grace_seconds=5 if mode == "missing-input" else 135)
    finally:
        # Event close 오류가 유효한 intent의 fallback 시도까지 건너뛰게 하지 않는다.
        # 단, handle 오류는 lifecycle 실패로 보존하며 성공으로 인정하지 않는다.
        try:
            event.close()
        except (ValueError, OSError) as error:
            if parent is None:
                parent = {"state": "FAILED_NOT_ACCEPTED", "worker_result": None, "owned_job_profile": None}
            parent["parent_event_close_error_code"] = subject.closed_error(error)
        if parent is not None:
            parent["parent_event_closed"] = event.closed
    return subject.finalize_owned_call(parent, nonce, case, arguments, resources, reader,
        shutil.which("docker") if subject.ownership.journal_path(nonce).exists() else None)


def light_suite():
    from tests.test_sql_call_accounting import SQLCallAccountingTests
    from tests.test_sql_cooperative_cancel import SQLCooperativeCancelTests
    from tests.test_sql_cancelled_call import SQLCancelledCallTests, SQLCancelledCleanupTests
    from tests.test_sql_call_supervisor import SQLCallSupervisorTests
    from tests.test_sql_container_ownership import SQLContainerOwnershipTests
    from tests.test_sql_parent_cleanup import SQLParentCleanupTests
    from tests.test_sql_owned_execution import SQLOwnedExecutionTests
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in (
        SQLCallAccountingTests, SQLCooperativeCancelTests, SQLCancelledCallTests, SQLCancelledCleanupTests,
        SQLCallSupervisorTests, SQLContainerOwnershipTests, SQLParentCleanupTests, SQLOwnedExecutionTests))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("light", "missing-input", "product"), required=True)
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--case", choices=tuple(subject.ownership.CASES))
    parser.add_argument("--receipt-run", type=int)
    parser.add_argument("--source-index", type=int, default=0)
    parser.add_argument("--input-mode", choices=("original", "numeric_derivative"), default="original")
    parser.add_argument("--expected", choices=("unchanged", "changed"), default="unchanged")
    args = parser.parse_args()
    c.require(Path.cwd().resolve() == c.ROOT, "SQL_EXECUTION_PARENT_ROOT")
    c.require(args.mode != "product" or args.case is not None and args.receipt_run is not None,
        "SQL_EXECUTION_PRODUCT_SELECTION_REQUIRED")
    tag = "product-"+args.case if args.mode == "product" else args.mode
    destination = subject.scoped_path(f"implementation/p09/evidence/p09-149-SQL-owned-execution.{tag}-run{args.run:02}.v1.json", fresh=True)
    cases = tuple(subject.ownership.CASES) if args.mode == "missing-input" else (args.case,)
    calls = [] if args.mode == "light" else [(case, subject.call_arguments(case, args.mode,
        91 if args.mode == "missing-input" else args.receipt_run, args.source_index, args.input_mode, args.expected)) for case in cases]
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-owned-SQL-execution/v1", "state": "FAILED_NOT_ACCEPTED",
        "mode": args.mode, "source_freeze": [], "source_freeze_exact_after": False,
        "resource_samples": resources.samples, "tests_run": 0, "tests_passed": 0, "failed_tests": [],
        "executions": [], "actual_SQL_Docker_Cargo_or_native_executed": False,
        "original_driver_source_modified": False, "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "P09_gate": "OPEN", "product_complete": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.mode == "light":
            suite = light_suite()
            with patch("subprocess.Popen", side_effect=AssertionError("SQL_EXECUTION_LIGHT_CHILD_FORBIDDEN")), \
                    patch("subprocess.run", side_effect=AssertionError("SQL_EXECUTION_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("SQL_EXECUTION_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 116 and checked.wasSuccessful() and not checked.skipped,
                "SQL_EXECUTION_LIGHT_TEST_FAILED")
            row["state"] = "PASS_CONNECTED_EXECUTION_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        else:
            resources.start()
            for case, arguments in calls:
                resources.checkpoint_io()
                # product 진입 여부를 failure에도 보존한다. 실제 SQL 실행 증거는 원래 receipt로 판정한다.
                if args.mode == "product":
                    row["actual_SQL_Docker_Cargo_or_native_executed"] = None
                execution = execute_case(args.mode, case, arguments, resources, reader)
                row["executions"].append(execution)
                if args.mode == "missing-input":
                    worker_row = (execution.get("supervisor") or {}).get("worker_result") or {}
                    accounted = worker_row.get("accounted_call") or {}
                    c.require(execution["state"] == "ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE"
                        and accounted.get("state") == "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS"
                        and accounted.get("driver_error_code") == "sql_source_link_or_missing"
                        and accounted.get("reader_count") == 1 and accounted.get("source_final_hash_completed") is False
                        and worker_row.get("journal_write_count") == 0 and execution["original_receipt_pin"] is None
                        and execution["fallback_cleanup"] is None and execution["backend_container_cleanup_confirmed"] is None
                        and not subject.scoped_path(arguments[0]).exists() and not subject.scoped_path(arguments[1]).exists(),
                        "SQL_EXECUTION_MISSING_FIXTURE_NOT_ACCEPTED")
                else:
                    original = execution["original_receipt_summary"] or {}
                    # SQL=false만으로 Docker 실행까지 없었다고 단정하지 않는다.
                    row["actual_SQL_Docker_Cargo_or_native_executed"] = True if original.get("actual_SQL_executed") is True else None
                    c.require(execution["state"] == "ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE",
                        "SQL_EXECUTION_PRODUCT_COMPONENT_NOT_ACCEPTED")
            row["state"] = "PASS_THREE_CONNECTED_ORIGINAL_PRE_CONTAINER_FAILURES_NOT_SQL_OR_GATE" if args.mode == "missing-input" \
                else "PASS_ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", subject.closed_error(error)
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_EXECUTION_FINAL_FRESHNESS_FAILED"
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
            "failed_tests": row["failed_tests"], "executions": len(row["executions"]), "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    return 0 if row["state"].startswith("PASS_") and row["source_freeze_exact_after"] \
        and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None else 2


if __name__ == "__main__":
    if len(sys.argv) == 10 and sys.argv[1] == "--worker":
        raise SystemExit(worker(*sys.argv[2:]))
    raise SystemExit(main())
