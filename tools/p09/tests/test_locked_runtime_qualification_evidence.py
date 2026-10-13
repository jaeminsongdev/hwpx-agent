"""P207 실제 결과의 scope/fresh/수명/권한/Gate 경계를 약화하지 않는다."""
import copy
import unittest
import locked_runtime_qualification_evidence as e


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.inputs={'tools/probe.txt':dict(path='tools/probe.txt',bytes=1,sha256='a'*64),
            'target/demo.exe':dict(path='target/demo.exe',bytes=2,sha256='b'*64)}
        self.helpers={'tools/probe.txt':self.inputs['tools/probe.txt']};self.binding={'original':'binding'}
        self.doc=dict(schema_version='hwpx-agent.p09-locked-runtime-input-qualification/v1',state=e.PASS,
            qualification_scope='full-runtime',input_lock_contract_tests_passed=43,binding=self.binding,
            qualified_input_pins=list(self.inputs.values()),qualified_inputs=2,qualified_input_bytes=3,
            prior_runtime_inputs=1,known_fixture_input_count=1,all_prior_runtime_inputs_retained=True,
            qualification_helper_pins=list(self.helpers.values()),resource_stop_reason=None,
            resource_watcher_cleanup_confirmed=True,goal_status='active',P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
            new_input_exclusions=[],actual_file_and_ancestor_handles_noninheritable=True,
            file_and_path_identities_checked_before_and_after_fresh_reads=True,
            locked_identity_before=dict(held_identity_checks_complete=True,regular_file_count=2,directory_count=3,
                path_identities_confirmed_on_acquisition=True),
            locked_identity_after=dict(held_identity_checks_complete=True,regular_file_count=2,directory_count=3,
                separate_pathname_reopens=0),
            byte_stream_identity_passes=dict(verified_byte_streams=4,locked_inputs=2,
                each_input_hashed_twice_with_same_open_stream_identity=True,separate_pathname_reopens=0),
            input_locks=dict(input_lock_handles_opened=5,input_lock_handles_closed=5,input_lock_handles_remaining=0,
                probe_handles_opened=3,probe_handles_closed=3,probe_handles_remaining=0,input_lock_cleanup_confirmed=True,
                handle_close_failed_attempts=0,probe_handle_close_failed_attempts=0,active_reader_bindings=0,
                active_byte_streams=0,release_started=True,ancestor_walk_steps=2,maximum_lock_seconds=600,
                byte_stream_identity_checks=4,handle_metadata_checks=14,separate_pathname_reopens=0,
                file_write_or_delete_operation_executed=False,input_scope_reduced=False,
                kernel_or_malicious_bypass_protection_claimed=False,native_open_pacing=dict(maximum_opens_per_second=32,
                    idle_time_cannot_accumulate_multiple_open_credits=True,open_reservations=15)),
            bound_input_pins=list(self.inputs.values()),IO=dict(finished=True,bound_inputs=2,final_fresh_hashes=2,
                read_passes=4,bytes_read=6,pacer_bytes_read=6,bytes_read_by_kind=dict(binary=4,other=2),
                maximum_scope_seconds=600,chunk_bytes=65536,burst_bytes=65536,parse_budget_bytes=16777216,
                all_original_read_operations_preserved=True,read_rates_by_kind=dict(binary=1048576,other=2097152),
                near_saturation_read_backpressure=dict(warning_system_CPU_percent=95,cool_distinct_sample_windows=2,
                    maximum_pause_windows_per_entry=8,original_hard_resource_decisions_unmodified=True,
                    original_IO_deadline_unmodified=True,original_sampler_windows_reused=True,
                    new_native_query_or_sampler_thread_started=False,original_read_checks_skipped=False)),
            access_during_held_locks=dict(read=dict(opened=True,win32_error=0),write=dict(opened=False,win32_error=32),
                delete=dict(opened=False,win32_error=32)),
            access_after_release=dict(write=dict(opened=True,win32_error=0),delete=dict(opened=True,win32_error=0)),
            probe_access_open_only_no_write_truncate_delete_or_rename=True,
            sharing_probe_file_pin=self.inputs['tools/probe.txt'],own_probe_after_release_read_bytes=1)
        for key in ('full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved',
                'whole1470_current_fresh_qualified','historical67_current_fresh_qualified','actual_product_child_executed',
                'actual_product_test_body_or_shared_frame_executed','existing_actual_runner_input_scope_changed',
                'content_or_attributes_written_or_deleted','verification_IO_reduction_already_applied'):self.doc[key]=False
    def validate(self,doc=None):return e.validate(self.doc if doc is None else doc,self.inputs,self.binding,self.helpers,1,1)
    def test_complete_scope_accepted_without_product_acceptance(self):
        before=copy.deepcopy(self.doc);out=self.validate()
        self.assertEqual(out['actual_byte_stream_checks'],4);self.assertFalse(out['shared_runtime_frame_or_product_acceptance'])
        self.assertEqual(self.doc,before)
    def test_input_omission_duplicate_or_different_pin_rejected(self):
        for kind in ('omission','duplicate','changed'):
            doc=copy.deepcopy(self.doc)
            if kind=='omission':doc['qualified_input_pins'].pop()
            elif kind=='duplicate':doc['qualified_input_pins'].append(doc['qualified_input_pins'][0])
            else:doc['qualified_input_pins'][0]['sha256']='c'*64
            with self.assertRaises(ValueError):self.validate(doc)
    def test_partial_final_hash_or_missing_bound_input_rejected(self):
        for kind in ('partial','missing','cache'):
            doc=copy.deepcopy(self.doc)
            if kind=='partial':doc['IO']['final_fresh_hashes']=1
            elif kind=='missing':doc['bound_input_pins'].pop()
            else:doc['IO']['bytes_read']=3
            with self.assertRaises(ValueError):self.validate(doc)
    def test_probe_or_stream_leak_and_close_failure_rejected(self):
        for key in ('input_lock_handles_remaining','probe_handles_remaining','active_byte_streams',
                'active_reader_bindings','handle_close_failed_attempts','probe_handle_close_failed_attempts'):
            doc=copy.deepcopy(self.doc);doc['input_locks'][key]=1
            with self.assertRaises(ValueError):self.validate(doc)
    def test_one_pass_or_identity_failure_rejected(self):
        for kind in ('one_pass','identity','directory'):
            doc=copy.deepcopy(self.doc)
            if kind=='one_pass':doc['byte_stream_identity_passes']['verified_byte_streams']=2
            elif kind=='identity':doc['locked_identity_after']['held_identity_checks_complete']=False
            else:doc['locked_identity_before']['directory_count']=2
            with self.assertRaises(ValueError):self.validate(doc)
    def test_unpaced_opens_or_weakened_resource_guard_rejected(self):
        for kind in ('rate','opens','guard'):
            doc=copy.deepcopy(self.doc)
            if kind=='rate':doc['input_locks']['native_open_pacing']['maximum_opens_per_second']=64
            elif kind=='opens':doc['input_locks']['native_open_pacing']['open_reservations']=16
            else:doc['IO']['near_saturation_read_backpressure']['original_read_checks_skipped']=True
            with self.assertRaises(ValueError):self.validate(doc)
    def test_writable_during_lock_or_failed_probe_release_rejected(self):
        for kind in ('writable','released','mutated'):
            doc=copy.deepcopy(self.doc)
            if kind=='writable':doc['access_during_held_locks']['write']=dict(opened=True,win32_error=0)
            elif kind=='released':doc['access_after_release']['delete']=dict(opened=False,win32_error=32)
            else:doc['probe_access_open_only_no_write_truncate_delete_or_rename']=False
            with self.assertRaises(ValueError):self.validate(doc)
    def test_product_promotion_or_CPU_stop_rejected(self):
        for key in ('product_complete','PC_freeze_resolved','actual_product_child_executed'):
            doc=copy.deepcopy(self.doc);doc[key]=True
            with self.assertRaises(ValueError):self.validate(doc)
        doc=copy.deepcopy(self.doc);doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU'
        with self.assertRaises(ValueError):self.validate(doc)


if __name__=='__main__':unittest.main()
