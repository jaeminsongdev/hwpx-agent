"""P212 별도 compound 수용: 정상 exact 본문 + 독립 전체 source frame.

원 STOP/FAILED/partial hash는 수정하지 않는다. 기존 CASE_PASS validator를
우회해 원 STOP를 PASS로 보이게 하지 않고, 새 스키마로 두 독립 증거를 결합한다.
원 runtime/whole 원장과 실행 성공을 중복 수용하지 않는다. 제품 재실행 없음.
"""
import argparse
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import close_borrowed_source_frame as closing
import verify_borrowed_frame_progress as documents

p=closing.p;review=closing.review;observation=closing.observation
SELF='tools/p09/accept_locked_runtime_candidate.py'
TEST='tools/p09/tests/test_locked_runtime_compound.py'
SCHEMA='hwpx-agent.p09-exact-r07-locked-runtime-compound/v1'
PASS='PASS_EXACT_R07_BODY_AND_SEPARATE_LOCKED_SOURCE_COMPOUND_NOT_WHOLE_OR_GATE'


def require(ok,code):p.require(ok,'COMPOUND_'+code)


def combine_evidence(frame,body,source,names,expected,exe,original,extras):
    checked=review.review(frame,body)
    identity=p.v.identity(names,expected,exe);name=names[11]
    require(body['binding']==identity and body['selected_test_names']==[name]
        and frame['selected_test_name']==name and not name.startswith(p.v.CORPUS_PREFIX),
        'CURRENT_COMPILED_BINDING_AND_EXACT_CASE12')
    require(body['minimal_owned_worker_path']==p.m.SELF and body['minimal_worker_task']==body['task']=='p204-r07-case-012-tests'
        and body['native_frame_candidate_only'] is True and body['native_frame_closing_required'] is True
        and body['tests_passed'] is None and body['actual_product_child_executed'] is True,
        'ORIGINAL_STOPPED_PARENT_NOT_RECLASSIFIED')
    require(p.v.pins(body['source_freeze'])==original and len(original)==1473
        and original.get(exe['path'])==exe==p.m.EXE
        and original[p.m.SELF]==p.prior.WORKER_PIN
        and all(original.get(name)==dict(path=name,**pin) for name,pin in p.m.CORE_PINS.items()),
        'FULL_ORIGINAL_EXECUTED_INPUT_AND_WORKER_BYTES')
    limits=body['owned_limits_readback']
    require(limits['verified'] is True and limits['cpu_hard_cap_machine_percent']==6.25
        and limits['affinity_mask']==1 and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] is True and limits['breakaway_disabled'] is True,'ACTUAL_ORIGINAL_LIMITS')
    require(set(extras)==set(closing.EXTRAS) and not set(extras)&set(original)
        and source['extra_controller_pins']==list(extras.values()),'EXACT_POST_CLOSING_CONTROLLERS')
    required={**original,**extras};closing.validate(source,required)
    require(source['review']==checked,'EXACT_SAME_UNACCEPTED_BODY_REVIEW')
    sf=source['source_frame'];held=sf['held_identity_after_owned_cleanup'];handles=sf['handles']
    require(held==dict(held_identity_checks_complete=True,separate_pathname_reopens=0,
            regular_file_count=1480,directory_count=306)
        and all(sf[key] is False for key in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed'))
        and handles['maximum_lock_seconds']==600 and handles['ancestor_walk_steps']==305
        and handles['native_open_pacing']['open_reservations']==4746
        and handles['file_write_or_delete_operation_executed'] is False and handles['input_scope_reduced'] is False,
        'REAL_FULL_READ_LOCK_FRAME_NOT_CACHED_OR_REDUCED')
    require(source['preparation_IO']['bound_inputs']==source['preparation_IO']['final_fresh_hashes']==9
        and source['preparation_IO']['maximum_scope_seconds']==600
        and source['P09_gate']==source['A12_gate']==source['A13_gate']=='OPEN','FRESH_SEPARATE_SOURCE_PROOF')
    return dict(selected_test_index=12,selected_test_name=name,binding=identity,
        compound_individual_case_qualified=True,validated_original_terminal_pass_count=1,
        original_parent_state='STOPPED_NOT_ACCEPTED',original_frame_state='FAILED_NOT_ACCEPTED',
        original_STOP_receipt_accepted=False,original_partial_post_hash_completed=False,
        original_failure_bytes_preserved=True,original_body_not_reexecuted=True,
        separate_full_source_frame_verified=True,whole_or_full249_or_Gate_promoted=False,
        original_executed_source_inputs=1473,separate_post_source_inputs=1480)


def merge(legacy,base,names,qualified):
    previous=base['runtime_qualified_test_names'];old=set(previous)
    require(len(previous)==len(old)==base['runtime_source_qualified_individual_cases']
        and old<=set(names) and len(qualified)==len(set(qualified))
        and set(qualified)<=set(names) and not old&set(qualified), 'NO_DUPLICATE_OLD_OR_NEW_ACCEPTANCE')
    require(base['runtime_successful_candidates_requiring_closing']==0,'CLOSE_EXISTING_PENDING_BEFORE_NEW_QUEUE')
    synthetic=dict(legacy,accepted_test_names=previous,accepted_individual_cases=len(old))
    plan=p.r.runtime_plan(synthetic,names,qualified,list(old|set(qualified)))
    plan.update(legacy_whole_accepted_individual_cases=legacy['accepted_individual_cases'],
        legacy_whole_pending_successful_candidates=legacy['successful_candidates_requiring_separate_closing'],
        prior_runtime_qualified_cases=len(old),locked_compound_qualified_individual_cases=len(qualified),
        all_successful_bodies_pending_whole_reconciliation=len(old|set(qualified))-legacy['accepted_individual_cases'],
        prior_runtime_receipts_and_validators_unchanged=True,original_STOP_receipts_not_reclassified=True)
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_locked_runtime_compound as tests
    with patch.object(tests,'FIXTURES',fixtures), \
            patch('subprocess.Popen',side_effect=AssertionError('P212_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P212_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P212_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped,'CONTRACT18')
    return 18


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p212-case-012-compound-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        actual_new_product_body_executed=False,additional_full_source_frame_executed=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        for pin in (review.FRAME,review.BODY,documents.CLOSED):require(q.pin(pin['path'])==pin,'IMMUTABLE_CANDIDATE_PROOF_PINS')
        frame=q.json(review.FRAME['path']);body=q.json(review.BODY['path']);source=q.json(documents.CLOSED['path'])
        expected,names,exe,runtime,fixture_inputs,helpers,base_scope=p.qualification.current_inputs(q)
        original_extras={name:q.pin(name) for name in p.EXTRAS}
        original=p.qualification.combine(base_scope,{}, {},original_extras)
        extras={name:q.pin(name) for name in closing.EXTRAS}
        compound=combine_evidence(frame,body,source,names,expected,exe,original,extras)
        engine={name:q.pin(name) for name in (p.b.SELF,p.b.TEST)}
        controls={name:q.pin(name) for name in p.prior.CONTROLLERS}
        with patch.object(p.prior.j,'case_controller',p.prior.case_controller):
            legacy,base,pins,attempts=p.prior.progress(q,expected,names,exe,engine,controls)
        require(base['runtime_source_qualified_individual_cases']==11 and base['next_runtime_index']==12,'PRIOR11_NEXT12_QUEUE')
        fixtures=(frame,body,source,names,expected,exe,original,extras,legacy,base)
        with context.scope('contract_tests'):out['compound_contract_tests_passed']=contracts(fixtures)
        plan=merge(legacy,base,names,[compound['selected_test_name']])
        consumers={name:q.pin(name) for name in (SELF,TEST)}
        require(plan['runtime_source_qualified_individual_cases']==12 and plan['runtime_remaining_individual_cases']==237
            and plan['runtime_remaining_regular_cases']==231 and plan['runtime_remaining_corpus_cases']==6
            and plan['runtime_successful_candidates_requiring_closing']==0 and plan['next_runtime_index']==13,
            'EXACT_NEW_COMPOUND_QUEUE')
        q.finish()
        out.update(state=PASS,compound=compound,runtime_plan=plan,prior_runtime_plan=base,legacy_plan=legacy,
            prior_runtime_closing_receipt_pins=pins,attempts=attempts,original_failed_frame_pin=review.FRAME,
            original_stopped_parent_pin=review.BODY,separate_source_frame_pin=documents.CLOSED,
            compound_consumer_pins=list(consumers.values()),extra_post_source_controller_pins=list(extras.values()),
            binding=compound['binding'],sealed_whole_before_anchor=p.b.BASE_CLOSE,
            original_partial_post_hash_not_retroactively_promoted=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=observation.summary(owner)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','compound_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
