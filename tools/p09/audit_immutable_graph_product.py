"""Independent current P156 product compile closing; no runtime/Gate promotion."""
import json
import re
import time
import build_immutable_graph_product as p

SELF='tools/p09/audit_immutable_graph_product.py'
ACTUAL='implementation/p09/evidence/p09-157-immutable-graph-product-build.actual-run01.v1.json'
PASS='PASS_CURRENT_IMMUTABLE_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'


def main():
    p.require(p.c.Path.cwd().resolve()==p.c.ROOT,'AUDIT_CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-157-immutable-graph-product-build.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,runtime_tests_executed=False,
        full_product_performance_improvement_measured=False,actual_SQL_native_or_new_OS_child_executed=False,
        remaining_non_permission_work_units=76,resource_samples=resources.samples)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_build_receipt_pin']=q.reader.snapshots[ACTUAL]
        stopped=row['state']=='STOPPED_NOT_ACCEPTED'
        if stopped:
            p.require(row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU' and row['build_only_accepted'] is False
                and row['current_build_binding_accepted'] is False and row['source_freeze_exact_after'] is False
                and row['protected_executables_exact_after'] is False and row['build_result'] is None
                and row['executable_pin'] is None and row['exit_code'] is None
                and all(x['system_cpu_percent']>=98 for x in row['samples'][-4:]),'AUDIT_ORIGINAL_CPU_STOP_NOT_PROMOTED')
        else:
            p.require(row['state']==p.PASS and row['build_only_accepted'] is True and row['current_build_binding_accepted'] is True
                and row['source_freeze_exact_after'] is True and row['protected_executables_exact_after'] is True
                and row['exit_code']==0 and row['stop_reason'] is None,'AUDIT_SUCCESS_SCOPE')
        p.require(row['source249_generation_connected_to_actual_build'] is True and row['whole_workspace_Rust_input_count']==785
            and row['protected_executables_expected']==row['previous_parent_EXE_inputs_preserved']==61
            and row['current_graph_delta_closing_pin']==p.PARENT,'AUDIT_ACTUAL_BUILD_SCOPE')
        p.require(row['cleanup_confirmed'] is True
            and row['owned_tree_empty'] is True and row['job_final']['active_processes']==0
            and row['job_final']['owned_processes']==[]
            and all(row[k] is True for k in ('worker_created','job_assigned','writer_authorized'))
            and row['post_hash_stable_admission_revalidated'] is True and row['compile_admission_RAM_percent']==15,'AUDIT_OWNED_TERMINAL')
        p.require(row['policy']==p.c.POLICY and row['maximum_seconds']==600 and row['owned_limits_readback']['verified'] is True
            and row['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
            and row['current_test_package_profile_config']==list(p.b.CONFIG) and row['compile_recipe']==p.s.recipe(p.RUN),'AUDIT_ORIGINAL_POLICY')
        for flag in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified','runtime_tests_executed',
                'actual_SQL_or_native_executed','product_complete','PC_freeze_resolved','full_product_performance_improvement_measured'):
            p.require(row[flag] is False,'AUDIT_BUILD_NOT_PRODUCT')
        result=row['build_result'];stream=None
        if not stopped:
            p.b.profile_scope(result['catalog_profile'])
            p.require(result['build_finished_success'] is True and result['diagnostics']==[]
                and result['actual_catalog_test_true_validated_before_legacy_protocol_adapter'] is True
                and result['executable_path']==p.b.executable_name(p.RUN),'AUDIT_LIBTEST_CATALOG')
            stream=result['validated_stream']
            p.require(stream['all_records_validated'] is True and stream['raw_output_truncated'] is False
                and stream['raw_logs_included'] is False and stream['stdout_record_buffer_limit']==32768
                and stream['stderr_total_limit']==32768 and stream['stdout_total_JSON_IO_budget']==16*1024*1024
                and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']),'AUDIT_WHOLE_CARGO_STREAM')
        frozen=p.s.inputs.inventory(row['source_freeze'])
        for n,pin in frozen.items():p.require(q.pin(n)==pin,'AUDIT_WHOLE_FROZEN_INPUT_CURRENT')
        p.require(q.pin(p.PARENT['path'])==p.PARENT,'AUDIT_PARENT_PIN')
        expected,protected=p.parent_scope(q.json(p.PARENT['path']))
        p.require(all(frozen.get(n)==pin for n,pin in expected.items()),'AUDIT_WHOLE1246_PARENT')
        observed=p.s.inputs.inventory(row['protected_executables'],61)
        p.require(observed==protected and all(frozen.get(n)==pin for n,pin in protected.items()),'AUDIT_ALL61_EXES')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        p.require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        names,modules=p.source_scope(q,frozen)
        exe=row['executable_pin']
        if not stopped:
            p.require(exe['path']==p.b.executable_name(p.RUN)
                and exe['path'] not in protected and q.pin(exe['path'])==exe,'AUDIT_NEW_CURRENT_EXE')
        for n in p.helpers():q.pin(n)
        out.update(p.contracts());q.finish()
        out.update(state='PASS_CPU_STOP_ACCOUNTED_CURRENT_INPUTS_ONLY_NOT_PRODUCT_BUILD_OR_GATE' if stopped else PASS,
            source_closing_exact=True,current_Rust_input_count=785,
            current_source_test_count=249,current_source_module_instance_count=59,source_test_names=names,source_module_instances=modules,
            protected_executables_exact=61,parent_EXE_inputs_preserved=61,compiled_test_executable_pin=exe,
            actual_libtest_profile=result['catalog_profile'] if result else None,actual_build_stream=stream,owned_job_final=row['job_final'],
            original_stop_reason=row['stop_reason'],original_source_final_hash_not_retroactively_promoted=stopped,
            current_build_accepted=not stopped,
            original_owned_policy_unchanged=True,graph_delta_closing_pin=p.PARENT,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']),
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P157_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P157_AUDIT_REDACTED_FAILURE'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
