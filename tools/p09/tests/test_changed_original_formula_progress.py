"""P121 current real-runtime negative guards; no native/trust/SQL acceptance."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

SPEC=importlib.util.spec_from_file_location("p121",Path(__file__).parents[1]/"verify_changed_original_formula_progress.py")
P121=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P121)

class ChangedRuntimeGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=json.loads((P121.ROOT/P121.RUNS[6]).read_bytes())
        cls.freeze=json.loads((P121.ROOT/P121.FREEZE).read_bytes())["source_freeze"]
        cls.executable=cls.runtime["executable_pin"]

    def check(self,doc): return P121.validate_runtime(doc,3,225,self.freeze,self.executable)
    def reject(self,edit):
        changed=copy.deepcopy(self.runtime)
        edit(changed)
        with self.assertRaises(ValueError): self.check(changed)

    def test_actual_runtime_positive(self): self.assertEqual(self.check(self.runtime)["cases"],16)
    def test_no_ignored_tests(self): self.reject(lambda d:d["tests"]["terminal_summary"].update(ignored=1))
    def test_no_false_gate(self): self.reject(lambda d:d.update(P09_gate="PASS"))
    def test_no_false_product(self): self.reject(lambda d:d.update(product_complete=True))
    def test_source_identity(self): self.reject(lambda d:d.update(source_freeze=[]))
    def test_executable_identity(self): self.reject(lambda d:d["executable_pin"].update(sha256="0"*64))
    def test_no_same_changed_bytes(self): self.reject(lambda d:d["tests"]["changed_corpus_result"]["rows"][0].update(candidate_sha256=d["tests"]["changed_corpus_result"]["rows"][0]["derivative_sha256"]))
    def test_no_duplicate_original(self): self.reject(lambda d:d["tests"]["changed_corpus_result"]["rows"][1].update(index=d["tests"]["changed_corpus_result"]["rows"][0]["index"]))
    def test_no_claim_boolean_string(self): self.reject(lambda d:d["tests"]["changed_corpus_result"]["rows"][0].update(outside_result_leaves_exact="true"))
    def test_protection_required(self): self.reject(lambda d:d["tests"].update(changed_protection_pass=False))
    def test_ram_guard(self): self.reject(lambda d:d["samples"][0].update(available_ram_mib=4095))
    def test_single_worker(self): self.reject(lambda d:d["plan"].update(test_arguments=["--test-threads=16"]))

if __name__=="__main__": unittest.main(verbosity=1)
