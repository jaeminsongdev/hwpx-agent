"""P173 independent complete249 or terminal-stop accounting, no native queries."""
import json
import re
import time
import run_writer_current_full as d
SELF='tools/p09/audit_writer_current_full.py'
ACTUAL='implementation/p09/evidence/p09-173-writer-current-full.actual-run01.v1.json'
PASS='PASS_CURRENT_WRITER_ALL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
STOP_PASS='PASS_CURRENT_WRITER_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
def main():
    d.require(d.c.Path.cwd().resolve()==d.c.ROOT,'AUDIT_CWD')
    destination=d.s.scoped_path('implementation/p09/evidence/p09-173-writer-current-full.terminal-audit-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_SQL_native_or_audit_OS_child_executed=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_full_receipt_pin']=q.reader.snapshots[ACTUAL];passed=row['state']==d.PASS
        d.require(row['state'] in (d.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['current_inventory_closing_pin']==row['current_writer_inventory_closing_pin']==d.PARENT
            and row['current_Rust_input_count']==785 and row['expected_test_count']==249
            and row['maximum_seconds']==1200 and row['policy']==d.c.POLICY
            and row['runtime_admission_RAM_percent']==10 and not row['actual_new_Cargo_compile_executed']
            and not row['native_Process_query_executed'] and not row['actual_Hangul_COM_or_SQL_run']
            and not row['original_test_bodies_or_product_sources_changed'] and not row['original_owned_resource_policy_changed']
            and not row['raw_logs_printed_or_saved'] and not row['product_complete'] and not row['PC_freeze_resolved']
            and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','ORIGINAL_SCOPE')
        d.require(row['cleanup_confirmed'] and row['owned_tree_empty']
            and row['full249_current_qualified'] is passed and row['signed16_current_qualified'] is passed
            and row['tests_passed']==(249 if passed else None),'ORIGINAL_PASS_OR_STOP')
        if row['heavy_work_started']:
            d.require(all(row[k] for k in ('worker_created','job_assigned','writer_authorized',
                    'post_hash_runtime_admission_revalidated','test_body_execution_authorized'))
                and row['owned_limits_readback']['verified']
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'REAL_JOB_TERMINAL')
        else:d.require(not passed and row['test_body_execution_authorized'] is False,'NOT_STARTED_NOT_PASS')
        cap=row['capture_diagnostics']
        if passed:
            d.require(row['exit_code']==0 and row['stop_reason'] is None and cap is not None and cap['error_code'] is None
                and cap['per_stream_limit_bytes']==32768 and all(0<=n<=32768 for n in cap['received_bytes'].values())
                and not cap['raw_log_content_included'],'COMPLETE249_TERMINAL')
        else:d.require(isinstance(row['stop_reason'],str) and re.fullmatch('[A-Z_]+',row['stop_reason']),'ORIGINAL_STOP_CODE')
        d.require(q.pin(d.PARENT['path'])==d.PARENT,'CURRENT_COMPILED249_PIN')
        parent=q.json(d.PARENT['path']);expected,exe=d.parent_scope(parent)
        frozen=d.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:d.require(all(frozen.get(n)==p for n,p in expected.items()),'WHOLE_PARENT_IN_FREEZE')
        for n,p in {**expected,**frozen}.items():d.require(q.pin(n)==p,'WHOLE_CURRENT_INPUTS')
        d.require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'SAME_CURRENT_R06_EXE')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.d.p.source_scope(q,expected)
        d.require(row['source_test_names']==row['selected_test_names']==names==parent['source_test_names']
            and row['source_module_instances']==modules==parent['source_module_instances']
            and row['test_package_profile_config']==list(d.b.CONFIG)
            and row['signed_original_test_name']==d.original.full.cost.original.NAME,'UNFILTERED249_59')
        d.contracts()
        for n in d.helpers():q.pin(n)
        q.finish();out.update(state=PASS if passed else STOP_PASS,source_closing_exact=True,
            current_compiled249_qualified=True,full249_current_qualified=passed,signed16_current_qualified=passed,
            actual_tests_passed=249 if passed else None,original_run_state=row['state'],original_stop_reason=row['stop_reason'],
            original_source_final_hash_not_retroactively_promoted=not passed,contract_tests_passed=32,current_Rust_input_count=785,
            source_test_names=names,source_module_instances=modules,protected_EXE_inputs_exact=66,
            compiled_test_executable_pin=exe,owned_job_final=row.get('job_final'),capture_diagnostics=cap,
            current_writer_inventory_closing_pin=d.PARENT,native_Process_query_executed=False,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_tests_passed','contract_tests_passed',
            'original_stop_reason','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
