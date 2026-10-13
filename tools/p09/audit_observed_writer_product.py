"""Independent P171 whole closure and compiler-observation accounting."""
import json
import re
import time
import build_observed_writer_product as d
from unittest.mock import patch
SELF='tools/p09/audit_observed_writer_product.py'
ACTUAL='implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run01.v1.json'
PASS='PASS_OBSERVED_WRITER_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'

def main():
    destination=d.s.scoped_path('implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_build_receipt_pin']=q.reader.snapshots[ACTUAL];success=row['state']==d.PASS
        with patch.object(d.d,'RUN',6):recipe=d.d.recipe()
        d.require(row['state'] in (d.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['writer_xml_delta_closing_pin']==d.WRITER_PARENT
            and row['previous_build_stop_closing_pin']==d.PARENT
            and row['protected_executables_expected']==row['previous_parent_EXE_inputs_preserved']==65
            and row['whole_workspace_Rust_input_count']==785 and row['writer_xml_lib71_accepted']
            and row['compile_recipe']==recipe and row['current_test_package_profile_config']==list(d.b.CONFIG)
            and row['policy']==d.c.POLICY and row['maximum_seconds']==600
            and row['compile_admission_RAM_percent']==15 and not row['native_Process_query_executed']
            and row['bounded_validated_compiler_progress_connected']
            and row['original_complete_Cargo_validation_preserved']
            and not row['additional_process_query_or_thread'],'ORIGINAL_SCOPE')
        for flag in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
            'runtime_tests_executed','actual_SQL_or_native_executed','product_complete','PC_freeze_resolved',
            'full_product_performance_improvement_measured'):
            d.require(row[flag] is False,'NO_RUNTIME_PROMOTION')
        d.require(row['cleanup_confirmed'] and row['owned_tree_empty'],'TERMINAL_CLEANUP')
        if row['heavy_work_started']:
            d.require(row['worker_created'] and row['job_assigned'] and row['writer_authorized']
                and row['post_hash_stable_admission_revalidated'] and row['owned_limits_readback']['verified']
                and row['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'JOB_CLEANUP')
        d.require(q.pin(d.PARENT['path'])==d.PARENT,'STOP_PARENT_PIN')
        parent=q.json(d.PARENT['path']);expected,protected=d.parent_scope(parent)
        frozen=d.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:d.require(all(frozen.get(n)==p for n,p in expected.items()),'PARENT_FREEZE')
        d.require(d.s.inputs.inventory(row['protected_executables'],65)==protected,'PROTECTED65')
        for n,p in {**expected,**frozen}.items():d.require(q.pin(n)==p,'WHOLE_FRESH_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.d.p.source_scope(q,expected)
        d.require(names==parent['source_test_names'] and modules==parent['source_module_instances'],'ORIGINAL249_59')
        observation=(row.get('capture_diagnostics') or {}).get('validated_compiler_progress')
        if row['heavy_work_started']:
            d.require(observation is not None,'ACTUAL_OBSERVATION')
            text=''.join(d.progress.prior.encode_event(r).decode() for r in observation['records'])
            replay=d.progress.prior.observe(text)
            for k in ('records','closing_observed','native_Process_query_started','raw_names_paths_versions_commands_saved',
                'exact_compiler_or_linker_phase_verified','unobserved_artifacts'):
                d.require(observation[k]==replay[k],'OBSERVATION_REPLAY')
            d.require(type(observation['partial_marker_bytes']) is int and 0<=observation['partial_marker_bytes']<256,'PARTIAL_BOUND')
        exe=row['executable_pin'];result=row['build_result']
        if success:
            d.require_closed(observation)
            d.require(all(row[k] for k in ('build_only_accepted','current_build_binding_accepted',
                'source_freeze_exact_after','protected_executables_exact_after'))
                and row['exit_code']==0 and row['stop_reason'] is None,'BUILD_SUCCESS')
            d.b.profile_scope(result['catalog_profile']);stream=result['validated_stream']
            d.require(result['build_finished_success'] and result['diagnostics']==[]
                and result['actual_catalog_test_true_validated_before_legacy_protocol_adapter']
                and result['executable_path']==recipe['executable_path']==exe['path']
                and exe['path'] not in protected and q.pin(exe['path'])==exe,'FRESH_R06_EXE')
            d.require(stream['all_records_validated'] and not stream['raw_output_truncated'] and not stream['raw_logs_included']
                and stream['stdout_record_buffer_limit']==stream['stderr_total_limit']==32768
                and stream['stdout_total_JSON_IO_budget']==16*1024*1024
                and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']),'EVERY_CARGO_RECORD')
        else:
            d.require(row['stop_reason'] is not None and not row['build_only_accepted']
                and not row['current_build_binding_accepted'] and not row['source_freeze_exact_after']
                and not row['protected_executables_exact_after'] and exe is None,'STOP_NOT_SUCCESS')
        d.contracts()
        for n in d.helpers():q.pin(n)
        q.finish()
        out.update(state=PASS if success else 'PASS_OBSERVED_WRITER_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE',
            source_closing_exact=True,current_build_accepted=success,contract_tests_passed=d.CONTRACT_COUNT,
            current_Rust_input_count=785,current_source_test_count=249,current_source_module_instance_count=59,
            source_test_names=names,source_module_instances=modules,protected_executables_exact=65,
            compiled_test_executable_pin=exe,validated_compiler_progress=observation,
            original_stop_reason=row['stop_reason'],original_source_final_hash_not_retroactively_promoted=not success,
            writer_xml_delta_closing_pin=d.WRITER_PARENT,previous_build_stop_closing_pin=d.PARENT)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','current_build_accepted',
            'error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
