"""P304 explicit synthetic current/following full1631. 테스트 자료는 실제 수용 증거 아님."""
import copy
import unittest
import resume_completed101_compound_runtime as m
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
    pin=dict(doc['case_receipt_pin'],path=f'{m.p.DIR}/cases/p304-case-{index:03}-run001.json')
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
    preentry(doc['preparation_IO']);preentry(component['metadata_IO'])
    doc.update(schema_version=m.SCHEMA,state=m.PASS,compound_anchor_pin=m.ANCHOR,
        retained_contract_qualification_pin=m.RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        runtime_contract_executions=m.EXECUTED,own_queue_contract_tests_passed=m.COUNT,
        synthetic_following_queue_contract_tests_passed=m.COUNT,selected_test_index=index,selected_test_name=name,
        case_receipt_pin=pin,prior_runtime_plan=copy.deepcopy(base),runtime_plan=m.g.advance(legacy,base,names,index),
        scope_budget=m.budget(required,baseline,added),scope_added_six_pins=copy.deepcopy(list(added.values())),
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
if __name__=='__main__':unittest.main()
