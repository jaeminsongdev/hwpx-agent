"""Independent whole249 terminal audit; stops/failures are preserved, not passed."""
import argparse
import base64
import hashlib
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import run_observed_stored_full as observed
s=observed.original

SELF='tools/p09/audit_observed_stored_full.py'


def audit_observations(row,passed):
    s.require(row['host_observer_closing_pin']==observed.PARENT and row['observed_same_owned_job'] is True
        and row['observer_collection_seconds']==1 and row['diagnostic_only_hot_threshold']==80
        and row['original_emergency_cpu_guard_unchanged'] is True and row['observer_calls_outside_parent_guard'] is False
        and row['diagnostic_snapshots_are_not_complete_host_process_history'] is True
        and row['individual_duplicated_PID_attribution'] is False,'AUDIT_DIAGNOSTIC_BOUNDARY')
    cap=row['capture_diagnostics']
    if cap is None:
        s.require(not passed,'AUDIT_NO_CAPTURE_NOT_PASSED');return
    s.require(cap['diagnostic_snapshots_max']==observed.MAX_SAVED and cap['diagnostic_frame_limit']==observed.MAX_FRAME
        and cap['raw_names_paths_commands_saved'] is False and cap['causal_attribution'] is False
        and cap['per_stream_limit_bytes']==32768,'AUDIT_CLOSED_DIAGNOSTICS')
    records=cap['host_cpu_records'];s.require(type(records) is list and len(records)<=observed.MAX_SAVED+3,'AUDIT_FRAME_COUNT')
    ready=None;samples=[];budget=False;sealed=False
    jobpids={p['pid'] for sample in row['samples'] for p in sample.get('owned_processes',[])}
    for item in records:
        observed.valid_record(item,ready['worker_pid'] if ready else None)
        s.require(not sealed,'AUDIT_AFTER_QUERY_CLOSE')
        kind=item['kind']
        if kind=='ready':
            s.require(ready is None and not samples and item['worker_pid'] in jobpids
                and item['processor_count']==row['resolved_owned_limits']['machine_logical_processors'],'AUDIT_READY_MEMBERSHIP')
            ready=item
        else:s.require(ready is not None,'AUDIT_READY_REQUIRED')
        if kind=='sample':
            s.require(item['test_pid']==ready['test_pid'] and item['sequence']==len(samples)+1
                and item['observation']['processor_count']==ready['processor_count']
                and (not samples or item['observed_at']>samples[-1]['observed_at']),'AUDIT_SAMPLE_BINDING')
            samples.append(item)
        if kind=='budget':
            s.require(not budget and len(samples)==observed.MAX_SAVED,'AUDIT_EXPLICIT_BUDGET');budget=True
        if kind=='closed':
            s.require(item['saved_samples']==len(samples) and item['diagnostic_budget_limited'] is budget,'AUDIT_QUERY_CLOSE_MATCH')
            sealed=True
    s.require(cap['explicit_query_cleanup_confirmed'] is sealed,'AUDIT_EXPLICIT_QUERY_CLOSE')
    if passed:
        s.require(ready is not None and ready['test_pid'] in jobpids and samples and sealed
            and cap['host_cpu_error_code'] is None,'AUDIT_PASSED_FULL_REQUIRES_OBSERVATIONS')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'AUDIT_REPOSITORY_CWD')
    destination=s.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-154-observed-full.terminal-audit-run{args.audit_run:02}.v1.json',fresh=True)
    resources=s.inventory.build.prepared.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-observed-fresh-full249-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,full249_current_qualified=False,signed16_current_qualified=False,
        actual_SQL_native_or_audit_OS_child_executed=False,audit_new_thread_started=False,
        raw_logs_included=False,PC_freeze_resolved=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,resource_samples=resources.samples)
    try:
        resources.admit();q=s.inventory.build.prepared.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-154-observed-full.actual-run{args.run:02}.v1.json'
        row=q.json(name);out['actual_full_receipt_pin']=q.reader.snapshots[name]
        archive=q.json('implementation/p09/source-archive/p09-154-pre-frame-budget-r36/source-preimages.v1.json')
        s.require(q.pin(archive['failed_light_pin']['path'])==archive['failed_light_pin'],'AUDIT_FAILED_LIGHT_PIN')
        prior=q.json(archive['failed_light_pin']['path'])
        s.require(prior['state']=='FAILED_NOT_ACCEPTED' and prior['contract_tests_run']==55
            and prior['contract_tests_passed']==54 and prior['failed_tests']==['test_frame_bound_original_stream_limit']
            and len(archive['files'])==2,'AUDIT_FAILED_LIGHT_SCOPE')
        for item in archive['files']:
            preimage=base64.b64decode(item['base64'],validate=True)
            pin={k:item[k] for k in ('path','bytes','sha256')}
            s.require(pin in prior['bound_input_pins'] and len(preimage)==item['bytes']
                and hashlib.sha256(preimage).hexdigest()==item['sha256'],'AUDIT_FAILED_LIGHT_WHOLE_SOURCE')
        light=q.json('implementation/p09/evidence/p09-154-observed-full.light-run02.v1.json')
        s.require(light['state']=='PASS_OBSERVED_FULL249_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
            and light['contract_tests_run']==light['contract_tests_passed']==55 and light['source_closing_exact'],'AUDIT_CURRENT_LIGHT55')
        for pin in light['bound_input_pins']:
            s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_LIGHT_SOURCE')
        s.require(row['state'] in (observed.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['current_inventory_closing_pin']==s.PARENT and row['current_Rust_input_count']==785
            and row['expected_test_count']==249 and row['maximum_seconds']==1200
            and row['policy']==s.c.POLICY and row['native_or_SQL_run'] is False
            and row['actual_new_Cargo_compile_executed'] is False and row['product_complete'] is False
            and row['P09_gate']=='OPEN','AUDIT_SCOPE_NOT_SQL_NATIVE_OR_GATE')
        s.require(row['cleanup_confirmed'] is True and row['owned_tree_empty'] is True,'AUDIT_TERMINAL_CLEANUP')
        passed=row['state']==observed.PASS
        s.require(row['full249_current_qualified'] is passed and row['signed16_current_qualified'] is passed
            and row['tests_passed']==(249 if passed else None),'AUDIT_ORIGINAL_PASS_OR_STOP_UNCHANGED')
        if row['heavy_work_started']:
            s.require(all(row[k] is True for k in ('worker_created','job_assigned','writer_authorized',
                'post_hash_runtime_admission_revalidated','test_body_execution_authorized'))
                and row['owned_limits_readback']['verified'] is True
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[], 'AUDIT_REAL_OWNED_JOB')
        else:s.require(not passed and row['test_body_execution_authorized'] is False,'AUDIT_NOT_STARTED_NOT_PASSED')
        capture=row['capture_diagnostics']
        audit_observations(row,passed)
        if passed:
            s.require(row['exit_code']==0 and row['stop_reason'] is None and capture is not None
                and capture['error_code'] is None and capture['per_stream_limit_bytes']==32768
                and all(0<=n<=32768 for n in capture['received_bytes'].values())
                and capture['raw_log_content_included'] is False,'AUDIT_COMPLETE249_TERMINAL')
        else:s.require(isinstance(row['stop_reason'],str) and re.fullmatch('[A-Z_]+',row['stop_reason']), 'AUDIT_STOP_CODE_PRESERVED')
        s.require(q.pin(s.PARENT['path'])==s.PARENT,'AUDIT_CURRENT_COMPILED249_PARENT')
        parent=q.json(s.PARENT['path']);expected=s.inventory.build.prepared.inputs.inventory(parent['bound_input_pins'],1203)
        frozen=s.inventory.build.prepared.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:s.require(all(frozen.get(n)==p for n,p in expected.items()),'AUDIT_WHOLE_RUN_SOURCE_CLOSURE')
        for path,pin in {**expected,**frozen}.items():s.require(q.pin(path)==pin,'AUDIT_CURRENT_INPUT')
        exe=row['compiled_test_executable_pin'];s.require(exe==parent['compiled_test_executable_pin']
            and exe['path']==s.inventory.build.executable_name(1) and q.pin(exe['path'])==exe,'AUDIT_EXACT_FRESH_EXE')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.inventory.build.prepared.inputs.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        def read(path):
            s.require(path in expected,'AUDIT_MODULE_SCOPE');value=q.text(path)
            s.require(q.reader.snapshots[path]==expected[path],'AUDIT_CURRENT_MODULE');return value
        names,modules=s.inventory.PARENT.recursive_names(read,'stored-form-tests');s.full.cost.original.select_names(names)
        s.require(len(modules)==59 and row['source_test_names']==row['selected_test_names']==list(names)
            and row['source_module_instances']==list(modules) and parent['source_test_names']==list(names)
            and row['test_package_profile_config']==list(s.inventory.build.CONFIG)
            and row['signed_original_test_name']==s.full.cost.original.NAME,'AUDIT_UNFILTERED_ORIGINAL249_59')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        for path in (s.SELF,s.TEST,s.full.SELF,s.full.TEST,observed.SELF,observed.TEST):q.pin(path)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_current_stored_full','test_compression_full_stored','test_observed_stored_full','test_host_cpu_groups'))
        with patch('subprocess.Popen',side_effect=AssertionError('P152_FULL_AUDIT_OS_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_FULL_AUDIT_OS_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P152_FULL_AUDIT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==55 and not checked.skipped,'AUDIT_FRESH_CONTRACT55')
        q.finish();out.update(state='PASS_OBSERVED_UNFILTERED_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE' if passed else
            'PASS_OBSERVED_FULL249_STOP_ACCOUNTED_NOT_RUNTIME_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,full249_current_qualified=passed,signed16_current_qualified=passed,
            actual_tests_passed=249 if passed else None,original_run_state=row['state'],original_stop_reason=row['stop_reason'],
            original_source_final_hash_not_retroactively_promoted=not passed,contract_tests_passed=55,
            current_Rust_input_count=785,source_test_names=list(names),source_module_instances=list(modules),
            protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),compiled_test_executable_pin=exe,
            owned_job_final=row.get('job_final'),capture_diagnostics=capture,
            bounded_host_diagnostics_verified=True,host_observer_closing_pin=observed.PARENT,
            individual_duplicated_PID_attribution=False,causal_attribution=False,
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']) if row['samples'] else None,
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=s.closed_error(error)
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['final_freshness_error']='P152_FULL_AUDIT_FINAL_FRESHNESS'
        s.inventory.build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_tests_passed','contract_tests_passed','original_stop_reason','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__=='__main__':raise SystemExit(main())

