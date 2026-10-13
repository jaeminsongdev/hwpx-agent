"""P234 실제 fresh STOP fixture의 fail-closed 계약. 값/로그를 출력하지 않는다."""
import copy
import unittest
from types import SimpleNamespace
import review_current_queue_stop as p
FIXTURES=None


class StopReviewTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_STOP_FIXTURES_REQUIRED')
        self.root,self.body=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.review(self.root,self.body)
    def test_review_preserves_failure_and_forbids_repeat(self):
        row=p.review(self.root,self.body)
        self.assertFalse(row['runtime_accepted']);self.assertFalse(row['same_product_body_reexecution_allowed'])
        self.assertTrue(row['source_closing_still_required'])
    def test_outer_null_never_masks_nested_cpu_stop(self):
        row=p.review(self.root,self.body)
        self.assertIsNone(row['outer_resource_stop_reason']);self.assertEqual(row['parent_resource_stop_reason'],p.STOP)
    def test_overall_pass_rejected(self):self.root['state']=p.r.PASS;self.reject()
    def test_parent_phase_before_exit_rejected(self):self.body['operation_phase']='running';self.reject()
    def test_wrong_stop_rejected(self):self.body['stop_reason']='STOP_LOW_AVAILABLE_RAM';self.reject()
    def test_bool_or_nonzero_exit_rejected(self):
        for code in (False,1):self.body['exit_code']=code;self.reject()
    def test_wrong_case_rejected(self):self.root['selected_test_index']=79;self.reject()
    def test_wrong_name_rejected(self):self.body['passed_test_names']=['other'];self.reject()
    def test_wrong_filtered_count_rejected(self):self.body['terminal_summary']['filtered_out']=247;self.reject()
    def test_missing_overall_pass_not_fabricated(self):self.body['tests_passed']=1;self.reject()
    def test_partial_capture_rejected(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_truncated_received_bytes_rejected(self):self.body['capture_diagnostics']['received_bytes']['stdout']=257;self.reject()
    def test_missing_go_or_job_cleanup_rejected(self):
        self.body['writer_authorized']=False;self.reject()
        self.body['writer_authorized']=True;self.body['job_final']['active_processes']=1;self.reject()
    def test_source_subset_rejected(self):self.body['source_freeze'].pop();self.reject()
    def test_partial_after_never_full_pass(self):self.body['owned_source_reader_passes'][1]['read_passes']=1512;self.reject()
    def test_pressure_guard_relaxation_rejected(self):
        self.body['owned_source_reader_passes'][1]['near_saturation_read_backpressure']['original_IO_deadline_unmodified']=False;self.reject()
    def test_unclosed_original_or_duplicate_rejected(self):
        handles=self.root['terminal_source_frame']['handles'];handles['input_lock_handles_remaining']=1;self.reject()
        handles['input_lock_handles_remaining']=0;handles['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_bad_sidecar_or_placeholder_link_rejected(self):self.root['terminal_parent_failure_sidecar_pin']['bytes']+=1;self.reject()
    def test_gate_promotion_rejected(self):self.root['P09_gate']='PASS';self.reject()
    def test_single_initial_read_binds_bytes_and_mismatch_rejects(self):
        calls=[];doc={'not_a_log':True};pin=dict(path='fixture.json',bytes=3,sha256='literal')
        def read(name):calls.append(name);return doc
        q=SimpleNamespace(json=read,reader=SimpleNamespace(snapshots={'fixture.json':pin}))
        self.assertIs(p.bound_json(q,pin),doc);self.assertEqual(calls,['fixture.json'])
        with self.assertRaises(ValueError):p.bound_json(q,dict(pin,bytes=4))
