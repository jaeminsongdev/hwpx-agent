from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import runtime_successor_manifest_v8 as m
from test_review_failed_run003_v1 import exact,fields,require
API=NS(exact=exact,fields=fields,require=require)
def pin(path):return dict(path=path,bytes=1,sha256="a"*64)
class Tests(unittest.TestCase):
    def setUp(self):
        self.base=pin("manifest029")
        self.row=dict(schema_version=m.SCHEMA,index=160,before=153,physical_product_run=4,
            base_manifest_pin=self.base,extra_prior_producer_pin=pin(m.PRODUCER))
        self.producer=dict(state="PASS_REAL_PRIOR136130_EXCLUSIVE_LOSSLESS_NOT_ADOPTED_MANIFEST_OR_GO",
            exact_original_restore_passes=4,write_rate_bytes_per_second=2097152,cleanup_confirmed=True,
            original_receipts_rewritten=False,product_or_Native_reexecuted=False,GO_authorized=False,
            fresh_inputs=1,final_fresh_hashes=1,selected_outputs=[dict(original_pin=dict(p)) for p in m.PRIORS])
    def test_exact_current_manifest(self):m.validate(self.row,API,self.base)
    def test_old_run_rejected(self):
        self.row["physical_product_run"]=3
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_rebased_manifest_rejected(self):
        with self.assertRaises(ValueError):m.validate(self.row,API,pin("other"))
    def test_extra_permission_key_rejected(self):
        self.row["GO_authorized"]=True
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_real_prior_order_exact(self):self.assertEqual(len(m.selected(self.producer,API)),2)
    def test_other_prior_rejected(self):
        self.producer["selected_outputs"][0]["original_pin"]["sha256"]="b"*64
        with self.assertRaises(ValueError):m.selected(self.producer,API)
    def test_partial_fresh_rejected(self):
        self.producer["final_fresh_hashes"]=0
        with self.assertRaises(ValueError):m.selected(self.producer,API)
    def test_raw_receipt_rewrite_not_accepted(self):
        self.producer["original_receipts_rewritten"]=True
        with self.assertRaises(ValueError):m.selected(self.producer,API)
if __name__=="__main__":unittest.main()
