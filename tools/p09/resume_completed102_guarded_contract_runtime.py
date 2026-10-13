"""P317: 수용102 불변 anchor와103 준비 STOP 뒤 계약별 원checkpoint 연결.
기존 full1640 + helper/test/새runtime/test4 = full1644. 두전체byte/Native/Job/600/720 유지.
원230 qualification은 marker로만 바인딩; 현재88+following88+원78=254를 실제 실행한다.
수용 본문 재실행, 실패 PASS 승격, 원guard/검사 삭제 없음.
"""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch
import resume_completed101_compound_runtime_r3 as previous
import resource_guarded_contract_suite as guarded
m=previous.m;p=previous.p;g=previous.g;r=previous.r
accepted=previous.accepted;leading=previous.leading;inner=previous.inner;counter=previous.counter
profile=previous.profile;connection=previous.connection;review=previous.review;early_review=previous.early_review
Reader=previous.Reader
SELF='tools/p09/resume_completed102_guarded_contract_runtime.py'
TEST='tools/p09/tests/test_completed102_guarded_contract_runtime.py'
ANCHOR=previous.ANCHOR
RETAINED_QUALIFIER=previous.RETAINED_QUALIFIER
INNER_QUALIFIER=previous.INNER_QUALIFIER
FROZEN66=previous.FROZEN66
FROZEN70=previous.FROZEN70
FROZEN75=previous.FROZEN75
FROZEN77=FROZEN75+[{"path":"tools/p09/resume_completed101_compound_runtime_r3.py","bytes":44007,"sha256":"9e88bfb0d6676270fc1714c75c0e5f2beec5d4f103a917cbc292865f47d1e006"},{"path":"tools/p09/tests/test_completed101_compound_runtime_r3.py","bytes":15257,"sha256":"f8b2eaf92402524d36986a5f553aa4fabbc766999b8dec77f7772850e9b41647"}]
GUARDED_CODE=[{"path":"tools/p09/resource_guarded_contract_suite.py","bytes":3547,"sha256":"68a98912a8e1c29ebfdfaeb0d2810e863008f04fdf325e74ea4e97644231a0d7"},{"path":"tools/p09/tests/test_resource_guarded_contract_suite.py","bytes":7747,"sha256":"e1ae72b8372023489ca6361993a7dd701ba59f5191c9cfda1b21b1a8415485f2"}]
NATIVE_STOP=previous.NATIVE_STOP
SUPPORT_STATUS=previous.SUPPORT_STATUS
IDLE=previous.IDLE
COUNTER_QUALIFIER=previous.COUNTER_QUALIFIER
COUNTER_REAL=previous.COUNTER_REAL
COMPLETED102={"path":"implementation/p09/evidence/locked-r07/p312-case-102-run002.v1.json","bytes":639564,"sha256":"fd829ade757b3108d48085d09f417fdc87bceb41a75ab43ce18642c2f50adcc6"}
PREPARATION103_STOP={"path":"implementation/p09/evidence/locked-r07/p312-case-103-run003.v1.json","bytes":88058,"sha256":"aa0abde2db6cca5f36cd20c6e87be162ade9bf1a1f96841cd5eba54a5fc451cc"}
GUARDED_QUALIFIER={"path":"implementation/p09/evidence/locked-r07/p315-guarded-contract21-and-existing230-qualification-run01.v1.json","bytes":48227,"sha256":"c85cfc594f6401adbea4e11be5e40d5d12a0a6c023bb7f8995d9bdc036d537b3"}
STATUS_STOP={"path":"implementation/p09/evidence/locked-r07/p316-r125-status-final-fresh-stop-run02.v1.json","bytes":77763,"sha256":"743106b144a8c2f44c73c5491a15728cbb16847f8252b569f7a2f090e3268de8"}
NEW=previous.NEW+(guarded.SELF,guarded.TEST,SELF,TEST)
N=1644
DIRECTORIES=308
SCHEMA='hwpx-agent.p09-completed102-per-test-guarded-runtime-pair/v1'
PASS='PASS_EXACT_R07_COMPLETED102_PER_TEST_GUARDED_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_COMPLETED102_PER_TEST_GUARDED_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p317-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=88
EXECUTED=2*COUNT+30+18+inner.COUNT

def require(ok,code):m.require(ok,'COMPLETED102_GUARDED_'+code)

def budget(required,baseline,added):
    require(len(baseline)==1625 and len(required)==N and len(added)==19
        and set(added)==set(NEW) and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in baseline.values())==120247880
        and sum(x['bytes'] for x in added.values())<=1048576,'FULL_QUALIFIED1625_PLUS_NINETEEN_NO_SUBSET')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_UNCHANGED600')
    return dict(full_runtime_inputs=N,baseline_full_source_inputs=1625,new_inputs=19,
        actual_ancestor_directory_count=DIRECTORIES,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_new_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)

def stop103(d,plan):
    io=d['preparation_IO'];obs=d['metadata_observation'];x=io['leading_metadata_checkpoint_pressure']
    require(d['schema_version']==previous.SCHEMA and d['state']=='FAILED_NOT_ACCEPTED'
        and d['error_code']==d['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and d['resource_watcher_cleanup_confirmed'] is True and d['failure_diagnostic']['stage']=='final_fresh_preparation'
        and d['selected_test_index']==103 and d['prior_runtime_plan']==plan and 'runtime_plan' not in d
        and d['runtime_contract_executions']==230 and d['accepted_exact_product_body_count']==0
        and d['actual_product_child_executed'] is False and 'case_receipt_path' not in d
        and 'terminal_source_frame' not in d and 'terminal_parent_failure_sidecar_pin' not in d
        and io['read_passes']==109 and io['bytes_read']==10717316 and io['bound_inputs']==98
        and io['final_fresh_hashes']==11 and io['finished'] is False
        and x['binding_active'] is False and x['hard_callback_restored_after_close'] is True
        and x['early_pressure']['warning_entries']==1 and x['early_pressure']['completed_pause_windows']==4
        and x['early_pressure']['requested_pause_seconds']==2
        and obs['completed_sample_count']==22 and all(row['system_cpu_percent']==100
            and row['parent_cpu_machine_percent']==0 and row['audited_logical_read_bytes_delta']==0
            for row in obs['samples'][-4:]),'EXACT103_PREPARATION_STOP_NO_NATIVE_OR_ADVANCE')
    return True

def guarded_contract(row,expected=EXECUTED):
    require(type(row) is dict and row['started_tests']==row['stopped_tests']==
        row['successful_before_test_checks']==row['successful_after_test_checks']==expected
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==5
        and row['original_unittest_results_preserved'] is True
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and row['original_guard_or_test_coverage_relaxed'] is False
        and row['test_results_are_not_product_acceptance'] is True,'EVERY_TEST_ORIGINAL_CHECKPOINT_NOT_ACCEPTANCE')

def anchor(q):
    a=previous.anchor(q)
    legacy,prior95,names,expected,exe,old_required,old_extras,baseline,old_added,old,oldbody,oldstop=a
    bound=m.m.review.bound_json
    root=bound(q,COMPLETED102);bp=root['case_receipt_pin'];body=bound(q,bp)
    plan=previous.record(root,body,bp,old_required,root['binding'],old_extras,names,legacy,prior95,baseline,old_added)
    require(plan['runtime_source_qualified_individual_cases']==96 and plan['next_runtime_index']==103,
        'EXACT102_ACCEPTED96_WITHOUT_BODY_REEXECUTION')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR).glob('p312-case-*-run*.v1.json'))==
        ['p312-case-102-run002.v1.json','p312-case-103-run003.v1.json']
        and sorted(x.name for x in (p.c.ROOT/p.DIR/'cases').glob('p312-*.json'))==
        ['p312-case-102-run002.json'],'IMMUTABLE_PREVIOUS_NAMESPACE_NO_RETRY')
    failure=bound(q,PREPARATION103_STOP);stop103(failure,plan)
    status=bound(q,STATUS_STOP)
    require(status['state']=='FAILED_NOT_ACCEPTED' and status['resource_stop_reason']==status['error_code']=='STOP_SUSTAINED_SYSTEM_CPU'
        and status['resource_watcher_cleanup_confirmed'] is True and status['runtime_plan']==plan
        and status['actual_new_product_or_Native_executed_during_review'] is False
        and status['IO']['read_passes']==117 and status['IO']['bound_inputs']==108
        and status['IO']['final_fresh_hashes']==8 and status['IO']['finished'] is False
        and status['IO']['leading_metadata_checkpoint_pressure']['hard_callback_restored_after_close'] is True,
        'P316_STOP_IS_NOT_SUCCESS_ANCHOR_OR_NEW_PRODUCT')
    qualification=bound(q,GUARDED_QUALIFIER)
    current=[q.pin(row['path']) for row in GUARDED_CODE]
    require(current==GUARDED_CODE==qualification['code_pins']
        and qualification['schema_version']=='hwpx-agent.p09-guarded-contract-suite-qualification/v1'
        and qualification['state']=='PASS_NEW21_AND_EXISTING230_EACH_CHECKPOINT_NOT_NATIVE_RUNTIME_OR_GATE'
        and qualification['prior_accepted_runtime_plan']==plan and qualification['failed103_pin']==PREPARATION103_STOP
        and qualification['failed103_pressure']==failure['preparation_IO']
        and qualification['new_tests_executed']==21 and qualification['original230_executed_once']==230
        and qualification['actually_executed_contract_tests']==251
        and qualification['resource_stop_reason'] is None and qualification['resource_watcher_cleanup_confirmed'] is True
        and qualification['new_helper_connected_to_product_runtime'] is False
        and qualification['actual_new_product_or_Native_executed'] is False
        and qualification['IO']['bound_inputs']==qualification['IO']['final_fresh_hashes']==100
        and qualification['IO']['read_passes']==200 and qualification['IO']['finished'] is True,
        'UNCHANGED21_HELPER_SUPPORT_NOT_PRODUCT')
    guarded_contract(qualification['guarded_runner_statistics'],230)
    require([old_required[x['path']] for x in FROZEN77]==FROZEN77,'ALL77_CURRENT_OLD_NATIVE_PINS')
    new_four={guarded.SELF:current[0],guarded.TEST:current[1],SELF:q.pin(SELF),TEST:q.pin(TEST)}
    added={**old_added,**new_four};required={**old_required,**new_four};extras={**old_extras,**new_four}
    directories={PurePosixPath('.')}
    for n in required:directories.update(PurePosixPath(n).parents)
    require(len(directories)==DIRECTORIES and len(extras)==177
        and required=={**baseline,**added} and list(added)==list(NEW),'FULL1640_PLUS4_AND_ALL308_ANCESTORS')
    budget(required,baseline,added)
    return legacy,plan,names,expected,exe,required,extras,baseline,added,old,oldbody,oldstop

def live_pins(q,names,expected):
    require(len(names)==len(set(names)) and names==tuple(x['path'] for x in expected),
        'DISTINCT_CURRENT_PLAN_NOT_HISTORY_CACHE')
    result={n:q.pin(n) for n in names}
    require(list(result.values())==expected,'ALL_FROZEN75_CURRENT_BYTES')
    return result

def inner_contract(row):
    x=row['leading_metadata_checkpoint_pressure']
    require(x['warning_CPU_percent']==90 and x['inner_guard_calls']>=row['read_passes']
        and x['binding_active'] is False and x['hard_callback_restored_after_close'] is True
        and x['original95_guard_callback_wrapped_only_while_bound'] is True
        and x['original_hard_CPU_RAM_IO600_callback_always_first'] is True
        and x['original95_object_and_outer90_and_entry32_callbacks_retained'] is True
        and x['original_reader_and_byte_pacer_and_counters_retained'] is True
        and x['new_sampler_or_thread_or_native_query_started'] is False
        and x['guards_or_deadline_or_source_coverage_relaxed'] is False
        and x['cleanup_not_guarded_or_paced'] is True
        and x['CPU_cause_or_PC_freeze_resolution_established'] is False,'INNER90_HARD_FIRST_CLOSED')
    m.early_contract(x['early_pressure'])

def leading_contract(row):
    inner_contract(row)
    x=row['leading_metadata_entry_pressure']
    require(x['pre_entry_warning_CPU_percent']==90 and x['original_entry_rate']==32
        and x['calls']==x['completed_original_reads']==row['read_passes'] and x['failed_calls']==0
        and x['leading_binding_active'] is False and x['original_inner95_and90_callbacks_unmodified'] is True
        and x['original_entry_pacer_and_reader_retained'] is True
        and x['original_hard_CPU_RAM_IO600_720_and_all_reads_preserved'] is True
        and x['new_sampler_or_thread_started'] is False and x['original_clock_credit_or_counter_reset'] is False
        and x['source_or_case_or_read_exclusions_added'] is False and x['cleanup_not_guarded_or_paced'] is True,
        'ORIGINAL_CALLBACKS_AND_NEW_PRE_ENTRY90')
    m.early_contract(x['early_pressure'])
    m.m.metadata_contract(row);m.metadata_contract(row['early_metadata_pressure'])
    m.entry_pressure.connection_contract(row['metadata_entry_early_pressure_connection'])

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'FULL1644_NATIVE_TWO_BYTE_AND_CLEANUP')
    m.m.r.h.h.pressure_contract(h['native_open_backpressure']);m.m.lower_contract(h)
    m.timing_contract(h['lock_timing_diagnostic']);profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)

def closed_attempt(d):
    require(type(d) is dict and d.get('schema_version')==SCHEMA and d.get('state') in (PASS,LIGHT),
        'CLOSED_SCHEMA_STATE_BEFORE_STATISTICS')
    guarded_contract(d['contract_checkpoint_statistics'])
    require(d['completed102_anchor_pin']==COMPLETED102 and d['previous103_preparation_STOP_pin']==PREPARATION103_STOP
        and d['guarded_contract_qualification_pin']==GUARDED_QUALIFIER
        and d['previous_status_STOP_pin']==STATUS_STOP and d['previous103_STOP_reviewed'] is True
        and d['per_test_original_checkpoint_selected'] is True
        and d['reused_helper_contract_executions']==21,'CLOSED_GUARDED_MARKERS_AND_REUSE_NOT_EXECUTED')
    require(d['schema_version']==SCHEMA and d['state'] in (PASS,LIGHT)
        and d.get('error_code') is None and d['resource_stop_reason'] is None
        and d['resource_watcher_cleanup_confirmed'] is True and d['runtime_contract_executions']==EXECUTED
        and d['reused_retained_contract_executions']==1486 and d['retained_contract_qualification_pin']==RETAINED_QUALIFIER
        and d['compound_anchor_pin']==ANCHOR and d['original_successful_bodies_not_reexecuted'] is True
        and d['previous_preparation_STOP_pin']==inner.FAILURE and d['inner_metadata_qualification_pin']==INNER_QUALIFIER
        and d['compound_anchor_verified_without_body_reexecution'] is True
        and d['metadata_entry_pressure_connection_selected'] is True and d['packed_root_writer_selected'] is True
        and d['previous_Native_STOP_pin']==NATIVE_STOP and d['counter_support_status_pin']==SUPPORT_STATUS
        and d['idle_support_pin']==IDLE and d['counter_qualification_pin']==COUNTER_QUALIFIER
        and d['counter_two_queries_pin']==COUNTER_REAL and d['previous_Native_STOP_reviewed'] is True
        and d['counter_code_qualification_selected'] is True
        and d['counter_role']=='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        'CLOSED_EXACT_CURRENT_NO_FAILED_RETRY')

def record(doc,body,pin,required,binding,extras,names,legacy,base,baseline,added):
    closed_attempt(doc);index,name=g.old.select(base,names)
    require(doc['state']==PASS and doc['selected_test_index']==index and doc['selected_test_name']==name
        and name not in base['runtime_qualified_test_names'] and doc['binding']==binding and doc['prior_runtime_plan']==base
        and doc['case_receipt_pin']==pin and doc['receipt_serialization_policy']==r.policy()
        and doc['monotonic_binding_policy']==review.policy() and doc['scope_budget']==budget(required,baseline,added)
        and doc['scope_added_nineteen_pins']==list(added.values()) and doc['extra_frame_controller_pins']==list(extras.values())
        and doc['accepted_exact_product_body_count']==1 and doc['runtime_plan']==g.advance(legacy,base,names,index),
        'EXACT_NEXT_ONE_QUALIFIED_NOT_DUPLICATE')
    require(doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['native_timing_connected'] is True and doc['early_source_guard_connected'] is True
        and doc['aggregate_post_reader_connection_verified'] is True and doc['diagnostic_parent_connection_selected'] is True
        and doc['original_parent_capture_adapter_selected'] is True and doc['acquisition_phase_connection_selected'] is True
        and doc['actual_product_child_executed'] is True and body['task']==f'p204-r07-case-{index:03}-tests'
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=720
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'ALL_CLOSED_BINDING_JOB_METADATA_GUARDS_NOT_GATE')
    leading_contract(doc['preparation_IO']);leading_contract(doc['closing_component']['metadata_IO'])
    m.job_contract(body);m.early_contract(doc['early_source_checkpoint'])
    native_pair(doc['closing_component'],body,pin,required,binding,extras);r.stats_contract(doc['packed_parent_write_statistics'],pin)
    return doc['runtime_plan']

def progress(q,legacy,base,names,required,binding,extras,baseline,added):
    folder=p.c.ROOT/p.DIR
    for path in sorted((*folder.glob('p317-light-run*.v1.json'),*folder.glob('p317-admission-run*.v1.json'))):
        closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    rows=sorted(folder.glob('p317-case-*-run*.v1.json'));require(len(rows)<=4096,'BOUNDED_NAMESPACE')
    plan=base
    for path in rows:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        d=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(d)
        require(d['selected_test_index']==index and d['case_receipt_pin']['path']==
            f'{p.DIR}/cases/p317-case-{index:03}-run{number:03}.json','FILENAME_BODY_IDENTITY')
        bp=d['case_receipt_pin'];body=m.m.review.bound_json(q,bp)
        plan=record(d,body,bp,required,binding,extras,names,legacy,plan,baseline,added)
    return plan

def contracts(fixtures,stop,q):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_completed102_guarded_contract_runtime as t
    statistics=None
    try:
        with guarded.bind(q.reader.checkpoint) as statistics, \
                patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
            require(p.contracts()==30 and leading.contracts()==18 and inner.contracts(stop)==30,
                'ORIGINAL_NATIVE30_LEADING18_AND_INNER30')
            for following in (False,True):
                with patch.object(t,'FIXTURES',fixtures),patch.object(t,'FOLLOWING',following):
                    rr=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                require(rr.wasSuccessful() and rr.testsRun==COUNT and not rr.skipped,'CURRENT88_AND_FOLLOWING88')
        row=statistics.summary();guarded_contract(row)
        require(unittest.TextTestRunner is guarded._ORIGINAL_RUNNER and guarded._ACTIVE is False,'ORIGINAL_RUNNER_RESTORED')
        return EXECUTED,row
    finally:
        # STOP時에도 시작/정지/통과checkpoint를 분리한 부분 통계를 보존한다.
        q.contract_checkpoint_statistics=statistics.summary() if statistics is not None else None

def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p317-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
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
    destination=p.c.ROOT/f'{p.DIR}/p317-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=ANCHOR,
        retained_contract_qualification_pin=RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        previous_preparation_STOP_pin=inner.FAILURE,inner_metadata_qualification_pin=INNER_QUALIFIER,
        completed102_anchor_pin=COMPLETED102,previous103_preparation_STOP_pin=PREPARATION103_STOP,
        guarded_contract_qualification_pin=GUARDED_QUALIFIER,previous_status_STOP_pin=STATUS_STOP,
        previous103_STOP_reviewed=False,per_test_original_checkpoint_selected=False,reused_helper_contract_executions=21,
        previous_Native_STOP_pin=NATIVE_STOP,counter_support_status_pin=SUPPORT_STATUS,idle_support_pin=IDLE,
        counter_qualification_pin=COUNTER_QUALIFIER,counter_two_queries_pin=COUNTER_REAL,
        previous_Native_STOP_reviewed=False,counter_code_qualification_selected=False,
        counter_role='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False,diagnostic_parent_connection_selected=False,
        native_timing_connected=False,acquisition_phase_connection_selected=False,metadata_entry_pressure_connection_selected=False)
    stage='admission'
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context)
        out['metadata_entry_pressure_connection_selected']=type(q.entry_early_binding) is m.entry_pressure.Binding and q.entry_binding.pacer.checkpoint is q.reader.checkpoint
        stage='anchor'
        legacy,base,names,expected,exe,required,extras,baseline,added,healthy,healthy_body,stop=anchor(q)
        stage='selection';binding=p.v.identity(names,expected,exe);plan=progress(q,legacy,base,names,required,binding,extras,baseline,added);index,name=g.old.select(plan,names)
        stage='contract_tests'
        with context.scope('contract_tests'):
            out['runtime_contract_executions'],out['contract_checkpoint_statistics']=contracts((legacy,plan,names,required,extras,baseline,added,healthy,healthy_body),stop,q)
        out['per_test_original_checkpoint_selected']=True
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),scope_added_nineteen_pins=list(added.values()),
            compound_anchor_verified_without_body_reexecution=True,scope_budget=budget(required,baseline,added),
            previous_Native_STOP_reviewed=True,counter_code_qualification_selected=True,previous103_STOP_reviewed=True)
        stage='final_fresh_preparation'
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p317-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p317-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p317-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,acquisition_phase_connection_selected=type(held) is profile.InputLocks,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out['original_parent_capture_adapter_selected']=isinstance(capture,m.m.support.candidate.Capture)
            out['diagnostic_parent_connection_selected']=type(parent) is connection.ParentConnection and type(capture) is m.a.Capture
            out['native_timing_connected']=isinstance(held,connection.TimedInputLocks)
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context);held.mark('after_parent')
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=review.construct(Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);m.job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);out['failure_diagnostic']=m.diagnostic(error,stage);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:
            out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
            if hasattr(q,'contract_checkpoint_statistics'):out['contract_checkpoint_statistics']=q.contract_checkpoint_statistics
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            closed_attempt(doc)
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan,baseline,added)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==EXECUTED and doc['monotonic_binding_policy']==review.policy()
                    and doc['compound_anchor_pin']==ANCHOR and doc['reused_retained_contract_executions']==1486
                    and doc['retained_contract_qualification_pin']==RETAINED_QUALIFIER
                    and doc['metadata_entry_pressure_connection_selected'] is True,
                    'LIGHT_FULL_FRESH_CURRENT_CONTRACTS_NOT_REPLAY')
                leading_contract(doc['preparation_IO'])
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
    sys.modules.setdefault('resume_completed102_guarded_contract_runtime',sys.modules[__name__])
    raise SystemExit(main())
