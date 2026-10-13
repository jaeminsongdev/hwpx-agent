"""Exact SQL22 metadata management component evidence; not actual DB/issuer/native/Gate qualification."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PRE = module("p137_preserved", "tools/p09/verify_formula_issuer_registry_reads.py")
T = module("p138_contracts", "tools/p09/tests/test_formula_issuer_registry_management.py")
require = PRE.require
RUN = PRE.RUN
CURRENT = "implementation/p09/evidence/p09-138-formula-issuer-registry-management.source-progress.v1.json"
REPORT = "implementation/p09/P09-138_FORMULA_ISSUER_REGISTRY_MANAGEMENT_REPORT.md"
FAILURE = "implementation/p09/evidence/p09-138-initial-source-contract-failure.v1.json"
FAILED_GUARD = "implementation/p09/source-archive/p09-138-initial-bind-shape/tools/p09/tests/test_formula_issuer_registry_management.py"
DELTA = [T.PARENT, T.SOURCE, T.DRIVER, T.LINT, "tools/p09/tests/test_formula_issuer_registry_management.py",
         "tools/p09/verify_formula_issuer_registry_management.py", REPORT, FAILURE]
ARCHIVES = [T.ARCHIVE, FAILED_GUARD]


def pin(path):
    raw = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def predecessor():
    require(pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 16586,
        "sha256": "e285932e66af805ba7058ae78debd59979c759868d1ddeec47ea06ae1f332157"}, "P137_checkpoint_drift")
    before = T.preimage()
    old_bytes, old_text, old_run = Path.read_bytes, Path.read_text, subprocess.run
    excluded = set([p for p in DELTA if p != T.PARENT] + ARCHIVES + [CURRENT])

    def key(path):
        try:
            return path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return ""

    def historical_bytes(path):
        return before if key(path) == T.PARENT else old_bytes(path)

    def historical_text(path, *args, **kw):
        if key(path) != T.PARENT:
            return old_text(path, *args, **kw)
        encoding = kw.get("encoding", args[0] if args else "utf-8") or "utf-8"
        return before.decode(encoding).replace("\r\n", "\n")

    def historical_run(args, *pos, **kw):
        result = old_run(args, *pos, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("rg", "rg.exe") and "--files" in args and result.returncode == 0 and isinstance(result.stdout, str):
            lines = [line for line in result.stdout.splitlines()
                if key(Path(line) if Path(line).is_absolute() else ROOT / line) not in excluded]
            return subprocess.CompletedProcess(result.args, result.returncode,
                "\n".join(lines) + ("\n" if result.stdout.endswith("\n") else ""), result.stderr)
        return result

    try:
        Path.read_bytes, Path.read_text, subprocess.run = historical_bytes, historical_text, historical_run
        result = PRE.current()
    finally:
        Path.read_bytes, Path.read_text, subprocess.run = old_bytes, old_text, old_run
    require(result["current_scoped_runtime_executions"] == 63 and result["historical_stored_cases"] == 234
        and result["SQL22_write_adapters_implemented"] is False and result["actual_sql_executed"] is False
        and result["P09_gate"] == "OPEN", "P137_history_scope_promoted")
    return result


def contracts(test_module):
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(test_module.Contracts).run(result)
    return result


def failed_guard():
    saved = module("p138_initial_bind_shape", FAILED_GUARD)
    saved.ROOT = ROOT
    result = contracts(saved)
    doc = read(FAILURE)
    require(result.testsRun == 8 and len(result.failures) == 1 and not result.errors and not result.skipped
        and result.failures[0][0]._testMethodName == doc["failed_contract"]
        and doc["state"] == "FAIL_CLOSED" and doc["passed"] == 7 and doc["failed"] == 1
        and doc["failed_source_archive"] == FAILED_GUARD and doc["Rust_or_SQL_changed_to_fix_guard"] is False
        and doc["actual_sql_executed"] is False and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False,
        "management_failed_guard_not_preserved")
    before = (ROOT / FAILED_GUARD).read_text(encoding="utf-8")
    after = (ROOT / "tools/p09/tests/test_formula_issuer_registry_management.py").read_text(encoding="utf-8")
    fixed = before.replace(' + root + "])"', ' + root + "],)"').replace(' + approval + "])"', ' + approval + "],)"')
    fixed = fixed.replace(', "WITH_CHECK_UNUSED_SENTINEL"', '')
    fixed = fixed.replace('            if guard != "WITH_CHECK_UNUSED_SENTINEL":\n                self.assertIn(guard, body)', '            self.assertIn(guard, body)')
    require(fixed == after, "management_guard_transition_drift")


def inputs(doc):
    require(doc["source_freeze_exact_after"] is True and doc["protected_executables_exact_after"] is True
        and len(doc["source_freeze"]) == len({p["path"] for p in doc["source_freeze"]}) == 813
        and all(pin(p["path"]) == p for p in doc["source_freeze"]), "management_compiled_input_drift")
    protected = read(RUN + "p135-case-001-attempt-001.json")["protected_executables"]
    previous = read(PRE.CURRENT)
    protected += previous["current_executables"] + previous["earlier_executables_preserved"]
    require(doc["protected_executables"] == protected and len(protected) == 27
        and len({p["path"] for p in protected}) == 27 and all(pin(p["path"]) == p for p in protected),
        "management_old_executable_drift")
    PRE.resource(doc)


def runtime():
    paths = [RUN + f"p138-revision-{mode}-r1.json" for mode in ("build", "list", "test")]
    docs = [read(p) for p in paths]
    for mode, doc in zip(("Build", "List", "Test"), docs):
        require(doc["mode"] == mode and doc["suite"] == "Revision" and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE"
            and doc["exit_code"] == 0 and doc["stop_reason"] is None
            and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False, "management_runtime_not_accepted")
        inputs(doc)
    require(docs[0]["build_marker"] is True and not docs[0]["build_diagnostics"]
        and not docs[0]["cargo_failure"], "management_build_not_clean")
    names = docs[1]["inventory"]
    require(len(names) == len(set(names)) == 32 and len([n for n in names if
        n.startswith("postgres::source_formula_policy::issuer_registry::management::tests::")]) == 8,
        "management_test_inventory_drift")
    exe = docs[1]["executable_pin"]
    require(exe["path"] == RUN + "debug/deps/revision_service-p138-r1.exe" and pin(exe["path"]) == exe
        and docs[2]["executable_pin"] == exe, "management_executable_drift")
    summary = docs[2]["tests"]["terminal_summary"]
    passed = docs[2]["tests"]["passed_test_names"]
    require(summary["outcome"] == "ok" and summary["passed"] == 32
        and summary["failed"] == summary["ignored"] == summary["measured"] == summary["filtered"] == 0
        and len(passed) == 32 and set(passed) == set(names), "management_exact_runtime_summary_missing")
    return [pin(p) for p in paths], exe


def lint():
    path = RUN + "p138-workspace-lint-r1.json"
    doc = read(path)
    require(doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["mode"] == "workspace_strict_lint"
        and doc["exit_code"] == 0 and doc["stop_reason"] is None
        and doc["build_finished_success"] is True and not doc["diagnostics"]
        and doc["test_or_app_executed"] is False and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False,
        "management_strict_lint_not_accepted")
    inputs(doc)
    require(doc["cargo_arguments"] == ["clippy", "--workspace", "--all-targets", "--locked", "--offline", "--jobs", "1",
        "--target-dir", str(ROOT / "target/p09-121-resource-optimized"), "--message-format", "json", "--", "-D", "warnings"],
        "management_lint_arguments_drift")
    identity = lambda row: (row["package_id"], row["name"], tuple(row["kind"]))
    expected = {identity(row) for row in doc["workspace_inventory"]}
    require(len(expected) == len(doc["workspace_inventory"]) == 358
        and len({row["package_id"] for row in doc["workspace_inventory"]}) == 32
        and {identity(row) for row in doc["workspace_artifacts"]} == expected,
        "management_strict_lint_target_coverage_missing")
    return pin(path)


def audit():
    old = predecessor()
    failed_guard()
    source = contracts(T)
    require(source.testsRun == 8 and source.wasSuccessful() and not source.skipped, "management_source_contracts_not_accepted")
    receipts, exe = runtime()
    return {"state": "PASS_SQL22_MANAGEMENT_COMPONENT_NOT_ACTUAL_DB_ISSUER_PROVISIONING_NATIVE_OR_GATE",
        "source_contract_tests": 8, "failed_guard_replays_preserved": 1,
        "current_revision_library_cases": 32, "new_management_unit_cases": 8,
        "historical_P137_component_executions": old["current_scoped_runtime_executions"],
        "historical_stored_cases": old["historical_stored_cases"],
        "strict_lint_packages": 32, "strict_lint_targets": 358,
        "SQL22_management_adapters_implemented": True, "issuer_product_provisioning_implemented": False,
        "actual_sql_executed": False, "schema22_migration_applied": False,
        "native_application_executed": False, "trust_configuration_changed": False,
        "production_key_custody_qualified": False, "atomic_publication_qualified": False,
        "management_receipt_is_row_readback_or_signature_authority": False,
        "P09_gate": "OPEN", "A12_gate": "OPEN", "A13_gate": "OPEN", "product_complete": False,
        "goal_status": "active", "P10_new_implementation": False,
        "accepted_runtime_receipts": receipts, "accepted_lint_receipt": lint(), "current_executable": exe}


def groups():
    return {"source_delta": [pin(p) for p in DELTA], "source_archives_added": [pin(p) for p in ARCHIVES],
        "predecessor_receipts_added": [pin(PRE.CURRENT)], "migration_inputs": [pin(p.relative_to(ROOT).as_posix())
            for p in sorted((ROOT / "migrations/postgres").glob("*.up.sql"))]}


def current():
    result = audit()
    doc = read(CURRENT)
    require(all(doc[k] == v for k, v in result.items()) and all(doc[k] == v for k, v in groups().items()),
        "management_checkpoint_scope_or_pin_drift")
    require(doc["schema_version"] == "hwpx-agent.p09-formula-issuer-registry-management-source-progress/v1"
        and doc["previous_source_files_count"] == 1202 and doc["current_source_files_count"] == 1202 + len(DELTA)
        and doc["source_inventory_counting"] == "historical_graph_plus_declared_delta_not_unique_path_union"
        and doc["inherited_raw_pin_entries"] == 3399 and doc["new_raw_pin_entries"] == sum(len(v) for v in groups().values()) + 5
        and doc["remaining_coarse_groups_minimum"] == 6 and doc["remaining_groups_closed_by_slice"] == 0
        and doc["minimum_30_conditions_not_exhaustive"] is True
        and doc["native34_state"] == "NOT_RUN_INPUT_CHANGED_RE_ADMISSION_REQUIRED", "management_scope_promoted")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="store_true")
    args = parser.parse_args()
    try:
        result = audit() if args.source else current()
        print(json.dumps({k: v for k, v in result.items() if k not in
            ("accepted_runtime_receipts", "accepted_lint_receipt", "current_executable")}, indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
