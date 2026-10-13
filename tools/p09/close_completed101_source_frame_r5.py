"""P299 R5: 완료101 본체 재실행 없이 원1599+review/보존prototype/closing/compound26의 독립 두 전체 읽기.
원 FAILED/STOPPED/zero/partial474 불변. 획득14/byte20·1/2MiB·600·identity·정리 유지.
"""
import argparse
import io
import json
import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch
import review_completed101_stop as review
import review_completed101_source_stop_r2 as source_stop
m=review.m
SELF='tools/p09/close_completed101_source_frame_r5.py'
TEST='tools/p09/tests/test_completed101_source_frame_r5.py'
OLD_CODE=[{"path":"tools/p09/close_completed101_source_frame.py","bytes":15129,"sha256":"f447b4b186e7e5925b5cbfbf2823fdb42ab6b5b648f9c9dec8076ec0662a4e46"},{"path":"tools/p09/tests/test_completed101_source_frame.py","bytes":8637,"sha256":"fd4707951bef8c2d635448ff89578fcfeb9cc019dad5d146cae20d1089464b77"},{"path":"tools/p09/accept_completed101_compound.py","bytes":10665,"sha256":"f06ca339b9ebe87cd961e102ee8eab9a07d1a7964164cc413924ee8a44a63fa3"},{"path":"tools/p09/tests/test_completed101_compound.py","bytes":3855,"sha256":"65fbf8a81cd3c0454018536540c28c0c6c66b8934b4436f8d9cbb400432eb0cc"},{"path":"tools/p09/close_completed101_source_frame_r2.py","bytes":17877,"sha256":"ec506450782799770aa0658fbd1536013c33863ea350a8c756b0aeb872e2caab"},{"path":"tools/p09/tests/test_completed101_source_frame_r2.py","bytes":8980,"sha256":"0bf6dd6790d473fc149a4f4a1b4c8187b2165277e837cdfd7a6bef657e02e729"},{"path":"tools/p09/accept_completed101_compound_r2.py","bytes":10689,"sha256":"87c839c6adc565790349763ed0e067e0d7198217278cd1bbcd03a04e5ff6c58b"},{"path":"tools/p09/tests/test_completed101_compound_r2.py","bytes":3858,"sha256":"6eab9b3b82e94f77c325abdb13abbe3a367d1f911114634cac36c21e13d49196"},{"path":"tools/p09/close_completed101_source_frame_r3.py","bytes":20211,"sha256":"887548629156bed419845d2136466b8983d87bb8670c1bc33f2e4a1d2289a21e"},{"path":"tools/p09/tests/test_completed101_source_frame_r3.py","bytes":9089,"sha256":"844f864afaabb79c7fa257736cba8c0744d5073f0d8a3a2514ba7e750e723f1d"},{"path":"tools/p09/accept_completed101_compound_r3.py","bytes":10689,"sha256":"e790edf464c612ce98956664db342d5c5ac252473024ce0d74be2832f06f802e"},{"path":"tools/p09/tests/test_completed101_compound_r3.py","bytes":3858,"sha256":"01e17b8ecd9b4d76a3be1b7eb45c369d4a1b12223a4fc30cf5aa58d00e08e247"}]
OLD_CODE += [{"path":"tools/p09/close_completed101_source_frame_r4.py","bytes":22565,"sha256":"ce7de74d7eb4e7ded75a124790b7a34e9edd709c622fe973673fc891a0643c91"},{"path":"tools/p09/tests/test_completed101_source_frame_r4.py","bytes":9198,"sha256":"e7925e84d80b31cc5266d4a952de46d4179ac54d9e2303c4fc3567216b37e29d"},{"path":"tools/p09/accept_completed101_compound_r4.py","bytes":10689,"sha256":"9c71c03f29d81b30fc7beb34e6d3a23404966193989aeaac9b8a219e344f86c4"},{"path":"tools/p09/tests/test_completed101_compound_r4.py","bytes":3858,"sha256":"93317f9b4259efda539bcb5cf9c82ae6847fbcfeef1be0008b6ba3957f033849"},{"path":"tools/p09/review_completed101_source_stop.py","bytes":8250,"sha256":"23438e624fe82c65013e2d103a88c9cdf6c20d81027cbe17c3918d78a829b084"},{"path":"tools/p09/tests/test_completed101_source_stop.py","bytes":2068,"sha256":"544311acea2b0180accc4ac078e94ed642de50a6405ba1f7d1ca37a36d412036"},{"path":"tools/p09/review_completed101_source_stop_r2.py","bytes":9770,"sha256":"5e48452ddfdf8d0a1906a26d87ffc64ef1fd49f50ba4ccc14332346cdb622321"},{"path":"tools/p09/tests/test_completed101_source_stop_r2.py","bytes":2071,"sha256":"bdc23a408b1c8f0091944d082f2add0216f188863b74d1c66bdef168351321d2"}]
EXTRAS=(review.SELF,review.TEST,*[x['path'] for x in OLD_CODE],SELF,TEST,
    'tools/p09/accept_completed101_compound_r5.py','tools/p09/tests/test_completed101_compound_r5.py')
OLD_PREPARATION_FAILURE={"path":"implementation/p09/evidence/locked-r07/p295-case101-source-light-run01.v1.json","bytes":11656,"sha256":"bd1c2137aafae1553bdb59a171c20bf9bd75f6adbc52cb646e93ebbc509983f3"}
R2_PREPARATION_FAILURE={"path":"implementation/p09/evidence/locked-r07/p295-r2-case101-source-light-run01.v1.json","bytes":12661,"sha256":"17cf32eeb6baea4d7255b9f535f80ab3d9c72d55955d9573219e814ca73cfb5a"}
R3_PREPARATION_FAILURE={"path":"implementation/p09/evidence/locked-r07/p295-r3-case101-source-light-run01.v1.json","bytes":13798,"sha256":"2daf8e60f0d364a9d84f8eb595687ee1a7955c92ead9d07ae0ec90b9fa6fa482"}

REVIEW_PIN=dict(path=m.p.DIR+'/p293-case101-completed-body-stop-review-run01.v1.json',bytes=3910,
    sha256='06a8c808e8ddf47e3f53115e1d103715bb9824ab4b02c8a8698b6368f47a0d41')
SOURCE_STOP_REVIEW_PIN=dict(path=m.p.DIR+'/p297-r2-case101-source-stop-review-run01.v1.json',bytes=10159,
    sha256='24b41cd89ab3f06f6ddab0e793c6c7dedb8c355c229ef2d1c76b804f3ad5f368')
SCHEMA='hwpx-agent.p09-completed101-independent-source-frame-r5/v1'
PASS='PASS_COMPLETED101_INDEPENDENT_FULL_SOURCE_R5_NOT_RUNTIME_OR_GATE'
LIGHT='PASS_COMPLETED101_SOURCE_PREPARATION_R5_NOT_NATIVE_RUNTIME_OR_GATE'
N=1625
DIRECTORIES=308
COUNT=29

def require(ok,code):m.require(ok,'COMPLETED101_SOURCE_'+code)

def budget(required):
    require(len(required)==N and required[m.p.m.EXE['path']]==m.p.m.EXE
        and all(n in required for n in EXTRAS),'FIXED_FULL_SCOPE_AND_EXE')
    binary=m.p.m.EXE['bytes'];other=sum(p['bytes'] for p in required.values())-binary
    native=(N+DIRECTORIES)/14+2*N/20
    byte_seconds=2*binary/1048576+2*other/2097152
    total=native+byte_seconds+60+15+60
    require(total<600 and sum(required[n]['bytes'] for n in EXTRAS)<=1048576,'NOMINAL_UNCHANGED600')
    return dict(inputs=N,ancestor_directories=DIRECTORIES,acquisition_rate=14,byte_native_rate=20,
        native_reservation_seconds=native,two_byte_pass_nominal_seconds=byte_seconds,
        metadata_allowance_seconds=60,early_pressure_allowance_seconds=15,margin_seconds=60,
        nominal_combined_seconds=total,unchanged_actual_deadline_seconds=600,
        estimate_not_completion_guarantee=True,unbounded_pressure_may_still_STOP=True)

def reviewed_preparation_failure(doc):
    require(doc['schema_version']=='hwpx-agent.p09-completed101-independent-source-frame/v1'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_COMPLETED101_SOURCE_SYNTHETIC_SOURCE26'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='contract_tests'
        and doc['early_source_native_and_byte_guard_connected'] is False
        and 'source_frame' not in doc and doc.get('closing_contract_tests_passed') is None,
        'ORIGINAL_FAKE_ORACLE_KEY_FAILURE_NOT_NATIVE_OR_CPU_STOP')
    row=doc['preparation_IO'];pins=m.p.v.pins(doc['preparation_bound_input_pins'])
    require(row['read_passes']==row['bound_inputs']==11 and row['final_fresh_hashes']==0
        and row['bytes_read']==1597881 and row['finished'] is False
        and all(pins.get(p['path'])==p for p in OLD_CODE[:4]),'ORIGINAL_PARTIAL_METADATA_AND_FOUR_CODE_PINS')
    return dict(original_preparation_failure_preserved=True,failed_receipt_accepted=False,
        wrong_test_flag_corrected_not_runtime_guard_relaxed=True,Native_or_product_reexecuted=False)

def reviewed_r2_constant_failure(doc):
    require(doc['schema_version']=='hwpx-agent.p09-completed101-independent-source-frame-r2/v1'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_COMPLETED101_SOURCE_FULL_ORIGINAL_AND_TEN'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='metadata'
        and doc['early_source_native_and_byte_guard_connected'] is False and 'source_frame' not in doc,
        'R2_WRONG_BYTE_CONSTANT_BEFORE_NATIVE_NOT_ACCEPTED')
    row=doc['preparation_IO'];pins=m.p.v.pins(doc['preparation_bound_input_pins'])
    require(row['read_passes']==row['bound_inputs']==16 and row['final_fresh_hashes']==0
        and row['bytes_read']==1650941 and row['finished'] is False
        and all(pins.get(p['path'])==p for p in OLD_CODE[4:8]),'R2_PARTIAL_METADATA_AND_CODE_PINS')
    return dict(original_r2_failure_preserved=True,accepted=False,wrong_byte_constant_corrected=True,Native_executed=False)

def reviewed_r3_comparison_failure(doc):
    require(doc['schema_version']=='hwpx-agent.p09-completed101-independent-source-frame-r3/v1'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_COMPLETED101_SOURCE_R2_WRONG_BYTE_CONSTANT_BEFORE_NATIVE_NOT_ACCEPTED'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='metadata'
        and doc['early_source_native_and_byte_guard_connected'] is False and 'source_frame' not in doc,
        'R3_WRONG_FAILED_ERROR_LITERAL_BEFORE_NATIVE_NOT_ACCEPTED')
    row=doc['preparation_IO'];pins=m.p.v.pins(doc['preparation_bound_input_pins'])
    require(row['read_passes']==row['bound_inputs']==21 and row['final_fresh_hashes']==0
        and row['bytes_read']==1707449 and row['finished'] is False
        and all(pins.get(p['path'])==p for p in OLD_CODE[8:12]),'R3_PARTIAL_METADATA_AND_CODE_PINS')
    return dict(original_r3_failure_preserved=True,accepted=False,wrong_failure_comparison_corrected=True,Native_executed=False)

def prepared(doc,required):
    require(doc['original_independent_source_stop_pin']==source_stop.PIN and doc['qualified_source_stop_review_pin']==SOURCE_STOP_REVIEW_PIN
        and doc['reviewed_source_acquire_STOP_preserved_not_accepted'] is True,'REVIEWED_R4_SOURCE_STOP_NOT_ACCEPTED')
    original=m.p.v.pins(doc['original_executed_source_pins']);extras=m.p.v.pins(doc['extra_controller_pins'])
    require(doc['schema_version']==SCHEMA and doc['original_failed_root_pin']==review.ROOT
        and doc['original_stopped_parent_pin']==review.BODY and doc['original_zero_placeholder_pin']==review.ZERO
        and doc['stop_review_pin']==REVIEW_PIN and doc['original_preparation_failure_pin']==OLD_PREPARATION_FAILURE
        and doc['reviewed_prior_preparation_failure_preserved_not_accepted'] is True
        and doc['r2_preparation_failure_pin']==R2_PREPARATION_FAILURE
        and doc['reviewed_r2_failure_preserved_not_accepted'] is True
        and doc['r3_preparation_failure_pin']==R3_PREPARATION_FAILURE
        and doc['reviewed_r3_failure_preserved_not_accepted'] is True,'LITERAL_FAILURE_AND_SCOPE')
    require(len(original)==1599 and sum(x['bytes'] for x in original.values())==119993724
        and set(extras)==set(EXTRAS) and not set(original)&set(extras) and required=={**original,**extras}
        and original.get(m.p.m.EXE['path'])==m.p.m.EXE
        and all(extras.get(p['path'])==p for p in OLD_CODE),'ALL_ORIGINAL1599_PLUS_EIGHTEEN')
    require(doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']==36
        and doc['preparation_IO']['maximum_scope_seconds']==600
        and doc['closing_contract_tests_passed']==COUNT and doc['nominal_scope_budget']==budget(required),
        'ALL_TWENTY_SIX_FRESH_ORIGINAL600')
    require(doc['review']['semantic_body_capture_complete'] is True
        and doc['review']['independent_full_source_closing_required'] is True
        and doc['review']['runtime_acceptance_changed'] is False
        and doc['review']['same_product_body_reexecution_allowed'] is False
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('runtime_acceptance_changed','actual_product_body_executed',
            'actual_product_child_executed','original_partial_post_source_hash_completed','whole1470_current_fresh_qualified',
            'historical67_current_fresh_qualified','full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved')),'SOURCE_ONLY_NO_PROMOTION')

def validate(doc,required):
    prepared(doc,required)
    require(doc['state']==PASS and len(required)==N,'FULL_SOURCE_NOT_PREPARATION')
    frame=doc['source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams'];total=sum(x['bytes'] for x in required.values())
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==N and frame['input_bytes']==total
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'FULL_LIVE_COMMITTED_NOT_CACHE')
    boundaries=frame['actual_byte_boundaries']
    require(len(boundaries)==2 and [b['role'] for b in boundaries]==['before','after']
        and all(m.p.v.pins(b['actual_byte_pins'])==required and b['reader_diagnostics']['read_passes']==N
            and b['reader_diagnostics']['bytes_read']==total
            and b['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and b['reader_diagnostics']['original_owned_read_operations_preserved'] is True
            and b['reader_diagnostics']['extra_sampler_or_native_query_started'] is False for b in boundaries),
        'TWO_COMPLETE_ACTUAL_BYTE_BOUNDARIES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['probe_handles_opened']==h['probe_handles_closed']==h['probe_handles_remaining']==0
        and h['byte_stream_identity_checks']==2*N and h['separate_pathname_reopens']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and h['file_write_or_delete_operation_executed'] is False,'ALL_NATIVE_LIMITS_AND_CLOSE')
    require(dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0
        and dup['original_pre_read_stream_identity_check_retained'] is True
        and dup['original_held_handles_closed_by_borrower'] is False,'ALL_SERIAL_DUPLICATES_IDENTITIES')
    require(frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'ALL_POST_CLEANUP_HELD_IDENTITIES')
    m.profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)
    pressure=h['native_open_backpressure']
    require(all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified','original_IO_deadline_unmodified',
        'original_sampler_windows_reused','cleanup_not_guarded_by_pressure')) and pressure['original_read_checks_skipped'] is False,
        'ORIGINAL_NATIVE_PRESSURE')
    m.early_contract(doc['early_source_checkpoint'])
    require(doc['early_source_runtime_connection_verified'] is True
        and doc['early_source_native_and_byte_guard_connected'] is True,'LIVE_EARLY_CONNECTION')
    timing=h['lock_timing_diagnostic']
    require(timing['first_original_error'] is None and timing['original_lock_limit_seconds']==600
        and timing['original_check_invoked_without_replacement'] is True and timing['unknown_measurements_not_zeroed'] is True
        and all(timing[k] is False for k in ('extra_CPU_RAM_or_native_query_started','original_resource_guard_or_deadline_extended',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_TIMING_GUARD')
    events=timing['explicit_phase_events']
    require([x['label'] for x in events]==['before_acquire','after_acquire','before_release']
        and all(type(x['original_lock_elapsed_seconds']) in (float,int) and 0<=x['original_lock_elapsed_seconds']<=600 for x in events)
        and all(events[i]['original_lock_elapsed_seconds']<=events[i+1]['original_lock_elapsed_seconds']
            and events[i]['guard_check_number']<events[i+1]['guard_check_number'] for i in range(2)),
        'THREE_SOURCE_BOUNDARIES_NO_PARENT_OR_INVENTED_EVENT')

def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_SOURCE_CHILD')),patch('subprocess.run',side_effect=AssertionError('NO_SOURCE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_SOURCE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_completed101_source_frame_r5'))
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'SYNTHETIC_SOURCE27')
    return COUNT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light');ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args();require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p299-r5-case101-source-{args.mode}-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY_NO_AUTO_RETRY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=frame=early=held=proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),original_failed_root_pin=review.ROOT,
        original_stopped_parent_pin=review.BODY,original_zero_placeholder_pin=review.ZERO,stop_review_pin=REVIEW_PIN,
        runtime_acceptance_changed=False,actual_product_body_executed=False,original_partial_post_source_hash_completed=False,
        early_source_runtime_connection_verified=False,early_source_native_and_byte_guard_connected=False,independent_post_source_only=True,
        original_preparation_failure_pin=OLD_PREPARATION_FAILURE,reviewed_prior_preparation_failure_preserved_not_accepted=False,
        r2_preparation_failure_pin=R2_PREPARATION_FAILURE,reviewed_r2_failure_preserved_not_accepted=False,
        r3_preparation_failure_pin=R3_PREPARATION_FAILURE,reviewed_r3_failure_preserved_not_accepted=False,
        original_independent_source_stop_pin=source_stop.PIN,qualified_source_stop_review_pin=SOURCE_STOP_REVIEW_PIN,
        reviewed_source_acquire_STOP_preserved_not_accepted=False)
    try:
        owner.admit();stage='metadata';q=m.Reader(owner,context)
        root=m.m.review.bound_json(q,review.ROOT);body=m.m.review.bound_json(q,review.BODY)
        checked=review.review(root,body);prior=m.m.review.bound_json(q,REVIEW_PIN)
        require(prior['schema_version']==review.SCHEMA and prior['state']==review.PASS and prior['review']==checked
            and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
            and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==7
            and prior['review_contract_tests_passed']==30,'SEALED_FRESH_STOP_REVIEW30')
        require(q.pin(review.ZERO['path'])==review.ZERO,'ZERO_PLACEHOLDER_PRESERVED')
        extras={name:q.pin(name) for name in EXTRAS};sealed=m.p.v.pins(prior['review_source_test_pins'])
        require(all(extras[n]==sealed[n] for n in EXTRAS[:2]),'UNCHANGED_REVIEW_CODE')
        require(q.pin(m.PHASE_QUALIFIER['path'])==m.PHASE_QUALIFIER,'ORIGINAL_QUALIFIED_ACQUISITION14')
        prior_failure=m.m.review.bound_json(q,OLD_PREPARATION_FAILURE);reviewed_preparation_failure(prior_failure)
        require(all(extras[p['path']]==p for p in OLD_CODE),'FROZEN_FAILED_PROTOTYPES_NOT_MODIFIED')
        out['reviewed_prior_preparation_failure_preserved_not_accepted']=True
        r2_failure=m.m.review.bound_json(q,R2_PREPARATION_FAILURE);reviewed_r2_constant_failure(r2_failure)
        out['reviewed_r2_failure_preserved_not_accepted']=True
        r3_failure=m.m.review.bound_json(q,R3_PREPARATION_FAILURE);reviewed_r3_comparison_failure(r3_failure)
        out['reviewed_r3_failure_preserved_not_accepted']=True
        stopped=m.m.review.bound_json(q,source_stop.PIN);checked_source_stop=source_stop.review(stopped)
        stop_support=m.m.review.bound_json(q,SOURCE_STOP_REVIEW_PIN)
        require(stop_support['state']==source_stop.PASS and stop_support['review']==checked_source_stop
            and stop_support['review_contract_tests_passed']==14 and stop_support['IO']['finished'] is True
            and stop_support['IO']['bound_inputs']==stop_support['IO']['final_fresh_hashes']==8
            and stop_support['resource_stop_reason'] is None and stop_support['resource_watcher_cleanup_confirmed'] is True,
            'FROZEN_SOURCE_ACQUIRE_STOP_REVIEW14')
        out['reviewed_source_acquire_STOP_preserved_not_accepted']=True
        original=m.p.v.pins(body['source_freeze'])
        require(len(original)==1599 and sum(x['bytes'] for x in original.values())==119993724 and not set(original)&set(extras),
            'FULL_ORIGINAL_AND_EIGHTEEN')
        required={**original,**extras};directories={PurePosixPath('.')}
        for name in required:directories.update(PurePosixPath(name).parents)
        require(len(directories)==DIRECTORIES,'ALL308_ANCESTORS')
        stage='contract_tests'
        out.update(nominal_scope_budget=budget(required),original_executed_source_pins=list(original.values()),
            extra_controller_pins=list(extras.values()),closing_contract_tests_passed=contracts(),review=checked)
        q.finish()
        if args.mode=='light':proposed=dict(state=LIGHT)
        else:
            early=m.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
            held=m.profile.InputLocks(m.p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,
                'EXACT_EARLY_OWNER_ORIGINAL_NATIVE20_ACQUISITION14')
            frame=m.p.frames.Frame(m.p.frames.Registry(),required,early,held=held)
            context.reader=m.p.frames.Counters(q.reader,frame.readers)
            out.update(early_source_native_and_byte_guard_connected=True)
            stage='source_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            def factory(checkpoint):
                return m.p.core.run.owned.OwnedReader(m.p.c.ROOT,checkpoint,samples=owner,protected={m.p.m.EXE['path']})
            for phase in ('metadata_hash','final_fresh_hash'):
                stage=phase
                with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
            stage='source_commit';held.mark('before_release')
            out.update(source_frame=frame.commit(body),early_source_runtime_connection_verified=True)
            proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error);out['failure_diagnostic']=m.diagnostic(error,stage)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='COMPLETED101_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='COMPLETED101_SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        if q is not None:q.close_entry();out.update(preparation_IO=q.summary(),preparation_bound_input_pins=list(q.reader.snapshots.values()))
        def terminal_validate(doc):
            if doc['state']==PASS:validate(doc,required)
            else:require(doc['state']==LIGHT and doc['early_source_native_and_byte_guard_connected'] is False,'PREPARATION_ONLY');prepared(doc,required)
        m.g.complete(out,owner,proposed,terminal_validate)
        out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:
            writer=m.r.packed.dump if out['state'] in (PASS,LIGHT) else m.r.compact.dump
            writer(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY_NO_RESOURCE_RESTART'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','closing_contract_tests_passed','early_source_runtime_connection_verified')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2

if __name__=='__main__':raise SystemExit(main())
