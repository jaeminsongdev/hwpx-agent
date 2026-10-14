from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import successor_bounded_graph_bootstrap_v6 as m
from test_review_failed_run003_v1 import exact,fields,require
API=NS(exact=exact,fields=fields,require=require)
def pin(name):return dict(path=name,bytes=1,sha256="a"*64)
def row():return dict(state="PASS_EXCLUSIVE_FAILED002003_TRANSPORT_NOT_ADMITTED_MANIFEST_RUNTIME_OR_GO",
    exact_original_restore_passes=4,cleanup_confirmed=True,failures_promoted=False,original_failures_rewritten=False,
    actual_product_or_Native_executed=False,GO_authorized=False,
    selected_outputs=[dict(original_pin=dict(p),physical_pin=pin("physical"+str(i)),independent_review_pin=pin("review"+str(i))) for i,p in enumerate(m.extras.ROOTS)])
class Tests(unittest.TestCase):
    def test_both_declarations_remain_unqualified(self):
        values=m.declared_failures(row(),API);self.assertEqual(len(values),2)
        self.assertFalse(values[1]["current_product_or_GO_qualified"])
    def test_promoted_failure_rejected(self):
        value=row();value["failures_promoted"]=True
        with self.assertRaises(ValueError):m.declared_failures(value,API)
    def test_foreign_root_rejected(self):
        value=row();value["selected_outputs"][0]["original_pin"]["sha256"]="b"*64
        with self.assertRaises(ValueError):m.declared_failures(value,API)
    def test_extra_or_missing_rows_rejected(self):
        value=row();value["selected_outputs"].pop()
        with self.assertRaises(ValueError):m.declared_failures(value,API)
    def test_exact_extra_files_small_enough_for_original_reader(self):
        self.assertEqual(len(m.EXTRA_PINS),4)
        self.assertTrue(all(0<p["bytes"]<=16384 for p in m.EXTRA_PINS))
if __name__=="__main__":unittest.main()
