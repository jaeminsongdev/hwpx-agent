"""P214 원 P213 후처리 오류 보존 + 정상 본문/완료 source-frame 독립 수용.

원 runner의 overall PASS를 근거로 삼지 않는다. original parent를 원 strict
validator로, 전체 source closing을 원 frame validator로 각각 검증하고 새
스키마의 큐 결합을 작성한다. 제품/전체 source hash 재실행 없이 metadata만 읽는다.
"""
import argparse
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_borrowed_runtime_r07_case as runner

p=runner.p;a=runner.accepted;observation=runner.observation
SELF='tools/p09/close_borrowed_runtime_pair.py'
TEST='tools/p09/tests/test_borrowed_runtime_pair.py'
SOURCE=dict(path='implementation/p09/evidence/locked-r07/p213-borrowed-frame-actual-run01.v1.json',
    bytes=1312117,sha256='48a9f05f2e37c6d9334ec65553bd2581f652e38f4b6385082dffbe38fae54126')
BODY=dict(path='implementation/p09/evidence/locked-r07/cases/p213-case-013-run01.json',
    bytes=789210,sha256='425791485d0d79724b50f345f05619e0b3c29b2ad6dbf196931dbbe470a2a928')
SCHEMA='hwpx-agent.p09-r07-borrowed-runtime-pair-closing/v1'
PASS='PASS_EXACT_R07_BORROWED_RUNTIME_PAIR_SEPARATE_ACCEPTANCE_NOT_WHOLE_OR_GATE'


def require(ok,code):p.require(ok,'BORROWED_PAIR_'+code)


def qualify(source,body,prior,names,expected,exe,required,extras):
    base=runner.prior_scope(prior,names,expected,exe);binding=p.v.identity(names,expected,exe)
    require(source['borrowed_runner_generation']=='P213_CURRENT1484' and source['selected_test_index']==13
        and source['selected_test_name']==names[12] and source['prior_compound_pin']==runner.PRIOR
        and source['prior_runtime_plan']==base and source['binding']==binding,'EXACT_PRIOR12_CASE13_BINDING')
    require(source['error_code']=='P152_FULL_REDACTED_FAILURE' and 'runtime_plan' not in source
        and 'runtime_pair_qualified_by_original_parent_and_live_frame' not in source
        and source['actual_product_child_executed_field_scope']=='SOURCE_FRAME_CLOSING_COMPONENT'
        and source['closing_component_did_not_execute_product_again'] is True
        and source['actual_new_product_body_executed'] is True and source['product_test_body_started'] is True,
        'ORIGINAL_POST_CLOSING_ERROR_NOT_IGNORED_AS_OVERALL_PASS')
    require(source['case_receipt_pin']==BODY and source['case_receipt_path']==BODY['path']
        and len(required)==1484 and required.get(exe['path'])==exe==p.m.EXE
        and set(extras)==set(runner.EXTRAS),'EXACT_BODY_AND_FULL_EXECUTED_SCOPE')
    # 원의 strict 정상 부모와 완료 frame 계약을 독립적으로 모두 유지한다.
    p.validate_parent(body,names[12],binding,required)
    p.validate_closing(source,body,BODY,required,binding,extras)
    handles=source['source_frame']['handles'];duplicate=handles['borrowed_byte_streams']
    require(handles['input_lock_handles_opened']==handles['input_lock_handles_closed']==1790
        and handles['maximum_lock_seconds']==600 and handles['ancestor_walk_steps']==305
        and handles['native_open_pacing']['maximum_opens_per_second']==32
        and handles['native_open_pacing']['open_reservations']==4758
        and duplicate['duplicate_handles_opened']==duplicate['duplicate_handles_closed']==duplicate['shared_offset_resets']==2968
        and duplicate['duplicate_handles_remaining']==duplicate['duplicate_close_failed_attempts']==0
        and duplicate['byte_stream_pathname_reopens']==0
        and source['preparation_IO']['bound_inputs']==source['preparation_IO']['final_fresh_hashes']==64
        and source['preparation_IO']['finished'] is True,'ALL_ORIGINAL_FRESH_IO_AND_NATIVE_CLEANUP')
    require(body['task']==body['minimal_worker_task']=='p204-r07-case-013-tests'
        and source['source_frame']['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=1484,directory_count=306), 'EXACT_TASK_AND_HELD_FILE_IDS')
    # 당시 코드가 finalize 전에 호출했던 상태를 재현한다. 실제 작업을 재실행하지 않는다.
    premature=dict(source);premature.pop('resource_stop_reason');premature.pop('resource_watcher_cleanup_confirmed')
    try:p.validate_closing(premature,body,BODY,required,binding,extras)
    except KeyError as error:require(error.args==('resource_stop_reason',),'PRE_FINALIZE_EXACT_MISSING_FIELD')
    else:require(False,'PRE_FINALIZE_REGRESSION_NOT_REPRODUCED')
    plan=a.merge(prior['legacy_plan'],base,names,[names[12]])
    require(plan['runtime_source_qualified_individual_cases']==13 and plan['next_runtime_index']==14
        and plan['runtime_remaining_individual_cases']==236 and plan['runtime_remaining_regular_cases']==230
        and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0,
        'EXACT_PAIR13_NEXT14_QUEUE')
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_borrowed_runtime_pair as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('P214_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P214_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P214_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==14 and not result.skipped,'CONTRACT14')
    return 14


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p214-case-013-pair-closing-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        actual_new_product_body_or_full_source_frame_executed=False,
        original_runner_overall_accepted=False,original_runner_error_preserved=True)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        for pin in (SOURCE,BODY,runner.PRIOR,a.documents.CLOSED,p.b.BASE_PREP,p.m.PARENT):
            require(q.pin(pin['path'])==pin,'SEALED_PROOF_PINS')
        source=q.json(SOURCE['path']);body=q.json(BODY['path']);prior=q.json(runner.PRIOR['path'])
        old_source=q.json(a.documents.CLOSED['path']);prep=q.json(p.b.BASE_PREP['path']);compiled=q.json(p.m.PARENT['path'])
        expected=p.v.pins(prep['whole_inputs']);names=compiled['source_test_names'];exe=compiled['compiled_test_executable_pin']
        required=p.v.pins(old_source['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        # P211 전체1480 + 당시 실행의 새4 제어 코드. 원 실행 파일은 재작성하지 않는다.
        required.update({name:q.pin(name) for name in (a.SELF,a.TEST,runner.SELF,runner.TEST)})
        extras={name:q.pin(name) for name in runner.EXTRAS}
        require(all(required.get(name)==pin for name,pin in extras.items()),'CURRENT_EXECUTED_CONTROLLER_BYTES')
        plan=qualify(source,body,prior,names,expected,exe,required,extras)
        with context.scope('contract_tests'):
            out['pair_closing_contract_tests_passed']=contracts((source,body,prior,names,expected,exe,required,extras))
        consumer=[q.pin(name) for name in (SELF,TEST)];q.finish()
        out.update(state=PASS,runtime_plan=plan,binding=p.v.identity(names,expected,exe),selected_test_index=13,
            selected_test_name=names[12],original_source_frame_receipt_pin=SOURCE,original_parent_receipt_pin=BODY,
            prior_compound_pin=runner.PRIOR,original_source_only_state_preserved=True,
            premature_finalization_missing_field_reproduced=True,current_strict_parent_and_full_frame_verified=True,
            pair_consumer_pins=consumer,original_executed_controller_pins=list(extras.values()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error))
    finally:
        p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=observation.summary(owner)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','pair_closing_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
