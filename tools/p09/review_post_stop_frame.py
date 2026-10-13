"""P210 원 post-source CPU 중단을 보존한 semantic 후보 조사. runtime 수용 아님.

통과 body를 재실행하지 않고 current-source closing으로 진행할 수 있는지
검사한다. STOP를 PASS로 바꾸거나 전체 입력의 최신성을 주장하지 않는다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_locked_runtime_r07_case as prior
import observe_shared_metadata_recheck as observation
import owned_source_read_pressure as owned

SELF='tools/p09/review_post_stop_frame.py'
TEST='tools/p09/tests/test_review_post_stop_frame.py'
FRAME=dict(path='implementation/p09/evidence/locked-r07/p208-frame-actual-run01.v1.json',
    bytes=1043780,sha256='01818f2b948d46e2f25b1ea4ad47bbd78ab18f2e6f53480fc2766e2bf565dbe2')
BODY=dict(path='implementation/p09/evidence/locked-r07/cases/p208-case-012-run01.json',
    bytes=781629,sha256='be515561752ee9cf873a1b3c959d99a1d70da0d7c5d2b20cc66f2fed91df0199')
STOP='STOP_SUSTAINED_SYSTEM_CPU'


def require(ok,code):prior.require(ok,'POST_STOP_REVIEW_'+code)


def review(frame,body):
    require(frame['schema_version']==prior.CLOSING_SCHEMA and frame['state']=='FAILED_NOT_ACCEPTED'
        and frame['resource_stop_reason']==frame['error_code']==STOP,'ORIGINAL_FRAME_FAILURE_PRESERVED')
    require(body['schema_version']==prior.SCHEMA and body['state']=='STOPPED_NOT_ACCEPTED'
        and body['resource_stop_reason']==body['stop_reason']==STOP
        and body['operation_phase']=='final_source_freeze','POST_SOURCE_STOP_ONLY')
    require(frame['case_receipt_path']==BODY['path'] and frame['selected_test_index']==12
        and frame['selected_test_name']==body['selected_test_names'][0]
        and body['selected_test_names']==body['passed_test_names'] and len(body['passed_test_names'])==1
        and body['test_arguments']==prior.v.arguments(frame['selected_test_name']),'EXACT_NAMED_ONE_CASE')
    require(body['policy']==prior.c.POLICY and type(body['maximum_seconds']) is int and body['maximum_seconds']==1200,
        'ORIGINAL_POLICY_AND_DEADLINE')
    require(type(body['exit_code']) is int and body['exit_code']==0
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False)
        and body['capture_diagnostics']['error_code'] is None
        and body['capture_diagnostics']['buffered_bytes']==body['capture_diagnostics']['received_bytes']
        and body['capture_diagnostics']['buffered_bytes']['stderr']==0
        and 0<body['capture_diagnostics']['buffered_bytes']['stdout']<=32768,'STRICT_COMPLETED_BODY')
    require(all(body[k] is True for k in ('cleanup_confirmed','owned_tree_empty','worker_created','job_assigned',
        'writer_authorized','actual_job_membership_checked','owned_limits_verified','minimal_worker_source_only_import_connected'))
        and type(body['job_final']['active_processes']) is int and body['job_final']['active_processes']==0
        and body['job_final']['owned_processes']==[] and body['owned_limits_readback']['verified'] is True,
        'ORIGINAL_GO_JOB_LIMITS_AND_CLEANUP')
    source=frame['source_frame'];boundary=source['actual_byte_boundaries'];pins=prior.v.pins(body['source_freeze'])
    require(len(pins)==1473 and len(boundary)==1 and boundary[0]['role']=='before'
        and prior.v.pins(boundary[0]['actual_byte_pins'])==pins and source['input_count']==1473
        and source['input_bytes']==sum(pin['bytes'] for pin in pins.values()),'FULL_BEFORE_BYTE_INPUTS')
    readers=body['owned_source_reader_passes']
    require(len(readers)==2 and boundary[0]['reader_diagnostics']==readers[0]
        and readers[0]['read_passes']==1473 and readers[0]['bytes_read']==source['input_bytes']
        and 0<readers[1]['read_passes']<1473 and 0<readers[1]['bytes_read']<source['input_bytes']
        and all(row['original_owned_read_operations_preserved'] is True
            and row['read_rates_by_kind']==dict(binary=1048576,other=2097152) for row in readers),
        'INCOMPLETE_POST_HASH_NEVER_PROMOTED')
    handles=source['handles']
    require(source['frame_state']=='CLOSED' and source['registered_live_frame'] is False
        and handles['input_lock_handles_opened']==handles['input_lock_handles_closed']==1779
        and handles['input_lock_handles_remaining']==handles['active_reader_bindings']==handles['active_byte_streams']==0
        and handles['input_lock_cleanup_confirmed'] is True and handles['handle_close_failed_attempts']==0
        and frame['resource_watcher_cleanup_confirmed'] is True,'FRAME_HANDLES_ALL_CLOSED')
    require(all(row[k] is False for row in (frame,body) for k in
        ('full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and all(row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN' for row in (frame,body)),
        'NO_RUNTIME_OR_GATE_PROMOTION')
    return dict(semantic_body_capture_complete=True,source_closing_still_required=True,
        same_product_body_reexecution_allowed=False,runtime_accepted=False,original_failure_states_preserved=True,
        selected_test_index=12,selected_test_name=frame['selected_test_name'],full_original_source_inputs=1473,
        runtime_previously_accepted=11,new_pending_source_closing_candidates=1,
        complete_original_post_source_hash_claimed=False,CPU_cause_or_PC_freeze_resolution_established=False)


def contracts(frame,body):
    sys.path.insert(0,str(prior.c.ROOT/'tools/p09/tests'))
    import test_review_post_stop_frame as tests
    with patch.object(tests,'FIXTURES',(frame,body)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'CONTRACT12')
    return 12


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=prior.c.ROOT;require(prior.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{prior.DIR}/p210-post-stop-review-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);reader=None
    out=dict(schema_version='hwpx-agent.p09-post-stop-semantic-candidate-review/v1',state='FAILED_NOT_ACCEPTED',
        **prior.r.flags(),actual_product_body_executed=False,current_full_source_closing_executed=False)
    try:
        owner.admit();reader=owned.WeightedReader(root,owner.checkpoint_io);context.reader=reader
        with context.scope('metadata_read_parse'):
            for pin in (FRAME,BODY):require(reader.fresh_pin(pin['path'])==pin,'IMMUTABLE_FAILURE_RECEIPT_PIN')
            frame=reader.json(FRAME['path']);body=reader.json(BODY['path'])
        result=review(frame,body)
        with context.scope('contract_tests'):out['review_contract_tests_passed']=contracts(frame,body)
        with context.scope('metadata_hash'):
            helpers=[reader.fresh_pin(name) for name in (SELF,TEST)]
        with context.scope('final_fresh_hash'):reader.finish()
        out.update(state='PASS_POST_STOP_CANDIDATE_REVIEW_NOT_CURRENT_SOURCE_RUNTIME_OR_GATE',
            review=result,original_failed_frame_pin=FRAME,original_stopped_parent_pin=BODY,
            review_helper_pins=helpers,metadata_IO=dict(bound_inputs=len(reader.snapshots),
                final_fresh_hashes=reader.final_fresh_hashes,read_passes=reader.read_passes,bytes_read=reader.bytes_read))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt):
        out['error_code']='P210_POST_STOP_REVIEW_FAILED_REDACTED'
    finally:
        owner.stop.set();out['resource_watcher_cleanup_confirmed']=owner.thread.ident is None
        out['resource_stop_reason']=owner.reason
        if owner.reason or not out['resource_watcher_cleanup_confirmed']:out['state']='FAILED_NOT_ACCEPTED'
        out['metadata_observation']=observation.summary(owner)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','review_contract_tests_passed','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
