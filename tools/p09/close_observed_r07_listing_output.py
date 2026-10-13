"""P186 separate fresh post-closing for clean validated r07 --list output.

P184 original final-source CPU STOP stays STOP/false. Only after fresh whole
post-source/EXE closing can a NEW compound listing qualification be accepted.
No list/test rerun, narrowing of249, SQL/Hangul, cache or skipped input checks.
"""
import argparse
import json
import io
import sys
import time
import unittest
from unittest.mock import patch
import run_observed_r07_inventory as run
import near_saturation_read_backpressure as pressure
b=run.b; s=run.s; c=run.c
SELF='tools/p09/close_observed_r07_listing_output.py'
TEST='tools/p09/tests/test_observed_r07_listing_post_closing.py'
ACTUAL=dict(path=run.ACTUAL,bytes=1845292,sha256='17537e88f376817d83ae37851d402ae405d414c4c9be7e26ae61456756eaa48e')
PREP=dict(path=run.PREP,bytes=336632,sha256='b16a0197cee62475bcb1a5b80ea22feca8e37721b4f194787ca0f97770b713ec')
LIGHT=dict(path=run.LIGHT,bytes=2735,sha256='e7b817d26d8f1964543c7cdc5c1d7da7a0f13db47a725d097ee233d851a00941')
EXE=dict(path=b.executable_name(),bytes=14216704,sha256='2b47e5815500549401f6f1960d92ba67f0d3410fc39d91cc91fd7f886d67dc5d')
PASS='PASS_R07_VALIDATED_LIST_OUTPUT_FRESH_POST_CLOSING_ONLY_NOT_FULL249_OR_GATE'
DEST='implementation/p09/evidence/p09-186-observed-r07-list-output.source-closing-run01.v1.json'

def metadata_scope(row):
    run.prior.require(row['state']=='STOPPED_NOT_ACCEPTED' and row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and row['operation_phase']=='final_source_freeze' and type(row['exit_code']) is int and row['exit_code']==0
        and row['cleanup_confirmed'] and row['owned_tree_empty'] and row['heavy_work_started']
        and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
        and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
        and row['owned_limits_readback']['verified'] and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
        and row['policy']==c.POLICY and row['maximum_seconds']==180,'ONLY_CLEAN_LIST_THEN_POST_CPU_STOP')
    run.prior.require(row['fresh_EXE_list_only'] and not row['runtime_tests_executed']
        and not row['compiled_inventory_exact'] and not row['current_compiled249_qualified']
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and not row['product_complete'] and not row['PC_freeze_resolved']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['expected_test_count']==249 and row['current_Rust_input_count']==785
        and row['current_compile_closing_pin']==run.prior.CLOSING
        and row['compiled_test_executable_pin']==EXE and row['test_package_profile_config']==list(b.b.CONFIG),
        'NO_ORIGINAL_PASS_OR_TEST_BODY_PROMOTION')
    cap=row['capture_diagnostics']
    run.prior.require(cap['error_code'] is None and cap['per_stream_limit_bytes']==32768
        and not cap['raw_log_content_included'] and cap['received_bytes']==cap['buffered_bytes']
        and cap['received_bytes']['stderr']==0 and 0<cap['received_bytes']['stdout']<=32768,
        'COMPLETE_VALIDATED_LIST_CAPTURE')
    names=row['source_test_names'];modules=row['source_module_instances']
    run.prior.require(len(names)==len(set(names))==249 and len(modules)==59,'ALL249_59')
    # This is source replay, NOT newly observed stdout. The pinned executed
    # Capture.communicate validates exact names BEFORE c.run can reach the
    # recorded final_source_freeze. Its success/exit0 flow is preserved below.
    replay=''.join(n+': test\n' for n in sorted(names))
    run.prior.i.validate_listing(replay,names)
    run.prior.require(len(replay.encode())==cap['received_bytes']['stdout'],'EXACT_TERSE_LIST_BYTE_COUNT')
    frozen=s.inputs.inventory(row['source_freeze'],1434)
    run.prior.require(frozen.get(EXE['path'])==EXE and sum(n.endswith('.exe') for n in frozen)==68
        and row['source_reader_passes'][0]['read_passes']==1434
        and row['source_reader_passes'][0]['bytes_read']==sum(p['bytes'] for p in frozen.values())
        and len(row['source_reader_passes'])==2
        and row['parent_ProcessTimes_observation_connected'] and row['readonly_parent_ProcessTimes_observation_connected']
        and row['readonly_parent_Process_query_executed'] and not row['foreign_Process_query_executed']
        and not row['additional_observer_thread_started'] and not row['readonly_extra_sampler_thread_started']
        and row['original_resource_guards_and_read_rates_preserved'] and row['original_P182_CPU_stop_receipt_preserved'],
        'WHOLE_BEFORE_AND_EXPLICIT_PARENT_ONLY')
    return frozen

def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_r07_listing_post_closing')
    with patch('subprocess.Popen',side_effect=AssertionError('P186_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P186_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P186_NO_NEW_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    run.prior.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'POST_LIST_CLOSING_CONTRACT6')
    return dict(post_closing_contract_tests_passed=6)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    run.prior.require(c.Path.cwd().resolve()==c.ROOT,'POST_LIST_CLOSING_CWD')
    destination=s.scoped_path(DEST if mode=='actual' else 'implementation/p09/evidence/p09-186-observed-r07-list-output.light-run01.v1.json',fresh=True)
    resources=run.observation.ObservedResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        original_run_state='STOPPED_NOT_ACCEPTED',original_listing_run_accepted=False,
        original_source_final_hash_not_retroactively_promoted=True,
        actual_new_list_Cargo_SQL_Hangul_child_or_test_body_executed=False,
        own_parent_Process_query_executed=True,foreign_Process_query_executed=False,
        extra_sampler_thread_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=pressure.PressureReader(resources);out.update(contracts())
        for n in (SELF,TEST):q.pin(n)
        run.prior.require(q.pin(ACTUAL['path'])==ACTUAL,'IMMUTABLE_ORIGINAL_LIST_STOP')
        actual=q.json(ACTUAL['path']);frozen=metadata_scope(actual)
        if mode=='actual':
            run.prior.require(q.pin(PREP['path'])==PREP and q.pin(LIGHT['path'])==LIGHT
                and q.pin(run.prior.CLOSING['path'])==run.prior.CLOSING,'ALL_BOUND_PREPARATION_AND_BUILD')
            prep=q.json(PREP['path']);light=q.json(LIGHT['path']);parent=q.json(run.prior.CLOSING['path'])
            expected,exe=run.prior.closing_scope(parent);prepared=s.inputs.inventory(prep['bound_input_pins'],1434)
            run.prior.require(prep['state']=='PASS_R07_LISTING_PREPARATION_ONLY_NOT_ACTUAL_OR_GATE'
                and prep['source_closing_exact'] and prep['contract_tests_passed']==33
                and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1434
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
                and light['state']=='PASS_OBSERVED_R07_LISTING_CONTRACT33_ONLY_NOT_ACTUAL_OR_CAUSE'
                and light['contract_tests_passed']==33 and light['resource_stop_reason'] is None
                and light['resource_watcher_cleanup_confirmed']
                and all(frozen.get(n)==p for n,p in {**expected,**prepared}.items()),'ALL_BEFORE_COMPILE_LIST_BINDINGS')
            q.reader.protected=frozenset(n for n in frozen if n.endswith('.exe'))
            for n,pin in {**expected,**prepared,**frozen}.items():run.prior.require(q.pin(n)==pin,'EVERY_INPUT_FRESH_AFTER_LIST')
            run.prior.require(q.pin(run.FAILED_PREP)==light['original_P182_preparation_pin'],'P182_STOP_IMMUTABLE')
            rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
            run.prior.require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
            names,modules=b.p.source_scope(q,frozen)
            run.prior.require(names==actual['source_test_names']==parent['source_test_names']==prep['source_test_names']
                and modules==actual['source_module_instances']==parent['source_module_instances']==prep['source_module_instances'],
                'ALL_ORIGINAL249_59_CURRENT')
            archive=q.json(b.parser.ARCHIVE);_,old=b.parser.preimage(archive,b.parser.SOURCE)
            b.parser.inverse(q.text(b.parser.SOURCE),old.decode('utf-8'))
            run.contracts();pressure.contracts()
            for n in (*run.helpers(),pressure.SELF,pressure.TEST,'implementation/p09/evidence/p09-185-near-saturation-read-backpressure.light-run01.v1.json'):
                q.pin(n)
            run.prior.require(q.pin(exe['path'])==exe,'CURRENT_R07_EXACT')
            q.finish();out.update(state=PASS,source_closing_exact=True,current_compiled249_qualified=True,
                separate_current_post_closing_exact=True,current_build_accepted=True,compiled_test_count=249,
                runtime_test_bodies_executed=False,source_test_names=names,source_module_instances=modules,
                current_Rust_input_count=785,current_source_module_instance_count=59,protected_parent_EXE_inputs_exact=68,
                compiled_test_executable_pin=exe,current_compile_closing_pin=run.prior.CLOSING,
                actual_inventory_receipt_pin=ACTUAL,preparation_receipt_pin=PREP,
                listing_contract_tests_passed=33,reader_contract_tests_passed=43,total_contract_tests_passed=82,
                original_incomplete_final_freeze_preserved=True,validated_original_list_output_by_pinned_control_flow=True,
                source_listing_replay_not_new_stdout=True,actual_original_stdout_bytes=actual['capture_diagnostics']['received_bytes']['stdout'])
        else:
            q.finish();out.update(state='PASS_LIST_POST_CPU_STOP_SCOPE_CONTRACT6_ONLY_NOT_WHOLE_CLOSING_OR_GATE',
                receipt_scope_fresh_hash_exact=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=run.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';out['current_compiled249_qualified']=False
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','compiled_test_count','current_compiled249_qualified',
            'post_closing_contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
