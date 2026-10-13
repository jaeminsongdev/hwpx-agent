"""P236: 원 case078 STOP를 바꾸지 않고 완료 본문+독립 전체 source를 결합.

P212 기존 방식처럼 새로운 compound 증거만 수용한다. 원 P230 progress를
수정하지 않는다. 원 정상 기록은 원 validator로 검증하고 단 하나의 literal
실패는 그대로 보존한다. JSON의 SHA binding을 재사용해 중복 첫 읽기를 제거.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import close_current_stop_source_frame as closing

review=closing.review;r=closing.r
SELF='tools/p09/accept_current_stop_compound.py'
TEST='tools/p09/tests/test_current_stop_compound.py'
SOURCE_PIN=dict(path=r.p.DIR+'/p235-current-stop-source-frame-run01.v1.json',bytes=1336314,
    sha256='cc7793e2ee7cc9facc9de8bcf72c64551ae629124d7c683fb95e367747582b62')
SCHEMA='hwpx-agent.p09-current-stop-exact-compound/v1'
PASS='PASS_CURRENT_CASE078_BODY_AND_SEPARATE_FULL_SOURCE_COMPOUND_NOT_WHOLE_OR_GATE'


def require(ok,code):r.require(ok,'CURRENT_COMPOUND_'+code)


def combine(root,body,source,names,expected,exe,required,extras):
    checked=review.review(root,body);binding=r.p.v.identity(names,expected,exe)
    require(len(names)==249 and names[77]==review.NAME and root['binding']==body['binding']==binding,
        'EXACT_COMPILED249_IDENTITY_AND_BODY78')
    require(len(required)==1512 and r.p.v.pins(body['source_freeze'])==required
        and required.get(exe['path'])==exe==r.p.m.EXE
        and required[r.p.m.SELF]==r.p.prior.WORKER_PIN
        and all(required.get(name)==dict(path=name,**pin) for name,pin in r.p.m.CORE_PINS.items()),
        'ALL_ORIGINAL_EXE_WORKER_AND_CORE_BYTES')
    limits=body['owned_limits_readback']
    require(limits['verified'] is True and limits['cpu_hard_cap_machine_percent']==6.25
        and limits['affinity_mask']==1 and limits['priority_class']==16384
        and limits['active_process_limit']==16 and limits['kill_on_close'] is True
        and limits['breakaway_disabled'] is True,'ORIGINAL_ACTUAL_JOB_LIMITS')
    require(set(extras)==set(closing.EXTRAS) and not set(extras)&set(required)
        and source['extra_controller_pins']==list(extras.values()),'EXACT_CURRENT_POST_SOURCE_HELPERS')
    closing.validate(source,{**required,**extras})
    require(source['closing_contract_tests_passed']==12 and source['review']==checked,
        'SAME_LITERAL_REVIEW_AND_FULL_SOURCE')
    return dict(selected_test_index=78,selected_test_name=review.NAME,binding=binding,
        compound_individual_case_qualified=True,validated_original_terminal_pass_count=1,
        original_parent_state='STOPPED_NOT_ACCEPTED',original_root_state='FAILED_NOT_ACCEPTED',
        original_STOP_receipt_accepted=False,original_partial_post_hash_completed=False,
        original_failure_bytes_preserved=True,original_body_not_reexecuted=True,
        separate_full_source_frame_verified=True,whole_or_full249_or_Gate_promoted=False,
        original_executed_source_inputs=1512,separate_post_source_inputs=1516)


def before_stop(q,legacy,base,names,required,binding,extras):
    folder=r.p.c.ROOT/r.p.DIR
    early=sorted((*folder.glob('p230-admission-run*.v1.json'),*folder.glob('p230-packed-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:r.closed_attempt(q.json(path.relative_to(r.p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p230-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base;stopped=None;accepted=0
    for path in files:
        match=r.FILE.fullmatch(path.name);require(match is not None,'EXACT_OLD_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        name=path.relative_to(r.p.c.ROOT).as_posix();doc=q.json(name)
        if name==review.ROOT_PIN['path']:
            require(stopped is None and q.reader.snapshots[name]==review.ROOT_PIN
                and doc['prior_runtime_plan']==plan and plan['next_runtime_index']==78,
                'ONLY_LITERAL_FAIL_AND_EXACT_PRIOR_PLAN')
            stopped=doc;continue
        # 未검토 실패/후속 항목/중복은 허용하지 않는다. 원 validator를 그대로 호출.
        require(stopped is None,'NO_LATER_RECORD_AFTER_STOP')
        r.closed_attempt(doc);require(doc['selected_test_index']==index,'EXACT_OLD_SELECTED_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{r.p.DIR}/cases/p230-case-{index:03}-run{number:03}.json',
            'EXACT_OLD_BODY_PATH')
        body=review.bound_json(q,pin)
        plan=r.record(doc,body,pin,required,binding,extras,names,legacy,plan);accepted+=1
    require(stopped is not None and accepted==17 and plan['runtime_source_qualified_individual_cases']==71
        and plan['next_runtime_index']==78,'ALL17_OLD_PASS_AND_LITERAL_STOP_ONLY')
    return plan,stopped


def advance(legacy,base,names):
    require(base['runtime_source_qualified_individual_cases']==71 and base['next_runtime_index']==78
        and base['runtime_successful_candidates_requiring_closing']==0
        and review.NAME not in base['runtime_qualified_test_names'],'NO_DUPLICATE_OR_UNCLOSED_ACCEPTANCE')
    plan=r.g.advance(legacy,base,names,78)
    require(plan['runtime_source_qualified_individual_cases']==72 and plan['next_runtime_index']==79
        and plan['runtime_remaining_individual_cases']==177 and plan['runtime_remaining_regular_cases']==171
        and plan['runtime_remaining_corpus_cases']==6,'EXACT72_NEXT79')
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_current_stop_compound as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_COMPOUND_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(checked.wasSuccessful() and checked.testsRun==20 and not checked.skipped,'CONTRACT20')
    return 20


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p236-case078-compound-run{args.run:02}.v1.json'
    require(not path.exists(),'NEW_RECEIPT_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**r.p.r.flags(),actual_new_product_body_executed=False,
        additional_full_source_frame_executed=False,original_failed_root_pin=review.ROOT_PIN,
        original_stopped_parent_pin=review.BODY_PIN,original_zero_placeholder_pin=review.ZERO_PIN,
        separate_source_frame_pin=SOURCE_PIN,stop_review_pin=closing.REVIEW_PIN,
        original_partial_post_hash_not_retroactively_promoted=True,initial_body_pin_read_coalesced_with_JSON=True)
    try:
        owner.admit();q=r.Reader(owner,context)
        legacy,base,names,expected,exe,required,old_extras=r.anchor(q)
        binding=r.p.v.identity(names,expected,exe)
        base,root=before_stop(q,legacy,base,names,required,binding,old_extras)
        body=review.bound_json(q,review.BODY_PIN);source=review.bound_json(q,SOURCE_PIN)
        prior=review.bound_json(q,closing.REVIEW_PIN)
        require(prior['state']==review.PASS and prior['review']==review.review(root,body)
            and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
            and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==8,
            'SEALED_REVIEW')
        require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'PRESERVED_ZERO_PLACEHOLDER')
        extras={name:q.pin(name) for name in closing.EXTRAS}
        compound=combine(root,body,source,names,expected,exe,required,extras)
        with context.scope('contract_tests'):
            out['compound_contract_tests_passed']=contracts((root,body,source,names,expected,exe,required,extras,legacy,base))
        plan=advance(legacy,base,names);consumers=[q.pin(name) for name in (SELF,TEST)]
        q.finish();out.update(compound=compound,prior_runtime_plan=base,runtime_plan=plan,legacy_plan=legacy,
            binding=binding,compound_consumer_pins=consumers,extra_post_source_controller_pins=list(extras.values()))
        candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
            and doc['compound_contract_tests_passed']==20,'ALL_FRESH_CONTRACT20'))
        out['metadata_observation']=r.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','compound_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
