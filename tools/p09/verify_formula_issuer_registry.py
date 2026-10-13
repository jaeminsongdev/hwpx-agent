"""SQL22 source contract and immutable SQL21/P135 history; NOT live SQL, adapter, issuer or Gate."""
import argparse
import importlib.util
import json
import subprocess
import types
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p135_preserved", Path(__file__).with_name("verify_final_stored_regression.py"))
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)
ROOT, R, require = PRE.ROOT, PRE.R, PRE.require
UP = "migrations/postgres/0022_p09_formula_issuer_registry.up.sql"
DOWN = "migrations/postgres/0022_p09_formula_issuer_registry.down.sql"
TEST = "tools/p09/tests/test_formula_issuer_registry_source.py"
FAILURES = ["implementation/p09/evidence/p09-136-initial-source-test-failure.v1.json",
            "implementation/p09/evidence/p09-136-intermediate-source-test-failure.v1.json"]
ARCHIVES = ["implementation/p09/source-archive/" + stage + "/" + TEST
            for stage in ("p09-136-initial-json-word-check", "p09-136-intermediate-fk-count-check")]
ROLLBACK_PREIMAGE = "implementation/p09/source-archive/p09-136-pre-global-rollback-visibility/" + DOWN
FINDING = "implementation/p09/evidence/p09-136-rollback-global-visibility.source-finding.v1.json"
DELTA = [UP, DOWN, TEST, "tools/p09/verify_formula_issuer_registry.py",
         "protocol/migrations/p09-formula-issuer-registry-sql21-to-sql22.md",
         "implementation/p09/P09-136_FORMULA_ISSUER_REGISTRY_REPORT.md", *FAILURES, FINDING]
CURRENT = "implementation/p09/evidence/p09-136-formula-issuer-registry.source-progress.v1.json"


class HistoricalMigrationDirectory(type(ROOT)):
    def glob(self, pattern, **kwargs):
        # Only the newly added SQL22 up file is outside the old, exact SQL21 profile.
        for path in super().glob(pattern, **kwargs):
            if path.relative_to(ROOT).as_posix() != UP:
                yield path


class HistoricalRoot(type(ROOT)):
    def __truediv__(self, path):
        result = ROOT / path
        return HistoricalMigrationDirectory(result) if str(path).replace("\\", "/") == "migrations/postgres" else result


def predecessor():
    require(R.pin(PRE.CURRENT) == {"path": PRE.CURRENT, "bytes": 51117,
            "sha256": "30c9a61c6bbe9271e75ce2b733ae762e036ed9e82e90be1fbae57f0f88bdf55a"}, "P135_checkpoint_drift")
    pending, seen, roots = [PRE], set(), []
    directory = Path(__file__).resolve().parent
    while pending:
        module = pending.pop()
        if id(module) in seen:
            continue
        seen.add(id(module))
        if isinstance(getattr(module, "ROOT", None), Path) and module.ROOT == ROOT:
            roots.append((module, module.ROOT))
        for value in vars(module).values():
            if isinstance(value, types.ModuleType) and getattr(value, "__file__", None) and Path(value.__file__).resolve().parent == directory:
                pending.append(value)
    original_factory, original_run, loaders = importlib.util.module_from_spec, subprocess.run, []

    def historical_factory(spec):
        module = original_factory(spec)
        if spec.origin and Path(spec.origin).resolve().parent == directory:
            loader, execute = spec.loader, spec.loader.exec_module
            def load(loaded):
                execute(loaded)
                if isinstance(getattr(loaded, "ROOT", None), Path) and loaded.ROOT == ROOT:
                    loaded.ROOT = HistoricalRoot(ROOT)
            loaders.append((loader, execute))
            loader.exec_module = load
        return module

    def historical_run(args, *a, **kw):
        result = original_run(args, *a, **kw)
        if isinstance(args, (list, tuple)) and Path(str(args[0])).name in ("rg", "rg.exe") and "--files" in args and result.returncode == 0 and isinstance(result.stdout, str):
            kept = []
            for line in result.stdout.splitlines():
                path = Path(line)
                try:
                    normalized = (path if path.is_absolute() else ROOT / path).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    normalized = line.replace("\\", "/")
                if normalized not in set(DELTA + ARCHIVES + [CURRENT]):
                    kept.append(line)
            return subprocess.CompletedProcess(result.args, result.returncode, "\n".join(kept) + ("\n" if result.stdout.endswith("\n") else ""), result.stderr)
        return result

    try:
        for module, _ in roots:
            module.ROOT = HistoricalRoot(ROOT)
        importlib.util.module_from_spec, subprocess.run = historical_factory, historical_run
        old = PRE.current()
    finally:
        importlib.util.module_from_spec, subprocess.run = original_factory, original_run
        for loader, execute in loaders:
            loader.exec_module = execute
        for module, root in roots:
            module.ROOT = root
    require(old["accepted"] == 234 and old["remaining"] == 0 and old["current_signed_marker_cases_accepted"] == 6
            and old["P09_gate"] == "OPEN" and old["product_complete"] is False, "P135_historical_coverage_lost")
    return old


def load_tests(path=TEST):
    spec = importlib.util.spec_from_file_location("sql22_source", ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Archived test paths have a different parents depth; bind to the original repository explicitly.
    module.ROOT = ROOT
    return module


def source_tests(path=TEST, down_path=DOWN):
    module = load_tests(path)
    module.DOWN = down_path
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
    return result


def failed_tests():
    # Replay the failed guards against unchanged SQL bytes; neither failure is upgraded to PASS.
    for path, archive in zip(FAILURES, ARCHIVES):
        doc, result = R.read(path), source_tests(archive)
        require(result.testsRun == 12 and len(result.failures) == 1 and not result.errors and not result.skipped
                and result.failures[0][0]._testMethodName == doc["failed_test_name"]
                and doc["passed"] == 11 and doc["failed"] == 1 and doc["failed_source_archive"] == archive
                and doc["SQL_source_changed_to_fix_this_guard"] is False and doc["actual_SQL_executed"] is False
                and doc["P09_gate"] == "OPEN" and doc["product_complete"] is False, "SQL22_failed_guard_not_preserved")
    initial, middle, final = [(ROOT / p).read_text(encoding="utf-8") for p in [*ARCHIVES, TEST]]
    old = '        self.assertNotRegex(self.up, r"\\bjsonb?\\b|\\bbytea\\b|\\bprivate_key\\b|\\bpassword\\b")\n'
    new = '        definitions = "\\n".join(re.findall(r"CREATE TABLE hwpx_agent\\.\\w+ \\((.*?)\\n\\);", self.up, re.S))\n' \
          '        self.assertNotRegex(definitions, r"\\b\\w+\\s+(?:jsonb?|bytea)\\b|\\bprivate_key\\b|\\bpassword\\b")\n'
    require(initial.count(old) == 1 and initial.replace(old, new) == middle, "SQL22_initial_guard_transition_drift")
    old = '        self.assertEqual(self.up.count("FOREIGN KEY"), 9)\n        self.assertEqual(self.up.count("ON DELETE RESTRICT"), 9)\n'
    new = '        # root2 + root-revocation1 + approval4 + approval-revocation1.\n' \
          '        self.assertEqual(self.up.count("FOREIGN KEY"), 8)\n' \
          '        self.assertEqual(self.up.count("ON DELETE RESTRICT"), 8)\n' \
          '        self.assertEqual(set(re.findall(r"REFERENCES hwpx_agent\\.(\\w+)", definitions)),\n' \
          '                         {"projects", "artifacts", "branches", "source_formula_policy_versions",\n' \
          '                          "formula_issuer_trust_versions", "formula_approval_versions"})\n'
    intermediate = middle.replace(old, new)
    anchor = '        self.assertNotIn("DROP TABLE hwpx_agent.source_formula_policy", self.down)\n'
    extension = '        self.assertIn("rolname=current_user AND (rolsuper OR rolbypassrls)", self.down)\n' \
                '        self.assertLess(self.down.index("FORMULA_ISSUER_ROLLBACK_GLOBAL_VISIBILITY_REQUIRED"),\n' \
                '                        self.down.index("EXISTS(SELECT 1 FROM hwpx_agent.formula_approval_revocations)"))\n' \
                '        self.assertNotRegex(sql, r"ALTER TABLE hwpx_agent\\.formula_\\w+ (?:DISABLE|NO FORCE) ROW LEVEL SECURITY")\n' \
                '        self.assertIn("IN ACCESS EXCLUSIVE MODE;", self.down)\n' \
                '        lock = self.down.split("LOCK TABLE", 1)[1].split("IN ACCESS EXCLUSIVE MODE;", 1)[0]\n' \
                '        self.assertEqual(set(re.findall(r"hwpx_agent\\.(\\w+)", lock)), set(TABLES))\n' \
                '        self.assertLess(self.down.index("IN ACCESS EXCLUSIVE MODE;"),\n' \
                '                        self.down.index("EXISTS(SELECT 1 FROM hwpx_agent.formula_approval_revocations)"))\n'
    require(middle.count(old) == 1 and intermediate.count(anchor) == 1
            and intermediate.replace(anchor, anchor + extension) == final, "SQL22_FK_and_rollback_guard_transition_drift")


def rollback_counterexample():
    finding = R.read(FINDING)
    result = source_tests(down_path=ROLLBACK_PREIMAGE)
    require(result.testsRun == 12 and len(result.failures) == 1 and not result.errors and not result.skipped
            and result.failures[0][0]._testMethodName == finding["pre_fix_contract_counterexample_expected"]
            and finding["pre_fix_source"] == ROLLBACK_PREIMAGE and finding["actual_rollback_executed"] is False
            and finding["actual_SQL_executed"] is False and finding["application_role_privilege_grants_added"] is False
            and finding["RLS_disabled_on_history_tables"] is False and finding["P09_gate"] == "OPEN"
            and finding["product_complete"] is False, "SQL22_rollback_counterexample_not_preserved")


def groups():
    return {"source_delta": DELTA, "source_archives_added": [*ARCHIVES, ROLLBACK_PREIMAGE],
            "predecessor_receipts_added": [PRE.CURRENT],
            "migration_inputs": sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "migrations/postgres").glob("*.up.sql"))}


def audit():
    old = predecessor()
    failed_tests()
    rollback_counterexample()
    result = source_tests()
    require(result.testsRun == 12 and result.wasSuccessful() and not result.skipped and not result.unexpectedSuccesses,
            "SQL22_source_contracts_not_accepted")
    require(len(groups()["migration_inputs"]) == 22, "SQL22_migration_inventory_drift")
    return {"state": "PASS_SQL22_SOURCE_CONTRACTS_HISTORICAL_P135_NOT_RUNTIME_OR_GATE", "source_contract_tests": 12,
            "failed_guard_replays_preserved": 2, "rollback_source_counterexamples": 1,
            "historical_stored_cases": old["accepted"], "current_stored_runtime_executions": 0,
            "actual_sql_executed": False, "SQL_parser_executed": False, "SQL22_product_adapters_implemented": False,
            "P09_gate": "OPEN", "product_complete": False}


def current():
    result = audit()
    doc = R.read(CURRENT)
    for key, paths in groups().items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(R.pin(r["path"]) == r for r in rows), "SQL22_checkpoint_pin_drift")
    require(all(doc[key] == value for key, value in result.items()) and doc["goal_status"] == "active"
            and doc["P10_new_implementation"] is False and doc["A12_gate"] == doc["A13_gate"] == "OPEN"
            and doc["native_application_executed"] is False and doc["trust_configuration_changed"] is False
            and doc["schema22_migration_applied"] is False and doc["old_SQL21_Rust_connectors_unchanged"] is True
            and doc["previous_source_files_count"] == 1179 and doc["current_source_files_count"] == 1188
            and doc["inherited_raw_pin_entries"] == 3291 and doc["new_raw_pin_entries"] == sum(len(v) for v in groups().values())
            and doc["remaining_coarse_groups_minimum"] == 6 and doc["remaining_groups_closed_by_slice"] == 0
            and doc["minimum_30_conditions_not_exhaustive"] is True, "SQL22_scope_promoted")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(audit() if args.source else current(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED", "error_code": code, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
