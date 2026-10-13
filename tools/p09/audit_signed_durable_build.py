"""Independent closing audit of P150 build only; never grants SQL/native admission."""
import base64
import argparse
import hashlib
import io
import json
import re
import sys
import threading
import unittest
import build_signed_durable_probe as build
from live_sql_evidence_reader import LiveSQLReader
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

SELF='tools/p09/audit_signed_durable_build.py'


def require(ok,code):build.require(ok,'AUDIT_'+code)


def audit(run):
    resources=SQLRuntimeResources();out={};before={t.ident for t in threading.enumerate()}
    try:
        resources.admit();q=LiveSQLReader(resources)
        build.task_for(run)
        name=f'implementation/p09/evidence/p09-150-durable-probe-build.actual-run{run:02}.v1.json'
        row=q.json(name)
        require(row['state']==build.PASS and row['current_build_binding_accepted']
            and row['exit_code']==0 and row['source_freeze_exact_after'] and row['protected_executables_exact_after']
            and row['cleanup_confirmed'] and row['owned_tree_empty'],'ACCEPTED_BUILD')
        require(row['policy']==build.c.POLICY and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
            and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15,'GO_POLICY')
        require(row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'TERMINAL_TREE')
        require(row['actual_SQL_or_native_executed'] is False and row['current_SQL_admission_qualified'] is False
            and row['old_SQL_admission_modified'] is False and row['product_complete'] is False and row['P09_gate']=='OPEN','NO_PROMOTION')
        limits=row['owned_limits_readback']
        require(limits['verified'] and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
            and limits['priority_class']==16384 and limits['active_process_limit']==16
            and limits['kill_on_close'] and limits['breakaway_disabled'],'LIMIT_READBACK')
        capture=row['capture_diagnostics'];proof=row['build_result']['validated_stream']
        require(row['build_result']['catalog_profile']==dict(opt_level='1',debuginfo='line-tables-only',
            debug_assertions=True,overflow_checks=True,test=False)
            and row['current_dev_package_profile_config']==list(build.DEV_CONFIG)
            and row['original_test_package_profile_config']==list(build.original.base.CONFIG),'ACTUAL_DEV_PROFILE')
        require(capture['per_stream_limit_bytes']==32768 and capture['error_code'] is None
            and not capture['raw_log_content_included'] and all(v<=32768 for v in capture['received_bytes'].values()),'OUTER_CAPTURE')
        require(proof['all_records_validated'] and not proof['raw_output_truncated'] and not proof['raw_logs_included']
            and proof['stdout_record_buffer_limit']==proof['stderr_total_limit']==32768
            and proof['stdout_total_JSON_IO_budget']==16*1024*1024,'STREAM_PROOF')
        pins={p['path']:p for p in row['source_freeze']};require(len(pins)==len(row['source_freeze']),'UNIQUE_INPUTS')
        for path,pin in pins.items():require(q.pin(path)==pin,'CURRENT_INPUT_DRIFT')
        rust={p for p in pins if p.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (p.endswith('.rs') or p.endswith('/Cargo.toml'))}
        require(len(rust)==784 and build.original.rust_inputs(build.c.ROOT,resources.checkpoint_io)==rust,'RUST784')
        protected=row['protected_executables'];require(len(protected)==len({p['path'] for p in protected})==51,'PROTECTED_SCOPE')
        for pin in protected:require(q.pin(pin['path'])==pin,'PROTECTED_DRIFT')
        executable=row['executable_pin'];require(executable['path']==build.executable_name(run)
            and q.pin(executable['path'])==executable and executable not in protected,'FRESH_EXECUTABLE')
        require(q.pin(build.AUDIT_PIN['path'])==build.AUDIT_PIN,'PARENT_AUDIT_DRIFT')
        parent=q.json(build.AUDIT_PIN['path']);prior={p['path']:p for p in parent['bound_input_pins']}
        for path in (build.original.ROOT_SOURCE,build.original.PROVIDER_SOURCE,build.original.BACKEND_SOURCE,build.original.SELF):
            require(q.pin(path)==prior[path],'ORIGINAL_PRODUCT_BODY_DRIFT')
        for archived in q.json(build.original.ARCHIVE)['files']:
            raw=base64.b64decode(archived['base64'],validate=True)
            restored=build.original.restore_original(archived['path'],q.text(archived['path']))
            restored=restored.replace('\n','\r\n').encode() if b'\r\n' in raw else restored.encode()
            require(restored==raw,'ORIGINAL_WHOLE_RESTORE')
        failed=q.json('implementation/p09/evidence/p09-150-durable-probe-build.actual-run01.v1.json')
        require(failed['state']=='STOPPED_NOT_ACCEPTED' and failed['stop_reason']=='FULL_CAPTURE_OUTPUT_LIMIT'
            and not failed['current_build_binding_accepted'] and failed['cleanup_confirmed'] and failed['owned_tree_empty'],'FAILURE_PRESERVED')
        archived=q.json(build.ARCHIVES[1]);require(q.pin(archived['failed_receipt_pin']['path'])==archived['failed_receipt_pin'],'FAILED_RECEIPT_PIN')
        for source in archived['files']:
            raw=base64.b64decode(source['base64'],validate=True);pin={k:source[k] for k in ('path','bytes','sha256')}
            require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                and pin in failed['source_freeze'],'FAILED_SOURCE_WHOLE')
        for archive_name in build.ARCHIVES[2:]:
            archive=q.json(archive_name);old=q.json(archive['failed_receipt_pin']['path'])
            require(q.pin(archive['failed_receipt_pin']['path'])==archive['failed_receipt_pin']
                and old['state']=='STOPPED_NOT_ACCEPTED' and old['stop_reason']=='OWNED_COMMAND_FAILED'
                and old['owned_tree_empty'] and old['cleanup_confirmed'],'LATER_FAILURE_PRESERVED')
            for source in archive['files']:
                raw=base64.b64decode(source['base64'],validate=True);pin={k:source[k] for k in ('path','bytes','sha256')}
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                    and pin in old['source_freeze'],'LATER_FAILURE_WHOLE_SOURCE')
        q.pin(SELF)
        sys.path.insert(0,str(build.c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_build_signed_durable_probe','test_signed_durable_build_stream'))
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        require(result.wasSuccessful() and result.testsRun==22,'LIGHT22')
        require({t.ident for t in threading.enumerate()}==before,'READER_THREADS_FINISHED')
        docs=[q.pin(n) for n in ('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')]
        q.finish()
        out.update(schema_version='hwpx-agent.p09-current-durable-build-terminal-audit/v1',
            state='PASS_CURRENT_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE',current_build_receipt_pin=q.reader.snapshots[name],
            source_closing_exact=True,whole_workspace_Rust_inputs=784,protected_executables_exact=51,
            executable_pin=executable,tests_run=22,tests_passed=22,failed_build_and_source_preserved=True,
            imported_helpers_exact=len(row['imported_helper_inventory']),compiler_profile=row['build_result']['catalog_profile'],
            stream_proof=proof,outer_capture=capture,job_final=row['job_final'],
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']),
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']),
            audit_new_child_started=False,bounded_test_reader_threads_finished=True,actual_SQL_or_native_executed=False,
            current_SQL_admission_qualified=False,PC_freeze_resolved=False,product_complete=False,P09_gate='OPEN',
            remaining_non_permission_work_units=76,document_inputs=docs,IO=q.summary(),
            bound_input_pins=list(q.reader.snapshots.values()),raw_logs_included=False)
    finally:
        out['resource_stop']=resources.reason;require(finish_watcher(resources,out),'WATCHER_CLEANUP')
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    args=parser.parse_args()
    try:print(json.dumps(audit(args.run),separators=(',',':')))
    except (ValueError,OSError,TypeError,KeyError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]+',str(error)) else 'DURABLE_BUILD_AUDIT_NOT_ACCEPTED'
        print(json.dumps(dict(state='NOT_ACCEPTED',error_code=code)));raise SystemExit(2) from None
