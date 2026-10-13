"""P235: P230 case078 본문을 재실행하지 않는 독립 전체 source 마감.

원 1512 입력과 새 검토/마감 코드 4개를 실제 두 번 읽는다. 입력/기준/속도는
줄이지 않는다. 원 STOP/부분 hash를 고치거나 runtime 수용으로 승격하지 않는다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import review_current_queue_stop as review
import native_open_backpressure as native

r=review.r
SELF='tools/p09/close_current_stop_source_frame.py'
TEST='tools/p09/tests/test_current_stop_source_frame.py'
EXTRAS=(review.SELF,review.TEST,SELF,TEST)
REVIEW_PIN=dict(path=r.p.DIR+'/p234-current-stop-review-run01.v1.json',bytes=15243,
    sha256='64bf2c461028d753d9f55e562f215f670c3237f5fbd042e78c7ec53313c9c30e')
SCHEMA='hwpx-agent.p09-current-stop-independent-source-frame/v1'
PASS='PASS_CURRENT_STOP_FULL_SOURCE_FRAME_NOT_RUNTIME_WHOLE_OR_GATE'


def require(ok,code):r.require(ok,'CURRENT_SOURCE_CLOSE_'+code)


def validate(doc,required):
    n=1516;frame=doc['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and len(required)==n
        and doc['original_failed_root_pin']==review.ROOT_PIN and doc['original_stopped_parent_pin']==review.BODY_PIN
        and doc['original_zero_placeholder_pin']==review.ZERO_PIN and doc['stop_review_pin']==REVIEW_PIN,
        'EXACT_LITERAL_PROOFS_AND_FULL_SCOPE')
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==n and frame['input_bytes']==sum(p['bytes'] for p in required.values())
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'LIVE_FULL_FRAME_COMMITTED_NOT_CACHE')
    boundaries=frame['actual_byte_boundaries']
    require(len(boundaries)==2 and [row['role'] for row in boundaries]==['before','after']
        and all(r.p.v.pins(row['actual_byte_pins'])==required
            and row['reader_diagnostics']['read_passes']==n
            and row['reader_diagnostics']['bytes_read']==frame['input_bytes']
            and row['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and row['reader_diagnostics']['original_owned_read_operations_preserved'] is True
            and row['reader_diagnostics']['extra_sampler_or_native_query_started'] is False
            for row in boundaries),'TWO_COMPLETE_ACTUAL_BYTE_READS')
    require(own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['input_lock_handles_remaining']==own['active_reader_bindings']==own['active_byte_streams']==0
        and own['input_lock_cleanup_confirmed'] is True and own['handle_close_failed_attempts']==0
        and own['probe_handles_opened']==own['probe_handles_closed']==own['probe_handles_remaining']==0
        and own['byte_stream_identity_checks']==2*n and own['separate_pathname_reopens']==0
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['file_write_or_delete_operation_executed'] is False,
        'ALL_ORIGINAL_LOCK_GUARDS_AND_CLEANUP')
    require(dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0
        and dup['original_pre_read_stream_identity_check_retained'] is True
        and dup['original_held_handles_closed_by_borrower'] is False,'ALL_BORROWED_STREAMS_CLOSED')
    require(frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=n,directory_count=306),'HELD_IDENTITIES_AFTER_OLD_JOB_CLEANUP')
    pressure=own['native_open_backpressure']
    require(all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified',
        'original_IO_deadline_unmodified','original_sampler_windows_reused','cleanup_not_guarded_by_pressure'))
        and pressure['original_read_checks_skipped'] is False,'PRESSURE_GUARDS_RETAINED')
    require(doc['review']['source_closing_still_required'] is True
        and doc['review']['semantic_body_capture_complete'] is True
        and doc['review']['runtime_accepted'] is False and doc['review']['same_product_body_reexecution_allowed'] is False
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('runtime_acceptance_changed','actual_product_body_executed',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved',
            'original_partial_post_source_hash_completed')),'INDEPENDENT_SOURCE_ONLY_NOT_ORIGINAL_PASS')
    require(doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']==8
        and doc['preparation_IO']['maximum_scope_seconds']==600,'ALL_METADATA_FRESH_NO_DEADLINE_EXTENSION')


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_SOURCE_CLOSE_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_SOURCE_CLOSE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_SOURCE_CLOSE_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_current_stop_source_frame'))
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    return 12


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p235-current-stop-source-frame-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_RECEIPT_NO_AUTO_RETRY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=frame=candidate=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**r.p.r.flags(),
        runtime_acceptance_changed=False,actual_product_body_executed=False,
        original_partial_post_source_hash_completed=False,
        original_failed_root_pin=review.ROOT_PIN,original_stopped_parent_pin=review.BODY_PIN,
        original_zero_placeholder_pin=review.ZERO_PIN,stop_review_pin=REVIEW_PIN,
        metadata_JSON_binding_uses_single_initial_read=True)
    try:
        owner.admit();q=r.Reader(owner,context)
        root=review.bound_json(q,review.ROOT_PIN);body=review.bound_json(q,review.BODY_PIN)
        checked=review.review(root,body);prior=review.bound_json(q,REVIEW_PIN)
        require(prior['state']==review.PASS and prior['review']==checked
            and prior['stop_review_contract_tests_passed']==20 and prior['peak_summary_contract_tests_passed']==8
            and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
            and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==8,
            'COMPLETE_FRESH_STOP_REVIEW')
        require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'ZERO_PLACEHOLDER_PRESERVED')
        sealed=r.p.v.pins(prior['bound_input_pins'])
        extras={name:q.pin(name) for name in EXTRAS}
        require(all(extras[name]==sealed[name] for name in (review.SELF,review.TEST)),'REVIEW_HELPERS_UNCHANGED')
        original=r.p.v.pins(body['source_freeze'])
        require(len(original)==1512 and not set(original)&set(extras),'ALL_ORIGINAL_PLUS_NEW_FOUR')
        required={**original,**extras};out['closing_contract_tests_passed']=contracts()
        q.finish()
        held=native.PressureInputLocks(r.p.c.ROOT,owner.checkpoint_io,owner)
        frame=r.p.frames.Frame(r.p.frames.Registry(),required,owner.checkpoint_io,held=held)
        context.reader=r.p.frames.Counters(q.reader,frame.readers)
        with context.scope('metadata_hash'):frame.acquire()
        def factory(checkpoint):
            return r.p.core.run.owned.OwnedReader(r.p.c.ROOT,checkpoint,samples=owner,protected={r.p.m.EXE['path']})
        for phase in ('metadata_hash','final_fresh_hash'):
            with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
        # 이전 Job의 실제 정리 witness만 사용. 새 Job/본문 실행을 주장하지 않는다.
        out.update(source_frame=frame.commit(body),review=checked,extra_controller_pins=list(extras.values()))
        candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='CURRENT_SOURCE_CLOSE_HANDLE_CLEANUP_FAILED';candidate=None
            except (ValueError,OSError):out['error_code']='CURRENT_SOURCE_CLOSE_HANDLE_CLEANUP_FAILED';candidate=None
            out['source_frame']=frame.summary()
        if q is not None:out.update(preparation_IO=q.summary(),preparation_bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda doc:validate(doc,required))
        out['metadata_observation']=r.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','closing_contract_tests_passed','error_code',
            'resource_stop_reason','resource_watcher_cleanup_confirmed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
