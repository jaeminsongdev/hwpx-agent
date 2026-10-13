"""Actual metric pair evidence negative guards; not stored228/native acceptance."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location("p122",Path(__file__).parents[1]/"verify_resource_crosscheck_progress.py")
P122=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P122)

class MetricGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.doc=json.loads((P122.ROOT/P122.RUNS[1]).read_bytes())
    def reject(self,edit):
        doc=copy.deepcopy(self.doc);edit(doc)
        with self.assertRaises(ValueError): P122.validate_pairs(doc,True)
    def test_actual_pair_positive(self): self.assertEqual(P122.validate_pairs(self.doc,True)["samples"],4)
    def test_bool_cpu(self): self.reject(lambda d:d["samples"][0].update(native_cpu_percent=True))
    def test_nan_cpu(self): self.reject(lambda d:d["samples"][0].update(native_cpu_percent=float("nan")))
    def test_infinite_ram(self): self.reject(lambda d:d["samples"][0].update(native_available_ram_mib=float("inf")))
    def test_cpu_not_relaxed(self): self.reject(lambda d:d["samples"][0]["conservative_inputs"].update(system_cpu_percent=0))
    def test_ram_not_relaxed(self): self.reject(lambda d:d["samples"][0]["conservative_inputs"].update(available_ram_mib=999999))
    def test_hot_samples_not_fabricated(self): self.reject(lambda d:d["samples"][0].update(consecutive_hot_samples=3))
    def test_decision_not_fabricated(self): self.reject(lambda d:d["samples"][0].update(resource_decision="PASS"))
    def test_measurement_not_tests(self): self.reject(lambda d:d.update(stored_test_started=True))
    def test_gate_not_promoted(self): self.reject(lambda d:d.update(P09_gate="PASS"))
    def test_count_not_dropped(self): self.reject(lambda d:d["samples"].pop())
    def test_windows_not_same(self): self.reject(lambda d:d.update(measurements_have_adjacent_not_identical_windows=False))

if __name__=="__main__": unittest.main(verbosity=1)
