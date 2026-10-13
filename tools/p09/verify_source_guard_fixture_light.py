"""Source guards and tiny fixture checks only; no authority audit or child process."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from conservative_maintenance import ROOT, Windows
from verify_audit_evidence_io import self_resource

SOURCE = "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"
AUTHORITY = "tools/p09/run_formula_issuer_authority_sql_probe.py"
LIVE = "tools/p09/run_formula_issuer_live_sql_probe.py"
SOURCES = ["tools/p09/source_guard_fixture.py", "tools/p09/tests/test_source_guard_fixture.py",
    "tools/p09/tests/test_authority_sql_consumer_boundary.py", "tools/p09/tests/test_live_sql_consumer_boundary.py",
    "tools/p09/verify_source_guard_fixture_light.py", "tools/p09/audit_evidence_io.py",
    "tools/p09/conservative_maintenance.py", "tools/p09/verify_audit_evidence_io.py",
    SOURCE, AUTHORITY, LIVE, "tools/p09/run_formula_issuer_corpus_probe.py",
    "tools/p09/bounded_process_progress.py",
    "tools/p09/verify_formula_issuer_authority_current.py",
    "implementation/p09/source-archive/p09-149-pre-shared-source-fixtures/source-preimages.v1.json"]


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
    windows = Windows()  # Limits before source reads, test imports and fixtures.
    from audit_evidence_io import AuditEvidenceReader
    from tests.test_source_guard_fixture import SourceGuardFixtureTests
    from tests.test_authority_sql_consumer_boundary import AuthoritySQLConsumerBoundary
    from tests.test_live_sql_consumer_boundary import LiveSQLConsumerBoundary
    destination = ROOT / f"implementation/p09/evidence/p09-149-source-fixture.light-source-progress-run{args.run:02}.v1.json"
    if Path.cwd().resolve() != ROOT or destination.exists() or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_light_receipt_scope_required")
    before = freeze()
    resource_before = self_resource(windows)
    started = time.monotonic()
    original_read, observations = AuditEvidenceReader._read, []
    def observed_read(reader, name, parse=False):
        result = original_read(reader, name, parse)
        if name in {SOURCE, AUTHORITY, LIVE}:
            observations.append((name, parse))
        return result
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in
        (SourceGuardFixtureTests, AuthoritySQLConsumerBoundary, LiveSQLConsumerBoundary))
    with patch.object(AuditEvidenceReader, "_read", observed_read):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    after = freeze()
    resource_after = self_resource(windows)
    expected = Counter({(SOURCE, True): 2, (SOURCE, False): 2,
        (AUTHORITY, True): 1, (AUTHORITY, False): 1, (LIVE, True): 1, (LIVE, False): 1})
    reads_exact = Counter(observations) == expected
    released = all(not any(name in cls.__dict__ for name in ("source", "driver", "live", "_source_reader"))
        for cls in (AuthoritySQLConsumerBoundary, LiveSQLConsumerBoundary))
    accepted = result.testsRun == 24 and result.wasSuccessful() and not result.skipped \
        and before == after and reads_exact and released
    row = {"schema_version": "hwpx-agent.p09-source-fixture-light-verification/v1",
        "state": "PASS_LIGHT_SOURCE_GUARDS_AND_FIXTURES_NOT_SQL_PRODUCT_OR_PC_FREEZE_PROOF" if accepted else "FAILED_NOT_ACCEPTED",
        "source_freeze": before, "source_freeze_exact_after": before == after,
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
        "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures+result.errors],
        "elapsed_seconds": round(time.monotonic()-started, 4), "logical_cpu_limit": 1, "priority": "BelowNormal",
        "self_resource_before": resource_before, "self_resource_after": resource_after,
        "self_cpu_seconds_during_checks": round(resource_after["cpu_seconds"]-resource_before["cpu_seconds"], 6),
        "memory_values_are_samples_not_peak": True,
        "setup_read_profile": {"prior_two_setup_reads_per_test": 28,
            "current_bound_text_reads": sum(parse for _, parse in observations),
            "current_fresh_final_hash_reads": sum(not parse for _, parse in observations),
            "inventory_exact": reads_exact, "class_text_released": released,
            "additional_test_method_reads_unchanged": True,
            "class_bound_text_only_not_JSON_or_cross_run_cache": True},
        "original_source_guard_methods_AST_identical": result.wasSuccessful(),
        "actual_Docker_or_child_process_started": False, "authority_audit_or_Rust_SQL_native_run": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds", "setup_read_profile")}))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
