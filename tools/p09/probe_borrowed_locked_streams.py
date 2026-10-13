"""P209 작은 원본 입력의 실제 Windows 복제/두 byte 읽기만 확인.

EXE/제품 body/전체 입력은 실행하지 않는다. 기존 CPU/RAM 보호와 1/2MiB
byte pacing, 32/s stream pacing을 그대로 사용하며 새 thread/child는 없다.
"""
import argparse
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import borrowed_locked_streams as borrowed
import observe_shared_metadata_recheck as observation
import owned_source_read_pressure as owned

SELF='tools/p09/probe_borrowed_locked_streams.py'
PROBE='tools/p09/tests/fixtures/p206-input-lock-probe.txt'
SOURCES=(borrowed.SELF,borrowed.TEST,SELF,PROBE)


def contracts():
    sys.path.insert(0,str(borrowed.locks.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_borrowed_locked_streams')
    with patch('subprocess.Popen',side_effect=AssertionError('P209_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P209_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P209_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    borrowed.require(result.wasSuccessful() and result.testsRun==24 and not result.skipped,'CONTRACT24')
    return 24


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=borrowed.locks.ROOT
    borrowed.require(root==borrowed.locks.Path.cwd().resolve() and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'implementation/p09/evidence/locked-r07/p209-borrowed-stream-probe-run{args.run:02}.v1.json'
    borrowed.require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);held=reader=None
    started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-borrowed-stream-small-native-probe/v1',state='FAILED_NOT_ACCEPTED',
        actual_product_body_executed=False,full_runtime_source_frame_qualified=False,
        PC_freeze_resolved=False,input_scope_reduced=False,P09_gate='OPEN')
    try:
        owner.admit();out['borrow_contract_tests_passed']=contracts()
        reader=owned.WeightedReader(root,owner.checkpoint_io);context.reader=reader
        with context.scope('metadata_hash'):pins={name:reader.fresh_pin(name) for name in SOURCES}
        borrowed.require(sum(pin['bytes'] for pin in pins.values())<=65536,'SMALL_TOTAL_BYTE_BOUND')
        held=borrowed.BorrowedInputLocks(root,owner.checkpoint_io)
        with context.scope('metadata_hash'):held.acquire(pins)
        boundaries=[]
        for phase in ('metadata_hash','final_fresh_hash'):
            with context.scope(phase),held.reader_sources(reader):
                before=(reader.read_passes,reader.bytes_read)
                actual={name:reader.fresh_pin(name) for name in pins}
                borrowed.require(actual==pins,'ACTUAL_TWO_BYTE_HASHES')
                boundaries.append(dict(pins=list(actual.values()),read_passes=reader.read_passes-before[0],
                    bytes_read=reader.bytes_read-before[1]))
        held.verify_two_byte_passes(pins);held.verify_held_identities()
        borrowed.require(held.close(),'ALL_NATIVE_AND_DUPLICATE_HANDLES_CLOSED')
        handles=held.summary();streams=handles['borrowed_byte_streams']
        borrowed.require(streams['duplicate_handles_opened']==streams['duplicate_handles_closed']==2*len(pins)
            and streams['shared_offset_resets']==2*len(pins) and streams['duplicate_handles_remaining']==0
            and streams['duplicate_close_failed_attempts']==0 and handles['input_lock_cleanup_confirmed'],
            'EXACT_NATIVE_STREAM_CLEANUP')
        out.update(state='PASS_SMALL_NATIVE_BORROWED_STREAMS_NOT_FULL_RUNTIME_PRODUCT_OR_GATE',
            source_pins=list(pins.values()),actual_byte_boundaries=boundaries,
            read_rates_by_kind=dict(binary=owned.BINARY_RATE,other=owned.OTHER_RATE),
            no_source_contents_or_raw_handles_saved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt):
        out['error_code']='P209_SMALL_NATIVE_PROBE_FAILED_REDACTED'
    finally:
        if held is not None:
            try:
                if not held.close():out['state']='FAILED_NOT_ACCEPTED'
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED'
            out['input_locks']=held.summary()
        owner.stop.set()
        out['resource_watcher_cleanup_confirmed']=owner.thread.ident is None
        out['resource_stop_reason']=owner.reason
        if owner.reason or not out['resource_watcher_cleanup_confirmed']:out['state']='FAILED_NOT_ACCEPTED'
        out['metadata_observation']=observation.summary(owner)
        out['wall_seconds']=round(time.monotonic()-started,4)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','borrow_contract_tests_passed','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
