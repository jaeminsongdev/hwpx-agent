"""fresh 원 중단 receipt의 fail-closed 검토. 독립 runtime 승격 불가."""
import copy
import unittest
import review_post_stop_frame as p
FIXTURES=None


class ReviewTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_RECEIPT_FIXTURES_REQUIRED')
        self.frame,self.body=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.review(self.frame,self.body)
    def test_valid_candidate_is_not_accepted_or_reexecuted(self):
        result=p.review(self.frame,self.body)
        self.assertFalse(result['runtime_accepted']);self.assertFalse(result['same_product_body_reexecution_allowed'])
        self.assertTrue(result['source_closing_still_required'])
    def test_stop_before_body_completion_rejected(self):self.body['operation_phase']='running';self.reject()
    def test_nonzero_or_bool_exit_rejected(self):
        for code in (1,False):self.body['exit_code']=code;self.reject()
    def test_wrong_test_name_rejected(self):self.body['passed_test_names']=['different'];self.reject()
    def test_wrong_filtered_summary_rejected(self):self.body['terminal_summary']['filtered_out']=247;self.reject()
    def test_partial_capture_rejected(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_nonempty_stderr_or_truncated_buffers_rejected(self):
        self.body['capture_diagnostics']['buffered_bytes']['stderr']=1;self.reject()
    def test_job_cleanup_or_go_absent_rejected(self):
        self.body['writer_authorized']=False;self.reject()
    def test_before_source_subset_rejected(self):self.body['source_freeze'].pop();self.reject()
    def test_partial_post_hash_not_full_pass_rejected(self):self.body['owned_source_reader_passes'][1]['read_passes']=1473;self.reject()
    def test_unclosed_source_handle_rejected(self):self.frame['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_failure_or_gate_status_reclassification_rejected(self):
        self.frame['state']='PASS_SCOPED_NOT_GATE';self.reject()
