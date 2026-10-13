"""P149 fresh exact source + mocked SQL IO/resources. No child, SQL, Docker or Cargo."""
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
from verify_bounded_pipe_io_light import EXTRA

SOURCES = list(EXTRA) + ["tools/p09/sql_percentage_resources.py",
    "tools/p09/tests/test_sql_percentage_resources.py", "tools/p09/verify_sql_percentage_resources_light.py",
    "implementation/p09/source-archive/p09-149-pre-sql-percentage-resource/source-preimages.v1.json",
    "tools/p09/run_resource_bounded_python.py", "tools/p09/run_formula_issuer_registry_sql_checks.py",
    "tools/p09/owned_sql_job.py", "tools/p09/tests/test_sql_job_integration.py",
    "implementation/p09/source-archive/p09-149-pre-owned-sql-job-integration/source-preimages.v1.json"]
SOURCES += ["tools/p09/live_sql_evidence_reader.py", "tools/p09/tests/test_live_sql_evidence_reader.py",
    "tools/p09/tests/test_audit_evidence_io.py",
    "implementation/p09/source-archive/p09-149-pre-live-sql-paced-reader/source-preimages.v1.json"]


def freeze():
    rows = c.pins()
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    for name in SOURCES:
        if name not in {row["path"] for row in rows}:
            rows.append(reader.pin(name))
    reader.finish()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows, started = c.Windows(), time.monotonic()
    destination = c.ROOT / f"implementation/p09/evidence/p09-149-sql-percentage-resource.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "fresh_SQL_resource_receipt_required")
    before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-SQL-percentage-resource-light/v1",
        "state": "DEFERRED_RESOURCE_PRESSURE_NOT_STARTED", "tests_run": 0, "tests_passed": 0,
        "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "self_resource_before": before, "logical_cpu_limit": 1, "priority": "BelowNormal",
        "actual_child_SQL_Docker_Cargo_native_or_full_audit_run": False,
        "host_SQL_children_aggregate_job_qualification": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    sample = before["system"]
    if sample["available_ram_percent"] >= c.POLICY["stop_ram_min_percent"] \
            and sample["commit_used_percent"] < c.POLICY["stop_commit_used_percent"] \
            and sample["system_cpu_percent"] < c.POLICY["emergency_cpu_percent"]:
        row["source_freeze"] = freeze()
        with patch("subprocess.Popen", side_effect=AssertionError("light_child_forbidden")), \
                patch("subprocess.run", side_effect=AssertionError("light_child_forbidden")), \
                patch("subprocess.call", side_effect=AssertionError("light_child_forbidden")), \
                patch("threading.Thread.start", side_effect=AssertionError("light_thread_forbidden")):
            from tests.test_sql_percentage_resources import SQLPercentageResourceTests
            from tests.test_sql_bounded_io_integration import SQLBoundedIOIntegrationTests
            from tests.test_sql_job_integration import SQLJobIntegrationTests
            checked = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLPercentageResourceTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLBoundedIOIntegrationTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLJobIntegrationTests)]))
        unsuccessful = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(unsuccessful),
            failed_tests=[test.id().split(".")[-1] for test, _ in checked.errors+checked.failures])
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = checked.testsRun == 20 and checked.wasSuccessful() and not checked.skipped and row["source_freeze_exact_after"]
        row["state"] = "PASS_SOURCE_AND_MOCK_SQL_RESOURCE_IO_NOT_ACTUAL_SQL_OR_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED"
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-started, 4)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
