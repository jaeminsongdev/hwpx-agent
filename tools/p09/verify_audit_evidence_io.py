"""Fresh light receipt for bounded IO fixtures only; never calls the authority audit."""
import argparse
import ctypes
import hashlib
import io
import json
from pathlib import Path
import time
import unittest

from conservative_maintenance import ROOT, POLICY, ProcessMemory, Windows

SOURCES = ["tools/p09/audit_evidence_io.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/tests/test_audit_evidence_io.py", "tools/p09/verify_audit_evidence_io.py",
    "tools/p09/conservative_maintenance.py",
    "implementation/p09/source-archive/p09-149-pre-single-read-audit/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-paced-audit-reads/source-preimages.v1.json"]


def freeze():
    rows = []
    for name in SOURCES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.is_junction():
            raise ValueError("light_source_scope_invalid")
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


def self_resource(windows):
    # GetSystemTimes has finite clock resolution. An immediate sample is unavailable,
    # not CPU=0. Retry only that observation case within a short bounded interval.
    for attempt in range(6):
        try:
            system = windows.sample()
            break
        except ValueError as error:
            if str(error) != "CPU_SAMPLE_INTERVAL_MISSING" or attempt == 5:
                raise
            time.sleep(0.02)
    memory = ProcessMemory()
    memory.size = ctypes.sizeof(memory)
    observed = bool(windows.k.K32GetProcessMemoryInfo(windows.k.GetCurrentProcess(),
        ctypes.byref(memory), memory.size))
    return {"cpu_seconds": time.process_time(), "memory_observed": observed,
        "working_set_mib": round(memory.ws / 1048576, 2) if observed else None,
        "private_mib": round(memory.private / 1048576, 2) if observed else None,
        "system": system}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    # One CPU/BelowNormal before imports, source reads and fixtures. No child process or heavy task.
    windows = Windows()
    destination = ROOT / f"implementation/p09/evidence/p09-149-audit-io.light-source-progress-run{args.run:02}.v1.json"
    if destination.exists() or Path.cwd().resolve() != ROOT or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_light_receipt_scope_required")
    resource_before = self_resource(windows)
    if resource_before["system"]["available_ram_percent"] < POLICY["stop_ram_min_percent"]:
        row = {"schema_version": "hwpx-agent.p09-audit-io-light-fixtures/v1",
            "state": "DEFERRED_LOW_AVAILABLE_RAM_NOT_STARTED", "fixtures_started": False,
            "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [],
            "source_freeze_exact_after": False, "self_resource_before": resource_before,
            "logical_cpu_limit": 1, "priority": "BelowNormal",
            "minimum_available_ram_percent": POLICY["stop_ram_min_percent"],
            "actual_Rust_SQL_native_or_authority_audit_run": False,
            "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
            "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed")}))
        return 2
    from tests.test_audit_evidence_io import AuditEvidenceIOTests
    before = freeze()
    started = time.monotonic()
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditEvidenceIOTests))
    after = freeze()
    resource_after = self_resource(windows)
    elapsed = round(time.monotonic() - started, 4)
    accepted = result.testsRun == 17 and result.wasSuccessful() and not result.skipped and before == after
    row = {"schema_version": "hwpx-agent.p09-audit-io-light-fixtures/v1",
        "state": "PASS_LIGHT_IO_FIXTURES_NOT_RUST_SQL_NATIVE_OR_PC_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED",
        "source_freeze": before, "source_freeze_exact_after": before == after,
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
        "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures + result.errors],
        "elapsed_seconds": elapsed, "logical_cpu_limit": 1, "priority": "BelowNormal",
        "self_resource_before": resource_before, "self_resource_after": resource_after,
        "self_cpu_seconds_during_checks": round(resource_after["cpu_seconds"]-resource_before["cpu_seconds"], 6),
        "memory_values_are_samples_not_peak": True,
        "hash_chunk_bytes": 65536, "maximum_parse_bytes": 16777216,
        "io_pacing": {"read_bytes_per_second": 8388608, "burst_bytes": 65536,
            "shared_across_files_and_final_hash": True, "idle_credit_burst_capped": True,
            "reserve_before_read": True, "short_read_and_EOF_refund": True},
        "json_read_pass_fixture": {"before_pin_parse_final": 3, "after_bound_parse_final": 2,
            "same_bytes_and_digest_verified": accepted, "final_fresh_hash_retained": accepted},
        "actual_Rust_SQL_native_or_authority_audit_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
