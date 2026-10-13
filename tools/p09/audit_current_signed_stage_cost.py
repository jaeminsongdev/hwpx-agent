"""Current signed-case stage timing/source/stop audit, not full acceptance."""
import json
import time
import run_current_signed_stage_cost as d

p=d.p
SELF='tools/p09/audit_current_signed_stage_cost.py'
ACTUAL='implementation/p09/evidence/p09-167-current-signed-stage-cost.actual-run01.v1.json'
PASS='PASS_CURRENT_SIGNED_STAGE_TIMING_SOURCE_ACCOUNTED_ONLY_NOT_FULL249_SQL_NATIVE_OR_GATE'

def require(ok,code):d.require(ok,'AUDIT_'+code)

def checked_observation(observation):
    require(type(observation) is dict and type(observation.get('events')) is list,'OBSERVATION_OBJECT')
    lines=[]
    for event in observation['events']:
        require(type(event) is dict and set(event)=={'case_index','stage','elapsed_us'}
            and type(event['case_index']) is int and type(event['stage']) is str and type(event['elapsed_us']) is int,
            'STRUCTURED_EVENT_TYPES')
        lines.append(f"P149_SIGNED_COST:{event['case_index']}:{event['stage']}:{event['elapsed_us']}\n")
    expected=d.stage.observe_cost(''.join(lines))
    require(expected==observation and observation['signed16_runtime_complete'] is False,'REPARSED_ORDER_AND_NO_PROMOTION')
    return observation

def main():
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-167-current-signed-stage-cost.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',diagnostic_only=True,source_closing_exact=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,exact_CPU_profiler=False,
        actual_audit_child_or_new_thread_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_stage_receipt_pin']=q.reader.snapshots[ACTUAL]
        require(row['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED',d.FINISHED)
            and row['task']==d.TASK and row['maximum_seconds']==180 and row['original_full_qualification_seconds']==1200
            and row['policy']==p.c.POLICY and row['diagnostic_only'] and row['current_Rust_input_count']==785
            and row['current_compiled249_qualified'] and row['tests_passed'] is None
            and not row['full249_current_qualified'] and not row['signed16_current_qualified']
            and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
            and not row['PC_freeze_resolved'] and not row['full_product_performance_improvement_measured']
            and not row['actual_new_Cargo_compile_executed'] and not row['actual_Hangul_COM_SQL_or_Process_query_run']
            and not row['original_test_bodies_or_product_sources_changed'] and not row['raw_logs_printed_or_saved'],
            'ORIGINAL_GUARDS_DIAGNOSTIC_ONLY')
        require(row['cleanup_confirmed'] and row['owned_tree_empty'],'CLEANUP')
        if row['heavy_work_started']:
            require(row['worker_created'] and row['job_assigned'] and row['writer_authorized']
                and row['post_hash_runtime_admission_revalidated'] and row['owned_limits_readback']['verified']
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],
                'ACTUAL_ASSIGNED_JOB_TERMINAL')
        require(q.pin(d.PARENT['path'])==d.PARENT and row['current_case_closing_pin']==d.PARENT,'CURRENT_PARENT')
        parent=q.json(d.PARENT['path']);expected,exe=d.parent_scope(parent)
        frozen=p.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:require(all(frozen.get(n)==pin for n,pin in expected.items()),'WHOLE_PARENT_CLOSURE')
        for n,pin in {**expected,**frozen}.items():require(q.pin(n)==pin,'WHOLE_CURRENT_SOURCE')
        require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'CURRENT_R04')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(row['source_test_names']==names and row['source_module_instances']==modules
            and len(names)==249 and len(modules)==59 and row['selected_test_names']==[d.NAME]
            and names.count(d.NAME)==1 and row['test_package_profile_config']==list(p.b.CONFIG),'ORIGINAL_SCOPE_NOT_SELECTED_AS_FULL')
        cap=row['capture_diagnostics'];observation=None
        if cap is not None:
            require(cap['per_stream_limit_bytes']==32768 and cap['raw_log_content_included'] is False
                and cap['native_Process_query_started'] is False and cap['error_code'] is None
                and all(type(n) is int and 0<=n<=32768 for n in cap['buffered_bytes'].values()),'BOUNDED_NO_NATIVE_CAPTURE')
            require(row['stage_record_error_code'] is None,'NO_REJECTED_MARKERS')
            observation=checked_observation(cap['signed_stage_cost'])
        finished=row['state']==d.FINISHED
        require(row['selected_body_finished'] is finished,'SELECTED_BODY_NOT_BROAD_PASS')
        if finished:
            require(row['exit_code']==0 and row['stop_reason'] is None and observation is not None
                and observation['fully_observed_case_sequences']==16,'COMPLETE_SELECTED_TIMING_ONLY')
        else:require(isinstance(row['stop_reason'],str),'STOP_NOT_PROMOTED')
        for n in (d.SELF,d.TEST,d.stage.SELF,d.stage.TEST,d.stage.SOURCE,d.stage.CONSUMER,d.stage.NEW):q.pin(n)
        d.contracts();q.finish()
        out.update(state=PASS,source_closing_exact=True,current_compiled249_qualified=True,
            contract_tests_passed=130,current_Rust_input_count=785,original_run_state=row['state'],
            original_stop_reason=row['stop_reason'],selected_body_finished=finished,
            signed_stage_cost=observation,current_case_closing_pin=d.PARENT,
            protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),compiled_test_executable_pin=exe,
            original_source_final_hash_not_retroactively_promoted=not finished,owned_job_final=row.get('job_final'),
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
            available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None,
            structured_stage_observations_not_exact_CPU_profile=True,nested_outer_signed_pair_must_not_be_double_counted=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','original_stop_reason','selected_body_finished',
            'contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
