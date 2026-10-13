"""Independent libtest compile closing. A build is not compiled249 listing/runtime."""
import argparse
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import build_current_stored_generation as s

SELF = 'tools/p09/audit_current_stored_build.py'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'AUDIT_REPOSITORY_CWD')
    destination=s.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-build.terminal-audit-run{args.audit_run:02}.v1.json',fresh=True)
    resources=s.prepared.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-current-stored-libtest-build-closing/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,current_compiled249_qualified=False,full249_current_qualified=False,
        signed16_current_qualified=False,runtime_tests_executed=False,actual_SQL_native_or_new_OS_child_executed=False,
        fixture_pipe_reader_threads_started_and_joined=True,raw_logs_included=False,PC_freeze_resolved=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        resource_samples=resources.samples)
    try:
        resources.admit();q=s.prepared.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-152-current-stored-build.actual-run{args.run:02}.v1.json'
        row=q.json(name);out['actual_build_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']==s.PASS and row['build_only_accepted'] is True and row['current_build_binding_accepted'] is True
            and row['source_freeze_exact_after'] is True and row['protected_executables_exact_after'] is True
            and row['source249_generation_connected_to_actual_build'] is True
            and row['whole_workspace_Rust_input_count']==785 and row['protected_executables_expected']==54
            and row['previous_parent_EXE_inputs_preserved']==59 and row['current_source249_preparation_closing_pin']==s.AUDIT_PIN,
            'AUDIT_ACTUAL_BUILD_SCOPE')
        s.require(row['exit_code']==0 and row['stop_reason'] is None and row['cleanup_confirmed'] is True
            and row['owned_tree_empty'] is True and row['job_final']['active_processes']==0
            and all(row[k] is True for k in ('worker_created','job_assigned','writer_authorized'))
            and row['post_hash_stable_admission_revalidated'] is True and row['compile_admission_RAM_percent']==15,
            'AUDIT_OWNED_TERMINAL')
        s.require(row['policy']==s.c.POLICY and row['maximum_seconds']==600
            and row['owned_limits_readback']['verified'] is True
            and row['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
            and row['current_test_package_profile_config']==list(s.CONFIG), 'AUDIT_ORIGINAL_POLICY')
        for flag in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
                'runtime_tests_executed','actual_SQL_or_native_executed','product_complete','PC_freeze_resolved'):
            s.require(row[flag] is False,'AUDIT_BUILD_NOT_PROMOTED')
        build=row['build_result'];s.profile_scope(build['catalog_profile'])
        s.require(build['build_finished_success'] is True and build['diagnostics']==[]
            and build['actual_catalog_test_true_validated_before_legacy_protocol_adapter'] is True
            and build['executable_path']==s.executable_name(args.run), 'AUDIT_CURRENT_LIBTEST_CATALOG')
        stream=build['validated_stream']
        s.require(stream['all_records_validated'] is True and stream['raw_output_truncated'] is False
            and stream['raw_logs_included'] is False and stream['stdout_record_buffer_limit']==32768
            and stream['stderr_total_limit']==32768 and stream['stdout_total_JSON_IO_budget']==16*1024*1024
            and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']), 'AUDIT_COMPLETE_STREAM')
        frozen=s.prepared.inputs.inventory(row['source_freeze'])
        for path,pin in frozen.items():s.require(q.pin(path)==pin,'AUDIT_CURRENT_INPUT')
        s.require(q.pin(s.AUDIT_PIN['path'])==s.AUDIT_PIN,'AUDIT_IMMUTABLE_SOURCE_CLOSING')
        parent=q.json(s.AUDIT_PIN['path'])
        s.require(all(frozen.get(pin['path'])==pin for pin in parent['bound_input_pins']), 'AUDIT_WHOLE_PARENT_CLOSURE')
        protected=s.prepared.inputs.inventory(row['protected_executables'],54)
        s.require(all(frozen.get(n)==p for n,p in protected.items()),'AUDIT_PROTECTED54')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.prepared.inputs.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        exe=row['executable_pin'];s.require(exe['path']==s.executable_name(args.run) and q.pin(exe['path'])==exe,'AUDIT_FRESH_LIBTEST_EXE')
        preparation=q.json(parent['preparation_receipt_pin']['path'])
        def read(path):
            s.require(path in frozen,'AUDIT_MODULE_SCOPE');value=q.text(path)
            s.require(q.reader.snapshots[path]==frozen[path],'AUDIT_CURRENT_MODULE');return value
        names,modules=s.prepared.profile.signed.previous.parent.recursive_names(read,'stored-form-tests')
        s.prepared.profile.signed.previous.original.select_names(names)
        s.require(len(modules)==59 and preparation['source_test_names']==list(names)
            and preparation['source_module_instances']==list(modules),'AUDIT_SOURCE249_59_NOT_COMPILED_LISTING')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_build_current_stored_generation','test_signed_durable_build_stream'))
        for path in (s.SELF,s.TEST,'tools/p09/tests/test_signed_durable_build_stream.py'):q.pin(path)
        with patch('subprocess.Popen',side_effect=AssertionError('P152_AUDIT_OS_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_AUDIT_OS_CHILD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and checked.testsRun==26 and not checked.skipped,'AUDIT_FRESH_CONTRACT26')
        q.finish();out.update(state='PASS_CURRENT_LIBTEST_BUILD_CLOSING_ONLY_NOT_COMPILED249_LISTING_RUNTIME_SQL_OR_GATE',
            source_closing_exact=True,contract_tests_passed=26,current_Rust_input_count=785,
            current_source_test_count=249,current_source_module_instance_count=59,protected_executables_exact=54,
            parent_EXE_inputs_preserved=sum(n.endswith('.exe') for n in frozen),compiled_test_executable_pin=exe,
            actual_libtest_profile=build['catalog_profile'],actual_build_stream=stream,
            owned_job_final=row['job_final'],original_owned_policy_unchanged=True,
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']),
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P152_BUILD_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P152_BUILD_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['final_freshness_error']='P152_BUILD_AUDIT_FINAL_FRESHNESS'
        s.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__=='__main__':raise SystemExit(main())
