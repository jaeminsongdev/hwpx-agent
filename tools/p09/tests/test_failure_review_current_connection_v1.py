import copy
from pathlib import Path
import sys
from types import FunctionType,ModuleType,SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import failure_review_current_connection_v1 as m
import same_reader_failure_review_once_v1 as helper
from test_same_reader_failure_review_once_v1 import ROOT,REVIEW,DECL,Reader

def require(ok,label):
    if not ok:raise ValueError(label)
def exact(left,right,label):require(left==right,label)
def fields(row,expected,label):require(all(row.get(k)==v for k,v in expected.items()),label)

class Tests(unittest.TestCase):
    def setUp(self):
        self.api=NS(require=require,exact=exact,fields=fields)
        self.calls=[]
        env=dict(STOPPED=ROOT,REVIEW=REVIEW["path"],calls=self.calls,copy=copy,DECL=DECL)
        exec("def reviewed_failure(q,a):\n calls.append(q)\n q.snapshots.update({p['path']:copy.deepcopy(p) for p in (STOPPED,DECL['review_pin'])})\n return copy.deepcopy(DECL)",env)
        attempt=NS(reviewed_failure=env["reviewed_failure"],STOPPED=ROOT,REVIEW=REVIEW["path"])
        role=NS(attempt=attempt,previous=NS(attempt=attempt))
        self.c=NS(attempt=attempt,binding_module=NS(manifest=NS(original=NS(role=role))),
            bootstrap=NS(original=NS(partial=role)),M=NS(a=self.api,
            base=NS(CONFIG=NS(index=160,before=153))))
        self.c.own_inputs=FunctionType((lambda q:None).__code__,{"attempt":attempt})
        self.q=Reader()
        self.q.pin=lambda p: self.q.snapshots.setdefault(p,dict(path=p,bytes=1,sha256="a"*64))
        self.proof=dict(state="PASS_SAME_READER_FAILED160_REVIEW_CODE14_AND_REAL_FIRST_REVIEW_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=dict(run=14,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            new_controller_or_GO_qualified=False,Native_or_product_executed=False,
            source_pins=[],failed_runtime_pin=ROOT,review_pin=REVIEW)
        self.q.json=lambda p:(self.q.pin(p),self.proof)[1]

    def test_same_private_dependency_all_sites_and_restore(self):
        old=self.c.attempt.reviewed_failure
        restore,counts,proof=m.connect(self.c,self.q,helper)
        self.c.attempt.reviewed_failure(self.q,self.api)
        self.c.bootstrap.original.partial.previous.attempt.reviewed_failure(self.q,self.api)
        self.assertEqual(len(self.calls),1);self.assertEqual(counts["duplicate_declarations_avoided"],1)
        self.assertFalse(proof["default_module_or_source_file_mutated"])
        restore();self.assertIs(self.c.attempt.reviewed_failure,old)

    def test_real_module_controller_rejected_before_mutation(self):
        with self.assertRaises(ValueError):m.connect(ModuleType("default"),self.q,helper)

    def test_default_attempt_module_rejected(self):
        self.c.attempt=ModuleType("default")
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)

    def test_separate_role_dependency_rejected(self):
        self.c.bootstrap.original.partial=NS()
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)

    def test_wrong_current_case_rejected(self):
        self.c.M.base.CONFIG.index=159
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)

    def test_duplicate_connection_rejected(self):
        restore,_,_=m.connect(self.c,self.q,helper)
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)
        restore()

    def test_unqualified_proof_rejected(self):
        self.proof["cleanup_confirmed"]=False
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)

    def test_wrong_review_pin_rejected(self):
        self.proof["review_pin"]=dict(REVIEW,path="other.json")
        with self.assertRaises(ValueError):m.connect(self.c,self.q,helper)

if __name__=="__main__":unittest.main()
