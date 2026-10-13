"""Close admission sources independently; SQL/container/root creation remains NOT_RUN."""
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
import durable_negative_sql_contract as s
import durable_negative_sql_driver as driver

SELF='tools/p09/audit_durable_negative_sql_admission.py'
ARCHIVE='implementation/p09/source-archive/p09-151-pre-SQL-light-helper-closing-r31/source-preimages.v1.json'


def audit(run,audit_run):
    resources=s.build.parent.SQLRuntimeResources();q=None;started=time.monotonic()
    destination=s.build.parent.scoped_path(f'implementation/p09/evidence/p09-151-SQL-admission.terminal-audit-run{audit_run:02}.v1.json',fresh=True)
    out=dict(schema_version='hwpx-agent.p09-ds06-SQL-admission-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,actual_SQL_Docker_native_or_EXE_executed=False,audit_new_child_or_thread_started=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        full_durable_DS01_DS09_qualified=False,actual_SQL_metadata_or_signed_consumer_qualified=False,
        independent_restart_or_key_custody_qualified=False,PC_freeze_resolved=False,raw_logs_included=False,
        resource_samples=resources.samples)
    try:
        resources.admit();q=s.build.parent.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-151-SQL-admission.admission-run{run:02}.v1.json';row=q.json(name)
        out['admission_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']=='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and row['source_closing_exact'] and row['resource_stop_reason'] is None
            and row['resource_watcher_cleanup_confirmed'] and row['tests_run']==row['tests_passed']==16,'AUDIT_ADMISSION')
        s.require(row['compiled_source_count']==846 and row['current_Rust_input_count']==785
            and row['protected_executables_exact']==53 and row['required_check_count']==39
            and row['exact_check_names']==driver.required_checks() and row['provided_driver_guard_count_delta']==[842,846]
            and row['whole_original_driver_inverse_exact'] and row['original_source_files_modified'] is False,'AUDIT_GENERATION')
        s.require(row['actual_SQL_Docker_native_or_EXE_executed'] is False and row['owned_root_created'] is False
            and row['image_downloaded_or_backend_changed'] is False and row['product_complete'] is False
            and row['P09_gate']=='OPEN' and row['actual_SQL_metadata_or_signed_consumer_qualified'] is False,'AUDIT_NO_PROMOTION')
        s.require(row['build_receipt_pin']==s.BUILD_PIN and row['build_closing_pin']==s.CLOSING_PIN
            and row['binding']['scheme']==s.SCHEME and row['binding']['required_check_count']==39
            and row['binding']['actual_SQL_qualified'] is False,'AUDIT_BINDING')
        frozen={p['path']:p for p in row['bound_input_pins']}
        s.require(len(frozen)==len(row['bound_input_pins']),'AUDIT_UNIQUE_INPUTS')
        for pin in frozen.values():s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_INPUT_DRIFT')
        s.require(q.pin(s.BUILD_PIN['path'])==s.BUILD_PIN and q.pin(s.CLOSING_PIN['path'])==s.CLOSING_PIN,'AUDIT_IMMUTABLE_PARENTS')
        build=q.json(s.BUILD_PIN['path']);source,protected,exe=s.accepted(build)
        s.require(exe==row['executable_pin'] and len(protected)==53,'AUDIT_RUNTIME_EXE')
        for pin in [*source.values(),*protected.values(),exe]:s.require(frozen[pin['path']]==pin,'AUDIT_RUNTIME_WHOLE_CLOSURE')
        closing=q.json(s.CLOSING_PIN['path'])
        s.require(closing['state']=='PASS_CURRENT_DS06_RUNTIME_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and closing['actual_receipt_pin']==s.BUILD_PIN and closing['source_closing_exact']
            and closing['protected_executables_exact']==53 and closing['contract_tests_passed']==22,'AUDIT_BUILD_CLOSING')
        for pin in closing['bound_input_pins']:s.require(frozen[pin['path']]==pin,'AUDIT_PRIOR_CLOSING_WHOLE_CLOSURE')
        rust={n for n in source if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.build.parent.original.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        old=q.json(s.prior.legacy.CURRENT_BUILD_PIN['path']);original=s.prior.inventory(old['source_freeze'])
        s.require(len(original)==842 and rust-set(original)==s.ADDED_RUST
            and len(set(original)|s.ADDED_RUST)==846,'AUDIT_VIEW846')
        archived=q.json(ARCHIVE);prior_light=q.json(archived['prior_light_receipt_pin']['path'])
        s.require(q.pin(archived['prior_light_receipt_pin']['path'])==archived['prior_light_receipt_pin']
            and prior_light['state']=='PASS_DS06_SQL_ADMISSION_CONTRACT_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and prior_light['tests_passed']==16,'AUDIT_PRIOR_LIGHT_RETAINED')
        for item in archived['files']:
            raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
            s.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                and pin in prior_light['bound_input_pins'],'AUDIT_PRIOR_LIGHT_WHOLE')
        light=q.json('implementation/p09/evidence/p09-151-SQL-admission.light-run02.v1.json')
        s.require(light['state']=='PASS_DS06_SQL_ADMISSION_CONTRACT_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and light['tests_passed']==light['tests_run']==16 and light['source_closing_exact'],'AUDIT_CURRENT_LIGHT16')
        for pin in light['bound_input_pins']:s.require(q.pin(pin['path'])==pin,'AUDIT_LIGHT_CLOSURE')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName('test_durable_negative_sql_admission')
        with patch('subprocess.Popen',side_effect=AssertionError('P151_ADMISSION_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_ADMISSION_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P151_ADMISSION_AUDIT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==16 and not checked.skipped,'AUDIT_FRESH_CONTRACT16')
        q.finish();out.update(state='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,current_Rust_input_count=785,compiled_source_count=846,
            protected_executables_exact=53,required_check_count=39,contract_tests_passed=16,
            original27_plus_durable4_plus_private_negative8_exact=True,executable_pin=exe,
            build_receipt_pin=s.BUILD_PIN,build_closing_pin=s.CLOSING_PIN,provided_driver_guard_count_delta=[842,846],
            full_runtime_and_closing_input_closures_exact=True,prior_light_and_whole_source_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        value=str(error) if isinstance(error,ValueError) else 'SQL_P151_ADMISSION_AUDIT_OPERATION_FAILED'
        out['error_code']=value if len(value)<=160 and re.fullmatch('[A-Z_]+',value) else 'SQL_P151_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='SQL_P151_AUDIT_FINAL_FRESHNESS'
        s.build.parent.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
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
