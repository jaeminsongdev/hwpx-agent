"""P263: 원91 본체를 재실행하지 않고 전체1555+새4 독립 source/관측 연결 마감.

원 FAILED bytes를 PASS로 바꾸지 않는다. 별도 frame 두 읽기와 동일성·정리가
완료된 새 증거만 만든다. runtime 수용은 별도 compound 검증 전까지 변경 없음.
"""
import argparse
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import review_monotonic_metadata_observation as review
m=review.m;p=review.p;g=review.g;old=review.old
SELF='tools/p09/close_observation_failure_source_frame.py'
TEST='tools/p09/tests/test_observation_failure_source_frame.py'
EXTRAS=(review.SELF,review.TEST,SELF,TEST)
REVIEW_PIN=dict(path=p.DIR+'/p262-case091-observation-review-run01.v1.json',bytes=22383,
    sha256='782f871474195561a4b6cd794fde8bff11e67565d44ec75f39980157ff7d826d')
SCHEMA='hwpx-agent.p09-observation-failure-independent-source-frame/v1'
PASS='PASS_CASE091_INDEPENDENT_FULL_SOURCE_MONOTONIC_READER_NOT_RUNTIME_OR_GATE'
N=1559
COUNT=16


def require(ok,code):old.require(ok,'OBSERVATION_SOURCE_'+code)


def budget(required):
    require(len(required)==N and required[p.m.EXE['path']]==p.m.EXE,'ALL_INPUTS_FIXED_EXE')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    native=(3*N+306)/20;byte=2*binary/1048576+2*other/2097152;total=native+byte+60+15+60
    require(total<600 and sum(required[n]['bytes'] for n in EXTRAS)<=1048576,'FITS_ORIGINAL600_ESTIMATE')
    return dict(inputs=N,native_reservation_rate=20,native_nominal_seconds=native,two_byte_nominal_seconds=byte,
        metadata_allowance_seconds=60,early_pressure_allowance_seconds=15,margin_seconds=60,
        nominal_combined_seconds=total,original_deadline_seconds=600,estimate_not_completion_guarantee=True)


def frame_contract(frame,required):
    require(len(required)==N,'ALL1559_INPUTS');h=frame['handles'];dup=h['borrowed_byte_streams']
    total=sum(x['bytes'] for x in required.values())
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==N and frame['input_bytes']==total
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'LIVE_COMMITTED_FRAME_NOT_SERIALIZED_HANDLES')
    rows=frame['actual_byte_boundaries'];require(len(rows)==2 and [r['role'] for r in rows]==['before','after'],'TWO_ROLES')
    for row in rows:
        d=row['reader_diagnostics'];require(p.v.pins(row['actual_byte_pins'])==required
            and d['read_passes']==N and d['bytes_read']==total
            and d['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and d['original_owned_read_operations_preserved'] is True
            and d['extra_sampler_or_native_query_started'] is False,'FULL_REAL_TWO_BYTE_READS')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+306
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['probe_handles_opened']==h['probe_handles_closed']==h['probe_handles_remaining']==h['probe_handle_close_failed_attempts']==0
        and h['byte_stream_identity_checks']==2*N and h['separate_pathname_reopens']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==305
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+306
        and h['file_write_or_delete_operation_executed'] is False,'EXACT_NATIVE_NO_RESIDUE')
    require(dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0
        and dup['original_pre_read_stream_identity_check_retained'] is True
        and dup['original_held_handles_closed_by_borrower'] is False,'SERIAL_DUPLICATE_OFFSET_IDENTITY_CLOSE')
    require(frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=N,directory_count=306),'POST_CLEANUP_HELD_IDENTITIES')
    m.r.h.h.pressure_contract(h['native_open_backpressure']);m.lower_contract(h)


def validate(doc,required):
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc['original_failed_root_pin']==review.ROOT_PIN
        and doc['original_body_pin']==review.BODY_PIN and doc['observation_review_pin']==REVIEW_PIN,'EXACT91_PROOF')
    original=p.v.pins(doc['original_executed_source_pins']);extras=p.v.pins(doc['extra_controller_pins'])
    require(len(original)==1555 and sum(x['bytes'] for x in original.values())==119338307
        and set(extras)==set(EXTRAS) and not set(original)&set(extras) and required=={**original,**extras},'FULL_ORIGINAL_PLUS_FOUR')
    frame_contract(doc['source_frame'],required);old.early_contract(doc['early_source_checkpoint'])
    require(doc['review']['independently_qualified_source_and_compound_required'] is True
        and doc['review']['runtime_acceptance_changed'] is False and doc['review']['same_product_body_reexecution_allowed'] is False
        and doc['monotonic_binding_policy']==review.policy() and doc['aggregate_reader_connection_verified'] is True
        and doc['early_source_native_and_byte_guard_connected'] is True,'CONNECTED_GUARDS_NOT_PARTIAL_CLOSING')
    for key,count in (('preparation_IO',18),('post_source_IO',1)):
        row=doc[key];m.metadata_contract(row);require(row['finished'] is True
            and row['bound_inputs']==row['final_fresh_hashes']==count and row['maximum_scope_seconds']==600,'ALL_METADATA_FRESH')
    require(doc['preparation_IO']['read_passes']+doc['post_source_IO']['read_passes']<=m.META_READ_LIMIT
        and doc['closing_contract_tests_passed']==COUNT and doc['retained_observation_contract_tests_passed']==review.COUNT
        and doc['nominal_scope_budget']==budget(required),'ALL52_CONTRACTS_SHARED720')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('runtime_acceptance_changed','actual_product_body_executed',
            'original_failed_frame_promoted','whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'SOURCE_ONLY_NOT_RUNTIME_GATE_OR_CAUSE')


def contracts(root,body,required):
    retained=review.contracts(root,body);sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_observation_failure_source_frame as tests
    with patch.object(tests,'FIXTURES',(root,required)),patch('subprocess.Popen',side_effect=AssertionError('NO_SOURCE_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_SOURCE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_SOURCE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'CONTRACT16_NO_SKIP')
    return retained


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p263-case091-source-frame-run{args.run:02}.v1.json';require(not destination.exists(),'FRESH_ONLY_NO_RETRY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=post=frame=early=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),original_failed_root_pin=review.ROOT_PIN,
        original_body_pin=review.BODY_PIN,observation_review_pin=REVIEW_PIN,runtime_acceptance_changed=False,
        actual_product_body_executed=False,original_failed_frame_promoted=False,aggregate_reader_connection_verified=False,
        early_source_native_and_byte_guard_connected=False,monotonic_binding_policy=review.policy())
    try:
        owner.admit();q=m.Reader(owner,context)
        root=m.review.bound_json(q,review.ROOT_PIN);body=m.review.bound_json(q,review.BODY_PIN);checked=review.review(root,body)
        previous=m.review.bound_json(q,REVIEW_PIN)
        require(previous['schema_version']==review.SCHEMA and previous['state']==review.PASS
            and previous['review']==checked and previous['resource_stop_reason'] is None
            and previous['resource_watcher_cleanup_confirmed'] is True and previous['observation_contract_tests_passed']==36
            and previous['IO']['finished'] is True and previous['IO']['bound_inputs']==previous['IO']['final_fresh_hashes']==15
            and previous['small_real_IO']['finished'] is True
            and previous['small_real_IO']['bound_inputs']==previous['small_real_IO']['final_fresh_hashes']==3,
            'UNCHANGED_QUALIFIED_SMALL_OBSERVATION_REPAIR')
        light=m.review.bound_json(q,review.LIGHT_PIN);old.closed_attempt(light)
        sealed=p.v.pins(previous['bound_input_pins']);original=p.v.pins(body['source_freeze'])
        added={n:q.pin(n) for n in EXTRAS}
        for n in EXTRAS[:2]:require(added[n]==sealed[n],'FROZEN_REVIEW_SOURCES')
        for n in old.NEW:require(q.pin(n)==original[n]==sealed[n],'ALL_EXECUTED_CONTROLLERS_UNCHANGED')
        require(not set(original)&set(added),'ONLY_FOUR_NEW_INPUTS');required={**original,**added}
        out.update(original_executed_source_pins=list(original.values()),extra_controller_pins=list(added.values()),
            review=checked,nominal_scope_budget=budget(required),closing_contract_tests_passed=COUNT,
            retained_observation_contract_tests_passed=contracts(root,body,required));q.finish()
        early=old.review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=m.lower.InputLocks(p.c.ROOT,early,owner)
        require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_EARLY_OWNER')
        frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers)
        context.reader=counter;out['early_source_native_and_byte_guard_connected']=True
        with context.scope('metadata_hash'):frame.acquire()
        def factory(checkpoint):return p.core.run.owned.OwnedReader(p.c.ROOT,checkpoint,samples=owner,protected={p.m.EXE['path']})
        for phase in ('metadata_hash','final_fresh_hash'):
            with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
        post=review.construct(m.Reader,owner,context,counter)
        after=m.review.bound_json(post,review.BODY_PIN);require(after==body,'IDENTICAL_ORIGINAL_BODY_AFTER_LIVE_SOURCE')
        p.validate_parent(after,review.NAME,root['binding'],original);post.finish()
        require(context.reader is counter and counter.metadata==[post.reader],'CONTINUOUS_MONOTONIC_AGGREGATE')
        out.update(source_frame=frame.commit(after),aggregate_reader_connection_verified=True,
            aggregate_read_bytes=counter.bytes_read,aggregate_read_passes=counter.read_passes);proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='OBSERVATION_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='OBSERVATION_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader,key in ((q,'preparation_IO'),(post,'post_source_IO')):
            if reader is not None:reader.close_entry();out[key]=reader.summary()
        if q is not None:out['preparation_bound_input_pins']=list(q.reader.snapshots.values())
        g.complete(out,owner,proposed,lambda doc:validate(doc,required));out['metadata_observation']=g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'closing_contract_tests_passed','retained_observation_contract_tests_passed','aggregate_reader_connection_verified')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
