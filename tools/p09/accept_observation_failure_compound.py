"""P264: 원91 단일본문 PASS와 새 독립 source를 strict 검증하는 결합 수용.

원 failed root/미완료 metadata는 불변. 재실행·현재 whole/Gate 수용 없음.
후속 실행기는 이 결합 증거와 원 판정을 소비해야 하며 원 P260은 수정하지 않는다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import close_observation_failure_source_frame as closing
review=closing.review;old=closing.old;m=closing.m;p=closing.p;g=closing.g
SELF='tools/p09/accept_observation_failure_compound.py'
TEST='tools/p09/tests/test_observation_failure_compound.py'
SOURCE_PIN=dict(path=p.DIR+'/p263-case091-source-frame-run01.v1.json',bytes=1880734,
    sha256='85fda297ba865d15588c62dd1e14248d8f1caa8991374c1d9ea6e448a4b49e05')
SCHEMA='hwpx-agent.p09-observation-failure-exact-compound/v1'
PASS='PASS_CASE091_BODY_AND_INDEPENDENT_FULL_SOURCE_COMPOUND_NOT_WHOLE_OR_GATE'
REPORT='implementation/p09/P09-264_CASE091_MONOTONIC_COMPOUND_RUNTIME_R0108_REPORT.md'
COUNT=26


def require(ok,code):old.require(ok,'OBSERVATION_COMPOUND_'+code)


def inventory(roots,bodies):
    require(sorted(roots)==sorted([review.LIGHT_PIN['path'].split('/')[-1],review.ROOT_PIN['path'].split('/')[-1]])
        and sorted(bodies)==[review.BODY_PIN['path'].split('/')[-1]],'ONLY_LITERAL_LIGHT_AND_FAILED91_NO_RETRY')


def combine(root,body,source,names,expected,exe,required,extras):
    checked=review.review(root,body);binding=p.v.identity(names,expected,exe)
    require(len(names)==249 and names[90]==review.NAME and root['binding']==body['binding']==binding,'EXACT_CURRENT249_BINDING')
    require(len(required)==1555 and p.v.pins(body['source_freeze'])==required
        and required.get(exe['path'])==exe==p.m.EXE and required[p.m.SELF]==p.prior.WORKER_PIN
        and all(required.get(n)==dict(path=n,**pin) for n,pin in p.m.CORE_PINS.items()),'ALL_EXECUTED_SOURCE_EXE_WORKER_CORE')
    limits=body['owned_limits_readback'];require(limits['verified'] is True
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] is True and limits['breakaway_disabled'] is True
        and type(body['job_final']['active_processes']) is int and body['job_final']['active_processes']==0,'ORIGINAL_JOB_NOT_BOOLEAN_ONLY')
    require(set(extras)==set(closing.EXTRAS) and not set(required)&set(extras)
        and p.v.pins(source['extra_controller_pins'])==extras
        and p.v.pins(source['original_executed_source_pins'])==required,'EXACT_NEW_INDEPENDENT_SCOPE')
    closing.validate(source,{**required,**extras});require(source['review']==checked,'SAME_IMMUTABLE_FAILURE_REVIEW')
    return dict(selected_test_index=91,selected_test_name=review.NAME,binding=binding,
        compound_individual_case_qualified=True,validated_original_terminal_pass_count=1,
        original_root_state='FAILED_NOT_ACCEPTED',original_parent_state='PASS_SCOPED_NOT_GATE',
        original_failed_root_accepted=False,original_incomplete_metadata_promoted=False,
        original_failure_bytes_preserved=True,original_body_not_reexecuted=True,
        independent_full_source_and_identity_frame_verified=True,monotonic_post_reader_connection_verified=True,
        original_executed_source_inputs=1555,separate_post_source_inputs=1559,
        CPU_improvement_or_PC_freeze_solution_established=False,whole_or_full249_or_Gate_promoted=False)


def advance(legacy,base,names):
    require(base['runtime_source_qualified_individual_cases']==84 and base['next_runtime_index']==91
        and base['runtime_successful_candidates_requiring_closing']==0
        and review.NAME not in base['runtime_qualified_test_names'],'NO_DUPLICATE_OR_PENDING')
    plan=g.advance(legacy,base,names,91)
    require(plan['runtime_source_qualified_individual_cases']==85 and plan['next_runtime_index']==92
        and plan['runtime_remaining_individual_cases']==164 and plan['runtime_remaining_regular_cases']==158
        and plan['runtime_remaining_corpus_cases']==6
        and plan['all_successful_bodies_pending_whole_reconciliation']==82,'EXACT85_NEXT92_NOT_GATE')
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_observation_failure_compound as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_COMPOUND_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'CONTRACT26_NO_SKIP');return COUNT


def status_documents(q,plan):
    prior=m.review.bound_json(q,old.COMPOUND);pins=p.v.pins(prior['bound_input_pins']);prefixes=[]
    for name in m.MUTABLE_DOCS:
        archive='implementation/p09/evidence/runtime-progress-r107/'+name.split('/')[-1]
        before=bytes(old.review.docs.bytes_docs.bound_bytes(q,archive));after=bytes(old.review.docs.bytes_docs.bound_bytes(q,name))
        require(q.reader.snapshots[archive]==dict(pins[name],path=archive) and after.endswith(before),'EXACT_R107_SUFFIX')
        prefix=after[:-len(before)].decode('utf-8');require(prefix.startswith('> P264 runtime-r108 ')
            and all(w in prefix for w in ('runtime 수용85/249','잔여164(일반158+corpus6)','다음index92',
                '독립source 마감대기0','whole재조정대기82','P09·A12·A13 OPEN','원 STOP/FAILED 보존','본문 재실행 없음')),'STATUS_BOUNDARIES')
        prefixes.append(prefix)
    require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
    report=bytes(old.review.docs.bytes_docs.bound_bytes(q,REPORT)).decode('utf-8')
    require(all(pin['sha256'] in report for pin in (review.ROOT_PIN,review.BODY_PIN,review.LIGHT_PIN,
        closing.REVIEW_PIN,SOURCE_PIN,old.COMPOUND)) and '원600초·CPU/RAM 기준은 변경하지 않음' in report
        and 'PC 프리즈 해결은 입증하지 않음' in report,'BOUND_REPORT_NOT_FREEZE_CLAIM')
    require(plan['runtime_source_qualified_individual_cases']==85,'STATUS_PLAN')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99 and isinstance(SOURCE_PIN,dict),'CWD_RUN_AND_PINNED_SOURCE')
    destination=p.c.ROOT/f'{p.DIR}/p264-case091-compound-run{args.run:02}.v1.json';require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),original_failed_root_pin=review.ROOT_PIN,
        original_body_pin=review.BODY_PIN,observation_review_pin=closing.REVIEW_PIN,separate_source_frame_pin=SOURCE_PIN,
        actual_new_product_body_executed=False,additional_full_source_frame_executed=False,
        original_incomplete_metadata_not_retroactively_promoted=True)
    try:
        owner.admit();q=m.Reader(owner,context)
        legacy,base,names,expected,exe,required,old_extras,*unused=old.anchor(q)
        folder=p.c.ROOT/p.DIR;inventory([x.name for x in folder.glob('p260-*.v1.json')],
            [x.name for x in (folder/'cases').glob('p260-*.json')])
        root=m.review.bound_json(q,review.ROOT_PIN);body=m.review.bound_json(q,review.BODY_PIN)
        require(root['prior_runtime_plan']==base,'LITERAL_FAILURE_PREVIOUS84')
        light=m.review.bound_json(q,review.LIGHT_PIN);old.closed_attempt(light)
        require(light['state']==old.LIGHT and light['runtime_contract_executions']==498 and light['prior_runtime_plan']==base,'EXACT_LIGHT')
        source=m.review.bound_json(q,SOURCE_PIN);prior=m.review.bound_json(q,closing.REVIEW_PIN)
        require(prior['schema_version']==review.SCHEMA and prior['state']==review.PASS
            and prior['review']==review.review(root,body) and prior['resource_stop_reason'] is None
            and prior['resource_watcher_cleanup_confirmed'] is True and prior['observation_contract_tests_passed']==36
            and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==15
            and prior['small_real_IO']['finished'] is True
            and prior['small_real_IO']['bound_inputs']==prior['small_real_IO']['final_fresh_hashes']==3,'QUALIFIED_REVIEW_AND_SMALL_CONNECTION')
        extras={n:q.pin(n) for n in closing.EXTRAS};combined=combine(root,body,source,names,expected,exe,required,extras)
        with context.scope('contract_tests'):
            out['compound_contract_tests_passed']=contracts((root,body,source,names,expected,exe,required,extras,legacy,base))
        plan=advance(legacy,base,names);status_documents(q,plan);consumers=[q.pin(n) for n in (SELF,TEST)];q.finish()
        out.update(compound=combined,prior_runtime_plan=base,runtime_plan=plan,legacy_plan=legacy,binding=root['binding'],
            compound_consumer_pins=consumers,extra_post_source_controller_pins=list(extras.values()),
            original_source_required_pins=list(required.values()),status_revision=108,exact_r107_document_bytes_preserved=True,
            required_bound_input_names=sorted(q.reader.snapshots),report_pin=q.reader.snapshots[REPORT]);proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            m.metadata_contract(doc['IO']);require(doc['IO']['finished'] is True
                and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(x['path'] for x in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['compound_contract_tests_passed']==COUNT,'ALL_FRESH_AND26')
        g.complete(out,owner,proposed,validate);out['metadata_observation']=g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','compound_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
