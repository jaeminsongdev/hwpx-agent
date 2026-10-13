"""Build consumer contract and whole-driver counterexamples; no child or SQL."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

import conservative_maintenance as c
import issuer_sql_build_contract as subject
from tests.sql_build_driver_delta import DRIVERS, restore_build_contract_driver_changes


class IssuerSQLBuildContractTests(unittest.TestCase):
    def actual(self):
        raw = (c.ROOT/subject.CURRENT_BUILD_PIN["path"]).read_bytes()
        self.assertEqual(len(raw), subject.CURRENT_BUILD_PIN["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), subject.CURRENT_BUILD_PIN["sha256"])
        return json.loads(raw)

    def fixture(self, build=None, name=None):
        row = self.actual() if build is None else build
        name = subject.CURRENT_BUILD_PIN["path"] if name is None else name
        pins = {p["path"]: p for field in ("source_freeze", "protected_executables", "build_helper_freeze")
            for p in row.get(field, [])}
        pins[row["executable_pin"]["path"]] = row["executable_pin"]
        pins[name] = dict(subject.CURRENT_BUILD_PIN, path=name)
        class Reader:
            def __init__(self):
                self.calls = []
            def pin(self, path):
                self.calls.append(path)
                return pins[path]
            def json(self, path):
                return row
        return row, pins, Reader()

    def legacy(self):
        row = self.actual()
        row["state"] = "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE"
        row["executable_pin"] = dict(row["executable_pin"], path=
            "target/p09-121-resource-optimized/debug/examples/formula_issuer_product_postgres_probe-p143-r999.exe")
        row.pop("build_helper_freeze")
        return row

    def test_actual_r4_full_current_contract_is_accepted_without_state_conversion(self):
        row = self.actual()
        sources, protected, helpers, executable = subject.build_contract(row, "current_r4")
        self.assertEqual((len(sources), len(protected), len(helpers)), (842, 50, 29))
        self.assertEqual(executable, row["executable_pin"])
        self.assertEqual(row["state"], subject.current.PASS)

    def test_all_original_build_flags_profile_and_inventory_guards_remain_required(self):
        row = self.actual()
        for name, value in (("exit_code", 1), ("source_freeze_exact_after", False),
                ("protected_executables_exact_after", False), ("logical_cpu_limit", 2), ("cargo_jobs", 2),
                ("priority", "Normal"), ("diagnostics", ["fixture"]),
                ("whole_workspace_Rust_input_coverage_enforced", False), ("historical_parent_archive_verified", False)):
            changed = copy.deepcopy(row)
            changed[name] = value
            with self.assertRaises(ValueError):
                subject.build_contract(changed, "current_r4")
        row["catalog_profile"]["test"] = True
        with self.assertRaises(ValueError):
            subject.build_contract(row, "current_r4")

    def test_current_failure_or_missing_checked_cleanup_cannot_be_consumed(self):
        row = self.actual()
        for name, value in (("state", "NOT_ACCEPTED_STOP_OR_FAILURE"), ("variant", "r3"),
                ("compiler_build_binding_accepted", False), ("build_helper_freeze_exact_after", False),
                ("mutex_cleanup_confirmed", False), ("stop_reason", "STOP_COMPILER_DURATION_LIMIT")):
            changed = copy.deepcopy(row)
            changed[name] = value
            with self.assertRaises(ValueError):
                subject.build_contract(changed, "current_r4")
        for name in ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed"):
            changed = copy.deepcopy(row)
            changed["owned_job_profile"][name] = False
            with self.assertRaises(ValueError):
                subject.build_contract(changed, "current_r4")

    def test_helper_inventory_cannot_shrink_duplicate_or_replace_required_path(self):
        for mode in ("missing", "duplicate", "replaced"):
            row = self.actual()
            if mode == "missing":
                row["build_helper_freeze"].pop()
            elif mode == "duplicate":
                row["build_helper_freeze"][-1] = row["build_helper_freeze"][0]
            else:
                row["build_helper_freeze"][-1] = dict(row["build_helper_freeze"][-1], path="Cargo.lock.extra")
            with self.assertRaises(ValueError):
                subject.build_contract(row, "current_r4")

    def test_executable_target_variant_and_product_phase_cannot_be_reclassified(self):
        row = self.actual()
        for name, value in (("product_complete", True), ("P09_gate", "PASS"),
                ("actual_SQL_or_native_product_executed", True), ("baseline_candidate_pin", {})):
            changed = copy.deepcopy(row)
            changed[name] = value
            with self.assertRaises(ValueError):
                subject.build_contract(changed, "current_r4")
        row["executable_pin"]["path"] = self.legacy()["executable_pin"]["path"]
        with self.assertRaises(ValueError):
            subject.build_contract(row, "current_r4")

    def test_legacy_still_requires_original_state_and_executable_generation(self):
        row = self.legacy()
        result = subject.build_contract(row, "legacy")
        self.assertEqual(result[2], {})
        row["state"] = subject.current.PASS
        with self.assertRaises(ValueError):
            subject.build_contract(row, "legacy")

    def test_current_binding_fresh_reads_every_source_protected_helper_and_executable(self):
        row, pins, reader = self.fixture()
        original = copy.deepcopy(row)
        build, executable, binding = subject.bind_probe_build(reader, c.ROOT/subject.CURRENT_BUILD_PIN["path"])
        self.assertEqual(row, original)
        self.assertIs(build, row)
        self.assertEqual(executable, row["executable_pin"])
        self.assertTrue(set(pins).issubset(reader.calls))
        self.assertEqual(binding["scheme"], "current_r4")
        self.assertFalse(binding["actual_SQL_qualified"])

    def test_current_receipt_drift_is_rejected_before_body_is_consumed(self):
        _, pins, reader = self.fixture()
        pins[subject.CURRENT_BUILD_PIN["path"]] = dict(subject.CURRENT_BUILD_PIN, sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "SQL_BUILD_CURRENT_RECEIPT_DRIFT"):
            subject.bind_probe_build(reader, c.ROOT/subject.CURRENT_BUILD_PIN["path"])
        self.assertEqual(reader.calls, [subject.CURRENT_BUILD_PIN["path"]])

    def test_any_current_source_protected_helper_or_executable_drift_fails_closed(self):
        for field in ("source_freeze", "protected_executables", "build_helper_freeze", "executable_pin"):
            row, pins, reader = self.fixture()
            expected = row[field][0] if isinstance(row[field], list) else row[field]
            pins[expected["path"]] = dict(expected, sha256="0"*64)
            with self.assertRaisesRegex(ValueError, "SQL_BUILD_INPUT_DRIFT"):
                subject.bind_probe_build(reader, c.ROOT/subject.CURRENT_BUILD_PIN["path"])

    def test_legacy_binding_keeps_legacy_state_and_original_full_pin_checks(self):
        name = "target/p09-121-resource-optimized/p143-issuer-product-build-r999.json"
        row, pins, reader = self.fixture(self.legacy(), name)
        build, _, binding = subject.bind_probe_build(reader, c.ROOT/name)
        self.assertIs(build, row)
        self.assertEqual(build["state"], "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE")
        self.assertEqual(binding["scheme"], "legacy")
        self.assertTrue(set(pins).issubset(reader.calls))

    def test_unreviewed_current_variant_and_outside_or_parent_paths_are_rejected(self):
        _, _, reader = self.fixture()
        for path in (c.ROOT/"target/p09-149-current-issuer-build/current-issuer-build-r5.json",
                c.ROOT.parent/"outside.json", c.ROOT/"target/../CURRENT_STATE.md"):
            with self.assertRaises(ValueError):
                subject.bind_probe_build(reader, path)

    def test_consumer_source_freeze_includes_all_build_helpers_and_new_contract_sources(self):
        _, _, reader = self.fixture()
        _, _, binding = subject.bind_probe_build(reader, c.ROOT/subject.CURRENT_BUILD_PIN["path"])
        names = subject.consumer_sources(binding)
        self.assertEqual(set(names), set(subject.SOURCES+[p["path"] for p in binding["build_helper_pins"]]))
        binding["actual_SQL_qualified"] = True
        with self.assertRaises(ValueError):
            subject.consumer_sources(binding)

    def source_union(self, name, *, duplicate_compiled=False, old_union=False):
        """실제 driver의 순수 목록 결합만 실행하며 SQL/worker는 시작하지 않는다."""
        tree = ast.parse((c.ROOT/name).read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        def assignment(key):
            return next(node for node in main.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == key for target in node.targets))
        extension = next(node for node in main.body if isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name) and node.target.id == "sources")
        index = main.body.index(extension)
        guard = main.body[index+1]
        self.assertIn("crypto_source_coverage_drift", ast.unparse(guard))
        build = self.actual()
        if duplicate_compiled:
            build["source_freeze"].append(copy.deepcopy(build["source_freeze"][0]))
        ns = {"build": build, "build_file": c.ROOT/subject.CURRENT_BUILD_PIN["path"], "ROOT": c.ROOT,
            "build_binding": {"scheme": "current_r4", "actual_SQL_qualified": False,
                "build_helper_pins": build["build_helper_freeze"]},
            "consumer_sources": subject.consumer_sources, "require": c.require,
            "original_source_pin": {"path": "fixtures/source-union-only-original.hwpx"}}
        if old_union:
            extension = ast.parse("sources += [path for path in additions if path not in sources]").body[0]
        block = ast.Module(body=[assignment("unit_receipt_paths"), assignment("additions"),
            assignment("sources"), extension, guard], type_ignores=[])
        exec(compile(ast.fix_missing_locations(block), "<driver-source-union-only>", "exec"), ns)
        return ns, guard

    def test_actual_driver_union_keeps_every_compiled_and_declared_input_exactly_once(self):
        for name in DRIVERS:
            ns, _ = self.source_union(name)
            compiled = [pin["path"] for pin in ns["build"]["source_freeze"]]
            self.assertEqual(ns["sources"], list(dict.fromkeys(compiled+ns["additions"])))
            self.assertEqual(len(ns["sources"]), len(set(ns["sources"])))
            self.assertGreater(len(ns["additions"]), len(set(ns["additions"])))

    def test_pre_repair_driver_union_reproduces_observed_coverage_failure(self):
        for name in DRIVERS:
            with self.assertRaisesRegex(ValueError, "crypto_source_coverage_drift"):
                self.source_union(name, old_union=True)

    def test_duplicate_compiled_inventory_still_fails_original_coverage_guard(self):
        for name in DRIVERS:
            with self.assertRaisesRegex(ValueError, "crypto_source_coverage_drift"):
                self.source_union(name, duplicate_compiled=True)

    def test_missing_declared_input_still_fails_original_coverage_guard(self):
        for name in DRIVERS:
            ns, guard = self.source_union(name)
            ns["sources"].remove(ns["original_source_pin"]["path"])
            block = ast.Module(body=[guard], type_ignores=[])
            with self.assertRaisesRegex(ValueError, "crypto_source_coverage_drift"):
                exec(compile(ast.fix_missing_locations(block), "<driver-coverage-guard-only>", "exec"), ns)

    def test_all_five_source_union_preimages_are_exact_and_contain_failed_old_union(self):
        archive = json.loads((c.ROOT/"implementation/p09/source-archive/p09-149-pre-sql-source-union-repair/source-preimages.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 5)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            if row["path"] in DRIVERS:
                self.assertIn(b"sources += [path for path in additions if path not in sources]", raw)

    def test_whole_driver_AST_matches_only_explicit_binding_import_freeze_and_receipt_delta(self):
        for name in DRIVERS:
            tree = ast.parse((c.ROOT/name).read_text(encoding="utf-8"))
            restore_build_contract_driver_changes(tree, name)

    def test_security_SQL_or_resource_mutation_is_not_hidden_by_driver_projection(self):
        for name in DRIVERS:
            text = (c.ROOT/name).read_text(encoding="utf-8")
            for before, after in (('"P09_gate": "OPEN"', '"P09_gate": "PASS"'),
                    ("adapter_total_time_limit", "weakened_total_limit"), ("ALTER ROLE", "ALTER BROKEN")):
                self.assertIn(before, text)
                with self.assertRaisesRegex(ValueError, "SQL_BUILD_NONBINDING_AST_CHANGED"):
                    restore_build_contract_driver_changes(ast.parse(text.replace(before, after, 1)), name)

    def test_all_four_preimage_files_are_preserved_with_exact_original_bytes(self):
        archive = json.loads((c.ROOT/subject.ARCHIVE).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 4)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_source_or_protected_pin_inventory_cannot_shrink_or_duplicate(self):
        for field in ("source_freeze", "protected_executables"):
            for mode in ("missing", "duplicate"):
                row = self.actual()
                if mode == "missing":
                    row[field].pop()
                else:
                    row[field][-1] = row[field][0]
                with self.assertRaises(ValueError):
                    subject.build_contract(row, "current_r4")
