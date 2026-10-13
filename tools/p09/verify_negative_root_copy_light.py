"""Explicit future light check; refuse low RAM before source reads/test imports. No children."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import time
import unittest

from conservative_maintenance import ROOT, POLICY, Windows
from verify_audit_evidence_io import self_resource

SOURCES = ["tools/p09/tests/test_authority_sql_current_audit.py", "tools/p09/tests/test_negative_root_copy.py",
    "tools/p09/verify_negative_root_copy_light.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
    "implementation/p09/source-archive/p09-149-pre-root-only-negative-copies/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-single-read-audit/source-preimages.v1.json"]


def freeze():
    rows = []
    for name in SOURCES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.is_junction():
            raise ValueError("light_source_scope_invalid")
        digest, size = hashlib.sha256(), 0
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                digest.update(chunk)
                size += len(chunk)
        rows.append({"path": name, "bytes": size, "sha256": digest.hexdigest()})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows = Windows()
    destination = ROOT / f"implementation/p09/evidence/p09-149-negative-root-copy.light-source-progress-run{args.run:02}.v1.json"
    if Path.cwd().resolve() != ROOT or destination.exists() or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_light_receipt_scope_required")
    resource_before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-negative-root-copy-light-verification/v1",
        "state": "DEFERRED_LOW_AVAILABLE_RAM_NOT_STARTED", "fixtures_started": False,
        "source_freeze": [], "source_freeze_exact_after": False, "tests_run": 0, "tests_passed": 0,
        "failed_tests": [], "logical_cpu_limit": 1, "priority": "BelowNormal",
        "minimum_available_ram_percent": POLICY["stop_ram_min_percent"],
        "self_resource_before": resource_before, "memory_values_are_samples_not_peak": True,
        "actual_authority_negative_tests_executed": False, "actual_child_or_Rust_SQL_native_run": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    if resource_before["system"]["available_ram_percent"] >= POLICY["stop_ram_min_percent"]:
        from tests.test_negative_root_copy import NegativeRootCopyTests
        row["source_freeze"] = freeze()
        started = time.monotonic()
        row["fixtures_started"] = True
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(NegativeRootCopyTests))
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = result.testsRun == 4 and result.wasSuccessful() and not result.skipped and row["source_freeze_exact_after"]
        row.update(state="PASS_LIGHT_ROOT_COPY_BOUNDARIES_NOT_AUTHORITY_SQL_OR_PC_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED",
            tests_run=result.testsRun, tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
            failed_tests=[test.id().split(".")[-1] for test, _ in result.failures+result.errors],
            elapsed_seconds=round(time.monotonic()-started, 4))
    row["self_resource_after"] = self_resource(windows)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "fixtures_started", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
