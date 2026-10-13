"""P272: 실패94 검토/진단·원600계측·metadata90 연결 후 전체1577 exact-one 실행.

수용 코드와 원 실패 불변. 생성 중 누적 관측 연결을 명시 사용하고 원 보호·
두 byte 읽기·identity·정리 유지. 미검토 실패 차단, 통과 본체 재실행 없음.
"""
import argparse
import copy
import hashlib
import io
import json
import math
import re
import sys
import unittest
from unittest.mock import patch
import resume_monotonic_compound_runtime as old
import qualify_rejected_parent_connection_r2 as connection
import qualify_early_metadata_pressure as metadata
import resume_diagnostic_guarded_runtime as prototype
a=connection.a
m=old.m;p=old.p;g=old.g;r=old.r
review=old.review;early_review=old.early_review
SELF='tools/p09/resume_diagnostic_guarded_runtime_r2.py'
TEST='tools/p09/tests/test_diagnostic_guarded_runtime_r2.py'
COMPOUND=dict(path=p.DIR+'/p264-case091-compound-run01.v1.json',bytes=473724,
    sha256='2e638cd49227bce9154690cddd41a65b736b31be6e97260f891ad869bed93827')
NEW=(a.docs.SELF,a.docs.TEST,a.SELF,a.TEST,connection.original.SELF,connection.original.TEST,
    connection.SELF,connection.TEST,metadata.SELF,metadata.TEST,prototype.SELF,prototype.TEST,SELF,TEST)
N=1577
SCHEMA='hwpx-agent.p09-diagnostic-guarded-runtime-pair/v1'
PASS='PASS_EXACT_R07_DIAGNOSTIC_GUARDED_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_DIAGNOSTIC_GUARDED_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p272-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=44
TOTAL=646


def require(ok,code):m.require(ok,'DIAGNOSTIC_RUNTIME_'+code)


class Reader(metadata.Reader):
    def json(self,path):
        carrier=super().json(path);name=self.name(path)
        if name.startswith(p.DIR+'/p272-') or name.startswith(p.DIR+'/cases/p272-'):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint) if carrier.get('schema_version')==r.packed.SCHEMA else carrier
        return carrier



def closed_attempt(doc):
    require(doc.get('schema_version')==SCHEMA and doc.get('state') in (PASS,LIGHT)
        and doc.get('error_code') is None and doc.get('resource_stop_reason') is None
        and doc.get('resource_watcher_cleanup_confirmed') is True
        and type(doc.get('runtime_contract_executions')) is int and doc['runtime_contract_executions']==TOTAL
        and doc.get('receipt_serialization_policy')==r.policy()
        and doc.get('monotonic_binding_policy')==review.policy(),'OWN_CLOSED_NOT_FAILED_OR_FOREIGN')


def budget(required,original,added):
    require(len(original)==1563 and len(required)==N and len(added)==14
        and set(added)==set(NEW) and not set(original)&set(added) and required=={**original,**added}
        and required[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in added.values())<=1048576,
        'ORIGINAL1563_PLUS_FOURTEEN_ONLY')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(3*N+306)/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_FITS_ORIGINAL600')
    return dict(full_runtime_inputs=N,new_inputs=14,native_rate=20,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)


def anchor(q):
    raw=old.anchor(q)
    legacy,base85,names,expected,exe,original,old_extras,legacy_original,legacy_extras,healthy,healthy_body,historical,historical_body=raw
    folder=p.c.ROOT/p.DIR
    a.inventory([x.name for x in folder.glob('p265-*.v1.json')],
        [x.name for x in (folder/'cases').glob('p265-*.json')])
    light=m.review.bound_json(q,a.LIGHT);old.closed_attempt(light)
    require(light['state']==old.LIGHT and light['selected_test_index']==92 and light['prior_runtime_plan']==base85,
        'ORIGINAL_LIGHT_PRIOR85')
    binding=p.v.identity(names,expected,exe);base=base85
    for pin in a.PAIRS:
        root=m.review.bound_json(q,pin);old.closed_attempt(root)
        body=m.review.bound_json(q,root['case_receipt_pin'])
        base=old.record(root,body,root['case_receipt_pin'],original,binding,old_extras,names,legacy,base)
    failed=m.review.bound_json(q,a.FAILURE);require(q.pin(a.ZERO['path'])==a.ZERO,'ORIGINAL94_ZERO_UNCHANGED')
    checked=a.review(failed,a.ZERO,base,original,binding)
    qualifier=m.review.bound_json(q,connection.QUALIFIED)
    require(qualifier['schema_version']==a.SCHEMA and qualifier['state']==a.PASS
        and qualifier['review']==checked and qualifier['runtime_plan']==base
        and qualifier['diagnostic_contract_tests_passed']==52,'P267_LITERAL_DIAGNOSTIC_REVIEW')
    failed_probe=m.review.bound_json(q,connection.FAILED);connection.review_failed_probe(failed_probe)
    probe=m.review.bound_json(q,metadata.ROOT);metadata.review(probe)
    diag=m.review.bound_json(q,probe['small_terminal_diagnostic_pin'])
    require(diag['runtime_accepted'] is False and diag['diagnostic_only'] is True
        and diag['original_parent_document']['job_final'] is None
        and diag['original_frame_snapshot']==probe['small_native_probe'],'SMALL_DIAGNOSTIC_NOT_RUNTIME_OR_JOB')
    repaired=m.review.bound_json(q,METADATA_PIN)
    require(repaired['schema_version']==metadata.SCHEMA and repaired['state']==metadata.PASS
        and repaired['metadata_contract_tests_passed']==32 and repaired['runtime_plan']==base
        and repaired['review']==metadata.review(probe)
        and repaired['actual_full_runtime_connection_qualified'] is False,'P270_METADATA_BINDING_NOT_FULL_RUNTIME')
    for doc in (qualifier,probe,repaired):
        require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
            and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes'],
            'ALL_QUALIFIERS_CLOSED_FRESH')
    failed_constructor=m.review.bound_json(q,METADATA_FAILED_PIN)
    constructor_failure(failed_constructor)
    initial=m.review.bound_json(q,P271_FAILED_PIN)
    require(initial['schema_version']==prototype.SCHEMA and initial['state']=='FAILED_NOT_ACCEPTED'
        and initial['error_code']=='P152_FULL_REDACTED_FAILURE'
        and initial['resource_stop_reason'] is None and initial['resource_watcher_cleanup_confirmed'] is True
        and initial['accepted_exact_product_body_count']==0 and 'runtime_contract_executions' not in initial
        and 'selected_test_index' not in initial and 'terminal_source_frame' not in initial
        and initial['preparation_IO']['finished'] is False,'P271_FAILED_ANCHOR_NOT_ACCEPTED')
    require(sorted(x.name for x in folder.glob('p271-*.v1.json'))==[P271_FAILED_PIN['path'].split('/')[-1]]
        and not list((folder/'cases').glob('p271-*.json')),'ONLY_REVIEWED_P271_NO_BODY')
    for pin in P271_CODE:require(q.pin(pin['path'])==pin,'P271_EXECUTED_CODE_PRESERVED')
    for generation,pins in (('p267',(connection.QUALIFIED,)),('p268',(connection.FAILED,)),
            ('p269',(metadata.ROOT,)),('p270',(METADATA_FAILED_PIN,METADATA_PIN))):
        require(sorted(x.name for x in folder.glob(generation+'-*.v1.json'))==
            sorted(pin['path'].split('/')[-1] for pin in pins),'UNKNOWN_QUALIFIER_ATTEMPT_BLOCKS')
    require(sorted(x.name for x in (folder/'cases').glob('p269-*.json'))==
        [probe['small_terminal_diagnostic_pin']['path'].split('/')[-1]],'ONLY_SMALL_DIAGNOSTIC')
    added={name:q.pin(name) for name in NEW}
    for doc in (qualifier,failed_probe,probe,repaired):
        frozen=p.v.pins(doc['bound_input_pins'])
        for name in set(NEW)&set(frozen):require(added[name]==frozen[name],'EXECUTED_QUALIFIER_CODE_UNCHANGED')
    required={**original,**added};extras={**old_extras,**added}
    require(len(original)==1563 and len(old_extras)==96 and len(extras)==110,'ALL_ORIGINAL_AND_NEW_CONTROLLERS110')
    budget(required,original,added)
    return (legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,
        historical,historical_body,legacy_original,legacy_extras,probe)



METADATA_PIN=dict(path=p.DIR+'/p270-early-metadata-pressure-run02.v1.json',bytes=156551,
    sha256='760509efb02dfb51f3d27a5d09dd6a7f9c07d1f6ce336004afb479e5802b3b60')
METADATA_FAILED_PIN=dict(path=p.DIR+'/p270-early-metadata-pressure-run01.v1.json',bytes=4244,
    sha256='707ed624d2df16780bb8c7c4900ef436a0501a0552593ac00c503ab92da99ae0')


P271_CODE=(
    dict(path='tools/p09/resume_diagnostic_guarded_runtime.py',bytes=28992,sha256='1349828826373ac0c8cdb520fcf96010ec2b9f60a10ab8bee9976a5d3fb82bde'),
    dict(path='tools/p09/tests/test_diagnostic_guarded_runtime.py',bytes=3058,sha256='28dbfb74efdbc147996a4d57e2927b67bd1fc7a57eb409a3f6adc9119523de04'))
P271_FAILED_PIN=dict(path=p.DIR+'/p271-light-run001.v1.json',bytes=43372,
    sha256='618acd5d4647b83970dbd4dd6133896af51cc901a0096ab4e31b7bf1fe426120')

def constructor_failure(doc):
    require(doc['schema_version']==metadata.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P152_FULL_REDACTED_FAILURE' and 'IO' not in doc
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['actual_product_body_or_full_source_executed'] is False,
        'ORIGINAL_CONSTRUCTOR_FAILURE_MISSING_IO_NOT_PROMOTED')

def diagnostic(error,stage):
    frames=[];cursor=error.__traceback__
    while cursor is not None:
        frames.append(dict(file=p.c.Path(cursor.tb_frame.f_code.co_filename).name,line=cursor.tb_lineno))
        cursor=cursor.tb_next
    return dict(stage=stage,exception_class=type(error).__name__,locations=frames[-8:],
        exception_message_included=False,diagnostic_not_acceptance=True)


def metadata_contract(row):
    require(row['selected_metadata_warning_CPU_percent']==90
        and all(row[k] is True for k in ('constructor_original95_path_retained','original95_pressure_retained_as_base',
            'original_guard_and_sampler_reused'))
        and all(row[k] is False for k in ('reader_or_aggregate_counter_replaced','CPU_RAM600_or720_guard_extended',
            'cleanup_callback_wrapped','new_sampler_or_thread_started','source_byte_or_identity_checks_skipped',
            'CPU_or_PC_freeze_improvement_established')),'ORIGINAL_METADATA95_600_720_NO_DROP')
    old.early_contract(row['original_early_source_algorithm_statistics'])


def timing_contract(row):
    require(row['first_original_error'] is None and row['original_lock_limit_seconds']==600
        and type(row['original_guard_checks']) is int and row['original_guard_checks']>0
        and row['original_check_invoked_without_replacement'] is True
        and row['extra_clock_only_at_boundary_or_first_error'] is True
        and row['unknown_measurements_not_zeroed'] is True
        and all(row[k] is False for k in ('extra_CPU_RAM_or_native_query_started','original_resource_guard_or_deadline_extended',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_LOCK_TIMING_NO_GUARD_CHANGE')
    events=row['explicit_phase_events'];require([x['label'] for x in events]==list(connection.LABELS),'FIVE_BOUNDARIES')
    previous_seconds=-1;previous_number=0
    for event in events:
        seconds=event['original_lock_elapsed_seconds'];number=event['guard_check_number']
        require(type(seconds) in (float,int) and math.isfinite(seconds) and previous_seconds<=seconds<=600
            and type(number) is int and previous_number<number<=row['original_guard_checks'],'REAL_FINITE_MONOTONIC_BOUNDARIES')
        previous_seconds=seconds;previous_number=number


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+306
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==305
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+306
        and h['handle_metadata_checks']==4*N+612
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=306),'ALL1577_NATIVE_IDENTITIES_AND_CLOSE')
    m.r.h.h.pressure_contract(h['native_open_backpressure']);m.lower_contract(h)
    timing_contract(h['lock_timing_diagnostic'])


def early_contract(row):
    require(row['early_source_warning_CPU_percent']==90 and row['cool_distinct_samples']==2
        and row['maximum_pause_windows']==8 and all(row[k] is True for k in
        ('original_guard_called_before_pressure','original_hard_CPU_RAM600_guards_preserved','existing_owner_samples_only'))
        and all(row[k] is False for k in ('new_sampler_or_thread_started','source_byte_reads_or_identity_checks_skipped',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_GUARDS_EARLY_SOURCE_ONLY')


def job_contract(body):
    limits=body['owned_limits_readback'];require(limits['verified'] is True
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] is True and limits['breakaway_disabled'] is True,'ORIGINAL_JOB_LIMIT_VALUES')


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['compound_anchor_pin']==COMPOUND and doc['preserved_case091_failure_pin']==review.ROOT_PIN
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['binding']==binding and doc['prior_runtime_plan']==base and doc['case_receipt_pin']==pin
        and doc['original_retained_contract_executions']==558 and doc['own_queue_contract_tests_passed']==COUNT
        and doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['old_contract_scope']=='ORIGINAL1563_NO_BODY_REEXECUTION'
        and doc['new_contract_scope']=='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1577'
        and type(doc['runtime_contract_executions']) is int and doc['runtime_contract_executions']==TOTAL
        and doc['receipt_serialization_policy']==r.policy() and doc['monotonic_binding_policy']==review.policy()
        and doc['aggregate_post_reader_connection_verified'] is True
        and doc['diagnostic_parent_connection_selected'] is True and doc['native_timing_connected'] is True
        and doc['early_metadata_connection_selected'] is True
        and doc['reviewed_case094_failure_pin']==a.FAILURE and doc['qualified_connection_pin']==metadata.ROOT
        and doc['qualified_metadata_pin']==METADATA_PIN
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and all(doc[k] is True for k in ('compound_anchor_verified_without_body_reexecution','early_source_guard_connected',
            'actual_product_child_executed','packed_root_writer_selected','original_successful_bodies_not_reexecuted',
            'original_parent_capture_adapter_selected')),'COMPLETE_OWN_PAIR_NOT_PARTIAL_OR_GATE')
    m.metadata_contract(doc['preparation_IO']);m.metadata_contract(doc['closing_component']['metadata_IO'])
    require(doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=m.META_READ_LIMIT,
        'SAME_SHARED720_CAP')
    metadata_contract(doc['preparation_IO']['early_metadata_pressure'])
    metadata_contract(doc['closing_component']['metadata_IO']['early_metadata_pressure'])
    job_contract(body);early_contract(doc['early_source_checkpoint']);native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    old={n:p for n,p in required.items() if n not in NEW};added={n:required[n] for n in NEW}
    require(doc['scope_budget']==budget(required,old,added)
        and body['task']==f'p204-r07-case-{index:03}-tests' and doc['accepted_exact_product_body_count']==1
        and doc['runtime_plan']==g.advance(legacy,base,names,index),'FULL_SCOPE_AND_EXACT_ONE_ADVANCE')
    return doc['runtime_plan']


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p272-admission-run*.v1.json'),*folder.glob('p272-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p272-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p272-case-{index:03}-run{number:03}.json','BODY_NAMESPACE')
        body=m.review.bound_json(q,pin);plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy,healthy_body,required,extras,original,old_extras,
        historical,historical_body,legacy_original,legacy_extras):
    require(old.contracts(fixtures,healthy,healthy_body,original,old_extras,legacy_original,legacy_extras,
        historical,historical_body)==558,'ORIGINAL558_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as f
    import test_monotonic_compound_runtime as retained
    import test_diagnostic_guarded_runtime_r2 as tests
    legacy,current,names,stop=fixtures;synthetic=copy.deepcopy(healthy)
    synthetic.update(original_retained_contract_executions=558,own_queue_contract_tests_passed=COUNT,
        synthetic_following_queue_contract_tests_passed=COUNT,old_contract_scope='ORIGINAL1563_NO_BODY_REEXECUTION',
        new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1577',preserved_case091_failure_pin=review.ROOT_PIN,
        runtime_contract_executions=TOTAL,receipt_serialization_policy=r.policy(),monotonic_binding_policy=review.policy(),
        aggregate_post_reader_connection_verified=True,early_source_guard_connected=True,original_parent_capture_adapter_selected=True,
        original_successful_bodies_not_reexecuted=True,actual_product_child_executed=True,packed_root_writer_selected=True,
        early_source_checkpoint=early_review.EarlySourceCheckpoint(lambda:None,None).summary(),
        scope_budget=budget(required,original,{n:required[n] for n in NEW}),
        diagnostic_parent_connection_selected=True,native_timing_connected=True,early_metadata_connection_selected=True,
        reviewed_case094_failure_pin=a.FAILURE,qualified_connection_pin=metadata.ROOT,qualified_metadata_pin=METADATA_PIN)
    with patch.object(f,'m',sys.modules[__name__]),patch.object(f,'FIXTURES',(fixtures,synthetic,healthy_body,required,extras)), \
            patch.object(retained,'m',sys.modules[__name__]), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_RUNTIME_CONTRACT_THREAD')):
        first=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        index,_=g.old.select(current,names);following=g.advance(legacy,current,names,index)
        with patch.object(f,'FIXTURES',((legacy,following,names,stop),synthetic,healthy_body,required,extras)):
            second=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(first.wasSuccessful() and first.testsRun==COUNT and not first.skipped
        and second.wasSuccessful() and second.testsRun==COUNT and not second.skipped,'CURRENT44_AND_FOLLOWING44')
    return TOTAL


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p272-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_rejected(Output(stream),owner,out) if capture.rejected else capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),bytes=written,
        sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light');ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p272-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=COMPOUND,
        preserved_case091_failure_pin=review.ROOT_PIN,original_retained_contract_executions=558,
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        old_contract_scope='ORIGINAL1563_NO_BODY_REEXECUTION',new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1577',
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False,diagnostic_parent_connection_selected=False,
        native_timing_connected=False,early_metadata_connection_selected=False,reviewed_case094_failure_pin=a.FAILURE,
        qualified_connection_pin=metadata.ROOT,qualified_metadata_pin=METADATA_PIN)
    stage='admission'
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context);stage='anchor'
        legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,historical,historical_body,legacy_original,legacy_extras,qualified_probe=anchor(q)
        stage='selection';binding=p.v.identity(names,expected,exe);plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        stage='contract_tests'
        with context.scope('contract_tests'):
            out['runtime_contract_executions']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),healthy,healthy_body,
                required,extras,original,old_extras,historical,historical_body,legacy_original,legacy_extras)
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),compound_anchor_verified_without_body_reexecution=True,
            scope_budget=budget(required,original,{n:required[n] for n in NEW}),early_metadata_connection_selected=True)
        stage='final_fresh_preparation'
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p272-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p272-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p272-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=connection.TimedInputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out['original_parent_capture_adapter_selected']=isinstance(capture,m.support.candidate.Capture)
            out['diagnostic_parent_connection_selected']=type(parent) is connection.ParentConnection and type(capture) is a.Capture
            out['native_timing_connected']=type(held) is connection.TimedInputLocks
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context);held.mark('after_parent')
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=review.construct(Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);out['failure_diagnostic']=diagnostic(error,stage);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==TOTAL and doc['monotonic_binding_policy']==review.policy(),
                    'LIGHT_ALL_FRESH_AND646')
                m.metadata_contract(doc['preparation_IO']);metadata_contract(doc['preparation_IO']['early_metadata_pressure'])
        g.complete(out,owner,proposed,validate)
        if capture is not None and (capture.pending or capture.rejected):
            try:preserve_failure(capture,frame,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                writer=r.packed.dump if out['state'] in (PASS,LIGHT) else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
                writer(out,stream,checkpoint=terminal,indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='MONOTONIC_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','runtime_contract_executions','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_diagnostic_guarded_runtime_r2',sys.modules[__name__])
    raise SystemExit(main())

