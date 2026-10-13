"""Isolated target compiler adapter: reviewed source/mocks, no actual child tools."""
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
import build_current_issuer_probe as subject
from sql_percentage_resources import PercentageResources
from verify_current_issuer_build_inputs_light import SOURCES as INPUT_SOURCES

SOURCES = INPUT_SOURCES+subject.OWN_SOURCES+[subject.CANDIDATE_PIN["path"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-current-issuer-compiler.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "fresh_current_compiler_light_receipt_required")
    resources = PercentageResources()
    started = time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-current-issuer-compiler-light/v1", "state": "FAILED_NOT_ACCEPTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "samples": resources.samples, "actual_Cargo_Rustc_SQL_Docker_native_child_run": False,
        "actual_current_compiler_qualified": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = AuditEvidenceReader(c.ROOT, resources.checkpoint_io)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        from tests.test_build_current_issuer_probe import BuildCurrentIssuerProbeTests
        from tests.test_current_issuer_build_inputs import CurrentIssuerBuildInputsTests
        from tests.test_owned_probe_build import OwnedProbeBuildTests
        from tests.test_owned_sql_job import OwnedSQLJobMockTests
        with patch.object(subprocess, "Popen", side_effect=AssertionError("no_child_in_light_verification")), \
                patch.object(threading.Thread, "start", side_effect=AssertionError("no_thread_in_light_verification")):
            suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in
                (BuildCurrentIssuerProbeTests, CurrentIssuerBuildInputsTests, OwnedProbeBuildTests, OwnedSQLJobMockTests)])
            result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        failed = {getattr(test, "test_case", test).id() for test, _ in result.errors+result.failures+result.skipped}
        row.update(tests_run=result.testsRun, tests_passed=result.testsRun-len(failed),
            failed_tests=sorted(test.split(".")[-1] for test in failed))
        reader.finish()
        row["source_freeze_exact_after"] = True
        row["bounded_input_IO"] = {"read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
            "bound_inputs": len(reader.snapshots), "final_fresh_hashes": reader.final_fresh_hashes}
        if result.testsRun == 68 and result.wasSuccessful() and not result.skipped:
            row["state"] = "PASS_ISOLATED_COMPILER_ADAPTER_SOURCE_MOCK_ONLY_NOT_BUILD_SQL_OR_GATE"
    except (ValueError, OSError) as error:
        row["error_code"] = str(error) if isinstance(error, ValueError) else "current_compiler_light_operation_failed"
    finally:
        resources.done.set()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
