"""Independent P151 terminal audit; actual service+disk units are NOT SQL/Gate."""
import argparse
import base64
import hashlib
import io
import json
import re
import sys
import threading
import time
import unittest
from unittest.mock import patch
import run_durable_negative_example_tests as s

SELF='tools/p09/audit_durable_negative_example.py'
PRE_LIGHT='implementation/p09/source-archive/p09-151-pre-disk-guard-tests-r30/source-preimages.v1.json'


def audit(run,audit_run):
    resources,q,started=s.SQLRuntimeResources(),None,time.monotonic()
    destination=s.scoped_path(f'implementation/p09/evidence/p09-151-durable-negative.terminal-audit-run{audit_run:02}.v1.json',fresh=True)
    out=dict(schema_version='hwpx-agent.p09-durable-negative-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,actual_SQL_or_native_executed=False,audit_new_child_or_thread_started=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        same_process_InMemory_metadata_only=True,actual_SQL_metadata_or_signed_consumer_controls_qualified=False,
        full_durable_DS01_DS09_qualified=False,production_scanner_or_key_custody_qualified=False,
        independent_restart_or_OS_ACL_qualified=False,full249_current_qualified=False,PC_freeze_resolved=False,
        raw_logs_included=False,resource_samples=resources.samples)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-151-durable-negative.actual-run{run:02}.v1.json';row=q.json(name)
        out['actual_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']=='PASS_SCOPED_NOT_GATE' and row['tests_passed']==27 and row['exit_code']==0
            and row['example_backend_tests_qualified'] is True and row['actual_service_and_owned_disk_controls_qualified'] is True
            and row['operation_phase']=='final_source_freeze' and row['stop_reason'] is None
            and row['protected_executables_exact_after'] is True,'AUDIT_ACCEPTED27')
        s.require(row['worker_created'] and row['job_assigned'] and row['writer_authorized']
            and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15
            and row['policy']==s.c.POLICY,'AUDIT_GO_POLICY')
        s.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['job_final']['active_processes']==0
            and row['job_final']['owned_processes']==[],'AUDIT_TERMINAL')
        limits=row['owned_limits_readback']
        s.require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
            and limits['priority_class']==16384 and limits['active_process_limit']==16
            and limits['kill_on_close'] and limits['breakaway_disabled'],'AUDIT_LIMITS')
        s.require(row['provided_driver_generation']=='P151_R30_DS06' and row['whole_workspace_Rust_input_count']==785
            and row['original_source_tests_retained']==11 and row['original_backend_tests_retained']==8
            and row['new_service_negative_tests']==8 and row['historical_preP151_build_admission_is_current'] is False
            and row['actual_SQL_metadata_or_signed_consumer_controls_qualified'] is False
            and row['actual_SQL_or_native_executed'] is False and row['product_complete'] is False
            and row['P09_gate']=='OPEN' and row['independent_restart_or_key_custody_qualified'] is False,'AUDIT_SCOPE')
        capture=row['capture_diagnostics']
        s.require(capture['complete_result_accepted'] and capture['error_code'] is None
            and capture['per_stream_limit_bytes']==32768 and capture['raw_log_content_included'] is False
            and capture['running_test_counts']==['27'] and capture['test_summary_numbers']==[['27','0','0','0','0']]
            and capture['compile_only_completed'] and len(capture['compiled_test_artifact'])==1,'AUDIT_CAPTURE')
        artifact,size,digest=capture['compiled_test_artifact'][0]
        compiled=q.pin((s.TARGET/'debug/examples'/artifact).relative_to(s.c.ROOT).as_posix())
        s.require(compiled['bytes']==int(size) and compiled['sha256']==digest,'AUDIT_REPORTED_TEST_EXE')
        frozen={p['path']:p for p in row['source_freeze']};s.require(len(frozen)==len(row['source_freeze']),'AUDIT_UNIQUE_INPUTS')
        for pin in frozen.values():s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_INPUT_DRIFT')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.original.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        protected=row['protected_executables'];s.require(len(protected)==len({p['path'] for p in protected})==52,'AUDIT_PROTECTED52')
        for pin in protected:
            s.require(not (s.c.ROOT/pin['path']).is_relative_to(s.TARGET) and q.pin(pin['path'])==pin,'AUDIT_OLD_EXE_EXACT')
        for item in q.json(s.ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True);current=q.text(item['path'])
            s.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
                and s.recovered(raw,s.restore_previous(item['path'],current))==raw,'AUDIT_WHOLE_R29_BODY')
        for item in q.json(s.original.ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            text=s.restore_previous(item['path'],q.text(item['path']))
            s.require(s.recovered(raw,s.original.restore_original(item['path'],text))==raw,'AUDIT_WHOLE_ORIGINAL')
        prior=q.json(PRE_LIGHT);old=q.json(prior['prior_light_receipt_pin']['path'])
        s.require(q.pin(prior['prior_light_receipt_pin']['path'])==prior['prior_light_receipt_pin']
            and old['state']=='PASS_P151_SOURCE_CONTRACT_ONLY_NOT_COMPILED_SQL_OR_GATE'
            and old['tests_passed']==10 and old['actual_compile_SQL_native_executed'] is False,'AUDIT_PRIOR_LIGHT_NOT_RUNTIME')
        old_pins={p['path']:p for p in old['source_freeze']}
        for item in prior['files']:
            raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
            s.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                and old_pins[pin['path']]==pin,'AUDIT_PRIOR_LIGHT_WHOLE')
        light=q.json('implementation/p09/evidence/p09-151-durable-negative.light-run02.v1.json')
        s.require(light['tests_passed']==light['tests_run']==10 and light['source_closing_exact']
            and light['state']=='PASS_P151_SOURCE_CONTRACT_ONLY_NOT_COMPILED_SQL_OR_GATE','AUDIT_CURRENT_LIGHT')
        for pin in light['source_freeze']:s.require(q.pin(pin['path'])==pin,'AUDIT_LIGHT_INPUT_DRIFT')
        failed_archive=q.json('implementation/p09/source-archive/p09-151-pre-audit-schema-fix-r30/source-preimages.v1.json')
        failed=q.json(failed_archive['failed_audit_pin']['path'])
        s.require(q.pin(failed_archive['failed_audit_pin']['path'])==failed_archive['failed_audit_pin']
            and failed['state']=='FAILED_NOT_ACCEPTED' and failed['actual_SQL_or_native_executed'] is False,
            'AUDIT_FAILED_AUDIT_PRESERVED')
        for item in failed_archive['files']:
            raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
            s.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                and pin in failed['bound_input_pins'],'AUDIT_FAILED_AUDIT_WHOLE_SOURCE')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'));before={t.ident for t in threading.enumerate()}
        suite=unittest.defaultTestLoader.loadTestsFromName('test_durable_negative_example_tests')
        with patch('subprocess.Popen',side_effect=AssertionError('P151_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P151_AUDIT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==10 and not checked.skipped,'AUDIT_LIGHT10')
        s.require({t.ident for t in threading.enumerate()}==before,'AUDIT_NO_NEW_THREADS')
        q.finish();out.update(state='PASS_CURRENT_SERVICE_OWNED_DISK_NEGATIVE_UNITS27_ONLY_NOT_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,actual_example_tests_passed=27,contract_tests_passed=10,
            current_Rust_input_count=785,protected_executables_exact=52,compiled_test_artifact=compiled,
            original_source_tests_retained=11,original_backend_tests_retained=8,new_negative_tests=8,
            runtime_control_check_names=list(s.CONTROL_CHECKS),runtime_job_final=row['job_final'],limits_readback=limits,
            original_preP150_and_prior_R29_whole_bodies_exact=True,prior_light_not_promoted_to_runtime=True,
            failed_audit_and_whole_source_preserved=True,original_runtime_final_source_freeze_phase_verified=True,
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']),
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        value=str(error) if isinstance(error,ValueError) else 'P151_AUDIT_OPERATION_FAILED'
        out['error_code']=value if len(value)<=160 and re.fullmatch('[A-Z_]+',value) else 'P151_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='P151_AUDIT_FINAL_FRESHNESS'
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_example_tests_passed','contract_tests_passed',
            'error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] \
        and out.get('resource_watcher_cleanup_confirmed') and resources.reason is None else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    raise SystemExit(audit(args.run,args.audit_run))
