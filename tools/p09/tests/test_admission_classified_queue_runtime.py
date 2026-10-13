"""P335 explicit synthetic current/following full1654. 테스트 자료는 실제 수용 증거 아님."""
import copy
import unittest
import resume_admission_classified_queue_runtime as m
FIXTURES=None
FOLLOWING=False
PRIOR_STOP=None
TEMPLATE=None
from types import SimpleNamespace
from unittest.mock import Mock

def fixture():
    global TEMPLATE
    if TEMPLATE is None:TEMPLATE=build_template()
    return copy.deepcopy(TEMPLATE)

def build_template():
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
    pin=dict(doc['case_receipt_pin'],path=f'{m.p.DIR}/cases/p335-case-{index:03}-run001.json')
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
        stop_resume_policy=copy.deepcopy(m.STOP_POLICY),prior323_STOP_pin=m.PRIOR323_STOP,
        prior323_status_pin=m.PRIOR323_STATUS,reused_prior323_contract_executions=268,
        previous104_STOP_pin=m.PRIOR104,previous104_STOP_review_pin=m.PRIOR104_REVIEW,
        previous104_STOP_status_pin=m.PRIOR104_STATUS,previous104_STOP_reviewed=True,
        reused_previous104_contract_executions=200,parent_return_record_policy=copy.deepcopy(m.RETURN_POLICY),
        parent_return_status_recorded_before_after_parent_guard=True,original_parent_return_code=0,
        original_parent_pending_failure_before_after_parent_guard=False,
        original_parent_rejected_failure_before_after_parent_guard=False,original_parent_STOP_captured_not_accepted=False,
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
        startup_limits=copy.deepcopy(m.STARTUP_LIMITS),scope_budget=m.budget(required,baseline,added),scope_added_ten_pins=copy.deepcopy(list(added.values())),
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
    def test_new_scope_added_pin_drift(self):self.doc['scope_added_ten_pins'][0]['sha256']='b'*64;self.reject()
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

    def test_prior104_stop_pin_drift(self):self.doc['previous104_STOP_pin']=dict(m.PRIOR104,bytes=1);self.reject()
    def test_prior104_review_pin_drift(self):self.doc['previous104_STOP_review_pin']=dict(m.PRIOR104_REVIEW,bytes=1);self.reject()
    def test_prior104_status_pin_drift(self):self.doc['previous104_STOP_status_pin']=dict(m.PRIOR104_STATUS,bytes=1);self.reject()
    def test_prior104_not_reviewed(self):self.doc['previous104_STOP_reviewed']=False;self.reject()
    def test_prior200_not_counted_as_current(self):self.doc['runtime_contract_executions']+=200;self.reject()
    def test_prior200_reuse_count(self):self.doc['reused_previous104_contract_executions']=0;self.reject()
    def test_return_policy_guard_replaced(self):self.doc['parent_return_record_policy']['original_after_parent_guard_called_once_without_replacement']=False;self.reject()
    def test_parent_return_not_recorded(self):self.doc['parent_return_status_recorded_before_after_parent_guard']=False;self.reject()
    def test_return_code_not_bool_zero(self):self.doc['original_parent_return_code']=False;self.reject()
    def test_return_failed_not_accept(self):self.doc['original_parent_return_code']=2;self.reject()
    def test_pending_not_accept(self):self.doc['original_parent_pending_failure_before_after_parent_guard']=True;self.reject()
    def test_rejected_not_accept(self):self.doc['original_parent_rejected_failure_before_after_parent_guard']=True;self.reject()
    def test_captured_STOP_not_accept(self):self.doc['original_parent_STOP_captured_not_accepted']=True;self.reject()
    def test_prior_runtime_code_scope_kept(self):self.added.pop(m.prior_runtime.SELF);self.reject()
    def test_prior_runtime_test_scope_kept(self):self.added.pop(m.prior_runtime.TEST);self.reject()
    def stop_rows(self):
        if PRIOR_STOP is None:raise RuntimeError('FRESH_STOP_FIXTURES_REQUIRED')
        return copy.deepcopy(PRIOR_STOP)
    def stop_reject(self,field,key,value):
        rows=self.stop_rows();rows[field][key]=value
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.prior104_contract(*rows)
    def test_exact_prior104_is_failed_not_acceptance(self):self.assertIs(m.prior104_contract(*self.stop_rows()),True)
    def test_prior104_fake_pass(self):self.stop_reject(0,'state',m.prior_runtime.PASS)
    def test_prior104_cleanup_missing(self):self.stop_reject(0,'resource_watcher_cleanup_confirmed',False)
    def test_prior104_missing_CPU_STOP(self):self.stop_reject(0,'resource_stop_reason',None)
    def test_prior104_acceptance_fabricated(self):self.stop_reject(0,'accepted_exact_product_body_count',1)
    def test_prior104_product_started(self):self.stop_reject(1,'actual_product_child_executed',True)
    def test_prior104_nonempty_owned_tree(self):self.stop_reject(1,'owned_tree_empty',False)
    def test_prior104_full_native_fabricated(self):self.stop_reject(3,'full1648_two_byte_Native_qualification_completed',True)
    def test_prior104_status_acceptance_fabricated(self):self.stop_reject(3,'new_runtime_cases_accepted',1)
    def test_prior104_review_incomplete(self):
        rows=self.stop_rows();rows[2]['IO']['finished']=False
        with self.assertRaises(ValueError):m.prior104_contract(*rows)
    def test_prior104_open_handle_remains(self):
        rows=self.stop_rows();rows[0]['terminal_source_frame']['handles']['input_lock_handles_remaining']=1
        with self.assertRaises(ValueError):m.prior104_contract(*rows)
    def test_prior104_duplicate_remains(self):
        rows=self.stop_rows();rows[0]['terminal_source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1
        with self.assertRaises(ValueError):m.prior104_contract(*rows)
    def test_prior104_partial_cannot_be_full(self):
        rows=self.stop_rows();rows[1]['owned_source_reader_passes'][0]['read_passes']=1648
        with self.assertRaises(ValueError):m.prior104_contract(*rows)
    def test_return_recorded_before_original_STOP(self):
        out={};capture=SimpleNamespace(pending={'state':'DEFERRED_NOT_STARTED'},rejected=None)
        error=ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        def check(label):
            self.assertEqual(label,'after_parent');self.assertIs(out['original_parent_STOP_captured_not_accepted'],True)
            self.assertEqual(out['original_parent_return_code'],2);raise error
        held=SimpleNamespace(mark=Mock(side_effect=check))
        with self.assertRaises(ValueError) as caught:m.record_return_before_original_guard(out,capture,2,held)
        self.assertIs(caught.exception,error);held.mark.assert_called_once_with('after_parent')
    def test_success_record_calls_same_guard_once(self):
        out={};held=SimpleNamespace(mark=Mock());capture=SimpleNamespace(pending=None,rejected=None)
        m.record_return_before_original_guard(out,capture,0,held);held.mark.assert_called_once_with('after_parent')
        self.assertIs(out['original_parent_STOP_captured_not_accepted'],False);self.assertEqual(out['original_parent_return_code'],0)
    def test_rejected_return_record_retained(self):
        out={};held=SimpleNamespace(mark=Mock());capture=SimpleNamespace(pending=None,rejected={'state':'FAILED'})
        m.record_return_before_original_guard(out,capture,2,held)
        self.assertIs(out['original_parent_rejected_failure_before_after_parent_guard'],True)
        self.assertIs(out['original_parent_pending_failure_before_after_parent_guard'],False)
    def test_KeyboardInterrupt_guard_not_swallowed(self):
        out={};error=KeyboardInterrupt();held=SimpleNamespace(mark=Mock(side_effect=error))
        with self.assertRaises(KeyboardInterrupt) as caught:
            m.record_return_before_original_guard(out,SimpleNamespace(pending=None,rejected=None),0,held)
        self.assertIs(caught.exception,error);self.assertIs(out['parent_return_status_recorded_before_after_parent_guard'],True)
    def test_capture_booleans_not_full_private_receipt(self):
        token={'private_original_evidence':object()};out={};held=SimpleNamespace(mark=Mock())
        m.record_return_before_original_guard(out,SimpleNamespace(pending=token,rejected=token),2,held)
        self.assertTrue(all(type(out[k]) is bool for k in ('original_parent_pending_failure_before_after_parent_guard',
            'original_parent_rejected_failure_before_after_parent_guard','original_parent_STOP_captured_not_accepted')))
    def test_return_before_guard_no_other_IO(self):
        out={};held=SimpleNamespace(mark=Mock())
        with unittest.mock.patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
                unittest.mock.patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')), \
                unittest.mock.patch('builtins.open',side_effect=AssertionError('NO_OPEN')):
            m.record_return_before_original_guard(out,SimpleNamespace(pending=None,rejected=None),0,held)
        held.mark.assert_called_once_with('after_parent')


    def test_prior323_pin_drift(self):self.doc['prior323_STOP_pin']=dict(m.PRIOR323_STOP,bytes=1);self.reject()
    def test_prior323_status_drift(self):self.doc['prior323_status_pin']=dict(m.PRIOR323_STATUS,bytes=1);self.reject()
    def test_prior268_reuse_not_new_execution(self):self.doc['runtime_contract_executions']+=268;self.reject()
    def test_prior268_reuse_count(self):self.doc['reused_prior323_contract_executions']=0;self.reject()
    def test_stable_policy_requires_review(self):self.doc['stop_resume_policy']['explicit_independent_review_pin_required']=False;self.reject()
    def test_prior323_source_kept(self):self.added.pop(m.prior323.SELF);self.reject()
    def test_prior323_test_kept(self):self.added.pop(m.prior323.TEST);self.reject()
    def synthetic_stop(self):
        d=copy.deepcopy(self.doc)
        d.update(state='FAILED_NOT_ACCEPTED',error_code='STOP_SUSTAINED_SYSTEM_CPU',
            resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',accepted_exact_product_body_count=0,
            actual_product_child_executed=False,original_parent_capture_adapter_selected=False,
            diagnostic_parent_connection_selected=False,parent_return_status_recorded_before_after_parent_guard=False,
            failure_diagnostic={'stage':'source_frame_acquire'},
            case_receipt_path=self.pin['path'],terminal_parent_failure_sidecar_pin=None)
        d['terminal_source_frame']=copy.deepcopy(d['closing_component']['source_frame'])
        f=d['terminal_source_frame'];f.update(frame_state='CLOSED',registered_live_frame=False,
            actual_byte_boundaries=[],held_identity_after_owned_cleanup=None)
        h=f['handles'];h.update(input_lock_handles_opened=194,input_lock_handles_closed=194,
            input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,
            active_reader_bindings=0,active_byte_streams=0,borrowed_byte_streams=None)
        h['acquisition_phase_pressure']['acquisition_complete']=False
        return d
    def stopped(self,d,side=None):
        return m.stopped_before_product(d,self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names,side)
    def stable_codes(self):return list(m.FROZEN89)+[self.added[m.SELF],self.added[m.TEST]]
    def synthetic_review(self,d):
        rootpin=dict(path=m.p.DIR+f'/p335-case-{d["selected_test_index"]:03}-run001.v1.json',bytes=1,sha256='a'*64)
        review=dict(schema_version=m.REVIEW_SCHEMA,state=m.REVIEW_PASS,reviewed_root_pin=copy.deepcopy(rootpin),
            stop_resume_policy=copy.deepcopy(m.STOP_POLICY),runtime_plan_at_review=copy.deepcopy(self.base),
            current91_metadata_code_pins=self.stable_codes(),resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
            preparation_IO=dict(finished=True,bound_inputs=100,final_fresh_hashes=100),
            accepted_exact_product_body_count=0,actual_product_child_executed=False,
            actual_Native_or_product_started_in_review=False,contract_tests_reexecuted_in_review=False,
            reviewed_failure_classification=self.stopped(d),reviewed_body_placeholder_pin=None)
        return rootpin,review
    def test_exact_stop_not_advance(self):
        result=self.stopped(self.synthetic_stop());self.assertEqual(result['accepted_count_delta'],0)
        self.assertIs(result['actual_product_reexecution_authorized'],False)
    def test_stop_cannot_be_pass(self):
        d=self.synthetic_stop();d['state']=m.PASS
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_cannot_accept_one(self):
        d=self.synthetic_stop();d['accepted_exact_product_body_count']=1
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_wrong_reason(self):
        d=self.synthetic_stop();d['resource_stop_reason']='STOP_RESOURCE_MEMORY'
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_unknown_phase(self):
        d=self.synthetic_stop();d['failure_diagnostic']['stage']='unknown'
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_post_product_no_retry(self):
        d=self.synthetic_stop();d['failure_diagnostic']['stage']='source_frame_closing'
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_product_already_executed(self):
        d=self.synthetic_stop();d['actual_product_child_executed']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_wrong_plan(self):
        d=self.synthetic_stop();d['prior_runtime_plan']['next_runtime_index']+=1
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_missing_selected_case(self):
        d=self.synthetic_stop();d['selected_test_index']=None
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_missing_frame(self):
        d=self.synthetic_stop();d.pop('terminal_source_frame')
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_open_handle(self):
        d=self.synthetic_stop();d['terminal_source_frame']['handles']['input_lock_handles_remaining']=1
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_partial_close(self):
        d=self.synthetic_stop();d['terminal_source_frame']['handles']['input_lock_handles_closed']=193
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_frame_registered(self):
        d=self.synthetic_stop();d['terminal_source_frame']['registered_live_frame']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_scope_subset(self):
        d=self.synthetic_stop();d['terminal_source_frame']['input_count']-=1
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_early_parent_flag(self):
        d=self.synthetic_stop();d['original_parent_capture_adapter_selected']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_stop_owned_unknown_sidecar(self):
        d=self.synthetic_stop();d['failure_diagnostic']['stage']='owned_parent'
        with self.assertRaises(ValueError):self.stopped(d)
    def test_exact_independent_review_is_not_acceptance(self):
        d=self.synthetic_stop();pin,review=self.synthetic_review(d)
        result=m.review_contract(review,pin,d,self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names,self.stable_codes())
        self.assertEqual(result['accepted_count_delta'],0)
    def review_reject(self,key,value):
        d=self.synthetic_stop();pin,review=self.synthetic_review(d);review[key]=value
        with self.assertRaises((ValueError,KeyError)):
            m.review_contract(review,pin,d,self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names,self.stable_codes())
    def test_failed_review_no_GO(self):self.review_reject('state','FAILED_NOT_ACCEPTED')
    def test_review_different_root(self):self.review_reject('reviewed_root_pin',dict(path='other',bytes=1,sha256='a'*64))
    def test_review_unclean(self):self.review_reject('resource_watcher_cleanup_confirmed',False)
    def test_review_STOP(self):self.review_reject('resource_stop_reason','STOP_SUSTAINED_SYSTEM_CPU')
    def test_review_changed_code(self):self.review_reject('current91_metadata_code_pins',[])
    def test_review_native_started(self):self.review_reject('actual_Native_or_product_started_in_review',True)
    def test_review_product_claim(self):self.review_reject('actual_product_child_executed',True)
    def test_review_acceptance_claim(self):self.review_reject('accepted_exact_product_body_count',1)
    def test_review_incomplete_fresh(self):self.review_reject('preparation_IO',dict(finished=False,bound_inputs=100,final_fresh_hashes=1))
    def test_review_classification_forged(self):self.review_reject('reviewed_failure_classification',dict(accepted_count_delta=1))
    def test_exact_root_pin_argument(self):
        p=dict(path=m.p.DIR+'/p335-case-104-run001.v1.json',bytes=1,sha256='a'*64)
        self.assertEqual(m.pin_argument(p),p)
    def test_root_pin_path_escape(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path='../p335-case-104-run001.v1.json',bytes=1,sha256='a'*64))
    def test_root_pin_bool_size(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p335-case-104-run001.v1.json',bytes=True,sha256='a'*64))
    def test_root_pin_hash_invalid(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p335-case-104-run001.v1.json',bytes=1,sha256='z'*64))
    def test_approval_pin_must_review_namespace(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p335-case-104-run001.v1.json',bytes=1,sha256='a'*64),True)
    def test_zero_placeholder_nonzero_rejected(self):
        d=self.synthetic_stop();q=SimpleNamespace(pin=lambda name:dict(path=name,bytes=1,sha256='a'*64))
        with unittest.mock.patch('pathlib.Path.exists',return_value=True):
            with self.assertRaises(ValueError):m.zero_placeholder(q,d)
    def test_zero_placeholder_preserved(self):
        d=self.synthetic_stop();pin=dict(path=d['case_receipt_path'],bytes=0,sha256=m.hashlib.sha256(b'').hexdigest())
        q=SimpleNamespace(pin=Mock(return_value=pin))
        with unittest.mock.patch('pathlib.Path.exists',return_value=True):
            self.assertEqual(m.zero_placeholder(q,d),pin)
        q.pin.assert_called_once_with(d['case_receipt_path'])
    def test_absent_placeholder_not_created(self):
        d=self.synthetic_stop();q=SimpleNamespace(pin=Mock(side_effect=AssertionError('NO_READ')))
        with unittest.mock.patch('pathlib.Path.exists',return_value=False):self.assertIsNone(m.zero_placeholder(q,d))
        q.pin.assert_not_called()
    def queue_fixture(self,approval=True):
        d=self.synthetic_stop();pin,review=self.synthetic_review(d)
        path=m.p.c.ROOT/pin['path'];codes=self.stable_codes()
        snapshots={p['path']:p for p in codes};snapshots[pin['path']]=pin
        q=SimpleNamespace(json=Mock(return_value=d),reader=SimpleNamespace(snapshots=snapshots))
        ap=dict(path=m.p.DIR+'/p335-stop-review-run002.v1.json',bytes=1,sha256='b'*64)
        approvals={pin['path']:(ap,review)} if approval else {}
        def glob(obj,pattern):return [path] if pattern=='p335-case-*-run*.v1.json' else []
        return q,pin,approvals,glob
    def test_unreviewed_failure_blocks_GO(self):
        q,pin,approved,glob=self.queue_fixture(False)
        with unittest.mock.patch('pathlib.Path.glob',autospec=True,side_effect=glob):
            with self.assertRaises(ValueError):m.progress(q,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def test_reviewed_failure_cursor_unchanged(self):
        q,pin,approved,glob=self.queue_fixture()
        with unittest.mock.patch('pathlib.Path.glob',autospec=True,side_effect=glob),unittest.mock.patch('pathlib.Path.exists',return_value=False):
            plan=m.progress(q,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,approved)
        self.assertEqual(plan,self.base)
    def test_target_review_only_cursor_unchanged(self):
        q,pin,approved,glob=self.queue_fixture(False)
        with unittest.mock.patch('pathlib.Path.glob',autospec=True,side_effect=glob),unittest.mock.patch('pathlib.Path.exists',return_value=False):
            plan,target=m.progress(q,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,{},pin)
        self.assertEqual(plan,self.base);self.assertEqual(target[0],pin)
    def test_review_pin_root_hash_drift_rejected(self):
        q,pin,approved,glob=self.queue_fixture();approved[pin['path']][1]['reviewed_root_pin']['sha256']='b'*64
        with unittest.mock.patch('pathlib.Path.glob',autospec=True,side_effect=glob):
            with self.assertRaises(ValueError):m.progress(q,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,approved)
    def test_unused_review_rejected(self):
        q,pin,approved,glob=self.queue_fixture()
        with unittest.mock.patch('pathlib.Path.glob',return_value=[]):
            with self.assertRaises(ValueError):m.progress(q,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,approved)
    def test_review_pin_count_bounded(self):
        q=SimpleNamespace();codes=self.stable_codes()
        with self.assertRaises(ValueError):m.review_approvals(q,[{}]*65,codes)

    def synthetic_defer(self):
        d=self.synthetic_stop()
        d.update(error_code='DEFERRED_ALREADY_SATURATED_SYSTEM',resource_stop_reason=None,
            failure_diagnostic=dict(stage='admission',exception_class='ValueError',diagnostic_not_acceptance=True),
            per_test_original_checkpoint_selected=False,compound_anchor_verified_without_body_reexecution=False,
            metadata_entry_pressure_connection_selected=False,early_source_guard_connected=False,
            native_timing_connected=False,acquisition_phase_connection_selected=False,
            aggregate_post_reader_connection_verified=False)
        for key in ('preparation_IO','bound_preparation_input_pins','terminal_source_frame','case_receipt_path',
            'case_receipt_pin','terminal_metadata_IO','closing_component','runtime_plan','prior_runtime_plan',
            'terminal_parent_failure_sidecar_pin','selected_test_name','scope_budget','selected_test_index','runtime_contract_executions'):
            d.pop(key,None)
        row=dict(system_cpu_percent=100.0,phase_at_sample='admission',phases_since_previous_sample=['admission'],
            reader_counters_observed=False,audited_logical_read_bytes=None,audited_logical_read_passes=None,
            audited_logical_read_bytes_delta=None)
        d['metadata_observation']=dict(samples=[row],completed_sample_count=1,new_sampler_thread_started=False)
        return d
    def defer_reject(self,key,value):
        d=self.synthetic_defer();d[key]=value
        with self.assertRaises((ValueError,KeyError)):self.stopped(d)
    def test_exact_admission_defer_preserves_null_and_cursor(self):
        d=self.synthetic_defer();result=self.stopped(d)
        self.assertEqual(result['failure_kind'],'ADMISSION_NO_WORK_DEFERRAL')
        self.assertIsNone(result['original_resource_stop_reason']);self.assertEqual(result['accepted_count_delta'],0)
    def test_hard_stop_kept_distinct(self):
        result=self.stopped(self.synthetic_stop());self.assertEqual(result['failure_kind'],'SUSTAINED_CPU_STOP')
        self.assertEqual(result['original_resource_stop_reason'],'STOP_SUSTAINED_SYSTEM_CPU')
    def test_defer_cannot_have_hard_reason(self):self.defer_reject('resource_stop_reason','STOP_SUSTAINED_SYSTEM_CPU')
    def test_defer_wrong_phase(self):self.defer_reject('failure_diagnostic',dict(stage='owned_parent',exception_class='ValueError',diagnostic_not_acceptance=True))
    def test_defer_cleanup_required(self):self.defer_reject('resource_watcher_cleanup_confirmed',False)
    def test_defer_contract_started(self):self.defer_reject('runtime_contract_executions',1)
    def test_defer_reader_started(self):self.defer_reject('preparation_IO',{})
    def test_defer_native_started(self):self.defer_reject('terminal_source_frame',None)
    def test_defer_body_started(self):self.defer_reject('case_receipt_path','somewhere')
    def test_defer_selected_index(self):self.defer_reject('selected_test_index',104)
    def test_defer_parent_sidecar(self):self.defer_reject('terminal_parent_failure_sidecar_pin',None)
    def test_defer_gate_claim(self):self.defer_reject('P09_gate','PASS')
    def test_defer_freeze_claim(self):self.defer_reject('PC_freeze_resolved',True)
    def test_defer_partial_counter(self):
        d=self.synthetic_defer();d['metadata_observation']['samples'][0]['reader_counters_observed']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_defer_low_cpu_not_saturation(self):
        d=self.synthetic_defer();d['metadata_observation']['samples'][0]['system_cpu_percent']=97
        with self.assertRaises(ValueError):self.stopped(d)
    def test_defer_nonfinite_cpu(self):
        d=self.synthetic_defer();d['metadata_observation']['samples'][0]['system_cpu_percent']=float('nan')
        with self.assertRaises(ValueError):self.stopped(d)
    def test_defer_bool_cpu(self):
        d=self.synthetic_defer();d['metadata_observation']['samples'][0]['system_cpu_percent']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_defer_no_new_sampler(self):
        d=self.synthetic_defer();d['metadata_observation']['new_sampler_thread_started']=True
        with self.assertRaises(ValueError):self.stopped(d)
    def test_defer_independent_review_classification(self):
        d=self.synthetic_defer();rp,review=self.synthetic_review(self.synthetic_stop())
        rp=dict(rp,path=m.p.DIR+'/p335-admission-run001.v1.json')
        review.update(reviewed_root_pin=rp,reviewed_failure_classification=self.stopped(d))
        result=m.review_contract(review,rp,d,self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names,self.stable_codes())
        self.assertEqual(result['failure_kind'],'ADMISSION_NO_WORK_DEFERRAL')
    def fake_startup(self,mask=0x14,apply=True,priority=0x4000,drift=False):
        class Function:
            def __init__(self,fn):self.fn=fn
            def __call__(self,*args):return self.fn(*args)
        state=dict(mask=mask);handle=object();events=[]
        def affinity(h,process,system):
            self.assertIs(h,handle);process._obj.value=state['mask'];system._obj.value=0xffff;events.append('get');return 1
        def setmask(h,value):
            self.assertIs(h,handle);events.append('mask');state['mask']=mask if drift else value;return apply
        def setpriority(h,value):self.assertIs(h,handle);self.assertEqual(value,0x4000);events.append('priority');return apply
        kernel=SimpleNamespace(GetCurrentProcess=Function(lambda:handle),GetProcessAffinityMask=Function(affinity),
            SetProcessAffinityMask=Function(setmask),SetPriorityClass=Function(setpriority),GetPriorityClass=Function(lambda h:priority))
        return kernel,events
    def test_startup_uses_one_allowed_core_and_readback(self):
        kernel,events=self.fake_startup();result=m.own_startup_limits(kernel)
        self.assertEqual(result['own_affinity_mask'],4);self.assertEqual(events,['get','mask','priority','get'])
        self.assertIs(result['foreign_process_modified'],False)
    def test_startup_zero_allowed_denies(self):
        kernel,_=self.fake_startup(mask=0)
        with self.assertRaises(ValueError):m.own_startup_limits(kernel)
    def test_startup_apply_failure_denies(self):
        kernel,_=self.fake_startup(apply=False)
        with self.assertRaises(ValueError):m.own_startup_limits(kernel)
    def test_startup_affinity_drift_denies(self):
        kernel,_=self.fake_startup(drift=True)
        with self.assertRaises(ValueError):m.own_startup_limits(kernel)
    def test_startup_priority_readback_denies(self):
        kernel,_=self.fake_startup(priority=0x20)
        with self.assertRaises(ValueError):m.own_startup_limits(kernel)
    def test_startup_limits_required_in_pass(self):self.doc['startup_limits']={};self.reject()


    def test_warm_duplicate_keys_denied(self):
        with self.assertRaises(ValueError):m.session_request('{"id":"a","mode":"light","run":1,"run":2}')
    def test_warm_unknown_shell_denied(self):
        with self.assertRaises(ValueError):m.session_request('{"id":"a","mode":"shell","run":1}')
    def test_warm_unknown_key_denied(self):
        with self.assertRaises(ValueError):m.session_request('{"id":"a","mode":"light","run":1,"cmd":"none"}')
    def test_warm_line_size_bounded(self):
        with self.assertRaises(ValueError):m.session_request(' '*65537)
    def test_warm_run_bool_denied(self):
        with self.assertRaises(ValueError):m.session_request('{"id":"a","mode":"light","run":true}')
    def test_warm_actual_needs_first_light(self):
        output=[];runner=Mock()
        code=m.serve(lambda size:'{"id":"a","mode":"actual","run":1}',output.append,runner)
        self.assertEqual(code,2);runner.assert_not_called()
    def test_warm_eof_no_command_no_resource(self):
        output=[];runner=Mock()
        self.assertEqual(m.serve(lambda size:'',output.append,runner),0);runner.assert_not_called()
    def test_warm_quit_no_resource(self):
        output=[];runner=Mock()
        self.assertEqual(m.serve(lambda size:'{"id":"a","mode":"quit"}',output.append,runner),0);runner.assert_not_called()
    def test_warm_same_current_code_guard(self):
        pins=self.stable_codes();q=SimpleNamespace(reader=SimpleNamespace(snapshots={p['path']:p for p in pins}))
        with unittest.mock.patch.object(m,'WARM_EXPECTED_CODE',pins):m.warm_code_guard(q)
    def test_warm_code_drift_denies_before_GO(self):
        pins=self.stable_codes();snapshots={p['path']:copy.deepcopy(p) for p in pins};snapshots[m.SELF]['sha256']='f'*64
        q=SimpleNamespace(reader=SimpleNamespace(snapshots=snapshots))
        with unittest.mock.patch.object(m,'WARM_EXPECTED_CODE',pins):
            with self.assertRaises(ValueError):m.warm_code_guard(q)
    def test_warm_safe_admission_has_no_code_qualification(self):
        d=self.synthetic_defer();summary=m.terminal_session_summary(d,'admission')
        self.assertIs(summary['safe_to_wait_without_live_resources'],True);self.assertIsNone(summary['current_code_pins'])
    def test_warm_uncertain_native_failure_closes(self):
        summary=m.terminal_session_summary(self.synthetic_stop(),'source_frame_acquire')
        self.assertIs(summary['safe_to_wait_without_live_resources'],False)
    def test_warm_live_watcher_closes(self):
        d=self.synthetic_defer();d['resource_watcher_cleanup_confirmed']=False
        self.assertIs(m.terminal_session_summary(d,'admission')['safe_to_wait_without_live_resources'],False)
    def test_warm_light_then_actual_once_no_auto_retry(self):
        lines=iter(['{"id":"l","mode":"light","run":1}','{"id":"r","mode":"light-review","run":2}',
            '{"id":"a","mode":"actual","run":3}','{"id":"q","mode":"quit"}'])
        output=[];calls=[]
        def run(argv):
            calls.append(argv);m.LAST_TERMINAL=dict(state=m.LIGHT if len(calls)==1 else m.LIGHT_REVIEW_PASS if len(calls)==2 else m.PASS,
                resource_watcher_cleanup_confirmed=True,safe_to_wait_without_live_resources=True,
                current_code_pins=self.stable_codes() if len(calls)<=2 else None)
            return 0
        self.assertEqual(m.serve(lambda size:next(lines,''),output.append,run),0);self.assertEqual(len(calls),3)
        self.assertIsNone(m.WARM_EXPECTED_CODE);self.assertIsNone(m.LAST_TERMINAL)
    def test_warm_missing_terminal_closes(self):
        output=[];self.assertEqual(m.serve(lambda size:'{"id":"l","mode":"light","run":1}',output.append,lambda argv:0),2)
    def test_warm_closes_after_uncertain_cleanup(self):
        output=[];calls=[]
        def run(argv):
            calls.append(argv);m.LAST_TERMINAL=dict(state='FAILED_NOT_ACCEPTED',
                safe_to_wait_without_live_resources=False,current_code_pins=None)
            return 2
        self.assertEqual(m.serve(lambda size:'{"id":"l","mode":"light","run":1}',output.append,run),2)
        self.assertEqual(len(calls),1)
    def test_warm_terminal_summary_no_full_samples_retained(self):
        summary=m.terminal_session_summary(self.synthetic_defer(),'admission')
        self.assertNotIn('metadata_observation',summary);self.assertNotIn('terminal_source_frame',summary)

    def test_warm_review_before_light_never_authorizes_actual(self):
        pin=dict(path=m.p.DIR+'/p335-admission-run001.v1.json',bytes=1,sha256='a'*64)
        lines=iter([m.json.dumps(dict(id='r',mode='stop-review',run=2,stop_root_pin=pin)),
            '{"id":"a","mode":"actual","run":3}'])
        calls=[];output=[]
        def run(argv):
            calls.append(argv);m.LAST_TERMINAL=dict(state=m.REVIEW_PASS,safe_to_wait_without_live_resources=True,current_code_pins=None)
            return 0
        self.assertEqual(m.serve(lambda size:next(lines,''),output.append,run),2);self.assertEqual(len(calls),1)

    def test_failed_first_light_pin_reviewable_but_not_approval_pin(self):
        pin=dict(path=m.p.DIR+'/p335-light-run001.v1.json',bytes=1,sha256='a'*64)
        self.assertEqual(m.pin_argument(pin),pin)
        with self.assertRaises(ValueError):m.pin_argument(pin,True)

    def test_warm_isolation_restores_outer_live_qualification(self):
        expected=object();reviewed=object();terminal=object()
        with unittest.mock.patch.object(m,'WARM_EXPECTED_CODE',expected),unittest.mock.patch.object(m,'WARM_REVIEWED_CODE',reviewed),unittest.mock.patch.object(m,'LAST_TERMINAL',terminal):
            with m.WarmTestIsolation():self.assertEqual(m.serve(lambda size:'',lambda line:None,Mock()),0)
            self.assertIs(m.WARM_EXPECTED_CODE,expected);self.assertIs(m.WARM_REVIEWED_CODE,reviewed);self.assertIs(m.LAST_TERMINAL,terminal)
    def test_warm_isolation_exception_restores_outer_state(self):
        expected=object()
        with unittest.mock.patch.object(m,'WARM_EXPECTED_CODE',expected):
            with self.assertRaises(ValueError):
                with m.WarmTestIsolation():
                    m.WARM_EXPECTED_CODE=None;raise ValueError('SYNTHETIC_STOP')
            self.assertIs(m.WARM_EXPECTED_CODE,expected)
    def test_warm_actual_requires_independent_current_review(self):
        lines=iter(['{"id":"l","mode":"light","run":1}','{"id":"a","mode":"actual","run":2}']);calls=[];out=[]
        def run(argv):
            calls.append(argv);m.LAST_TERMINAL=dict(state=m.LIGHT,safe_to_wait_without_live_resources=True,current_code_pins=self.stable_codes());return 0
        self.assertEqual(m.serve(lambda size:next(lines,''),out.append,run),2);self.assertEqual(len(calls),1)
    def test_warm_review_existing_light_does_not_reexecute_contracts(self):
        lines=iter(['{"id":"r","mode":"light-review","run":1}','{"id":"a","mode":"actual","run":2}','{"id":"q","mode":"quit"}'])
        calls=[];out=[]
        def run(argv):
            calls.append(argv);m.LAST_TERMINAL=dict(state=m.LIGHT_REVIEW_PASS if len(calls)==1 else m.PASS,
                safe_to_wait_without_live_resources=True,current_code_pins=self.stable_codes() if len(calls)==1 else None);return 0
        self.assertEqual(m.serve(lambda size:next(lines,''),out.append,run),0);self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][:2],['--mode','light-review'])
    def synthetic_light_pair(self):
        codes=self.stable_codes();light=copy.deepcopy(self.doc)
        light.update(state=m.LIGHT,accepted_exact_product_body_count=0,actual_product_child_executed=False,
            bound_preparation_input_pins=copy.deepcopy(codes))
        light.pop('terminal_source_frame',None);light.pop('closing_component',None)
        pin=dict(path=m.p.DIR+'/p335-light-run001.v1.json',bytes=1,sha256='a'*64)
        review=copy.deepcopy(light)
        review.update(state=m.LIGHT_REVIEW_PASS,reviewed_light_pin=pin,current91_metadata_code_pins=codes,
            light_contract_executions_reused_not_executed=m.EXECUTED,contract_tests_reexecuted_in_review=False,
            preparation_IO=dict(finished=True,bound_inputs=100,final_fresh_hashes=100))
        review.pop('runtime_contract_executions')
        return review,light,pin,codes
    def test_light_fresh_review_no_product_or_contract_reexecution(self):
        args=self.synthetic_light_pair();self.assertIs(m.light_review_contract(*args),args[0])
    def test_light_review_incomplete_fresh_denies(self):
        args=self.synthetic_light_pair();args[0]['preparation_IO']['finished']=False
        with self.assertRaises(ValueError):m.light_review_contract(*args)
    def test_light_review_contract_replay_denies(self):
        args=self.synthetic_light_pair();args[0]['runtime_contract_executions']=m.EXECUTED
        with self.assertRaises(ValueError):m.light_review_contract(*args)
    def test_light_review_changed_code_denies(self):
        args=self.synthetic_light_pair();args[0]['current91_metadata_code_pins']=[]
        with self.assertRaises(ValueError):m.light_review_contract(*args)
    def test_light_review_product_claim_denies(self):
        args=self.synthetic_light_pair();args[0]['actual_product_child_executed']=True
        with self.assertRaises(ValueError):m.light_review_contract(*args)
    def test_light_review_false_acceptance_denies(self):
        args=self.synthetic_light_pair();args[0]['accepted_exact_product_body_count']=1
        with self.assertRaises(ValueError):m.light_review_contract(*args)
    def test_failed_light_review_pin_can_be_explicitly_reviewed(self):
        pin=dict(path=m.p.DIR+'/p335-light-review-run001.v1.json',bytes=1,sha256='a'*64)
        self.assertEqual(m.pin_argument(pin),pin)

    def test_template_clones_do_not_share_mutation(self):
        first=fixture();second=fixture()
        first[0]['binding']['whole_test_count']=99999
        self.assertNotEqual(first[0]['binding'],second[0]['binding'])
        self.assertEqual(second[0]['binding'],TEMPLATE[0]['binding'])
    def test_template_builder_once_per_bound_suite(self):
        with unittest.mock.patch(__name__+'.build_template',side_effect=AssertionError('NO_REBUILD')):
            first=fixture();second=fixture()
        self.assertEqual(first,second);self.assertIsNot(first[0],second[0])

    def test_terminal_unbound_validation_preserved_not_PASS(self):
        out=dict(state='FAILED_NOT_ACCEPTED',resource_watcher_cleanup_confirmed=True)
        owner=object();proposed=dict(state=m.LIGHT_REVIEW_PASS);validate=Mock()
        with unittest.mock.patch.object(m.g,'complete',side_effect=UnboundLocalError('synthetic local')):
            m.complete_runtime(out,owner,proposed,validate)
        self.assertEqual(out['state'],'FAILED_NOT_ACCEPTED')
        self.assertIs(out['terminal_validation_error_preserved_after_original_cleanup'],True)
        self.assertEqual(out['failure_diagnostic']['stage'],'terminal_validation')
    def test_terminal_original_complete_called_once_no_extra_cleanup(self):
        out={};owner=object();proposed=dict(state=m.LIGHT_REVIEW_PASS);validate=Mock()
        with unittest.mock.patch.object(m.g,'complete') as original:
            m.complete_runtime(out,owner,proposed,validate);original.assert_called_once_with(out,owner,proposed,validate)

    def idle_scope(self):return (self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names)
    def cpu_anchor_idle(self):
        d=self.synthetic_defer()
        d.update(error_code='STOP_SUSTAINED_SYSTEM_CPU',resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',
            failure_diagnostic=dict(stage='anchor'))
        return d
    def warm_failure_pin(self):
        return dict(path=m.p.DIR+'/p335-admission-run003.v1.json',bytes=123,sha256='a'*64)
    def test_closed_anchor_STOP_retains_idle_not_actual_code(self):
        d=self.cpu_anchor_idle();s=m.terminal_session_summary(d,'anchor',receipt_pin=self.warm_failure_pin())
        self.assertTrue(s['safe_to_wait_without_live_resources'])
        self.assertTrue(s['pre_product_idle_candidate_not_review_or_GO'])
        self.assertIsNone(s['current_code_pins']);self.assertEqual(s['failure_root_pin'],self.warm_failure_pin())
    def test_closed_partial_acquire_STOP_can_idle_without_retaining_locks(self):
        d=self.synthetic_stop()
        s=m.terminal_session_summary(d,'source_frame_acquire',scope=self.idle_scope(),receipt_pin=self.warm_failure_pin())
        self.assertTrue(s['safe_to_wait_without_live_resources']);self.assertNotIn('terminal_source_frame',s)
    def test_closed_owned_parent_idle_requires_original_no_worker_document(self):
        d=self.synthetic_stop();d['failure_diagnostic']['stage']='owned_parent'
        d['terminal_source_frame']['handles']['input_lock_handles_opened']=m.N+m.DIRECTORIES
        d['terminal_source_frame']['handles']['input_lock_handles_closed']=m.N+m.DIRECTORIES
        d['terminal_source_frame']['handles']['acquisition_phase_pressure']['acquisition_complete']=True
        d['terminal_parent_failure_sidecar_pin']=dict(path='already_original',bytes=1,sha256='a'*64)
        side=dict(state='DEFERRED_NOT_STARTED',actual_product_child_executed=False,exit_code=None,
            worker_created=False,job_assigned=False,owned_tree_empty=True,cleanup_confirmed=True,
            resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',stop_reason='STOP_SUSTAINED_SYSTEM_CPU')
        s=m.terminal_session_summary(d,'owned_parent',scope=self.idle_scope(),parent_document=side,receipt_pin=self.warm_failure_pin())
        self.assertTrue(s['safe_to_wait_without_live_resources'])
        for key in ('worker_created','job_assigned','actual_product_child_executed'):
            side[key]=True
            self.assertFalse(m.terminal_session_summary(d,'owned_parent',scope=self.idle_scope(),parent_document=side)['safe_to_wait_without_live_resources'])
            side[key]=False
    def test_warm_post_product_stop_always_closes(self):
        d=self.cpu_anchor_idle();d['failure_diagnostic']['stage']='post_reader_constructor'
        self.assertFalse(m.terminal_session_summary(d,'post_reader_constructor')['safe_to_wait_without_live_resources'])
    def test_warm_error_stage_mismatch_closes(self):
        self.assertFalse(m.terminal_session_summary(self.cpu_anchor_idle(),'admission')['safe_to_wait_without_live_resources'])
    def test_warm_STOP_product_claim_closes(self):
        d=self.cpu_anchor_idle();d['actual_product_child_executed']=True
        self.assertFalse(m.terminal_session_summary(d,'anchor')['safe_to_wait_without_live_resources'])
    def test_warm_STOP_acceptance_claim_closes(self):
        d=self.cpu_anchor_idle();d['accepted_exact_product_body_count']=1
        self.assertFalse(m.terminal_session_summary(d,'anchor')['safe_to_wait_without_live_resources'])
    def test_warm_other_resource_failure_closes(self):
        d=self.cpu_anchor_idle();d['resource_stop_reason']=d['error_code']='STOP_RAM'
        self.assertFalse(m.terminal_session_summary(d,'anchor')['safe_to_wait_without_live_resources'])
    def test_warm_bad_receipt_pin_closes(self):
        self.assertFalse(m.terminal_session_summary(self.cpu_anchor_idle(),'anchor',receipt_pin={})['safe_to_wait_without_live_resources'])
    def test_warm_unwritten_parent_diagnostic_closes(self):
        d=self.synthetic_stop();d['failure_diagnostic']['stage']='owned_parent'
        self.assertFalse(m.terminal_session_summary(d,'owned_parent',scope=self.idle_scope())['safe_to_wait_without_live_resources'])
    def test_warm_native_live_handle_cannot_idle(self):
        d=self.synthetic_stop();d['terminal_source_frame']['handles']['input_lock_handles_remaining']=1
        self.assertFalse(m.terminal_session_summary(d,'source_frame_acquire',scope=self.idle_scope())['safe_to_wait_without_live_resources'])
    def test_warm_failed_sidecar_cannot_idle(self):
        d=self.synthetic_stop();d['terminal_failure_write_error']='FAILED'
        self.assertFalse(m.terminal_session_summary(d,'source_frame_acquire',scope=self.idle_scope())['safe_to_wait_without_live_resources'])
    def cpu_stop_sequence(self,tail):
        pin=self.warm_failure_pin()
        seq=[dict(id='l',mode='light',run=1),dict(id='r',mode='light-review',run=2),dict(id='a',mode='actual',run=3)]+tail
        lines=iter([m.json.dumps(d) for d in seq]);calls=[];output=[];observed=[]
        def run(argv):
            mode=argv[1];calls.append(argv)
            if len(calls)==3:
                m.LAST_TERMINAL=dict(state='FAILED_NOT_ACCEPTED',safe_to_wait_without_live_resources=True,
                    current_code_pins=None,pre_product_idle_candidate_not_review_or_GO=True,failure_root_pin=pin)
                return 2
            if len(calls)>3:observed.append((m.WARM_REVIEWED_CODE,m.WARM_PENDING_STOP_PIN))
            state=m.LIGHT if mode=='light' else m.LIGHT_REVIEW_PASS if mode=='light-review' else m.REVIEW_PASS if mode=='stop-review' else m.PASS
            m.LAST_TERMINAL=dict(state=state,safe_to_wait_without_live_resources=True,
                current_code_pins=self.stable_codes() if mode in ('light','light-review') else None,
                reviewed_root_pin=pin if mode=='stop-review' else None)
            return 0
        return m.serve(lambda size:next(lines,''),output.append,run),calls,observed,output
    def test_warm_STOP_cannot_direct_actual_retry(self):
        code,calls,_,_=self.cpu_stop_sequence([dict(id='again',mode='actual',run=4)])
        self.assertEqual(code,2);self.assertEqual(len(calls),3)
    def test_warm_STOP_cannot_skip_failure_review_via_fresh(self):
        code,calls,_,_=self.cpu_stop_sequence([dict(id='again',mode='light-review',run=4)])
        self.assertEqual(code,2);self.assertEqual(len(calls),3)
    def test_warm_STOP_requires_exact_failure_pin(self):
        pin=dict(self.warm_failure_pin(),sha256='b'*64)
        code,calls,_,_=self.cpu_stop_sequence([dict(id='review',mode='stop-review',run=4,stop_root_pin=pin)])
        self.assertEqual(code,2);self.assertEqual(len(calls),3)
    def test_warm_STOP_review_still_needs_new_independent_fresh(self):
        code,calls,_,_=self.cpu_stop_sequence([dict(id='review',mode='stop-review',run=4,stop_root_pin=self.warm_failure_pin()),
            dict(id='actual',mode='actual',run=5)])
        self.assertEqual(code,2);self.assertEqual(len(calls),4)
    def test_warm_STOP_review_fresh_then_explicit_actual_only(self):
        code,calls,observed,_=self.cpu_stop_sequence([dict(id='review',mode='stop-review',run=4,stop_root_pin=self.warm_failure_pin()),
            dict(id='fresh',mode='light-review',run=5),dict(id='actual',mode='actual',run=6),dict(id='quit',mode='quit')])
        self.assertEqual(code,0);self.assertEqual(len(calls),6)
        self.assertIsNone(observed[0][0]);self.assertEqual(observed[0][1],self.warm_failure_pin())
        self.assertIsNone(observed[1][0]);self.assertIsNone(observed[1][1])
    def test_warm_STOP_idle_quit_no_retry(self):
        code,calls,_,_=self.cpu_stop_sequence([dict(id='q',mode='quit')])
        self.assertEqual(code,0);self.assertEqual(len(calls),3)
    def test_warm_isolation_restores_pending_STOP_pin(self):
        pending=object()
        with unittest.mock.patch.object(m,'WARM_PENDING_STOP_PIN',pending):
            with m.WarmTestIsolation():m.WARM_PENDING_STOP_PIN=None
            self.assertIs(m.WARM_PENDING_STOP_PIN,pending)
    def test_pinning_output_records_exact_single_write_no_read(self):
        target=m.io.StringIO();writer=m.PinningOutput(target);writer.write('{"value":1}')
        self.assertEqual(writer.written,11);self.assertEqual(writer.digest.hexdigest(),m.hashlib.sha256(b'{"value":1}').hexdigest())
    def test_pinning_output_partial_write_never_retries(self):
        target=Mock();target.write.return_value=1;writer=m.PinningOutput(target)
        with self.assertRaises(ValueError):writer.write('abc')
        target.write.assert_called_once_with('abc');self.assertEqual(writer.written,0)
    def test_pinning_output_block_bounds(self):
        target=m.io.StringIO();writer=m.PinningOutput(target)
        for block in ('','한글','a'*(m.r.compact.WRITE_CHARS+1)):
            with self.assertRaises(ValueError):writer.write(block)
        self.assertEqual(target.getvalue(),'')
    def test_prior333_schema_only_explicit_migration_not_current_acceptance(self):
        d=self.synthetic_stop();d['schema_version']=m.PRIOR333_SCHEMA
        with self.assertRaises(ValueError):self.stopped(d)
        result=m.stopped_before_product(d,*self.idle_scope(),expected_schema=m.PRIOR333_SCHEMA)
        self.assertEqual(result['accepted_count_delta'],0)

if __name__=='__main__':unittest.main()
