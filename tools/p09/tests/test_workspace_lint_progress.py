"""P130 closed evidence/byte-inverse guards; units do not execute native apps or SQL."""
import copy
import importlib.util
import os
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p130_guard", Path(__file__).resolve().parents[1] / "verify_workspace_lint_progress.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class WorkspaceLintGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial, cls.current = [V.OLD.R.read(p) for p in V.RUNS]

    def reject(self, mutation):
        doc = copy.deepcopy(self.current)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            V.validate_lint(doc, True)

    def test_current_whole_workspace_accepts(self):
        self.assertEqual(V.validate_lint(self.current, True)["observed_targets"], 358)

    def test_real_initial_failure_remains_failed(self):
        self.assertFalse(V.validate_lint(self.initial, False)["successful"])

    def test_two_actual_whole_inverses(self):
        for parent in V.PARENTS:
            V.validate_inverse((V.ROOT / V.ARCHIVES[parent]).read_bytes(), (V.ROOT / parent).read_bytes())

    def test_unrelated_edit_rejects(self):
        p = V.PARENTS[0]
        with self.assertRaises(ValueError):
            V.validate_inverse((V.ROOT / V.ARCHIVES[p]).read_bytes(), (V.ROOT / p).read_bytes() + b"\n")

    def test_missing_visibility_edit_rejects(self):
        p = V.PARENTS[0]
        original = (V.ROOT / V.ARCHIVES[p]).read_bytes()
        with self.assertRaises(ValueError):
            V.validate_inverse(original, original)

    def test_cwd_and_nondeclared_reads_stay_real(self):
        view = V.WholePreimageRoot(V.ROOT)
        self.assertEqual(os.fspath(view), str(V.ROOT))
        self.assertEqual(view / "Cargo.toml", V.ROOT / "Cargo.toml")
        self.assertEqual(view / V.PARENTS[0], V.ROOT / V.ARCHIVES[V.PARENTS[0]])

    def test_dynamic_import_context_restores_factory(self):
        factory = importlib.util.module_from_spec
        self.assertEqual(V.predecessor()["historical_scoped_cases"], 228)
        self.assertIs(importlib.util.module_from_spec, factory)
        self.assertNotIsInstance(V.OLD.ROOT, V.WholePreimageRoot)

    def test_relaxed_arguments_reject(self):
        self.reject(lambda d: d["cargo_arguments"].remove("--all-targets"))

    def test_missing_target_rejects(self):
        first = self.current["workspace_artifacts"][0]
        self.reject(lambda d: d.__setitem__("workspace_artifacts", [r for r in d["workspace_artifacts"]
                    if (r["package_id"], r["name"], r["kind"]) != (first["package_id"], first["name"], first["kind"])]))

    def test_warning_rejects(self):
        self.reject(lambda d: d["diagnostics"].append({"level": "warning", "code": "clippy::unused", "spans": []}))

    def test_raw_diagnostic_payload_rejects(self):
        self.reject(lambda d: d["diagnostics"].append({"level": "note", "code": None, "spans": [], "message": "redacted_fixture"}))

    def test_more_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("logical_cpu_limit", 2))

    def test_ram_threshold_relaxation_rejects(self):
        self.reject(lambda d: d.__setitem__("minimum_available_ram_mib", 0))

    def test_hot_baseline_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("system_cpu_percent", 85))

    def test_low_ram_observation_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))

    def test_gate_promotion_rejects(self):
        self.reject(lambda d: d.__setitem__("P09_gate", "PASS"))

    def test_lost_protected_binary_rejects(self):
        self.reject(lambda d: d["protected_executables"].pop())

    def test_source_inventory_omission_rejects(self):
        self.reject(lambda d: d["source_freeze"].pop())

    def test_initial_failure_cannot_be_erased(self):
        doc = copy.deepcopy(self.initial)
        doc["diagnostics"] = []
        with self.assertRaises(ValueError):
            V.validate_lint(doc, False)


if __name__ == "__main__":
    unittest.main()
