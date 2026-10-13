"""P174 independent pipe timing/current source/terminal accounting, no queries."""
import json
import math
import time
import run_writer_case_cost as d
SELF='tools/p09/audit_writer_case_cost.py'
ACTUAL='implementation/p09/evidence/p09-174-writer-case-cost.actual-run01.v1.json'
PASS='PASS_CURRENT_WRITER_PIPE_CASE_COST_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE'
def validate_trace(trace,names,complete):
    d.require(trace['observed_times_are_pipe_arrival_wall_times'] and not trace['raw_test_output_saved']
        and len(trace['completed'])<=249,'TRACE_SCOPE')
    seen=set();last=0.0
    for item in trace['completed']:
        d.require(set(item)=={'case','started_seconds','finished_seconds','observed_wall_seconds','result'}
            and item['case'] in names and item['case'] not in seen and item['result'] in ('ok','FAILED','ignored'),'COMPLETE_CASE_FIELDS')
        seen.add(item['case'])
        for key in ('started_seconds','finished_seconds','observed_wall_seconds'):
            d.require(type(item[key]) in (int,float) and math.isfinite(item[key]) and item[key]>=0,'FINITE_TIME')
        d.require(item['started_seconds']>=last and item['finished_seconds']>=item['started_seconds']
            and math.isclose(item['observed_wall_seconds'],item['finished_seconds']-item['started_seconds'],abs_tol=1e-9),'WALL_INTERVAL')
        last=item['finished_seconds']
    active=trace['active']
    if active:
        d.require(set(active)=={'case','started_seconds','observed_wall_seconds'} and active['case'] in names
            and active['case'] not in seen and type(active['started_seconds']) in (int,float)
            and math.isfinite(active['started_seconds']) and active['started_seconds']>=last
            and type(active['observed_wall_seconds']) in (int,float)
            and math.isfinite(active['observed_wall_seconds']) and active['observed_wall_seconds']>=0,'ACTIVE_NOT_PASS')
    d.require(trace['completed_case_count']==len(seen)
        and trace['started_case_count']==len(seen)+int(active is not None),'COUNTS')
    if seen or active:d.require(trace['running_count']==249,'RUNNING249')
    if complete:d.require(seen==set(names) and active is None and trace['summary_seen']
        and all(x['result']=='ok' for x in trace['completed']),'ALL249_DIAGNOSTIC_COMPLETE')
def main():
    destination=d.s.scoped_path('implementation/p09/evidence/p09-174-writer-case-cost.terminal-audit-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,diagnostic_only=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,current_compiled249_qualified=True,
        actual_EXE_SQL_native_or_audit_child_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_diagnostic_receipt_pin']=q.reader.snapshots[ACTUAL]
        complete=row['state']=='DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE'
        d.require(row['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE')
            and row['diagnostic_only'] and row['maximum_seconds']==row['diagnostic_maximum_seconds']==360
            and row['original_full_qualification_seconds']==1200 and row['policy']==d.c.POLICY
            and not row['full249_current_qualified'] and not row['signed16_current_qualified'] and row['tests_passed'] is None
            and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
            and row['actual_test_format']=='pretty' and row['current_Rust_input_count']==785
            and row['original_all249_unfiltered_single_thread_nocapture0'] and row['timing_is_pipe_arrival_wall_not_CPU_profile']
            and not row['native_Process_query_executed'] and not row['actual_new_Cargo_compile_executed']
            and not row['original_test_bodies_or_product_sources_changed'] and not row['raw_logs_printed_or_saved'],'DIAGNOSTIC_NOT_FULL')
        d.require(row['cleanup_confirmed'] and row['owned_tree_empty'],'CLEANUP')
        if row['heavy_work_started']:d.require(row['job_assigned'] and row['writer_authorized']
            and row['post_hash_runtime_admission_revalidated'] and row['owned_limits_readback']['verified']
            and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
            and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'JOB_TERMINAL')
        if complete:d.require(row['exit_code']==0 and row['stop_reason'] is None,'DIAGNOSTIC_COMPLETE')
        else:d.require(row['stop_reason'] is not None,'STOP_RETAINED')
        d.require(q.pin(d.PARENT['path'])==d.PARENT and row['immutable_full_stop_closing_pin']==d.PARENT,'FULL_STOP_PIN')
        parent=q.json(d.PARENT['path']);expected,exe=d.parent_scope(parent)
        frozen=d.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:d.require(all(frozen.get(n)==p for n,p in expected.items()),'WHOLE_PARENT_IN_FREEZE')
        for n,p in {**expected,**frozen}.items():d.require(q.pin(n)==p,'WHOLE_FRESH_INPUTS')
        d.require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'CURRENT_R06')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.d.p.source_scope(q,expected)
        d.require(row['source_test_names']==row['selected_test_names']==names==parent['source_test_names']
            and row['source_module_instances']==modules==parent['source_module_instances'],'ALL249_59_UNFILTERED')
        cap=row['capture_diagnostics'];trace=None
        if cap:
            d.require(cap['per_stream_limit_bytes']==32768 and not cap['raw_log_content_included']
                and not cap['native_Process_query_started'] and not cap['additional_pipe_reader_threads']
                and not cap['raw_case_or_process_output_saved'],'ORIGINAL_BOUNDED_CAPTURE')
            trace=cap['case_progress'];validate_trace(trace,names,complete)
        else:d.require(not row['heavy_work_started'],'CAPTURE_REQUIRED_IF_STARTED')
        d.contracts()
        for n in d.helpers():q.pin(n)
        q.finish();out.update(state=PASS,source_closing_exact=True,contract_tests_passed=58,current_Rust_input_count=785,
            source_test_names=names,source_module_instances=modules,protected_EXE_inputs_exact=66,
            compiled_test_executable_pin=exe,case_progress=trace,
            completed_case_observations=len(trace['completed']) if trace else 0,
            active_case_observation=trace['active'] if trace else None,original_run_state=row['state'],
            original_stop_reason=row['stop_reason'],original_source_final_hash_not_retroactively_promoted=not complete,
            native_Process_query_executed=False,owned_job_final=row.get('job_final'),
            immutable_full_stop_closing_pin=d.PARENT)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','completed_case_observations',
            'original_stop_reason','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
