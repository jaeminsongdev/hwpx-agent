"""P318: authentic pinned103을 자료로 쓴 합성 거부계약; 제품본문 재실행 없음."""
import copy
import unittest
import review_compact_completed103_anchor as m
FIXTURES=None
class Tests(unittest.TestCase):
 def setUp(self):
  if FIXTURES is None:raise RuntimeError('EXACT_LIVE_FIXTURES_REQUIRED')
  self.f=copy.deepcopy(FIXTURES);self.prior,self.root,self.body,self.names,self.expected,self.legacy,self.current,self.prior_body=self.f
 def validate(self):return m.validate(*self.f)
 def reject(self):
  with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.validate()
 def test_exact_single_advance(self):
  plan,*_=self.validate();self.assertEqual(plan['runtime_source_qualified_individual_cases'],97)
 def test_no_mutation(self):
  before=copy.deepcopy(self.f);self.validate();self.assertEqual(before,self.f)
 def test_failed_checkpoint(self):self.prior['state']='FAILED_NOT_ACCEPTED';self.reject()
 def test_partial_checkpoint(self):self.prior['IO']['finished']=False;self.reject()
 def test_checkpoint_cleanup(self):self.prior['resource_watcher_cleanup_confirmed']=False;self.reject()
 def test_checkpoint_STOP(self):self.prior['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
 def test_untyped_checkpoint(self):self.prior['actual102_typed_compound_recomputed']=False;self.reject()
 def test_checkpoint_code_subset(self):self.prior['current77_Native_source_covered_code_pins'].pop();self.reject()
 def test_code81_subset(self):self.current.popitem();self.reject()
 def test_code81_drift(self):self.current[m.m.SELF]['sha256']='b'*64;self.reject()
 def test_wrong_prior_count(self):self.prior['runtime_plan']['runtime_source_qualified_individual_cases']=97;self.reject()
 def test_wrong_selected(self):self.root['selected_test_index']=102;self.reject()
 def test_body_pin_drift(self):self.root['case_receipt_pin']=dict(m.BODY,bytes=1);self.reject()
 def test_source_subset(self):self.body['source_freeze'].pop();self.reject()
 def test_expected_scope_subset(self):self.expected.popitem();self.reject()
 def test_duplicate_acceptance(self):self.root['prior_runtime_plan']['runtime_qualified_test_names'].append(self.root['selected_test_name']);self.reject()
 def test_locks_remaining(self):self.root['closing_component']['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
 def test_after_byte_incomplete(self):self.body['owned_source_reader_passes'][1]['read_passes']=1;self.reject()
 def test_native_deadline_relaxed(self):self.root['closing_component']['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
 def test_JobCPU_relaxed(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
 def test_original254_checkpoint_missing(self):self.root['contract_checkpoint_statistics']['successful_after_test_checks']-=1;self.reject()
 def test_failed103_root(self):self.root['state']='FAILED_NOT_ACCEPTED';self.reject()
 def test_original103_cleanup_missing(self):self.root['resource_watcher_cleanup_confirmed']=False;self.reject()
 def test_gate_promotion(self):self.root['P09_gate']='PASS';self.reject()
 def test_previous1640_source_changed(self):self.prior_body['source_freeze'][0]['bytes']+=1;self.reject()
 def test_individual_NOT_whole1470(self):
  plan,*_=self.validate();self.assertFalse(plan['whole1470_current_fresh_qualified']);self.assertFalse(plan['full249_current_qualified'])
if __name__=='__main__':unittest.main()
