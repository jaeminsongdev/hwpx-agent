"""P149 owned host Job launcher: mocked guards + two small real Python trees, never SQL."""
import argparse
import io
import json
from pathlib import Path
import time
import unittest

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
from verify_audit_evidence_io import self_resource
from verify_sql_percentage_resources_light import freeze as base_freeze

EXTRA = ["tools/p09/owned_sql_job.py", "tools/p09/tests/test_owned_sql_job.py",
    "tools/p09/verify_owned_sql_job_light.py"]


def freeze():
    rows = base_freeze()
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    for name in EXTRA:
        if name not in {row["path"] for row in rows}:
            rows.append(reader.pin(name))
    reader.finish()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows, started = c.Windows(), time.monotonic()
    destination = c.ROOT / f"implementation/p09/evidence/p09-149-owned-SQL-job.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "fresh_owned_SQL_job_receipt_required")
    before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-owned-SQL-job-light/v1", "state": "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "self_resource_before": before, "logical_cpu_limit": 1, "priority": "BelowNormal", "owned_job_profiles": [],
        "actual_SQL_Docker_Cargo_native_or_full_audit_run": False, "SQL_driver_job_integration_complete": False,
        "SQL_driver_job_source_integration_complete": True,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    sample = before["system"]
    if sample["available_ram_percent"] >= c.POLICY["start_ram_min_percent"] \
            and sample["commit_used_percent"] < c.POLICY["stop_commit_used_percent"] \
            and sample["system_cpu_percent"] < c.POLICY["emergency_cpu_percent"]:
        row["source_freeze"] = freeze()
        from tests.test_owned_sql_job import OwnedSQLJobMockTests, OwnedSQLJobActualTests, OwnedSQLFactoryActualTests
        from tests.test_sql_job_integration import SQLJobIntegrationTests
        from tests.test_sql_percentage_resources import SQLPercentageResourceTests
        from tests.test_sql_bounded_io_integration import SQLBoundedIOIntegrationTests
        class Result(unittest.TextTestResult):
            def stopTest(self, test):
                row["owned_job_profiles"].extend(getattr(test, "owned_job_profiles", []))
                super().stopTest(test)
        checked = unittest.TextTestRunner(stream=io.StringIO(), resultclass=Result).run(unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(OwnedSQLJobMockTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(OwnedSQLJobActualTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(OwnedSQLFactoryActualTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(SQLPercentageResourceTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(SQLBoundedIOIntegrationTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(SQLJobIntegrationTests)]))
        unsuccessful = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(unsuccessful),
            failed_tests=[test.id().split(".")[-1] for test, _ in checked.errors+checked.failures])
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = checked.testsRun == 29 and checked.wasSuccessful() and not checked.skipped and row["source_freeze_exact_after"] \
            and len(row["owned_job_profiles"]) == 4 and all(profile["cleanup_confirmed"]
                and profile["owned_tree_empty"] and profile["job_handle_closed"]
                and profile["limits_readback"]["verified"] for profile in row["owned_job_profiles"])
        row["state"] = "PASS_OWNED_JOB_LAUNCHER_SOURCE_MOCK_AND_SMALL_PYTHON_TREES_NOT_SQL_OR_GATE" if accepted else "FAILED_NOT_ACCEPTED"
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-started, 4)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
