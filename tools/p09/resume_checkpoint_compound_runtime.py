"""P260: case090 결합 증거를 원 판정으로 소비하고 다음 exact-one 실행.

P255/P257~P259 불변. 원1545+현재helper10=1555 입력/두읽기/guard 유지.
미검토 실패는 차단, 통과 body 재실행 없음. synthetic 계약은 실제 PASS 아님.
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
import accept_checkpoint_stop_compound as compound
m=compound.m;p=m.p;g=m.g;r=m.r;review=compound.review
SELF='tools/p09/resume_checkpoint_compound_runtime.py'
TEST='tools/p09/tests/test_checkpoint_compound_runtime.py'
COMPOUND=dict(path=p.DIR+'/p259-case090-compound-run01.v1.json',bytes=457284,
    sha256='fb23580ab7ba0a0dccf6caaf0e19c693e6d12be0705c51f35d0711443a19c3ea')
NEW=(*compound.closing.EXTRAS,compound.SELF,compound.TEST,SELF,TEST)
N=1555
SCHEMA='hwpx-agent.p09-checkpoint-compound-runtime-pair/v1'
PASS='PASS_EXACT_R07_CHECKPOINT_COMPOUND_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_CHECKPOINT_COMPOUND_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p260-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=24


def require(ok,code):m.require(ok,'COMPOUND_RUNTIME_'+code)


def closed_attempt(doc):
    require(doc.get('schema_version')==SCHEMA and doc.get('state') in (PASS,LIGHT)
        and doc.get('error_code') is None and doc.get('resource_stop_reason') is None
        and doc.get('resource_watcher_cleanup_confirmed') is True,'OWN_CLOSED_NOT_FAILED_OR_FOREIGN')


def budget(required,original,added):
    require(len(original)==1545 and len(required)==N and len(added)==10
        and set(added)==set(NEW) and not set(original)&set(added) and required=={**original,**added}
        and required[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in added.values())<=1048576,
        'ORIGINAL1545_PLUS_TEN_ONLY')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(3*N+306)/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_FITS_ORIGINAL600')
    return dict(full_runtime_inputs=N,new_inputs=10,native_rate=20,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)


def anchor(q):
    legacy,oldbase,names,expected,exe,original,old_extras,healthy,healthy_body,historical,historical_body=m.anchor(q)
    binding=p.v.identity(names,expected,exe)
    prior83,root=compound.before_stop(q,legacy,oldbase,names,original,binding,old_extras)
    body=m.review.bound_json(q,review.BODY_PIN);source=m.review.bound_json(q,compound.SOURCE_PIN)
    prior=m.review.bound_json(q,COMPOUND);sealed_review=m.review.bound_json(q,compound.closing.REVIEW_PIN)
    require(sealed_review['schema_version']==review.SCHEMA and sealed_review['state']==review.PASS
        and sealed_review['review']==review.review(root,body) and sealed_review['resource_stop_reason'] is None
        and sealed_review['resource_watcher_cleanup_confirmed'] is True and sealed_review['IO']['finished'] is True
        and sealed_review['IO']['bound_inputs']==sealed_review['IO']['final_fresh_hashes']==15,
        'UNCHANGED_LITERAL_STOP_REVIEW')
    require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'PRESERVED_ZERO_BODY_PLACEHOLDER')
    added={name:q.pin(name) for name in NEW};source_extra={name:added[name] for name in compound.closing.EXTRAS}
    checked=compound.combine(root,body,source,names,expected,exe,original,source_extra)
    base=compound.advance(legacy,prior83,names)
    require(prior['schema_version']==compound.SCHEMA and prior['state']==compound.PASS
        and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
        and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==151
        and prior['IO']['read_passes']==314 and prior['compound_contract_tests_passed']==26
        and prior['compound']==checked and prior['prior_runtime_plan']==prior83 and prior['runtime_plan']==base
        and p.v.pins(prior['original_source_required_pins'])==original
        and p.v.pins(prior['extra_post_source_controller_pins'])==source_extra
        and p.v.pins(prior['compound_consumer_pins'])=={n:added[n] for n in (compound.SELF,compound.TEST)}
        and prior['original_failed_root_pin']==review.ROOT_PIN and prior['original_stopped_parent_pin']==review.BODY_PIN
        and prior['separate_source_frame_pin']==compound.SOURCE_PIN,'EXACT_COMPOUND84_RECOMPUTED_NOT_STATE_TEXT')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR).glob('p259-*.v1.json'))==[COMPOUND['path'].split('/')[-1]],
        'UNKNOWN_NEW_COMPOUND_ATTEMPT_BLOCKS')
    extras={**old_extras,**added};required={**original,**added};require(len(extras)==88,'ALL_CURRENT_CONTROLLERS88')
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
            separate_pathname_reopens=0,regular_file_count=N,directory_count=306),'ALL1555_NATIVE_IDENTITIES_AND_CLOSE')
    m.r.h.h.pressure_contract(h['native_open_backpressure']);m.lower_contract(h)


def early_contract(row):
    require(row['early_source_warning_CPU_percent']==90 and row['cool_distinct_samples']==2
        and row['maximum_pause_windows']==8 and all(row[k] is True for k in
        ('original_guard_called_before_pressure','original_hard_CPU_RAM600_guards_preserved','existing_owner_samples_only'))
        and all(row[k] is False for k in ('new_sampler_or_thread_started','source_byte_reads_or_identity_checks_skipped',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_GUARDS_EARLY_SOURCE_ONLY')


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['compound_anchor_pin']==COMPOUND and doc['preserved_case090_stop_pin']==review.ROOT_PIN
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['binding']==binding and doc['prior_runtime_plan']==base and doc['case_receipt_pin']==pin
        and doc['original_retained_contract_executions']==450 and doc['own_queue_contract_tests_passed']==COUNT
        and doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['old_contract_scope']=='ORIGINAL1545_NO_BODY_REEXECUTION'
        and doc['new_contract_scope']=='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1555'
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
    early_contract(doc['early_source_checkpoint']);native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    old={n:p for n,p in required.items() if n not in NEW};added={n:required[n] for n in NEW}
    require(doc['scope_budget']==budget(required,old,added)
        and body['task']==f'p204-r07-case-{index:03}-tests' and doc['accepted_exact_product_body_count']==1
        and doc['runtime_plan']==g.advance(legacy,base,names,index),'FULL_SCOPE_AND_EXACT_ONE_ADVANCE')
    return doc['runtime_plan']


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p260-admission-run*.v1.json'),*folder.glob('p260-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p260-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p260-case-{index:03}-run{number:03}.json','BODY_NAMESPACE')
        body=m.review.bound_json(q,pin);plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy,healthy_body,required,extras,original,old_extras,historical,historical_body):
    require(m.contracts(fixtures,healthy,healthy_body,original,old_extras,historical,historical_body)==18,'ORIGINAL450_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as f
    import test_checkpoint_compound_runtime as tests
    legacy,current,names,stop=fixtures;synthetic=copy.deepcopy(healthy)
    synthetic.update(original_retained_contract_executions=450,own_queue_contract_tests_passed=COUNT,
        synthetic_following_queue_contract_tests_passed=COUNT,old_contract_scope='ORIGINAL1545_NO_BODY_REEXECUTION',
        new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1555',preserved_case090_stop_pin=review.ROOT_PIN,
        early_source_guard_connected=True,original_parent_capture_adapter_selected=True,
        original_successful_bodies_not_reexecuted=True,actual_product_child_executed=True,packed_root_writer_selected=True,
        early_source_checkpoint=review.EarlySourceCheckpoint(lambda:None,None).summary(),
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
        and second.wasSuccessful() and second.testsRun==COUNT and not second.skipped,'CURRENT24_AND_FOLLOWING24')
    return 498


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p260-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
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
    destination=p.c.ROOT/f'{p.DIR}/p260-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=COMPOUND,
        preserved_case090_stop_pin=review.ROOT_PIN,original_retained_contract_executions=450,
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        old_contract_scope='ORIGINAL1545_NO_BODY_REEXECUTION',new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1555',
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy())
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
            destination=p.c.ROOT/f'{p.DIR}/p260-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p260-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p260-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=m.lower.InputLocks(p.c.ROOT,early,owner)
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
            meta=m.Reader(owner,context);counter.metadata.append(meta.reader)
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);r.stats_contract(writes[0],pin);meta.finish()
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
                if not frame.close():out['error_code']='COMPOUND_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='COMPOUND_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
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
            else:require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True,'LIGHT_ALL_FRESH')
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
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='COMPOUND_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','runtime_contract_executions','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_checkpoint_compound_runtime',sys.modules[__name__])
    raise SystemExit(main())
