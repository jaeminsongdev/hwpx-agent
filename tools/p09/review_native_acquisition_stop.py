"""P242: P241 case080 Native 획득 CPU STOP의 미실행·정리 검토. 수용/재시도 아님."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_uncreated_borrower_runtime as r
import review_packed_cpu_peak_r2 as peak
SELF='tools/p09/review_native_acquisition_stop.py'
TEST='tools/p09/tests/test_native_acquisition_stop.py'
ROOT_PIN=dict(path=r.p.DIR+'/p241-case-080-run002.v1.json',bytes=277167,
    sha256='08745fbcf7738da69dbc4bbc9418ceddf811ea0f1a4a1999869ca6711aec6891')
LIGHT_PIN=dict(path=r.p.DIR+'/p241-light-run001.v1.json',bytes=48474,
    sha256='85096d817bcf17d10da8281aacd0fa9d63628e3bebac6647e823d4ec06f0e68d')
PEAK_SUPPORT=dict(path=r.p.DIR+'/p224-cpu-peak-review-run01.v1.json',bytes=8727,
    sha256='659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254')
PASS='PASS_NATIVE_ACQUISITION_STOP_REVIEW_NOT_RUNTIME_OR_AUTOMATIC_RETRY'


def require(ok,code):r.require(ok,'ACQUIRE_STOP_'+code)


def review(doc):
    require(doc['schema_version']==r.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True,'ORIGINAL_FAILURE_AND_CLEANUP')
    require(doc['selected_test_index']==80 and doc['prior_runtime_plan']['next_runtime_index']==80
        and doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']==73
        and doc['current_queue_runtime_contract_tests_passed']==156
        and doc['post_stop_runtime_contract_tests_passed']==18
        and doc['uncreated_borrower_connection_contract_tests_passed']==8,'EXACT_NEXT80_AFTER182_CONTRACTS')
    require(doc['frame_acquisition_requested'] is True and doc['frame_acquisition_complete'] is False
        and doc['product_worker_invocation_requested'] is False and doc['uncreated_borrower_adapter_selected'] is False
        and doc['accepted_exact_product_body_count']==0 and doc['actual_product_child_executed'] is False
        and all(doc.get(key) is None for key in ('case_receipt_path','case_receipt_pin',
            'terminal_parent_failure_sidecar_pin','original_parent_STOP_captured_not_accepted')),
        'NO_ORIGINAL_PARENT_WORKER_BODY_OR_SIDECAR_INVOKED')
    frame=doc['terminal_source_frame'];own=frame['handles']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1525 and frame['input_bytes']==119022055
        and frame['actual_byte_boundaries']==[] and own['borrowed_byte_streams'] is None,
        'PARTIAL_ACQUIRE_NOT_SOURCE_READ_OR_BORROWER')
    require(own['input_lock_handles_opened']==own['input_lock_handles_closed']==854
        and own['input_lock_cleanup_confirmed'] is True
        and all(type(own[k]) is int and own[k]==0 for k in ('input_lock_handles_remaining',
            'active_reader_bindings','active_byte_streams','handle_close_failed_attempts','byte_stream_identity_checks')),
        'ALL854_LOCKS_CLOSED_NO_BYTE_READ')
    require(own['maximum_lock_seconds']==600 and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['native_open_pacing']['open_reservations']==854,'UNCHANGED_NATIVE_LIMITS')
    pressure=own['native_open_backpressure']
    require(pressure['warning_entries']==1 and pressure['completed_pause_windows']==3
        and pressure['requested_pause_seconds']==1.5 and pressure['cleanup_not_guarded_by_pressure'] is True
        and all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified',
            'original_IO_deadline_unmodified','original_sampler_windows_reused'))
        and pressure['original_read_checks_skipped'] is False,'PRESSURE_PRESENT_NOT_SWALLOWED_STOP')
    require(doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']==218,
        'COMPLETED_METADATA_NOT_ACTUAL_PRODUCT_SOURCE_CLOSING')
    summary=peak.summarize(doc['metadata_observation']['samples'])
    require(summary['maximum_consecutive98_samples']==4 and summary['own_CPU_max_at_warning']==0
        and summary['job_CPU_max_at_warning'] is None and summary['job_CPU_samples_at_warning']==0,
        'ORIGINAL_4_HOT_WINDOWS_JOB_UNOBSERVED_NOT_ZERO')
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved')),'NO_FAILURE_OR_GATE_PROMOTION')
    return dict(selected_test_index=80,original_failure_preserved=True,product_body_unexecuted=True,
        stopped_before_original_parent_call=True,all_partial_native_handles_closed=True,
        absent_Job_or_borrower_not_invented_as_measured_zero=True,
        runtime_acceptance_changed=False,automatic_retry_allowed=False,
        optimization_and_reviewed_new_generation_required_before_next_attempt=True,
        runtime_previously_accepted=73,next_unexecuted_index=80,
        CPU_cause_or_PC_freeze_resolution_established=False)


def contracts(doc):
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_native_acquisition_stop as tests
    with patch.object(tests,'FIXTURE',doc),patch('subprocess.Popen',side_effect=AssertionError('NO_STOP_REVIEW_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_STOP_REVIEW_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_STOP_REVIEW_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(checked.wasSuccessful() and checked.testsRun==20 and not checked.skipped,'CONTRACT20')
    return 20


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p242-native-acquisition-stop-review-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-native-acquisition-stop-review/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_or_full_source_executed=False,automatic_retry_allowed=False,
        original_failed_root_pin=ROOT_PIN,original_preflight_pin=LIGHT_PIN)
    try:
        owner.admit();q=r.Reader(owner,context);doc=r.review.bound_json(q,ROOT_PIN)
        light=r.review.bound_json(q,LIGHT_PIN)
        require(light['state']==r.LIGHT and light['selected_test_index']==80
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True,'SEALED182_PREFLIGHT')
        body_path=r.p.c.ROOT/f'{r.p.DIR}/cases/p241-case-080-run002.json'
        require(not body_path.exists() and not list((r.p.c.ROOT/r.p.DIR/'cases').glob('p241-*080*.json')),
            'ORIGINAL_BODY_AND_SIDECAR_NOT_CREATED')
        helpers=r.p.v.pins(doc['extra_frame_controller_pins'])
        for name in (r.SELF,r.TEST):require(q.pin(name)==helpers[name],'FAILED_EXECUTED_HELPERS_UNCHANGED')
        out['review']=review(doc);out['stop_review_contract_tests_passed']=contracts(doc)
        support=r.review.bound_json(q,PEAK_SUPPORT);pins=r.p.v.pins(support['bound_input_pins'])
        require(support['state']==peak.PASS and support['resource_stop_reason'] is None,'SEALED_PEAK_SUPPORT')
        for name in (peak.SELF,peak.TEST):require(q.pin(name)==pins[name],'PEAK_HELPERS_UNCHANGED')
        out['peak_summary_contract_tests_passed']=peak.contracts()
        out['metadata_peak_review']=peak.summarize(doc['metadata_observation']['samples'])
        for name in (SELF,TEST):q.pin(name)
        q.finish();proposed=dict(state=PASS,original_uncreated_body_and_sidecar_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,lambda row:require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==9
            and row['stop_review_contract_tests_passed']==20 and row['peak_summary_contract_tests_passed']==8,'ALL9_FRESH28'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','stop_review_contract_tests_passed',
            'peak_summary_contract_tests_passed','review')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
