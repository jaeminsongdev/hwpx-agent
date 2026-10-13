"""P259: P255 case090 완료본문+P258 독립전체source의 새 결합 수용.

원 FAILED/STOPPED와 partial hash 불변. 이전8본문은 재실행 없이 원record로
판정. 단 하나의 literal STOP만 검토; 원720/600/CPU/RAM 보호 유지.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import close_checkpoint_stop_source_frame as closing
review=closing.review;m=closing.m
SELF='tools/p09/accept_checkpoint_stop_compound.py'
TEST='tools/p09/tests/test_checkpoint_stop_compound.py'
SOURCE_PIN=dict(path=m.p.DIR+'/p258-case090-source-frame-run01.v1.json',bytes=1869973,
    sha256='4cd9bc4ffdf844d1eb54c5a30ed8ade5f4a33c203f89bab58cbda2dd503674fd')
SCHEMA='hwpx-agent.p09-checkpoint-stop-exact-compound/v1'
PASS='PASS_CASE090_BODY_AND_INDEPENDENT_FULL_SOURCE_COMPOUND_NOT_WHOLE_OR_GATE'
REPORT='implementation/p09/P09-259_CASE090_COMPOUND_RUNTIME_R0107_REPORT.md'


def require(ok,code):m.require(ok,'CHECKPOINT_COMPOUND_'+code)


def combine(root,body,source,names,expected,exe,required,extras):
    checked=review.review(root,body);binding=m.p.v.identity(names,expected,exe)
    require(len(names)==249 and names[89]==review.NAME and root['binding']==body['binding']==binding,'EXACT_MANIFEST_BINDING')
    require(len(required)==1545 and m.p.v.pins(body['source_freeze'])==required
        and required.get(exe['path'])==exe==m.p.m.EXE
        and required[m.p.m.SELF]==m.p.prior.WORKER_PIN
        and all(required.get(n)==dict(path=n,**pin) for n,pin in m.p.m.CORE_PINS.items()),'ALL_ORIGINAL_EXECUTED_BYTES')
    require(set(extras)==set(closing.EXTRAS) and not set(extras)&set(required)
        and m.p.v.pins(source['extra_controller_pins'])==extras
        and m.p.v.pins(source['original_executed_source_pins'])==required,'EXACT_INDEPENDENT_SOURCE_INPUTS')
    closing.validate(source,{**required,**extras})
    require(source['review']==checked and source['closing_contract_tests_passed']==14,'SAME_REVIEW_AND_FULL_FRAME')
    return dict(selected_test_index=90,selected_test_name=review.NAME,binding=binding,
        compound_individual_case_qualified=True,validated_original_terminal_pass_count=1,
        original_parent_state='STOPPED_NOT_ACCEPTED',original_root_state='FAILED_NOT_ACCEPTED',
        original_STOP_receipt_accepted=False,original_partial_post_hash_completed=False,
        original_failure_bytes_preserved=True,original_body_not_reexecuted=True,
        separate_full_source_frame_verified=True,early_source_runtime_connection_verified=True,
        actual_early_warning_yield_observed=source['early_source_checkpoint']['warning_entries']>0,
        CPU_improvement_or_PC_freeze_solution_established=False,whole_or_full249_or_Gate_promoted=False,
        original_executed_source_inputs=1545,separate_post_source_inputs=1551)


def before_stop(q,legacy,base,names,required,binding,extras):
    folder=m.p.c.ROOT/m.p.DIR
    early=sorted((*folder.glob('p255-admission-run*.v1.json'),*folder.glob('p255-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:m.closed_attempt(q.json(path.relative_to(m.p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p255-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base;stopped=None;accepted=0
    for path in files:
        match=m.FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        name=path.relative_to(m.p.c.ROOT).as_posix();doc=q.json(name)
        if name==review.ROOT_PIN['path']:
            require(stopped is None and q.reader.snapshots[name]==review.ROOT_PIN
                and doc['prior_runtime_plan']==plan and plan['next_runtime_index']==90,
                'ONLY_LITERAL_STOP_AND_EXACT_PRIOR_PLAN')
            stopped=doc;continue
        require(stopped is None,'NO_LATER_RECORD_AFTER_STOP')
        m.closed_attempt(doc);require(doc['selected_test_index']==index,'EXACT_SELECTED_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{m.p.DIR}/cases/p255-case-{index:03}-run{number:03}.json','EXACT_BODY_PATH')
        body=m.review.bound_json(q,pin)
        plan=m.record(doc,body,pin,required,binding,extras,names,legacy,plan);accepted+=1
    require(stopped is not None and accepted==8 and plan['runtime_source_qualified_individual_cases']==83
        and plan['next_runtime_index']==90,'ALL_EIGHT_CLOSED_AND_ONLY_STOP90')
    return plan,stopped


def advance(legacy,base,names):
    require(base['runtime_source_qualified_individual_cases']==83 and base['next_runtime_index']==90
        and base['runtime_successful_candidates_requiring_closing']==0
        and review.NAME not in base['runtime_qualified_test_names'],'NO_DUPLICATE_OR_PENDING_PRIOR_CASE')
    plan=m.g.advance(legacy,base,names,90)
    require(plan['runtime_source_qualified_individual_cases']==84 and plan['next_runtime_index']==91
        and plan['runtime_remaining_individual_cases']==165 and plan['runtime_remaining_regular_cases']==159
        and plan['runtime_remaining_corpus_cases']==6
        and plan['all_successful_bodies_pending_whole_reconciliation']==81,'EXACT84_NEXT91_NOT_GATE')
    return plan


def contracts(fixtures):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_checkpoint_stop_compound as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_COMPOUND_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_COMPOUND_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==26 and not result.skipped,'CONTRACT26')
    return 26


def status_documents(q,plan,prior):
    pins=m.p.v.pins(prior['bound_input_pins']);prefixes=[]
    for name in m.MUTABLE_DOCS:
        archive='implementation/p09/evidence/runtime-progress-r106/'+name.split('/')[-1]
        before=bytes(review.docs.bytes_docs.bound_bytes(q,archive));after=bytes(review.docs.bytes_docs.bound_bytes(q,name))
        require(q.reader.snapshots[archive]==dict(pins[name],path=archive) and after.endswith(before),'EXACT_R106_DOCUMENT_SUFFIX')
        prefix=after[:-len(before)].decode('utf-8');require(prefix.startswith('> P259 runtime-r107 ')
            and all(w in prefix for w in ('runtime 수용84/249','잔여165(일반159+corpus6)',
                '독립source 마감대기0','다음index91','whole재조정대기81','P09·A12·A13 OPEN',
                '원 STOP/FAILED 보존','본문 재실행 없음')),'STATUS_PLAN_AND_BOUNDARIES')
        prefixes.append(prefix)
    require(prefixes[0]==prefixes[1],'IDENTICAL_DOCUMENT_PREFIXES')
    report=bytes(review.docs.bytes_docs.bound_bytes(q,REPORT)).decode('utf-8')
    require(all(pin['sha256'] in report for pin in (review.ROOT_PIN,review.BODY_PIN,review.ZERO_PIN,SOURCE_PIN,closing.REVIEW_PIN))
        and '원600초·CPU/RAM 기준은 변경하지 않음' in report and '조기 완화 실제 경고 진입0' in report,
        'REPORT_PROOF_AND_NO_FALSE_IMPROVEMENT')
    require(plan['runtime_source_qualified_individual_cases']==84,'QUALIFIED_DOCUMENT_PLAN')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=m.p.c.ROOT/f'{m.p.DIR}/p259-case090-compound-run{args.run:02}.v1.json';require(not path.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
        actual_new_product_body_executed=False,additional_full_source_frame_executed=False,
        original_failed_root_pin=review.ROOT_PIN,original_stopped_parent_pin=review.BODY_PIN,
        original_zero_placeholder_pin=review.ZERO_PIN,stop_review_pin=closing.REVIEW_PIN,
        separate_source_frame_pin=SOURCE_PIN,original_partial_post_hash_not_retroactively_promoted=True)
    try:
        owner.admit();q=m.Reader(owner,context)
        legacy,base,names,expected,exe,required,old_extras,*unused=m.anchor(q)
        binding=m.p.v.identity(names,expected,exe)
        base,root=before_stop(q,legacy,base,names,required,binding,old_extras)
        body=m.review.bound_json(q,review.BODY_PIN);source=m.review.bound_json(q,SOURCE_PIN)
        prior=m.review.bound_json(q,closing.REVIEW_PIN)
        require(prior['schema_version']==review.SCHEMA and prior['state']==review.PASS
            and prior['review']==review.review(root,body) and prior['resource_stop_reason'] is None
            and prior['resource_watcher_cleanup_confirmed'] is True and prior['IO']['finished'] is True
            and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==15
            and prior['stop_and_early_source_contract_tests_passed']==32 and prior['original_peak_contract_tests_passed']==8,
            'QUALIFIED_STOP_REVIEW_AND_EARLY_POLICY')
        require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'ZERO_PLACEHOLDER_PRESERVED')
        extras={n:q.pin(n) for n in closing.EXTRAS};combined=combine(root,body,source,names,expected,exe,required,extras)
        with context.scope('contract_tests'):
            out['compound_contract_tests_passed']=contracts((root,body,source,names,expected,exe,required,extras,legacy,base))
        plan=advance(legacy,base,names);status_documents(q,plan,prior)
        consumers=[q.pin(n) for n in (SELF,TEST)];q.finish()
        out.update(compound=combined,prior_runtime_plan=base,runtime_plan=plan,legacy_plan=legacy,
            binding=binding,compound_consumer_pins=consumers,extra_post_source_controller_pins=list(extras.values()),
            original_source_required_pins=list(required.values()),status_revision=107,exact_r106_document_bytes_preserved=True,
            required_bound_input_names=sorted(q.reader.snapshots),report_pin=q.reader.snapshots[REPORT])
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(p['path'] for p in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['compound_contract_tests_passed']==26,'EVERY_BOUND_INPUT_FRESH_AND_CONTRACT26')
        m.g.complete(out,owner,proposed,validate)
        out['metadata_observation']=m.g.observation.summary(owner)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','compound_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
