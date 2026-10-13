"""P181 separate fresh post-closing for clean r07 compiler output, not P180 retrofit.

Only CPU interruption in final_source_freeze AFTER clean compiler exit is
eligible. Every before-freeze input and protected EXE is read anew and again
at closing. Original STOP/false final hash is immutable; no test executes here.
"""
import argparse
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import build_xml_capacity_product as b
import build_parent_observed_xml_product as build
SELF='tools/p09/close_r07_compiler_output.py'
TEST='tools/p09/tests/test_r07_compiler_post_closing.py'
ACTUAL=dict(path=build.ACTUAL,bytes=3237422,sha256='8f73cb9ed6752cd1189bc6866882c816638adc32ecafce5377aa46c4d1b91541')
PREP=dict(path=build.PREPARATION,bytes=350361,sha256='943d449b67fe750246030cf29ca0059cf87042d81ceddb89bb17b6c9e14d2184')
PASS='PASS_R07_COMPILER_OUTPUT_FRESH_POST_CLOSING_ONLY_NOT_LISTING_RUNTIME_OR_GATE'
DEST='implementation/p09/evidence/p09-181-r07-compiler-output.source-closing-run01.v1.json'

def metadata_scope(row):
    b.require(row['state']=='STOPPED_NOT_ACCEPTED' and row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and row['operation_phase']=='final_source_freeze' and type(row['exit_code']) is int and row['exit_code']==0
        and row['heavy_work_started'] and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
        and row['cleanup_confirmed'] and row['owned_tree_empty'] and row['post_hash_stable_admission_revalidated']
        and row['owned_limits_readback']['verified'] and row['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
        and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
        and row['policy']==b.c.POLICY and row['maximum_seconds']==600 and row['compile_recipe']==b.recipe()
        and row['current_test_package_profile_config']==list(b.b.CONFIG),'ONLY_CLEAN_COMPILER_THEN_CPU_POST_STOP')
    b.require(row['executable_pin'] is None and not row['current_build_binding_accepted'] and not row['build_only_accepted']
        and not row['source_freeze_exact_after'] and not row['protected_executables_exact_after']
        and row['parser_delta_closing_pin']==b.PARENT and row['protected_executables_expected']==67
        and row['previous_parent_EXE_inputs_preserved']==67,'NO_OLD_RUN_PROMOTION')
    for key in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
                'product_complete','runtime_tests_executed','actual_SQL_or_native_executed','PC_freeze_resolved'):
        b.require(row[key] is False,'NO_RUNTIME_OR_CAUSE_PROMOTION')
    result=row['build_result'];b.b.profile_scope(result['catalog_profile'])
    b.require(result['build_finished_success'] and result['diagnostics']==[]
        and result['actual_catalog_test_true_validated_before_legacy_protocol_adapter']
        and result['executable_path']==b.executable_name(),'COMPILER_R07_ONLY')
    stream=result['validated_stream']
    b.require(stream['all_records_validated'] and not stream['raw_output_truncated'] and not stream['raw_logs_included']
        and stream['stdout_record_buffer_limit']==stream['stderr_total_limit']==32768
        and stream['stdout_total_JSON_IO_budget']==16*1024*1024
        and re.fullmatch('[0-9a-f]{64}',stream['raw_stdout_sha256']) is not None
        and 2<=stream['messages']<=2048 and 0<stream['raw_stdout_bytes']<=16*1024*1024
        and 0<stream['maximum_record_bytes']<=32768 and 0<=stream['raw_stderr_bytes']<=32768,'WHOLE_CARGO_VALIDATION')
    observation=row['capture_diagnostics']['validated_compiler_progress'];b.observed.require_closed(observation)
    text=''.join(b.observed.progress.prior.encode_event(r).decode() for r in observation['records'])
    replay=b.observed.progress.prior.observe(text)
    b.require(all(observation[k]==replay[k] for k in ('records','closing_observed','native_Process_query_started',
        'raw_names_paths_versions_commands_saved','exact_compiler_or_linker_phase_verified','unobserved_artifacts')),
        'ORIGINAL_PROGRESS_REPLAY')
    return b.s.inputs.inventory(row['source_freeze'],1418)

def contracts():
    sys.path.insert(0,str(b.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_r07_compiler_post_closing')
    with patch('subprocess.Popen',side_effect=AssertionError('P181_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P181_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P181_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    b.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'POST_CLOSING_CONTRACT6')
    return dict(post_closing_contract_tests_passed=6)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    destination=b.s.scoped_path(DEST if mode=='actual' else 'implementation/p09/evidence/p09-181-r07-compiler-output.light-run01.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,original_source_final_hash_not_retroactively_promoted=True,
        original_run_state='STOPPED_NOT_ACCEPTED',actual_new_Cargo_or_EXE_SQL_Hangul_or_child_executed=False,
        remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources)
        for n in (SELF,TEST):q.pin(n)
        out.update(contracts());b.require(q.pin(ACTUAL['path'])==ACTUAL,'IMMUTABLE_ACTUAL_STOP')
        row=q.json(ACTUAL['path']);frozen=metadata_scope(row)
        if mode=='actual':
            b.require(q.pin(PREP['path'])==PREP and q.pin(b.PARENT['path'])==b.PARENT,'PARENT_PINS')
            prep=q.json(PREP['path']);parent=q.json(b.PARENT['path']);expected,protected=b.parent_scope(parent)
            prepared=b.s.inputs.inventory(prep['bound_input_pins'],1418)
            b.require(prep['state']=='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE'
                and prep['source_closing_exact'] and prep['contract_tests_passed']==271
                and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1418
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
                and all(frozen.get(n)==p for n,p in {**expected,**prepared}.items()),'EVERY_PRE_RUN_INPUT_FROZEN')
            b.require(b.s.inputs.inventory(row['protected_executables'],67)==protected,'OLD67_UNCHANGED_SCOPE')
            for n,pin in {**expected,**prepared,**frozen}.items():b.require(q.pin(n)==pin,'EVERY_INPUT_FRESH_AFTER_COMPILER')
            rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
            b.require(len(rust)==785 and b.s.inputs.rust_inputs(b.c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
            names,modules=b.p.source_scope(q,frozen)
            b.require(names==parent['source_test_names'] and modules==parent['source_module_instances'],'ORIGINAL249_59')
            archive=q.json(b.parser.ARCHIVE);_,old=b.parser.preimage(archive,b.parser.SOURCE)
            b.parser.inverse(q.text(b.parser.SOURCE),old.decode('utf-8'))
            exe=q.pin(b.executable_name());b.require(exe['path'] not in frozen and exe['path'] not in protected,'NEW_R07_NOT_OLD_EXE')
            build.contracts()
            for n in build.helpers():q.pin(n)
            q.finish();out.update(state=PASS,source_closing_exact=True,current_build_accepted=True,
                separate_current_post_closing_exact=True,original_build_accepted=False,contract_tests_passed=271,
                total_contract_tests_passed=277,compiled_test_executable_pin=exe,protected_executables_exact=67,
                current_Rust_input_count=785,current_source_test_count=249,current_source_module_instance_count=59,
                source_test_names=names,source_module_instances=modules,parser_delta_closing_pin=b.PARENT,
                actual_build_receipt_pin=ACTUAL,preparation_receipt_pin=PREP,
                validated_compiler_progress=row['capture_diagnostics']['validated_compiler_progress'],
                original_stop_reason=row['stop_reason'],original_incomplete_final_freeze_preserved=True)
        else:
            q.finish();out.update(state='PASS_POST_COMPILER_CPU_STOP_SCOPE_CONTRACTS_ONLY_NOT_SOURCE_CLOSING_OR_GATE',
                source_closing_exact=False,receipt_scope_fresh_hash_exact=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';out['current_build_accepted']=False
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=b.weighted.resource_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','current_build_accepted','post_closing_contract_tests_passed',
            'error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
