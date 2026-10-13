"""P213 P212 compound 큐를 소비하는 미실행 exact-one borrowed-frame 실행.

이미 수용된 1~12번을 건너뛴다. 원 c.run/GO/Job/환경/guard/정리와 입력 전후
전체 실제 읽기를 유지한다. 원 P208/P211/P212 파일은 수정하지 않는다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import accept_locked_runtime_candidate as accepted
import borrowed_locked_streams as borrowed

p=accepted.p;closing=accepted.closing;observation=accepted.observation
SELF='tools/p09/run_borrowed_runtime_r07_case.py'
TEST='tools/p09/tests/test_borrowed_runtime_case.py'
PRIOR=dict(path='implementation/p09/evidence/locked-r07/p212-case-012-compound-run02.v1.json',
    bytes=124287,sha256='e3659306fa6daa34531be0049a18117265124ef3509cbb44e79a2ebd9df3837d')
EXTRAS=(*p.EXTRAS,*closing.EXTRAS,accepted.SELF,accepted.TEST,SELF,TEST)


def require(ok,code):p.require(ok,'BORROWED_RUN_'+code)


def prior_scope(doc,names,expected,exe):
    require(doc['schema_version']==accepted.SCHEMA and doc['state']==accepted.PASS
        and doc['binding']==p.v.identity(names,expected,exe) and doc['compound_contract_tests_passed']==20
        and doc['original_failed_frame_pin']==accepted.review.FRAME and doc['original_stopped_parent_pin']==accepted.review.BODY
        and doc['separate_source_frame_pin']==accepted.documents.CLOSED,'EXACT_PREVIOUS_COMPOUND_BINDING')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==82
        and doc['actual_new_product_body_executed'] is False
        and doc['original_partial_post_hash_not_retroactively_promoted'] is True,'SEALED_CLEAN_COMPOUND_IO')
    plan=accepted.merge(doc['legacy_plan'],doc['prior_runtime_plan'],names,[names[11]])
    require(plan==doc['runtime_plan'] and plan['runtime_source_qualified_individual_cases']==12
        and plan['next_runtime_index']==13 and plan['runtime_successful_candidates_requiring_closing']==0,
        'RECOMPUTED12_QUEUE_NOT_OLD11_NEXT12')
    require(doc['compound']['selected_test_index']==12 and doc['compound']['selected_test_name']==names[11]
        and doc['compound']['compound_individual_case_qualified'] is True
        and doc['compound']['original_STOP_receipt_accepted'] is False
        and doc['compound']['original_partial_post_hash_completed'] is False,'STOP_NOT_RECLASSIFIED')
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[key] is False for key in ('full249_current_qualified','signed16_current_qualified','product_complete',
            'PC_freeze_resolved','whole1470_current_fresh_qualified')), 'NO_PRIOR_SCOPE_PROMOTION')
    return plan


def select(plan,names):
    index=plan['next_runtime_index']
    require(type(index) is int and 1<=index<=249 and plan['runtime_successful_candidates_requiring_closing']==0,
        'UNEXECUTED_NEXT_INDEX')
    name=names[index-1]
    require(name not in plan['runtime_qualified_test_names'] and not name.startswith(p.v.CORPUS_PREFIX),
        'NO_PASSED_BODY_REPEAT_OR_UNSUPPORTED_CORPUS')
    return index,name


def contracts(doc,names,expected,exe):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_borrowed_runtime_case as tests
    with patch.object(tests,'FIXTURES',(doc,names,expected,exe)), \
            patch('subprocess.Popen',side_effect=AssertionError('P213_NO_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P213_NO_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P213_NO_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'CONTRACT12')
    return 12


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light')
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p213-borrowed-frame-{args.mode}-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=meta=frame=None;body=None
    out=dict(schema_version=p.CLOSING_SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        borrowed_runner_generation='P213_CURRENT1484',actual_new_product_body_executed=False,
        actual_product_child_executed_field_scope='SOURCE_FRAME_CLOSING_COMPONENT',
        closing_component_did_not_execute_product_again=True,original_passed_bodies_not_reexecuted=True)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        require(q.pin(PRIOR['path'])==PRIOR,'SEALED_COMPOUND_PIN');prior=q.json(PRIOR['path'])
        expected,names,exe,runtime,fixture_inputs,helpers,base_scope=p.qualification.current_inputs(q)
        plan=prior_scope(prior,names,expected,exe)
        require(prior['compound_consumer_pins']==[q.pin(name) for name in (accepted.SELF,accepted.TEST)],
            'TESTED_COMPOUND_CONSUMERS_UNCHANGED')
        with context.scope('contract_tests'):out['borrowed_runtime_contract_tests_passed']=contracts(prior,names,expected,exe)
        index,name=select(plan,names);extra={n:q.pin(n) for n in EXTRAS}
        required=p.qualification.combine(base_scope,{}, {},extra);require(len(required)==1484,'ALL_ORIGINAL_PLUS_BORROWED_AND_QUEUE_CONTROLLERS')
        binding=p.v.identity(names,expected,exe)
        out.update(selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,prior_compound_pin=PRIOR,
            binding=binding,extra_frame_controller_pins=list(extra.values()))
        if args.mode=='light':
            q.finish();out['state']='PASS_BORROWED_EXACT_NEXT_CASE_SELECTION_NOT_ACTUAL_OR_GATE'
        else:
            existing=list((root/p.DIR/'cases').glob(f'p213-case-{index:03}-run*.json'))
            require(not existing,'INSPECT_EXISTING_CASE_BEFORE_ANY_REPEAT')
            body_path=root/f'{p.DIR}/cases/p213-case-{index:03}-run{args.run:02}.json'
            require(not body_path.exists(),'FRESH_PARENT_RECEIPT')
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            held=borrowed.BorrowedInputLocks(root,owner.checkpoint_io)
            frame=p.frames.Frame(p.frames.Registry(),required,owner.checkpoint_io,held=held)
            counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            with context.scope('metadata_hash'):frame.acquire()
            out.update(product_test_body_started=True,case_receipt_path=body_path.relative_to(root).as_posix())
            code=p.run_parent(frame,index,name,body_path,context,binding)
            meta=p.qualification.Reader(owner,context);counter.metadata.append(meta.reader);context.reader=counter
            body=meta.json(body_path.relative_to(root).as_posix());pin=meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_new_product_body_executed']=body.get('actual_product_child_executed',False)
            require(code==0,'ORIGINAL_PARENT_NOT_ACCEPTED');p.validate_parent(body,name,binding,required)
            meta.finish();out.update(state=p.PASS,case_receipt_pin=pin,metadata_IO=meta.summary(),
                source_frame=frame.commit(body),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            p.validate_closing(out,body,pin,required,binding,extra)
            own=out['source_frame']['handles'];dup=own['borrowed_byte_streams']
            require(own['input_lock_handles_opened']==own['input_lock_handles_closed']==1790
                and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2968
                and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0,
                'FULL_BORROWED_NATIVE_CLEANUP')
            out['runtime_plan']=accepted.merge(prior['legacy_plan'],plan,names,[name])
            require(out['runtime_plan']['runtime_source_qualified_individual_cases']==13
                and out['runtime_plan']['next_runtime_index']==14,'NEW_PAIR_RUNTIME13_NEXT14')
            out['runtime_pair_qualified_by_original_parent_and_live_frame']=True
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['state']='FAILED_NOT_ACCEPTED'
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED'
            out['source_frame']=frame.summary()
        p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['preparation_IO']=q.summary()
        out['metadata_observation']=observation.summary(owner)
        if out['state']==p.PASS:
            try:p.validate_closing(out,body,pin,required,binding,extra)
            except (ValueError,OSError,KeyError,TypeError):out['state']='FAILED_NOT_ACCEPTED'
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','borrowed_runtime_contract_tests_passed','selected_test_index',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
