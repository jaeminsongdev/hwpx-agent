"""Fresh bounded fixtures; no actual Docker, authority audit, Cargo or Git execution."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from conservative_maintenance import ROOT, Windows
from verify_audit_evidence_io import self_resource

SOURCES = ["tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py",
    "tools/p09/verify_container_absence_light.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/conservative_maintenance.py", "tools/p09/bounded_process_progress.py",
    "tools/p09/verify_audit_evidence_io.py",
    "implementation/p09/source-archive/p09-149-pre-batch-absence-audit/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-final-resource-check/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-live-bounded-absence/source-preimages.v1.json"]


def freeze():
    rows = []
    for name in SOURCES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.is_junction():
            raise ValueError("light_source_scope_invalid")
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows = Windows()  # Before source reads and tests: one CPU, BelowNormal.
    from tests.test_bounded_container_absence import BoundedContainerAbsenceTests
    destination = ROOT / f"implementation/p09/evidence/p09-149-container-absence.light-source-progress-run{args.run:02}.v1.json"
    if Path.cwd().resolve() != ROOT or destination.exists() or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_light_receipt_scope_required")
    before = freeze()
    resource_before = self_resource(windows)
    started = time.monotonic()
    with patch("subprocess.Popen", side_effect=AssertionError("light_child_creation_forbidden")), \
            patch("subprocess.call", side_effect=AssertionError("light_child_creation_forbidden")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(BoundedContainerAbsenceTests))
    after = freeze()
    resource_after = self_resource(windows)
    accepted = result.testsRun == 21 and result.wasSuccessful() and not result.skipped and before == after
    row = {"schema_version": "hwpx-agent.p09-container-absence-light-fixtures/v1",
        "state": "PASS_LIGHT_ABSENCE_FIXTURES_NOT_DOCKER_OR_PC_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED",
        "source_freeze": before, "source_freeze_exact_after": before == after,
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
        "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures+result.errors],
        "elapsed_seconds": round(time.monotonic()-started, 4), "logical_cpu_limit": 1, "priority": "BelowNormal",
        "self_resource_before": resource_before, "self_resource_after": resource_after,
        "self_cpu_seconds_during_checks": round(resource_after["cpu_seconds"]-resource_before["cpu_seconds"], 6),
        "memory_values_are_samples_not_peak": True,
        "query_structure": {"references_preserved": 12, "old_inspect_processes": 12,
            "new_inspect_batches": 2, "new_waiting_workers": 2,
            "timeout_seconds_per_batch": 10, "output_limit_bytes_per_stream": 32768},
        "actual_Docker_or_child_process_started": False, "authority_audit_or_Rust_SQL_native_run": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "live_inspector_lifecycle_verified": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
