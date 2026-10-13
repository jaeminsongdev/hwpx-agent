"""Exact partial160 role's closed context, inverse and no promotion."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed160_partial_projection_v1 as m

class Tests(unittest.TestCase):
    def test_exact_declared_partial_role(self):
        row=m.declaration();self.assertEqual(row["current_case"],160)
        self.assertIn("partial_post_product",row["source_role"])
        self.assertFalse(row["original_failure_promoted"]);self.assertFalse(row["current_product_or_GO_qualified"])
    def test_entire_original_connect_code_inverse(self):
        code=m.original.connect.__code__;projected=m.project(code,m.MAPPING)
        self.assertEqual(m.project(projected,{v:k for k,v in m.MAPPING.items()}),code)
    def test_previous_failed004_names_not_reused(self):
        self.assertIn("failed160_partial_receipt_extension",m.MAPPING.values())
        self.assertNotIn("failed004_receipt_extension",m.MAPPING.values())
    def test_wrong_admission_rejected_before_graph_mutation(self):
        for bad in (dict(m.declaration(),current_case=159),dict(m.declaration(),original_failure_promoted=True),
                    dict(m.declaration(),source_role=m.original.ROLE)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):m.connect(None,None,bad)
    def test_exact_new_failure_path_is_distinct(self):
        self.assertEqual(m.ROOT["path"],m.attempt.STOPPED["path"])
        self.assertNotEqual(m.PHYSICAL,m.original.PHYSICAL)
        self.assertTrue(m.PHYSICAL.endswith("case160-runtime-run001.failed.envelope.v1.json"))
    def test_relabelled_root_pin_denied(self):
        row=m.declaration();row["failed_runtime_pin"]=dict(row["failed_runtime_pin"],sha256="0"*64)
        with self.assertRaises(ValueError):m.connect(None,None,row)
