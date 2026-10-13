"""P180 independent parent-observed r07 build closing; never compiled listing/runtime promotion."""
import json
import math
import re
import time
import build_xml_capacity_product as d
import build_parent_observed_xml_product as candidate
SELF='tools/p09/audit_parent_observed_xml_product.py'
DEST='implementation/p09/evidence/p09-180-parent-observed-xml-product.terminal-audit-run01.v1.json'
PASS='PASS_PARENT_OBSERVED_R07_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'

def main():
    destination=d.s.scoped_path(DEST,fresh=True);resources=d.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.weighted.WeightedLiveReader(resources);q.pin(SELF);row=q.json(candidate.ACTUAL)
        out['actual_build_receipt_pin']=q.reader.snapshots[candidate.ACTUAL];success=row['state']==d.PASS;recipe=d.recipe()
        d.require(row['state'] in (d.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['parser_delta_closing_pin']==d.PARENT and row['parser_lib74_accepted']
            and row['protected_executables_expected']==row['previous_parent_EXE_inputs_preserved']==67
            and row['whole_workspace_Rust_input_count']==785 and row['compile_recipe']==recipe
            and row['current_test_package_profile_config']==list(d.b.CONFIG) and row['policy']==d.c.POLICY
            and row['maximum_seconds']==600 and row['compile_admission_RAM_percent']==15
            and row['bounded_validated_compiler_progress_connected'] and row['original_complete_Cargo_validation_preserved']
            and row['weighted_fresh_source_reads_connected'] and not row['source_read_checks_skipped']
            and row['additional_process_query_or_thread'] and row['native_Process_query_executed']
            and row['parent_ProcessTimes_observation_connected'] and row['parent_ProcessTimes_query_executed']
            and not row['foreign_Process_query_executed'] and not row['additional_observer_thread_started']
            and row['additional_Process_query_scope']=='current_parent_pseudo_handle_only','ORIGINAL_SCOPE')
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
        d.require(q.pin(d.PARENT['path'])==d.PARENT,'PARENT_PIN');parent=q.json(d.PARENT['path'])
        expected,protected=d.parent_scope(parent);preparation=q.json(candidate.PREPARATION)
        d.require(preparation['state']=='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE'
            and preparation['source_closing_exact'] and preparation['parser_delta_closing_pin']==d.PARENT
            and preparation['contract_tests_passed']==271 and preparation['protected_executables_exact']==67
            and preparation['whole_original_parser_inverse_exact'] and preparation['compile_recipe']==recipe
            and preparation['resource_stop_reason'] is None and preparation['resource_watcher_cleanup_confirmed'],
            'CURRENT_PREPARATION')
        prepared=d.s.inputs.inventory(preparation['bound_input_pins'])
        d.require(all(prepared.get(n)==pin for n,pin in expected.items()) and preparation['IO']['finished']
            and preparation['IO']['bound_inputs']==preparation['IO']['final_fresh_hashes']==len(prepared),'WHOLE_PREPARATION')
        frozen=d.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:d.require(all(frozen.get(n)==pin for n,pin in prepared.items()),'EVERY_PREPARED_INPUT_FROZEN')
        d.require(d.s.inputs.inventory(row['protected_executables'],67)==protected,'PROTECTED67')
        for n,pin in {**expected,**prepared,**frozen}.items():d.require(q.pin(n)==pin,'WHOLE_FRESH_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        d.require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.p.source_scope(q,expected)
        d.require(names==parent['source_test_names']==preparation['source_test_names']
            and modules==parent['source_module_instances']==preparation['source_module_instances'],'ORIGINAL249_59')
        archive=q.json(d.parser.ARCHIVE);_,old=d.parser.preimage(archive,d.parser.SOURCE)
        d.parser.inverse(q.text(d.parser.SOURCE),old.decode('utf-8'))
        observation=(row.get('capture_diagnostics') or {}).get('validated_compiler_progress')
        if row['heavy_work_started']:
            d.require(observation is not None,'ACTUAL_OBSERVATION')
            text=''.join(d.observed.progress.prior.encode_event(r).decode() for r in observation['records'])
            replay=d.observed.progress.prior.observe(text)
            for key in ('records','closing_observed','native_Process_query_started','raw_names_paths_versions_commands_saved',
                'exact_compiler_or_linker_phase_verified','unobserved_artifacts'):
                d.require(observation[key]==replay[key],'OBSERVATION_REPLAY')
            d.require(type(observation['partial_marker_bytes']) is int and 0<=observation['partial_marker_bytes']<256,'PARTIAL_BOUND')
        readers=row['source_reader_passes'];d.require(isinstance(readers,list) and len(readers)<=3,'READERS_BOUNDED')
        for reader in readers:
            d.require(reader['read_rates_by_kind']=={'binary':1048576,'other':2097152}
                and reader['bytes_read']==reader['pacer_bytes_read']==sum(reader['bytes_read_by_kind'].values()),'ACTUAL_WEIGHTED_READS')
        observed=[s for s in row['samples'] if 'parent_cpu_machine_percent' in s]
        d.require(len(observed)==row['parent_CPU_observed_samples'] and len(observed)>0,'PARENT_ACTUAL_CPU_SAMPLES')
        for sample in observed:
            raw=sample['raw_system_cpu_delta_100ns']
            d.require(set(raw)=={'idle','kernel_including_idle','user','total'}
                and all(type(v) is int and v>=0 for v in raw.values())
                and raw['total']==raw['kernel_including_idle']+raw['user']>0 and raw['idle']<=raw['total'],
                'PARENT_RAW_SYSTEM_COUNTERS')
            own=sample['parent_cpu_delta_100ns'];ratio=sample['parent_cpu_machine_percent']
            d.require(type(own) is int and own>=0 and type(ratio) in (int,float) and math.isfinite(ratio)
                and 0<=ratio<=100 and ratio==round(100*own/raw['total'],6)
                and sample['system_cpu_percent']==round(100*(raw['total']-raw['idle'])/raw['total'],2)
                and sample['parent_affinity_mask']==1 and sample['parent_priority_readback']=='BelowNormal'
                and sample['parent_process_only'] and not sample['foreign_Process_query_executed'],'OWN_PARENT_ONLY')
        d.require(row['parent_CPU_max_machine_percent']==max(s['parent_cpu_machine_percent'] for s in observed)
            and not row['PC_freeze_cause_qualified'],'PARENT_SAMPLE_SUMMARY_NOT_CAUSE')
        contexts=row['protected_file_read_context']
        d.require(len(contexts)==len(readers) and len(contexts)<=3,'BOUNDED_EXISTING_READ_CONTEXT')
        for context,reader in zip(contexts,readers):
            d.require(context['read_passes']==reader['read_passes'] and context['bytes_read']==reader['bytes_read']
                and not context['arbitrary_source_paths_or_private_artifact_names_saved'],'NO_ADDITIONAL_READ')
            for key in ('last_completed_protected_EXE_path','interrupted_protected_EXE_path'):
                name=context[key];d.require(name is None or name in protected and name.endswith('.exe'),'PROTECTED_EXE_ALLOWLIST')
        exe=row['executable_pin'];result=row['build_result']
        if success:
            d.observed.require_closed(observation)
            d.require(all(row[k] for k in ('build_only_accepted','current_build_binding_accepted',
                'source_freeze_exact_after','protected_executables_exact_after'))
                and row['exit_code']==0 and row['stop_reason'] is None and len(readers)==3,'BUILD_SUCCESS')
            for reader in readers[:2]:
                d.require(reader['read_passes']==len(frozen) and reader['bytes_read']==sum(pin['bytes'] for pin in frozen.values()),
                    'EVERY_PRE_AND_POST_HASH_RETAINED')
            d.b.profile_scope(result['catalog_profile']);stream=result['validated_stream']
            d.require(result['build_finished_success'] and result['diagnostics']==[]
                and result['actual_catalog_test_true_validated_before_legacy_protocol_adapter']
                and result['executable_path']==recipe['executable_path']==exe['path']
                and exe['path'] not in protected and q.pin(exe['path'])==exe,'FRESH_R07_EXE')
            d.require(readers[2]['read_passes']==2 and readers[2]['bytes_read']==2*exe['bytes'],'EXE_REPEATED_FRESH_HASH')
            d.require(stream['all_records_validated'] and not stream['raw_output_truncated'] and not stream['raw_logs_included']
                and stream['stdout_record_buffer_limit']==stream['stderr_total_limit']==32768
                and stream['stdout_total_JSON_IO_budget']==16*1024*1024
                and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']),'EVERY_CARGO_RECORD')
        else:
            d.require(row['stop_reason'] is not None and not row['build_only_accepted']
                and not row['current_build_binding_accepted'] and not row['source_freeze_exact_after']
                and not row['protected_executables_exact_after'] and exe is None,'STOP_NOT_SUCCESS')
        candidate.contracts()
        for n in candidate.helpers():q.pin(n)
        old=q.json(d.ACTUAL)
        d.require(old['state']=='DEFERRED_NOT_STARTED' and old['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and not old['heavy_work_started'] and not old['worker_created'] and old['executable_pin'] is None
            and old['cleanup_confirmed'] and old['owned_tree_empty'],'OLD_PRE_GO_STOP_UNCHANGED')
        out.update(original_P177_stop_receipt_pin=q.reader.snapshots[d.ACTUAL],
            own_parent_CPU_max_machine_percent=row['parent_CPU_max_machine_percent'],
            protected_file_read_context=contexts,parent_native_CPU_query_scope='current_parent_pseudo_handle_only',
            additional_observer_thread_started=False,foreign_Process_query_executed=False,
            lower_owned_hash_rates={'binary':1048576,'other':2097152},
            independent_live_reader_rates={'binary':2621440,'other':4194304},
            CPU_stop_or_PC_freeze_cause_qualified=False)
        q.finish();out.update(state=PASS if success else 'PASS_R07_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE',
            source_closing_exact=True,current_build_accepted=success,contract_tests_passed=271,
            current_Rust_input_count=785,current_source_test_count=249,current_source_module_instance_count=59,
            source_test_names=names,source_module_instances=modules,protected_executables_exact=67,
            compiled_test_executable_pin=exe,validated_compiler_progress=observation,
            preparation_receipt_pin=q.reader.snapshots[candidate.PREPARATION],parser_delta_closing_pin=d.PARENT,
            original_stop_reason=row['stop_reason'],original_source_final_hash_not_retroactively_promoted=not success)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=d.parser.d.original.closed_error(error)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=d.weighted.resource_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','current_build_accepted','error_code',
            'wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
