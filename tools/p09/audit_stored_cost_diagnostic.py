"""Independent whole-source terminal account for diagnostic, never full249 PASS."""
import argparse
import io
import json
import math
import re
import sys
import time
import unittest
from unittest.mock import patch
import run_stored_cost_diagnostic as d

SELF='tools/p09/audit_stored_cost_diagnostic.py'


def require(ok,code):d.require(ok,'AUDIT_'+code)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=int,choices=range(1,100),required=True);p.add_argument('--audit-run',type=int,choices=range(1,100),required=True);args=p.parse_args()
    require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    dest=d.s.original.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-155-stored-cost.terminal-audit-run{args.audit_run:02}.v1.json',fresh=True)
    resources=d.s.original.inventory.build.prepared.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,diagnostic_only=True,full249_current_qualified=False,
        signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',PC_freeze_resolved=False,
        actual_EXE_SQL_native_or_audit_child_started=False,audit_new_thread_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.s.original.inventory.build.prepared.LiveSQLReader(resources);q.pin(SELF)
        name=f'implementation/p09/evidence/p09-155-stored-cost.actual-run{args.run:02}.v1.json';row=q.json(name)
        out['actual_diagnostic_receipt_pin']=q.reader.snapshots[name]
        require(row['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE')
            and row['diagnostic_only'] is True and row['maximum_seconds']==180 and row['original_full_qualification_seconds']==1200
            and row['policy']==d.c.POLICY and row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
            and row['tests_passed'] is None and row['product_complete'] is False and row['P09_gate']=='OPEN'
            and row['actual_test_format']=='pretty' and row['current_Rust_input_count']==785
            and row['original_all249_unfiltered_single_thread_nocapture0'] and row['native_or_SQL_run'] is False
            and row['actual_new_Cargo_compile_executed'] is False and row['original_test_bodies_or_product_sources_changed'] is False,'SCOPE_NOT_FULL_OR_GATE')
        require(row['cleanup_confirmed'] and row['owned_tree_empty'],'CLEANUP')
        if row['heavy_work_started']:
            require(row['job_assigned'] and row['writer_authorized'] and row['post_hash_runtime_admission_revalidated']
                and row['owned_limits_readback']['verified'] and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'REAL_OWNED_TERMINAL')
        require(q.pin(d.PARENT['path'])==d.PARENT and row['immutable_full_stop_closing_pin']==d.PARENT,'PARENT_PIN')
        parent=q.json(d.PARENT['path']);expected=d.s.original.inventory.build.prepared.inputs.inventory(parent['bound_input_pins'],1233)
        frozen=d.s.original.inventory.build.prepared.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:require(all(frozen.get(n)==pin for n,pin in expected.items()),'WHOLE_PARENT_CLOSURE')
        for n,pin in {**expected,**frozen}.items():require(q.pin(n)==pin,'FRESH_INPUT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and d.s.original.inventory.build.prepared.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        def read(n):require(n in expected,'MODULE_SCOPE');return q.text(n)
        names,modules=d.s.original.inventory.PARENT.recursive_names(read,'stored-form-tests');d.s.original.full.cost.original.select_names(names)
        require(list(names)==row['source_test_names']==row['selected_test_names']==parent['source_test_names']
            and list(modules)==row['source_module_instances'] and len(modules)==59,'ORIGINAL249_59_NO_FILTER')
        exe=row['compiled_test_executable_pin'];require(exe==parent['compiled_test_executable_pin'] and q.pin(exe['path'])==exe,'EXE_CURRENT')
        cap=row['capture_diagnostics'];trace=None
        if cap is not None:
            require(cap['per_stream_limit_bytes']==32768 and all(0<=n<=32768 for n in cap['received_bytes'].values())
                and cap['raw_case_or_process_output_saved'] is False and cap['raw_names_paths_commands_saved'] is False
                and cap['causal_attribution'] is False and cap['diagnostic_snapshots_max']==6,'BOUNDED_REDACTED_CAPTURE')
            trace=cap['case_progress'];require(trace['observed_times_are_pipe_arrival_wall_times'] is True
                and trace['raw_test_output_saved'] is False and len(trace['completed'])<=249,'TRACE_SCOPE')
            seen=set()
            for item in trace['completed']:
                require(set(item)=={'case','started_seconds','finished_seconds','observed_wall_seconds','result'}
                    and item['case'] in names and item['case'] not in seen and item['result'] in ('ok','FAILED','ignored'),'CLOSED_COMPLETED_CASE')
                seen.add(item['case'])
                for key in ('started_seconds','finished_seconds','observed_wall_seconds'):
                    require(type(item[key]) in (int,float) and math.isfinite(item[key]) and item[key]>=0,'TIME_NUMBER')
                require(item['finished_seconds']>=item['started_seconds'] and math.isclose(item['observed_wall_seconds'],
                    item['finished_seconds']-item['started_seconds'],abs_tol=1e-9),'WALL_TIME_NOT_CPU')
            active=trace['active']
            if active:require(set(active)=={'case','started_seconds','observed_wall_seconds'} and active['case'] in names
                and active['case'] not in seen and type(active['observed_wall_seconds']) in (int,float)
                and math.isfinite(active['observed_wall_seconds']) and active['observed_wall_seconds']>=0,'ACTIVE_NOT_PASSED')
            require(trace['completed_case_count']==len(seen) and trace['started_case_count']==len(seen)+int(active is not None),'TRACE_COUNT')
            ready=next((r for r in cap['host_cpu_records'] if r['kind']=='ready'),None)
            samples=[r for r in cap['host_cpu_records'] if r['kind']=='sample']
            with patch.object(d.s,'MAX_SAVED',6):
                for record in cap['host_cpu_records']:d.s.valid_record(record,ready['worker_pid'] if ready else None)
            require(len(cap['churn_identity_records'])<=6 and len(cap['churn_identity_records'])<=len(samples),'CHURN_COUNT')
            for index,record in enumerate(cap['churn_identity_records']):
                d.observation.valid_churn(record['churn'])
                require(all(record[k]==samples[index][k] for k in ('worker_pid','test_pid','sequence','observed_at')),'CHURN_INTERVAL_BINDING')
        sys.path.insert(0,str(d.c.ROOT/'tools/p09/tests'))
        for n in (d.SELF,d.TEST,'tools/p09/stored_cost_observation.py'):q.pin(n)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_stored_cost_observation','test_observed_stored_full','test_current_stored_full','test_compression_full_stored','test_host_cpu_groups'))
        with patch('subprocess.Popen',side_effect=AssertionError('AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('AUDIT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        require(checked.wasSuccessful() and checked.testsRun==75 and not checked.skipped,'CONTRACT75')
        q.finish();out.update(state='PASS_UNFILTERED_COST_DIAGNOSTIC_TERMINAL_ACCOUNTED_NOT_FULL249_OR_GATE',source_closing_exact=True,
            original_run_state=row['state'],original_stop_reason=row['stop_reason'],contract_tests_passed=75,
            completed_case_observations=len(trace['completed']) if trace else 0,active_case_observation=trace['active'] if trace else None,
            case_progress=trace,capture_diagnostics=cap,owned_job_final=row.get('job_final'),current_Rust_input_count=785,
            protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),compiled_test_executable_pin=exe,
            original_source_final_hash_not_retroactively_promoted=row['state']=='STOPPED_NOT_ACCEPTED')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=d.s.original.closed_error(error)
    finally:
        d.s.original.inventory.build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with dest.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','original_stop_reason','completed_case_observations','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
