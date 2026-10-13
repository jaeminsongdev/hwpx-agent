"""P246: 원10+metadata15 계약, 작은 실제11입력/fresh 검증. 전체 runtime 연결 아님."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import metadata_read_entry_pacing as pacing
import review_metadata_read_stop as reviewed
r=reviewed.r
SELF='tools/p09/qualify_metadata_read_entry_pacing.py'
REVIEW=dict(path=r.p.DIR+'/p245-metadata-read-stop-review-run02.v1.json',bytes=6138,
    sha256='93cc3f95e2dfaae7407b7495f46de37e3d56103d96a34e797ec97818bbe687dd')
PASS='PASS_METADATA_ENTRY32_CONTRACT25_SMALL_REAL_READS_NOT_FULL_RUNTIME_OR_GATE'


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
        ('test_native_open_backpressure','test_metadata_read_entry_pacing'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_ENTRY_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_ENTRY_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_ENTRY_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    r.require(result.wasSuccessful() and result.testsRun==25 and not result.skipped,'METADATA_ENTRY25')
    return 25


def validate(doc):
    own=doc['metadata_entry_pacing'];io_row=doc['IO']
    r.require(io_row['finished'] is True and io_row['bound_inputs']==io_row['final_fresh_hashes']==11
        and io_row['maximum_scope_seconds']==600 and io_row['chunk_bytes']==65536
        and io_row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
        and own['completed_original_read_calls']==own['reservations']==own['entry_calls']==io_row['read_passes']
        and own['failed_calls']==0 and own['maximum_metadata_read_entries_per_second']==32
        and own['binding_active'] is False and doc['metadata_entry_contract_tests_passed']==25,
        'METADATA_ENTRY_ALL11_FRESH_ORIGINAL_CALLS')
    r.require(all(own[k] is True for k in ('no_idle_burst','original_reader_and_bytes_and_fresh_checks_preserved',
        'original_CPU_RAM_IO_and_parse_budget_preserved','original_pressure_checkpoint_reused','cleanup_not_guarded_or_paced'))
        and all(own[k] is False for k in ('extra_sampler_or_thread_started','original_reads_skipped',
            'cached_pins_or_parsed_JSON_substituted','measured_CPU_or_PC_freeze_improvement_claimed')),'UNCHANGED_GUARDS_NO_CLAIM')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'ENTRY_CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p246-metadata-entry32-support-run{args.run:02}.v1.json'
    r.require(not path.exists(),'ENTRY_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=binding=proposed=None
    out=dict(schema_version='hwpx-agent.p09-metadata-read-entry-pacing-support/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_or_full_source_executed=False,actual_CPU_stress_executed=False,
        actual_runtime_connection_qualified=False,reviewed_metadata_stop_pin=reviewed.ROOT_PIN,
        reviewed_metadata_receipt_pin=REVIEW)
    try:
        owner.admit();q=r.Reader(owner,context)
        binding=pacing.Binding(q.reader)
        with binding:
            failed=r.review.bound_json(q,reviewed.ROOT_PIN);checked=r.review.bound_json(q,REVIEW)
            r.require(checked['state']==reviewed.PASS and checked['review']==reviewed.review(failed)
                and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True
                and checked['metadata_stop_contract_tests_passed']==12,'ENTRY_REVIEWED_STOP_NOT_RUNTIME')
            pins=r.p.v.pins(checked['bound_input_pins'])
            for name in (reviewed.SELF,reviewed.TEST):r.require(q.pin(name)==pins[name],'ENTRY_REVIEW_SOURCE_UNCHANGED')
            native=r.review.bound_json(q,r.LOWER_SUPPORT);r.lower_support.validate(native)
            r.require(native['state']==r.lower_support.PASS and native['resource_stop_reason'] is None
                and native['resource_watcher_cleanup_confirmed'] is True,'ENTRY_NATIVE_SUPPORT_NOT_RUNTIME')
            pins=r.p.v.pins(native['bound_input_pins'])
            for name in (r.lower.SELF,r.lower.TEST,r.lower_support.SELF):
                r.require(q.pin(name)==pins[name],'ENTRY_LOWER_SOURCES_UNCHANGED')
            out['combined_future_budget']=pacing.estimate_budget(native['rate_budget'])
            out['metadata_entry_contract_tests_passed']=contracts()
            for name in (pacing.SELF,pacing.TEST,SELF):q.pin(name)
            q.finish()
        out['metadata_entry_pacing']=binding.summary();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if binding is not None:out['metadata_entry_pacing']=binding.summary()
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,validate);out['metadata_observation']=r.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','metadata_entry_contract_tests_passed','error_code',
            'resource_stop_reason','combined_future_budget','metadata_entry_pacing')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
