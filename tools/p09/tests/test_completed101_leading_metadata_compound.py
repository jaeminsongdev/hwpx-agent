"""P302: 실패 결합 준비를 수용/전체 source재실행으로 바꾸지 않는12거부조건."""
import copy
import unittest
import accept_completed101_leading_metadata_compound as p
FIXTURE=None
class Tests(unittest.TestCase):
    def setUp(self):self.d=copy.deepcopy(FIXTURE)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.review_failure(self.d)
    def test_exact_immutable(self):
        before=copy.deepcopy(self.d);r=p.review_failure(self.d);self.assertEqual(self.d,before)
        self.assertFalse(r['failed_compound_accepted']);self.assertFalse(r['product_body_or_full_source_reexecution_allowed'])
    def test_wrong_state(self):self.d['state']=p.PASS;self.reject()
    def test_wrong_phase(self):self.d['failure_diagnostic']['stage']='contract_tests';self.reject()
    def test_wrong_source(self):self.d['separate_source_frame_pin']=dict(p.SOURCE_PIN,bytes=1);self.reject()
    def test_unfinished_cleanup(self):self.d['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_no_body_rerun(self):self.d['actual_new_product_body_executed']=True;self.reject()
    def test_no_source_rerun(self):self.d['additional_full_source_frame_executed']=True;self.reject()
    def test_partial_fresh_not_accept(self):self.d['IO']['finished']=True;self.reject()
    def test_original_contract_count_unknown(self):self.d['compound_contract_tests_passed']=22;self.reject()
    def test_original_plan_not_fabricated(self):self.d['runtime_plan']={};self.reject()
    def test_own_CPU_not_zeroed(self):self.d['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=1;self.reject()
    def test_read_delta_not_zeroed(self):self.d['metadata_observation']['samples'][-1]['audited_logical_read_bytes_delta']=1;self.reject()
if __name__=='__main__':unittest.main()
