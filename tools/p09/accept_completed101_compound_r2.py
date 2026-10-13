"""P296: 원FAILED/STOPPED101+P295 독립전체source의 새 결합 수용. 본체 재실행 없음."""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import close_completed101_source_frame_r2 as closing
review=closing.review;m=closing.m
SELF='tools/p09/accept_completed101_compound_r2.py'
TEST='tools/p09/tests/test_completed101_compound_r2.py'
SOURCE_PATH=m.p.DIR+'/p295-r2-case101-source-actual-run02.v1.json'
SCHEMA='hwpx-agent.p09-completed101-exact-compound-r2/v1'
PASS='PASS_COMPLETED101_BODY_AND_INDEPENDENT_FULL_SOURCE_COMPOUND_R2_NOT_WHOLE_OR_GATE'
COUNT=22

def require(ok,code):m.require(ok,'COMPLETED101_COMPOUND_'+code)

def combine(root,body,source,names,expected,exe,required,extras):
    checked=review.review(root,body);binding=m.p.v.identity(names,expected,exe)
    require(len(names)==249 and names[100]==review.NAME and root['binding']==body['binding']==binding,'EXACT_COMPILED_MANIFEST_BINDING')
    require(len(required)==1599 and m.p.v.pins(body['source_freeze'])==required
        and required.get(exe['path'])==exe==m.p.m.EXE and required[m.p.m.SELF]==m.p.prior.WORKER_PIN
        and all(required.get(n)==dict(path=n,**pin) for n,pin in m.p.m.CORE_PINS.items()),'ALL_ORIGINAL_EXECUTED_BYTES')
    require(set(extras)==set(closing.EXTRAS) and not set(extras)&set(required)
        and m.p.v.pins(source['extra_controller_pins'])==extras
        and m.p.v.pins(source['original_executed_source_pins'])==required,'EXACT_INDEPENDENT_SOURCE_INPUTS')
    closing.validate(source,{**required,**extras})
    require(source['review']==checked,'SAME_IMMUTABLE_STOP_REVIEW')
    return dict(selected_test_index=101,selected_test_name=review.NAME,binding=binding,compound_individual_case_qualified=True,
        validated_original_terminal_pass_count=1,original_parent_state='STOPPED_NOT_ACCEPTED',original_root_state='FAILED_NOT_ACCEPTED',
        original_STOP_receipt_accepted=False,original_partial_post_hash_completed=False,original_failure_bytes_preserved=True,
        original_body_not_reexecuted=True,separate_full_source_frame_verified=True,CPU_improvement_or_PC_freeze_solution_established=False,
        whole_or_full249_or_Gate_promoted=False,original_executed_source_inputs=1599,separate_post_source_inputs=1609)

def advance(legacy,base,names):
    require(base['runtime_source_qualified_individual_cases']==94 and base['next_runtime_index']==101
        and base['runtime_successful_candidates_requiring_closing']==0
        and review.NAME not in base['runtime_qualified_test_names'],'NO_DUPLICATE_OR_PENDING_PRIOR')
    plan=m.g.advance(legacy,base,names,101)
    require(plan['runtime_source_qualified_individual_cases']==95 and plan['next_runtime_index']==102
        and plan['runtime_remaining_individual_cases']==154 and plan['runtime_remaining_regular_cases']==148
        and plan['runtime_remaining_corpus_cases']==6 and plan['all_successful_bodies_pending_whole_reconciliation']==92,
        'EXACT_ONE_ADVANCE95_NEXT102_NOT_GATE')
    return plan

def contracts(fixtures):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'));import test_completed101_compound_r2 as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_COMPOUND_CHILD')),patch('threading.Thread.start',side_effect=AssertionError('NO_COMPOUND_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'COMPOUND22')
    return COUNT

def validate(doc,root,body,source,names,expected,exe,original,extras,legacy,base):
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['original_failed_root_pin']==review.ROOT and doc['original_stopped_parent_pin']==review.BODY
        and doc['original_zero_placeholder_pin']==review.ZERO and doc['stop_review_pin']==closing.REVIEW_PIN
        and doc['separate_source_frame_pin']['path']==SOURCE_PATH and doc['compound_contract_tests_passed']==COUNT
        and doc['compound']==combine(root,body,source,names,expected,exe,original,extras)
        and doc['prior_runtime_plan']==base and doc['runtime_plan']==advance(legacy,base,names)
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('actual_new_product_body_executed','actual_product_child_executed',
            'additional_full_source_frame_executed','whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'ONLY_EXACT_CLOSED_COMPOUND')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--source-bytes',type=int,required=True);ap.add_argument('--source-sha256',required=True)
    args=ap.parse_args();require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99
        and 0<args.source_bytes<=16777216 and re.fullmatch('[0-9a-f]{64}',args.source_sha256),'CWD_RUN_LITERAL_SOURCE_PIN')
    # 생산 코드도 독립 source scope에 포함된다. 생성된 receipt pin만 인자로 바인딩하여
    # source가 통과한 뒤 코드를 바꾸는 순환 hash 의존성을 만들지 않는다.
    source_pin=dict(path=SOURCE_PATH,bytes=args.source_bytes,sha256=args.source_sha256)
    destination=m.p.c.ROOT/f'{m.p.DIR}/p296-r2-case101-compound-run{args.run:02}.v1.json';require(not destination.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),actual_new_product_body_executed=False,
        additional_full_source_frame_executed=False,original_failed_root_pin=review.ROOT,original_stopped_parent_pin=review.BODY,
        original_zero_placeholder_pin=review.ZERO,stop_review_pin=closing.REVIEW_PIN,separate_source_frame_pin=source_pin)
    try:
        owner.admit();stage='metadata';q=m.Reader(owner,context)
        root=m.m.review.bound_json(q,review.ROOT);body=m.m.review.bound_json(q,review.BODY)
        source=m.m.review.bound_json(q,source_pin);support=m.m.review.bound_json(q,closing.REVIEW_PIN)
        checked=review.review(root,body)
        require(support['schema_version']==review.SCHEMA and support['state']==review.PASS and support['review']==checked
            and support['resource_stop_reason'] is None and support['resource_watcher_cleanup_confirmed'] is True
            and support['IO']['finished'] is True and support['IO']['bound_inputs']==support['IO']['final_fresh_hashes']==7
            and support['review_contract_tests_passed']==30,'SEALED_REVIEW30')
        require(q.pin(review.ZERO['path'])==review.ZERO,'ZERO_PLACEHOLDER_PRESERVED')
        ip=root['binding']['compiled_inventory_pin'];inventory=m.m.review.bound_json(q,ip);names=inventory['source_test_names']
        prep=m.m.review.bound_json(q,m.p.b.BASE_PREP);expected=m.p.v.pins(prep['whole_inputs']);exe=m.p.m.EXE
        require(len(expected)==1470 and prep['source_closing_exact'] is True and prep['resource_stop_reason'] is None
            and prep['resource_watcher_cleanup_confirmed'] is True,'PINNED_BASELINE_CATALOG_NOT_CURRENT_WHOLE_AUDIT')
        binding=m.p.v.identity(names,expected,exe)
        original100=m.m.review.bound_json(q,m.OLD_PAIRS[-1][0]);old_body_pin=original100['case_receipt_pin']
        old_body=m.m.review.bound_json(q,old_body_pin);old_required=m.p.v.pins(old_body['source_freeze'])
        old_extras=m.p.v.pins(original100['extra_frame_controller_pins']);legacy=m.m.review.bound_json(q,m.g.old.PRIOR)['legacy_plan']
        base=m.previous.record(original100,old_body,old_body_pin,old_required,binding,old_extras,names,legacy,original100['prior_runtime_plan'])
        require(base==root['prior_runtime_plan'],'SOURCE_STOP_DID_NOT_ADVANCE_PRIOR94')
        original=m.p.v.pins(body['source_freeze']);extras={n:q.pin(n) for n in closing.EXTRAS}
        for n in m.NEW:require(q.pin(n)==original[n],'ALL36_RUNTIME_CODE_PINS_UNCHANGED')
        require(sorted(x.name for x in (m.p.c.ROOT/m.p.DIR).glob('p291-*.v1.json'))==
            ['p291-case-101-run002.v1.json','p291-light-run001.v1.json'],'NO_UNREVIEWED_P291_ROOT_OR_RETRY')
        require(sorted(x.name for x in (m.p.c.ROOT/m.p.DIR/'cases').glob('p291-*.json'))==
            ['p291-case-101-run002.json','p291-failure-101-run002.json'],'NO_ADDITIONAL_PRODUCT_BODY')
        combined=combine(root,body,source,names,expected,exe,original,extras)
        stage='contract_tests';out['compound_contract_tests_passed']=contracts((root,body,source,names,expected,exe,original,extras,legacy,base))
        plan=advance(legacy,base,names);q.finish()
        out.update(compound=combined,prior_runtime_plan=base,runtime_plan=plan,legacy_plan=legacy,binding=binding,
            original_source_required_pins=list(original.values()),extra_post_source_controller_pins=list(extras.values()),
            accepted100_root_pin=m.OLD_PAIRS[-1][0],accepted100_body_pin=old_body_pin,compiled_inventory_pin=ip,
            baseline_catalog_pin=m.p.b.BASE_PREP,legacy_plan_pin=m.g.old.PRIOR)
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error);out['failure_diagnostic']=m.diagnostic(error,stage)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        m.g.complete(out,owner,proposed,lambda doc:validate(doc,root,body,source,names,expected,exe,original,extras,legacy,base))
        out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:
            writer=m.r.packed.dump if out['state']==PASS else m.r.compact.dump
            writer(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','compound_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
