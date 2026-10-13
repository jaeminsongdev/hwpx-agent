"""P258: 본문90 재실행 없이 원1545+새/문서helper6의 독립 두 전체 읽기.

수용된 P255/P257/원 failed bytes 불변. 조기90%yield를 새 frame에 연결하며
원 Native20/byte1·2MiB/600/identity/정리 유지. 별도 compound 전 runtime 아님.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import review_checkpoint_queue_stop as review
m=review.m
SELF='tools/p09/close_checkpoint_stop_source_frame.py'
TEST='tools/p09/tests/test_checkpoint_stop_source_frame.py'
EXTRAS=(review.SELF,review.TEST,review.docs.SELF,review.docs.TEST,SELF,TEST)
REVIEW_PIN=dict(path=m.p.DIR+'/p257-case090-stop-review-run01.v1.json',bytes=10377,
    sha256='73ab14f7f7a66a40ac2ad3e00531541e6b0207b6a286d1e8f5bfcb4acf2b1c4b')
SCHEMA='hwpx-agent.p09-checkpoint-stop-independent-source-frame/v1'
PASS='PASS_CASE090_INDEPENDENT_FULL_SOURCE_EARLY_CHECKPOINT_NOT_RUNTIME_OR_GATE'
N=1551


def require(ok,code):m.require(ok,'CHECKPOINT_SOURCE_'+code)


def budget(required):
    require(len(required)==N and required[m.p.m.EXE['path']]==m.p.m.EXE,'FIXED_FULL_SCOPE_AND_EXE')
    binary=m.p.m.EXE['bytes'];other=sum(p['bytes'] for p in required.values())-binary
    # 독립 source-only 경로. 예상은 보증이 아니며 실제600초 guard 그대로 적용.
    native=(3*N+306)/20;byte_seconds=2*binary/1048576+2*other/2097152
    total=native+byte_seconds+60+15+60
    require(total<600 and sum(required[n]['bytes'] for n in EXTRAS)<=1048576,'NOMINAL_FITS_UNCHANGED600')
    return dict(inputs=N,native20_reservation_seconds=native,two_byte_pass_nominal_seconds=byte_seconds,
        metadata_allowance_seconds=60,early_pressure_allowance_seconds=15,margin_seconds=60,
        nominal_combined_seconds=total,unchanged_actual_deadline_seconds=600,
        estimate_not_completion_guarantee=True,unbounded_pressure_may_still_STOP=True)


def validate(doc,required):
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and len(required)==N
        and doc['original_failed_root_pin']==review.ROOT_PIN and doc['original_stopped_parent_pin']==review.BODY_PIN
        and doc['original_zero_placeholder_pin']==review.ZERO_PIN and doc['stop_review_pin']==REVIEW_PIN,
        'LITERAL_FAILURE_AND_SCOPE')
    original=m.p.v.pins(doc['original_executed_source_pins']);extras=m.p.v.pins(doc['extra_controller_pins'])
    require(len(original)==1545 and sum(p['bytes'] for p in original.values())==119242806
        and set(extras)==set(EXTRAS) and not set(original)&set(extras)
        and required=={**original,**extras} and original.get(m.p.m.EXE['path'])==m.p.m.EXE,'ALL_ORIGINAL_PLUS_SIX')
    frame=doc['source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams'];total=sum(p['bytes'] for p in required.values())
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==N and frame['input_bytes']==total
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'FULL_LIVE_COMMITTED_FRAME_NOT_CACHE')
    boundaries=frame['actual_byte_boundaries'];require(len(boundaries)==2
        and [b['role'] for b in boundaries]==['before','after']
        and all(m.p.v.pins(b['actual_byte_pins'])==required
            and b['reader_diagnostics']['read_passes']==N and b['reader_diagnostics']['bytes_read']==total
            and b['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and b['reader_diagnostics']['original_owned_read_operations_preserved'] is True
            and b['reader_diagnostics']['extra_sampler_or_native_query_started'] is False for b in boundaries),
        'TWO_ACTUAL_COMPLETE_BYTE_READS')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+306
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['probe_handles_opened']==h['probe_handles_closed']==h['probe_handles_remaining']==0
        and h['byte_stream_identity_checks']==2*N and h['separate_pathname_reopens']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==305
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['file_write_or_delete_operation_executed'] is False,'ORIGINAL_NATIVE_LIMITS_AND_CLOSE')
    require(dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0
        and dup['original_pre_read_stream_identity_check_retained'] is True
        and dup['original_held_handles_closed_by_borrower'] is False,'SERIAL_DUPLICATES_IDENTITY_AND_CLEANUP')
    require(frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=N,directory_count=306),'POST_CLEANUP_HELD_IDENTITIES')
    pressure=h['native_open_backpressure'];require(all(pressure[k] is True for k in
        ('original_hard_resource_decisions_unmodified','original_IO_deadline_unmodified',
         'original_sampler_windows_reused','cleanup_not_guarded_by_pressure'))
        and pressure['original_read_checks_skipped'] is False,'ORIGINAL_NATIVE95_YIELD_RETAINED')
    early=doc['early_source_checkpoint'];require(early['early_source_warning_CPU_percent']==90
        and early['cool_distinct_samples']==2 and early['maximum_pause_windows']==8
        and all(early[k] is True for k in ('original_guard_called_before_pressure',
            'original_hard_CPU_RAM600_guards_preserved','existing_owner_samples_only'))
        and all(early[k] is False for k in ('new_sampler_or_thread_started','source_byte_reads_or_identity_checks_skipped',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established'))
        and doc['early_source_runtime_connection_verified'] is True
        and doc['early_source_native_and_byte_guard_connected'] is True,'EARLY_GUARD_CONNECTED_NOT_CAUSE')
    require(doc['review']['semantic_body_capture_complete'] is True
        and doc['review']['independent_full_source_closing_required'] is True
        and doc['review']['runtime_acceptance_changed'] is False
        and doc['review']['same_product_body_reexecution_allowed'] is False
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('runtime_acceptance_changed','actual_product_body_executed',
            'original_partial_post_source_hash_completed','full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved')),'SOURCE_ONLY_NO_PROMOTION')
    require(doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']==10
        and doc['preparation_IO']['maximum_scope_seconds']==600
        and doc['closing_contract_tests_passed']==14 and doc['nominal_scope_budget']==budget(required),
        'ALL_FRESH_METADATA_AND_ORIGINAL600')


def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_SOURCE_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_SOURCE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_SOURCE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_checkpoint_stop_source_frame'))
    require(result.wasSuccessful() and result.testsRun==14 and not result.skipped,'CONTRACT14')
    return 14


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p258-case090-source-frame-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY_NO_AUTO_RETRY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context)
    q=frame=early=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
        original_failed_root_pin=review.ROOT_PIN,original_stopped_parent_pin=review.BODY_PIN,
        original_zero_placeholder_pin=review.ZERO_PIN,stop_review_pin=REVIEW_PIN,
        runtime_acceptance_changed=False,actual_product_body_executed=False,
        original_partial_post_source_hash_completed=False,early_source_runtime_connection_verified=False,
        early_source_native_and_byte_guard_connected=False,independent_post_source_only=True)
    try:
        owner.admit();q=m.Reader(owner,context)
        root=m.review.bound_json(q,review.ROOT_PIN);body=m.review.bound_json(q,review.BODY_PIN)
        checked=review.review(root,body);prior=m.review.bound_json(q,REVIEW_PIN)
        require(prior['schema_version']==review.SCHEMA and prior['state']==review.PASS
            and prior['review']==checked and prior['resource_stop_reason'] is None
            and prior['resource_watcher_cleanup_confirmed'] is True
            and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==15
            and prior['stop_and_early_source_contract_tests_passed']==32 and prior['original_peak_contract_tests_passed']==8,
            'SEALED_FRESH_STOP_REVIEW')
        require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'ZERO_PLACEHOLDER_PRESERVED')
        extras={name:q.pin(name) for name in EXTRAS};sealed=m.p.v.pins(prior['bound_input_pins'])
        require(all(extras[n]==sealed[n] for n in EXTRAS[:4]),'UNCHANGED_REVIEW_AND_DOC_HELPERS')
        original=m.p.v.pins(body['source_freeze']);require(len(original)==1545
            and sum(p['bytes'] for p in original.values())==119242806 and not set(original)&set(extras),
            'FULL_ORIGINAL_AND_NEW_SIX')
        required={**original,**extras};out.update(nominal_scope_budget=budget(required),
            original_executed_source_pins=list(original.values()),extra_controller_pins=list(extras.values()),
            closing_contract_tests_passed=contracts(),review=checked)
        q.finish()
        early=review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
        held=m.lower.InputLocks(m.p.c.ROOT,early,owner)
        require(held.checkpoint is early and held.api.pacer.rate==20
            and held.open_pressure.resources is owner,'EXACT_EARLY_AND_ORIGINAL_NATIVE_OWNER')
        frame=m.p.frames.Frame(m.p.frames.Registry(),required,early,held=held)
        context.reader=m.p.frames.Counters(q.reader,frame.readers)
        out.update(early_source_native_and_byte_guard_connected=True)
        with context.scope('metadata_hash'):frame.acquire()
        def factory(checkpoint):
            return m.p.core.run.owned.OwnedReader(m.p.c.ROOT,checkpoint,samples=owner,protected={m.p.m.EXE['path']})
        for phase in ('metadata_hash','final_fresh_hash'):
            with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
        # 90의 실제 과거 Job 정리 witness만 사용. 새 Job/본문은 만들지 않는다.
        out.update(source_frame=frame.commit(body),early_source_runtime_connection_verified=True)
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='CHECKPOINT_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='CHECKPOINT_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        if q is not None:q.close_entry();out.update(preparation_IO=q.summary(),preparation_bound_input_pins=list(q.reader.snapshots.values()))
        m.g.complete(out,owner,proposed,lambda doc:validate(doc,required))
        out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'closing_contract_tests_passed','early_source_runtime_connection_verified')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
