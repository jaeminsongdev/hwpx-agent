"""P188 immutable running-stop accounting plus empty owned-Job IO API probe.

No current whole-source/binary closing or product-runtime qualification.
The original incomplete full249/signed16 stays false; no immediate test retry.
"""
import base64
import hashlib
import io
import json
import math
import sys
import time
import unittest
from unittest.mock import patch
import run_current_r07_full as run
import owned_job_io_observer as observer

c=run.c;s=run.s
SELF='tools/p09/inspect_current_r07_stop_r2.py'
TEST='tools/p09/tests/test_current_r07_stop_r2.py'
DEST='implementation/p09/evidence/p09-188-current-r07-full-stop-and-owned-IO-probe-r2-run01.v1.json'
ACTUAL=dict(path=run.ACTUAL,bytes=1992698,sha256='681466f38eaa9d99be9070d4342ff8f6bfaeb18c29723737dcdc55e41d7de761')
PREP=dict(path=run.PREP,bytes=339465,sha256='72c75dab9b05611c58c7c0820f90050397b564367eaee545577dfc216277ece3')
LIGHT=dict(path='implementation/p09/evidence/p09-187-current-r07-full.light-run01.v1.json',bytes=3483,
    sha256='d8354e6e6196ccc8af1c5004be3b3a649edd6f9b45c775b7b7aca5e597270b0b')
PASS='PASS_R07_RUNNING_STOP_METADATA_AND_EMPTY_JOB_IO_API_ONLY_NOT_RUNTIME_FRESH_SOURCE_OR_CAUSE'

PRIOR_PINS=[{"path":"tools/p09/inspect_current_r07_stop.py","bytes":13361,"sha256":"b68dfafaf70a1c768d3ee38f7ae8df77172f06c85b3b84cfa61e05b56dd4895f"},{"path":"tools/p09/tests/test_current_r07_stop.py","bytes":2839,"sha256":"b55b4c60368effe00ece8b73f447ca4b1e74ab76b8fdbd36a20632e19eeb84db"},{"path":"implementation/p09/evidence/p09-188-current-r07-full-stop-and-owned-IO-probe-run01.v1.json","bytes":3239,"sha256":"a62e5b5121b5d3233b072b16ad387826c2bef90e91000d4406c89f1fde750dd1"}]
ARCHIVE='implementation/p09/source-archive/p09-188-pre-io-inspector-r2/helper-and-failure-preimages.v1.json'

def require(ok,code):run.require(ok,'STOP_ACCOUNT_'+code)

def actual_scope(row,prep,parent):
    expected,exe=run.parent_scope(parent)
    require(row['state']=='STOPPED_NOT_ACCEPTED' and row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and row['operation_phase']=='running' and row['exit_code'] is None
        and all(row[k] is True for k in ('worker_created','job_assigned','writer_authorized','heavy_work_started',
            'post_hash_runtime_admission_revalidated','test_body_execution_authorized','cleanup_confirmed','owned_tree_empty')),
        'INCOMPLETE_RUNTIME_TERMINAL_NOT_POST_HASH')
    require(row['current_inventory_closing_pin']==run.PARENT and row['compiled_test_executable_pin']==exe
        and row['current_Rust_input_count']==785 and row['current_compiled249_qualified']
        and row['expected_test_count']==249 and row['maximum_seconds']==1200
        and row['policy']==c.POLICY and row['runtime_admission_RAM_percent']==10
        and row['test_package_profile_config']==list(run.original.inventory.build.CONFIG),'CURRENT_R07_ORIGINAL_POLICY')
    require(row['source_test_names']==row['selected_test_names']==parent['source_test_names']
        and row['source_module_instances']==parent['source_module_instances']
        and row['signed_original_test_name']==run.original.full.cost.original.NAME,'ALL_ORIGINAL249_59')
    require(all(row[k] is False for k in ('full249_current_qualified','signed16_current_qualified','product_complete',
        'PC_freeze_resolved','actual_new_Cargo_compile_executed','actual_Hangul_COM_or_SQL_run','foreign_Process_query_executed',
        'additional_observer_thread_started','extra_hash_sampler_started','original_test_bodies_or_product_sources_changed',
        'original_owned_resource_policy_changed','raw_logs_printed_or_saved')) and row['tests_passed'] is None
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['native_Process_query_executed'] and row['own_parent_ProcessTimes_observation_connected'],
        'NO_RUNTIME_OR_CAUSE_PROMOTION')
    require(prep['state']=='PASS_CURRENT_R07_FULL249_PREPARATION_ONLY_NOT_RUNTIME_OR_GATE'
        and prep['source_closing_exact'] and prep['contract_tests_passed']==86
        and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
        and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1447,
        'ORIGINAL_COMPLETE_PREPARATION')
    prepared=s.inputs.inventory(prep['bound_input_pins'],1447);before=s.inputs.inventory(row['source_freeze'],1447)
    require(before==prepared and all(before.get(n)==p for n,p in expected.items())
        and sum(n.endswith('.exe') for n in before)==68,'WHOLE1447_BEFORE_ONLY_METADATA')
    cap=row['capture_diagnostics']
    require(cap['error_code'] is None and cap['per_stream_limit_bytes']==32768
        and cap['buffered_bytes']==cap['received_bytes']==dict(stdout=66,stderr=0)
        and not cap['raw_log_content_included'],'PARTIAL66_NOT_COMPLETE249_RESULT')
    limits=row['owned_limits_readback'];final=row['job_final']
    require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==0x4000 and limits['active_process_limit']==16 and limits['kill_on_close']
        and limits['breakaway_disabled'] and final['active_processes']==0 and final['owned_processes']==[],
        'REAL_JOB_LIMITS_AND_EMPTY_TERMINAL')
    readers=row['owned_source_reader_passes']
    require(len(readers)==1 and readers[0]['read_passes']==1447
        and readers[0]['bytes_read']==sum(p['bytes'] for p in before.values())
        and readers[0]['read_rates_by_kind']==dict(binary=1048576,other=2097152)
        and readers[0]['original_owned_read_operations_preserved']
        and not readers[0]['extra_sampler_or_native_query_started'],'OWNED_PRE_HASH_ONLY_NO_AFTER')
    pressure=readers[0]['near_saturation_read_backpressure']
    require(pressure['original_hard_resource_decisions_unmodified'] and pressure['original_IO_deadline_unmodified']
        and pressure['original_sampler_windows_reused'] and not pressure['new_native_query_or_sampler_thread_started']
        and not pressure['original_read_checks_skipped'] and pressure['warning_system_CPU_percent']==95
        and pressure['cool_distinct_sample_windows']==2 and pressure['maximum_pause_windows_per_entry']==8
        and pressure['maximum_observed_pause_windows_in_one_entry']<=8,'PRESSURE_GUARDS_RETAINED')
    samples=row['samples'];require(len(samples)==1371,'ALL_ORIGINAL_OBSERVATIONS')
    hot=0
    for i,sample in enumerate(samples):
        hot,reason=c.decision(sample,hot)
        require(reason is None if i<len(samples)-1 else reason==row['stop_reason'],'ORIGINAL_DECISION_REPLAY')
        raw=sample['raw_system_cpu_delta_100ns'];delta=sample['parent_cpu_delta_100ns']
        require(all(type(raw[n]) is int and raw[n]>=0 for n in ('idle','kernel_including_idle','user','total'))
            and raw['total']==raw['kernel_including_idle']+raw['user'] and raw['total']>0
            and type(delta) is int and delta>=0
            and abs(sample['parent_cpu_machine_percent']-100*delta/raw['total'])<=0.000001,
            'SELF_CPU_SAME_ORIGINAL_RAW_DENOMINATOR')
    last=samples[-4:]
    require(all(x['system_cpu_percent']>=98 for x in last) and hot==4,'LAST4_ORIGINAL_CPU_STOP')
    return dict(original_run_state=row['state'],original_stop_reason=row['stop_reason'],operation_phase=row['operation_phase'],
        original_tests_passed=None,current_parent_compiled249_qualified=True,original_full249_qualified=False,
        original_signed16_qualified=False,original_test_execution_started=True,original_whole_before_inputs=1447,
        current_whole_runtime_inputs_reaudited=False,original_final_source_freeze_completed=False,
        original_complete_test_summary_available=False,actual_active_test_name_or_pass_count_inferred=False,
        original_sample_count=len(samples),host_CPU_max_percent=max(x['system_cpu_percent'] for x in samples),
        host_available_RAM_min_percent=min(x['available_ram_percent'] for x in samples),
        parent_CPU_max_machine_percent=max(x['parent_cpu_machine_percent'] for x in samples),
        owned_job_CPU_max_machine_percent=max(x.get('owned_job_cpu_machine_percent',0) for x in samples),
        owned_peak_private_mib=final['peak_job_private_mib'],owned_peak_private_percent=final['peak_job_private_percent'],
        last4_system_CPU_percent=[x['system_cpu_percent'] for x in last],
        last4_parent_CPU_machine_percent=[x['parent_cpu_machine_percent'] for x in last],
        last4_owned_job_CPU_machine_percent=[x['owned_job_cpu_machine_percent'] for x in last],
        full_runtime_read_write_counters_present=False,original_owned_read_backpressure=pressure,
        capture_diagnostics=cap,owned_job_final_empty=True,PC_freeze_cause_established=False)

def contracts():
    run.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_owned_job_io_observer','test_current_r07_stop_r2'))
    with patch('subprocess.Popen',side_effect=AssertionError('P188_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P188_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P188_NO_NEW_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==14 and not checked.skipped,'CONTRACT86_PLUS8_PLUS6')
    return dict(contract_tests_passed=100,stop_metadata_contract_tests_passed=6,owned_IO_contract_tests_passed=8)

def main():
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');destination=s.scoped_path(DEST,fresh=True)
    resources=run.pressure.observation.OriginalResources();q=None;windows=None;job=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        actual_product_test_Cargo_SQL_Hangul_or_child_executed=False,new_runtime_IO_observer_connected_to_product=False,
        foreign_Process_query_executed=False,additional_sampler_or_observer_thread_started=False,
        private_values_or_raw_logs_saved=False,artifact_EXE_scan_started=False,empty_owned_job_cleanup_confirmed=True)
    try:
        resources.admit();q=run.pressure.PressureReader(resources)
        archive=q.json(ARCHIVE)
        require(archive['state']=='WHOLE_P188_INITIAL_ATTRIBUTE_BINDING_FAILURE_PREIMAGES_NOT_RUNTIME_OR_GATE'
            and len(archive['files'])==3,'WHOLE_FIRST_FAILURE_ARCHIVE')
        for pin,item in zip(PRIOR_PINS,archive['files']):
            raw=base64.b64decode(item['base64'],validate=True)
            require({k:item[k] for k in ('path','bytes','sha256')}==pin and len(raw)==pin['bytes']
                and hashlib.sha256(raw).hexdigest()==pin['sha256'] and q.pin(pin['path'])==pin,'WHOLE_ORIGINAL_FAILURE_PRESERVED')
        failed=q.json(PRIOR_PINS[2]['path'])
        require(failed['state']=='FAILED_NOT_ACCEPTED' and failed['error_code']=='P152_FULL_REDACTED_FAILURE'
            and failed['empty_owned_job_cleanup_confirmed'] and failed['resource_watcher_cleanup_confirmed']
            and failed['resource_stop_reason'] is None and not failed['full249_current_qualified'], 'FIRST_FAILURE_NOT_PASS')
        out.update(first_P188_failure_preserved=True,prior_helper_and_failure_pins=PRIOR_PINS,
            sole_scope_semantic_correction='resolve_existing_81_package_profile_through_original.inventory.build.CONFIG')
        for pin in (ACTUAL,PREP,LIGHT,run.PARENT):require(q.pin(pin['path'])==pin,'IMMUTABLE_RECEIPT')
        row=q.json(ACTUAL['path']);prep=q.json(PREP['path']);parent=q.json(run.PARENT['path'])
        out.update(actual_scope(row,prep,parent));out.update(contracts())
        prepared=s.inputs.inventory(prep['bound_input_pins'],1447)
        for n in (run.SELF,run.TEST,run.owned.SELF,run.owned.TEST,run.pressure.SELF,run.pressure.TEST,
                run.original.SELF,run.original.TEST):require(q.pin(n)==prepared[n],'P187_HELPERS_PRESERVED')
        for n in (SELF,TEST,observer.SELF,observer.TEST):q.pin(n)
        resources.checkpoint_io();windows=observer.windows_type(c.Windows)();job=windows.job()
        out['empty_owned_job_cleanup_confirmed']=False;out['empty_owned_job_limits_readback']=windows.verify_job_limits(job)
        observed=[]
        for _ in range(4):
            time.sleep(c.POLICY['sample_seconds']);resources.checkpoint_io();sample=windows.accounting(job)
            require(sample['active_processes']==0 and sample['owned_processes']==[]
                and sample['job_IO_observed'] and sum(sample['job_IO_totals'].values())==0,'EMPTY_JOB_ONLY')
            observed.append({k:sample[k] for k in ('active_processes','job_IO_observed','job_IO_totals',
                'job_IO_delta_since_previous_query','job_IO_query_sequence')})
        out.update(empty_owned_job_IO_observations=observed,empty_owned_job_IO_API_verified=True,
            QueryInformationJobObject_reference=observer.REFERENCE,aggregate_IO_structure_reference=observer.STRUCT_REFERENCE)
        q.finish();out.update(state=PASS,metadata_and_probe_inputs_only_fresh=True,
            actual_full_receipt_pin=ACTUAL,preparation_receipt_pin=PREP,current_compiled249_parent_pin=run.PARENT)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=run.original.closed_error(error)
    finally:
        if job:
            try:
                require(windows.k.TerminateJobObject(job,1),'EMPTY_JOB_TERMINATE_FAILED')
                final=windows.accounting(job);require(final['active_processes']==0 and final['owned_processes']==[],
                    'EMPTY_JOB_NOT_EMPTY')
                require(windows.k.CloseHandle(job),'EMPTY_JOB_CLOSE_FAILED');job=None
                out['empty_owned_job_cleanup_confirmed']=True
            except (ValueError,OSError):
                out['empty_owned_job_cleanup_confirmed']=False;out['state']='FAILED_NOT_ACCEPTED'
                if job:windows.k.CloseHandle(job)
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed') or not out['empty_owned_job_cleanup_confirmed']:
            out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason',
            'empty_owned_job_cleanup_confirmed','wall_seconds')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=run.original.closed_error(error))));raise SystemExit(2) from None
