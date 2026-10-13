import copy
import unittest
import close_borrowed_runtime_pair as x
FIXTURES=None


class PairTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_PAIR_FIXTURES_REQUIRED')
        self.rows=copy.deepcopy(FIXTURES)
        self.source,self.body,self.prior,self.names,self.expected,self.exe,self.required,self.extras=self.rows
    def qualify(self):return x.qualify(*self.rows)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):self.qualify()
    def test_independent_pair13_next14_does_not_reclassify_original(self):
        before=copy.deepcopy(self.rows);plan=self.qualify()
        self.assertEqual((plan['runtime_source_qualified_individual_cases'],plan['next_runtime_index']),(13,14))
        self.assertEqual(self.rows,before);self.assertIn('error_code',self.source)
    def test_original_root_error_not_silently_cleared(self):self.source.pop('error_code');self.reject()
    def test_original_runtime_queue_not_fabricated(self):self.source['runtime_plan']={};self.reject()
    def test_nonzero_parent_exit_rejected(self):self.body['exit_code']=1;self.reject()
    def test_partial_parent_capture_rejected(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_parent_stop_not_valid_pair(self):self.body['stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_wrong_body_receipt_pin_rejected(self):
        self.source['case_receipt_pin']=dict(self.source['case_receipt_pin'],sha256='b'*64);self.reject()
    def test_wrong_body_case_name_rejected(self):self.body['selected_test_names']=[self.names[11]];self.reject()
    def test_full_source_scope_subset_rejected(self):self.required.popitem();self.reject()
    def test_missing_after_actual_byte_read_rejected(self):
        self.source['source_frame']['actual_byte_boundaries'].pop();self.reject()
    def test_unreleased_duplicate_rejected(self):
        self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_resource_stop_rejected(self):self.source['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_current_controller_byte_drift_rejected(self):self.extras[x.runner.SELF]['sha256']='b'*64;self.reject()
    def test_whole_or_Gate_promotion_rejected(self):self.source['whole1470_current_fresh_qualified']=True;self.reject()
