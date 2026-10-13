"""P236 원 CPU STOP 보존 및 본문 비재실행 결합 계약."""
import copy
import unittest
import accept_current_stop_compound as p
FIXTURES=None


class CompoundTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_COMPOUND_FIXTURES_REQUIRED')
        (self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras,
            self.legacy,self.base)=copy.deepcopy(FIXTURES)
    def combined(self):
        return p.combine(self.root,self.body,self.source,self.names,self.expected,self.exe,self.required,self.extras)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.combined()
    def test_exact_preserved_compound(self):
        before=copy.deepcopy((self.root,self.body,self.source));row=self.combined()
        self.assertTrue(row['compound_individual_case_qualified']);self.assertFalse(row['original_STOP_receipt_accepted'])
        self.assertFalse(row['original_partial_post_hash_completed']);self.assertEqual((self.root,self.body,self.source),before)
    def test_wrong_manifest_binding(self):self.body['binding']['exact_input_manifest_sha256']='a'*64;self.reject()
    def test_wrong_case_in_inventory(self):self.names[77],self.names[78]=self.names[78],self.names[77];self.reject()
    def test_wrong_parent_phase(self):self.body['operation_phase']='running';self.reject()
    def test_failed_body_exit(self):self.body['exit_code']=1;self.reject()
    def test_partial_capture(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_subset_original_source(self):self.required.popitem();self.reject()
    def test_EXE_drift(self):self.required[self.exe['path']]['sha256']='b'*64;self.reject()
    def test_worker_drift(self):self.required[p.r.p.m.SELF]['sha256']='b'*64;self.reject()
    def test_relaxed_job_cpu_cap(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_relaxed_job_affinity(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_stopped_post_source(self):self.source['resource_stop_reason']=p.review.STOP;self.reject()
    def test_controller_drift(self):self.extras[p.closing.SELF]['sha256']='b'*64;self.reject()
    def test_serialized_pin_instead_live_frame(self):self.source['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_duplicate_handle_not_closed(self):self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_original_STOP_not_promoted(self):self.body['state']='PASS_SCOPED_NOT_GATE';self.reject()
    def test_original_overall_tests_pass_not_filled(self):self.body['tests_passed']=1;self.reject()
    def test_next79_and_no_duplicate_acceptance(self):
        plan=p.advance(self.legacy,self.base,self.names)
        self.assertEqual((plan['runtime_source_qualified_individual_cases'],plan['next_runtime_index']),(72,79))
        self.assertFalse(plan['whole1470_current_fresh_qualified']);self.assertFalse(plan['full249_current_qualified'])
    def test_already_accepted_body_rejected(self):
        self.base['runtime_qualified_test_names'].append(p.review.NAME)
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
    def test_pending_candidate_blocks_advance(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):p.advance(self.legacy,self.base,self.names)
