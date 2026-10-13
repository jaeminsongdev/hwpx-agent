"""P264 원 실패/새 source 오수용 및 단일본문 재실행 금지 계약."""
import copy
import unittest
import accept_observation_failure_compound as v
FIXTURES=None


class CompoundTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURES,'exact immutable fixtures required; no skip')
        (self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras,self.legacy,self.base)=copy.deepcopy(FIXTURES)
    def combined(self):return v.combine(self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.combined()
    def test_exact_compound_preserves_inputs(self):
        before=copy.deepcopy((self.root,self.body,self.source));row=self.combined()
        self.assertTrue(row['compound_individual_case_qualified']);self.assertFalse(row['original_failed_root_accepted'])
        self.assertFalse(row['original_incomplete_metadata_promoted']);self.assertEqual((self.root,self.body,self.source),before)
    def test_different_case(self):self.names[90],self.names[91]=self.names[91],self.names[90];self.reject()
    def test_binding(self):self.body['binding']['exact_input_manifest_sha256']='a'*64;self.reject()
    def test_failed_root_not_original_pass(self):self.root['state']=v.old.PASS;self.reject()
    def test_failed_parent_not_pass(self):self.body['state']='STOPPED_NOT_ACCEPTED';self.reject()
    def test_original_scope(self):self.required.popitem();self.reject()
    def test_EXE_drift(self):self.required[self.exe['path']]['sha256']='b'*64;self.reject()
    def test_worker_drift(self):self.required[v.p.m.SELF]['sha256']='b'*64;self.reject()
    def test_relaxed_cpu(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_relaxed_affinity(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_relaxed_process_count(self):self.body['owned_limits_readback']['active_process_limit']=17;self.reject()
    def test_breakaway(self):self.body['owned_limits_readback']['breakaway_disabled']=False;self.reject()
    def test_source_STOP(self):self.source['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_source_subset(self):self.source['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop();self.reject()
    def test_source_uncommitted(self):self.source['source_frame']['frame_state']='CLOSED';self.reject()
    def test_source_duplicate_residue(self):self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_source_controller_drift(self):self.extras[v.closing.SELF]['sha256']='b'*64;self.reject()
    def test_observer_binding_required(self):self.source['aggregate_reader_connection_verified']=False;self.reject()
    def test_no_freeze_claim(self):self.assertFalse(self.combined()['CPU_improvement_or_PC_freeze_solution_established'])
    def test_exact_next92_no_gate(self):
        plan=v.advance(self.legacy,self.base,self.names);self.assertEqual((plan['runtime_source_qualified_individual_cases'],plan['next_runtime_index']),(85,92))
        self.assertFalse(plan['full249_current_qualified']);self.assertEqual(plan['P09_gate'],'OPEN')
    def test_duplicate_case_rejected(self):
        self.base['runtime_qualified_test_names'].append(v.review.NAME)
        with self.assertRaises(ValueError):v.advance(self.legacy,self.base,self.names)
    def test_pending_prior_rejected(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):v.advance(self.legacy,self.base,self.names)
    def test_exact_literal_inventory(self):v.inventory([v.review.ROOT_PIN['path'].split('/')[-1],v.review.LIGHT_PIN['path'].split('/')[-1]],[v.review.BODY_PIN['path'].split('/')[-1]])
    def test_unknown_failure_rejected(self):
        with self.assertRaises(ValueError):v.inventory(['p260-case-091-run099.v1.json'],[])
    def test_retry_body_rejected(self):
        roots=[v.review.ROOT_PIN['path'].split('/')[-1],v.review.LIGHT_PIN['path'].split('/')[-1]]
        with self.assertRaises(ValueError):v.inventory(roots,[v.review.BODY_PIN['path'].split('/')[-1],'p260-case-091-run004.json'])
    def test_missing_literal_rejected(self):
        with self.assertRaises(ValueError):v.inventory([],[])


if __name__=='__main__':unittest.main()
