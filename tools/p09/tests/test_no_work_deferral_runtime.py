"""P285 현재/다음1597 synthetic82. 원P26530 거부조건 유지/새연결34 추가/무작업보류18."""
import resume_no_work_deferral_runtime as m
import test_monotonic_compound_runtime as old
import io
from types import SimpleNamespace
from unittest.mock import patch


class QueueTests(old.QueueTests):
    def setUp(self):
        super().setUp()
        policy=m.metadata.Binding.summary(type('Policy',(),dict(early=m.early_review.EarlySourceCheckpoint(lambda:None,None)))())
        self.doc['preparation_IO']['early_metadata_pressure']=policy
        self.doc['closing_component']['metadata_IO']['early_metadata_pressure']=policy
        h=self.doc['closing_component']['source_frame']['handles']
        connection=dict(entry_and_byte_warning_CPU_percent=90,original_entry_rate_per_second=32,
            same_original_entry_pacer=True,entry_and_byte_share_existing_early_object=True,original95_retained_as_first_base=True,
            original_clock_sleeper_reader_retained=True,constructor_before_attachment_original95_preserved=True,
            clock_credit_or_read_counter_reset=False,original600_720_CPU_RAM_guards_preserved=True,
            extra_CPU_native_query_sampler_or_thread_started=False,cleanup_callback_wrapped=False,
            original_reads_source_byte_or_identity_checks_skipped=False,CPU_or_PC_freeze_improvement_established=False)
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']=connection
        self.doc['closing_component']['metadata_IO']['metadata_entry_early_pressure_connection']=connection
        h['handle_metadata_checks']=4*len(self.required)+2*m.DIRECTORIES
        h['input_lock_handles_opened']=h['input_lock_handles_closed']=len(self.required)+m.DIRECTORIES
        h['ancestor_walk_steps']=m.DIRECTORIES-1
        h['native_open_pacing']['open_reservations']=3*len(self.required)+m.DIRECTORIES
        self.doc['closing_component']['source_frame']['held_identity_after_owned_cleanup']['directory_count']=m.DIRECTORIES
        h['acquisition_phase_pressure']=dict(acquisition_maximum_reservations_per_second=14,
            original_global_and_byte_reservation_ceiling_per_second=20,acquisition_used=True,acquisition_complete=True,
            acquisition_reservations=len(self.required)+m.DIRECTORIES,restored_original_rate=20,same_original_pacer=True,
            clock_and_sleeper_and_checkpoint_retained=True,clock_previous_credit_or_reservation_counter_reset=False,
            extra_sampler_or_thread_started=False,original_CPU_RAM600_and_all_byte_identity_guards_preserved=True,
            cleanup_callback_wrapped=False,CPU_or_PC_freeze_improvement_established=False)
        h['lock_timing_diagnostic']=dict(original_guard_checks=100,first_original_error=None,original_lock_limit_seconds=600,
            original_check_invoked_without_replacement=True,extra_clock_only_at_boundary_or_first_error=True,
            unknown_measurements_not_zeroed=True,extra_CPU_RAM_or_native_query_started=False,
            original_resource_guard_or_deadline_extended=False,cleanup_callback_wrapped=False,
            CPU_or_PC_freeze_improvement_established=False,
            explicit_phase_events=[dict(label=label,phase='admission',original_lock_elapsed_seconds=float(i),
                guard_check_number=i+1) for i,label in enumerate(m.connection.LABELS)])
    def test_diagnostic_connection_not_selected_denied(self):self.doc['diagnostic_parent_connection_selected']=False;self.reject()
    def test_native_timing_not_connected_denied(self):self.doc['native_timing_connected']=False;self.reject()
    def test_metadata90_not_connected_denied(self):self.doc['early_metadata_connection_selected']=False;self.reject()
    def test_qualified_metadata_pin_drift_denied(self):self.doc['qualified_metadata_pin']=dict(m.METADATA_PIN,bytes=0);self.reject()
    def test_metadata_warning_not_delayed_back_to95(self):
        self.doc['preparation_IO']['early_metadata_pressure']['selected_metadata_warning_CPU_percent']=95;self.reject()
    def test_original95_not_removed(self):
        self.doc['preparation_IO']['early_metadata_pressure']['original95_pressure_retained_as_base']=False;self.reject()
    def test_timing_original_error_not_PASS(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['first_original_error']={};self.reject()
    def test_timing600_not_extended(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['original_lock_limit_seconds']=601;self.reject()
    def test_unknown_timing_not_invented_zero(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['explicit_phase_events'][0]['original_lock_elapsed_seconds']=None;self.reject()
    def test_timing_claim_or_query_not_added(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['extra_CPU_RAM_or_native_query_started']=True;self.reject()
    def test_constructor_failure_missing_io_reviewed_not_accepted(self):
        row=dict(schema_version=m.metadata.SCHEMA,state='FAILED_NOT_ACCEPTED',error_code='P152_FULL_REDACTED_FAILURE',
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,actual_product_body_or_full_source_executed=False)
        m.constructor_failure(row)
    def test_constructor_failure_io_invented_denied(self):
        row=dict(schema_version=m.metadata.SCHEMA,state='FAILED_NOT_ACCEPTED',error_code='P152_FULL_REDACTED_FAILURE',
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,actual_product_body_or_full_source_executed=False,IO=None)
        with self.assertRaises(ValueError):m.constructor_failure(row)
    def test_constructor_failure_pass_not_reviewed(self):
        row=dict(schema_version=m.metadata.SCHEMA,state=m.metadata.PASS,error_code='P152_FULL_REDACTED_FAILURE',
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,actual_product_body_or_full_source_executed=False)
        with self.assertRaises(ValueError):m.constructor_failure(row)
    def test_diagnostic_no_message_or_value(self):
        try:raise KeyError('PRIVATE_VALUE_MUST_NOT_ESCAPE')
        except KeyError as error:row=m.diagnostic(error,'anchor')
        self.assertEqual(row['exception_class'],'KeyError')
        self.assertNotIn('PRIVATE_VALUE_MUST_NOT_ESCAPE',str(row))
        self.assertFalse(row['exception_message_included'])

    def test_packed_byte_bound_canonical_only_once(self):
        value={'schema_version':'synthetic-only','a':1}
        carrier,unused=m.r.packed.pack(value,lambda:None)
        stream=io.StringIO();m.r.compact.dump(carrier,stream,checkpoint=lambda:None,indent=2)
        encoded=stream.getvalue().encode('ascii');name=m.p.DIR+'/p280-light-synthetic.v1.json'
        q=SimpleNamespace(name=lambda path:name,checkpoint=lambda:None,
            reader=SimpleNamespace(snapshots={name:dict(path=name,bytes=len(encoded),sha256=m.hashlib.sha256(encoded).hexdigest())}))
        with patch.object(m.RAW_JSON_READER,'json',return_value=carrier),patch.object(m.r.h,'canonical',wraps=m.r.h.canonical) as checked:
            self.assertEqual(m.Reader.json(q,name),value)
            self.assertEqual(checked.call_count,1)
    def test_packed_carrier_byte_drift_denied_before_decode(self):
        carrier,unused=m.r.packed.pack({'schema_version':'synthetic-only'},lambda:None)
        name=m.p.DIR+'/p280-light-synthetic.v1.json'
        q=SimpleNamespace(name=lambda path:name,checkpoint=lambda:None,
            reader=SimpleNamespace(snapshots={name:dict(path=name,bytes=0,sha256='0'*64)}))
        with patch.object(m.RAW_JSON_READER,'json',return_value=carrier):
            with self.assertRaises(ValueError):m.Reader.json(q,name)

    def test_acquisition_phase_not_connected_denied(self):
        self.doc['acquisition_phase_connection_selected']=False;self.reject()
    def test_acquisition14_not_replaced_with20(self):
        self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_byte20_not_left_at14(self):
        self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['restored_original_rate']=14;self.reject()
    def test_phase_clock_credit_not_reset(self):
        self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['clock_previous_credit_or_reservation_counter_reset']=True;self.reject()
    def test_partial_acquisition_not_full_scope(self):
        self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['acquisition_reservations']-=1;self.reject()
    def test_phase_qualification_pin_not_foreign(self):
        self.doc['qualified_acquisition_phase_pin']=dict(m.PHASE_QUALIFIER,bytes=0);self.reject()

    def test_cached_entry_binding_not_selected_denied(self):
        self.doc['metadata_entry_pressure_connection_selected']=False;self.reject()
    def test_entry_not_shared_with_byte90_denied(self):
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']['entry_and_byte_share_existing_early_object']=False;self.reject()
    def test_original95_not_removed_from_shared_base(self):
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']['original95_retained_as_first_base']=False;self.reject()
    def test_original_metadata32_not_reconfigured(self):
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']['original_entry_rate_per_second']=20;self.reject()
    def test_shared_callback_counters_not_reset(self):
        self.doc['preparation_IO']['metadata_entry_early_pressure_connection']['clock_credit_or_read_counter_reset']=True;self.reject()
    def test_qualified_entry_pin_not_foreign(self):
        self.doc['qualified_metadata_entry_pressure_pin']=dict(m.ENTRY_QUALIFIER,bytes=0);self.reject()

    def test_latest_preparation_stop_pin_not_foreign(self):
        self.doc['reviewed_latest_preparation_STOP_pin']=dict(m.LATEST_STOP,bytes=0);self.reject()
    def test_latest_stop_not_unreviewed_or_accepted(self):
        self.doc['reviewed_latest_STOP_preserved_not_accepted']=False;self.reject()

    def test_current97_stop_pin_not_foreign(self):
        self.doc['reviewed_current97_STOP_pin']=dict(m.CURRENT97_STOP,bytes=0);self.reject()
    def test_current97_stop_not_unreviewed_or_accepted(self):
        self.doc['reviewed_current97_STOP_preserved_not_accepted']=False;self.reject()

    def test_original_no_work_defer_pin_not_foreign(self):
        self.doc['reviewed_original_no_work_deferral_pin']=dict(m.ORIGINAL_NO_WORK_DEFER,bytes=0);self.reject()
    def test_original_no_work_defer_not_accepted_as_body(self):
        self.doc['reviewed_original_no_work_deferral_preserved']=False;self.reject()


import unittest
import copy


class DeferralTests(unittest.TestCase):
    def setUp(self):
        false_keys=('compound_anchor_verified_without_body_reexecution','early_source_guard_connected',
            'original_parent_capture_adapter_selected','aggregate_post_reader_connection_verified',
            'diagnostic_parent_connection_selected','native_timing_connected','early_metadata_connection_selected',
            'acquisition_phase_connection_selected','metadata_entry_pressure_connection_selected',
            'reviewed_latest_STOP_preserved_not_accepted','reviewed_current97_STOP_preserved_not_accepted',
            'reviewed_original_no_work_deferral_preserved')
        self.doc=dict(schema_version=m.SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
            error_code='DEFERRED_ALREADY_SATURATED_SYSTEM',resource_stop_reason=None,
            resource_watcher_cleanup_confirmed=True,accepted_exact_product_body_count=0,
            failure_diagnostic=dict(stage='admission',exception_class='ValueError',diagnostic_not_acceptance=True),
            metadata_observation=dict(completed_sample_count=1,new_sampler_thread_started=False,
                samples=[dict(system_cpu_percent=100,phase_at_sample='admission',phases_since_previous_sample=['admission'],
                    reader_counters_observed=False,audited_logical_read_bytes=None,
                    audited_logical_read_passes=None,audited_logical_read_bytes_delta=None)]))
        self.doc.update({k:False for k in false_keys})
    def review(self):return m.deferred_admission_review(self.doc,m.SCHEMA)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.review()
    def test_no_work_review_preserves_failed_row_not_queue(self):
        before=copy.deepcopy(self.doc);r=self.review()
        self.assertEqual(self.doc,before);self.assertFalse(r['accepted_queue_advanced'])
        self.assertEqual(r['accepted_product_body_count'],0)
    def test_later_anchor_failure_not_noop(self):self.doc['failure_diagnostic']['stage']='anchor';self.reject()
    def test_partial_reader_not_noop(self):self.doc['preparation_IO']={};self.reject()
    def test_body_path_not_noop(self):self.doc['case_receipt_path']='case';self.reject()
    def test_actual_product_not_noop(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_executed_contracts_not_noop(self):self.doc['runtime_contract_executions']=990;self.reject()
    def test_selected_case_not_noop(self):self.doc['selected_test_index']=97;self.reject()
    def test_original_hard_STOP_not_noop(self):self.doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_cleanup_unconfirmed_not_noop(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_new_sampler_not_noop(self):self.doc['metadata_observation']['new_sampler_thread_started']=True;self.reject()
    def test_missing_original_sample_not_noop(self):self.doc['metadata_observation']['samples']=[];self.reject()
    def test_foreign_schema_not_noop(self):self.doc['schema_version']=m.previous.SCHEMA;self.reject()
    def test_queue_field_not_noop(self):self.doc['runtime_plan']={};self.reject()
    def test_observed_reader_counters_not_noop(self):self.doc['metadata_observation']['samples'][0]['reader_counters_observed']=True;self.reject()
    def test_other_error_not_noop(self):self.doc['error_code']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_callback_attached_after_reader_not_noop(self):self.doc['metadata_entry_pressure_connection_selected']=True;self.reject()
    def test_no_work_failed_not_own_closed_PASS(self):
        with self.assertRaises(ValueError):m.closed_attempt(self.doc)
    def test_gate_not_promoted_by_noop(self):self.doc['P09_gate']='PASS';self.reject()


if __name__=='__main__':
    import unittest
    unittest.main()
