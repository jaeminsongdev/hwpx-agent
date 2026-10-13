"""P297 exact STOP: 거부조건/불변성만 검사, 재시도 없음."""
import copy
import unittest
import review_completed101_source_stop as p
FIXTURE=None
class Tests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:raise RuntimeError('EXACT_FROZEN_STOP_REQUIRED')
        self.d=copy.deepcopy(FIXTURE)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.review(self.d)
    def test_exact_immutable_review(self):
        before=copy.deepcopy(self.d);r=p.review(self.d)
        self.assertFalse(r['runtime_advance']);self.assertEqual(before,self.d)
    def test_failure_not_pass(self):self.d['state']=p.c.PASS;self.reject()
    def test_wrong_stage(self):self.d['failure_diagnostic']['stage']='final_fresh_hash';self.reject()
    def test_unclosed_handle(self):self.d['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_registered_frame(self):self.d['source_frame']['registered_live_frame']=True;self.reject()
    def test_partial_source_not_full(self):self.d['source_frame']['actual_byte_boundaries']=[{}];self.reject()
    def test_parent_reexecution(self):self.d['actual_product_body_executed']=True;self.reject()
    def test_own_load_not_zeroed(self):self.d['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=1;self.reject()
    def test_read_not_zeroed(self):self.d['metadata_observation']['samples'][-1]['audited_logical_read_bytes_delta']=1;self.reject()
    def test_600_not_extended(self):self.d['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_rate_not_relaxed(self):self.d['source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_watcher_cleanup(self):self.d['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_gate_not_promoted(self):self.d['P09_gate']='PASS';self.reject()
    def test_original_full_scope(self):self.d['original_executed_source_pins'].pop();self.reject()
if __name__=='__main__':unittest.main()
