"""P295 synthetic27: 실제 Native/byte 수용 증거가 아닌 validator 거부조건."""
import copy
import unittest
from types import SimpleNamespace
import close_completed101_source_frame_r3 as p

def fixture():
    n=p.N;exe=p.m.p.m.EXE
    original={f'fixture/{i}.rs':dict(path=f'fixture/{i}.rs',bytes=1,sha256='a'*64) for i in range(1598)}
    original[exe['path']]=dict(exe)
    original['fixture/0.rs']['bytes']+=119993724-sum(x['bytes'] for x in original.values())
    extras={name:dict(path=name,bytes=1,sha256='b'*64) for name in p.EXTRAS}
    extras.update({x['path']:dict(x) for x in p.OLD_CODE})
    required={**original,**extras};total=sum(x['bytes'] for x in required.values())
    diagnostic=dict(read_passes=n,bytes_read=total,read_rates_by_kind=dict(binary=1048576,other=2097152),
        original_owned_read_operations_preserved=True,extra_sampler_or_native_query_started=False)
    h=dict(input_lock_handles_opened=n+p.DIRECTORIES,input_lock_handles_closed=n+p.DIRECTORIES,input_lock_handles_remaining=0,
        active_reader_bindings=0,active_byte_streams=0,input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,
        probe_handles_opened=0,probe_handles_closed=0,probe_handles_remaining=0,byte_stream_identity_checks=2*n,
        separate_pathname_reopens=0,maximum_lock_seconds=600,ancestor_walk_steps=p.DIRECTORIES-1,handle_metadata_checks=4*n+2*p.DIRECTORIES,
        native_open_pacing=dict(maximum_opens_per_second=20,open_reservations=3*n+p.DIRECTORIES),file_write_or_delete_operation_executed=False,
        borrowed_byte_streams=dict(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n,
            duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,active_borrow_binding=False,
            byte_stream_pathname_reopens=0,original_pre_read_stream_identity_check_retained=True,
            original_held_handles_closed_by_borrower=False),
        native_open_backpressure=dict(original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
            original_sampler_windows_reused=True,cleanup_not_guarded_by_pressure=True,original_read_checks_skipped=False),
        acquisition_phase_pressure=dict(acquisition_maximum_reservations_per_second=14,original_global_and_byte_reservation_ceiling_per_second=20,
            restored_original_rate=20,acquisition_used=True,acquisition_complete=True,acquisition_reservations=n+p.DIRECTORIES,
            same_original_pacer=True,clock_and_sleeper_and_checkpoint_retained=True,original_CPU_RAM600_and_all_byte_identity_guards_preserved=True,
            clock_previous_credit_or_reservation_counter_reset=False,extra_sampler_or_thread_started=False,cleanup_callback_wrapped=False,
            CPU_or_PC_freeze_improvement_established=False),
        lock_timing_diagnostic=dict(first_original_error=None,original_lock_limit_seconds=600,original_check_invoked_without_replacement=True,
            unknown_measurements_not_zeroed=True,extra_CPU_RAM_or_native_query_started=False,original_resource_guard_or_deadline_extended=False,
            cleanup_callback_wrapped=False,CPU_or_PC_freeze_improvement_established=False,explicit_phase_events=[
                dict(label=label,original_lock_elapsed_seconds=float(i),guard_check_number=i+1)
                for i,label in enumerate(('before_acquire','after_acquire','before_release'))]))
    frame=dict(frame_state='COMMITTED',registered_live_frame=False,input_count=n,input_bytes=total,handles=h,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True,
        serialized_pin_reused_as_live_handle=False,input_exclusions_added=False,security_sandbox_claimed=False,
        held_identity_after_owned_cleanup=dict(held_identity_checks_complete=True,separate_pathname_reopens=0,
            regular_file_count=n,directory_count=p.DIRECTORIES),actual_byte_boundaries=[dict(role=role,
            actual_byte_pins=list(required.values()),reader_diagnostics=copy.deepcopy(diagnostic)) for role in ('before','after')])
    doc=dict(schema_version=p.SCHEMA,state=p.PASS,**p.m.p.r.flags(),source_frame=frame,
        original_failed_root_pin=p.review.ROOT,original_stopped_parent_pin=p.review.BODY,original_zero_placeholder_pin=p.review.ZERO,
        stop_review_pin=p.REVIEW_PIN,original_preparation_failure_pin=p.OLD_PREPARATION_FAILURE,
        reviewed_prior_preparation_failure_preserved_not_accepted=True,r2_preparation_failure_pin=p.R2_PREPARATION_FAILURE,
        reviewed_r2_failure_preserved_not_accepted=True,original_executed_source_pins=list(original.values()),extra_controller_pins=list(extras.values()),
        review=dict(semantic_body_capture_complete=True,independent_full_source_closing_required=True,
            runtime_acceptance_changed=False,same_product_body_reexecution_allowed=False),
        resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
        early_source_checkpoint=p.m.early_review.EarlySourceCheckpoint(lambda:None,SimpleNamespace()).summary(),
        early_source_runtime_connection_verified=True,early_source_native_and_byte_guard_connected=True,
        runtime_acceptance_changed=False,actual_product_body_executed=False,original_partial_post_source_hash_completed=False,
        closing_contract_tests_passed=p.COUNT,nominal_scope_budget=p.budget(required),
        preparation_IO=dict(finished=True,bound_inputs=21,final_fresh_hashes=21,maximum_scope_seconds=600))
    return doc,required

class ClosingTests(unittest.TestCase):
    def setUp(self):self.doc,self.required=fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(self.doc,self.required)
    def test_independent_source_only(self):p.validate(self.doc,self.required)
    def test_wrong_literal(self):self.doc['original_failed_root_pin']=dict(p.review.ROOT,bytes=1);self.reject()
    def test_source_subset(self):self.required.popitem();self.reject()
    def test_partial_or_cached_boundary(self):self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_passes']=1;self.reject()
    def test_original_inputs_retained(self):self.doc['original_executed_source_pins'].pop();self.reject()
    def test_unreleased_handle(self):self.doc['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unreleased_duplicate(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_offsets_and_identities(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['shared_offset_resets']-=1;self.reject()
    def test_600_not_relaxed(self):self.doc['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_byte_rate_not_relaxed(self):self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_rates_by_kind']['other']*=2;self.reject()
    def test_stop_not_pass(self):self.doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_original_partial_not_promoted(self):self.doc['original_partial_post_source_hash_completed']=True;self.reject()
    def test_runtime_not_promoted(self):self.doc['runtime_acceptance_changed']=True;self.reject()
    def test_final_metadata_fresh(self):self.doc['preparation_IO']['finished']=False;self.reject()
    def test_early_bridge_required(self):self.doc['early_source_native_and_byte_guard_connected']=False;self.reject()
    def test_early_guard_not_removed(self):self.doc['early_source_checkpoint']['original_hard_CPU_RAM600_guards_preserved']=False;self.reject()
    def test_no_new_sampler(self):self.doc['early_source_checkpoint']['new_sampler_or_thread_started']=True;self.reject()
    def test_acquisition14_not20(self):self.doc['source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_byte_native20_not14(self):self.doc['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=14;self.reject()
    def test_all308_ancestors(self):self.doc['source_frame']['held_identity_after_owned_cleanup']['directory_count']=306;self.reject()
    def test_all_native_reservations(self):self.doc['source_frame']['handles']['native_open_pacing']['open_reservations']-=1;self.reject()
    def test_controller_six_not_subset(self):self.doc['extra_controller_pins'].pop();self.reject()
    def test_source_not_light(self):self.doc['state']=p.LIGHT;self.reject()
    def test_real_guards_not_extended(self):self.doc['source_frame']['handles']['lock_timing_diagnostic']['original_resource_guard_or_deadline_extended']=True;self.reject()
    def test_first_error_not_PASS(self):self.doc['source_frame']['handles']['lock_timing_diagnostic']['first_original_error']={};self.reject()
    def test_gate_not_PASS(self):self.doc['P09_gate']='PASS';self.reject()

    def test_prior_failed_preparation_not_removed(self):self.doc['reviewed_prior_preparation_failure_preserved_not_accepted']=False;self.reject()

if __name__=='__main__':unittest.main()
