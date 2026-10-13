"""P129 guard counterexamples are units, not additional product tests."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p129", Path(__file__).resolve().parents[1] / "run_current_stored_batch.py")
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class CurrentStoredGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = R.read(R.RUN + "p129-current-case-001-attempt-001.json")
        cls.freeze = R.read(R.BUILD)["source_freeze"]
        cls.name = cls.doc["test_name"]

    def reject(self, mutation):
        doc = copy.deepcopy(self.doc)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            R.accept_case(doc, self.name, self.freeze)

    def test_actual_current_case_accepts(self):
        R.accept_case(self.doc, self.name, self.freeze)

    def test_reordered_inventory_remains_exact(self):
        doc = copy.deepcopy(self.doc)
        doc["source_freeze"].reverse()
        R.accept_case(doc, self.name, self.freeze)

    def test_duplicate_source_rejects(self):
        self.reject(lambda d: d["source_freeze"].__setitem__(0, d["source_freeze"][1]))

    def test_source_hash_drift_rejects(self):
        self.reject(lambda d: d["source_freeze"][0].__setitem__("sha256", "0" * 64))

    def test_old_binary_substitution_rejects(self):
        self.reject(lambda d: d.__setitem__("executable_pin", R.pin(R.OLD_EXE)))

    def test_different_case_rejects(self):
        self.reject(lambda d: d.__setitem__("test_name", "unrelated_case"))

    def test_false_historical_preservation_rejects(self):
        self.reject(lambda d: d.__setitem__("historical_executable_exact_after", False))

    def test_extra_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("logical_cpu_limit", 2))

    def test_lower_ram_guard_rejects(self):
        self.reject(lambda d: d.__setitem__("minimum_available_ram_mib", 1))

    def test_hot_three_samples_rejects(self):
        self.reject(lambda d: d.__setitem__("samples", [dict(d["samples"][0], system_cpu_percent=100)] * 3))

    def test_hot_baseline_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("system_cpu_percent", 85))

    def test_low_ram_sample_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))

    def test_gate_promotion_rejects(self):
        self.reject(lambda d: d.__setitem__("P09_gate", "PASS"))

    def test_failed_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("failed", 1))

    def test_ignored_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("ignored", 1))

    def test_missing_filtered_case_rejects(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].__setitem__("filtered", 226))

    def test_duplicate_pass_name_rejects(self):
        self.reject(lambda d: d["tests"].__setitem__("passed_test_names", [self.name, self.name]))


if __name__ == "__main__":
    unittest.main()
