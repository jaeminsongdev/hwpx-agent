import copy
import unittest
import review_native_acquisition_stop as m
FIXTURE=None


class NativeStopTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('FRESH_NATIVE_STOP_REQUIRED')
        self.doc=copy.deepcopy(FIXTURE)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(self.doc)
    def test_preserve_unexecuted_case_and_forbid_auto_retry(self):
        row=m.review(self.doc);self.assertTrue(row['product_body_unexecuted']);self.assertFalse(row['automatic_retry_allowed'])
    def test_failure_not_PASS(self):self.doc['state']=m.r.PASS;self.reject()
    def test_other_stop(self):self.doc['resource_stop_reason']='OTHER';self.reject()
    def test_wrong_next(self):self.doc['selected_test_index']=81;self.reject()
    def test_worker_invoked(self):self.doc['product_worker_invocation_requested']=True;self.reject()
    def test_acquisition_complete(self):self.doc['frame_acquisition_complete']=True;self.reject()
    def test_adapter_created(self):self.doc['uncreated_borrower_adapter_selected']=True;self.reject()
    def test_body_executed(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_body_reference_created(self):self.doc['case_receipt_path']='body';self.reject()
    def test_source_subset(self):self.doc['terminal_source_frame']['input_count']=1524;self.reject()
    def test_byte_boundary_created(self):self.doc['terminal_source_frame']['actual_byte_boundaries']=[{}];self.reject()
    def test_missing_borrower_not_counter_zero(self):self.doc['terminal_source_frame']['handles']['borrowed_byte_streams']={};self.reject()
    def test_unclosed_lock(self):self.doc['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_bool_zero_not_count(self):self.doc['terminal_source_frame']['handles']['active_byte_streams']=False;self.reject()
    def test_registered_frame(self):self.doc['terminal_source_frame']['registered_live_frame']=True;self.reject()
    def test_pressure_removed(self):self.doc['terminal_source_frame']['handles']['native_open_backpressure']['warning_entries']=0;self.reject()
    def test_deadline_relaxed(self):self.doc['terminal_source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_partial_metadata(self):self.doc['preparation_IO']['finished']=False;self.reject()
    def test_missing_Job_CPU_not_zero(self):
        for row in self.doc['metadata_observation']['samples']:row['owned_job_cpu_machine_percent']=0
        self.reject()
    def test_gate_promotion(self):self.doc['P09_gate']='PASS';self.reject()
