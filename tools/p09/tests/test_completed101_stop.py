"""P293: 완료본문 후보와 미완료source를 구분하는 명시적 거부조건."""
import copy
import unittest
import review_completed101_stop as m
FIXTURES=None

class ReviewTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_LITERAL101_STOP_FIXTURES_REQUIRED')
        self.root,self.body=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.review(self.root,self.body)
    def test_literal_candidate_not_mutated_or_accepted(self):
        before=copy.deepcopy((self.root,self.body));result=m.review(self.root,self.body)
        self.assertEqual((self.root,self.body),before)
        self.assertFalse(result['runtime_acceptance_changed'])
        self.assertTrue(result['independent_full_source_closing_required'])
        self.assertFalse(result['same_product_body_reexecution_allowed'])
    def test_root_PASS_denied(self):self.root['state']=m.m.PASS;self.reject()
    def test_root_cleanup_missing_denied(self):self.root['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_root_case_not101(self):self.root['selected_test_index']=102;self.reject()
    def test_root_contracts_missing(self):self.root['runtime_contract_executions']=0;self.reject()
    def test_foreign_sidecar(self):self.root['terminal_parent_failure_sidecar_pin']=dict(m.BODY,bytes=0);self.reject()
    def test_body_pin_not_closed_pair(self):self.root['case_receipt_pin']={};self.reject()
    def test_queue_not_advanced(self):self.root['runtime_plan']={};self.reject()
    def test_prior94_not_changed(self):self.root['prior_runtime_plan']['runtime_source_qualified_individual_cases']=95;self.reject()
    def test_partial_body_NOT_PASS(self):self.body['state']='PASS_SCOPED_NOT_GATE';self.reject()
    def test_final_source_phase_required(self):self.body['operation_phase']='running';self.reject()
    def test_max1200_not_extended(self):self.body['maximum_seconds']=1201;self.reject()
    def test_selected_name_matches_passed(self):self.body['passed_test_names']=[];self.reject()
    def test_terminal_one_pass_required(self):self.body['terminal_summary']['passed']=0;self.reject()
    def test_filtered248_required(self):self.body['terminal_summary']['filtered_out']=247;self.reject()
    def test_incomplete_capture_denied(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_actual_child_required(self):self.body['actual_product_child_executed']=False;self.reject()
    def test_job_active_denied(self):self.body['job_final']['active_processes']=1;self.reject()
    def test_job_cleanup_denied(self):self.body['owned_tree_empty']=False;self.reject()
    def test_job_cpu_limit_not_relaxed(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_source_scope_not_reduced(self):self.body['source_freeze'].pop();self.reject()
    def test_post_partial_not_invented_full(self):self.body['owned_source_reader_passes'][1]['read_passes']=1599;self.reject()
    def test_partial_Frame_NOT_COMMITTED(self):self.root['terminal_source_frame']['frame_state']='COMMITTED';self.reject()
    def test_extra_second_boundary_denied(self):
        self.root['terminal_source_frame']['actual_byte_boundaries'].append(copy.deepcopy(self.root['terminal_source_frame']['actual_byte_boundaries'][0]))
        self.reject()
    def test_input_lock_remaining_denied(self):self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_duplicate_remaining_denied(self):self.root['terminal_source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_acquisition14_preserved(self):self.root['terminal_source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_cpu_stop_tail_not_removed(self):self.root['metadata_observation']['samples'][-1]['system_cpu_percent']=0;self.reject()
    def test_semantic_failure_fields_not_removed(self):self.root['terminal_parent_failure_statistics']['semantic_fields_intentionally_removed']=1;self.reject()
    def test_gate_NOT_PASS(self):self.body['P09_gate']='PASS';self.reject()

if __name__=='__main__':unittest.main()
