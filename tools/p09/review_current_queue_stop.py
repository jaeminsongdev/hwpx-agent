"""P234: case078 원 CPU STOP 보존, 완료 본문/부분 source 읽기의 독립 검토.

본문 재실행과 runtime 승격은 금지한다. JSON 첫 읽기가 이미 length/SHA를
계산하므로 별도 pin 선행 읽기를 중복하지 않는다. 마지막 fresh 읽기는 유지.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_current_queue_runtime as r
import review_packed_cpu_peak_r2 as peak

SELF='tools/p09/review_current_queue_stop.py'
TEST='tools/p09/tests/test_current_queue_stop_review.py'
ROOT_PIN=dict(path=r.p.DIR+'/p230-case-078-run018.v1.json',bytes=885680,
    sha256='0f426067907084932489b7bb00425cca017851b726ca2f466dba4777d456ebf1')
BODY_PIN=dict(path=r.p.DIR+'/cases/p230-failure-078-run018.json',bytes=600156,
    sha256='66127715459940855848724d8e918add4f3bad4fa3227a73e804cee5702904db')
ZERO_PIN=dict(path=r.p.DIR+'/cases/p230-case-078-run018.json',bytes=0,
    sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
SUPPORT=dict(path=r.p.DIR+'/p224-cpu-peak-review-run01.v1.json',bytes=8727,
    sha256='659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254')
NAME='actual_import::formula_policy_issuer::wrong_approval_media_role_and_artifact_alias_cannot_use_policy_or_other_domain_as_signature'
STOP='STOP_SUSTAINED_SYSTEM_CPU'
PASS='PASS_CURRENT_QUEUE_STOP_REVIEW_PENDING_SOURCE_NOT_RUNTIME_OR_GATE'


def require(ok,code):r.require(ok,'CURRENT_STOP_'+code)


def bound_json(q,pin):
    # 같은 첫 byte 읽기에서 parse와 SHA/length 검사를 모두 수행한다.
    doc=q.json(pin['path'])
    require(q.reader.snapshots[pin['path']]==pin,'IMMUTABLE_LITERAL_BYTES')
    return doc


def review(root,body):
    require(root['schema_version']==r.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']=='ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED'
        and root['original_parent_STOP_captured_not_accepted'] is True
        and root['accepted_exact_product_body_count']==0
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True,
        'OUTER_FAILURE_NOT_PASS_OR_PARENT_REASON')
    require(root['terminal_parent_failure_sidecar_pin']==BODY_PIN
        and root['case_receipt_path']==ZERO_PIN['path']
        and root['original_failure_body_placeholder_preserved'] is True
        and root.get('terminal_failure_write_error') is None,'EXACT_PRESERVED_FAILURE_LINK')
    require(root['selected_test_index']==78 and root['selected_test_name']==NAME
        and root['prior_runtime_plan']['runtime_source_qualified_individual_cases']==71
        and root['prior_runtime_plan']['next_runtime_index']==78
        and root['current_queue_runtime_contract_tests_passed']==156,'EXACT_PENDING_CASE_AND_PRIOR71')
    require(body['schema_version']==r.p.SCHEMA and body['state']=='STOPPED_NOT_ACCEPTED'
        and body['resource_stop_reason']==body['stop_reason']==STOP
        and body['operation_phase']=='final_source_freeze','ORIGINAL_PARENT_CPU_STOP')
    require(body['binding']==root['binding'] and body['selected_test_names']==body['passed_test_names']==[NAME]
        and body['test_arguments']==r.p.v.arguments(NAME)
        and body['task']==body['minimal_worker_task']=='p204-r07-case-078-tests'
        and body['minimal_owned_worker_path']==r.p.m.SELF,'EXACT_ORIGINAL_BODY_CONNECTION')
    require(body['policy']==r.p.c.POLICY and type(body['maximum_seconds']) is int
        and body['maximum_seconds']==1200,'UNCHANGED_POLICY_AND_DEADLINE')
    require(type(body['exit_code']) is int and body['exit_code']==0
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body.get('tests_passed') is None
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False),
        'STRICT_COMPLETED_BODY_NOT_OVERALL_TESTS_PASS')
    capture=body['capture_diagnostics']
    require(capture['error_code'] is None and capture['buffered_bytes']==capture['received_bytes']
        and capture['buffered_bytes']==dict(stdout=256,stderr=0)
        and capture['per_stream_limit_bytes']==32768 and capture['raw_log_content_included'] is False,
        'NO_TRUNCATED_OR_PRIVATE_LOG_CAPTURE')
    require(all(body[k] is True for k in ('cleanup_confirmed','owned_tree_empty','worker_created','job_assigned',
        'writer_authorized','actual_job_membership_checked','owned_limits_verified',
        'minimal_worker_source_only_import_connected','actual_product_child_executed'))
        and type(body['job_final']['active_processes']) is int and body['job_final']['active_processes']==0
        and body['job_final']['owned_processes']==[] and body['owned_limits_readback']['verified'] is True,
        'ORIGINAL_JOB_LIMITS_GO_AND_CLEANUP')
    frame=root['terminal_source_frame'];boundaries=frame['actual_byte_boundaries']
    inputs=r.p.v.pins(body['source_freeze']);readers=body['owned_source_reader_passes']
    require(len(inputs)==frame['input_count']==1512 and frame['input_bytes']==118919360
        and sum(pin['bytes'] for pin in inputs.values())==frame['input_bytes']
        and inputs.get(r.p.m.EXE['path'])==r.p.m.EXE
        and len(boundaries)==1 and boundaries[0]['role']=='before'
        and r.p.v.pins(boundaries[0]['actual_byte_pins'])==inputs,'EXACT_FULL_BEFORE_SOURCE')
    require(len(readers)==2 and readers[0]==boundaries[0]['reader_diagnostics']
        and readers[0]['read_passes']==1512 and readers[0]['bytes_read']==118919360
        and readers[1]['read_passes']==1362 and readers[1]['bytes_read']==110635044
        and readers[1]['interrupted_protected_EXE_path']==r.p.m.EXE['path']
        and all(row['original_owned_read_operations_preserved'] is True
            and row['extra_sampler_or_native_query_started'] is False
            and row['read_rates_by_kind']==dict(binary=1048576,other=2097152) for row in readers),
        'INCOMPLETE_AFTER_HASH_NOT_COMPLETE')
    pressure=readers[1]['near_saturation_read_backpressure']
    require(pressure['warning_entries']==1 and pressure['completed_pause_windows']==3
        and pressure['requested_pause_seconds']==1.5
        and all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified',
            'original_IO_deadline_unmodified','original_sampler_windows_reused'))
        and pressure['original_read_checks_skipped'] is False,'EXISTING_READ_PRESSURE_NOT_MISSING')
    handles=frame['handles'];dup=handles['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and handles['input_lock_handles_opened']==handles['input_lock_handles_closed']==1818
        and handles['input_lock_handles_remaining']==handles['active_reader_bindings']==handles['active_byte_streams']==0
        and handles['input_lock_cleanup_confirmed'] is True and handles['handle_close_failed_attempts']==0
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2874
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0,
        'ALL_NATIVE_AND_DUPLICATE_HANDLES_CLOSED')
    require(all(row[k] is False for row in (root,body) for k in
        ('full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and all(row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN' for row in (root,body)),
        'NO_GATE_OR_FREEZE_PROMOTION')
    return dict(selected_test_index=78,selected_test_name=NAME,semantic_body_capture_complete=True,
        original_overall_failure_preserved=True,parent_resource_stop_reason=STOP,
        outer_resource_stop_reason=None,missing_overall_tests_passed_not_invented=True,
        existing_read_backpressure_connected_and_observed=True,source_closing_still_required=True,
        same_product_body_reexecution_allowed=False,runtime_accepted=False,
        runtime_previously_accepted=71,new_pending_source_closing_candidates=1,
        complete_original_post_source_hash_claimed=False,CPU_cause_or_PC_freeze_resolution_established=False)


def contracts(root,body):
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_current_queue_stop_review as tests
    with patch.object(tests,'FIXTURES',(root,body)),patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(checked.wasSuccessful() and checked.testsRun==20 and not checked.skipped,'CONTRACT20')
    return 20


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True,type=int);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p234-current-stop-review-run{args.run:02}.v1.json'
    require(not path.exists(),'NEW_RECEIPT_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-current-queue-stop-review/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_executed=False,current_full_source_closing_executed=False,
        original_failed_root_pin=ROOT_PIN,original_stopped_parent_pin=BODY_PIN,original_zero_placeholder_pin=ZERO_PIN,
        redundant_initial_metadata_pin_reads_removed=True,original_final_fresh_hashes_retained=True)
    try:
        owner.admit();q=r.Reader(owner,context)
        root=bound_json(q,ROOT_PIN);body=bound_json(q,BODY_PIN)
        require(q.pin(ZERO_PIN['path'])==ZERO_PIN,'ORIGINAL_ZERO_PLACEHOLDER')
        support=bound_json(q,SUPPORT)
        require(support['state']==peak.PASS and support['resource_stop_reason'] is None
            and support['resource_watcher_cleanup_confirmed'] is True
            and support['IO']['finished'] is True and support['IO']['bound_inputs']==support['IO']['final_fresh_hashes']==6,
            'SEALED_PEAK_SUPPORT')
        for name in (peak.SELF,peak.TEST):
            pins=[pin for pin in support['bound_input_pins'] if pin['path']==name]
            require(len(pins)==1 and q.pin(name)==pins[0],'UNCHANGED_PEAK_REVIEWER')
        for name in (SELF,TEST):q.pin(name)
        out['review']=review(root,body)
        out['stop_review_contract_tests_passed']=contracts(root,body)
        out['peak_summary_contract_tests_passed']=peak.contracts()
        out['metadata_peak_review']=peak.summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review']=peak.summarize(body['samples'])
        q.finish();candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==8
            and doc['stop_review_contract_tests_passed']==20 and doc['peak_summary_contract_tests_passed']==8,
            'ALL_FRESH_AND28_CONTRACTS'))
        out['metadata_observation']=r.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'stop_review_contract_tests_passed','peak_summary_contract_tests_passed','review',
            'metadata_peak_review','original_parent_peak_review')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
