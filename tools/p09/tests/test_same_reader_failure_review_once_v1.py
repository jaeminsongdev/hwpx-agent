import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import same_reader_failure_review_once_v1 as m

ROOT=dict(path="failed.json",bytes=4,sha256="a"*64)
REVIEW=dict(path="review.json",bytes=5,sha256="b"*64)
DECL=dict(failed_runtime_pin=ROOT,review_pin=REVIEW,original_failure_promoted=False,
    queue_acceptance_called=False,physical_run002_or_GO_authorized=False)
class Reader:
    def __init__(self):
        self.snapshots={};self.final_fresh_hashes=0;self.checkpoint=lambda:None

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.error=None;self.row=copy.deepcopy(DECL);self.api=object()
        def original(q,a):
            self.calls.append(q)
            if self.error is not None:raise self.error
            q.snapshots.update({p["path"]:copy.deepcopy(p) for p in (ROOT,REVIEW)})
            return copy.deepcopy(self.row)
        self.original=original
        self.checked,self.counts=m.connect(original,expected_runtime_pin=ROOT,expected_review_pin=REVIEW)
        self.q=Reader()

    def test_first_whole_review_then_metadata_reuse(self):
        self.assertEqual(self.checked(self.q,self.api),DECL)
        self.assertEqual(self.checked(self.q,self.api),DECL)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.counts,dict(original_complete_reviews=1,duplicate_declarations_avoided=1))

    def test_different_reader_requires_complete_review(self):
        self.checked(self.q,self.api);self.checked(Reader(),self.api)
        self.assertEqual(len(self.calls),2)

    def test_changed_api_requires_complete_review(self):
        self.checked(self.q,self.api);self.checked(self.q,object())
        self.assertEqual(len(self.calls),2)

    def test_changed_ledger_requires_complete_review(self):
        self.checked(self.q,self.api);self.q.snapshots[ROOT["path"]]=dict(ROOT,bytes=6)
        self.checked(self.q,self.api);self.assertEqual(len(self.calls),2)

    def test_removed_ledger_requires_complete_review(self):
        self.checked(self.q,self.api);del self.q.snapshots[REVIEW["path"]]
        self.checked(self.q,self.api);self.assertEqual(len(self.calls),2)

    def test_new_input_does_not_replace_old_witness(self):
        self.checked(self.q,self.api);self.q.snapshots["extra"]=dict(ROOT,path="extra")
        self.checked(self.q,self.api);self.assertEqual(len(self.calls),1)

    def test_final_started_forces_original_review(self):
        self.checked(self.q,self.api);self.q.final_fresh_hashes=1
        self.checked(self.q,self.api);self.checked(self.q,self.api)
        self.assertEqual(len(self.calls),3)

    def test_changed_checkpoint_forces_original_review(self):
        self.checked(self.q,self.api);self.q.checkpoint=lambda:None
        self.checked(self.q,self.api);self.assertEqual(len(self.calls),2)

    def test_original_error_identity_and_no_failed_record(self):
        self.error=ValueError("ORIGINAL_STOP")
        with self.assertRaises(ValueError) as caught:self.checked(self.q,self.api)
        self.assertIs(caught.exception,self.error)
        self.error=None;self.checked(self.q,self.api);self.assertEqual(len(self.calls),2)

    def test_cached_path_still_calls_original_resource_guard(self):
        error=ValueError("RESOURCE_STOP");state={"stop":False}
        def checkpoint():
            if state["stop"]:raise error
        self.q.checkpoint=checkpoint;self.checked(self.q,self.api);state["stop"]=True
        with self.assertRaises(ValueError) as caught:self.checked(self.q,self.api)
        self.assertIs(caught.exception,error)
        self.assertEqual(self.counts["duplicate_declarations_avoided"],0)

    def test_returned_metadata_mutation_cannot_change_witness(self):
        result=self.checked(self.q,self.api);result["failed_runtime_pin"]["bytes"]=100
        result["original_failure_promoted"]=True
        self.assertEqual(self.checked(self.q,self.api),DECL)

    def test_runtime_row_payload_is_not_a_declaration(self):
        self.row["source_frame"]={"large_payload":"not retained"}
        with self.assertRaises(ValueError):self.checked(self.q,self.api)

    def test_product_authorization_rejected(self):
        self.row["physical_run002_or_GO_authorized"]=True
        with self.assertRaises(ValueError):self.checked(self.q,self.api)

    def test_other_owner_cannot_reuse_review(self):
        self.checked(self.q,self.api)
        with patch.object(m.threading,"get_ident",return_value=-1):self.checked(self.q,self.api)
        self.assertEqual(len(self.calls),2)

if __name__=="__main__":unittest.main()
