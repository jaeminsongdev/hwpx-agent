"""Current39-check SQL caller with unchanged original owned cancel/grace/fallback.

light/preflight/pre-cancel/product 모드는 명시적이다. pre-cancel은 실제 OS Job/event
증거만 제공하며 SQL 실행 중 취소나 backend cleanup 성공으로 승격하지 않는다.
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
import durable_negative_sql_contract as contract
import durable_negative_sql_driver as driver
import durable_negative_sql_preflight as preflight
import signed_durable_sql_root as root
import sql_owned_execution as subject
from sql_call_supervisor import supervise_owned_call
from sql_cooperative_cancel import CancelEvent,CANCEL_REASON
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from run_supervised_sql_probe import SOURCES as SUPERVISION_SOURCES

c=contract.c
SELF='tools/p09/run_durable_negative_sql_probe.py'
TEST='tools/p09/tests/test_durable_negative_sql_execution.py'
PREFLIGHT_TEST='tools/p09/tests/test_durable_negative_sql_preflight.py'
ADMISSION_PIN=dict(path='implementation/p09/evidence/p09-151-SQL-admission.terminal-audit-run01.v1.json',
    bytes=283975,sha256='d5bdda244d37851c51afa14cdaa85487e267fc5d30579c12be14ab44bb17b1cb')
SOURCES=list(dict.fromkeys([SELF,TEST,PREFLIGHT_TEST,preflight.SELF,*contract.SOURCES,*SUPERVISION_SOURCES,
    'tools/p09/sql_cooperative_cancel.py','tools/p09/sql_owned_execution.py',
    'tools/p09/sql_call_supervisor.py','tools/p09/signed_durable_sql_root.py',ADMISSION_PIN['path'],
    'implementation/p09/source-archive/p09-151-pre-current-execution-count-fix-r32/source-preimages.v1.json',
    'implementation/p09/source-archive/p09-151-pre-local-docker-case-fix-r32/source-preimages.v1.json']))


def require(ok,code):c.require(ok,'SQL_P151_EXECUTION_'+code)


def closed_error(error):
    value=str(error) if isinstance(error,ValueError) else 'SQL_P151_EXECUTION_OPERATION_FAILED'
    return value if len(value)<=160 and re.fullmatch(r'SQL_P151_[A-Z0-9_]+|SQL_[A-Z_]+|STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+|sql_[a-z_]+|input_changed_during_audit',value) \
        else 'SQL_P151_EXECUTION_REDACTED_FAILURE'


def arguments(receipt_run,index,input_mode,expected):
    require(type(receipt_run) is int and 1<=receipt_run<=90 and type(index) is int and 0<=index<36,'SELECTION_SCOPE')
    require((input_mode,expected) in {('original','unchanged'),('numeric_derivative','changed')},'CASE_SCOPE')
    receipt=f'implementation/p09/evidence/p09-146-corpus-consumer-run{receipt_run:02}.v1.json'
    subject.scoped_path(receipt,fresh=True)
    return (contract.BUILD_PIN['path'],receipt,index,input_mode,expected,'approval')


def make_driver(reader,nonce):
    made,holder=driver.make_driver(reader,nonce)
    original=made.consumer_sources
    def current_sources(binding):return list(dict.fromkeys([*original(binding),*SOURCES]))
    made.consumer_sources=current_sources
    require(made.ROOT_CHECKS==driver.required_checks() and len(made.ROOT_CHECKS)==39
        and made.CHECKS==driver.prior.original.CHECKS and made.resource_policy()==driver.prior.original.resource_policy(),'EXACT_PROVIDED_DRIVER')
    return made,holder


def worker(nonce,event_name,receipt_run,index,input_mode,expected):
    require(Path.cwd().resolve()==c.ROOT,'WORKER_ROOT')
    args=arguments(int(receipt_run),int(index),input_mode,expected);subject.ownership.uuid_value(nonce)
    require(not subject.ownership.journal_path(nonce).exists(),'FRESH_INTENT')
    event=CancelEvent.open(event_name);row=None;prep=SQLRuntimeResources();reader=None
    try:
        prep.admit();reader=LiveSQLReader(prep)
        for name in SOURCES:reader.pin(name)
        made,_=make_driver(reader,nonce);reader.finish()
        require(prep.reason is None,'PREPARATION_RESOURCE_STOP')
        row=subject.journalled_driver_call(made,args,event,nonce,'approval')
    finally:
        checked={};finish_watcher(prep,checked);event.close()
        if row is not None:row['child_event_closed']=event.closed
    subject.decode_worker(json.dumps(row),nonce,'approval',args[1]);print(json.dumps(row));return 0


def execute(args,resources,reader,*,pre_cancel=False):
    require(type(pre_cancel) is bool,'PRE_CANCEL_MODE')
    nonce,event,parent=str(uuid.uuid4()),CancelEvent.create(),None
    try:
        require(not subject.ownership.journal_path(nonce).exists(),'FRESH_INTENT')
        if pre_cancel:event.request();require(event.is_set() is True,'PRE_CANCEL_SIGNAL_READBACK')
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
    checked.update(pre_cancel_signal_sent_before_supervision=pre_cancel,
        provided_driver_adapter=dict(original_source_files_modified=False,guard_count_delta=[842,846],
            original_body_inverse_exact=True,original_SQL_security_and_resource_policy_unchanged=True,
            exact_DI_overrides=['bind_probe_build','consumer_sources','ROOT_CHECKS','OwnedSQLJobFactory'],
            all_original_root_checks_preserved=27,prior_durable_checks_preserved=4,new_private_DS06_checks=8,
            exact_required_check_count=39,current_runtime_scheme=contract.SCHEME,
            collector_modified_false_is_relative_to_provided_adapter=True))
    holder=root.OwnedRootHolder(nonce,str(c.ROOT/contract.build.executable_name(1)))
    if subject.ownership.journal_path(nonce).exists():
        intent=subject.ownership.load_intent(nonce,'approval')['intent'];candidate=subject.scoped_path(root.root_name(intent['run_id']))
        if candidate.exists():holder.run=intent['run_id'];holder.root=candidate
    checked['retained_owned_ciphertext_root']=holder.manifest(reader)
    return checked


def verify_pre_cancelled(execution,args):
    parent=execution['supervisor'];worker=parent['worker_result'];accounted=worker['accounted_call']
    require(execution['state']=='ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE'
        and execution['pre_cancel_signal_sent_before_supervision'] is True
        and parent['state']=='OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE'
        and parent['forced_termination'] is False and parent['parent_event_closed'] is True
        and parent['pipe_cleanup_confirmed'] is True and subject.host_tree_closed(parent),'PRE_CANCEL_HOST_TERMINAL')
    profile=parent['owned_job_profile'];limits=profile['limits_readback']
    require(all(profile[key] is True for key in ('worker_created','job_assigned','target_authorized'))
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] and limits['breakaway_disabled'],'PRE_CANCEL_ACTUAL_GO_AND_LIMITS')
    require(worker['child_event_closed'] is True and worker['journal_write_count']==0 and worker['journal_pin'] is None
        and accounted['state']=='ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS'
        and accounted['driver_return_code'] is None and accounted['driver_error_code']==CANCEL_REASON
        and accounted['cooperative_resource_count']==1 and accounted['cooperative_resource_stop_reason']==CANCEL_REASON
        and accounted['cooperative_resource_stop_latched'] is True and accounted['original_resource_type_inherited'] is True
        and accounted['original_driver_dependencies_restored'] is True
        and accounted['reader_count']==0 and accounted['source_final_hash_completed'] is False,'PRE_CANCEL_ORIGINAL_STOP')
    require(execution['journal_pin'] is None and execution['fallback_cleanup'] is None
        and execution['original_receipt_pin'] is None and execution['backend_container_cleanup_confirmed'] is None
        and execution['retained_owned_ciphertext_root']['created'] is False
        and not subject.ownership.journal_path(execution['parent_nonce']).exists()
        and not subject.scoped_path(args[1]).exists(),'PRE_CANCEL_NO_BACKEND_OR_RECEIPT')
    return dict(actual_pre_backend_OS_event_and_owned_host_tree_qualified=True,
        current39_check_driver_cancelled_before_original_reader_creation=True,original_failure_preserved=True,
        original_final_hash_not_promoted=True,actual_SQL_executed=False,
        live_SQL_cancellation_and_backend_cleanup_qualified=False,all_36_sources_qualified=False,
        full_durable_DS01_DS09_qualified=False,independent_process_restart_qualified=False)


def verify_component(execution,reader):
    require(execution['state']=='ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE','COMPONENT_NOT_ACCEPTED')
    receipt=reader.json(execution['original_receipt_pin']['path']);result=receipt['product_probe']['result']
    manifest=execution['retained_owned_ciphertext_root'];binding=receipt['compiled_build_binding']
    require(binding['scheme']==contract.SCHEME and binding['receipt_pin']==contract.BUILD_PIN
        and binding['compiled_source_count']==846 and binding['required_check_count']==39
        and receipt['product_executable_pin']['path']==contract.build.executable_name(1)
        and result['checks']==driver.required_checks() and result['failed_stage'] is None
        and result['durable_blob_store_qualified'] is False and receipt['durable_blob_store_qualified'] is False
        and receipt['P09_gate']=='OPEN' and receipt['product_complete'] is False,'CURRENT_COMPONENT_SCOPE')
    require(manifest['created'] is True and manifest['owner_exact'] is True and manifest['run_id']==receipt['run_id']
        and manifest['retained'] is True and len(manifest['files'])>=2 and manifest['total_bytes']>len(root.marker(receipt['run_id']))
        and manifest['OS_ACL_qualified'] is False and manifest['independent_restart_or_key_custody_qualified'] is False,'DISK_ROOT_PROOF')
    return dict(current_signed_SQL_case_with_private_DS06_controls_qualified=True,
        original27_plus_durable4_plus_private_DS06_eight_exact=True,fresh_handle_same_process_original_keys=True,
        source_inputs_covered=1,all_36_sources_qualified=False,full_durable_DS01_DS09_qualified=False,
        production_key_custody_qualified=False,independent_process_restart_qualified=False,PC_freeze_resolved=False)


def bind_current(reader):
    require(reader.pin(ADMISSION_PIN['path'])==ADMISSION_PIN,'IMMUTABLE_CURRENT_ADMISSION')
    prior=reader.json(ADMISSION_PIN['path'])
    require(prior['state']=='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
        and prior['source_closing_exact'] and prior['compiled_source_count']==846 and prior['required_check_count']==39,
        'CURRENT_ADMISSION_SCOPE')
    for pin in prior['bound_input_pins']:require(reader.pin(pin['path'])==pin,'CURRENT_ADMISSION_INPUT_DRIFT')
    view,exe,binding=contract.bind_probe_build(reader,contract.BUILD_PIN['path'])
    return view,exe,binding


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','preflight','pre-cancel','product'),required=True)
    parser.add_argument('--run',type=int,choices=range(1,100),required=True);parser.add_argument('--receipt-run',type=int)
    parser.add_argument('--source-index',type=int,default=0)
    parser.add_argument('--input-mode',choices=('original','numeric_derivative'),default='original')
    parser.add_argument('--expected',choices=('unchanged','changed'),default='unchanged');args=parser.parse_args()
    require(Path.cwd().resolve()==c.ROOT,'PARENT_ROOT')
    require(args.mode not in {'product','pre-cancel'} or args.receipt_run is not None,'EXPLICIT_NEW_RECEIPT')
    destination=subject.scoped_path(f'implementation/p09/evidence/p09-151-current-SQL-execution.{args.mode}-run{args.run:02}.v1.json',fresh=True)
    call=arguments(args.receipt_run,args.source_index,args.input_mode,args.expected) if args.mode in {'product','pre-cancel'} else None
    resources,q,started=SQLRuntimeResources(),None,time.monotonic()
    row=dict(schema_version='hwpx-agent.p09-current-DS06-owned-SQL-execution/v1',state='FAILED_NOT_ACCEPTED',mode=args.mode,
        source_closing_exact=False,resource_samples=resources.samples,tests_run=0,tests_passed=0,failed_tests=[],
        executions=[],actual_SQL_executed=False,Docker_read_only_executed=False,
        actual_Docker_container_operations_executed=False,actual_owned_worker_executed=False,native_application_executed=False,
        full_SQL_wrapper_cancellation_and_cleanup_qualified=False,full_durable_DS01_DS09_qualified=False,
        independent_process_restart_or_key_custody_qualified=False,PC_freeze_resolved=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        new_git_started=False,system_or_Defender_or_WSL_settings_changed=False,raw_logs_included=False)
    try:
        resources.admit();q=LiveSQLReader(resources)
        for name in SOURCES:q.pin(name)
        made,_=make_driver(q,str(uuid.uuid4()));require(made.ROOT_CHECKS==driver.required_checks(),'EXACT39_CHECK_LIST')
        row.update(provided_driver_guard_count_delta=[842,846],original_body_inverse_exact=True,required_check_names=made.ROOT_CHECKS,
            original_root_checks_retained=27,prior_durable_checks_retained=4,new_DS06_checks=8,product_entrypoint_connected=True)
        if args.mode=='light':
            sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
            suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
                ('test_durable_negative_sql_admission','test_durable_negative_sql_execution','test_durable_negative_sql_preflight'))
            with patch('subprocess.Popen',side_effect=AssertionError('P151_EXEC_LIGHT_CHILD_FORBIDDEN')), \
                    patch('subprocess.run',side_effect=AssertionError('P151_EXEC_LIGHT_CHILD_FORBIDDEN')), \
                    patch('threading.Thread.start',side_effect=AssertionError('P151_EXEC_LIGHT_THREAD_FORBIDDEN')):
                checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            failed={getattr(t,'test_case',t).id() for t,_ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failed),failed_tests=sorted(n.split('.')[-1] for n in failed))
            require(checked.wasSuccessful() and not checked.skipped and checked.testsRun==36,'LIGHT36')
            row['state']='PASS_CURRENT39_SQL_EXECUTION_CONTRACT_ONLY_NOT_SQL_NATIVE_OR_GATE'
        else:
            if args.mode in {'preflight','product'}:
                row['Docker_read_only_executed']=None;row['preflight']=preflight.check(resources,q)
                row['Docker_read_only_executed']=True
                if args.mode=='product':require(row['preflight']['ready'] is True,'PRODUCT_FIXED_LOCAL_IMAGE_NOT_READY')
            if args.mode=='preflight':row['state']='PASS_CURRENT39_READ_ONLY_PREREQUISITE_CHECK_NOT_SQL_OR_GATE'
            else:
                view,exe,binding=bind_current(q)
                row.update(compiled_source_count=len(view['source_freeze']),current_Rust_input_count=785,
                    protected_executables_exact=53,executable_pin=exe,current_build_binding=binding)
                resources.start();row['actual_owned_worker_executed']=None
                if args.mode=='product':row['actual_SQL_executed']=None;row['actual_Docker_container_operations_executed']=None
                execution=execute(call,resources,q,pre_cancel=args.mode=='pre-cancel');row['executions'].append(execution)
                profile=execution['supervisor'].get('owned_job_profile') or {}
                row['actual_owned_worker_executed']=profile.get('target_authorized') if type(profile.get('target_authorized')) is bool else None
                if args.mode=='pre-cancel':
                    row['component_scope']=verify_pre_cancelled(execution,call)
                    row['state']='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_ONLY_NOT_SQL_OR_GATE'
                else:
                    original=execution.get('original_receipt_summary') or {}
                    observed=original.get('actual_SQL_executed')
                    row['actual_SQL_executed']=observed if type(observed) is bool else None
                    row['component_scope']=verify_component(execution,q)
                    row['actual_Docker_container_operations_executed']=True
                    row['state']='PASS_ONE_CURRENT39_SIGNED_DURABLE_SQL_COMPONENT_NOT_FULL_DS_NATIVE_OR_GATE'
        helpers=set()
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers):q.pin(name)
        row['imported_helper_inventory']=sorted(helpers);q.finish();row['source_closing_exact']=True
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        row['state']='FAILED_NOT_ACCEPTED';row['error_code']=closed_error(error)
    finally:
        if q is not None and not q.finished:
            try:q.finish();row['source_closing_exact']=True
            except (ValueError,OSError):row['state']='FAILED_NOT_ACCEPTED';row['final_freshness_error']='SQL_P151_EXECUTION_FINAL_FRESHNESS'
        finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
        if resources.reason:row['state']='FAILED_NOT_ACCEPTED'
        if q is not None:row['IO']=q.summary();row['bound_input_pins']=list(q.reader.snapshots.values())
        row['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
        print(json.dumps({k:row.get(k) for k in ('state','tests_run','tests_passed','failed_tests','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if row['state'].startswith('PASS_') and row['source_closing_exact'] and not resources.reason \
        and row.get('resource_watcher_cleanup_confirmed') else 2


if __name__=='__main__':
    if len(sys.argv)==8 and sys.argv[1]=='--worker':raise SystemExit(worker(*sys.argv[2:]))
    raise SystemExit(main())
