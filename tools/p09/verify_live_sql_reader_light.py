"""P149 source/mock reader integration and immutable small manifest IO; no child/SQL."""
import argparse
import io
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
from verify_audit_evidence_io import self_resource
from verify_sql_percentage_resources_light import freeze as base_freeze


def freeze():
    rows = base_freeze()
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    rows.append(reader.pin("tools/p09/verify_live_sql_reader_light.py"))
    rows.append(reader.pin("implementation/p09/source-archive/p09-149-pre-reader-mutation-error-code-repair/source-preimages.v1.json"))
    reader.finish()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows, started = c.Windows(), time.monotonic()
    destination = c.ROOT / f"implementation/p09/evidence/p09-149-live-SQL-reader.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "fresh_live_SQL_reader_receipt_required")
    before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-live-SQL-reader-light/v1", "state": "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "self_resource_before": before, "logical_cpu_limit": 1, "priority": "BelowNormal", "actual_reader_observations": [],
        "actual_child_SQL_Docker_Cargo_native_or_full_audit_run": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    sample = before["system"]
    if sample["available_ram_percent"] >= c.POLICY["start_ram_min_percent"] \
            and sample["commit_used_percent"] < c.POLICY["stop_commit_used_percent"] \
            and sample["system_cpu_percent"] < c.POLICY["emergency_cpu_percent"]:
        row["source_freeze"] = freeze()
        with patch("subprocess.Popen", side_effect=AssertionError("light_child_forbidden")), \
                patch("subprocess.run", side_effect=AssertionError("light_child_forbidden")), \
                patch("subprocess.call", side_effect=AssertionError("light_child_forbidden")), \
                patch("threading.Thread.start", side_effect=AssertionError("light_thread_forbidden")):
            from tests.test_live_sql_evidence_reader import LiveSQLReaderTests, LiveSQLReaderActualTests
            from tests.test_audit_evidence_io import AuditEvidenceIOTests
            from tests.test_sql_percentage_resources import SQLPercentageResourceTests
            from tests.test_sql_bounded_io_integration import SQLBoundedIOIntegrationTests
            from tests.test_sql_job_integration import SQLJobIntegrationTests
            class Result(unittest.TextTestResult):
                def stopTest(self, test):
                    if hasattr(test, "actual_reader_summary"):
                        row["actual_reader_observations"].append(test.actual_reader_summary)
                    super().stopTest(test)
            checked = unittest.TextTestRunner(stream=io.StringIO(), resultclass=Result).run(unittest.TestSuite([
                unittest.defaultTestLoader.loadTestsFromTestCase(LiveSQLReaderTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(LiveSQLReaderActualTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(AuditEvidenceIOTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLPercentageResourceTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLBoundedIOIntegrationTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLJobIntegrationTests)]))
        unsuccessful = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(unsuccessful),
            failed_tests=[test.id().split(".")[-1] for test, _ in checked.errors+checked.failures])
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = checked.testsRun == 45 and checked.wasSuccessful() and not checked.skipped and row["source_freeze_exact_after"] \
            and len(row["actual_reader_observations"]) == 1 and row["actual_reader_observations"][0]["finished"]
        row["state"] = "PASS_PACED_FRESH_SQL_READER_SOURCE_MOCK_AND_SMALL_MANIFEST_NOT_SQL_OR_GATE" if accepted else "FAILED_NOT_ACCEPTED"
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-started, 4)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
