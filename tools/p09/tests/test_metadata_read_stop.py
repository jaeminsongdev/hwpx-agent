import copy
import unittest
import review_metadata_read_stop as m
FIXTURE=None


class MetadataStopTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('FRESH_METADATA_STOP_REQUIRED')
        self.doc=copy.deepcopy(FIXTURE)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(self.doc)
    def test_exact_stop_not_acceptance(self):self.assertFalse(m.review(self.doc)['automatic_retry_allowed'])
    def test_original_failure_cannot_be_pass(self):self.doc['state']=m.r.PASS;self.reject()
    def test_native_requested(self):self.doc['frame_acquisition_requested']=True;self.reject()
    def test_product_requested(self):self.doc['product_worker_invocation_requested']=True;self.reject()
    def test_selection_not_retroactively_filled(self):self.doc['selected_test_index']=80;self.reject()
    def test_native_snapshot_not_fabricated(self):self.doc['terminal_source_frame']={};self.reject()
    def test_partial_metadata_not_finished(self):self.doc['preparation_IO']['finished']=True;self.reject()
    def test_original_read_not_skipped(self):self.doc['preparation_IO']['all_original_read_operations_preserved']=False;self.reject()
    def test_original_io_limit_not_extended(self):self.doc['preparation_IO']['maximum_scope_seconds']=601;self.reject()
    def test_cleanup_required(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_missing_job_cannot_be_measured_zero(self):
        for row in self.doc['metadata_observation']['samples']:row['owned_job_cpu_machine_percent']=0
        self.reject()
    def test_gate_cannot_advance(self):self.doc['P09_gate']='PASS';self.reject()
