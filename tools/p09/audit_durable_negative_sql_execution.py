"""Independent closing of current39/pre-cancel host evidence; NOT actual SQL/Gate."""
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
import run_durable_negative_sql_probe as s

SELF='tools/p09/audit_durable_negative_sql_execution.py'
ARCHIVES=(
    'implementation/p09/source-archive/p09-151-pre-current-execution-count-fix-r32/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-151-pre-local-docker-case-fix-r32/source-preimages.v1.json')


def audit(run,audit_run):
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    destination=s.subject.scoped_path(f'implementation/p09/evidence/p09-151-current-SQL-execution.terminal-audit-run{audit_run:02}.v1.json',fresh=True)
    out=dict(schema_version='hwpx-agent.p09-current39-pre-backend-cancel-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,actual_SQL_native_or_runtime_EXE_executed=False,audit_new_child_or_thread_started=False,
        full_SQL_wrapper_cancellation_and_container_cleanup_qualified=False,full_durable_DS01_DS09_qualified=False,
        production_key_custody_or_independent_restart_qualified=False,PC_freeze_resolved=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        raw_logs_included=False,resource_samples=resources.samples)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-151-current-SQL-execution.pre-cancel-run{run:02}.v1.json';row=q.json(name)
        out['pre_cancel_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']=='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_ONLY_NOT_SQL_OR_GATE'
            and row['source_closing_exact'] and row['resource_stop_reason'] is None
            and row['resource_watcher_cleanup_confirmed'] and row['mode']=='pre-cancel'
            and row['actual_owned_worker_executed'] is True and row['actual_SQL_executed'] is False
            and row['Docker_read_only_executed'] is False and row['actual_Docker_container_operations_executed'] is False,'AUDIT_ACTUAL_PRE_CANCEL_SCOPE')
        s.require(row['compiled_source_count']==846 and row['current_Rust_input_count']==785
            and row['protected_executables_exact']==53 and row['required_check_names']==s.driver.required_checks()
            and len(row['required_check_names'])==39 and row['product_entrypoint_connected'] is True
            and row['original_body_inverse_exact'] and row['provided_driver_guard_count_delta']==[842,846],'AUDIT_CURRENT39_GENERATION')
        s.require(len(row['executions'])==1,'AUDIT_EXACT_ONE_EXECUTION')
        execution=row['executions'][0];parent=execution['supervisor'];worker=parent['worker_result']
        args=(s.contract.BUILD_PIN['path'],worker['receipt_path'],0,'original','unchanged','approval')
        s.require(row['component_scope']==s.verify_pre_cancelled(execution,args),'AUDIT_ORIGINAL_CANCEL_NOT_PROMOTED')
        frozen={p['path']:p for p in row['bound_input_pins']}
        s.require(len(frozen)==len(row['bound_input_pins']),'AUDIT_UNIQUE_INPUTS')
        for pin in frozen.values():s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_INPUT')
        s.require(q.pin(s.ADMISSION_PIN['path'])==s.ADMISSION_PIN,'AUDIT_CURRENT_ADMISSION_IMMUTABLE')
        admission=q.json(s.ADMISSION_PIN['path'])
        s.require(admission['state']=='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and admission['source_closing_exact'] and admission['compiled_source_count']==846
            and admission['required_check_count']==39,'AUDIT_ORIGINAL_ADMISSION_SCOPE')
        for pin in admission['bound_input_pins']:s.require(frozen[pin['path']]==pin,'AUDIT_PARENT_INPUT_WHOLE_CLOSURE')
        s.require(q.pin(s.contract.BUILD_PIN['path'])==s.contract.BUILD_PIN,'AUDIT_CURRENT_BUILD_IMMUTABLE')
        build=q.json(s.contract.BUILD_PIN['path']);source,protected,exe=s.contract.accepted(build)
        s.require(len(protected)==53 and row['executable_pin']==exe,'AUDIT_CURRENT_EXE')
        for pin in [*source.values(),*protected.values(),exe]:s.require(frozen[pin['path']]==pin,'AUDIT_BUILD_WHOLE_CLOSURE')
        rust={n for n in source if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.contract.build.parent.original.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        preflight=q.json('implementation/p09/evidence/p09-151-current-SQL-execution.preflight-run02.v1.json')
        s.require(preflight['state']=='PASS_CURRENT39_READ_ONLY_PREREQUISITE_CHECK_NOT_SQL_OR_GATE'
            and preflight['source_closing_exact'] and preflight['resource_stop_reason'] is None
            and preflight['resource_watcher_cleanup_confirmed'] and preflight['actual_SQL_executed'] is False
            and preflight['Docker_read_only_executed'] is True,'AUDIT_PREFLIGHT_READ_ONLY')
        prerequisite=preflight['preflight'];profiles=prerequisite['owned_host_job_profiles']
        s.require(prerequisite['diagnosis']=='FIXED_LOCAL_IMAGE_ABSENT' and prerequisite['ready'] is False
            and len(prerequisite['commands'])==len(profiles)==2
            and prerequisite['commands'][0]['exact_identity_accepted'] is True
            and prerequisite['commands'][1]['pinned_image_not_found_error'] is True
            and prerequisite['container_created'] is False and prerequisite['image_pulled_or_removed'] is False
            and prerequisite['Docker_daemon_or_WSL_contained_in_host_Job'] is False,'AUDIT_PREFLIGHT_FIXED_IMAGE_ABSENT')
        for profile in profiles:
            s.require(all(profile[k] is True for k in ('worker_created','job_assigned','target_authorized','owned_tree_empty',
                'cleanup_confirmed','job_handle_closed')) and profile['limits_readback']['verified']
                and profile['limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and profile['limits_readback']['affinity_mask']==1
                and profile['last_job_accounting']['active_processes']==0,'AUDIT_PREFLIGHT_HOST_CLEANUP')
        for pin in preflight['bound_input_pins']:s.require(q.pin(pin['path'])==pin,'AUDIT_PREFLIGHT_INPUT')
        light=q.json('implementation/p09/evidence/p09-151-current-SQL-execution.light-run03.v1.json')
        s.require(light['state']=='PASS_CURRENT39_SQL_EXECUTION_CONTRACT_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and light['tests_run']==light['tests_passed']==36 and light['source_closing_exact'],'AUDIT_LIGHT36')
        for pin in light['bound_input_pins']:s.require(q.pin(pin['path'])==pin,'AUDIT_LIGHT_CURRENT_INPUT')
        for index,archive_name in enumerate(ARCHIVES):
            archive=q.json(archive_name);failed=q.json(archive['failed_receipt_pin']['path'])
            s.require(q.pin(archive['failed_receipt_pin']['path'])==archive['failed_receipt_pin']
                and failed['state']=='FAILED_NOT_ACCEPTED' and failed['actual_SQL_executed'] is False,'AUDIT_FAILED_RECEIPT_PRESERVED')
            if index==0:s.require(failed['tests_run']==failed['tests_passed']==35 and failed['mode']=='light','AUDIT_FAILED_LIGHT_SCOPE')
            else:s.require(failed['mode']=='preflight' and failed['error_code']=='SQL_P151_PREFLIGHT_EXACT_LOCAL_DOCKER'
                and failed['executions']==[],'AUDIT_FAILED_CASE_GUARD_SCOPE')
            for item in archive['files']:
                raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
                s.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                    and pin in failed['bound_input_pins'],'AUDIT_FAILURE_WHOLE_SOURCE')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_durable_negative_sql_admission','test_durable_negative_sql_execution','test_durable_negative_sql_preflight'))
        with patch('subprocess.Popen',side_effect=AssertionError('P151_EXEC_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_EXEC_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P151_EXEC_AUDIT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==36 and not checked.skipped,'AUDIT_FRESH_CONTRACT36')
        q.finish();out.update(state='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,contract_tests_passed=36,current_Rust_input_count=785,compiled_source_count=846,
            protected_executables_exact=53,required_check_count=39,product_entrypoint_connected=True,
            pre_backend_actual_OS_event_and_owned_tree_qualified=True,original_driver_failure_and_final_hash_false_preserved=True,
            Docker_prerequisite_refreshed_read_only=True,actual_SQL_backend_prerequisite='FIXED_LOCAL_IMAGE_ABSENT',
            current_runtime_executable_pin=exe,actual_cancel_owned_job_profile=parent['owned_job_profile'],
            preflight_owned_job_profiles=profiles,failed_receipts_and_whole_sources_preserved=True,
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['resource_samples']),
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['resource_samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=s.closed_error(error)
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='SQL_P151_EXEC_AUDIT_FINAL_FRESHNESS'
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] and not resources.reason \
        and out.get('resource_watcher_cleanup_confirmed') else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    raise SystemExit(audit(args.run,args.audit_run))
