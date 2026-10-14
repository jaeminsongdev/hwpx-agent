import copy
from pathlib import Path
import sys
from types import FunctionType,SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed160_extras_v1 as m
from test_review_failed_run003_v1 import exact

def pin(name):return dict(path=name,bytes=1,sha256="a"*64)
def descriptor(old,new,*,next_case):return dict(old=old,new=new,next_case=next_case,delegated=True)
def init(self):pass
def graph():
    env=dict(__name__="p09_exact_test",descriptor=descriptor)
    constructor=FunctionType(init.__code__,env)
    projection=type("Projection",(),{"__init__":constructor})
    source=NS(Projection=projection,descriptor=descriptor,copy_pin=lambda p:copy.deepcopy(p),SCHEMA="descriptor/v1")
    class Binding:
        def representation(self,projection):return dict(original_retained=True)
    binding=NS(source=source,Binding=Binding,exact=exact)
    admitted=[dict(schema_version=m.SCHEMA,current_case=160,failed_runtime_pin=dict(root),
        independent_review_pin=pin("review"+str(i)),physical_pin=pin("implementation/p09/evidence/p361-lossless-runtime-inputs/case160-runtime-run%03d.failed.envelope.v1.json"%(i+2)),
        original_failure_promoted=False,current_product_or_GO_qualified=False) for i,root in enumerate(m.ROOTS)]
    return source,binding,admitted
class Tests(unittest.TestCase):
    def test_both_exact_failed_descriptors_admitted_not_success(self):
        source,binding,rows=graph();proof=m.connect(source,binding,rows)
        for row in rows:
            d=source.descriptor(row["failed_runtime_pin"],row["physical_pin"],next_case=160)
            self.assertEqual(d["semantic_original_pin"],row["failed_runtime_pin"])
        self.assertFalse(proof["GO_authorized"])
    def test_all_other_paths_delegated(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        self.assertTrue(source.descriptor(pin("other"),pin("new"),next_case=159)["delegated"])
    def test_provenance_retains_both_failed_not_accepted_roles(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        obj=binding.Binding();obj.originals={r["path"]:r for r in m.ROOTS}
        result=obj.representation(None);self.assertTrue(result["original_retained"])
        self.assertEqual(len(result["same_case_failed160_extra_receipt_provenance"]),2)
        self.assertFalse(result["same_case_failed160_extra_receipt_provenance"][0]["original_failure_promoted"])
    def test_returned_provenance_cannot_mutate_private_admission(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        obj=binding.Binding();obj.originals={r["path"]:r for r in m.ROOTS};result=obj.representation(None)
        result["same_case_failed160_extra_receipt_provenance"][0]["failed_runtime_pin"]["bytes"]=1
        self.assertEqual(source.failed160_extra_receipts[0]["failed_runtime_pin"],m.SECOND)
    def test_default_or_shared_environment_rejected(self):
        source,binding,rows=graph();source.Projection.__init__.__globals__["__name__"]="default"
        with self.assertRaises(ValueError):m.connect(source,binding,rows)
    def test_reinstall_rejected(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        with self.assertRaises(ValueError):m.connect(source,binding,rows)
    def test_promoted_failure_rejected(self):
        source,binding,rows=graph();rows[0]["original_failure_promoted"]=True
        with self.assertRaises(ValueError):m.connect(source,binding,rows)
    def test_foreign_original_pin_rejected(self):
        source,binding,rows=graph();rows[0]["failed_runtime_pin"]["sha256"]="b"*64
        with self.assertRaises(ValueError):m.connect(source,binding,rows)
    def test_wrong_physical_path_rejected(self):
        source,binding,rows=graph();rows[0]["physical_pin"]["path"]="unrelated"
        with self.assertRaises(ValueError):m.connect(source,binding,rows)
    def test_modified_physical_bytes_rejected(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        p=dict(rows[0]["physical_pin"],bytes=2)
        with self.assertRaises(ValueError):source.descriptor(m.SECOND,p,next_case=160)
    def test_wrong_or_bool_case_rejected(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        for value in (159,True):
            with self.assertRaises(ValueError):source.descriptor(m.SECOND,rows[0]["physical_pin"],next_case=value)
    def test_missing_failed_alias_not_silently_omitted(self):
        source,binding,rows=graph();m.connect(source,binding,rows)
        obj=binding.Binding();obj.originals={m.SECOND["path"]:m.SECOND}
        with self.assertRaises(ValueError):obj.representation(None)
if __name__=="__main__":unittest.main()
