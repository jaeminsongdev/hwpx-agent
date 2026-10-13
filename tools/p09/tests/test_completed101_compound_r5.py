"""P300 R5: 명시적인 fake/current STOP/source fixture는 실제 source 수용이 아니다."""
import copy
import unittest
import accept_completed101_compound_r5 as p
FIXTURES=None

class CompoundTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_COMPLETED101_SOURCE_FIXTURES_REQUIRED')
        (self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras,self.legacy,self.base)=copy.deepcopy(FIXTURES)
    def combined(self):return p.combine(self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.combined()
    def test_exact_original_immutable_compound(self):
        before=copy.deepcopy((self.root,self.body,self.source));result=self.combined()
        self.assertTrue(result['compound_individual_case_qualified']);self.assertFalse(result['original_STOP_receipt_accepted'])
        self.assertFalse(result['original_partial_post_hash_completed']);self.assertEqual((self.root,self.body,self.source),before)
    def test_wrong_manifest(self):self.body['binding']['exact_input_manifest_sha256']='a'*64;self.reject()
    def test_wrong_inventory_case(self):self.names[100],self.names[101]=self.names[101],self.names[100];self.reject()
    def test_wrong_parent_phase(self):self.body['operation_phase']='running';self.reject()
    def test_failed_exit(self):self.body['exit_code']=1;self.reject()
    def test_incomplete_capture(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_subset_original_source(self):self.required.popitem();self.reject()
    def test_EXE_drift(self):self.required[self.exe['path']]['sha256']='b'*64;self.reject()
    def test_worker_drift(self):self.required[p.m.p.m.SELF]['sha256']='b'*64;self.reject()
    def test_relaxed_job_cpu(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_relaxed_affinity(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_stopped_independent_source(self):self.source['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_controller_drift(self):self.extras[p.closing.SELF]['sha256']='b'*64;self.reject()
    def test_serialized_not_live_frame(self):self.source['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_unclosed_duplicate(self):self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_original_STOP_not_promoted(self):self.body['state']='PASS_SCOPED_NOT_GATE';self.reject()
    def test_original_tests_passed_not_fabricated(self):self.body['tests_passed']=1;self.reject()
    def test_exact95_next102_no_gate(self):
        plan=p.advance(self.legacy,self.base,self.names)
        self.assertEqual((plan['runtime_source_qualified_individual_cases'],plan['next_runtime_index']),(95,102))
        self.assertFalse(plan['whole1470_current_fresh_qualified']);self.assertFalse(plan['full249_current_qualified'])
    def test_duplicate_acceptance(self):
        self.base['runtime_qualified_test_names'].append(p.review.NAME)
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
    def test_pending_prior_candidate(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
    def test_early_connection_required(self):self.source['early_source_runtime_connection_verified']=False;self.reject()
    def test_no_CPU_resolution_claim(self):
        result=self.combined();self.assertFalse(result['CPU_improvement_or_PC_freeze_solution_established'])

if __name__=='__main__':unittest.main()
