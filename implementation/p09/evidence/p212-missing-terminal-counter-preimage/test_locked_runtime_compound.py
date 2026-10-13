"""원 source/본문/closing/원장을 보존하는 compound 검증. fresh fixtures 필요."""
import copy
import unittest
import accept_locked_runtime_candidate as a
FIXTURES=None


class CompoundTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_PROOF_FIXTURES_REQUIRED')
        (self.frame,self.body,self.source,self.names,self.expected,self.exe,self.original,self.extras,
            self.legacy,self.base)=copy.deepcopy(FIXTURES)
    def combined(self):return a.combine_evidence(self.frame,self.body,self.source,self.names,
        self.expected,self.exe,self.original,self.extras)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.combined()
    def test_exact_compound_preserves_original_failures(self):
        before=copy.deepcopy((self.frame,self.body,self.source));result=self.combined()
        self.assertTrue(result['compound_individual_case_qualified'])
        self.assertFalse(result['original_STOP_receipt_accepted']);self.assertFalse(result['original_partial_post_hash_completed'])
        self.assertEqual((self.frame,self.body,self.source),before)
    def test_wrong_compiled_manifest_binding_rejected(self):
        self.body['binding']['exact_input_manifest_sha256']='a'*64;self.reject()
    def test_wrong_case_index_name_rejected(self):self.names[11],self.names[12]=self.names[12],self.names[11];self.reject()
    def test_before_exit_or_running_stop_rejected(self):self.body['operation_phase']='running';self.reject()
    def test_nonzero_exit_rejected(self):self.body['exit_code']=1;self.reject()
    def test_capture_partial_rejected(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_original_source_subset_rejected(self):self.original.popitem();self.reject()
    def test_EXE_digest_drift_rejected(self):self.original[self.exe['path']]['sha256']='b'*64;self.reject()
    def test_worker_byte_drift_rejected(self):self.original[a.p.m.SELF]['sha256']='b'*64;self.reject()
    def test_job_affinity_or_cpu_limit_drift_rejected(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_source_frame_partial_or_STOP_rejected(self):self.source['resource_stop_reason']=a.review.STOP;self.reject()
    def test_post_source_controller_drift_rejected(self):self.extras[a.closing.SELF]['sha256']='b'*64;self.reject()
    def test_live_handle_replaced_by_serialized_pin_rejected(self):self.source['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_unreleased_duplicate_or_missing_seek_rejected(self):
        self.source['source_frame']['handles']['borrowed_byte_streams']['shared_offset_resets']=2959;self.reject()
    def test_original_STOP_promoted_rejected(self):self.body['state']='PASS_SCOPED_NOT_GATE';self.reject()
    def test_queue12_next13_no_whole_or_Gate_promotion(self):
        before=copy.deepcopy((self.legacy,self.base));result=a.merge(self.legacy,self.base,self.names,[self.names[11]])
        self.assertEqual((result['runtime_source_qualified_individual_cases'],result['next_runtime_index']),(12,13))
        self.assertEqual(result['all_successful_bodies_pending_whole_reconciliation'],9)
        self.assertFalse(result['whole1470_current_fresh_qualified']);self.assertFalse(result['full249_current_qualified'])
        self.assertEqual((self.legacy,self.base),before)
    def test_duplicate_new_or_existing_qualified_case_rejected(self):
        for names in ([self.names[11],self.names[11]],[self.base['runtime_qualified_test_names'][0]]):
            with self.assertRaises(ValueError):a.merge(self.legacy,self.base,self.names,names)
    def test_unclosed_previous_candidate_blocks_new_queue(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):a.merge(self.legacy,self.base,self.names,[self.names[11]])
