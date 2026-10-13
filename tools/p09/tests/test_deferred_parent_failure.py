"""원 P208 함수와 합성 STOP caller 계약. 실제 EXE/Job/입력 frame 획득 없음."""
import copy
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import deferred_parent_failure as m

NAME='actual_import::formula_policy_issuer::provision::provision_approval_write_and_postcommit_failures_preserve_exact_outcome_without_retry'
BINDING={'synthetic':'connection-only'}


class Frame:
    def __init__(self):self.state='HELD';self.readers=[];self.check_calls=0
    def check(self):
        self.check_calls+=1
        if self.state=='BROKEN':raise ValueError('P206_LOCK_P208_FRAME_LIVE_STATE')
    def close(self):self.state='CLOSED';return True
    def summary(self):
        return dict(frame_state=self.state,registered_live_frame=self.state!='CLOSED',handles=dict(
            input_lock_cleanup_confirmed=True,input_lock_handles_remaining=0,active_byte_streams=0,
            active_reader_bindings=0,handle_close_failed_attempts=0,
            borrowed_byte_streams=dict(duplicate_handles_remaining=0,duplicate_close_failed_attempts=0)))


def document():
    return dict(**m.original.p.r.flags(),state='STOPPED_NOT_ACCEPTED',stop_reason=m.failure.STOP,
        resource_stop_reason=m.failure.STOP,cleanup_confirmed=True,owned_tree_empty=True,
        job_final=dict(active_processes=0,owned_processes=[]),schema_version=m.original.p.SCHEMA,
        selected_test_names=[NAME],binding=BINDING,test_arguments=m.original.p.v.arguments(NAME),
        task='p204-r07-case-060-tests',payload=['한글',{'partial_source':True}],tests_passed=None)


def terminal():
    done=threading.Event();done.set()
    return SimpleNamespace(done=done,reason=None),dict(resource_watcher_cleanup_confirmed=True)


class Deferred(unittest.TestCase):
    def fresh(self):
        frame=Frame();return frame,m.Capture(frame,[],60,NAME,BINDING)
    def test_defer_has_no_live_check_or_write(self):
        frame,cap=self.fresh();frame.state='BROKEN';stream=io.StringIO()
        cap.writer(document(),stream,ensure_ascii=False,indent=2)
        self.assertEqual(frame.check_calls,0);self.assertEqual(stream.getvalue(),'');self.assertTrue(cap.pending)
    def test_original_writer_reproduces_zero_body_bug(self):
        frame,_=self.fresh();frame.state='BROKEN';stream=io.StringIO()
        with self.assertRaisesRegex(ValueError,'FRAME_LIVE_STATE'):
            m.original.parent_writer(frame,[])(document(),stream,ensure_ascii=False,indent=2)
        self.assertEqual(stream.getvalue(),'')
    def test_terminal_full_values_and_no_mutation(self):
        frame,cap=self.fresh();row=document();old=copy.deepcopy(row)
        cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);frame.close();owner,out=terminal();stream=io.StringIO()
        cap.write_terminal(stream,owner,out);self.assertEqual(json.loads(stream.getvalue()),old);self.assertEqual(row,old)
    def test_parent_job_not_closed_denied(self):
        _,cap=self.fresh();row=document();row['job_final']['active_processes']=1
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_foreign_parent_denied(self):
        _,cap=self.fresh();row=document();row['task']='p204-r07-case-061-tests'
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_unknown_stop_denied(self):
        _,cap=self.fresh();row=document();row['stop_reason']='OTHER'
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_original_options_only(self):
        _,cap=self.fresh()
        with self.assertRaises(ValueError):cap.writer(document(),io.StringIO(),indent=2)
    def test_duplicate_capture_denied(self):
        _,cap=self.fresh();cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2)
        with self.assertRaises(ValueError):cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2)
    def test_duplicate_pass_denied(self):
        _,cap=self.fresh();cap.writer({'state':'PASS_SCOPED_NOT_GATE'},io.StringIO(),ensure_ascii=False,indent=2)
        with self.assertRaises(ValueError):cap.writer({'state':'PASS_SCOPED_NOT_GATE'},io.StringIO(),ensure_ascii=False,indent=2)
    def test_identity_changed_before_terminal_denied(self):
        frame,cap=self.fresh();row=document();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        row['selected_test_names']=['other'];owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_owner_alive_denied(self):
        frame,cap=self.fresh();cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        owner,out=terminal();owner.done.clear()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_frame_broken_denied_after_capture(self):
        frame,cap=self.fresh();cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2);frame.state='BROKEN'
        owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_remaining_duplicate_denied(self):
        frame,cap=self.fresh();cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        snapshot=frame.summary();snapshot['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1
        owner,out=terminal()
        with patch.object(frame,'summary',return_value=snapshot),self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_document_changed_after_capture_denied(self):
        frame,cap=self.fresh();row=document();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        row['state']='PASS_SCOPED_NOT_GATE';owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_sidecar_failure_no_retry(self):
        class Short:
            def write(self,block):return 0
        frame,cap=self.fresh();cap.writer(document(),io.StringIO(),ensure_ascii=False,indent=2);frame.close();owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(Short(),owner,out)
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_pass_still_original_frame_guard(self):
        frame,cap=self.fresh();stream=io.StringIO();row={'state':'PASS_SCOPED_NOT_GATE','value':'원문'}
        cap.writer(row,stream,ensure_ascii=False,indent=2)
        self.assertEqual(m.original.packed.unpack(json.loads(stream.getvalue()),lambda:None),row)
        self.assertGreater(frame.check_calls,0);self.assertFalse(cap.pending)
    def test_pass_cannot_use_broken_frame(self):
        frame,cap=self.fresh();frame.state='BROKEN'
        with self.assertRaises(ValueError):cap.writer({'state':'PASS_SCOPED_NOT_GATE'},io.StringIO(),ensure_ascii=False,indent=2)
    def test_gate_promotion_denied_at_terminal(self):
        frame,cap=self.fresh();row=document();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        row['P09_gate']='PASS';owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_no_capture_no_terminal_write(self):
        frame,cap=self.fresh();frame.close();owner,out=terminal()
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
    def test_deferred_parent_state_not_reclassified(self):
        frame,cap=self.fresh();row=document();row.update(state='DEFERRED_NOT_STARTED',heavy_work_started=False,
            actual_product_child_executed=False,worker_created=False,job_assigned=False,writer_authorized=False)
        row.pop('job_final');cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);frame.close()
        owner,out=terminal();stream=io.StringIO();cap.write_terminal(stream,owner,out)
        self.assertEqual(json.loads(stream.getvalue()),row)
    def test_deferred_parent_must_not_have_executed_product(self):
        _,cap=self.fresh();row=document();row.update(state='DEFERRED_NOT_STARTED',heavy_work_started=False,
            actual_product_child_executed=True)
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
    def test_original_parent_call_path_stop_connection(self):
        frame,cap=self.fresh();empty=io.StringIO();context=m.original.g.observation.Context()
        def stopped_run(task,destination,seconds):
            self.assertEqual(task,'p204-r07-case-060-tests');self.assertEqual(seconds,1200)
            row=document();frame.state='BROKEN';json.dump(row,empty,ensure_ascii=False,indent=2);return 2
        with patch.object(m.original.p,'ORIGINAL_RUN',stopped_run),patch.object(m.original.p,'RAW_DUMP',cap.writer):
            code=m.original.p.run_parent(frame,60,NAME,None,context,BINDING)
        self.assertEqual(code,2);self.assertEqual(empty.getvalue(),'');frame.close();owner,out=terminal();stream=io.StringIO()
        cap.write_terminal(stream,owner,out);saved=json.loads(stream.getvalue())
        self.assertEqual(saved['state'],'STOPPED_NOT_ACCEPTED');self.assertEqual(saved['capture']['error_code'],'NO_CAPTURE')
        self.assertEqual(saved['passed_test_names'],[])


if __name__=='__main__':unittest.main()
