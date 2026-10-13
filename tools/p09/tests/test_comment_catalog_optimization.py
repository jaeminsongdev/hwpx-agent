"""P132 runtime and byte-exact optimization boundary counterexamples."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p132", Path(__file__).resolve().parents[1] / "verify_comment_catalog_optimization.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class CatalogGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = V.expected_names()["Catalog"]
        cls.doc = V.R.read(V.run_path("Catalog", "Test"))

    def reject(self, mutation):
        doc = copy.deepcopy(self.doc)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            V.validate_run(doc, "Catalog", "Test", self.names)

    def test_current_catalog_accepts(self):
        self.assertEqual(V.validate_run(self.doc, "Catalog", "Test", self.names), 15)

    def test_inventory_is_exact(self):
        self.assertEqual([len(n) for n in V.expected_names().values()], [15, 10, 16, 24])

    def test_inverse_is_exact(self):
        V.validate_inverse((V.ROOT / V.ARCHIVES[V.PARENT]).read_bytes(), (V.ROOT / V.PARENT).read_bytes())

    def test_unrelated_parent_edit_rejects(self):
        with self.assertRaises(ValueError):
            V.validate_inverse((V.ROOT / V.ARCHIVES[V.PARENT]).read_bytes(), (V.ROOT / V.PARENT).read_bytes() + b"\n")

    def test_more_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("logical_cpu_limit", 2))

    def test_lower_ram_guard_rejects(self):
        self.reject(lambda d: d.__setitem__("minimum_available_ram_mib", 0))

    def test_sustained_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("samples", [d["samples"][0]] + [dict(d["samples"][0], system_cpu_percent=90)] * 3))

    def test_low_ram_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))

    def test_filtered_cases_reject(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("filtered", 1))

    def test_duplicate_case_rejects(self):
        self.reject(lambda d: d["tests"]["passed_test_names"].__setitem__(0, d["tests"]["passed_test_names"][1]))

    def test_source_omission_rejects(self):
        self.reject(lambda d: d["source_freeze"].pop())

    def test_old_executable_substitution_rejects(self):
        self.reject(lambda d: d.__setitem__("executable_pin", d["protected_executables"][0]))

    def test_timing_sample_omission_rejects(self):
        self.reject(lambda d: d["catalog_profile"]["before_ns"].pop())

    def test_unobserved_speedup_rejects(self):
        self.reject(lambda d: d["catalog_profile"].__setitem__("after_ns", d["catalog_profile"]["before_ns"]))

    def test_end_to_end_promotion_rejects(self):
        self.reject(lambda d: d["catalog_profile"].__setitem__("scope", "end_to_end"))

    def test_native_promotion_rejects(self):
        self.reject(lambda d: d["catalog_profile"].__setitem__("native_verified", True))


if __name__ == "__main__":
    unittest.main()
