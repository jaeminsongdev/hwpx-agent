"""미생성 borrower를 missing 측정값과 구별. 실제 pre-GO CPU stress 없음."""
import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import deferred_uncreated_borrower_failure as m
import test_deferred_parent_failure as old


def fixture():
    frame=old.Frame();frame.held=SimpleNamespace(borrower=None,closed=True,active_readers=set(),active_streams=0)
    frame.boundaries=[];frame.close();snapshot=frame.summary()
    snapshot.update(actual_byte_boundaries=[])
    snapshot['handles'].update(borrowed_byte_streams=None,input_lock_handles_opened=1826,
        input_lock_handles_closed=1826,byte_stream_identity_checks=0,
        probe_handles_opened=0,probe_handles_closed=0,probe_handles_remaining=0)
    frame.summary=lambda:snapshot
    row=old.document();row.update(state='DEFERRED_NOT_STARTED',heavy_work_started=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,writer_authorized=False)
    row.pop('job_final')
    cap=m.Capture(frame,[],60,old.NAME,old.BINDING)
    return frame,snapshot,row,cap


class UncreatedBorrowerTests(unittest.TestCase):
    def test_explicit_nonexistence_preserves_full_document_and_None(self):
        frame,snapshot,row,cap=fixture();before=copy.deepcopy(row);cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        owner,out=old.terminal();saved=io.StringIO();stats=cap.write_terminal(saved,owner,out)
        self.assertEqual(json.loads(saved.getvalue()),before);self.assertEqual(row,before)
        self.assertIsNone(snapshot['handles']['borrowed_byte_streams']);self.assertNotIn('job_final',row)
        self.assertTrue(stats['uncreated_borrower_witness']['borrower_object_explicitly_not_created'])
        self.assertFalse(stats['runtime_connection_qualified'])
    def test_started_STOP_without_borrower_not_inferred(self):
        frame,snapshot,row,_=fixture();row.update(state='STOPPED_NOT_ACCEPTED')
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
    def test_reader_exists_or_byte_use_rejected(self):
        frame,snapshot,row,_=fixture();frame.readers=[object()]
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
        frame.readers=[];snapshot['handles']['byte_stream_identity_checks']=1
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
    def test_missing_borrower_attribute_not_zero(self):
        frame,snapshot,row,_=fixture();del frame.held.borrower
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
    def test_live_or_unclosed_frame_rejected(self):
        frame,snapshot,row,_=fixture();snapshot['registered_live_frame']=True
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
        snapshot['registered_live_frame']=False;frame.held.closed=False
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
    def test_remaining_lock_or_bool_counter_rejected(self):
        frame,snapshot,row,_=fixture();snapshot['handles']['input_lock_handles_remaining']=1
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
        snapshot['handles']['input_lock_handles_remaining']=False
        with self.assertRaises(ValueError):m.unused_witness(frame,snapshot,row)
    def test_existing_borrower_uses_original_exact_path(self):
        frame=old.Frame();frame.held=SimpleNamespace(borrower=object());frame.close()
        frame.summary=lambda:(_ for _ in ()).throw(AssertionError('REDUNDANT_FRAME_SUMMARY'))
        cap=m.Capture(frame,[],60,old.NAME,old.BINDING)
        row=old.document();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);owner,out=old.terminal()
        with patch.object(m.original.Capture,'write_terminal',return_value={'original_path':True}) as used:
            self.assertEqual(cap.write_terminal(io.StringIO(),owner,out),{'original_path':True});self.assertEqual(used.call_count,1)
    def test_short_write_never_retried(self):
        frame,_,row,cap=fixture();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2);owner,out=old.terminal()
        class Short:
            def write(self,block):return 0
        with self.assertRaises(ValueError):cap.write_terminal(Short(),owner,out)
        with self.assertRaises(ValueError):cap.write_terminal(io.StringIO(),owner,out)
