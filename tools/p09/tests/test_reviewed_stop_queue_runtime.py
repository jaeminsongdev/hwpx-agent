"""P326 explicit synthetic current/following full1652. 테스트 자료는 실제 수용 증거 아님."""
import copy
import unittest
import resume_reviewed_stop_queue_runtime as m
FIXTURES=None
FOLLOWING=False
PRIOR_STOP=None
from types import SimpleNamespace
from unittest.mock import Mock

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
    pin=dict(doc['case_receipt_pin'],path=f'{m.p.DIR}/cases/p326-case-{index:03}-run001.json')
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
        scope_budget=m.budget(required,baseline,added),scope_added_eight_pins=copy.deepcopy(list(added.values())),
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
    def test_new_scope_added_pin_drift(self):self.doc['scope_added_eight_pins'][0]['sha256']='b'*64;self.reject()
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
    def stable_codes(self):return list(m.FROZEN87)+[self.added[m.SELF],self.added[m.TEST]]
    def synthetic_review(self,d):
        rootpin=dict(path=m.p.DIR+f'/p326-case-{d["selected_test_index"]:03}-run001.v1.json',bytes=1,sha256='a'*64)
        review=dict(schema_version=m.REVIEW_SCHEMA,state=m.REVIEW_PASS,reviewed_root_pin=copy.deepcopy(rootpin),
            stop_resume_policy=copy.deepcopy(m.STOP_POLICY),runtime_plan_at_review=copy.deepcopy(self.base),
            current89_metadata_code_pins=self.stable_codes(),resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
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
    def test_review_changed_code(self):self.review_reject('current89_metadata_code_pins',[])
    def test_review_native_started(self):self.review_reject('actual_Native_or_product_started_in_review',True)
    def test_review_product_claim(self):self.review_reject('actual_product_child_executed',True)
    def test_review_acceptance_claim(self):self.review_reject('accepted_exact_product_body_count',1)
    def test_review_incomplete_fresh(self):self.review_reject('preparation_IO',dict(finished=False,bound_inputs=100,final_fresh_hashes=1))
    def test_review_classification_forged(self):self.review_reject('reviewed_failure_classification',dict(accepted_count_delta=1))
    def test_exact_root_pin_argument(self):
        p=dict(path=m.p.DIR+'/p326-case-104-run001.v1.json',bytes=1,sha256='a'*64)
        self.assertEqual(m.pin_argument(p),p)
    def test_root_pin_path_escape(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path='../p326-case-104-run001.v1.json',bytes=1,sha256='a'*64))
    def test_root_pin_bool_size(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p326-case-104-run001.v1.json',bytes=True,sha256='a'*64))
    def test_root_pin_hash_invalid(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p326-case-104-run001.v1.json',bytes=1,sha256='z'*64))
    def test_approval_pin_must_review_namespace(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p326-case-104-run001.v1.json',bytes=1,sha256='a'*64),True)
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
        ap=dict(path=m.p.DIR+'/p326-stop-review-run002.v1.json',bytes=1,sha256='b'*64)
        approvals={pin['path']:(ap,review)} if approval else {}
        def glob(obj,pattern):return [path] if pattern=='p326-case-*-run*.v1.json' else []
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

if __name__=='__main__':unittest.main()

