"""P215 안정된 원장에서 다음 exact-one 실행. 원 본문/소스/보호 검사를 유지.

한 호출은 한 사례이며 완료 원장을 소비한다. 실패 시 같은 body 자동 재시도
없음. source component와 overall state를 분리하고 정리/검증 뒤에만 성공한다.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import close_borrowed_runtime_pair as pair
import verify_locked_pair_progress as verified
import borrowed_locked_streams as borrowed

p=pair.p;a=pair.a;old=pair.runner;observation=pair.observation
SELF='tools/p09/resume_generic_locked_runtime.py'
TEST='tools/p09/tests/test_generic_locked_runtime.py'
EXTRAS=(*old.EXTRAS,pair.SELF,pair.TEST,SELF,TEST)
SCHEMA='hwpx-agent.p09-generic-locked-runtime-pair/v1'
PASS='PASS_EXACT_R07_GENERIC_LOCKED_RUNTIME_PAIR_NOT_WHOLE_OR_GATE'
LIGHT='PASS_GENERIC_LOCKED_RUNTIME_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p215-case-([0-9]{3})-run([0-9]{3})\.v1\.json')


def require(ok,code):p.require(ok,'GENERIC_'+code)


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);own=component['source_frame']['handles'];dup=own['borrowed_byte_streams']
    require(n==1488 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['byte_stream_pathname_reopens']==0
        and component['source_frame']['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306), 'EXACT_NATIVE_STREAM_AND_HELD_CLEANUP')


def advance(legacy,base,names,index):
    selected,name=old.select(base,names)
    require(type(index) is int and index==selected,'EXACT_RECOMPUTED_NEXT_NOT_ARBITRARY')
    return a.merge(legacy,base,names,[name])


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,_=old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['selected_test_index']==index and doc['selected_test_name']==names[index-1]
        and doc['binding']==binding and doc['prior_runtime_plan']==base
        and doc['case_receipt_pin']==pin and doc['resource_stop_reason'] is None
        and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes'],
        'ONLY_COMPLETE_ERROR_FREE_OVERALL_RECORD')
    native_pair(doc['closing_component'],body,pin,required,binding,extras)
    require(body['task']==f'p204-r07-case-{index:03}-tests'
        and doc['runtime_plan']==advance(legacy,base,names,index)
        and doc['accepted_exact_product_body_count']==1,'EXACT_TASK_AND_ADVANCED_QUEUE')
    return doc['runtime_plan']


def anchor(q):
    for pin in (verified.PAIR,pair.SOURCE,pair.BODY,old.PRIOR,a.documents.CLOSED,p.b.BASE_PREP,p.m.PARENT):
        require(q.pin(pin['path'])==pin,'IMMUTABLE13_ANCHOR_PINS')
    proof=q.json(verified.PAIR['path']);source=q.json(pair.SOURCE['path']);body=q.json(pair.BODY['path'])
    prior=q.json(old.PRIOR['path']);native=q.json(a.documents.CLOSED['path'])
    prep=q.json(p.b.BASE_PREP['path']);compiled=q.json(p.m.PARENT['path'])
    expected=p.v.pins(prep['whole_inputs']);names=compiled['source_test_names'];exe=compiled['compiled_test_executable_pin']
    earlier=p.v.pins(native['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
    earlier.update({n:q.pin(n) for n in (a.SELF,a.TEST,old.SELF,old.TEST)})
    old_extra={n:q.pin(n) for n in old.EXTRAS}
    plan=pair.qualify(source,body,prior,names,expected,exe,earlier,old_extra)
    require(proof['schema_version']==pair.SCHEMA and proof['state']==pair.PASS and proof['runtime_plan']==plan
        and proof['resource_stop_reason'] is None and proof['resource_watcher_cleanup_confirmed'] is True
        and proof['IO']['finished'] is True and proof['IO']['bound_inputs']==proof['IO']['final_fresh_hashes']==25
        and proof['pair_consumer_pins']==[q.pin(n) for n in (pair.SELF,pair.TEST)], 'REVALIDATED13_ANCHOR')
    rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and p.b.s.inputs.rust_inputs(p.c.ROOT,q.resources.checkpoint_io)==rust,'LIVE_RUST785_SET')
    extras={n:q.pin(n) for n in EXTRAS}
    required={**earlier,**{n:extras[n] for n in (pair.SELF,pair.TEST,SELF,TEST)}}
    require(len(required)==1488 and all(required[n]==pin for n,pin in extras.items()),'FULL1484_PLUS_NEW4_SCOPE')
    return prior['legacy_plan'],plan,names,expected,exe,required,extras


def progress(q,legacy,base,names,required,binding,extras):
    files=sorted((p.c.ROOT/p.DIR).glob('p215-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_RECORDS')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_RECORD_FILENAME')
        index=int(match[1]);doc=q.json(path.relative_to(p.c.ROOT).as_posix())
        if doc['state']!=PASS:
            require(doc['state']=='FAILED_NOT_ACCEPTED','CLOSED_FAILURE_STATE')
            # 실행 요청 이후 실패는 검사/정리 없이 반복하지 않는다. 정상/비정상 body 모두 보존.
            require(doc.get('product_worker_invocation_requested') is not True,'INSPECT_FAILED_ACTUAL_BEFORE_RESUME')
            continue
        require(index==doc['selected_test_index'],'RECORD_INDEX')
        body_path=doc['case_receipt_pin']['path'];pin=q.pin(body_path)
        require(pin==doc['case_receipt_pin'],'UNCHANGED_BODY_RECEIPT');body=q.json(body_path)
        plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_generic_locked_runtime as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==16 and not result.skipped,'CONTRACT16')
    return 16


def complete(out,owner,candidate,validate):
    # 성공을 임시로 out에 기록하지 않는다. 정리·관측·최종 검증 뒤에만 publish.
    p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
    if owner.reason or not out.get('resource_watcher_cleanup_confirmed') or out.get('error_code'):
        out['state']='FAILED_NOT_ACCEPTED';return
    if candidate is None:return
    proposed={**out,**candidate}
    try:validate(proposed)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));return
    out.update(candidate)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light')
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=999,'CWD_RUN')
    light_path=root/f'{p.DIR}/p215-generic-light-run{args.run:03}.v1.json'
    destination=light_path if args.mode=='light' else root/f'{p.DIR}/p215-admission-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ADMISSION_RECEIPT')
    context=observation.Context();owner=observation.Resources(context);q=meta=frame=None;candidate=None;body=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        product_worker_invocation_requested=False,accepted_exact_product_body_count=0,original_successful_bodies_not_reexecuted=True)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        legacy,base,names,expected,exe,required,extras=anchor(q);binding=p.v.identity(names,expected,exe)
        plan=progress(q,legacy,base,names,required,binding,extras);index,name=old.select(plan,names)
        with context.scope('contract_tests'):out['generic_contract_tests_passed']=contracts((legacy,plan,names))
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            fixed13_anchor=verified.PAIR,extra_frame_controller_pins=list(extras.values()))
        if args.mode=='light':
            q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p215-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_RECORD')
            require(not list((root/p.DIR/'cases').glob(f'p215-case-{index:03}-run*.json')),'NO_EXISTING_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p215-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            frame=p.frames.Frame(p.frames.Registry(),required,owner.checkpoint_io,
                held=borrowed.BorrowedInputLocks(root,owner.checkpoint_io))
            counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            with context.scope('metadata_hash'):frame.acquire()
            out.update(product_worker_invocation_requested=True,case_receipt_path=body_path.relative_to(root).as_posix())
            code=p.run_parent(frame,index,name,body_path,context,binding)
            meta=p.qualification.Reader(owner,context);counter.metadata.append(meta.reader);context.reader=counter
            body=meta.json(body_path.relative_to(root).as_posix());pin=meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_product_child_executed']=True if body.get('actual_product_child_executed') is True else None
            require(code==0,'ORIGINAL_PARENT_NOT_ACCEPTED');p.validate_parent(body,name,binding,required);meta.finish()
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component)
            candidate=dict(state=PASS,runtime_plan=advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out.update(state='FAILED_NOT_ACCEPTED',error_code='P215_FRAME_CLEANUP_FAILED');candidate=None
            except (ValueError,OSError):out.update(state='FAILED_NOT_ACCEPTED',error_code='P215_FRAME_CLEANUP_FAILED');candidate=None
            out['terminal_source_frame']=frame.summary()
        if q is not None:out['preparation_IO']=q.summary()
        out['metadata_observation']=observation.summary(owner)
        def validate(proposed):
            if proposed['state']==PASS:
                component=proposed['closing_component']
                component.update(resource_stop_reason=proposed['resource_stop_reason'],
                    resource_watcher_cleanup_confirmed=proposed['resource_watcher_cleanup_confirmed'])
                record(proposed,body,pin,required,binding,extras,names,legacy,plan)
            else:require(proposed['state']==LIGHT and proposed['preparation_IO']['finished'] is True,'LIGHT_FINAL_FRESH')
        complete(out,owner,candidate,validate)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','generic_contract_tests_passed','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':raise SystemExit(main())
