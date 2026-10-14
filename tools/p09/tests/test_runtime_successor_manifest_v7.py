from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import runtime_successor_manifest_v7 as m
from test_review_failed_run003_v1 import exact,fields,require
API=NS(exact=exact,fields=fields,require=require)
def pin(path):return dict(path=path,bytes=1,sha256="a"*64)
class Tests(unittest.TestCase):
    def setUp(self):
        self.base=pin("manifest028")
        self.row=dict(schema_version=m.SCHEMA,index=160,before=153,physical_product_run=4,
            base_manifest_pin=self.base,extra_failure_producer_pin=pin(m.extras.PRODUCER),prior132_producer_pin=pin(m.PRIOR_PRODUCER))
    def test_exact_stored_current_context(self):self.assertEqual(m.validate(self.row,API,self.base),self.row)
    def test_old_physical_not_relabelled(self):
        self.row["physical_product_run"]=3
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_bool_before_rejected(self):
        self.row["before"]=True
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_wrong_current_index_rejected(self):
        self.row["index"]=161
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_missing_failure_producer_rejected(self):
        del self.row["extra_failure_producer_pin"]
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_other_prior_producer_rejected(self):
        self.row["prior132_producer_pin"]["path"]="other"
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_rebased_original_manifest_rejected(self):
        self.row["base_manifest_pin"]=pin("other")
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
    def test_extra_permission_key_rejected(self):
        self.row["GO_authorized"]=True
        with self.assertRaises(ValueError):m.validate(self.row,API,self.base)
if __name__=="__main__":unittest.main()
