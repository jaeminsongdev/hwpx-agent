"""Fresh P147 IO-only source/mock proof; no full audit or external child tools."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from conservative_maintenance import ROOT, POLICY, Windows
from verify_audit_evidence_io import self_resource

SOURCES = ["tools/p09/verify_formula_issuer_live_current.py", "tools/p09/audit_evidence_io.py",
    "tools/p09/tests/test_live_audit_io_integration.py", "tools/p09/verify_live_audit_io_light.py",
    "tools/p09/tests/test_audit_evidence_io.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
    "implementation/p09/source-archive/p09-149-pre-live-audit-bound-io/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-single-read-audit/source-preimages.v1.json",
    "tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py",
    "tools/p09/bounded_process_progress.py", "tools/p09/tests/test_live_absence_integration.py",
    "tools/p09/verify_live_absence_light.py",
    "implementation/p09/source-archive/p09-149-pre-live-bounded-absence/source-preimages.v1.json"]


def freeze():
    rows = []
    for name in SOURCES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.is_junction():
            raise ValueError("live_io_source_scope_invalid")
        digest, size = hashlib.sha256(), 0
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                size += len(chunk)
                digest.update(chunk)
        rows.append({"path": name, "bytes": size, "sha256": digest.hexdigest()})
    return rows


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    windows = Windows()
    destination = ROOT / f"implementation/p09/evidence/p09-149-live-audit-io.light-source-progress-run{args.run:02}.v1.json"
    if Path.cwd().resolve() != ROOT or destination.exists() or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_live_io_receipt_scope_required")
    before = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-live-audit-io-light/v1",
        "state": "DEFERRED_LOW_AVAILABLE_RAM_NOT_STARTED", "tests_run": 0, "tests_passed": 0,
        "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "self_resource_before": before, "logical_cpu_limit": 1, "priority": "BelowNormal",
        "actual_child_tools_run": False, "full_live_or_authority_audit_run": False,
        "actual_Cargo_Rust_compile_product_EXE_SQL_native_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    if before["system"]["available_ram_percent"] >= POLICY["stop_ram_min_percent"]:
        row["source_freeze"] = freeze()
        with patch("subprocess.Popen", side_effect=AssertionError("light_child_creation_forbidden")), \
                patch("subprocess.call", side_effect=AssertionError("light_child_creation_forbidden")):
            from tests.test_audit_evidence_io import AuditEvidenceIOTests
            from tests.test_live_audit_io_integration import LiveAuditIOIntegrationTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                for cls in (AuditEvidenceIOTests, LiveAuditIOIntegrationTests))
            checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        unsuccessful = {test.id() for test, _ in checked.errors+checked.failures+checked.skipped
            if isinstance(test, unittest.TestCase)}
        row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(unsuccessful),
            suite_error_count=len(checked.errors),
            failed_tests=[test.id().split(".")[-1] for test, _ in checked.errors+checked.failures])
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = checked.testsRun == 23 and checked.wasSuccessful() and not checked.skipped \
            and row["source_freeze_exact_after"]
        row["state"] = "PASS_LIGHT_P147_BOUND_IO_NOT_FULL_AUDIT_PRODUCT_OR_PC_FREEZE_PROOF" \
            if accepted else "FAILED_NOT_ACCEPTED"
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-started, 4)
    row["elapsed_scope"] = "main_entry_through_final_resource_sample_excludes_python_startup_and_receipt_write"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
