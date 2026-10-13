"""P265: case091 독립 결합 수용 이후 원 전체1555+새8의 exact-one 실행.

수용 코드와 원 실패 불변. 생성 중 누적 관측 연결을 명시 사용하고 원 보호·
두 byte 읽기·identity·정리 유지. 미검토 실패 차단, 통과 본체 재실행 없음.
"""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import accept_observation_failure_compound as compound
previous=compound.old;m=previous.m;p=m.p;g=m.g;r=m.r
review=compound.review;early_review=previous.review
SELF='tools/p09/resume_monotonic_compound_runtime.py'
TEST='tools/p09/tests/test_monotonic_compound_runtime.py'
COMPOUND=dict(path=p.DIR+'/p264-case091-compound-run01.v1.json',bytes=473724,
    sha256='2e638cd49227bce9154690cddd41a65b736b31be6e97260f891ad869bed93827')
NEW=(*compound.closing.EXTRAS,compound.SELF,compound.TEST,SELF,TEST)
N=1563
SCHEMA='hwpx-agent.p09-monotonic-compound-runtime-pair/v1'
PASS='PASS_EXACT_R07_MONOTONIC_COMPOUND_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_MONOTONIC_COMPOUND_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p265-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=30
TOTAL=558


def require(ok,code):m.require(ok,'MONOTONIC_RUNTIME_'+code)


def closed_attempt(doc):
    require(doc.get('schema_version')==SCHEMA and doc.get('state') in (PASS,LIGHT)
        and doc.get('error_code') is None and doc.get('resource_stop_reason') is None
        and doc.get('resource_watcher_cleanup_confirmed') is True
        and type(doc.get('runtime_contract_executions')) is int and doc['runtime_contract_executions']==TOTAL
        and doc.get('receipt_serialization_policy')==r.policy()
        and doc.get('monotonic_binding_policy')==review.policy(),'OWN_CLOSED_NOT_FAILED_OR_FOREIGN')


def budget(required,original,added):
    require(len(original)==1555 and len(required)==N and len(added)==8
        and set(added)==set(NEW) and not set(original)&set(added) and required=={**original,**added}
        and required[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in added.values())<=1048576,
        'ORIGINAL1555_PLUS_EIGHT_ONLY')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(3*N+306)/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_FITS_ORIGINAL600')
    return dict(full_runtime_inputs=N,new_inputs=8,native_rate=20,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)


def anchor(q):
    legacy,prior84,names,expected,exe,original,old_extras,*unused=previous.anchor(q)
    healthy,healthy_body,historical,historical_body=unused[-4:]
    folder=p.c.ROOT/p.DIR
    compound.inventory([x.name for x in folder.glob('p260-*.v1.json')],
        [x.name for x in (folder/'cases').glob('p260-*.json')])
    root=m.review.bound_json(q,review.ROOT_PIN);body=m.review.bound_json(q,review.BODY_PIN)
    source=m.review.bound_json(q,compound.SOURCE_PIN);qualified=m.review.bound_json(q,compound.closing.REVIEW_PIN)
    prior=m.review.bound_json(q,COMPOUND);light=m.review.bound_json(q,review.LIGHT_PIN);previous.closed_attempt(light)
    require(root['prior_runtime_plan']==prior84 and light['prior_runtime_plan']==prior84
        and light['state']==previous.LIGHT and light['runtime_contract_executions']==498,'EXACT_PRIOR84_FAILURE_AND_LIGHT')
    checked=review.review(root,body)
    require(qualified['schema_version']==review.SCHEMA and qualified['state']==review.PASS
        and qualified['review']==checked and qualified['resource_stop_reason'] is None
        and qualified['resource_watcher_cleanup_confirmed'] is True and qualified['IO']['finished'] is True
        and qualified['IO']['bound_inputs']==qualified['IO']['final_fresh_hashes']==15
        and qualified['small_real_IO']['finished'] is True
        and qualified['small_real_IO']['bound_inputs']==qualified['small_real_IO']['final_fresh_hashes']==3
        and qualified['observation_contract_tests_passed']==36,'IMMUTABLE_QUALIFIED_OBSERVER_REPAIR')
    added={n:q.pin(n) for n in NEW};source_extra={n:added[n] for n in compound.closing.EXTRAS}
    combined=compound.combine(root,body,source,names,expected,exe,original,source_extra)
    base=compound.advance(legacy,prior84,names)
    require(prior['schema_version']==compound.SCHEMA and prior['state']==compound.PASS
        and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
        and prior['IO']['finished'] is True and prior['IO']['read_passes']==343
        and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==165
        and prior['compound_contract_tests_passed']==26 and prior['compound']==combined
        and prior['prior_runtime_plan']==prior84 and prior['runtime_plan']==base
        and p.v.pins(prior['original_source_required_pins'])==original
        and p.v.pins(prior['extra_post_source_controller_pins'])==source_extra
        and p.v.pins(prior['compound_consumer_pins'])=={n:added[n] for n in (compound.SELF,compound.TEST)}
        and prior['original_failed_root_pin']==review.ROOT_PIN and prior['original_body_pin']==review.BODY_PIN
        and prior['separate_source_frame_pin']==compound.SOURCE_PIN,'EXACT_RECOMPUTED_COMPOUND85_NOT_STATE_TEXT')
    for generation,pin in (('p262',compound.closing.REVIEW_PIN),('p263',compound.SOURCE_PIN),('p264',COMPOUND)):
        require(sorted(x.name for x in folder.glob(generation+'-*.v1.json'))==[pin['path'].split('/')[-1]],
            'UNKNOWN_NEW_REVIEW_SOURCE_OR_COMPOUND_ATTEMPT_BLOCKS')
    extras={**old_extras,**added};required={**original,**added}
    require(len(original)==1555 and len(old_extras)==88 and len(extras)==96,'ALL_ORIGINAL_AND_CURRENT_CONTROLLERS96')
    budget(required,original,added)
    return legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,historical,historical_body


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+306
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==305
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=306),'ALL1563_NATIVE_IDENTITIES_AND_CLOSE')
    m.r.h.h.pressure_contract(h['native_open_backpressure']);m.lower_contract(h)


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
        and doc['original_retained_contract_executions']==498 and doc['own_queue_contract_tests_passed']==COUNT
        and doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['old_contract_scope']=='ORIGINAL1555_NO_BODY_REEXECUTION'
        and doc['new_contract_scope']=='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1563'
        and type(doc['runtime_contract_executions']) is int and doc['runtime_contract_executions']==TOTAL
        and doc['receipt_serialization_policy']==r.policy() and doc['monotonic_binding_policy']==review.policy()
        and doc['aggregate_post_reader_connection_verified'] is True
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
    job_contract(body);early_contract(doc['early_source_checkpoint']);native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    old={n:p for n,p in required.items() if n not in NEW};added={n:required[n] for n in NEW}
    require(doc['scope_budget']==budget(required,old,added)
        and body['task']==f'p204-r07-case-{index:03}-tests' and doc['accepted_exact_product_body_count']==1
        and doc['runtime_plan']==g.advance(legacy,base,names,index),'FULL_SCOPE_AND_EXACT_ONE_ADVANCE')
    return doc['runtime_plan']


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p265-admission-run*.v1.json'),*folder.glob('p265-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p265-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p265-case-{index:03}-run{number:03}.json','BODY_NAMESPACE')
        body=m.review.bound_json(q,pin);plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy,healthy_body,required,extras,original,old_extras,historical,historical_body):
    legacy_original={n:pin for n,pin in original.items() if n not in previous.NEW}
    legacy_extras={n:pin for n,pin in old_extras.items() if n not in previous.NEW}
    require(len(legacy_original)==1545 and len(legacy_extras)==78,'EXPLICIT_OLD_CONTRACT_DOMAINS')
    require(previous.contracts(fixtures,healthy,healthy_body,original,old_extras,legacy_original,legacy_extras,
        historical,historical_body)==498,'ORIGINAL498_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as f
    import test_monotonic_compound_runtime as tests
    legacy,current,names,stop=fixtures;synthetic=copy.deepcopy(healthy)
    synthetic.update(original_retained_contract_executions=498,own_queue_contract_tests_passed=COUNT,
        synthetic_following_queue_contract_tests_passed=COUNT,old_contract_scope='ORIGINAL1555_NO_BODY_REEXECUTION',
        new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1563',preserved_case091_failure_pin=review.ROOT_PIN,
        runtime_contract_executions=TOTAL,receipt_serialization_policy=r.policy(),monotonic_binding_policy=review.policy(),
        aggregate_post_reader_connection_verified=True,early_source_guard_connected=True,original_parent_capture_adapter_selected=True,
        original_successful_bodies_not_reexecuted=True,actual_product_child_executed=True,packed_root_writer_selected=True,
        early_source_checkpoint=early_review.EarlySourceCheckpoint(lambda:None,None).summary(),
        scope_budget=budget(required,original,{n:required[n] for n in NEW}))
    with patch.object(f,'m',sys.modules[__name__]),patch.object(f,'FIXTURES',(fixtures,synthetic,healthy_body,required,extras)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_RUNTIME_CONTRACT_THREAD')):
        first=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        index,_=g.old.select(current,names);following=g.advance(legacy,current,names,index)
        with patch.object(f,'FIXTURES',((legacy,following,names,stop),synthetic,healthy_body,required,extras)):
            second=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(first.wasSuccessful() and first.testsRun==COUNT and not first.skipped
        and second.wasSuccessful() and second.testsRun==COUNT and not second.skipped,'CURRENT30_AND_FOLLOWING30')
    return TOTAL


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p265-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),bytes=written,
        sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light');ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p265-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=COMPOUND,
        preserved_case091_failure_pin=review.ROOT_PIN,original_retained_contract_executions=498,
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        old_contract_scope='ORIGINAL1555_NO_BODY_REEXECUTION',new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1563',
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False)
    try:
        owner.admit();q=m.Reader(owner,context)
        legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,historical,historical_body=anchor(q)
        binding=p.v.identity(names,expected,exe);plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        with context.scope('contract_tests'):
            out['runtime_contract_executions']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),healthy,healthy_body,
                required,extras,original,old_extras,historical,historical_body)
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),compound_anchor_verified_without_body_reexecution=True,
            scope_budget=budget(required,original,{n:required[n] for n in NEW}))
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p265-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p265-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p265-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=m.lower.InputLocks(p.c.ROOT,early,owner)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            with context.scope('metadata_hash'):frame.acquire()
            capture=m.capture_for(frame,writes,index,name,binding)
            out['original_parent_capture_adapter_selected']=type(capture) is m.support.candidate.Capture
            with patch.object(p,'RAW_DUMP',capture.writer):code=p.run_parent(frame,index,name,body_path,context,binding)
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            meta=review.construct(m.Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:out['preparation_IO']=q.summary()
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==TOTAL and doc['monotonic_binding_policy']==review.policy(),
                    'LIGHT_ALL_FRESH_AND558')
                m.metadata_contract(doc['preparation_IO'])
        g.complete(out,owner,proposed,validate)
        if capture is not None and capture.pending:
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
    sys.modules.setdefault('resume_monotonic_compound_runtime',sys.modules[__name__])
    raise SystemExit(main())
