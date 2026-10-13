"""Independent P151 runtime closing. Never executes its EXE, SQL or native app."""
import argparse
import base64
import hashlib
import io
import json
import sys
import threading
import time
import unittest
from unittest.mock import patch
import build_durable_negative_probe as s

SELF='tools/p09/audit_durable_negative_runtime_build.py'
FAILED_ARCHIVE='implementation/p09/source-archive/p09-151-pre-build-reader-fixture-r31/source-preimages.v1.json'


def audit(run,audit_run):
    resources=s.parent.SQLRuntimeResources();q=None;started=time.monotonic()
    destination=s.parent.scoped_path(f'implementation/p09/evidence/p09-151-runtime-build.terminal-audit-run{audit_run:02}.v1.json',fresh=True)
    out=dict(schema_version='hwpx-agent.p09-ds06-runtime-build-terminal-audit/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,audit_new_child_started=False,actual_SQL_or_native_executed=False,
        actual_SQL_metadata_or_signed_consumer_qualified=False,full_durable_DS01_DS09_qualified=False,
        independent_restart_or_key_custody_qualified=False,PC_freeze_resolved=False,full249_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        raw_logs_included=False,resource_samples=resources.samples)
    try:
        resources.admit();q=s.parent.LiveSQLReader(resources);q.pin(SELF);s.task_for(run)
        name=f'implementation/p09/evidence/p09-151-runtime-build.actual-run{run:02}.v1.json';row=q.json(name)
        out['actual_receipt_pin']=q.reader.snapshots[name]
        s.require(row['state']==s.PASS and row['current_build_binding_accepted'] is True
            and row['runtime_only_build_accepted'] is True and row['exit_code']==0 and row['stop_reason'] is None
            and row['source_freeze_exact_after'] is True and row['protected_executables_exact_after'] is True,'AUDIT_ACCEPTED_BUILD')
        s.require(row['provided_driver_generation']=='P151_R31_CURRENT_DS06_NON_TEST'
            and row['whole_workspace_Rust_input_count']==785 and row['protected_executables_expected']==53
            and row['parent_example_audit_pin']==s.AUDIT_PIN and row['cache_target_reused']
            and row['distinct_output_suffix_preserves_prior_unit_executable'] and row['prior_unit27_not_reexecuted'],'AUDIT_GENERATION')
        s.require(row['policy']==s.c.POLICY and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
            and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15,'AUDIT_GO_POLICY')
        s.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['job_final']['active_processes']==0
            and row['job_final']['owned_processes']==[],'AUDIT_TERMINAL')
        limits=row['owned_limits_readback']
        s.require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
            and limits['priority_class']==16384 and limits['active_process_limit']==16
            and limits['kill_on_close'] and limits['breakaway_disabled'],'AUDIT_LIMITS')
        profile=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,overflow_checks=True,test=False)
        s.require(row['build_result']['catalog_profile']==profile and row['current_dev_package_profile_config']==list(s.DEV_CONFIG)
            and row['original_test_package_profile_config']==list(s.parent.original.base.CONFIG),'AUDIT_DEV_PROFILE')
        capture=row['capture_diagnostics'];proof=row['build_result']['validated_stream']
        s.require(capture['error_code'] is None and capture['per_stream_limit_bytes']==32768
            and not capture['raw_log_content_included'] and all(v<=32768 for v in capture['received_bytes'].values()),'AUDIT_OUTER_CAPTURE')
        s.require(proof['all_records_validated'] and not proof['raw_output_truncated'] and not proof['raw_logs_included']
            and proof['stdout_record_buffer_limit']==proof['stderr_total_limit']==32768
            and proof['stdout_total_JSON_IO_budget']==16*1024*1024,'AUDIT_WHOLE_STREAM')
        s.require(row['old_SQL_admission_modified'] is False and row['current_SQL_admission_qualified'] is False
            and row['actual_SQL_or_native_executed'] is False and row['product_complete'] is False
            and row['P09_gate']=='OPEN' and row['actual_SQL_metadata_or_signed_consumer_qualified'] is False,'AUDIT_NO_PROMOTION')
        frozen={p['path']:p for p in row['source_freeze']}
        s.require(len(frozen)==len(row['source_freeze']),'AUDIT_UNIQUE_INPUTS')
        for pin in frozen.values():s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_INPUT')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        s.require(len(rust)==785 and s.parent.original.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST')
        protected=row['protected_executables']
        s.require(len(protected)==len({p['path'] for p in protected})==53,'AUDIT_PROTECTED53')
        for pin in protected:s.require(q.pin(pin['path'])==pin and frozen[pin['path']]==pin,'AUDIT_PROTECTED_BYTES')
        exe=row['executable_pin']
        s.require(exe['path']==s.executable_name(run) and exe not in protected and q.pin(exe['path'])==exe,'AUDIT_FRESH_NON_TEST_EXE')
        s.require(q.pin(s.AUDIT_PIN['path'])==s.AUDIT_PIN,'AUDIT_PARENT_PIN')
        prior=q.json(s.AUDIT_PIN['path'])
        s.require(prior['compiled_test_artifact'] in protected and prior['actual_example_tests_passed']==27
            and prior['current_Rust_input_count']==785 and prior['actual_SQL_metadata_or_signed_consumer_controls_qualified'] is False,'AUDIT_PRIOR_UNIT_SEPARATE')
        for pin in prior['bound_input_pins']:s.require(frozen[pin['path']]==pin,'AUDIT_PARENT_CLOSURE')
        for archive,restore in ((s.parent.ARCHIVE,s.parent.restore_previous),
                (s.parent.original.ARCHIVE,lambda n,t:s.parent.original.restore_original(n,s.parent.restore_previous(n,t)))):
            for item in q.json(archive)['files']:
                raw=base64.b64decode(item['base64'],validate=True)
                s.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
                    and s.parent.recovered(raw,restore(item['path'],q.text(item['path'])))==raw,'AUDIT_WHOLE_BODY_INVERSE')
        archive=q.json(FAILED_ARCHIVE);failed=q.json(archive['failed_receipt_pin']['path'])
        s.require(q.pin(archive['failed_receipt_pin']['path'])==archive['failed_receipt_pin']
            and failed['state']=='FAILED_NOT_ACCEPTED' and failed['tests_passed']==21 and failed['tests_run']==22
            and failed['failed_tests']==['test_in_process_fake_child_cleanup_and_validator'],'AUDIT_FAILURE_PRESERVED')
        for item in archive['files']:
            raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
            s.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                and pin in failed['source_freeze'],'AUDIT_FAILURE_WHOLE_SOURCES')
        light=q.json('implementation/p09/evidence/p09-151-runtime-build.light-run02.v1.json')
        s.require(light['state']=='PASS_P151_BUILD_CONTRACT_ONLY_NOT_COMPILED_SQL_OR_GATE'
            and light['tests_run']==light['tests_passed']==22 and light['source_closing_exact'],'AUDIT_LIGHT22')
        for pin in light['source_freeze']:s.require(q.pin(pin['path'])==pin,'AUDIT_CURRENT_LIGHT')
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'));before={t.ident for t in threading.enumerate()}
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_build_durable_negative_probe','test_signed_durable_build_stream'))
        with patch('subprocess.Popen',side_effect=AssertionError('P151_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_AUDIT_CHILD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        s.require(checked.wasSuccessful() and not checked.skipped and checked.testsRun==22,'AUDIT_FRESH_CONTRACT22')
        s.require({t.ident for t in threading.enumerate()}==before,'AUDIT_FAKE_READER_THREADS_FINISHED')
        q.finish();out.update(state='PASS_CURRENT_DS06_RUNTIME_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE',
            source_closing_exact=True,current_Rust_input_count=785,protected_executables_exact=53,executable_pin=exe,
            contract_tests_passed=22,prior_unit27_preserved_not_reexecuted=True,compiler_profile=profile,
            all_prior_input_pins_retained=True,whole_prior_and_original_bodies_restored_exact=True,
            failed_light_and_whole_source_preserved=True,stream_proof=proof,outer_capture=capture,
            runtime_job_final=row['job_final'],limits_readback=limits,bounded_fake_reader_threads_finished=True,
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']),
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        value=str(error) if isinstance(error,ValueError) else 'P151_BUILD_AUDIT_OPERATION_FAILED'
        out['error_code']=value if len(value)<=160 and __import__('re').fullmatch('[A-Z_]+',value) else 'P151_BUILD_AUDIT_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='P151_BUILD_AUDIT_FINAL_FRESHNESS'
        s.parent.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] \
        and out.get('resource_watcher_cleanup_confirmed') and resources.reason is None else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    raise SystemExit(audit(args.run,args.audit_run))
