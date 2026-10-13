"""Real Model10 receipt guards; mutated clones are unit counterexamples, not runtime evidence."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p128", Path(__file__).parents[1] / "verify_comment_regression_progress.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class Guards(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((P.ROOT / "target/p09-121-resource-optimized/p128-model-tests-a.json").read_bytes())

    def reject(self, edit):
        doc = copy.deepcopy(self.doc)
        edit(doc)
        with self.assertRaises(ValueError): P.validate_runtime(doc, "Model", "Test")

    def test_real_positive(self): self.assertEqual(P.validate_runtime(self.doc, "Model", "Test")["test_count"], 10)
    def test_wrong_suite(self): self.reject(lambda d: d.update(suite="Operation"))
    def test_extra_cpu(self): self.reject(lambda d: d.update(logical_cpu_limit=16))
    def test_ram_threshold_relaxed(self): self.reject(lambda d: d.update(minimum_available_ram_mib=0))
    def test_cpu_threshold_relaxed(self): self.reject(lambda d: d.update(cpu_stop_percent=100))
    def test_sustained_cpu(self):
        self.reject(lambda d: d.update(samples=[dict(d["samples"][0], system_cpu_percent=100)] * 3))
    def test_low_ram_observed(self): self.reject(lambda d: d["samples"][0].update(available_ram_mib=1024))
    def test_fake_gate(self): self.reject(lambda d: d.update(P09_gate="PASS"))
    def test_source_drift(self): self.reject(lambda d: d.update(source_freeze=[]))
    def test_duplicate_cases(self):
        self.reject(lambda d: d["tests"]["passed_test_names"].__setitem__(1, d["tests"]["passed_test_names"][0]))
    def test_ignored_case(self): self.reject(lambda d: d["tests"]["terminal_summary"].update(ignored=1))
    def test_failed_count(self): self.reject(lambda d: d["tests"]["terminal_summary"].update(failed=1))


if __name__ == "__main__": unittest.main(verbosity=1)
