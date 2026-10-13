"""Independent source/Cargo/native-diagnostic closing of P158 current build."""
import json
import re
import time
import build_observed_graph_product as d

p=d.p
SELF='tools/p09/audit_observed_graph_build.py'
ACTUAL='implementation/p09/evidence/p09-158-observed-graph-build.actual-run01.v1.json'
PASS='PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'


def main():
    d.require(p.c.Path.cwd().resolve()==p.c.ROOT,'AUDIT_CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-158-observed-graph-build.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_SQL_native_or_new_OS_child_executed=False,
        remaining_non_permission_work_units=76,resource_samples=resources.samples)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_build_receipt_pin']=q.reader.snapshots[ACTUAL];success=row['state']==d.PASS
        if success:
            d.require(all(row[k] is True for k in ('build_only_accepted','current_build_binding_accepted',
                'source_freeze_exact_after','protected_executables_exact_after')) and row['exit_code']==0 and row['stop_reason'] is None,'AUDIT_ACTUAL_SUCCESS')
        else:
            d.require(row['state']=='STOPPED_NOT_ACCEPTED' and row['stop_reason'] is not None
                and all(row[k] is False for k in ('build_only_accepted','current_build_binding_accepted',
                    'source_freeze_exact_after','protected_executables_exact_after'))
                and row['build_result'] is None and row['executable_pin'] is None,'AUDIT_ORIGINAL_STOP_NOT_SUCCESS')
        d.require(row['current_graph_delta_closing_pin']==p.PARENT and row['previous_CPU_stop_closing_pin']==d.STOP_PIN
            and row['protected_executables_expected']==row['previous_parent_EXE_inputs_preserved']==61
            and row['whole_workspace_Rust_input_count']==785 and row['observed_same_owned_job'] is True
            and row['host_observed_target']=='cargo-launcher-process'
            and row['original_emergency_cpu_guard_unchanged'] is True and row['individual_duplicated_PID_attribution'] is False,'AUDIT_CURRENT_BINDING')
        d.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['job_final']['active_processes']==0
            and row['job_final']['owned_processes']==[] and all(row[k] for k in ('worker_created','job_assigned','writer_authorized'))
            and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent']==15,'AUDIT_JOB_TERMINAL')
        d.require(row['policy']==p.c.POLICY and row['maximum_seconds']==600 and row['owned_limits_readback']['verified']
            and row['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
            and row['current_test_package_profile_config']==list(p.b.CONFIG) and row['compile_recipe']==p.s.recipe(d.RUN),'AUDIT_UNCHANGED_CAPS')
        for key in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified','runtime_tests_executed',
                'actual_SQL_or_native_executed','product_complete','PC_freeze_resolved','full_product_performance_improvement_measured'):
            d.require(row[key] is False,'AUDIT_NOT_FULL_PRODUCT')
        frozen=p.s.inputs.inventory(row['source_freeze'])
        for n,pin in frozen.items():d.require(q.pin(n)==pin,'AUDIT_WHOLE_CURRENT_FROZEN_INPUT')
        d.require(q.pin(d.STOP_PIN['path'])==d.STOP_PIN,'AUDIT_IMMUTABLE_PREVIOUS_STOP')
        stop=q.json(d.STOP_PIN['path']);prior=p.s.inputs.inventory(stop['bound_input_pins'],1251)
        d.require(all(frozen.get(n)==pin for n,pin in prior.items()),'AUDIT_WHOLE_STOP_CLOSURE')
        d.require(q.pin(p.PARENT['path'])==p.PARENT,'AUDIT_GRAPH_CLOSING_PIN')
        expected,protected=p.parent_scope(q.json(p.PARENT['path']))
        d.require(all(frozen.get(n)==pin for n,pin in expected.items())
            and p.s.inputs.inventory(row['protected_executables'],61)==protected,'AUDIT_ALL_PARENT_AND_EXE61')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_RUST785')
        names,modules=p.source_scope(q,frozen);exe=row['executable_pin'];result=row['build_result']
        cap=row['capture_diagnostics'];records=cap['host_cpu_records']
        for item in records:d.observed.valid_record(item)
        d.require(cap['causal_attribution'] is False and cap['raw_names_paths_commands_saved'] is False
            and cap['diagnostic_snapshots_max']==10 and cap['diagnostic_frame_limit']==2800,'AUDIT_DIAGNOSTIC_BOUNDARY')
        if success:
            p.b.profile_scope(result['catalog_profile']);stream=result['validated_stream']
            d.require(result['build_finished_success'] and result['diagnostics']==[]
                and result['actual_catalog_test_true_validated_before_legacy_protocol_adapter']
                and result['executable_path']==p.b.executable_name(d.RUN)
                and exe['path']==p.b.executable_name(d.RUN) and exe['path'] not in protected and q.pin(exe['path'])==exe,'AUDIT_FRESH_COMPLETE_BUILD')
            d.require(stream['all_records_validated'] and not stream['raw_output_truncated'] and not stream['raw_logs_included']
                and stream['stdout_record_buffer_limit']==stream['stderr_total_limit']==32768
                and stream['stdout_total_JSON_IO_budget']==16*1024*1024
                and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']),'AUDIT_WHOLE_CARGO_STREAM')
            d.require(cap['explicit_query_cleanup_confirmed'] and cap['host_cpu_error_code'] is None
                and records[0]['kind']=='ready' and records[-1]['kind']=='closed'
                and 1<=sum(r['kind']=='sample' for r in records)<=10,'AUDIT_NATIVE_CLOSING')
        for n in (*p.helpers(),d.SELF,d.TEST):q.pin(n)
        out.update(d.contracts());q.finish()
        out.update(state=PASS if success else 'PASS_OBSERVED_GRAPH_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE',
            source_closing_exact=True,current_build_accepted=success,current_Rust_input_count=785,current_source_test_count=249,
            current_source_module_instance_count=59,source_test_names=names,source_module_instances=modules,
            protected_executables_exact=61,compiled_test_executable_pin=exe,graph_delta_closing_pin=p.PARENT,
            previous_CPU_stop_closing_pin=d.STOP_PIN,original_stop_reason=row['stop_reason'],
            original_source_final_hash_not_retroactively_promoted=not success,owned_job_final=row['job_final'],
            host_cpu_records=records,explicit_query_cleanup_confirmed=cap['explicit_query_cleanup_confirmed'],
            host_cpu_error_code=cap['host_cpu_error_code'],actual_libtest_profile=result['catalog_profile'] if result else None,
            actual_build_stream=result['validated_stream'] if result else None,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']),
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P158_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P158_AUDIT_REDACTED_FAILURE'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','current_build_accepted','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
