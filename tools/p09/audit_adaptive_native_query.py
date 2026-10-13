"""P164 independent source/Job/native schedule audit; no runtime retry."""
import json
import time
from unittest.mock import patch
import probe_adaptive_host_cpu_sampler_r2 as probe

p=probe.full.p
SELF='tools/p09/audit_adaptive_native_query.py'
ACTUAL='implementation/p09/evidence/p09-164-adaptive-native-query.actual-run02.v1.json'
LIGHT='implementation/p09/evidence/p09-164-adaptive-native-query.light-run02.v1.json'
OLD='implementation/p09/evidence/p09-164-adaptive-native-query.actual-run01.v1.json'
PARENT=dict(path='implementation/p09/evidence/p09-163-source-xml-product-full.terminal-audit-run01.v1.json',
    bytes=367844,sha256='d98386dbde4fc75c1507f07893a303f9dac2b93b8b9c2dbec590a22098acbaba')
PASS='PASS_ADAPTIVE_NATIVE_QUERY_CURRENT_SOURCE_CLOSING_ONLY_NOT_FULL249_OR_GATE'

def main():
    probe.require(p.c.Path.cwd().resolve()==p.c.ROOT,'AUDIT_CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-164-adaptive-native-query.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_thread_started=False,causal_attribution=False,remaining_non_permission_work_units=76,
        hot_resume_native_actual_verified=False,production_callback_actual_full249_executed=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P164_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P164_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P164_AUDIT_THREAD_FORBIDDEN')):
            probe.require(q.pin(PARENT['path'])==PARENT,'AUDIT_PRESERVED_P163_STOP')
            parent=q.json(PARENT['path'])
            probe.require(parent['state']=='PASS_SOURCE_XML_CURRENT_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
                and parent['source_closing_exact'] and parent['current_Rust_input_count']==785
                and parent['protected_EXE_inputs_exact']==64 and parent['actual_tests_passed'] is None
                and not parent['full249_current_qualified'] and not parent['signed16_current_qualified']
                and not parent['product_complete'] and parent['P09_gate']=='OPEN','AUDIT_PARENT_STOP_NOT_PASS')
            expected=p.s.inputs.inventory(parent['bound_input_pins'],1295)
            for n,pin in expected.items():probe.require(q.pin(n)==pin,'AUDIT_WHOLE_CURRENT_PARENT')
            rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
            probe.require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_RUST785')
            names,modules=p.source_scope(q,expected)
            probe.require(names==parent['source_test_names'] and modules==parent['source_module_instances'],'AUDIT_ORIGINAL249_59')
            row=q.json(ACTUAL);light=q.json(LIGHT);old=q.json(OLD)
            out.update(actual_probe_pin=q.reader.snapshots[ACTUAL],light_probe_pin=q.reader.snapshots[LIGHT],
                preserved_partial_run01_pin=q.reader.snapshots[OLD])
            probe.require(row['state']==probe.PASS and row['exit_code']==0 and row['stop_reason'] is None
                and row['maximum_seconds']==30 and row['policy']==p.c.POLICY
                and all(row[k] for k in ('worker_created','job_assigned','writer_authorized','cleanup_confirmed','owned_tree_empty'))
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
                and row['owned_limits_readback']['verified']
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25,'AUDIT_REAL_OWNED_NATIVE_ONLY')
            probe.require(row['observer_query_cleanup_confirmed'] and row['observer_failure_code'] is None
                and not row['actual_product_test_body_executed'] and not row['Rust_or_test_body_executed']
                and not row['full249_current_qualified'] and not row['signed16_current_qualified']
                and not row['product_complete'] and not row['PC_freeze_resolved']
                and not row['full_product_performance_improvement_measured'] and not row['host_CPU_cause_proven'],'AUDIT_NO_PRODUCT_OR_CAUSE')
            frozen=p.s.inputs.inventory(row['source_freeze'],67)
            # __main__ is the auditor here; exclude it from the dispatcher's
            # declared runtime scope, then bind this audit itself separately.
            required=set(probe.FILES)-{SELF}
            probe.require(set(frozen)==required,'AUDIT_ALL67_ACTIVE_HELPERS')
            for n,pin in frozen.items():probe.require(q.pin(n)==pin,'AUDIT_NATIVE_FROZEN_WHOLE_HELPERS')
            probe.require(light['state']=='PASS_ADAPTIVE_QUERY_CONTRACTS_ONLY_NOT_NATIVE_RUNTIME_OR_GATE'
                and light['contract_tests_passed']==81 and light['source_closing_exact'],'AUDIT_LIGHT81')
            probe.validate_payload(row['observer_probe']);schedule=row['observer_probe']['schedule']
            probe.require(schedule['host_polls']==4 and schedule['query_calls']==3
                and schedule['emitted_samples']==2 and schedule['skipped_cold_polls']==2
                and schedule['discarded_resume_warm_calls']==schedule['skipped_budget_polls']==0,'AUDIT_ACTUAL_COLD_REDUCTION')
            oldscope=p.s.inputs.inventory(old['source_freeze'],13)
            probe.require(set(oldscope)<set(frozen)|{'tools/p09/probe_adaptive_host_cpu_sampler.py'}
                and old['observer_query_cleanup_confirmed'] and not old['full249_current_qualified'],'AUDIT_RUN01_PARTIAL_SCOPE')
            for n,pin in oldscope.items():probe.require(q.pin(n)==pin,'AUDIT_OLD_RECEIPT_AND_PRODUCER_PRESERVED')
            out.update(probe.contracts());q.finish()
            out.update(state=PASS,source_closing_exact=True,current_Rust_input_count=785,
                source_test_names=names,source_module_instances=modules,protected_EXE_inputs_exact=64,
                compiled_test_executable_pin=parent['compiled_test_executable_pin'],prior_stop_closing_pin=PARENT,
                actual_native_probe_helper_count=67,one_native_query_closed_explicitly=True,
                actual_four_host_poll_schedule=schedule,actual_native_query_calls=3,
                equivalent_old_per_poll_recipe_query_calls=5,old_per_poll_recipe_not_actually_rerun=True,
                actual_saved_native_samples=2,cold_native_queries_avoided=2,
                prior_run01_startup_helper_binding_complete=False,prior_run01_product_or_full_qualification=False,
                owned_native_job_final=row['job_final'],host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']),
                host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=probe.full.s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','actual_native_query_calls',
            'cold_native_queries_avoided','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
