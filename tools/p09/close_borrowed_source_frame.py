"""P211: P208의 정상 끝난 본문은 다시 실행하지 않는 전체 current-source frame.

원 STOP receipt를 그대로 보존한다. 모든 원1473입력과 새 제어 소스를 두 번
실제 읽는다. 이 독립 source frame만으로 runtime/whole/Gate를 승격하지 않는다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import borrowed_locked_streams as borrowed
import review_post_stop_frame as review

p=review.prior;observation=review.observation
SELF='tools/p09/close_borrowed_source_frame.py'
TEST='tools/p09/tests/test_borrowed_source_frame_closing.py'
EXTRAS=(borrowed.SELF,borrowed.TEST,'tools/p09/probe_borrowed_locked_streams.py',review.SELF,review.TEST,SELF,TEST)
SCHEMA='hwpx-agent.p09-borrowed-current-source-frame/v1'
PASS='PASS_FULL_BORROWED_CURRENT_SOURCE_FRAME_NOT_RUNTIME_WHOLE_OR_GATE'


def require(ok,code):p.require(ok,'BORROWED_SOURCE_CLOSE_'+code)


def validate(doc,required):
    frame=doc['source_frame'];handles=frame['handles'];streams=handles['borrowed_byte_streams'];n=len(required)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and n==1480
        and doc['original_failed_frame_pin']==review.FRAME and doc['original_stopped_parent_pin']==review.BODY,
        'EXACT_SCOPE_AND_IMMUTABLE_ORIGINAL_FAILURE')
    require(doc['review']['semantic_body_capture_complete'] is True
        and doc['review']['runtime_accepted'] is False
        and doc['review']['same_product_body_reexecution_allowed'] is False,
        'NO_PRODUCT_BODY_REPEAT_OR_ACCEPTANCE')
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==n and frame['input_bytes']==sum(pin['bytes'] for pin in required.values())
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True,
        'REAL_FULL_FRAME_CLOSED')
    require(len(frame['actual_byte_boundaries'])==2
        and [row['role'] for row in frame['actual_byte_boundaries']]==['before','after']
        and all(p.v.pins(row['actual_byte_pins'])==required
            and row['reader_diagnostics']['read_passes']==n
            and row['reader_diagnostics']['bytes_read']==frame['input_bytes']
            and row['reader_diagnostics']['original_owned_read_operations_preserved'] is True
            and row['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            for row in frame['actual_byte_boundaries']), 'EXACT_TWO_FULL_BYTE_PASSES')
    require(handles['input_lock_handles_opened']==handles['input_lock_handles_closed']==n+306
        and handles['input_lock_handles_remaining']==0 and handles['input_lock_cleanup_confirmed'] is True
        and handles['byte_stream_identity_checks']==2*n
        and handles['active_reader_bindings']==handles['active_byte_streams']==0
        and handles['handle_close_failed_attempts']==0
        and handles['probe_handles_opened']==handles['probe_handles_closed']==handles['probe_handles_remaining']==0
        and handles['native_open_pacing']['maximum_opens_per_second']==32,
        'ALL_HELD_HANDLES_AND_ORIGINAL_STREAM_IDENTITY_CHECKS')
    require(streams['duplicate_handles_opened']==streams['duplicate_handles_closed']==streams['shared_offset_resets']==2*n
        and streams['duplicate_handles_remaining']==streams['duplicate_close_failed_attempts']==0
        and streams['active_borrow_binding'] is False and streams['byte_stream_pathname_reopens']==0
        and streams['original_pre_read_stream_identity_check_retained'] is True
        and streams['original_held_handles_closed_by_borrower'] is False,
        'ALL_DUPLICATES_CLOSED_WITHOUT_REOPEN_OR_SOURCE_CLOSE')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']=='OPEN' and all(doc[k] is False for k in
        ('runtime_acceptance_changed','actual_product_body_executed','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved','whole1470_current_fresh_qualified')),
        'SOURCE_FRAME_NOT_RUNTIME_WHOLE_GATE_OR_FREEZE_CAUSE')
    require(doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes'],
        'ORIGINAL_FAILURE_AND_NEW_HELPERS_FRESHLY_BOUND')


def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('P211_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P211_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P211_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_borrowed_source_frame_closing'))
    require(result.wasSuccessful() and result.testsRun==10 and not result.skipped,'CONTRACT10')
    return 10


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p211-borrowed-source-frame-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=frame=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        runtime_acceptance_changed=False,actual_product_body_executed=False,
        original_failed_frame_pin=review.FRAME,original_stopped_parent_pin=review.BODY)
    try:
        owner.admit();q=p.qualification.Reader(owner,context);out['closing_contract_tests_passed']=contracts()
        require(q.pin(review.FRAME['path'])==review.FRAME and q.pin(review.BODY['path'])==review.BODY,'IMMUTABLE_FAILURE_PINS')
        failed=q.json(review.FRAME['path']);body=q.json(review.BODY['path']);out['review']=review.review(failed,body)
        original=p.v.pins(failed['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        require(original[p.m.EXE['path']]==p.m.EXE,'ORIGINAL_EXACT_EXE_INPUT_RETAINED')
        extras={name:q.pin(name) for name in EXTRAS}
        require(not set(original)&set(extras),'SEPARATE_NEW_HELPERS_WITHOUT_ORIGINAL_SUBSTITUTION')
        required={**original,**extras};require(len(required)==1480,'ALL_ORIGINAL_PLUS_SEVEN_CONTROLLER_INPUTS')
        q.finish()
        held=borrowed.BorrowedInputLocks(root,owner.checkpoint_io)
        frame=p.frames.Frame(p.frames.Registry(),required,owner.checkpoint_io,held=held)
        context.reader=p.frames.Counters(q.reader,frame.readers)
        with context.scope('metadata_hash'):frame.acquire()
        def factory(checkpoint):
            return p.core.run.owned.OwnedReader(root,checkpoint,samples=owner,protected={p.m.EXE['path']})
        for phase in ('metadata_hash','final_fresh_hash'):
            with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
        # 원 STOP body의 정리 witness만 사용. stop/state/tests_passed는 수정하지 않는다.
        frame.commit(body)
        out.update(state=PASS,source_frame=frame.summary(),extra_controller_pins=list(extras.values()),
            preparation_IO=q.summary(),resource_stop_reason=None,resource_watcher_cleanup_confirmed=True)
        validate(out,required)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['state']='FAILED_NOT_ACCEPTED'
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED'
            out['source_frame']=frame.summary()
        p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['preparation_IO']=q.summary()
        out['metadata_observation']=observation.summary(owner)
        if out['state']==PASS:
            try:validate(out,required)
            except (ValueError,OSError,KeyError,TypeError):out['state']='FAILED_NOT_ACCEPTED'
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','closing_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
