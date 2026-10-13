"""P320 explicit synthetic current/following full1648. 테스트 자료는 실제 수용 증거 아님."""
import copy
import unittest
import resume_compact_completed103_runtime as m
FIXTURES=None
FOLLOWING=False

def fixture():
    if FIXTURES is None:raise RuntimeError('EXACT_FRESH_ANCHOR_REQUIRED')
    legacy,base,names,required,extras,baseline,added,old,body=copy.deepcopy(FIXTURES)
    if FOLLOWING:
        index,_=m.g.old.select(base,names);base=m.g.advance(legacy,base,names,index)
    index,name=m.g.old.select(base,names);doc=copy.deepcopy(old);n=len(required);total=sum(x['bytes'] for x in required.values())
    delta=total-body['owned_source_reader_passes'][0]['bytes_read']
    body.update(selected_test_names=[name],passed_test_names=[name],test_arguments=m.p.v.arguments(name),
        task=f'p204-r07-case-{index:03}-tests',minimal_worker_task=f'p204-r07-case-{index:03}-tests',
        source_freeze=copy.deepcopy(list(required.values())))
    for row in body['owned_source_reader_passes']:
        row.update(read_passes=n,bytes_read=total);row['bytes_read_by_kind']['other']+=delta
    pin=dict(doc['case_receipt_pin'],path=f'{m.p.DIR}/cases/p320-case-{index:03}-run001.json')
    component=doc['closing_component'];frame=component['source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    component.update(case_receipt_pin=pin,selected_test_name=name,extra_frame_controller_pins=copy.deepcopy(list(extras.values())))
    frame.update(input_count=n,input_bytes=total)
    for i,row in enumerate(frame['actual_byte_boundaries']):
        row.update(actual_byte_pins=copy.deepcopy(list(required.values())),reader_diagnostics=copy.deepcopy(body['owned_source_reader_passes'][i]))
    h.update(input_lock_handles_opened=n+m.DIRECTORIES,input_lock_handles_closed=n+m.DIRECTORIES,
        byte_stream_identity_checks=2*n,ancestor_walk_steps=m.DIRECTORIES-1,handle_metadata_checks=4*n+2*m.DIRECTORIES)
    h['native_open_pacing']['open_reservations']=3*n+m.DIRECTORIES
    h['acquisition_phase_pressure']['acquisition_reservations']=n+m.DIRECTORIES
    dup.update(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n)
    frame['held_identity_after_owned_cleanup'].update(regular_file_count=n,directory_count=m.DIRECTORIES)
    def preentry(row):
        x=dict(pre_entry_warning_CPU_percent=90,original_entry_rate=32,calls=row['read_passes'],
            completed_original_reads=row['read_passes'],failed_calls=0,leading_binding_active=False,
            early_pressure=m.early_review.EarlySourceCheckpoint(lambda:None,None).summary(),
            original_inner95_and90_callbacks_unmodified=True,original_entry_pacer_and_reader_retained=True,
            original_hard_CPU_RAM_IO600_720_and_all_reads_preserved=True,new_sampler_or_thread_started=False,
            original_clock_credit_or_counter_reset=False,source_or_case_or_read_exclusions_added=False,
            cleanup_not_guarded_or_paced=True,CPU_cause_or_PC_freeze_resolution_established=False)
        row['leading_metadata_entry_pressure']=x
        row['leading_metadata_checkpoint_pressure']=dict(warning_CPU_percent=90,inner_guard_calls=row['read_passes'],
            early_pressure=m.early_review.EarlySourceCheckpoint(lambda:None,None).summary(),binding_active=False,
            hard_callback_restored_after_close=True,original95_guard_callback_wrapped_only_while_bound=True,
            original_hard_CPU_RAM_IO600_callback_always_first=True,
            original95_object_and_outer90_and_entry32_callbacks_retained=True,
            original_reader_and_byte_pacer_and_counters_retained=True,new_sampler_or_thread_or_native_query_started=False,
            guards_or_deadline_or_source_coverage_relaxed=False,cleanup_not_guarded_or_paced=True,
            CPU_cause_or_PC_freeze_resolution_established=False)
    preentry(doc['preparation_IO']);preentry(component['metadata_IO'])
    checkpoints=dict(started_tests=m.EXECUTED,stopped_tests=m.EXECUTED,
        successful_before_test_checks=m.EXECUTED,successful_after_test_checks=m.EXECUTED,
        runner_calls=2,returned_runner_calls=2,successful_before_runner_checks=2,successful_after_runner_checks=2,
        original_unittest_results_preserved=True,new_sampler_or_thread_or_sleep_started=False,
        original_guard_or_test_coverage_relaxed=False,test_results_are_not_product_acceptance=True)
    doc.update(schema_version=m.SCHEMA,state=m.PASS,compound_anchor_pin=m.ANCHOR,
        compact_qualification_pin=m.COMPACT_QUALIFIER,compact_status_pin=m.COMPACT_STATUS,
        compact_checkpoint_policy=m.compact.policy(),compact_checkpoint_selected=True,reused_compact_contract_executions=26,
        reused_original_guard_contract_executions=78,reused_original_guard_qualification_root_pin=m.compact.ROOT,
        completed102_anchor_pin=m.COMPLETED102,previous103_preparation_STOP_pin=m.PREPARATION103_STOP,
        guarded_contract_qualification_pin=m.GUARDED_QUALIFIER,previous_status_STOP_pin=m.STATUS_STOP,
        previous103_STOP_reviewed=True,per_test_original_checkpoint_selected=True,reused_helper_contract_executions=21,
        contract_checkpoint_statistics=checkpoints,
        retained_contract_qualification_pin=m.RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        previous_preparation_STOP_pin=m.inner.FAILURE,inner_metadata_qualification_pin=m.INNER_QUALIFIER,
        previous_Native_STOP_pin=m.NATIVE_STOP,counter_support_status_pin=m.SUPPORT_STATUS,idle_support_pin=m.IDLE,
        counter_qualification_pin=m.COUNTER_QUALIFIER,counter_two_queries_pin=m.COUNTER_REAL,
        previous_Native_STOP_reviewed=True,counter_code_qualification_selected=True,
        counter_role='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        compound_anchor_verified_without_body_reexecution=True,
        metadata_entry_pressure_connection_selected=True,packed_root_writer_selected=True,
        runtime_contract_executions=m.EXECUTED,own_queue_contract_tests_passed=m.COUNT,
        synthetic_following_queue_contract_tests_passed=m.COUNT,selected_test_index=index,selected_test_name=name,
        case_receipt_pin=pin,prior_runtime_plan=copy.deepcopy(base),runtime_plan=m.g.advance(legacy,base,names,index),
        scope_budget=m.budget(required,baseline,added),scope_added_four_pins=copy.deepcopy(list(added.values())),
        extra_frame_controller_pins=copy.deepcopy(list(extras.values())))
    return doc,body,pin,required,doc['binding'],extras,names,legacy,base,baseline,added

class Tests(unittest.TestCase):
    def setUp(self):
        (self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.base,self.baseline,self.added)=fixture()
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.base,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.record()
    def test_exact_synthetic_record(self):
        result=self.record();self.assertEqual(result['runtime_source_qualified_individual_cases'],self.base['runtime_source_qualified_individual_cases']+1)
    def test_prior_immutable(self):
        before=copy.deepcopy(self.base);self.record();self.assertEqual(before,self.base)
    def test_not_failed_row(self):self.doc['state']='FAILED_NOT_ACCEPTED';self.reject()
    def test_not_support_LIGHT(self):self.doc['state']=m.LIGHT;self.reject()
    def test_wrong_anchor(self):self.doc['compound_anchor_pin']=dict(m.ANCHOR,bytes=1);self.reject()
    def test_wrong_retained_pin(self):self.doc['retained_contract_qualification_pin']=dict(m.RETAINED_QUALIFIER,bytes=1);self.reject()
    def test_reused_not_executed_count(self):self.doc['runtime_contract_executions']+=1486;self.reject()
    def test_retained_count(self):self.doc['reused_retained_contract_executions']=0;self.reject()
    def test_subset_scope(self):self.required.popitem();self.reject()
    def test_baseline_changed(self):self.baseline.popitem();self.reject()
    def test_six_missing(self):self.added.popitem();self.reject()
    def test_current_code_drift(self):self.added[m.SELF]['sha256']='b'*64;self.reject()
    def test_EXE_drift(self):self.required[m.p.m.EXE['path']]['sha256']='b'*64;self.reject()
    def test_body_source_subset(self):self.body['source_freeze'].pop();self.reject()
    def test_body_partial_after(self):self.body['owned_source_reader_passes'][1]['read_passes']=1;self.reject()
    def test_body_bad_capture(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_body_failed_exit(self):self.body['exit_code']=1;self.reject()
    def test_body_job_cpu_relaxed(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_body_job_affinity_relaxed(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_body_wrong_task(self):self.body['task']='p204-r07-case-101-tests';self.reject()
    def test_wrong_selected_name(self):self.doc['selected_test_name']=self.names[100];self.reject()
    def test_accepted_duplicate(self):self.base['runtime_qualified_test_names'].append(self.doc['selected_test_name']);self.reject()
    def test_wrong_prior(self):self.doc['prior_runtime_plan']['next_runtime_index']+=1;self.reject()
    def test_wrong_next_plan(self):self.doc['runtime_plan']['next_runtime_index']+=1;self.reject()
    def test_scope_budget_relaxed(self):self.doc['scope_budget']['original_IO_scope_seconds']=601;self.reject()
    def test_native_handle_unclosed(self):self.doc['closing_component']['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_duplicate_unclosed(self):self.doc['closing_component']['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_native_count_partial(self):self.doc['closing_component']['source_frame']['handles']['input_lock_handles_opened']-=1;self.reject()
    def test_directory_partial(self):self.doc['closing_component']['source_frame']['held_identity_after_owned_cleanup']['directory_count']=306;self.reject()
    def test_boundary_cached(self):self.doc['closing_component']['source_frame']['serialized_pin_reused_as_live_handle']=True;self.reject()
    def test_source_registered(self):self.doc['closing_component']['source_frame']['registered_live_frame']=True;self.reject()
    def test_CPU_STOP_not_accept(self):self.doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_cleanup_not_confirmed(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_gate_not_promoted(self):self.doc['P09_gate']='PASS';self.reject()
    def test_leading_callback_changed(self):self.doc['preparation_IO']['leading_metadata_entry_pressure']['original_inner95_and90_callbacks_unmodified']=False;self.reject()
    def test_leading_hard_guard_relaxed(self):self.doc['closing_component']['metadata_IO']['leading_metadata_entry_pressure']['original_hard_CPU_RAM_IO600_720_and_all_reads_preserved']=False;self.reject()
    def test_leading_suppressed_read(self):self.doc['preparation_IO']['leading_metadata_entry_pressure']['completed_original_reads']-=1;self.reject()
    def test_extra_sampler(self):self.doc['preparation_IO']['leading_metadata_entry_pressure']['new_sampler_or_thread_started']=True;self.reject()
    def test_lossy_body_writer(self):self.doc['packed_parent_write_statistics']['semantic_fields_removed']=1;self.reject()
    def test_timing_deadline_relaxed(self):self.doc['closing_component']['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_acquisition_rate_relaxed(self):self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_unknown_failed_attempt(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(schema_version=m.SCHEMA,state='FAILED_NOT_ACCEPTED'))

    def inner(self):return self.doc['preparation_IO']['leading_metadata_checkpoint_pressure']
    def test_inner_not_restored(self):self.inner()['hard_callback_restored_after_close']=False;self.reject()
    def test_inner_active(self):self.inner()['binding_active']=True;self.reject()
    def test_inner_guard_not_first(self):self.inner()['original_hard_CPU_RAM_IO600_callback_always_first']=False;self.reject()
    def test_inner_original_callback_lost(self):self.inner()['original95_object_and_outer90_and_entry32_callbacks_retained']=False;self.reject()
    def test_inner_source_guard_relaxed(self):self.inner()['guards_or_deadline_or_source_coverage_relaxed']=True;self.reject()
    def test_inner_new_native_query(self):self.inner()['new_sampler_or_thread_or_native_query_started']=True;self.reject()
    def test_inner_suppressed_checkpoint(self):self.inner()['inner_guard_calls']=0;self.reject()
    def test_inner_cleanup_guarded(self):self.inner()['cleanup_not_guarded_or_paced']=False;self.reject()
    def test_inner_post_callback_lost(self):self.doc['closing_component']['metadata_IO']['leading_metadata_checkpoint_pressure']['hard_callback_restored_after_close']=False;self.reject()
    def test_anchor_marker_false(self):self.doc['compound_anchor_verified_without_body_reexecution']=False;self.reject()
    def test_entry_marker_false(self):self.doc['metadata_entry_pressure_connection_selected']=False;self.reject()
    def test_writer_marker_false(self):self.doc['packed_root_writer_selected']=False;self.reject()
    def test_stop_pin_drift(self):self.doc['previous_preparation_STOP_pin']=dict(m.inner.FAILURE,bytes=1);self.reject()
    def test_inner_qualification_pin_drift(self):self.doc['inner_metadata_qualification_pin']=dict(m.INNER_QUALIFIER,bytes=1);self.reject()
    def test_required_old_generation_omitted(self):self.baseline.pop(m.FROZEN70[-2]['path']);self.reject()
    def test_required_optimizer_omitted(self):self.baseline.pop(m.inner.SELF);self.reject()
    def test_distinct_plan_live_once(self):
        class Q:
            def __init__(self):self.calls=[]
            def pin(self,name):self.calls.append(name);return {'path':name,'bytes':1,'sha256':'a'*64}
        q=Q();expected=[q.pin(n) for n in ('a','b')];q.calls=[]
        result=m.live_pins(q,('a','b'),expected)
        self.assertEqual(q.calls,['a','b']);self.assertEqual(list(result.values()),expected)
    def test_distinct_plan_duplicate_rejected(self):
        class Q:
            def pin(self,name):raise AssertionError('DUPLICATE_PLAN_NO_READ')
        with self.assertRaises(ValueError):m.live_pins(Q(),('a','a'),[{'path':'a'},{'path':'a'}])


    def test_native_stop_pin_drift(self):self.doc['previous_Native_STOP_pin']=dict(m.NATIVE_STOP,bytes=1);self.reject()
    def test_support_pin_drift(self):self.doc['counter_support_status_pin']=dict(m.SUPPORT_STATUS,bytes=1);self.reject()
    def test_idle_pin_drift(self):self.doc['idle_support_pin']=dict(m.IDLE,bytes=1);self.reject()
    def test_counter_qualification_drift(self):self.doc['counter_qualification_pin']=dict(m.COUNTER_QUALIFIER,bytes=1);self.reject()
    def test_real_qualification_drift(self):self.doc['counter_two_queries_pin']=dict(m.COUNTER_REAL,bytes=1);self.reject()
    def test_stop_unreviewed(self):self.doc['previous_Native_STOP_reviewed']=False;self.reject()
    def test_unqualified_counter(self):self.doc['counter_code_qualification_selected']=False;self.reject()
    def test_counter_replaces_guard(self):self.doc['counter_role']='OVERRIDE_GUARD';self.reject()
    def test_full_p307_source_omitted(self):self.baseline.pop(m.FROZEN75[-5]['path']);self.reject()
    def test_full_p307_test_omitted(self):self.baseline.pop(m.FROZEN75[-4]['path']);self.reject()
    def test_full_counter_code_omitted(self):self.baseline.pop(m.counter.SELF);self.reject()
    def test_full_counter_test_omitted(self):self.baseline.pop(m.counter.TEST);self.reject()
    def test_full_collector_omitted(self):self.baseline.pop(m.counter.COLLECTOR);self.reject()
    def test_new_scope_added_pin_drift(self):self.doc['scope_added_four_pins'][0]['sha256']='b'*64;self.reject()
    def test_native_scope_keeps_old1635_count(self):self.doc['closing_component']['source_frame']['input_count']=1635;self.reject()
    def test_old_case_body_replay(self):self.doc['selected_test_index']=101;self.reject()

    def test_completed102_anchor_drift(self):self.doc['completed102_anchor_pin']=dict(m.COMPLETED102,bytes=1);self.reject()
    def test_previous103_STOP_pin_drift(self):self.doc['previous103_preparation_STOP_pin']=dict(m.PREPARATION103_STOP,bytes=1);self.reject()
    def test_guarded_qualification_drift(self):self.doc['guarded_contract_qualification_pin']=dict(m.GUARDED_QUALIFIER,bytes=1);self.reject()
    def test_failed_status_support_not_PIN(self):self.doc['previous_status_STOP_pin']=dict(m.STATUS_STOP,bytes=1);self.reject()
    def test_helper_reuse_not_new_execution(self):self.doc['reused_helper_contract_executions']=0;self.reject()
    def test_per_test_checkpoint_not_selected(self):self.doc['per_test_original_checkpoint_selected']=False;self.reject()
    def test_previous103_not_reviewed(self):self.doc['previous103_STOP_reviewed']=False;self.reject()
    def test_missing_before_test_checkpoint(self):self.doc['contract_checkpoint_statistics']['successful_before_test_checks']-=1;self.reject()
    def test_missing_after_test_checkpoint(self):self.doc['contract_checkpoint_statistics']['successful_after_test_checks']-=1;self.reject()
    def test_contract_new_thread_forbidden(self):self.doc['contract_checkpoint_statistics']['new_sampler_or_thread_or_sleep_started']=True;self.reject()
    def test_runner_not_returned(self):self.doc['contract_checkpoint_statistics']['returned_runner_calls']=4;self.reject()
    def test_full_helper_code_omitted(self):self.baseline.pop(m.guarded.SELF);self.reject()

    def test_compact_qualification_pin_drift(self):self.doc['compact_qualification_pin']=dict(m.COMPACT_QUALIFIER,bytes=1);self.reject()
    def test_compact_status_pin_drift(self):self.doc['compact_status_pin']=dict(m.COMPACT_STATUS,bytes=1);self.reject()
    def test_compact_selected_false(self):self.doc['compact_checkpoint_selected']=False;self.reject()
    def test_compact_policy_changed(self):self.doc['compact_checkpoint_policy']['original_guards_and_reader_and_rates_preserved']=False;self.reject()
    def test_compact_reuse_count_changed(self):self.doc['reused_compact_contract_executions']=0;self.reject()
    def test_old_guard_reuse_not_new_execution(self):self.doc['runtime_contract_executions']+=78;self.reject()
    def test_old_guard_reuse_count_changed(self):self.doc['reused_original_guard_contract_executions']=0;self.reject()
    def test_old_guard_qualification_drift(self):self.doc['reused_original_guard_qualification_root_pin']=dict(m.compact.ROOT,bytes=1);self.reject()
    def test_compact_source_omitted(self):self.added.pop(m.compact.SELF);self.reject()
    def test_compact_test_omitted(self):self.added.pop(m.compact.TEST);self.reject()
    def test_baseline1644_not_subset(self):self.baseline.pop(m.guarded.TEST);self.reject()
    def test_do_not_claim_five_new_runners(self):self.doc['contract_checkpoint_statistics']['runner_calls']=5;self.reject()
if __name__=='__main__':unittest.main()
