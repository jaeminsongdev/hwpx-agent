"""Fresh EXE compiled249 listing closing only; actual all249 tests remain NOT_RUN."""
import argparse
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import run_current_stored_inventory as s

SELF='tools/p09/audit_current_stored_inventory.py'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'AUDIT_REPOSITORY_CWD')
    destination=s.build.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-inventory.terminal-audit-run{args.audit_run:02}.v1.json',fresh=True)
    resources=s.build.prepared.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-current-stored-inventory-closing/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,current_compiled249_qualified=False,full249_current_qualified=False,
        signed16_current_qualified=False,runtime_test_bodies_executed=False,actual_SQL_native_or_audit_OS_child_executed=False,
        fixture_pipe_reader_threads_started_and_joined=True,raw_logs_included=False,PC_freeze_resolved=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        resource_samples=resources.samples)
    try:
        resources.admit();q=s.build.prepared.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-152-current-stored-inventory.actual-run{args.run:02}.v1.json'
        row=q.json(name);out['actual_inventory_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']==s.PASS and row['compiled_inventory_exact'] is True
            and row['current_compiled249_qualified'] is True and row['fresh_EXE_list_only'] is True
            and row['runtime_tests_executed'] is False and row['full249_current_qualified'] is False
            and row['signed16_current_qualified'] is False and row['current_Rust_input_count']==785
            and row['expected_test_count']==249 and row['current_compile_closing_pin']==s.CLOSING,'AUDIT_LISTING_SCOPE')
        s.require(row['exit_code']==0 and row['stop_reason'] is None and row['cleanup_confirmed'] is True
            and row['owned_tree_empty'] is True and row['job_final']['active_processes']==0
            and row['job_final']['owned_processes']==[] and row['maximum_seconds']==180
            and row['policy']==s.c.POLICY and row['owned_limits_readback']['verified'] is True
            and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25,'AUDIT_ORIGINAL_JOB_CLEANUP')
        capture=row['capture_diagnostics'];s.require(capture['error_code'] is None
            and capture['per_stream_limit_bytes']==32768 and capture['raw_log_content_included'] is False
            and capture['received_bytes']['stderr']==0,'AUDIT_CLOSED_CAPTURE')
        frozen=s.build.prepared.inputs.inventory(row['source_freeze'])
        for path,pin in frozen.items():s.require(q.pin(path)==pin,'AUDIT_CURRENT_INPUT')
        s.require(q.pin(s.CLOSING['path'])==s.CLOSING,'AUDIT_COMPILE_CLOSING_IMMUTABLE')
        closing=q.json(s.CLOSING['path']);s.require(all(frozen.get(p['path'])==p for p in closing['bound_input_pins']),'AUDIT_WHOLE_COMPILED_PARENT')
        exe=row['compiled_test_executable_pin']
        s.require(exe==closing['compiled_test_executable_pin'] and exe['path']==s.build.executable_name(1)
            and frozen[exe['path']]==exe,'AUDIT_FRESH_SUFFIX_NOT_CANONICAL')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.build.prepared.inputs.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        def read(path):
            s.require(path in frozen,'AUDIT_MODULE_SCOPE');value=q.text(path)
            s.require(q.reader.snapshots[path]==frozen[path],'AUDIT_MODULE_FRESH');return value
        names,modules=s.PARENT.recursive_names(read,'stored-form-tests')
        s.build.prepared.profile.signed.previous.original.select_names(names)
        s.require(len(modules)==59 and row['source_test_names']==list(names)
            and row['source_module_instances']==list(modules),'AUDIT_SOURCE_COMPILED249_IDENTITY')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_current_stored_inventory','test_build_current_stored_generation','test_signed_durable_build_stream'))
        for path in (s.SELF,s.TEST,'tools/p09/tests/test_signed_durable_build_stream.py'):q.pin(path)
        with patch('subprocess.Popen',side_effect=AssertionError('P152_INVENTORY_AUDIT_OS_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_INVENTORY_AUDIT_OS_CHILD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==34 and not checked.skipped,'AUDIT_FRESH_CONTRACT34')
        q.finish();out.update(state='PASS_CURRENT_FRESH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,current_compiled249_qualified=True,contract_tests_passed=34,
            current_Rust_input_count=785,source_test_names=list(names),source_module_instances=list(modules),
            compiled_test_count=249,source_module_instance_count=59,compiled_test_executable_pin=exe,
            current_compile_closing_pin=s.CLOSING,protected_parent_EXE_inputs_exact=sum(n.endswith('.exe') for n in frozen),
            owned_inventory_job_final=row['job_final'],capture_diagnostics=capture,
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']),
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P152_INVENTORY_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P152_INVENTORY_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['final_freshness_error']='P152_INVENTORY_AUDIT_FINAL_FRESHNESS'
        s.build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','compiled_test_count','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__=='__main__':raise SystemExit(main())
