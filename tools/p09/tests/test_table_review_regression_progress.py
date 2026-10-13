"""P131 runtime/inventory guard counterexamples, not native qualification."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p131", Path(__file__).resolve().parents[1] / "verify_table_review_regression_progress.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class TableReviewGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = V.expected_names()
        cls.doc = V.R.read(V.run_path("Output", "Test"))

    def reject(self, mutation):
        doc = copy.deepcopy(self.doc)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            V.validate_run(doc, "Output", "Test", self.names["Output"])

    def test_actual_current_run_accepts(self):
        self.assertEqual(V.validate_run(self.doc, "Output", "Test", self.names["Output"]), 21)

    def test_legacy_runner_and_snapshot_remain_exact(self):
        self.assertEqual(V.validate_run(V.R.read(V.run_path("Create", "Test")), "Create", "Test", self.names["Create"]), 8)

    def test_current_compiled_inventory_accepts(self):
        V.validate_run(V.R.read(V.run_path("Filled", "List")), "Filled", "List", self.names["Filled"])

    def test_source_definition_counts_not_duplicate_executions(self):
        self.assertEqual([len(self.names[k]) for k in V.SUITES], [8, 15, 21, 23])
        self.assertEqual(len({n for n in self.names["Output"] if not n.startswith("previous::")}), 6)

    def test_wrong_suite_rejects(self):
        self.reject(lambda d: d.__setitem__("suite", "Create"))

    def test_duplicate_case_rejects(self):
        self.reject(lambda d: d["tests"]["passed_test_names"].__setitem__(0, d["tests"]["passed_test_names"][1]))

    def test_ignored_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("ignored", 1))

    def test_filtered_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("filtered", 1))

    def test_failed_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("failed", 1))

    def test_worker_input_omission_rejects(self):
        self.reject(lambda d: d.__setitem__("source_freeze", [r for r in d["source_freeze"] if r["path"] != V.LEGACY_OMITTED]))

    def test_source_hash_drift_rejects(self):
        self.reject(lambda d: d["source_freeze"][0].__setitem__("sha256", "0" * 64))

    def test_old_executable_substitution_rejects(self):
        self.reject(lambda d: d.__setitem__("executable_pin", d["protected_executables"][0]))

    def test_more_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("logical_cpu_limit", 2))

    def test_lower_ram_guard_rejects(self):
        self.reject(lambda d: d.__setitem__("minimum_available_ram_mib", 0))

    def test_hot_baseline_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("system_cpu_percent", 85))

    def test_low_ram_sample_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))

    def test_product_promotion_rejects(self):
        self.reject(lambda d: d.__setitem__("product_complete", True))

    def test_gate_promotion_rejects(self):
        self.reject(lambda d: d.__setitem__("P09_gate", "PASS"))


if __name__ == "__main__":
    unittest.main()
