import copy
import unittest
import run_borrowed_runtime_r07_case as r
FIXTURES=None


class BorrowedRuntimeTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_COMPOUND_FIXTURES_REQUIRED')
        self.doc,self.names,self.expected,self.exe=copy.deepcopy(FIXTURES)
    def plan(self):return r.prior_scope(self.doc,self.names,self.expected,self.exe)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):self.plan()
    def test_sealed_compound_selects13_without_repeating12(self):
        self.assertEqual(r.select(self.plan(),self.names),(13,self.names[12]))
    def test_original_compound_not_pass_rejected(self):self.doc['state']='FAILED_NOT_ACCEPTED';self.reject()
    def test_wrong_compiled_binding_rejected(self):self.doc['binding']['exact_input_manifest_sha256']='b'*64;self.reject()
    def test_source_frame_receipt_substitution_rejected(self):
        self.doc['separate_source_frame_pin']=dict(self.doc['separate_source_frame_pin'],sha256='b'*64);self.reject()
    def test_nonfresh_compound_IO_rejected(self):self.doc['IO']['finished']=False;self.reject()
    def test_tampered_queue_count_rejected(self):self.doc['runtime_plan']['runtime_source_qualified_individual_cases']=13;self.reject()
    def test_original_partial_hash_reclassification_rejected(self):self.doc['compound']['original_partial_post_hash_completed']=True;self.reject()
    def test_full_or_gate_promotion_rejected(self):self.doc['full249_current_qualified']=True;self.reject()
    def test_stop_never_selects_next_body(self):self.doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_passed_case12_selection_rejected(self):
        plan=self.plan();plan['next_runtime_index']=12
        with self.assertRaises(ValueError):r.select(plan,self.names)
    def test_pending_success_blocks_body_selection(self):
        plan=self.plan();plan['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):r.select(plan,self.names)
    def test_unsupported_corpus_selection_rejected(self):
        plan=self.plan();self.names[12]=r.p.v.CORPUS_PREFIX+'mock'
        with self.assertRaises(ValueError):r.select(plan,self.names)
