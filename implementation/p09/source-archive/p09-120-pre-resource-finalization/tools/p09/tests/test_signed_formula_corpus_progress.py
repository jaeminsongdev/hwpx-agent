"""Exact original corpus/current receipt negative guards, not native/issuer/SQL execution evidence."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
SPEC = importlib.util.spec_from_file_location("p120_bytes",Path(__file__).parents[1] / "verify_signed_formula_corpus_progress.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = V.inherited()
        cls.data = json.loads((V.ROOT / V.CURRENT).read_bytes())
        cls.corpus = json.loads((V.ROOT / V.NEW_SOURCES[-1]).read_bytes())
        cls.regression = json.loads((V.ROOT / V.NEW_SOURCES[-2]).read_bytes())
    def test_whole_previous_audit_and_exact_parent_inverse(self):
        self.assertEqual(self.prior["unchanged_previous_source_files"],1080)
        self.assertTrue(self.prior["previous_unmodified_audit_on_preimages_passed"])
        self.assertEqual(self.prior["old_executables_preserved"],497)
    def test_exact_current_inventory(self):
        self.assertEqual(V.verify_current_manifest(self.data,self.prior),{
            "source_delta":9,"source_archives_added":6,"predecessor_receipts_added":2,"current_executables":4})
    def test_every_pin_group_rejects_missing_duplicate_extra_or_changed_entries(self):
        for group in ["source_delta","source_archives_added","predecessor_receipts_added","current_executables"]:
            for change in ["missing","duplicate","extra","hash","bytes"]:
                data = copy.deepcopy(self.data)
                if change == "missing": data[group].pop()
                elif change == "duplicate": data[group].append(copy.deepcopy(data[group][0]))
                elif change == "extra": data[group].append({"path":"not-in-scope","bytes":0,"sha256":"0"*64})
                elif change == "hash": data[group][0]["sha256"] = "0"*64
                else: data[group][0]["bytes"] += 1
                with self.subTest(group=group,change=change),self.assertRaises(ValueError): V.verify_current_manifest(data,self.prior)
    def test_no_unsupported_qualification_promotion(self):
        for key in V.FALSE_QUALIFICATIONS:
            data = copy.deepcopy(self.data); data["qualification"][key] = True
            with self.subTest(key=key),self.assertRaises(ValueError): V.verify_current_manifest(data,self.prior)
    def test_gate_count_and_undeclared_parent_edit_never_promote(self):
        for key,value in [("P09_gate","PASS"),("P10_new_implementation",True),("product_complete",True),
            ("remaining_coarse_groups_minimum",5),("remaining_coarse_groups_closed_by_slice",1),
            ("conversation_minimum_30_conditions_not_exhaustive_or_decremented",False),("current_source_files_count",1088)]:
            data = copy.deepcopy(self.data); data[key] = value
            with self.subTest(key=key),self.assertRaises(ValueError): V.verify_current_manifest(data,self.prior)
        path = V.PARENTS[0]; current = (V.ROOT / path).read_bytes(); archive = (V.ROOT / (V.ARCHIVE+path)).read_bytes()
        self.assertEqual(V.restored_parent(path,current),archive)
        self.assertNotEqual(V.restored_parent(path,current+b"undeclared edit"),archive)
        with self.assertRaises(ValueError): V.restored_parent(path,archive)
    def test_corpus_coverage_source_identity_and_derivative_counts_cannot_drift(self):
        for case in range(10):
            data = copy.deepcopy(self.corpus)
            if case == 0: data["result"]["originals"].pop()
            elif case == 1: data["result"]["originals"][1] = copy.deepcopy(data["result"]["originals"][0])
            elif case == 2: data["result"]["originals"][0]["source_sha256"] = "0"*64
            elif case == 3: data["result"]["counts"][1] = 19
            elif case == 4: data["derived_current_cases"] = 15
            elif case == 5: data["protected_derivative_cases"] = 31
            elif case == 6: data["production_trust_verified"] = True
            elif case == 7: data["native_recalculation_verified"] = True
            elif case == 8: data["result"]["originals"][0]["index"] = False
            else: data["result"]["counts"][0] = 16.0
            with self.subTest(case=case),self.assertRaises(ValueError): V.verify_corpus(data)
    def test_corpus_positive_candidate_preservation_and_revocation_guards_cannot_drift(self):
        for key,value in [("candidate_sha256","invalid"),("formula_targets",True),("source_cell_bindings",7),
                          ("whole_candidate_and_outside_leaves_exact",False),("live_revocation_denied_callback",False)]:
            data = copy.deepcopy(self.corpus)
            row = next(r for r in data["result"]["originals"] if r["outcome"] != "no_formula_denied_no_policy_proof_or_result")
            row[key] = value
            with self.subTest(key=key),self.assertRaises(ValueError): V.verify_corpus(data)
    def test_tested_source_runtime_scope_and_executable_cannot_drift(self):
        for case in range(7):
            data = copy.deepcopy(self.regression)
            if case == 0: data["source_freeze"].pop()
            elif case == 1: data["source_freeze"][0]["sha256"] = "0"*64
            elif case == 2: data["runtime"]["passed"] = 304
            elif case == 3: data["runtime"]["filtered"] = 1
            elif case == 4: data["runtime"]["other_P119_suites_rerun"] = True
            elif case == 5: data["test_executable"]["sha256"] = "0"*64
            else: data["state"] = "IN_PROGRESS"
            with self.subTest(case=case),self.assertRaises(ValueError): V.verify_regression(data,self.data)
if __name__ == "__main__": unittest.main()
