"""Independent current-r03 cost terminal account; not full249 acceptance."""
import json
import math
import time
from unittest.mock import patch
import run_current_graph_cost as d

p=d.p
SELF='tools/p09/audit_current_graph_cost.py'
ACTUAL='implementation/p09/evidence/p09-160-current-graph-cost.actual-run01.v1.json'

def require(ok,code):d.require(ok,'AUDIT_'+code)

def check_native(row,cap):
    observed=d.old.s
    records=cap['host_cpu_records'];ready=None;samples=[];budget=False;sealed=False
    require(type(records) is list and len(records)<=9,'NATIVE_FRAME_BOUND')
    jobpids={item['pid'] for sample in row['samples'] for item in sample.get('owned_processes',[])}
    with patch.object(observed,'MAX_SAVED',6):
        for item in records:
            observed.valid_record(item,ready['worker_pid'] if ready else None)
            require(not sealed,'AFTER_CLOSE')
            kind=item['kind']
            if kind=='ready':
                require(ready is None and not samples and item['worker_pid'] in jobpids
                    and item['processor_count']==row['resolved_owned_limits']['machine_logical_processors'],'READY_JOB')
                ready=item
            else:require(ready is not None,'READY_REQUIRED')
            if kind=='sample':
                require(item['test_pid']==ready['test_pid'] and item['sequence']==len(samples)+1
                    and item['observation']['processor_count']==ready['processor_count']
                    and (not samples or item['observed_at']>samples[-1]['observed_at']),'SAMPLE_BINDING')
                samples.append(item)
            if kind=='budget':require(not budget and len(samples)==6,'BUDGET');budget=True
            if kind=='closed':
                require(item['saved_samples']==len(samples) and item['diagnostic_budget_limited'] is budget,'CLOSE_MATCH')
                sealed=True
    require(cap['explicit_query_cleanup_confirmed'] is sealed,'CLOSE_NOT_RETROACTIVE')
    require(len(cap['churn_identity_records'])<=6 and len(cap['churn_identity_records'])<=len(samples),'CHURN_BOUND')
    for index,record in enumerate(cap['churn_identity_records']):
        d.old.observation.valid_churn(record['churn'])
        require(all(record[k]==samples[index][k] for k in ('worker_pid','test_pid','sequence','observed_at')),'CHURN_BINDING')

def check_trace(trace,names):
    require(trace['observed_times_are_pipe_arrival_wall_times'] and not trace['raw_test_output_saved']
        and len(trace['completed'])<=249,'TRACE_SCOPE')
    seen=set();last=0
    for item in trace['completed']:
        require(set(item)=={'case','started_seconds','finished_seconds','observed_wall_seconds','result'}
            and item['case'] in names and item['case'] not in seen and item['result'] in ('ok','FAILED','ignored'),'CASE')
        for k in ('started_seconds','finished_seconds','observed_wall_seconds'):
            require(type(item[k]) in (int,float) and math.isfinite(item[k]) and item[k]>=0,'TIME')
        require(item['finished_seconds']>=item['started_seconds']>=last and math.isclose(item['observed_wall_seconds'],
            item['finished_seconds']-item['started_seconds'],abs_tol=1e-9),'WALL_NOT_CPU')
        seen.add(item['case']);last=item['finished_seconds']
    active=trace['active']
    if active:
        require(set(active)=={'case','started_seconds','observed_wall_seconds'} and active['case'] in names
            and active['case'] not in seen,'ACTIVE_NOT_PASS')
        for k in ('started_seconds','observed_wall_seconds'):
            require(type(active[k]) in (int,float) and math.isfinite(active[k]) and active[k]>=0,'ACTIVE_TIME')
        require(active['started_seconds']>=last,'SERIAL_ACTIVE')
    require(trace['completed_case_count']==len(seen) and trace['started_case_count']==len(seen)+int(active is not None),'COUNT')
    return len(seen)

def main():
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-160-current-graph-cost.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,diagnostic_only=True,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_new_thread_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_diagnostic_receipt_pin']=q.reader.snapshots[ACTUAL]
        require(row['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE')
            and row['diagnostic_only'] and row['maximum_seconds']==d.MAXIMUM_SECONDS==360
            and row['current_cost_diagnostic_seconds']==360 and row['original_full_qualification_seconds']==1200
            and row['policy']==p.c.POLICY and row['tests_passed'] is None and not row['full249_current_qualified']
            and not row['signed16_current_qualified'] and not row['product_complete'] and row['P09_gate']=='OPEN'
            and row['actual_test_format']=='pretty' and row['current_Rust_input_count']==785
            and row['current_compiled249_qualified'] and row['original_all249_unfiltered_single_thread_nocapture0']
            and not row['actual_new_Cargo_compile_executed'] and not row['actual_Hangul_COM_or_SQL_run']
            and not row['original_test_bodies_or_product_sources_changed'],'SCOPE_ONLY')
        require(row['cleanup_confirmed'] and row['owned_tree_empty'],'CLEANUP')
        if row['heavy_work_started']:
            require(row['job_assigned'] and row['writer_authorized'] and row['post_hash_runtime_admission_revalidated']
                and row['owned_limits_readback']['verified'] and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'JOB_TERMINAL')
        require(q.pin(d.PARENT['path'])==d.PARENT and row['immutable_full_stop_closing_pin']==row['current_graph_stop_closing_pin']==d.PARENT,'PARENT')
        parent=q.json(d.PARENT['path']);expected,exe=d.parent_scope(parent)
        frozen=p.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:require(all(frozen.get(n)==pin for n,pin in expected.items()),'WHOLE_PARENT_CLOSURE')
        for n,pin in {**expected,**frozen}.items():require(q.pin(n)==pin,'WHOLE_SOURCE')
        require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'CURRENT_EXE')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(row['source_test_names']==row['selected_test_names']==names==parent['source_test_names']
            and row['source_module_instances']==modules==parent['source_module_instances'],'ALL249_59')
        cap=row['capture_diagnostics'];trace=None;count=0
        if cap is not None:
            require(cap['per_stream_limit_bytes']==32768 and all(0<=n<=32768 for n in cap['received_bytes'].values())
                and not cap['raw_case_or_process_output_saved'] and not cap['raw_names_paths_commands_saved']
                and not cap['causal_attribution'] and cap['diagnostic_snapshots_max']==6,'BOUNDED_CAPTURE')
            trace=cap['case_progress'];count=check_trace(trace,names)
            check_native(row,cap)
        for n in (d.SELF,d.TEST,d.old.SELF,d.old.TEST,'tools/p09/stored_cost_observation.py'):q.pin(n)
        d.contracts();q.finish()
        out.update(state='PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE',source_closing_exact=True,
            current_compiled249_qualified=True,contract_tests_passed=80,current_Rust_input_count=785,
            protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),compiled_test_executable_pin=exe,
            original_run_state=row['state'],original_stop_reason=row['stop_reason'],completed_case_observations=count,
            case_progress=trace,capture_diagnostics=cap,owned_job_final=row.get('job_final'),
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None,
            original_source_final_hash_not_retroactively_promoted=row['state']=='STOPPED_NOT_ACCEPTED')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.full.s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','original_stop_reason','completed_case_observations','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
