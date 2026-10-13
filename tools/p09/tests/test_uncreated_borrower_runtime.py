"""P241 원 P208 호출 seam의 합성 pre-GO STOP 연결. 실제 Native/Job/CPU stress 없음."""
import copy
import io
import json
import unittest
from unittest.mock import patch
import resume_uncreated_borrower_runtime as m
import test_uncreated_borrower_failure as fixtures
import test_deferred_parent_failure as old


def prepared():
    frame,snapshot,row,_=fixtures.fixture()
    cap=m.capture_for(frame,[],60,old.NAME,old.BINDING)
    return frame,snapshot,row,cap


class RuntimeConnectionTests(unittest.TestCase):
    def test_original_parent_seam_and_complete_none_sidecar(self):
        frame,snapshot,row,cap=prepared();frame.state='HELD';placeholder=io.StringIO();calls=[]
        before=copy.deepcopy(row)
        def stopped(task,path,maximum):
            self.assertEqual(task,'p204-r07-case-060-tests');self.assertEqual(maximum,1200)
            calls.append(task);frame.state='BROKEN';json.dump(row,placeholder,ensure_ascii=False,indent=2);return 2
        with patch.object(m.p,'ORIGINAL_RUN',stopped),patch.object(m.p,'RAW_DUMP',cap.writer):
            code=m.p.run_parent(frame,60,old.NAME,None,m.g.observation.Context(),old.BINDING)
        self.assertEqual(code,2);self.assertEqual(len(calls),1)
        self.assertEqual(placeholder.getvalue(),'');self.assertTrue(cap.pending)
        frame.close();owner,out=old.terminal();saved=io.StringIO();stats=cap.write_terminal(saved,owner,out)
        result=json.loads(saved.getvalue());self.assertEqual(result,row)
        self.assertEqual(result['state'],before['state']);self.assertNotIn('job_final',result)
        self.assertIsNone(snapshot['handles']['borrowed_byte_streams'])
        self.assertFalse(result['actual_product_child_executed']);self.assertFalse(stats['runtime_accepted'])
    def test_capture_selects_qualified_new_type(self):
        _,_,_,cap=prepared();self.assertIs(type(cap),m.candidate.Capture)
    def test_no_terminal_write_while_original_owner_alive(self):
        _,_,row,cap=prepared();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        owner,out=old.terminal();owner.done.clear()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_deferred_cannot_claim_actual_body(self):
        _,_,row,cap=prepared();row['actual_product_child_executed']=True
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_missing_job_after_setup_not_empty_job(self):
        _,_,row,cap=prepared();row['worker_created']=True
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_registered_frame_prevents_terminal_write(self):
        _,snapshot,row,cap=prepared();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        snapshot['registered_live_frame']=True;owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_any_byte_reader_use_prevents_uncreated_witness(self):
        frame,_,row,cap=prepared();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        frame.readers=[object()];owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_normal_pass_preserves_original_guarded_writer(self):
        _,_,_,cap=prepared();stream=io.StringIO();calls=[]
        cap._pass_writer=lambda document,output,**kw:calls.append((document,output,kw))
        row={'state':'PASS_SCOPED_NOT_GATE'};cap.writer(row,stream,ensure_ascii=False,indent=2)
        self.assertEqual(calls,[(row,stream,dict(ensure_ascii=False,indent=2))]);self.assertFalse(cap.pending)
