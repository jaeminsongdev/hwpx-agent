import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import same_reader_history_declaration_once_v1 as m
from test_same_reader_failure_review_once_v1 import Reader,ROOT

DECL=dict(next_case=159,accepted_count_before=152,prior_case=158,
    prior_failures_promoted=False,current159_or_GO_qualified=False,failures=[dict(ROOT)])

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.result=copy.deepcopy(DECL);self.error=None
        def original(q,a,first,second):
            self.calls.append(q)
            if self.error is not None:raise self.error
            q.snapshots[ROOT["path"]]=dict(ROOT)
            return copy.deepcopy(self.result)
        self.call,self.counts=m.connect(original,DECL)
        self.q=Reader();self.deps=(object(),object(),object())
    def test_first_complete_then_same_declaration(self):
        self.assertEqual(self.call(self.q,*self.deps),DECL)
        self.assertEqual(self.call(self.q,*self.deps),DECL)
        self.assertEqual(len(self.calls),1)
    def test_other_reader_not_reused(self):
        self.call(self.q,*self.deps);self.call(Reader(),*self.deps)
        self.assertEqual(len(self.calls),2)
    def test_each_dependency_identity_not_reused(self):
        self.call(self.q,*self.deps)
        for index in range(3):
            deps=list(self.deps);deps[index]=object();self.call(self.q,*deps)
        self.assertEqual(len(self.calls),4)
    def test_changed_ledger_not_reused(self):
        self.call(self.q,*self.deps);self.q.snapshots[ROOT["path"]]=dict(ROOT,bytes=99)
        self.call(self.q,*self.deps);self.assertEqual(len(self.calls),2)
    def test_final_started_not_reused(self):
        self.call(self.q,*self.deps);self.q.final_fresh_hashes=1
        self.call(self.q,*self.deps);self.assertEqual(len(self.calls),2)
    def test_resource_stop_is_original(self):
        state={"stop":False};error=ValueError("ORIGINAL_STOP")
        def checkpoint():
            if state["stop"]:raise error
        self.q.checkpoint=checkpoint;self.call(self.q,*self.deps);state["stop"]=True
        with self.assertRaises(ValueError) as caught:self.call(self.q,*self.deps)
        self.assertIs(caught.exception,error)
    def test_first_error_not_cached(self):
        self.error=ValueError("ORIGINAL_FULL_STOP")
        with self.assertRaises(ValueError) as caught:self.call(self.q,*self.deps)
        self.assertIs(caught.exception,self.error)
        self.error=None;self.call(self.q,*self.deps);self.assertEqual(len(self.calls),2)
    def test_returned_declaration_cannot_mutate_witness(self):
        row=self.call(self.q,*self.deps);row["failures"][0]["bytes"]=100
        self.assertEqual(self.call(self.q,*self.deps),DECL)
    def test_runtime_row_or_promoted_result_rejected(self):
        self.result["source_frame"]={}
        with self.assertRaises(ValueError):self.call(self.q,*self.deps)
    def test_current160_declaration_rejected(self):
        with self.assertRaises(ValueError):m.connect(lambda:None,dict(DECL,next_case=160))
    def test_checkpoint_change_not_reused(self):
        self.call(self.q,*self.deps);self.q.checkpoint=lambda:None
        self.call(self.q,*self.deps);self.assertEqual(len(self.calls),2)
    def test_new_input_preserves_existing_ledger(self):
        self.call(self.q,*self.deps);self.q.snapshots["extra"]=dict(ROOT,path="extra")
        self.call(self.q,*self.deps);self.assertEqual(len(self.calls),1)

if __name__=="__main__":unittest.main()
