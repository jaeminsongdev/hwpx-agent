import copy
import unittest
import close_borrowed_source_frame as p


def fixture():
    required={f'input/{i}.rs':dict(path=f'input/{i}.rs',bytes=1,sha256='a'*64) for i in range(1480)}
    diagnostic=dict(read_passes=1480,bytes_read=1480,original_owned_read_operations_preserved=True,
        read_rates_by_kind=dict(binary=1048576,other=2097152))
    handles=dict(input_lock_handles_opened=1786,input_lock_handles_closed=1786,input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True,byte_stream_identity_checks=2960,active_reader_bindings=0,active_byte_streams=0,
        handle_close_failed_attempts=0,probe_handles_opened=0,probe_handles_closed=0,probe_handles_remaining=0,
        native_open_pacing=dict(maximum_opens_per_second=32),borrowed_byte_streams=dict(duplicate_handles_opened=2960,
            duplicate_handles_closed=2960,shared_offset_resets=2960,duplicate_handles_remaining=0,
            duplicate_close_failed_attempts=0,active_borrow_binding=False,byte_stream_pathname_reopens=0,
            original_pre_read_stream_identity_check_retained=True,original_held_handles_closed_by_borrower=False))
    frame=dict(frame_state='COMMITTED',registered_live_frame=False,input_count=1480,input_bytes=1480,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True,
        handles=handles,actual_byte_boundaries=[dict(role=role,actual_byte_pins=list(required.values()),
            reader_diagnostics=copy.deepcopy(diagnostic)) for role in ('before','after')])
    doc=dict(schema_version=p.SCHEMA,state=p.PASS,source_frame=frame,original_failed_frame_pin=p.review.FRAME,
        original_stopped_parent_pin=p.review.BODY,review=dict(semantic_body_capture_complete=True,
            runtime_accepted=False,same_product_body_reexecution_allowed=False),resource_stop_reason=None,
        resource_watcher_cleanup_confirmed=True,runtime_acceptance_changed=False,actual_product_body_executed=False,
        preparation_IO=dict(finished=True,bound_inputs=9,final_fresh_hashes=9),**p.p.r.flags())
    return doc,required


class ClosingTests(unittest.TestCase):
    def setUp(self):self.doc,self.required=fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(self.doc,self.required)
    def test_source_only_full_frame_is_not_runtime(self):p.validate(self.doc,self.required)
    def test_original_failed_receipt_substitution_rejected(self):
        self.doc['original_failed_frame_pin']=dict(self.doc['original_failed_frame_pin'],sha256='b'*64);self.reject()
    def test_input_subset_rejected(self):self.required.popitem();self.reject()
    def test_cached_hash_instead_of_actual_byte_pass_rejected(self):
        self.doc['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_passes']=0;self.reject()
    def test_unreleased_original_handles_rejected(self):
        self.doc['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unreleased_duplicate_rejected(self):
        self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_missing_shared_position_reset_rejected(self):
        self.doc['source_frame']['handles']['borrowed_byte_streams']['shared_offset_resets']=2959;self.reject()
    def test_failed_close_rejected(self):
        self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_close_failed_attempts']=1;self.reject()
    def test_resource_stop_never_source_pass(self):self.doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_runtime_or_gate_promotion_rejected(self):self.doc['runtime_acceptance_changed']=True;self.reject()
