"""Small mock boundaries plus optional fixed-input formatter smoke, never a product build/audit."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import unittest

from conservative_maintenance import ROOT, POLICY, Windows
from verify_audit_evidence_io import self_resource

SOURCES = ["tools/p09/bounded_audit_tools.py", "tools/p09/tests/test_bounded_audit_tools.py",
    "tools/p09/verify_bounded_audit_tools_light.py", "tools/p09/conservative_maintenance.py",
    "tools/p09/verify_audit_evidence_io.py"]


def freeze():
    rows = []
    names = SOURCES + [name for name in ("rustfmt.toml", ".rustfmt.toml", "rust-toolchain.toml", "rust-toolchain")
        if (ROOT / name).exists()]
    for name in names:
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.is_junction():
            raise ValueError("light_source_scope_invalid")
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


def main():
    main_started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    parser.add_argument("--live-rustfmt-smoke", action="store_true")
    args = parser.parse_args()
    windows = Windows()
    destination = ROOT / f"implementation/p09/evidence/p09-149-bounded-audit-tools.light-source-progress-run{args.run:02}.v1.json"
    if Path.cwd().resolve() != ROOT or destination.exists() or not destination.parent.is_dir() \
            or destination.parent.is_symlink() or destination.parent.is_junction():
        raise ValueError("fresh_light_receipt_scope_required")
    before_resource = self_resource(windows)
    row = {"schema_version": "hwpx-agent.p09-bounded-audit-tool-light-verification/v1",
        "state": "DEFERRED_LOW_AVAILABLE_RAM_NOT_STARTED", "fixtures_started": False,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [],
        "source_freeze_exact_after": False, "self_resource_before": before_resource,
        "logical_cpu_limit": 1, "priority": "BelowNormal", "raw_logs_printed_or_saved": False,
        "actual_rustfmt_smoke_attempted": False, "rustfmt_smoke_accepted": False,
        "actual_rg_inventory_run": False, "full_authority_or_negative_audit_run": False,
        "actual_Cargo_Rust_compile_product_EXE_SQL_native_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "P09_gate": "OPEN", "product_complete": False}
    if before_resource["system"]["available_ram_percent"] >= POLICY["stop_ram_min_percent"]:
        from tests.test_bounded_audit_tools import BoundedAuditToolsTests
        row["source_freeze"] = freeze()
        started = time.monotonic()
        row["fixtures_started"] = True
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(BoundedAuditToolsTests))
        row.update(tests_run=result.testsRun,
            tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
            failed_tests=[test.id().split(".")[-1] for test, _ in result.failures+result.errors])
        accepted = result.testsRun == 20 and result.wasSuccessful() and not result.skipped
        if accepted and args.live_rustfmt_smoke:
            from bounded_audit_tools import run_audit_tool
            text = "fn main(){let _value=1;}\n"
            expected = "fn main() {\n    let _value = 1;\n}\n"
            row["actual_rustfmt_smoke_attempted"] = True
            try:
                checked = run_audit_tool("rustfmt-stdin", text)
                row["rustfmt_smoke_exit_code"] = checked.returncode
                diagnostic = re.fullmatch(r"P149_AUDIT_ERROR:(audit_tool_[a-z_]+|[A-Z_]+)\n", checked.stderr)
                row["rustfmt_smoke_error_code"] = diagnostic[1] if diagnostic else None
                row["rustfmt_smoke_accepted"] = checked.returncode == 0 and checked.stderr == "" \
                    and checked.stdout == expected and checked.audit_limits["owned_tree_empty"]
                row["rustfmt_smoke_profile"] = checked.audit_limits
                row["rustfmt_smoke_output_bytes"] = len(checked.stdout.encode("utf-8"))
                row["rustfmt_smoke_output_sha256"] = hashlib.sha256(checked.stdout.encode("utf-8")).hexdigest()
                accepted = accepted and row["rustfmt_smoke_accepted"]
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                code = str(error) if isinstance(error, ValueError) else "audit_tool_os_failure"
                row["rustfmt_smoke_error_code"] = code if re.fullmatch(r"audit_tool_[a-z_]+|STOP_[A-Z_]+", code) \
                    else "audit_tool_failure"
                row["rustfmt_smoke_profile"] = getattr(error, "audit_limits", None)
                accepted = False
        row["source_freeze_exact_after"] = row["source_freeze"] == freeze()
        accepted = accepted and row["source_freeze_exact_after"]
        row["state"] = ("PASS_LIGHT_BOUNDED_PIPES_AND_RUSTFMT_SMOKE_NOT_PRODUCT_OR_PC_FREEZE_PROOF"
            if args.live_rustfmt_smoke else "PASS_LIGHT_BOUNDED_AUDIT_TOOL_MOCKS_NOT_ACTUAL_TOOL_OR_PC_FREEZE_PROOF") \
            if accepted else "FAILED_NOT_ACCEPTED"
        row["verification_elapsed_seconds"] = round(time.monotonic()-started, 4)
    row["self_resource_after"] = self_resource(windows)
    row["elapsed_seconds"] = round(time.monotonic()-main_started, 4)
    row["elapsed_scope"] = "main_entry_through_final_resource_sample_includes_imports_and_source_freezes_excludes_python_startup_and_receipt_write"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests",
        "actual_rustfmt_smoke_attempted", "rustfmt_smoke_accepted")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
