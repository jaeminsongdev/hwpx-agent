"""Paced current-r4 receipt/input audit; no SQL, Docker, compiler or formatter."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import threading
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import current_authority_sql_receipts as subject
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_issuer_sql_build_contract import SOURCES as CONTRACT_SOURCES

SELF = "tools/p09/verify_current_authority_sql_receipts.py"
SOURCES = list(dict.fromkeys(CONTRACT_SOURCES+[SELF, "tools/p09/current_authority_sql_receipts.py",
    "tools/p09/tests/test_current_authority_sql_receipts.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/verify_formula_issuer_live_current.py", subject.ARCHIVE, subject.MANIFEST,
    *subject.CURRENT_RUNS.values(), "implementation/p09/evidence/p09-146-corpus-consumer-run10.v1.json",
    "implementation/p09/evidence/p09-148-authority-consumer-run05.v1.json",
    "target/p09-121-resource-optimized/p143-issuer-product-build-r14.json",
    "implementation/p09/source-archive/p09-149-pre-current-authority-closed-error-encoding-repair/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-current-authority-final-exit-guard/source-preimages.v1.json"]))


def receipt_exit_code(row):
    final = row.get("source_freeze_exact_after") is True and row.get("resource_watcher_cleanup_confirmed") is True \
        and row.get("resource_stop_reason") is None
    accepted = row.get("state") == "PASS_CURRENT_AUTHORITY_RECEIPT_CONTRACT_ONLY_NOT_SQL_OR_GATE" or \
        (row.get("state") == "CURRENT_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE"
            and row.get("all_six_current_replays_validated") is True)
    return 0 if final and accepted else 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    kind = "actual" if args.audit else "light"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-current-authority-SQL-receipts.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "CURRENT_AUTHORITY_FRESH_RECEIPT")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-current-authority-SQL-receipt-audit/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "validated_current_cases": [],
        "missing_required_replays": subject.missing_replays({}), "required_replay_count": 6,
        "all_six_current_replays_validated": False, "actual_current_input_byte_binding_executed": False,
        "actual_SQL_Docker_Cargo_native_formatter_or_child_executed": False,
        "full_current_authority_audit_executed": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        with patch.object(subprocess, "Popen", side_effect=AssertionError("CURRENT_AUTHORITY_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("CURRENT_AUTHORITY_CHILD_FORBIDDEN")), \
                patch.object(threading.Thread, "start", side_effect=AssertionError("CURRENT_AUTHORITY_THREAD_FORBIDDEN")):
            if args.audit:
                contract = subject.build_contract
                c.require(reader.pin(contract.CURRENT_BUILD_PIN["path"]) == contract.CURRENT_BUILD_PIN,
                    "CURRENT_AUTHORITY_BUILD_RECEIPT_DRIFT")
                build = reader.json(contract.CURRENT_BUILD_PIN["path"])
                sources, protected, helpers, executable = contract.build_contract(build, "current_r4")
                manifest = reader.json(subject.MANIFEST)
                groups = [sources.values(), protected.values(), helpers.values(), [executable]]
                cases = {}
                for (case, mode), name in subject.CURRENT_RUNS.items():
                    resources.checkpoint_io()
                    run = reader.json(name)
                    subject.validate_current_case(run, build, manifest, case, mode,
                        "unchanged" if mode == "original" else "changed")
                    cases[(case, mode)] = run
                    groups.extend((run["source_freeze"], run["protected_executables"], [run["frozen_original_source_pin"]]))
                    row["validated_current_cases"].append({"case": case, "input_mode": mode,
                        "receipt_pin": reader.pin(name), "SQL_checks": len(run["product_probe"]["result"]["checks"]),
                        "component_only": True})
                merged = subject.merge_pins(groups)
                row["exact_union_input_count"] = len(merged)
                print("P149_CURRENT_AUTHORITY_PHASE:fresh_union_inputs", flush=True)
                for name, expected in merged.items():
                    c.require(reader.pin(contract.direct_name(name)) == expected, "CURRENT_AUTHORITY_INPUT_BYTES_DRIFT")
                row["actual_current_input_byte_binding_executed"] = True
                row["missing_required_replays"] = subject.missing_replays(cases)
                if not row["missing_required_replays"]:
                    subject.require_all_replays(cases, build, manifest)
                    row["all_six_current_replays_validated"] = True
                row["state"] = "CURRENT_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE" if \
                    row["all_six_current_replays_validated"] else "PARTIAL_CURRENT_SQL_RECEIPT_AUDIT_REQUIRED_REPLAYS_MISSING"
            else:
                from tests.test_current_authority_sql_receipts import CurrentAuthoritySQLReceiptTests
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(
                    unittest.defaultTestLoader.loadTestsFromTestCase(CurrentAuthoritySQLReceiptTests))
                failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
                row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                    failed_tests=sorted(name.split(".")[-1] for name in failed))
                c.require(checked.testsRun == 21 and checked.wasSuccessful() and not checked.skipped,
                    "CURRENT_AUTHORITY_CONTRACT_TEST_FAILED")
                row["state"] = "PASS_CURRENT_AUTHORITY_RECEIPT_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "CURRENT_AUTHORITY_OPERATION_FAILED"
        row["state"] = "FAILED_NOT_ACCEPTED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "CURRENT_AUTHORITY_REDACTED_FAILURE"
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "CURRENT_AUTHORITY_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({"state": row["state"], "tests_run": row["tests_run"], "tests_passed": row["tests_passed"],
            "failed_tests": row["failed_tests"], "validated_current_cases": len(row["validated_current_cases"]),
            "missing_required_replays": len(row["missing_required_replays"]), "elapsed_seconds": row["elapsed_seconds"]}))
    return receipt_exit_code(row)


if __name__ == "__main__":
    raise SystemExit(main())
