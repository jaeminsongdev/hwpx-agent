"""Same real targeted corpus; resource limits may only become stricter, no scope promotion."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location("p123",Path(__file__).parents[1]/"verify_single_cpu_formula_regression.py")
P123=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P123)

class Guards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads((P123.ROOT/P123.P121.RUNS[6]).read_bytes())
        cls.freeze=cls.doc["source_freeze"]
        cls.exe=cls.doc["executable_pin"]
    def check(self,doc): return P123.validate_component(doc,3,225,self.freeze,self.exe,2)
    def reject(self,edit):
        doc=copy.deepcopy(self.doc);edit(doc)
        with self.assertRaises(ValueError): self.check(doc)
    def test_actual_targeted_positive(self): self.assertEqual(self.check(self.doc)["cases"],16)
    def test_one_cpu_policy_only(self):
        doc=copy.deepcopy(self.doc);doc["plan"]["logical_cpu_limit"]=1;doc["plan"]["affinity_mask"]=1
        P123.validate_policy(doc,1) # Arithmetic policy test, NOT one-CPU execution evidence.
    def test_more_cpu_rejected(self): self.reject(lambda d:d["plan"].update(logical_cpu_limit=16,affinity_mask=65535))
    def test_mask_mismatch(self): self.reject(lambda d:d["plan"].update(affinity_mask=1))
    def test_cpu_threshold_not_relaxed(self): self.reject(lambda d:d["plan"].update(cpu_stop_percent=100))
    def test_ram_threshold_not_relaxed(self): self.reject(lambda d:d["plan"].update(minimum_available_ram_mib=0))
    def test_workers_not_increased(self): self.reject(lambda d:d["plan"].update(test_arguments=["--test-threads=16"]))
    def test_no_fake_full_count(self): self.reject(lambda d:d["tests"]["terminal_summary"].update(passed=228))
    def test_ignored_rejected(self): self.reject(lambda d:d["tests"]["terminal_summary"].update(ignored=1))
    def test_false_gate_rejected(self): self.reject(lambda d:d.update(P09_gate="PASS"))
    def test_changed_receipt_rejected(self): self.reject(lambda d:d["tests"]["changed_corpus_result"].update(cases=15))
    def test_source_identity_rejected(self): self.reject(lambda d:d.update(source_freeze=[]))

class DocumentGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads((P123.ROOT/P123.DOCUMENT_RUN).read_bytes())
        cls.freeze=cls.doc["source_freeze"];cls.exe=cls.doc["executable_pin"]
    def test_actual_document20(self):
        self.assertEqual(len(P123.validate_scoped(self.doc,20,208,self.freeze,self.exe,1)["passed_test_names"]),20)
    def test_document_not_full228(self):
        with self.assertRaises(ValueError): P123.validate_scoped(self.doc,228,0,self.freeze,self.exe,1)
    def test_duplicate_document_names(self):
        doc=copy.deepcopy(self.doc);doc["tests"]["passed_test_names"][1]=doc["tests"]["passed_test_names"][0]
        with self.assertRaises(ValueError): P123.validate_scoped(doc,20,208,self.freeze,self.exe,1)

if __name__=="__main__": unittest.main(verbosity=1)
