"""P262: case091 관측 오류 검토와 생성 중에도 끊기지 않는 누적 reader 연결.

원 실패/본체/수용 코드 불변. 새 Context나 표본을 만들거나 previous를 reset하지
않는다. 본체 재실행 및 runtime 수용 없음; 작은 실제 metadata 연결만 확인한다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_checkpoint_compound_runtime as old
m=old.m;p=old.p;g=old.g
SELF='tools/p09/review_monotonic_metadata_observation.py'
TEST='tools/p09/tests/test_monotonic_metadata_observation.py'
ROOT_PIN=dict(path=p.DIR+'/p260-case-091-run003.v1.json',bytes=1186964,
    sha256='8f67957fad03a952aec0ce47893f1b2ce7e06d91a6386c1efc6cf21d3dd76cff')
BODY_PIN=dict(path=p.DIR+'/cases/p260-case-091-run003.json',bytes=183603,
    sha256='3bed523c8db3404c537cf341a4bb23742cc976975a6793ea3ef0d2ccfd048b2a')
LIGHT_PIN=dict(path=p.DIR+'/p260-light-run002.v1.json',bytes=24621,
    sha256='5fa419f43368571f5f981a854a6d3c21fd443e97b6e01efa1974e5947e1835d4')
NAME='actual_import::formula_policy_revocation::current_writer_can_revoke_another_creators_policy_without_author_defaults'
SCHEMA='hwpx-agent.p09-monotonic-metadata-observation-review/v1'
PASS='PASS_CASE091_OBSERVATION_REVIEW_SMALL_READER_CONNECTION_NOT_RUNTIME_SOURCE_OR_GATE'
COUNT=36


def require(ok,code):old.require(ok,'MONOTONIC_'+code)


class AggregateContext:
    """원 Context의 reader 대입만 받아 첫 checkpoint 전에 누적값에 등록.

    이전 aggregate와 previous는 동일 객체/값으로 유지한다. 생성자가 표본을
    찍어도 새 reader만 관측하지 않으며, 실패한 reader의 실제 읽기도 삭제하지 않는다.
    """
    def __init__(self,context,counter):
        require(context.reader is counter and isinstance(counter,p.frames.Counters),'LIVE_AGGREGATE')
        self.context=context;self.counter=counter;self.bound=None
    def __getattr__(self,name):return getattr(self.context,name)
    @property
    def reader(self):return self.counter
    @reader.setter
    def reader(self,value):
        require(self.context.reader is self.counter and self.bound is None,'ONE_EXACT_ATTACHMENT')
        require(value is not self.counter and value is not self.counter.initial
            and not any(value is row for row in (*self.counter.readers,*self.counter.metadata)),'NO_COUNTER_DOUBLE_COUNT')
        require(type(value.bytes_read) is int and value.bytes_read>=0
            and type(value.read_passes) is int and value.read_passes>=0,'VALID_REAL_COUNTERS')
        self.counter.metadata.append(value);self.bound=value


def construct(reader_type,owner,context,counter):
    # 초기화 중 실패해도 이미 만든 entry binding만 정리; STOP이나 읽기 이력은 유지.
    require(isinstance(reader_type,type),'EXPLICIT_READER_CLASS')
    adapter=AggregateContext(context,counter);reader=reader_type.__new__(reader_type)
    try:
        reader_type.__init__(reader,owner,adapter)
        require(adapter.bound is reader.reader and context.reader is counter,'ORIGINAL_READER_CONNECTED')
        return reader
    except BaseException:
        if hasattr(reader,'entry_binding'):reader.close_entry()
        raise


def policy():
    return dict(same_original_context=True,register_before_constructor_sample=True,
        original_previous_and_all_reader_counters_retained=True,duplicate_counter_registration_rejected=True,
        failed_reader_counters_not_removed=True,constructor_failure_entry_cleanup=True,
        original_CPU_RAM600_and_metadata720_guards_preserved=True,original_guard_and_sampler_reused=True,
        new_sampler_thread_started=False,read_or_identity_checks_skipped=False,
        unknown_measurement_substituted_with_zero=False,CPU_or_PC_freeze_improvement_established=False)


def review(root,body):
    require(root['schema_version']==old.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']=='P193_READ_COUNTER_RESET'
        and root['resource_stop_reason']=='STOP_RESOURCE_OBSERVATION_FAILED'
        and root['resource_watcher_cleanup_confirmed'] is True
        and root['accepted_exact_product_body_count']==0,'LITERAL_OBSERVATION_FAILURE_NOT_CPU_STOP')
    require(root['selected_test_index']==91 and root['selected_test_name']==NAME
        and root['case_receipt_path']==BODY_PIN['path'] and root['compound_anchor_pin']==old.COMPOUND
        and root['preserved_case090_stop_pin']==old.review.ROOT_PIN,'EXACT_91_IDENTITY')
    prior=root['prior_runtime_plan'];require(prior['runtime_source_qualified_individual_cases']==84
        and prior['next_runtime_index']==91 and prior['runtime_remaining_individual_cases']==165,'PRIOR84_NOT_ADVANCED')
    require(root['runtime_contract_executions']==498 and root['original_retained_contract_executions']==450
        and root['own_queue_contract_tests_passed']==root['synthetic_following_queue_contract_tests_passed']==24
        and root['receipt_serialization_policy']==old.r.policy(),'ORIGINAL_CONTRACTS_AND_CODEC')
    required=p.v.pins(body['source_freeze']);require(len(required)==1555
        and sum(x['bytes'] for x in required.values())==119338307,'FULL1555_BODY_SCOPE')
    p.validate_parent(body,NAME,root['binding'],required)
    require(body['task']==body['minimal_worker_task']=='p204-r07-case-091-tests'
        and body['actual_product_child_executed'] is True and body['owned_limits_verified'] is True
        and body['cleanup_confirmed'] is True and body['owned_tree_empty'] is True
        and body['job_final']['active_processes']==0 and body['job_final']['owned_processes']==[],
        'BODY_PASS_AND_ORIGINAL_JOB_CLEANUP_NOT_OUTER_ACCEPTANCE')
    frame=root['terminal_source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['original_owned_cleanup_confirmed_before_release'] is False
        and frame['held_identity_after_owned_cleanup'] is None
        and frame['input_count']==1555 and frame['input_bytes']==119338307,'UNCOMMITTED_FRAME_NOT_PROMOTED')
    boundaries=frame['actual_byte_boundaries'];require(len(boundaries)==2,'TWO_ORIGINAL_BOUNDARIES')
    for role,row,diagnostic in zip(('before','after'),boundaries,body['owned_source_reader_passes']):
        require(row['role']==role and p.v.pins(row['actual_byte_pins'])==required
            and row['reader_diagnostics']==diagnostic,'EXACT_COMPLETE_ORIGINAL_BYTES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==1861
        and h['input_lock_handles_remaining']==h['handle_close_failed_attempts']==0
        and h['input_lock_cleanup_confirmed'] is True and h['maximum_lock_seconds']==600
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==4971
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==3110
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0,
        'ORIGINAL_NATIVE_CLEANUP_AND_RATE')
    old.early_contract(root['early_source_checkpoint'])
    prep=root['preparation_IO'];m.metadata_contract(prep)
    require(prep['finished'] is True and prep['bound_inputs']==prep['final_fresh_hashes']==151
        and prep['read_passes']==314,'COMPLETE_ORIGINAL_PREPARATION')
    post=root['terminal_metadata_IO'];require(post['finished'] is False and post['read_passes']==1
        and post['bytes_read']==131072 and post['bound_inputs']==post['final_fresh_hashes']==0
        and post['metadata_read_entry_pacing']['failed_calls']==1
        and post['metadata_read_entry_pacing']['binding_active'] is False,'INCOMPLETE_METADATA_NOT_SOURCE_FAILURE')
    for doc in (root,body):
        require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
            and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
                'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'NO_GATE_PROMOTION')
    return dict(selected_test_index=91,semantic_body_capture_complete=True,original_two1555_byte_reads_complete=True,
        original_frame_identity_commit_missing=True,original_metadata_final_fresh_missing=True,
        independently_qualified_source_and_compound_required=True,same_product_body_reexecution_allowed=False,
        runtime_previously_accepted=84,runtime_acceptance_changed=False,
        failure_class='OBSERVATION_COUNTER_BINDING_NOT_SUSTAINED_CPU_STOP',CPU_cause_or_freeze_resolution_established=False)


def contracts(root,body):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_monotonic_metadata_observation as tests
    with patch.object(tests,'FIXTURES',(root,body)),patch('subprocess.Popen',side_effect=AssertionError('NO_REVIEW_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_REVIEW_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_REVIEW_THREAD')):
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
            ('test_monotonic_metadata_observation','test_observed_shared_metadata'))
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'CONTRACT36_NO_SKIP')
    return COUNT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p262-case091-observation-review-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=post=counter=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),original_failed_root_pin=ROOT_PIN,
        original_body_pin=BODY_PIN,original_light_pin=LIGHT_PIN,runtime_acceptance_changed=False,
        actual_product_body_or_full_source_executed=False,actual_runtime_connection_qualified=False,
        monotonic_binding_policy=policy())
    try:
        owner.admit();q=m.Reader(owner,context)
        root=m.review.bound_json(q,ROOT_PIN);body=m.review.bound_json(q,BODY_PIN);checked=review(root,body)
        light=m.review.bound_json(q,LIGHT_PIN);old.closed_attempt(light)
        require(light['state']==old.LIGHT and light['selected_test_index']==91
            and light['runtime_contract_executions']==498 and light['prior_runtime_plan']==root['prior_runtime_plan'],
            'UNCHANGED_LIGHT91_PREVIOUS84')
        sealed=p.v.pins(light['extra_frame_controller_pins']);executed=p.v.pins(body['source_freeze'])
        for name in old.NEW:require(q.pin(name)==sealed[name]==executed[name],'EXECUTED_CONTROLLER_UNCHANGED')
        for name in (SELF,TEST):q.pin(name)
        out.update(review=checked,observation_contract_tests_passed=contracts(root,body))
        q.finish();counter=p.frames.Counters(q.reader,[]);context.reader=counter
        post=construct(m.Reader,owner,context,counter)
        for pin in (BODY_PIN,ROOT_PIN,LIGHT_PIN):require(post.pin(pin['path'])==pin,'SMALL_REAL_PINS')
        post.finish();require(context.reader is counter and counter.metadata==[post.reader],'SAME_LIVE_AGGREGATE')
        out.update(small_real_connection=dict(metadata_read_passes=post.reader.read_passes,
            metadata_bytes_read=post.reader.bytes_read,aggregate_read_passes=counter.read_passes,
            aggregate_bytes_read=counter.bytes_read,original_context_retained=True,final_fresh_completed=True))
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        for reader,key in ((q,'IO'),(post,'small_real_IO')):
            if reader is not None:reader.close_entry();out[key]=reader.summary()
        if q is not None:out['bound_input_pins']=list(q.reader.snapshots.values())
        def validate(doc):
            a=doc['IO'];b=doc['small_real_IO'];m.metadata_contract(a);m.metadata_contract(b)
            require(a['finished'] is True and a['bound_inputs']==a['final_fresh_hashes']==15
                and b['finished'] is True and b['bound_inputs']==b['final_fresh_hashes']==3
                and b['read_passes']==6 and a['read_passes']+b['read_passes']<=m.META_READ_LIMIT
                and doc['observation_contract_tests_passed']==COUNT,'SMALL_REAL18_ALL_FRESH')
        g.complete(out,owner,proposed,validate);out['metadata_observation']=g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','observation_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
