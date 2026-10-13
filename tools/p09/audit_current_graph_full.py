"""Independent actual current ALL249 closing; preserve stops/NOT_RUN as such."""
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import run_current_graph_full as d
import audit_observed_stored_full as diagnostic

p=d.p
SELF='tools/p09/audit_current_graph_full.py'
ACTUAL='implementation/p09/evidence/p09-159-current-graph-full.actual-run01.v1.json'
PASS='PASS_CURRENT_GRAPH_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'


def main():
    d.require(p.c.Path.cwd().resolve()==p.c.ROOT,'AUDIT_CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-159-current-graph-full.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_SQL_native_or_audit_OS_child_executed=False,audit_new_thread_started=False,
        remaining_non_permission_work_units=76,resource_samples=resources.samples)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_full_receipt_pin']=q.reader.snapshots[ACTUAL];passed=row['state']==d.PASS
        d.require(row['state'] in (d.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['current_inventory_closing_pin']==row['current_graph_inventory_closing_pin']==d.PARENT
            and row['current_Rust_input_count']==785 and row['expected_test_count']==249 and row['maximum_seconds']==1200
            and row['policy']==p.c.POLICY and row['actual_new_Cargo_compile_executed'] is False
            and row['actual_Hangul_COM_or_SQL_run'] is False and row['product_complete'] is False
            and row['P09_gate']=='OPEN' and row['PC_freeze_resolved'] is False,'AUDIT_ACTUAL_SCOPE')
        d.require(row['cleanup_confirmed'] and row['owned_tree_empty']
            and row['full249_current_qualified'] is passed and row['signed16_current_qualified'] is passed
            and row['tests_passed']==(249 if passed else None),'AUDIT_ORIGINAL_PASS_OR_STOP')
        if row['heavy_work_started']:
            d.require(all(row[k] for k in ('worker_created','job_assigned','writer_authorized',
                    'post_hash_runtime_admission_revalidated','test_body_execution_authorized'))
                and row['owned_limits_readback']['verified'] and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'AUDIT_REAL_JOB_TERMINAL')
        else:d.require(not passed and row['test_body_execution_authorized'] is False,'AUDIT_NOT_STARTED_NOT_PASSED')
        diagnostic.audit_observations(row,passed);cap=row['capture_diagnostics']
        if passed:
            d.require(row['exit_code']==0 and row['stop_reason'] is None and cap is not None and cap['error_code'] is None
                and cap['per_stream_limit_bytes']==32768 and all(0<=n<=32768 for n in cap['received_bytes'].values())
                and cap['raw_log_content_included'] is False,'AUDIT_COMPLETE249_TERMINAL')
        else:d.require(isinstance(row['stop_reason'],str) and re.fullmatch('[A-Z_]+',row['stop_reason']),'AUDIT_ORIGINAL_STOP_CODE')
        d.require(q.pin(d.PARENT['path'])==d.PARENT,'AUDIT_IMMUTABLE_CURRENT_COMPILED249')
        parent=q.json(d.PARENT['path']);expected,exe=d.parent_scope(parent)
        frozen=p.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:d.require(all(frozen.get(n)==pin for n,pin in expected.items()),'AUDIT_WHOLE_RUN_PARENT')
        for n,pin in {**expected,**frozen}.items():d.require(q.pin(n)==pin,'AUDIT_WHOLE_CURRENT_INPUT')
        d.require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'AUDIT_CURRENT_R03_EXE')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_RUST785')
        names,modules=p.source_scope(q,expected)
        d.require(row['source_test_names']==row['selected_test_names']==names==parent['source_test_names']
            and row['source_module_instances']==modules and row['test_package_profile_config']==list(p.b.CONFIG)
            and row['signed_original_test_name']==d.s.original.full.cost.original.NAME,'AUDIT_ORIGINAL_UNFILTERED249_59')
        for n in (*p.helpers(),d.SELF,d.TEST,'tools/p09/tests/test_host_cpu_groups.py'):q.pin(n)
        d.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
        group_tests=unittest.defaultTestLoader.loadTestsFromName('test_host_cpu_groups')
        with patch('subprocess.Popen',side_effect=AssertionError('P159_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P159_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P159_AUDIT_THREAD_FORBIDDEN')):
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(group_tests)
        d.require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'AUDIT_GROUP12')
        q.finish();out.update(state=PASS if passed else 'PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE',
            source_closing_exact=True,current_compiled249_qualified=True,full249_current_qualified=passed,signed16_current_qualified=passed,
            actual_tests_passed=249 if passed else None,original_run_state=row['state'],original_stop_reason=row['stop_reason'],
            original_source_final_hash_not_retroactively_promoted=not passed,contract_tests_passed=60,current_Rust_input_count=785,
            source_test_names=names,source_module_instances=modules,protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),
            compiled_test_executable_pin=exe,owned_job_final=row.get('job_final'),capture_diagnostics=cap,
            current_graph_inventory_closing_pin=d.PARENT,bounded_host_diagnostics_verified=True,
            individual_duplicated_PID_attribution=False,causal_attribution=False,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P159_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P159_AUDIT_REDACTED_FAILURE'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_tests_passed','contract_tests_passed','original_stop_reason','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
