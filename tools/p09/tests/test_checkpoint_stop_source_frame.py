"""P258 fake validation fixture는 actual source 수용 증거가 아니다."""
import copy
import unittest
from types import SimpleNamespace
import close_checkpoint_stop_source_frame as p


def fixture():
    n=p.N;exe=p.m.p.m.EXE
    original={f'fixture/{i}.rs':dict(path=f'fixture/{i}.rs',bytes=1,sha256='a'*64) for i in range(1544)}
    original[exe['path']]=dict(exe)
    original['fixture/0.rs']['bytes']+=119242806-sum(x['bytes'] for x in original.values())
    extras={name:dict(path=name,bytes=1,sha256='b'*64) for name in p.EXTRAS}
    required={**original,**extras};total=sum(x['bytes'] for x in required.values())
    diagnostic=dict(read_passes=n,bytes_read=total,read_rates_by_kind=dict(binary=1048576,other=2097152),
        original_owned_read_operations_preserved=True,extra_sampler_or_native_query_started=False)
    h=dict(input_lock_handles_opened=n+306,input_lock_handles_closed=n+306,input_lock_handles_remaining=0,
        active_reader_bindings=0,active_byte_streams=0,input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,
        probe_handles_opened=0,probe_handles_closed=0,probe_handles_remaining=0,byte_stream_identity_checks=2*n,
        separate_pathname_reopens=0,maximum_lock_seconds=600,ancestor_walk_steps=305,
        native_open_pacing=dict(maximum_opens_per_second=20),file_write_or_delete_operation_executed=False,
        borrowed_byte_streams=dict(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n,
            duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,active_borrow_binding=False,
            byte_stream_pathname_reopens=0,original_pre_read_stream_identity_check_retained=True,
            original_held_handles_closed_by_borrower=False),
        native_open_backpressure=dict(original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
            original_sampler_windows_reused=True,cleanup_not_guarded_by_pressure=True,original_read_checks_skipped=False))
    f=dict(frame_state='COMMITTED',registered_live_frame=False,input_count=n,input_bytes=total,handles=h,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True,
        serialized_pin_reused_as_live_handle=False,input_exclusions_added=False,security_sandbox_claimed=False,
        held_identity_after_owned_cleanup=dict(held_identity_checks_complete=True,separate_pathname_reopens=0,
            regular_file_count=n,directory_count=306),actual_byte_boundaries=[dict(role=role,
            actual_byte_pins=list(required.values()),reader_diagnostics=copy.deepcopy(diagnostic)) for role in ('before','after')])
    early=p.review.EarlySourceCheckpoint(lambda:None,SimpleNamespace()).summary()
    d=dict(schema_version=p.SCHEMA,state=p.PASS,**p.m.p.r.flags(),source_frame=f,
        original_failed_root_pin=p.review.ROOT_PIN,original_stopped_parent_pin=p.review.BODY_PIN,
        original_zero_placeholder_pin=p.review.ZERO_PIN,stop_review_pin=p.REVIEW_PIN,
        original_executed_source_pins=list(original.values()),extra_controller_pins=list(extras.values()),
        review=dict(semantic_body_capture_complete=True,independent_full_source_closing_required=True,
            runtime_acceptance_changed=False,same_product_body_reexecution_allowed=False),
        resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,early_source_checkpoint=early,
        early_source_runtime_connection_verified=True,early_source_native_and_byte_guard_connected=True,
        runtime_acceptance_changed=False,actual_product_body_executed=False,original_partial_post_source_hash_completed=False,
        closing_contract_tests_passed=14,nominal_scope_budget=p.budget(required),
        preparation_IO=dict(finished=True,bound_inputs=10,final_fresh_hashes=10,maximum_scope_seconds=600))
    return d,required


class ClosingTests(unittest.TestCase):
    def setUp(self):self.doc,self.required=fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(self.doc,self.required)
    def test_independent_source_only(self):p.validate(self.doc,self.required)
    def test_wrong_literal(self):self.doc['original_failed_root_pin']=dict(p.review.ROOT_PIN,bytes=1);self.reject()
    def test_source_subset(self):self.required.popitem();self.reject()
    def test_partial_or_cached_boundary(self):self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_passes']=1;self.reject()
    def test_original_inputs_retained(self):self.doc['original_executed_source_pins'].pop();self.reject()
    def test_unreleased_handle(self):self.doc['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unreleased_duplicate(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_offsets_and_identities(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['shared_offset_resets']-=1;self.reject()
    def test_rate_and600_not_relaxed(self):
        self.doc['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
        self.doc['source_frame']['handles']['maximum_lock_seconds']=600
        self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_rates_by_kind']['other']*=2;self.reject()
    def test_stop_not_pass(self):self.doc['resource_stop_reason']=p.review.STOP;self.reject()
    def test_no_original_or_runtime_promotion(self):
        self.doc['original_partial_post_source_hash_completed']=True;self.reject()
        self.doc['original_partial_post_source_hash_completed']=False;self.doc['runtime_acceptance_changed']=True;self.reject()
    def test_final_metadata_fresh(self):self.doc['preparation_IO']['finished']=False;self.reject()
    def test_early_bridge_required(self):self.doc['early_source_native_and_byte_guard_connected']=False;self.reject()
    def test_early_guard_or_new_sampler_rejected(self):
        self.doc['early_source_checkpoint']['original_hard_CPU_RAM600_guards_preserved']=False;self.reject()
        self.doc['early_source_checkpoint']['original_hard_CPU_RAM600_guards_preserved']=True
        self.doc['early_source_checkpoint']['new_sampler_or_thread_started']=True;self.reject()
