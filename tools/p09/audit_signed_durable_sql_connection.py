"""Independent final-byte audit; no Docker/SQL/native launch, no phase promotion."""
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
import run_signed_durable_sql_probe as runtime

c=runtime.c
SELF='tools/p09/audit_signed_durable_sql_connection.py'
FAILURE_ARCHIVES=(
    'implementation/p09/source-archive/p09-150-pre-SQL-light-fixture-fix-r29/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-150-pre-SQL-policy-key-fixture-fix-r29/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-150-pre-SQL-root-recovery-mock-fix-r29/source-preimages.v1.json')


def require(ok,code):runtime.require(ok,'AUDIT_'+code)


def audit(product_run,audit_run):
    resources,q,started=runtime.SQLRuntimeResources(),None,time.monotonic()
    destination=runtime.subject.scoped_path(
        f'implementation/p09/evidence/p09-150-durable-SQL-connection.terminal-audit-run{audit_run:02}.v1.json',fresh=True)
    out=dict(schema_version='hwpx-agent.p09-signed-durable-SQL-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,audit_actual_SQL_Docker_native_or_child_started=False,raw_logs_included=False,
        resource_samples=resources.samples,full_durable_DS01_DS09_qualified=False,production_key_custody_qualified=False,
        independent_restart_qualified=False,native_qualified=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        product_complete=False,remaining_non_permission_work_units=76,PC_freeze_resolved=False)
    try:
        resources.admit();q=runtime.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-150-durable-SQL-connection.product-run{product_run:02}.v1.json'
        row=q.json(name);out['runtime_receipt_pin']=q.reader.snapshots[name]
        complete=row['state']==runtime.PASS_PRODUCT
        require((complete or row['state']=='FAILED_NOT_ACCEPTED'
            and row['error_code']=='SQL_EXECUTION_DURABLE_COMPONENT_NOT_ACCEPTED') and row['source_freeze_exact_after'] is True
            and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'] is True
            and row['actual_SQL_or_Docker_executed'] is (True if complete else None)
            and len(row['executions'])==1,'RUNTIME_OR_FAILED_PREFLIGHT_CLOSING')
        require(row['mode']=='product' and row['original_body_inverse_exact'] is True
            and row['provided_driver_guard_count_delta']==[842,845] and row['original_source_files_modified'] is False
            and row['native_application_executed'] is False and row['full_durable_blob_store_qualified'] is False
            and row['production_key_custody_qualified'] is False and row['independent_process_restart_qualified'] is False
            and row['P09_gate']=='OPEN' and row['product_complete'] is False,'ADAPTER_PHASE_SCOPE')
        for pin in row['bound_input_pins']:require(q.pin(pin['path'])==pin,'BOUND_INPUT_DRIFT')
        for pin in row['source_freeze']:require(q.pin(pin['path'])==pin,'SOURCE_DRIFT')
        view,exe,binding=runtime.contract.bind_probe_build(q,runtime.contract.BUILD_PIN['path'])
        require(row['current_build_receipt_pin']==runtime.contract.BUILD_PIN and row['closing_audit_pin']==runtime.contract.CLOSING_PIN
            and row['compiled_source_count']==len(view['source_freeze'])==845 and row['current_Rust_input_count']==784
            and row['protected_executables']==51 and row['executable_pin']==exe and row['current_build_binding']==binding,'CURRENT845')
        execution=row['executions'][0];supervised=execution['supervisor']
        require(runtime.subject.host_tree_closed(supervised) and supervised['forced_termination'] is False
            and supervised['parent_event_closed'] is True and supervised['pipe_cleanup_confirmed'] is True
            and supervised['cancel_reason'] is None
            and execution['backend_container_cleanup_confirmed'] is (True if complete else None),'OWNED_TERMINAL')
        original=q.json(execution['original_receipt_pin']['path'])
        require(q.pin(execution['original_receipt_pin']['path'])==execution['original_receipt_pin']
            and original['container_removed'] is complete and original['source_freeze_exact_after'] is complete
            and original['protected_executables_exact_after'] is complete and original['resource_watcher_cleanup_confirmed'] is True
            and original['resource_stop_reason'] is None and len(original['migrations_applied'])==(22 if complete else 0)
            and len(original['protected_executables'])==57,'ORIGINAL_SQL22')
        for pin in original['source_freeze']+original['protected_executables']:require(q.pin(pin['path'])==pin,'ORIGINAL_FINAL_DRIFT')
        if complete:
            scope=runtime.verify_component(execution,q);require(scope==row['component_scope'],'COMPONENT_SCOPE')
            checked=runtime.subject.ownership.load_intent(execution['parent_nonce'],'approval')
            require(q.pin(checked['journal_pin']['path'])==checked['journal_pin']==execution['journal_pin']
                and checked['intent']['run_id']==original['run_id'],'INTENT_BINDING')
            holder=runtime.root.OwnedRootHolder(execution['parent_nonce'],str(c.ROOT/exe['path']))
            holder.run=checked['intent']['run_id'];holder.root=c.ROOT/runtime.root.root_name(holder.run)
            root=holder.manifest(q);require(root==execution['retained_owned_ciphertext_root'],'WHOLE_DISK_ROOT_EXACT')
            out['retained_owned_ciphertext_root']=root
        else:
            worker=supervised['worker_result'];accounted=worker['accounted_call']
            require(execution['state']=='ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE'
                and original['state']=='FAIL_CLOSED' and original['failed_stage']=='cached_image_identity'
                and original['error_code']=='pinned_local_image_missing' and original['last_command_exit_code']==1
                and original['container_id'] is None and original['actual_SQL_executed'] is False
                and original['actual_Rust_DB_adapter_executed'] is False and original['original_product_consumer_executed'] is False
                and worker['journal_write_count']==0 and worker['journal_pin'] is None
                and not runtime.subject.ownership.journal_path(execution['parent_nonce']).exists()
                and execution['journal_pin'] is None and execution['fallback_cleanup'] is None
                and execution['retained_owned_ciphertext_root']==dict(created=False,retained=True,files=[])
                and accounted['driver_return_code']==1 and accounted['source_final_hash_completed'] is False,'FAILED_PRE_CONTAINER_NOT_SUCCESS')
            diagnostic=q.json('implementation/p09/evidence/p09-150-durable-SQL-backend.read-only-run01.v1.json')
            require(diagnostic['state']=='PASS_READ_ONLY_DIAGNOSIS_ONLY_NOT_SQL_OR_GATE'
                and diagnostic['diagnosis']=='FIXED_LOCAL_IMAGE_ABSENT' and diagnostic['source_closing_exact'] is True
                and diagnostic['resource_stop_reason'] is None and diagnostic['resource_watcher_cleanup_confirmed'] is True
                and diagnostic['commands'][0]['exit_code']==0 and diagnostic['commands'][1]['pinned_image_not_found_error'] is True
                and diagnostic['image_pulled_or_removed'] is False and diagnostic['backend_started_or_stopped'] is False,'READ_ONLY_BACKEND_DIAGNOSIS')
            for pin in diagnostic['bound_input_pins']:require(q.pin(pin['path'])==pin,'DIAGNOSTIC_SOURCE_DRIFT')
            scope=dict(current_signed_SQL_case_qualified=False,SQL_executed=False,Docker_read_only_inspection_executed=True,
                owned_container_requested=False,owned_ciphertext_root_created=False,original_driver_final_freshness_qualified=False,
                image_prerequisite='FIXED_LOCAL_IMAGE_ABSENT',backend_diagnosis_only=True)
        out['runtime_owned_job_final']=supervised['owned_job_profile']['last_job_accounting']
        out['read_only_Docker_job_final']=original['owned_host_job_profiles'][-1]['last_job_accounting']
        for archive_name in FAILURE_ARCHIVES:
            archive=q.json(archive_name);pin=archive['failed_receipt_pin'];failed=q.json(pin['path'])
            require(q.pin(pin['path'])==pin and failed['state']=='FAILED_NOT_ACCEPTED'
                and failed['tests_passed']<failed['tests_run'] and failed['actual_SQL_or_Docker_executed'] is False,'FAILURE_NOT_RESTAMPED')
            frozen={p['path']:p for p in failed['source_freeze']}
            for item in archive['files']:
                raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
                require(hashlib.sha256(raw).hexdigest()==pin['sha256'] and len(raw)==pin['bytes']
                    and frozen[pin['path']]==pin,'FAILED_SOURCE_WHOLE')
        light_name='implementation/p09/evidence/p09-150-durable-SQL-connection.light-run05.v1.json'
        light=q.json(light_name);require(light['state']==runtime.PASS_LIGHT and light['tests_run']==light['tests_passed']==40
            and light['source_freeze_exact_after'] is True and light['actual_SQL_or_Docker_executed'] is False,'LIGHT40_RECEIPT')
        for pin in light['source_freeze']:require(q.pin(pin['path'])==pin,'CURRENT_LIGHT40_INPUTS')
        before={t.ident for t in threading.enumerate()};sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_signed_durable_sql_connection','test_signed_durable_sql_execution'))
        with patch('subprocess.Popen',side_effect=AssertionError('DURABLE_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('DURABLE_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('DURABLE_AUDIT_THREAD_FORBIDDEN')):
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        require(result.wasSuccessful() and not result.skipped and result.testsRun==40,'FRESH_LIGHT40')
        require({t.ident for t in threading.enumerate()}==before,'NO_NEW_THREADS')
        q.finish();out.update(state='PASS_ONE_CURRENT_SIGNED_DURABLE_SQL_CLOSING_NOT_FULL_DURABLE_NATIVE_OR_GATE' if complete
            else 'PASS_CURRENT_BUILD_AND_FAILED_PREFLIGHT_CLOSING_ONLY_NOT_SQL_DURABLE_OR_GATE',
            source_closing_exact=True,tests_run=40,tests_passed=40,current_Rust_inputs=784,current_SQL_source_view=845,
            protected_runtime_parent_executables=51,original_SQL_protected_executables=57,executable_pin=exe,
            current_build_receipt_pin=runtime.contract.BUILD_PIN,build_closing_audit_pin=runtime.contract.CLOSING_PIN,
            original_SQL_receipt_pin=execution['original_receipt_pin'],all_original_root_checks_preserved=27,
            additional_durable_checks=list(runtime.driver.ROOT_EXTRA+runtime.driver.CONSUMER_EXTRA),
            failed_light_and_whole_sources_preserved=True,owned_host_tree_empty=True,owned_backend_container_absent=True,
            original_SQL_run_promoted_to_success=False,original_SQL_run_final_freshness_qualified=complete,
            component_scope=scope,original_body_inverse_exact=True,guard_count_delta=[842,845])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['state']='FAILED_NOT_ACCEPTED';out['error_code']=runtime.closed_error(error)
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='SQL_EXECUTION_DURABLE_AUDIT_FINAL'
        runtime.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','tests_run','tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] \
        and out.get('resource_watcher_cleanup_confirmed') is True and resources.reason is None else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    raise SystemExit(audit(args.run,args.audit_run))
