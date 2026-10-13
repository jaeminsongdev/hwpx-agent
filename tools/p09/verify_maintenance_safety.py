"""Light policy and owned Python-process fixtures. No Cargo, SQL, native or Git launches."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
from verify_audit_evidence_io import self_resource


def freeze():
    rows = c.pins()
    for name in ("tools/p09/verify_maintenance_safety.py", "tools/p09/verify_audit_evidence_io.py"):
        path = c.ROOT / name
        c.require(path.is_file() and not path.is_symlink() and not path.is_junction(), "light_source_scope_invalid")
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows = c.Windows()
    from tests.test_conservative_maintenance import PolicyTests
    destination = c.ROOT / f"implementation/p09/evidence/p09-149-runner-safety.light-source-progress-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists()
        and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "fresh_light_receipt_required")
    before = freeze()
    resource_before = self_resource(windows)
    started = time.monotonic()
    owned_job_observations = []
    console_helper_bindings = []
    class SafetyResult(unittest.TextTestResult):
        def stopTest(self, test):
            for binding in getattr(test, "owned_console_helper_bindings", []):
                # Closed booleans/PID only. Never retain system path or raw exception details.
                console_helper_bindings.append({"pid": binding["pid"],
                    "system_image_match": binding["system_image_match"] is True,
                    "affinity_matches": binding["affinity_matches"] is True,
                    "priority_matches": binding["priority_matches"] is True})
            super().stopTest(test)
    accounting = c.Windows.accounting
    def observed_accounting(instance, job):
        row = accounting(instance, job)
        if len(owned_job_observations) < 24:
            owned_job_observations.append(row)
        return row
    with patch.object(c.Windows, "accounting", observed_accounting):
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=SafetyResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests))
    elapsed = round(time.monotonic()-started, 4)
    after = freeze()
    resource_after = self_resource(windows)
    accepted = result.testsRun == 12 and result.wasSuccessful() and not result.skipped and before == after
    failed = []
    for test, detail in result.failures + result.errors:
        mismatch = re.search(r"AssertionError: (\d+) != (\d+)", detail)
        failed.append({"test": test.id().split(".")[-1],
            "equality_count_mismatch": [int(mismatch[1]), int(mismatch[2])] if mismatch else None})
    row = {"schema_version": "hwpx-agent.p09-runner-safety-light-fixtures/v1",
        "state": "PASS_LIGHT_RUNNER_SAFETY_NOT_RUST_SQL_NATIVE_OR_PC_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED",
        "source_freeze": before, "source_freeze_exact_after": before == after,
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
        "failed_tests": failed, "elapsed_seconds": elapsed,
        "profile": c.POLICY, "self_resource_before": resource_before, "self_resource_after": resource_after,
        "self_cpu_seconds_during_checks": round(resource_after["cpu_seconds"]-resource_before["cpu_seconds"], 6),
        "memory_values_are_samples_not_peak": True,
        "owned_job_observations": owned_job_observations,
        "console_helper_bindings": console_helper_bindings,
        "actual_Rust_SQL_native_or_authority_audit_run": False, "owned_python_job_smokes_run": True,
        "new_git_started": False, "foreign_processes_modified": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
