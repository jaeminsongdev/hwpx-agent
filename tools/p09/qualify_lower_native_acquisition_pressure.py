"""P243 16계약 + 실제 소규모 Native20 probe. 제품/전체 runtime/CPU stress 아님."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import lower_native_acquisition_pressure as lower
import review_native_acquisition_stop as review
r=review.r
SELF='tools/p09/qualify_lower_native_acquisition_pressure.py'
REVIEW=dict(path=r.p.DIR+'/p242-native-acquisition-stop-review-run01.v1.json',bytes=6512,
    sha256='e936567327e23f8d36d084967f8dc4a8d9ed30f9816cf83d3ef35a9d313c1454')
PASS='PASS_LOWER_NATIVE20_CONTRACT16_AND_SMALL_REAL_PROBE_NOT_PRODUCT_OR_FULL_RUNTIME'


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
        ('test_native_open_backpressure','test_lower_native_acquisition_pressure'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_LOWER_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_LOWER_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_LOWER_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    r.require(result.wasSuccessful() and result.testsRun==16 and not result.skipped,'LOWER_NATIVE16')
    return 16


def validate(doc):
    own=doc['small_native_probe'];dup=own['borrowed_byte_streams']
    r.require(own['input_lock_handles_opened']==own['input_lock_handles_closed']==7
        and own['input_lock_handles_remaining']==own['active_reader_bindings']==own['active_byte_streams']==0
        and own['input_lock_cleanup_confirmed'] is True and own['handle_close_failed_attempts']==0
        and own['byte_stream_identity_checks']==6 and own['maximum_lock_seconds']==600
        and own['native_open_pacing']['maximum_opens_per_second']==20
        and own['native_open_pacing']['open_reservations']==13
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==6
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0,
        'LOWER_SMALL_REAL_NATIVE_CLEANUP')
    r.require(len(doc['small_actual_read_passes'])==2
        and all(row['read_passes']==3 and row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and row['original_owned_read_operations_preserved'] is True for row in doc['small_actual_read_passes']),
        'LOWER_TWO_REAL_SMALL_BYTE_PASSES')
    r.require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==8
        and doc['lower_native_contract_tests_passed']==16,'LOWER_FRESH8_CONTRACT16')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True,type=int);args=ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'LOWER_CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p243-lower-native20-support-run{args.run:02}.v1.json'
    r.require(not path.exists(),'LOWER_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=held=proposed=None
    out=dict(schema_version='hwpx-agent.p09-lower-native-acquisition-pressure-support/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_executed=False,actual_full_runtime_or_CPU_stress_executed=False,
        actual_runtime_connection_qualified=False,reviewed_stop_pin=review.ROOT_PIN,review_receipt_pin=REVIEW)
    try:
        owner.admit();q=r.Reader(owner,context)
        root=r.review.bound_json(q,review.ROOT_PIN);checked=r.review.bound_json(q,REVIEW)
        r.require(checked['state']==review.PASS and checked['review']==review.review(root)
            and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True,
            'LOWER_REVIEWED_UNEXECUTED_STOP')
        light=r.review.bound_json(q,review.LIGHT_PIN)
        for name in (review.SELF,review.TEST):q.pin(name)
        small={name:q.pin(name) for name in (lower.SELF,lower.TEST,SELF)}
        # 원 STOP frame 집계와 고정 EXE 크기만 사용한다. 원 입력 pin을 합성하지 않는다.
        frame=root['terminal_source_frame'];binary=r.p.m.EXE['bytes']
        out['rate_budget']=lower.estimate(frame['input_count'],binary,frame['input_bytes']-binary,
            light['metadata_observation']['completed_sample_count']*0.5)
        out['lower_native_contract_tests_passed']=contracts();q.finish()
        held=lower.InputLocks(r.p.c.ROOT,owner.checkpoint_io,owner)
        with context.scope('metadata_hash'):held.acquire(small)
        readers=[];passes=[]
        for phase in ('metadata_hash','final_fresh_hash'):
            reader=r.p.core.run.owned.OwnedReader(r.p.c.ROOT,owner.checkpoint_io,samples=owner)
            readers.append(reader);context.reader=r.p.frames.Counters(q.reader,readers)
            with context.scope(phase),held.reader_sources(reader):
                for name,pin in small.items():r.require(reader.fresh_pin(name)==pin,'LOWER_REAL_SMALL_SOURCE_BYTES')
            passes.append(reader.diagnostics())
        held.verify_two_byte_passes(small);out['small_actual_read_passes']=passes
        r.require(held.close(),'LOWER_SMALL_ALL_HANDLES_CLOSED');proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if held is not None:
            if not held.close():out['error_code']='LOWER_SMALL_NATIVE_CLEANUP_FAILED';proposed=None
            out['small_native_probe']=held.summary()
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,validate)
        out['metadata_observation']=r.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','lower_native_contract_tests_passed','error_code','resource_stop_reason','rate_budget')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
