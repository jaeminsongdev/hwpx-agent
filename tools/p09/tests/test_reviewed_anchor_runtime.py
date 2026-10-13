"""P291 현재/다음1599 synthetic104. 원82 거부조건과 부분 anchor 실패20/연결2."""
import copy
import unittest
import resume_reviewed_anchor_runtime as m
import test_no_work_deferral_runtime as retained

STOP_FIXTURE=None

class QueueTests(retained.QueueTests):
    def test_partial_anchor_stop_pin_not_foreign(self):
        self.doc['reviewed_partial_anchor_STOP_pin']=dict(m.PARTIAL_ANCHOR_STOP,bytes=0)
        self.reject()
    def test_partial_anchor_stop_not_accepted_or_unreviewed(self):
        self.doc['reviewed_partial_anchor_STOP_preserved_not_accepted']=False
        self.reject()

class DeferralTests(retained.DeferralTests):
    def setUp(self):
        super().setUp()
        self.doc['schema_version']=m.SCHEMA
        self.doc['reviewed_partial_anchor_STOP_preserved_not_accepted']=False
    def review(self):
        return m.deferred_admission_review(self.doc,m.SCHEMA)

class PartialStopTests(unittest.TestCase):
    def setUp(self):
        if STOP_FIXTURE is None:raise RuntimeError('BYTE_BOUND_PARTIAL_STOP_FIXTURE_REQUIRED')
        self.doc=copy.deepcopy(STOP_FIXTURE)
    def review(self):return m.partial_anchor_stop_review(self.doc)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.review()
    def test_exact_failed_review_does_not_mutate_or_accept(self):
        before=copy.deepcopy(self.doc);r=self.review()
        self.assertEqual(self.doc,before)
        self.assertFalse(r['accepted_queue_advanced'])
        self.assertEqual(r['accepted_product_body_count'],0)
        self.assertTrue(r['partial_IO_is_not_admission_only_no_work'])
    def test_PASS_not_original_failed(self):self.doc['state']=m.previous.PASS;self.reject()
    def test_foreign_schema_not_reviewed(self):self.doc['schema_version']=m.SCHEMA;self.reject()
    def test_later_stage_not_anchor(self):self.doc['failure_diagnostic']['stage']='owned_parent';self.reject()
    def test_cleanup_unconfirmed_not_reviewed(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_product_started_not_reviewed(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_failed_acceptance_not_advanced(self):self.doc['accepted_exact_product_body_count']=1;self.reject()
    def test_selected_case_not_preselection(self):self.doc['selected_test_index']=101;self.reject()
    def test_contracts_started_not_preselection(self):self.doc['runtime_contract_executions']=1486;self.reject()
    def test_runtime_queue_not_invented(self):self.doc['runtime_plan']={};self.reject()
    def test_Frame_not_preselection(self):self.doc['terminal_source_frame']={};self.reject()
    def test_body_pin_not_preselection(self):self.doc['case_receipt_pin']={};self.reject()
    def test_partial_fresh_not_finished(self):self.doc['preparation_IO']['finished']=True;self.reject()
    def test_entry_not_restored_denied(self):self.doc['preparation_IO']['metadata_read_entry_pacing']['binding_active']=True;self.reject()
    def test_original_four98_tail_not_replaced(self):self.doc['metadata_observation']['samples'][-1]['system_cpu_percent']=97;self.reject()
    def test_own_hot_tail_not_invented_idle(self):self.doc['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=1;self.reject()
    def test_sample_count_not_dropped(self):self.doc['metadata_observation']['completed_sample_count']=42;self.reject()
    def test_partial_fresh_not_invented_complete(self):self.doc['preparation_IO']['final_fresh_hashes']=151;self.reject()
    def test_entry_shared_callback_not_missing(self):
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']['entry_and_byte_share_existing_early_object']=False
        self.reject()
    def test_gate_not_promoted(self):self.doc['P09_gate']='PASS';self.reject()

if __name__=='__main__':
    unittest.main()
