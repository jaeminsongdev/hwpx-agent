"""P245: P244 metadata STOP를 미실행으로 검토. 실패/unknown/Gate를 승격하지 않는다."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_lower_native_runtime as r
import review_packed_cpu_peak_r2 as peak
SELF='tools/p09/review_metadata_read_stop.py'
TEST='tools/p09/tests/test_metadata_read_stop.py'
ROOT_PIN=dict(path=r.p.DIR+'/p244-admission-run002.v1.json',bytes=68645,
    sha256='b0b1d3714afa9b47dff09361e51c7fbfdede7aeb9b4160a619bd11efb0b86319')
LIGHT_PIN=dict(path=r.p.DIR+'/p244-light-run001.v1.json',bytes=47554,
    sha256='7799f70bbd6641f187ead3c5901ee3173ee0d46ea498fb78aabc3940d4876233')
PASS='PASS_METADATA_READ_STOP_REVIEW_NOT_RUNTIME_OR_AUTOMATIC_RETRY'


def require(ok,code):r.require(ok,'METADATA_STOP_'+code)


def review(doc):
    require(doc['schema_version']==r.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True,'ORIGINAL_STOP_CLEANUP')
    require(all(doc.get(k) is False for k in ('frame_acquisition_requested','frame_acquisition_complete',
        'product_worker_invocation_requested','actual_product_child_executed','lower_native20_adapter_selected',
        'uncreated_borrower_adapter_selected'))
        and all(doc.get(k) is None for k in ('selected_test_index','selected_test_name','prior_runtime_plan',
            'terminal_source_frame','case_receipt_pin','case_receipt_path','terminal_parent_failure_sidecar_pin'))
        and doc['accepted_exact_product_body_count']==0,'NO_NATIVE_OR_BODY_OR_SOURCE_QUALIFICATION')
    row=doc['preparation_IO']
    require(row['finished'] is False and row['read_passes']==125 and row['bound_inputs']==72
        and row['final_fresh_hashes']==0 and row['bytes_read']==row['pacer_bytes_read']==69547076
        and row['bytes_read_by_kind']==dict(binary=0,other=69547076)
        and row['maximum_scope_seconds']==600 and row['chunk_bytes']==65536
        and row['parse_budget_bytes']==16777216
        and row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
        and row['all_original_read_operations_preserved'] is True,'PARTIAL_METADATA_NOT_FRESH_PASS')
    pressure=row['near_saturation_read_backpressure']
    require(pressure['warning_entries']==1 and pressure['completed_pause_windows']==3
        and pressure['requested_pause_seconds']==1.5
        and all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified',
            'original_IO_deadline_unmodified','original_sampler_windows_reused'))
        and pressure['original_read_checks_skipped'] is False,'ORIGINAL_PRESSURE_STOP_NOT_SWALLOWED')
    summary=peak.summarize(doc['metadata_observation']['samples'])
    require(summary['sample_count']==71 and summary['maximum_consecutive98_samples']==4
        and summary['warning_phase_counts']==dict(metadata_read_parse=4)
        and summary['own_CPU_max_at_warning']==0.378788 and summary['job_CPU_max_at_warning'] is None
        and summary['job_CPU_samples_at_warning']==0,'EXACT_METADATA_PEAK_JOB_UNKNOWN_NOT_ZERO')
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and doc['PC_freeze_resolved'] is False and doc['product_complete'] is False,'NO_GATE_OR_CAUSE_PROMOTION')
    return dict(original_failure_preserved=True,stopped_during_metadata_before_selection=True,
        Native20_not_exercised=True,product_body_unexecuted=True,runtime_previously_accepted=73,
        next_unexecuted_index=80,automatic_retry_allowed=False,
        additional_metadata_entry_density_optimization_required=True,
        CPU_cause_or_PC_freeze_resolution_established=False,missing_Job_not_measured_zero=True)


def contracts(doc):
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_metadata_read_stop as tests
    with patch.object(tests,'FIXTURE',doc),patch('subprocess.Popen',side_effect=AssertionError('NO_META_REVIEW_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_META_REVIEW_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_META_REVIEW_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    return 12


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p245-metadata-read-stop-review-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-metadata-read-stop-review/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_or_full_source_executed=False,automatic_retry_allowed=False,
        original_failed_root_pin=ROOT_PIN,original_preflight_pin=LIGHT_PIN)
    try:
        owner.admit();q=r.Reader(owner,context);failed=r.review.bound_json(q,ROOT_PIN)
        light=r.review.bound_json(q,LIGHT_PIN)
        require(light['state']==r.LIGHT and light['selected_test_index']==80
            and light['current_queue_runtime_contract_tests_passed']==156
            and light['post_stop_runtime_contract_tests_passed']==18
            and light['uncreated_borrower_connection_contract_tests_passed']==8
            and light['lower_native_runtime_contract_tests_passed']==8
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True
            and light['preparation_IO']['finished'] is True
            and light['preparation_IO']['bound_inputs']==light['preparation_IO']['final_fresh_hashes']==228,
            'EXACT190_PREFLIGHT_NOT_PRODUCT')
        pins=r.p.v.pins(light['extra_frame_controller_pins'])
        for name in (r.SELF,r.TEST):require(q.pin(name)==pins[name],'EXECUTED_P244_SOURCE_UNCHANGED')
        require(not list((r.p.c.ROOT/r.p.DIR).glob('p244-case-*-run*.v1.json'))
            and not list((r.p.c.ROOT/r.p.DIR/'cases').glob('p244-*080*.json')),'NO_CASE_ROOT_BODY_OR_SIDECAR')
        out['review']=review(failed);out['metadata_stop_contract_tests_passed']=contracts(failed)
        out['metadata_peak_review']=peak.summarize(failed['metadata_observation']['samples'])
        out['peak_summary_contract_tests_passed']=peak.contracts()
        for name in (SELF,TEST,peak.SELF,peak.TEST):q.pin(name)
        q.finish();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,lambda row:require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==8
            and row['metadata_stop_contract_tests_passed']==12 and row['peak_summary_contract_tests_passed']==8,'FRESH8_CONTRACT20'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','metadata_stop_contract_tests_passed','review')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
