"""P267: 원22 계약 유지 + 진단18/실제 실패의 거부 계약12. 제품/Thread 없음."""
import copy
import io
import json
import unittest
from unittest.mock import patch
import test_deferred_parent_failure as old
import review_rejected_parent_diagnostic as m
FIXTURES=None


class Diagnostic(unittest.TestCase):
    def fresh(self):
        frame=old.Frame();return frame,m.Capture(frame,[],60,old.NAME,old.BINDING)
    def rejected(self,row=None):
        frame,cap=self.fresh();row=old.document() if row is None else row
        row['stop_reason']=row['resource_stop_reason']='STOP_SQL_IO_SCOPE_TIME'
        with self.assertRaisesRegex(ValueError,'EXACT_STOP_NOT_PASS'):
            cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        return frame,cap,row
    def saved(self,frame,cap):
        frame.close();owner,out=old.terminal();stream=io.StringIO()
        cap.write_rejected(stream,owner,out);return json.loads(stream.getvalue())
    def test_unknown_stop_lossless_not_accepted(self):
        frame,cap,row=self.rejected();before=copy.deepcopy(row);saved=self.saved(frame,cap)
        self.assertEqual(saved['original_parent_document'],before);self.assertEqual(row,before)
        self.assertEqual(saved['original_validation_error'],'TERMINAL_FAILURE_EXACT_STOP_NOT_PASS')
        self.assertFalse(saved['runtime_accepted']);self.assertFalse(cap.pending)
    def test_no_live_stream_write_or_copy(self):
        frame,cap=self.fresh();row=old.document();row['stop_reason']='OWNED_RUNNER_FAILURE';stream=io.StringIO()
        with patch('copy.deepcopy',side_effect=AssertionError('NO_LIVE_COPY')),self.assertRaises(ValueError):
            cap.writer(row,stream,ensure_ascii=False,indent=2)
        self.assertIs(cap._rejected,row);self.assertEqual(stream.getvalue(),'')
    def test_no_live_frame_recheck(self):
        frame,cap,row=self.rejected();self.assertEqual(frame.check_calls,0)
        frame.close();self.saved(frame,cap);self.assertEqual(frame.check_calls,0)
    def test_original_CPU_path_unchanged(self):
        frame,cap=self.fresh();row=old.document();cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        self.assertTrue(cap.pending);self.assertFalse(cap.rejected);frame.close();owner,out=old.terminal();stream=io.StringIO()
        cap.write_terminal(stream,owner,out);self.assertEqual(json.loads(stream.getvalue()),row)
    def test_original_PASS_packed_guard(self):
        frame,cap=self.fresh();row={'state':'PASS_SCOPED_NOT_GATE','value':'원본'};stream=io.StringIO()
        cap.writer(row,stream,ensure_ascii=False,indent=2)
        self.assertEqual(old.m.original.packed.unpack(json.loads(stream.getvalue()),lambda:None),row)
        self.assertGreater(frame.check_calls,0);self.assertFalse(cap.rejected)
    def test_broken_PASS_never_diagnostic(self):
        frame,cap=self.fresh();frame.state='BROKEN'
        with self.assertRaises(ValueError):cap.writer({'state':'PASS_SCOPED_NOT_GATE'},io.StringIO(),ensure_ascii=False,indent=2)
        self.assertFalse(cap.rejected)
    def test_foreign_failure_not_retained(self):
        frame,cap=self.fresh();row=old.document();row['task']='foreign'
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        self.assertFalse(cap.rejected)
    def test_wrong_options_not_retained(self):
        frame,cap=self.fresh()
        with self.assertRaises(ValueError):cap.writer(old.document(),io.StringIO(),indent=2)
        self.assertFalse(cap.rejected)
    def test_duplicate_capture_and_write_denied(self):
        frame,cap,row=self.rejected()
        with self.assertRaises(ValueError):cap.writer(row,io.StringIO(),ensure_ascii=False,indent=2)
        self.saved(frame,cap);owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_owner_live_no_write(self):
        frame,cap,row=self.rejected();frame.close();owner,out=old.terminal();owner.done.clear();stream=io.StringIO()
        with self.assertRaises(ValueError):cap.write_rejected(stream,owner,out)
        self.assertEqual(stream.getvalue(),'')
    def test_frame_live_no_write(self):
        frame,cap,row=self.rejected();owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_original_state_reason_mutation_denied(self):
        for key,value in (('state','PASS_SCOPED_NOT_GATE'),('stop_reason','OTHER'),('resource_stop_reason',None),('P09_gate','PASS')):
            frame,cap,row=self.rejected();row[key]=value;frame.close();owner,out=old.terminal()
            with self.subTest(key=key),self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_unknown_cleanup_not_zeroed(self):
        frame,cap,row=self.rejected();row['job_final']=None;row['cleanup_confirmed']=None
        frame.close();owner,out=old.terminal();out.clear();stream=io.StringIO();cap.write_rejected(stream,owner,out)
        saved=json.loads(stream.getvalue());self.assertIsNone(saved['owner_cleanup_confirmed'])
        self.assertIsNone(saved['original_parent_document']['job_final']);self.assertFalse(saved['runtime_accepted'])
    def test_partial_cleanup_preserved_not_qualified(self):
        frame,cap,row=self.rejected();frame.close();snapshot=frame.summary()
        snapshot['handles']['input_lock_handles_remaining']=1;snapshot['handles']['input_lock_cleanup_confirmed']=False
        owner,out=old.terminal();stream=io.StringIO()
        with patch.object(frame,'summary',return_value=snapshot):cap.write_rejected(stream,owner,out)
        saved=json.loads(stream.getvalue());self.assertEqual(saved['original_frame_snapshot'],snapshot)
        self.assertTrue(saved['cleanup_values_retained_not_qualified']);self.assertFalse(saved['runtime_accepted'])
    def test_short_write_no_retry(self):
        class Short:
            def write(self,block):return 0
        frame,cap,row=self.rejected();frame.close();owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_rejected(Short(),owner,out)
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_NaN_no_replacement_or_retry(self):
        frame,cap,row=self.rejected();row['payload'].append(float('nan'));frame.close();owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_fixed_bounded_writer(self):
        frame,cap,row=self.rejected();frame.close();owner,out=old.terminal()
        with patch.object(m,'MAX_BYTES',8),self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)
    def test_identity_mutation_after_capture_denied(self):
        frame,cap,row=self.rejected();row['selected_test_names']=['foreign'];frame.close();owner,out=old.terminal()
        with self.assertRaises(ValueError):cap.write_rejected(io.StringIO(),owner,out)


class FailureReview(unittest.TestCase):
    def fresh(self):
        self.assertIsNotNone(FIXTURES,'ACTUAL_LITERAL_FIXTURES_REQUIRED')
        return copy.deepcopy(FIXTURES)
    def reject(self,change):
        args=list(self.fresh());change(args)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(*args)
    def test_original_review_never_promotes(self):
        args=self.fresh();before=copy.deepcopy(args);row=m.review(*args)
        self.assertEqual(args,before);self.assertFalse(row['semantic_body_PASS_established'])
        self.assertIsNone(row['exact_original_parent_stop_reason']);self.assertIsNone(row['after_hash_completion_count'])
        self.assertFalse(row['original_Job_cleanup_established']);self.assertFalse(row['automatic_retry_allowed'])
    def test_failure_state_not_PASS(self):self.reject(lambda a:a[0].update(state=m.PASS))
    def test_unknown_error_not_whitelisted(self):self.reject(lambda a:a[0].update(error_code='OTHER'))
    def test_outer_CPU_stop_not_original_reason(self):self.reject(lambda a:a[0].update(resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU'))
    def test_zero_placeholder_must_be_exact(self):self.reject(lambda a:a[1].update(bytes=1))
    def test_invented_parent_or_body_proof_denied(self):self.reject(lambda a:a[0].update(terminal_parent_failure_sidecar_pin=m.ZERO))
    def test_prior_plan_not_advanced(self):self.reject(lambda a:a[0]['prior_runtime_plan'].update(runtime_source_qualified_individual_cases=88))
    def test_selected_case_exact(self):self.reject(lambda a:a[0].update(selected_test_index=95))
    def test_before_byte_inventory_not_truncated(self):self.reject(lambda a:a[0]['terminal_source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'].pop())
    def test_after_boundary_never_invented(self):
        self.reject(lambda a:a[0]['terminal_source_frame']['actual_byte_boundaries'].append(
            copy.deepcopy(a[0]['terminal_source_frame']['actual_byte_boundaries'][0])))
    def test_native_cleanup_not_unknown_zero(self):self.reject(lambda a:a[0]['terminal_source_frame']['handles'].update(input_lock_handles_remaining=None))
    def test_original600_and20_not_extended(self):
        self.reject(lambda a:a[0]['terminal_source_frame']['handles'].update(maximum_lock_seconds=1200))
        self.reject(lambda a:a[0]['terminal_source_frame']['handles']['native_open_pacing'].update(maximum_opens_per_second=32))


if __name__=='__main__':unittest.main()
