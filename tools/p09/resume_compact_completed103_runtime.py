"""P320: qualifiedcompact97 경계를 runtime에 연결; 기존1644 + reviewer2 + runtime2 =1648.
현재code83 live/final-fresh, oldguard78 qualified 재사용(실행횟수에합산안함).
새current100+following100은200실제검사/각전후원checkpoint. 원두전체byte/Native/Job/600/720 보존.
이미수용한 본문 재실행/실패승격/새threshold/읽기축소 없음.
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
import resume_completed102_guarded_contract_runtime as old
import review_compact_completed103_anchor as compact
m=old.m;p=old.p;g=old.g;r=old.r
accepted=old.accepted;leading=old.leading;inner=old.inner;counter=old.counter;guarded=old.guarded
profile=old.profile;connection=old.connection;review=old.review;early_review=old.early_review
Reader=old.Reader
SELF='tools/p09/resume_compact_completed103_runtime.py'
TEST='tools/p09/tests/test_compact_completed103_runtime.py'
ANCHOR=old.ANCHOR;RETAINED_QUALIFIER=old.RETAINED_QUALIFIER;INNER_QUALIFIER=old.INNER_QUALIFIER
FROZEN66=old.FROZEN66;FROZEN70=old.FROZEN70;FROZEN75=old.FROZEN75
NATIVE_STOP=old.NATIVE_STOP;SUPPORT_STATUS=old.SUPPORT_STATUS;IDLE=old.IDLE
COUNTER_QUALIFIER=old.COUNTER_QUALIFIER;COUNTER_REAL=old.COUNTER_REAL
COMPLETED102=old.COMPLETED102;PREPARATION103_STOP=old.PREPARATION103_STOP
GUARDED_QUALIFIER=old.GUARDED_QUALIFIER;STATUS_STOP=old.STATUS_STOP
COMPACT_QUALIFIER={"path":"implementation/p09/evidence/locked-r07/p318-compact-checkpoint-actual103-accepted-run02.v1.json","bytes":71816,"sha256":"8ad8c1da2fc26e4bd873e0c73b75d7e834fbf66ae519521120f0a993dc791c07"}
COMPACT_STATUS={"path":"implementation/p09/evidence/locked-r07/p319-compact103-accepted-status-doc-r0126-run01.v1.json","bytes":71372,"sha256":"5804600b10201fc9c8be08b48fa62f230532a5282619bc2e6f94ce56189b4174"}
COMPACT_CODE=[{"path":"tools/p09/review_compact_completed103_anchor.py","bytes":11588,"sha256":"f7ef6580d7e6982aaaa3e9753aa1a376a1f27628e8413d08a0d873ba3f5efe21"},{"path":"tools/p09/tests/test_compact_completed103_anchor.py","bytes":3454,"sha256":"b3f62d89d71ec9820f518c399c7de3406815f655a2b02c3b766002aef43c3624"}]
FROZEN83=compact.FROZEN81+COMPACT_CODE
NEW=(compact.SELF,compact.TEST,SELF,TEST)
N=1648
DIRECTORIES=308
SCHEMA='hwpx-agent.p09-compact-completed103-runtime-pair/v1'
PASS='PASS_EXACT_R07_COMPACT_COMPLETED103_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_COMPACT_COMPLETED103_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p320-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=100
EXECUTED=2*COUNT

def require(ok,code):m.require(ok,'COMPACT103_RUNTIME_'+code)

def budget(required,baseline,added):
    require(len(baseline)==1644 and len(required)==N and len(added)==4 and list(added)==list(NEW)
        and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in baseline.values())==120516712
        and sum(x['bytes'] for x in added.values())<=1048576,'ALL_PRIOR1644_PLUS_FOUR_NOT_SUBSET')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_UNCHANGED600')
    return dict(full_runtime_inputs=N,baseline_full_source_inputs=1644,new_inputs=4,
        actual_ancestor_directory_count=DIRECTORIES,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_new_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)

def anchor(q):
    fixtures=compact.load(q);prior,root,body,names,expected,legacy,current81,prior_body=fixtures
    plan,baseline,old_extras,old_baseline,old_added=compact.validate(*fixtures)
    bound=m.m.review.bound_json
    qualification=bound(q,COMPACT_QUALIFIER);status=bound(q,COMPACT_STATUS)
    require(qualification['state']==compact.PASS and qualification['runtime_plan']==plan
        and qualification['root_pin']==compact.ROOT and qualification['body_pin']==compact.BODY
        and qualification['accepted_checkpoint_pin']==compact.PRIOR and qualification['policy']==compact.policy()
        and qualification['actually_executed_mutation_contracts']==26
        and qualification['resource_stop_reason'] is None and qualification['resource_watcher_cleanup_confirmed'] is True
        and qualification['IO']['finished'] is True and qualification['IO']['bound_inputs']==qualification['IO']['final_fresh_hashes']==92
        and qualification['IO']['read_passes']==184 and qualification['product_or_Native_reexecuted'] is False
        and qualification['current81_Native_covered_code_pins']==compact.FROZEN81
        and qualification['new2_metadata_only_code_pins']==COMPACT_CODE,'QUALIFIED_COMPACT97_AND26_NO_REPLAY')
    require(status['state']=='PASS_EXACT97_COMPACT_CHECKPOINT_AND_R126_DOCUMENTS_NOT_WHOLE_OR_GATE'
        and status['runtime_plan']==plan and status['compact_accepted_checkpoint_qualification_pin']==COMPACT_QUALIFIER
        and status['resource_stop_reason'] is None and status['resource_watcher_cleanup_confirmed'] is True
        and status['IO']['finished'] is True and status['IO']['bound_inputs']==status['IO']['final_fresh_hashes']==97
        and status['current81_Native_covered_code_pins']==compact.FROZEN81
        and status['new2_metadata_only_code_pins']==COMPACT_CODE and status['contract_tests_reexecuted'] is False,
        'R126_NOT_FAILED_STATUS_AND_SAME97_SOURCE')
    current2={pin['path']:q.pin(pin['path']) for pin in COMPACT_CODE}
    require(list(current2.values())==COMPACT_CODE and list(current81.values())+list(current2.values())==FROZEN83,
        'ALL83_DISTINCT_CURRENT_PINS')
    # 변경되지 않은78계약은 actual103의254실행 및 독립qualification에 근거해 재사용한다.
    # 현재200실행에 더하지 않는다. 변경한 queue/classifier는100+100을 실행한다.
    old.closed_attempt(root)
    require(root['runtime_contract_executions']==254 and root['contract_checkpoint_statistics']['started_tests']==254
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True
        and all(baseline[pin['path']]==pin for pin in compact.FROZEN81),'FROZEN_OLD_GUARD78_QUALIFIED_NOT_EXECUTED_NOW')
    added={**current2,SELF:q.pin(SELF),TEST:q.pin(TEST)};required={**baseline,**added};extras={**old_extras,**added}
    directories={PurePosixPath('.')}
    for name in required:directories.update(PurePosixPath(name).parents)
    require(len(directories)==DIRECTORIES and len(extras)==181 and required=={**baseline,**added},
        'ALL1644_PLUS4_AND308_ANCESTORS_AND181_CONTROLLERS')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR).glob('p317-case-*-run*.v1.json'))==
        ['p317-case-103-run002.v1.json']
        and sorted(x.name for x in (p.c.ROOT/p.DIR/'cases').glob('p317-*.json'))==
        ['p317-case-103-run002.json'],'NO_UNKNOWN_PRIOR_P317_BODY_OR_REPLAY')
    budget(required,baseline,added)
    return legacy,plan,names,expected,p.m.EXE,required,extras,baseline,added,root,body,None

def guarded_contract(row,expected=EXECUTED):
    require(type(row) is dict and row['started_tests']==row['stopped_tests']==
        row['successful_before_test_checks']==row['successful_after_test_checks']==expected
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==2
        and row['original_unittest_results_preserved'] is True
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and row['original_guard_or_test_coverage_relaxed'] is False
        and row['test_results_are_not_product_acceptance'] is True,'EVERY_TEST_ORIGINAL_CHECKPOINT_NOT_ACCEPTANCE')

inner_contract=old.inner_contract
leading_contract=old.leading_contract
live_pins=old.live_pins

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
            separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'FULL1648_NATIVE_TWO_BYTE_AND_CLEANUP')
    m.m.r.h.h.pressure_contract(h['native_open_backpressure']);m.m.lower_contract(h)
    m.timing_contract(h['lock_timing_diagnostic']);profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)

def closed_attempt(d):
    require(type(d) is dict and d.get('schema_version')==SCHEMA and d.get('state') in (PASS,LIGHT),
        'CLOSED_SCHEMA_STATE_BEFORE_STATISTICS')
    guarded_contract(d['contract_checkpoint_statistics'])
    require(d['compact_qualification_pin']==COMPACT_QUALIFIER and d['compact_status_pin']==COMPACT_STATUS
        and d['compact_checkpoint_policy']==compact.policy()
        and d['compact_checkpoint_selected'] is True and d['reused_compact_contract_executions']==26
        and d['reused_original_guard_contract_executions']==78
        and d['reused_original_guard_qualification_root_pin']==compact.ROOT,
        'COMPACT_QUALIFIED_AND78_REUSED_NOT_EXECUTED')
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
        and doc['scope_added_four_pins']==list(added.values()) and doc['extra_frame_controller_pins']==list(extras.values())
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
    for path in sorted((*folder.glob('p320-light-run*.v1.json'),*folder.glob('p320-admission-run*.v1.json'))):
        closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    rows=sorted(folder.glob('p320-case-*-run*.v1.json'));require(len(rows)<=4096,'BOUNDED_NAMESPACE')
    plan=base
    for path in rows:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        d=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(d)
        require(d['selected_test_index']==index and d['case_receipt_pin']['path']==
            f'{p.DIR}/cases/p320-case-{index:03}-run{number:03}.json','FILENAME_BODY_IDENTITY')
        bp=d['case_receipt_pin'];body=m.m.review.bound_json(q,bp)
        plan=record(d,body,bp,required,binding,extras,names,legacy,plan,baseline,added)
    return plan

def contracts(fixtures,stop,q):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_compact_completed103_runtime as t
    statistics=None
    try:
        with guarded.bind(q.reader.checkpoint) as statistics, \
                patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
            for following in (False,True):
                with patch.object(t,'FIXTURES',fixtures),patch.object(t,'FOLLOWING',following):
                    rr=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                require(rr.wasSuccessful() and rr.testsRun==COUNT and not rr.skipped,'CURRENT100_AND_FOLLOWING100')
        row=statistics.summary();guarded_contract(row)
        require(unittest.TextTestRunner is guarded._ORIGINAL_RUNNER and guarded._ACTIVE is False,'ORIGINAL_RUNNER_RESTORED')
        return EXECUTED,row
    finally:
        q.contract_checkpoint_statistics=statistics.summary() if statistics is not None else None

def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p320-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
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
    destination=p.c.ROOT/f'{p.DIR}/p320-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=ANCHOR,
        retained_contract_qualification_pin=RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        previous_preparation_STOP_pin=inner.FAILURE,inner_metadata_qualification_pin=INNER_QUALIFIER,
        compact_qualification_pin=COMPACT_QUALIFIER,compact_status_pin=COMPACT_STATUS,
        compact_checkpoint_policy=compact.policy(),compact_checkpoint_selected=False,reused_compact_contract_executions=26,
        reused_original_guard_contract_executions=78,reused_original_guard_qualification_root_pin=compact.ROOT,
        completed102_anchor_pin=COMPLETED102,previous103_preparation_STOP_pin=PREPARATION103_STOP,
        guarded_contract_qualification_pin=GUARDED_QUALIFIER,previous_status_STOP_pin=STATUS_STOP,
        previous103_STOP_reviewed=False,per_test_original_checkpoint_selected=False,reused_helper_contract_executions=21,
        previous_Native_STOP_pin=NATIVE_STOP,counter_support_status_pin=SUPPORT_STATUS,idle_support_pin=IDLE,
        counter_qualification_pin=COUNTER_QUALIFIER,counter_two_queries_pin=COUNTER_REAL,
        previous_Native_STOP_reviewed=False,counter_code_qualification_selected=False,
        counter_role='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        own_queue_contract_tests_passed=0,synthetic_following_queue_contract_tests_passed=0,
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
        out['own_queue_contract_tests_passed']=COUNT
        out['synthetic_following_queue_contract_tests_passed']=COUNT
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),scope_added_four_pins=list(added.values()),
            compound_anchor_verified_without_body_reexecution=True,scope_budget=budget(required,baseline,added),
            previous_Native_STOP_reviewed=True,counter_code_qualification_selected=True,previous103_STOP_reviewed=True,compact_checkpoint_selected=True)
        stage='final_fresh_preparation'
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p320-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p320-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p320-case-{index:03}-run{args.run:03}.json';q.finish()
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
    sys.modules.setdefault('resume_compact_completed103_runtime',sys.modules[__name__])
    raise SystemExit(main())
