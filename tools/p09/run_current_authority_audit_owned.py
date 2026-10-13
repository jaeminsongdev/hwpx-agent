"""Run the unchanged whole current-r4 input audit under an owned aggregate Job.

全 입력/closing hash를 생략하지 않는다. 원래 PARTIAL/exit3와 새 host lifecycle 증거를
분리한다. audit worker 안에서는 subprocess/Thread.start를 금지한다.
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

import conservative_maintenance as c
import current_authority_audit_accounting as subject
from sql_cooperative_cancel import CancelEvent
from sql_call_supervisor import supervise_owned_call
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from sql_owned_execution import scoped_path, host_tree_closed
from live_sql_evidence_reader import LiveSQLReader
from run_supervised_sql_probe import SOURCES as EXECUTION_SOURCES
from verify_current_authority_sql_receipts import SOURCES as AUDIT_SOURCES

SELF = "tools/p09/run_current_authority_audit_owned.py"
SOURCES = list(dict.fromkeys(EXECUTION_SOURCES+AUDIT_SOURCES+[SELF,
    "tools/p09/current_authority_audit_accounting.py", "tools/p09/tests/test_current_authority_audit_accounting.py"]))


def worker(run, name):
    c.require(Path.cwd().resolve() == c.ROOT, "CURRENT_AUTHORITY_CALL_WORKER_ROOT")
    subject.original_receipt_path(run)
    import verify_current_authority_sql_receipts as audit
    event, row = CancelEvent.open(name), None
    try:
        with patch("subprocess.Popen", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_CHILD_FORBIDDEN")), \
                patch("subprocess.run", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_CHILD_FORBIDDEN")), \
                patch("threading.Thread.start", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_THREAD_FORBIDDEN")):
            row = subject.account_original_audit(audit, run, event)
    finally:
        event.close()
        if row is not None:
            row["child_event_closed"] = event.closed
    subject.decode_worker(json.dumps(row), run)
    print(json.dumps(row))
    return 0  # 프로토콜 종료일 뿐이다. 원래 exit3/PARTIAL은 그대로 전달한다.


def execute(run, resources):
    event, parent = CancelEvent.create(), None
    try:
        parent = supervise_owned_call([sys.executable, "-B", str(c.ROOT/SELF), "--worker", str(run), event.name],
            resources, event, lambda output: subject.decode_worker(output, run), maximum_seconds=600, grace_seconds=5)
    finally:
        try:
            event.close()
        except (ValueError, OSError) as error:
            if parent is None:
                parent = {"state": "FAILED_NOT_ACCEPTED"}
            parent["parent_event_close_error_code"] = subject.closed_error(error)
        if parent is not None:
            parent["parent_event_closed"] = event.closed
    return parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--light", action="store_true")
    parser.add_argument("--audit-run", type=int, choices=range(1, 100))
    args = parser.parse_args()
    c.require(Path.cwd().resolve() == c.ROOT and (args.light or args.audit_run is not None),
        "CURRENT_AUTHORITY_CALL_PARENT_SCOPE")
    if not args.light:
        subject.original_receipt_path(args.audit_run)
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-current-authority-owned.{kind}-run{args.run:02}.v1.json", fresh=True)
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-owned-current-authority-audit/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "supervisor": None,
        "original_receipt_pin": None, "original_audit_summary": None,
        "actual_whole_current_input_byte_audit_executed": False,
        "actual_SQL_Docker_Cargo_native_formatter_executed": False, "full_current_authority_audit_executed": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN",
        "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.light:
            from tests.test_current_authority_sql_receipts import CurrentAuthoritySQLReceiptTests
            from tests.test_current_authority_audit_accounting import CurrentAuthorityAuditAccountingTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in
                (CurrentAuthoritySQLReceiptTests, CurrentAuthorityAuditAccountingTests))
            with patch("subprocess.Popen", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch("subprocess.run", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("CURRENT_AUTHORITY_CALL_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 31 and checked.wasSuccessful() and not checked.skipped,
                "CURRENT_AUTHORITY_CALL_LIGHT_TEST_FAILED")
            row["state"] = "PASS_OWNED_AUTHORITY_CALL_CONTRACT_ONLY_NOT_FULL_AUDIT_OR_GATE"
        else:
            resources.start()
            parent = row["supervisor"] = execute(args.audit_run, resources)
            name = subject.original_receipt_path(args.audit_run, fresh=False)
            if scoped_path(name).is_file():
                row["original_receipt_pin"] = reader.pin(name)
                original = reader.json(name)
                row["actual_whole_current_input_byte_audit_executed"] = original.get("actual_current_input_byte_binding_executed") is True
            else:
                original = None
            c.require(isinstance(parent, dict) and host_tree_closed(parent)
                and parent.get("state") == "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
                and parent.get("forced_termination") is False and parent.get("parent_event_closed") is True,
                "CURRENT_AUTHORITY_CALL_LIFECYCLE_UNVERIFIED")
            worker_row = subject.decode_worker(json.dumps(parent["worker_result"]), args.audit_run)
            c.require(worker_row["state"] == "ORIGINAL_AUTHORITY_AUDIT_EXIT_ACCOUNTED_NOT_SQL_OR_GATE"
                and worker_row["resource_count"] == 1 and worker_row["resource_stop_latched"] is False
                and worker_row["resource_stop_reason"] is None and worker_row["original_error_code"] is None,
                "CURRENT_AUTHORITY_CALL_ORIGINAL_FAILURE")
            row["original_audit_summary"] = subject.classify_original_receipt(original, worker_row["original_return_code"])
            row["state"] = "PARTIAL_OWNED_CURRENT_SQL_RECEIPT_AUDIT_REQUIRED_REPLAYS_MISSING" if \
                row["original_audit_summary"]["missing_required_replays"] else "CURRENT_OWNED_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE"
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
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "CURRENT_AUTHORITY_CALL_FINAL_FRESHNESS_FAILED"
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
            "failed_tests": row["failed_tests"], "original_exit_code": (row["original_audit_summary"] or {}).get("original_exit_code"),
            "wrapper_wall_seconds": row["wrapper_wall_seconds"]}))
    final = row["source_freeze_exact_after"] and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None
    return 0 if final and row["state"] in {"PASS_OWNED_AUTHORITY_CALL_CONTRACT_ONLY_NOT_FULL_AUDIT_OR_GATE",
        "CURRENT_OWNED_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE"} else 3


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        raise SystemExit(worker(int(sys.argv[2]), sys.argv[3]))
    raise SystemExit(main())
