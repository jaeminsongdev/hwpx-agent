"""Explicit light/admission/product modes. A single case is NOT the P09 Gate.

원래 SQL 본문은 842->845 guard 한 곳만 변환한다. 기존 collector의 modified=false는
collector가 제공받은 module/policy를 바꾸지 않았다는 뜻이며, 이 별도 adapter의
guard/DI/check-list 변경을 숨기거나 원래 driver byte-identical로 주장하지 않는다.
"""
import argparse
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
import uuid

import conservative_maintenance as c
import signed_durable_sql_contract as contract
import signed_durable_sql_driver as driver
import signed_durable_sql_root as root
import sql_owned_execution as subject
from sql_call_supervisor import supervise_owned_call
from sql_cooperative_cancel import CancelEvent
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from run_supervised_sql_probe import SOURCES as SUPERVISION_SOURCES

SELF='tools/p09/run_signed_durable_sql_probe.py'
PASS_LIGHT='PASS_CURRENT_DURABLE_SQL_CONNECTION_CONTRACT_ONLY_NOT_SQL_OR_GATE'
PASS_ADMISSION='PASS_CURRENT_BUILD_ADMISSION_ONLY_NOT_SQL_DURABLE_OR_GATE'
PASS_PRODUCT='PASS_ONE_CURRENT_SIGNED_DURABLE_SQL_COMPONENT_NOT_FULL_DURABLE_NATIVE_OR_GATE'
SOURCES=list(dict.fromkeys([*contract.SOURCES,*SUPERVISION_SOURCES,
    'tools/p09/signed_durable_sql_root.py','tools/p09/signed_durable_sql_driver.py']))


def require(ok,code):c.require(ok,'SQL_EXECUTION_DURABLE_'+code)


def closed_error(error):
    value=str(error) if isinstance(error,ValueError) else 'SQL_EXECUTION_DURABLE_OPERATION_FAILED'
    return value if len(value)<=160 and re.fullmatch(r'SQL_[A-Z_]+|STOP_[A-Z_]+|sql_[a-z_]+|input_changed_during_audit',value) \
        else 'SQL_EXECUTION_DURABLE_REDACTED_FAILURE'


def arguments(receipt_run,index,input_mode,expected):
    require(type(receipt_run) is int and 1<=receipt_run<=90 and type(index) is int and 0<=index<36,'SELECTION_SCOPE')
    require((input_mode,expected) in {('original','unchanged'),('numeric_derivative','changed')},'CASE_SCOPE')
    receipt=f'implementation/p09/evidence/p09-146-corpus-consumer-run{receipt_run:02}.v1.json'
    subject.scoped_path(receipt,fresh=True)
    return (contract.BUILD_PIN['path'],receipt,index,input_mode,expected,'approval')


def worker(nonce,event_name,receipt_run,index,input_mode,expected):
    require(Path.cwd().resolve()==c.ROOT,'WORKER_ROOT')
    args=arguments(int(receipt_run),int(index),input_mode,expected)
    subject.ownership.uuid_value(nonce)
    require(not subject.ownership.journal_path(nonce).exists(),'FRESH_INTENT')
    event,row,prep=CancelEvent.open(event_name),None,SQLRuntimeResources()
    reader=None
    try:
        prep.admit();reader=LiveSQLReader(prep)
        made,_=driver.make_driver(reader,nonce);reader.finish()
        require(prep.reason is None,'PREPARATION_RESOURCE_STOP')
        row=subject.journalled_driver_call(made,args,event,nonce,'approval')
    finally:
        checked={};finish_watcher(prep,checked)
        event.close()
        if row is not None:row['child_event_closed']=event.closed
    subject.decode_worker(json.dumps(row),nonce,'approval',args[1])
    print(json.dumps(row));return 0


def execute(args,resources,reader):
    nonce,event,parent=str(uuid.uuid4()),CancelEvent.create(),None
    try:
        require(not subject.ownership.journal_path(nonce).exists(),'FRESH_INTENT')
        run=int(Path(args[1]).name.removeprefix('p09-146-corpus-consumer-run').removesuffix('.v1.json'))
        parent=supervise_owned_call([sys.executable,'-B',str(c.ROOT/SELF),'--worker',nonce,event.name,
            str(run),str(args[2]),args[3],args[4]],resources,event,
            lambda output:subject.decode_worker(output,nonce,'approval',args[1]),maximum_seconds=690,grace_seconds=135)
    finally:
        try:event.close()
        except (ValueError,OSError) as error:
            if parent is None:parent=dict(state='FAILED_NOT_ACCEPTED',worker_result=None,owned_job_profile=None)
            parent['parent_event_close_error_code']=closed_error(error)
        if parent is not None:parent['parent_event_closed']=event.closed
    checked=subject.finalize_owned_call(parent,nonce,'approval',args,resources,reader,
        shutil.which('docker') if subject.ownership.journal_path(nonce).exists() else None)
    checked['provided_driver_adapter']=dict(original_source_files_modified=False,guard_count_delta=[842,845],
        original_body_inverse_exact=True,original_SQL_security_and_resource_policy_unchanged=True,
        exact_DI_overrides=['bind_probe_build','consumer_sources','ROOT_CHECKS','OwnedSQLJobFactory'],
        all_original_root_checks_preserved=27,additional_durable_checks=list(driver.ROOT_EXTRA+driver.CONSUMER_EXTRA),
        collector_modified_false_is_relative_to_provided_adapter=True)
    holder=root.OwnedRootHolder(nonce,str(c.ROOT/contract.build.executable_name(5)))
    if subject.ownership.journal_path(nonce).exists():
        intent=subject.ownership.load_intent(nonce,'approval')['intent']
        candidate=subject.scoped_path(root.root_name(intent['run_id']))
        if candidate.exists():holder.run=intent['run_id'];holder.root=candidate
    checked['retained_owned_ciphertext_root']=holder.manifest(reader)
    return checked


def verify_component(execution,reader):
    require(execution['state']=='ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE','COMPONENT_NOT_ACCEPTED')
    receipt=reader.json(execution['original_receipt_pin']['path'])
    result=receipt['product_probe']['result'];manifest=execution['retained_owned_ciphertext_root']
    require(receipt['compiled_build_binding']['scheme']=='p150_current_runtime_r05'
        and receipt['compiled_build_binding']['receipt_pin']==contract.BUILD_PIN
        and receipt['product_executable_pin']['path']==contract.build.executable_name(5)
        and result['checks']==driver.required_checks() and result['failed_stage'] is None
        and result['durable_blob_store_qualified'] is False and receipt['durable_blob_store_qualified'] is False
        and receipt['P09_gate']=='OPEN' and receipt['product_complete'] is False,'CURRENT_COMPONENT_SCOPE')
    require(manifest['created'] is True and manifest['owner_exact'] is True
        and manifest['run_id']==receipt['run_id'] and manifest['retained'] is True
        and len(manifest['files'])>=2 and manifest['total_bytes']>len(root.marker(receipt['run_id']))
        and manifest['OS_ACL_qualified'] is False and manifest['independent_restart_or_key_custody_qualified'] is False,
        'DISK_ROOT_PROOF')
    return dict(current_signed_SQL_case_qualified=True,fresh_handle_same_process_original_keys=True,
        original_27_plus_durable_4_checks_exact=True,source_inputs_covered=1,all_36_sources_qualified=False,
        full_durable_DS01_DS09_qualified=False,production_key_custody_qualified=False,
        independent_process_restart_qualified=False,PC_freeze_resolved=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','admission','product'),required=True)
    parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--receipt-run',type=int);parser.add_argument('--source-index',type=int,default=0)
    parser.add_argument('--input-mode',choices=('original','numeric_derivative'),default='original')
    parser.add_argument('--expected',choices=('unchanged','changed'),default='unchanged');args=parser.parse_args()
    require(Path.cwd().resolve()==c.ROOT,'PARENT_ROOT')
    require(args.mode!='product' or args.receipt_run is not None,'PRODUCT_EXPLICIT_RECEIPT')
    destination=subject.scoped_path(f'implementation/p09/evidence/p09-150-durable-SQL-connection.{args.mode}-run{args.run:02}.v1.json',fresh=True)
    call=arguments(args.receipt_run,args.source_index,args.input_mode,args.expected) if args.mode=='product' else None
    resources,reader,started=SQLRuntimeResources(),None,time.monotonic()
    row=dict(schema_version='hwpx-agent.p09-current-signed-durable-SQL-connection/v1',state='FAILED_NOT_ACCEPTED',
        mode=args.mode,source_freeze=[],source_freeze_exact_after=False,resource_samples=resources.samples,
        tests_run=0,tests_passed=0,failed_tests=[],executions=[],actual_SQL_or_Docker_executed=False,
        current_build_consumption_view=False,original_source_files_modified=False,
        provided_driver_guard_count_delta=[842,845],original_body_inverse_exact=False,
        full_durable_blob_store_qualified=False,production_key_custody_qualified=False,
        independent_process_restart_qualified=False,full_SQL_wrapper_cancellation_and_cleanup_qualified=False,
        PC_freeze_resolved=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',product_complete=False,
        remaining_non_permission_work_units=76,native_application_executed=False,
        new_git_started=False,system_or_Defender_or_WSL_settings_changed=False,raw_logs_included=False)
    try:
        resources.admit();reader=LiveSQLReader(resources)
        row['source_freeze']=[reader.pin(n) for n in SOURCES]
        made,_=driver.make_driver(reader,str(uuid.uuid4()))
        require(made.ROOT_CHECKS==driver.required_checks(),'CHECK_LIST')
        row['original_body_inverse_exact']=True
        row['original_root_checks_retained']=27;row['additional_durable_checks']=list(driver.ROOT_EXTRA+driver.CONSUMER_EXTRA)
        if args.mode=='light':
            sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
            suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
                ('test_signed_durable_sql_connection','test_signed_durable_sql_execution'))
            with patch('subprocess.Popen',side_effect=AssertionError('DURABLE_SQL_LIGHT_CHILD_FORBIDDEN')), \
                    patch('subprocess.run',side_effect=AssertionError('DURABLE_SQL_LIGHT_CHILD_FORBIDDEN')), \
                    patch('threading.Thread.start',side_effect=AssertionError('DURABLE_SQL_LIGHT_THREAD_FORBIDDEN')):
                checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            failures={getattr(test,'test_case',test).id() for test,_ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failures),
                failed_tests=sorted(n.split('.')[-1] for n in failures))
            require(checked.wasSuccessful() and not checked.skipped and checked.testsRun==40,'LIGHT_TESTS')
            row['state']=PASS_LIGHT
        else:
            view,exe,binding=contract.bind_probe_build(reader,contract.BUILD_PIN['path'])
            row.update(current_build_consumption_view=True,current_build_receipt_pin=contract.BUILD_PIN,
                closing_audit_pin=contract.CLOSING_PIN,compiled_source_count=len(view['source_freeze']),
                current_Rust_input_count=784,protected_executables=51,executable_pin=exe,
                current_build_binding=binding)
            if args.mode=='admission':row['state']=PASS_ADMISSION
            else:
                resources.start();row['actual_SQL_or_Docker_executed']=None
                execution=execute(call,resources,reader);row['executions'].append(execution)
                original=execution.get('original_receipt_summary') or {}
                row['actual_SQL_or_Docker_executed']=True if original.get('actual_SQL_executed') is True else None
                row['component_scope']=verify_component(execution,reader);row['state']=PASS_PRODUCT
        reader.finish();row['source_freeze_exact_after']=True
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        row['state']='FAILED_NOT_ACCEPTED';row['error_code']=closed_error(error)
    finally:
        if reader is not None and not reader.finished:
            try:reader.finish();row['source_freeze_exact_after']=True
            except (ValueError,OSError):row['state']='FAILED_NOT_ACCEPTED';row['final_freshness_error']='SQL_EXECUTION_DURABLE_FINAL_FRESHNESS'
        finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
        if resources.reason:row['state']='FAILED_NOT_ACCEPTED'
        if reader is not None:row['IO']=reader.summary();row['bound_input_pins']=list(reader.reader.snapshots.values())
        row['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
        print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests','wall_seconds','resource_stop_reason')}))
    return 0 if row['state'].startswith('PASS_') and row['source_freeze_exact_after'] \
        and row.get('resource_watcher_cleanup_confirmed') is True and resources.reason is None else 2


if __name__=='__main__':
    if len(sys.argv)==8 and sys.argv[1]=='--worker':raise SystemExit(worker(*sys.argv[2:]))
    raise SystemExit(main())
