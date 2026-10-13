"""P293: 완료본문 후보와 미완료source를 구분하는 명시적 거부조건."""
import copy
import unittest
import complete_preserved106_source as m
FIXTURES=None

class ReviewTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_LITERAL101_STOP_FIXTURES_REQUIRED')
        self.root,self.body=copy.deepcopy(FIXTURES[:2])
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
    def test_root_case_not106(self):self.root['selected_test_index']=107;self.reject()
    def test_root_contracts_missing(self):self.root['runtime_contract_executions']=0;self.reject()
    def test_foreign_sidecar(self):self.root['terminal_parent_failure_sidecar_pin']=dict(m.BODY,bytes=0);self.reject()
    def test_body_pin_not_closed_pair(self):self.root['case_receipt_pin']={};self.reject()
    def test_queue_not_advanced(self):self.root['runtime_plan']={};self.reject()
    def test_prior94_not_changed(self):self.root['prior_runtime_plan']['runtime_source_qualified_individual_cases']=100;self.reject()
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
    def test_post_partial_not_invented_full(self):self.body['owned_source_reader_passes'][1]['read_passes']=1654;self.reject()
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


def source_fixture():
    root,body,original,required,latest=copy.deepcopy(FIXTURES)
    frame=latest['terminal_source_frame'];h=frame['handles'];du=h['borrowed_byte_streams']
    n=len(required);oldn=len(original);total=sum(v['bytes'] for v in required.values());delta=total-sum(v['bytes'] for v in original.values())
    frame.update(input_count=n,input_bytes=total)
    for row in frame['actual_byte_boundaries']:
        row['actual_byte_pins']=copy.deepcopy(list(required.values()))
        diag=row['reader_diagnostics'];diag.update(read_passes=n,bytes_read=total);diag['bytes_read_by_kind']['other']+=delta
    frame['held_identity_after_owned_cleanup']['regular_file_count']=n
    h.update(input_lock_handles_opened=n+m.DIRECTORIES,input_lock_handles_closed=n+m.DIRECTORIES,
        byte_stream_identity_checks=2*n,handle_metadata_checks=4*n+2*m.DIRECTORIES)
    h['native_open_pacing']['open_reservations']=3*n+m.DIRECTORIES
    h['acquisition_phase_pressure']['acquisition_reservations']=n+m.DIRECTORIES
    for key in ('duplicate_handles_opened','duplicate_handles_closed','shared_offset_resets'):du[key]=2*n
    events=h['lock_timing_diagnostic']['explicit_phase_events']
    h['lock_timing_diagnostic']['explicit_phase_events']=[events[0],events[1],events[-1]]
    return dict(schema_version=m.SCHEMA,state=m.SOURCE_PASS,**m.m.p.r.flags(),
        original_root_pin=m.ROOT,original_parent_pin=m.BODY,original_zero_pin=m.ZERO,
        successful_body_reexecution_allowed=False,actual_source_frame_executed=True,
        contract_tests_passed=0,contracts_checkpoint_statistics=None,qualified_contract_tests=m.COUNT,
        reused_review_contract_executions=m.COUNT,
        qualified_review_contract_statistics=dict(started_tests=m.COUNT,stopped_tests=m.COUNT,
            successful_before_test_checks=m.COUNT,successful_after_test_checks=m.COUNT),
        review_pin=dict(path=m.m.p.DIR+'/p338-review-run003.v1.json',bytes=1,sha256='a'*64),source_frame_qualified=True,
        IO=dict(finished=True,bound_inputs=100,final_fresh_hashes=100),
        resource_watcher_cleanup_confirmed=True,resource_stop_reason=None,source_budget=m.budget(required),
        extended_source_pins=copy.deepcopy(list(required.values())),source_frame=frame,
        early_source_checkpoint=copy.deepcopy(latest['early_source_checkpoint']),
        early_source_native_and_byte_guard_connected=True,early_source_runtime_connection_verified=True)

class SourceTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_COMPLETED106_FIXTURES_REQUIRED')
        self.required=copy.deepcopy(FIXTURES[3]);self.doc=source_fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.validate_source(self.doc,self.required)
    def test_explicit_synthetic_source_validator_only(self):m.validate_source(self.doc,self.required)
    def test_scope_cannot_omit_support_code(self):self.required.pop(m.SELF);self.reject()
    def test_scope_cannot_omit_old_file(self):self.required.pop(next(iter(FIXTURES[2])));self.reject()
    def test_source_frame_NOT_partial_commit(self):self.doc['source_frame']['frame_state']='CLOSED';self.reject()
    def test_source_needs_two_boundaries(self):self.doc['source_frame']['actual_byte_boundaries'].pop();self.reject()
    def test_source_partial_byte_pins_denied(self):self.doc['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop();self.reject()
    def test_source_old_byte_accounting_not_reused(self):self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['bytes_read']-=1;self.reject()
    def test_source_old_input_accounting_not_reused(self):self.doc['source_frame']['actual_byte_boundaries'][0]['reader_diagnostics']['read_passes']-=1;self.reject()
    def test_source_pacing_not_loosened(self):self.doc['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=100;self.reject()
    def test_source_deadline_not_extended(self):self.doc['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_source_lock_leak_denied(self):self.doc['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_source_duplicate_leak_denied(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_source_registry_must_be_empty(self):self.doc['source_frame']['registered_live_frame']=True;self.reject()
    def test_source_original_identity_check_retained(self):self.doc['source_frame']['held_identity_after_owned_cleanup']['regular_file_count']-=1;self.reject()
    def test_source_partial_old_identity_not_reused(self):self.doc['source_frame']['handles']['byte_stream_identity_checks']-=1;self.reject()
    def test_source_completed_Job_cleanup_required(self):self.doc['source_frame']['original_owned_cleanup_confirmed_before_release']=False;self.reject()
    def test_source_product_reexecution_forbidden(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_source_fixture_cannot_claim_freeze_solution(self):self.doc['PC_freeze_resolved']=True;self.reject()
    def test_source_full_reader_fresh_required(self):self.doc['IO']['finished']=False;self.reject()
    def test_source_no_serialized_live_handle(self):self.doc['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_source_boundaries_do_not_fake_parent_events(self):
        self.doc['source_frame']['handles']['lock_timing_diagnostic']['explicit_phase_events'][1]['label']='after_parent'
        self.reject()
    def test_source_no_CPU_deadline_relaxation(self):
        self.doc['source_frame']['handles']['lock_timing_diagnostic']['original_resource_guard_or_deadline_extended']=True
        self.reject()
    def test_source_no_scope_exclusion(self):self.doc['source_frame']['input_exclusions_added']=True;self.reject()
    def test_source_no_new_sampler(self):
        self.doc['source_frame']['handles']['native_open_backpressure']['original_sampler_windows_reused']=False
        self.reject()

    def test_source_reused_tests_cannot_be_claimed_new(self):self.doc['contract_tests_passed']=m.COUNT;self.reject()
    def test_source_reuse_requires_exact_review_count(self):self.doc['reused_review_contract_executions']=0;self.reject()
    def test_source_reuse_needs_review_pin(self):self.doc.pop('review_pin');self.reject()
    def test_source_reuse_does_not_fabricate_current_checkpoints(self):self.doc['contracts_checkpoint_statistics']={};self.reject()
    def test_native_attempt_marker_does_not_claim_completion(self):
        out=dict(actual_source_frame_executed=False,source_frame_qualified=True)
        m.mark_native_attempt(out)
        self.assertTrue(out['actual_source_frame_executed']);self.assertFalse(out['source_frame_qualified'])
    def test_code_reuses_only_current_Reader_bindings_not_old_global(self):
        q=unittest.mock.Mock()
        q.pin.side_effect=[{'path':m.SELF},{'path':m.TEST}]
        with unittest.mock.patch.object(m.m,'current_code',return_value=copy.deepcopy(m.CODE91)):
            codes=m.code(q)
        self.assertEqual(codes[:91],m.CODE91)
        self.assertEqual(q.pin.call_args_list,[unittest.mock.call(m.SELF),unittest.mock.call(m.TEST)])
    def test_same_Reader_code_drift_denies_before_source(self):
        q=unittest.mock.Mock();wrong=copy.deepcopy(m.CODE91);wrong[0]['bytes']+=1
        with unittest.mock.patch.object(m.m,'current_code',return_value=wrong):
            with self.assertRaises(ValueError):m.code(q)
        q.pin.assert_not_called()

if __name__=='__main__':unittest.main()
