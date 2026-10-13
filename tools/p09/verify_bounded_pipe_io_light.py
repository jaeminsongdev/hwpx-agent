"""P149 bounded pipe input/output and owned Python Job smokes. Never SQL/Cargo/native."""
import argparse
import io
import json
import time
import unittest

import conservative_maintenance as subject
from audit_evidence_io import AuditEvidenceReader
from verify_audit_evidence_io import self_resource

EXTRA = ["tools/p09/tests/test_bounded_process_progress.py", "tools/p09/verify_bounded_pipe_io_light.py",
    "tools/p09/verify_audit_evidence_io.py",
    "tools/p09/tests/test_sql_bounded_io_integration.py",
    "tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py",
    "implementation/p09/source-archive/p09-149-pre-live-sql-bounded-io/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-bounded-stdin-capture/source-preimages.v1.json",
    "tools/p09/sql_percentage_resources.py", "tools/p09/tests/test_sql_percentage_resources.py",
    "implementation/p09/source-archive/p09-149-pre-sql-percentage-resource/source-preimages.v1.json"]


def freeze():
    rows = subject.pins()
    reader = AuditEvidenceReader(subject.ROOT, lambda: None)
    for path in EXTRA:
        rows.append(reader.pin(path))
    reader.finish()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows = subject.Windows()
    started = time.monotonic()
    destination = subject.ROOT / f"implementation/p09/evidence/p09-149-bounded-pipe-io.light-source-progress-run{args.run:02}.v1.json"
    subject.require(not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "fresh_pipe_receipt_required")
    before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-bounded-pipe-io-light/v1", "state": "DEFERRED_LOW_RAM_NOT_STARTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [],
        "source_freeze_exact_after": False, "self_resource_before": before, "owned_job_observations": [],
        "actual_SQL_Cargo_native_or_full_audit_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    if before["system"]["available_ram_percent"] >= subject.POLICY["stop_ram_min_percent"]:
        row["source_freeze"] = freeze()
        from tests.test_bounded_process_progress import BoundedProcessProgressTests
        from tests.test_sql_bounded_io_integration import SQLBoundedIOIntegrationTests
        class Result(unittest.TextTestResult):
            def stopTest(self, test):
                row["owned_job_observations"].extend(getattr(test, "owned_job_observations", []))
                super().stopTest(test)
        checked = unittest.TextTestRunner(stream=io.StringIO(), resultclass=Result).run(
            unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(BoundedProcessProgressTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(SQLBoundedIOIntegrationTests)]))
        unsuccessful = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(unsuccessful),
            failed_tests=[test.id().split(".")[-1] for test, _ in checked.errors+checked.failures])
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = checked.testsRun == 19 and checked.wasSuccessful() and not checked.skipped \
            and row["source_freeze_exact_after"] and len(row["owned_job_observations"]) == 4 \
            and all(observation["active_processes"] == 0 for observation in row["owned_job_observations"])
        row["state"] = "PASS_BOUNDED_PIPE_IO_AND_OWNED_PYTHON_SMOKES_NOT_SQL_OR_GATE" if accepted else "FAILED_NOT_ACCEPTED"
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-started, 4)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
