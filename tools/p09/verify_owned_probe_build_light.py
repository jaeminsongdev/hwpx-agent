"""Owned probe build source/mock qualification only; absolutely no compiler child."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import threading
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
import owned_probe_build as subject
from sql_percentage_resources import PercentageResources

SOURCES = subject.SOURCES + ["tools/p09/tests/test_owned_sql_job.py"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    destination = c.ROOT / f"implementation/p09/evidence/p09-149-owned-probe-build.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists()
        and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "fresh_owned_probe_build_light_receipt_required")
    resources = PercentageResources()
    started = time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-owned-probe-build-light/v1", "state": "FAILED_NOT_ACCEPTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [],
        "source_freeze_exact_after": False, "samples": resources.samples,
        "compiler_job_source_integration_complete": False, "actual_compiler_job_qualification": False,
        "actual_Cargo_Rustc_SQL_Docker_native_child_or_full_audit_run": False,
        "new_git_started": False, "raw_logs_printed_or_saved": False,
        "system_or_Defender_or_WSL_settings_changed": False,
        "P09_gate": "OPEN", "product_complete": False, "stop_reason": None}
    try:
        resources.admit()
        reader = AuditEvidenceReader(c.ROOT, resources.checkpoint_io)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        from tests.test_owned_probe_build import OwnedProbeBuildTests
        from tests.test_owned_sql_job import OwnedSQLJobMockTests
        # Any accidental compiler/tool launch or sampler/capture thread is an immediate test failure.
        with patch.object(subprocess, "Popen", side_effect=AssertionError("no_child_in_light_verification")), \
                patch.object(threading.Thread, "start", side_effect=AssertionError("no_thread_in_light_verification")):
            suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(OwnedProbeBuildTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(OwnedSQLJobMockTests)])
            checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
            failed_tests=sorted(test.split(".")[-1] for test in failed))
        reader.finish()
        row["source_freeze_exact_after"] = True
        row["bounded_input_IO"] = {"read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
            "bound_inputs": len(reader.snapshots), "final_fresh_hashes": reader.final_fresh_hashes}
        row["compiler_job_source_integration_complete"] = checked.testsRun == 23 and checked.wasSuccessful() \
            and not checked.skipped and row["source_freeze_exact_after"]
        if row["compiler_job_source_integration_complete"]:
            row["state"] = "PASS_COMPILER_SUPERVISOR_SOURCE_MOCK_ONLY_NOT_BUILD_SQL_OR_GATE"
    except (ValueError, OSError) as error:
        row["stop_reason"] = subject.closed_error(error)
    finally:
        resources.done.set()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
