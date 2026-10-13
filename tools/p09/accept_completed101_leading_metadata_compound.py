"""P302: 이미 끝난 원101본문/P299fullsource를 다시 실행하지 않는 metadata-only 결합 executor.
원 P300실패 불변. 원 classifier/22계약/95·90·98x4/600/720/전체fresh읽기 유지.
새 executor4개는 metadata 두 fresh읽기로 따로 바인딩, 기존 full Native1625 범위에 포함됐다고 주장하지 않음.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import accept_completed101_compound_r5 as sealed
import leading_metadata_entry_pressure as leading
closing=sealed.closing;review=sealed.review;m=sealed.m
SELF='tools/p09/accept_completed101_leading_metadata_compound.py'
TEST='tools/p09/tests/test_completed101_leading_metadata_compound.py'
SOURCE_PATH=sealed.SOURCE_PATH
SCHEMA=sealed.SCHEMA
PASS=sealed.PASS
COUNT=sealed.COUNT
SOURCE_PIN={"path":"implementation/p09/evidence/locked-r07/p299-r5-case101-source-actual-run02.v1.json","bytes":480412,"sha256":"e9b571513abaabdf8485f6b3849b1cd9b2e38152ec71a7fb57e46c4417f1d742"}
FAILURE_PIN={"path":"implementation/p09/evidence/locked-r07/p300-r5-case101-compound-run01.v1.json","bytes":31915,"sha256":"f005fb4d34898abc65e4c2e6ba2501389a421af6519c7a278f4c4828027328af"}
QUALIFIED_PIN={"path":"implementation/p09/evidence/locked-r07/p301-leading-entry90-qualification-run01.v1.json","bytes":8056,"sha256":"a0d478bab879c7eadb4ed7a4ce8ea6787d00870e5a3159fbab2afe84842d96a8"}
QUALIFIED_CODE=[{"path":"tools/p09/leading_metadata_entry_pressure.py","bytes":6377,"sha256":"2695334be227a307cfcc69921d6326fefc1bca073239942882e36c93e8c2d412"},{"path":"tools/p09/tests/test_leading_metadata_entry_pressure.py","bytes":4799,"sha256":"53b53677af556735efa181a3d9cc467daa744c2465713824d1113e26838c4e08"}]
combine=sealed.combine
advance=sealed.advance
contracts=sealed.contracts
require=sealed.require

def review_failure(doc):
    require(doc['schema_version']==SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='metadata'
        and doc['separate_source_frame_pin']==SOURCE_PIN
        and doc['original_failed_root_pin']==review.ROOT and doc['original_stopped_parent_pin']==review.BODY
        and doc['original_zero_placeholder_pin']==review.ZERO
        and doc['actual_new_product_body_executed'] is False
        and doc['additional_full_source_frame_executed'] is False
        and doc.get('compound_contract_tests_passed') is None and doc.get('runtime_plan') is None
        and doc.get('compound') is None,'PRIOR_METADATA_STOP_NOT_COMPOUND_OR_SOURCE_RERUN')
    row=doc['IO'];pressure=row['near_saturation_read_backpressure'];early=row['early_metadata_pressure']['original_early_source_algorithm_statistics']
    require(row['read_passes']==row['bound_inputs']==69 and row['final_fresh_hashes']==0
        and row['bytes_read']==4664975 and row['finished'] is False
        and row['metadata_read_entry_pacing']['entry_calls']==70
        and row['metadata_read_entry_pacing']['failed_calls']==1
        and pressure['warning_entries']==1 and pressure['completed_pause_windows']==7
        and pressure['requested_pause_seconds']==3.5 and early['warning_entries']==0,
        'PRIOR95_WAIT_PRECEDED_OUTER90_PARTIAL_NOT_ACCEPTED')
    obs=doc['metadata_observation']
    require(obs['completed_sample_count']==len(obs['samples'])==17
        and obs['own_cpu_max_machine_percent']==1.318267 and obs['own_private_max_bytes']==44195840
        and obs['system_cpu_max_percent']==100
        and all(x['system_cpu_percent']==100 and x['parent_cpu_machine_percent']==0
            and x['audited_logical_read_bytes_delta']==0 for x in obs['samples'][-4:]),
        'OBSERVED_ZERO_OWN_WORK_LAST4_NOT_CAUSE')
    return dict(original_failed_compound_preserved=True,failed_compound_accepted=False,
        independent_full_source_receipt_preserved=True,product_body_or_full_source_reexecution_allowed=False,
        metadata_only_new_executor_qualified=True,old95_wait_entered_before_outer90=True,
        original95_and90_callbacks_and_all_hard_guards_retained=True,
        CPU_cause_or_PC_freeze_resolution_established=False)

def review_contracts(doc):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'));import test_completed101_leading_metadata_compound as t
    with patch.object(t,'FIXTURE',doc),patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')),patch('threading.Thread.start',side_effect=AssertionError('NO_NEW_THREAD')):
        r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
    require(r.wasSuccessful() and r.testsRun==12 and not r.skipped,'PRIOR_STOP12')
    return 12

def validate(doc,*args,previous_failed):
    sealed.validate(doc,*args)
    x=doc['IO']['leading_metadata_entry_pressure']
    require(doc['reviewed_previous_compound_STOP']==review_failure(previous_failed)
        and doc['previous_failed_compound_pin']==FAILURE_PIN and doc['leading_entry_qualification_pin']==QUALIFIED_PIN
        and doc['prior_compound_STOP_contract_tests_passed']==12
        and doc['leading_metadata_contract_tests_passed']==18
        and len(doc['post_source_metadata_executor_pins'])==4
        and doc['post_source_metadata_executor_claimed_in_original_Native_scope'] is False
        and x['calls']==x['completed_original_reads']==doc['IO']['read_passes'] and x['failed_calls']==0
        and x['leading_binding_active'] is False and x['original_inner95_and90_callbacks_unmodified'] is True
        and x['original_entry_pacer_and_reader_retained'] is True
        and x['original_hard_CPU_RAM_IO600_720_and_all_reads_preserved'] is True
        and x['new_sampler_or_thread_started'] is False,'EXACT_METADATA_LEADING90_AND_OLD_CLASSIFIER')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--source-bytes',type=int,required=True);ap.add_argument('--source-sha256',required=True)
    args=ap.parse_args();require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99
        and 0<args.source_bytes<=16777216 and re.fullmatch('[0-9a-f]{64}',args.source_sha256),'CWD_RUN_LITERAL_SOURCE_PIN')
    # 생산 코드도 독립 source scope에 포함된다. 생성된 receipt pin만 인자로 바인딩하여
    # source가 통과한 뒤 코드를 바꾸는 순환 hash 의존성을 만들지 않는다.
    source_pin=dict(path=SOURCE_PATH,bytes=args.source_bytes,sha256=args.source_sha256)
    require(source_pin==SOURCE_PIN,'LITERAL_ALREADY_COMPLETED_SOURCE_ONLY')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p302-case101-leading-metadata-compound-run{args.run:02}.v1.json';require(not destination.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),actual_new_product_body_executed=False,
        additional_full_source_frame_executed=False,original_failed_root_pin=review.ROOT,original_stopped_parent_pin=review.BODY,
        original_zero_placeholder_pin=review.ZERO,stop_review_pin=closing.REVIEW_PIN,separate_source_frame_pin=source_pin)
    try:
        owner.admit();stage='metadata';q=leading.Reader(owner,context)
        previous_failed=m.m.review.bound_json(q,FAILURE_PIN)
        out.update(previous_failed_compound_pin=FAILURE_PIN,reviewed_previous_compound_STOP=review_failure(previous_failed),
            prior_compound_STOP_contract_tests_passed=review_contracts(previous_failed))
        qualified=m.m.review.bound_json(q,QUALIFIED_PIN)
        require(qualified['state']=='PASS_LEADING_ENTRY90_REAL_READER_NOT_COMPOUND_RUNTIME_OR_GATE'
            and qualified['contract_tests_passed']==18 and qualified['resource_stop_reason'] is None
            and qualified['resource_watcher_cleanup_confirmed'] is True and qualified['qualified_code_pins']==QUALIFIED_CODE,
            'QUALIFIED_REAL_READER18')
        for pin in QUALIFIED_CODE:require(q.pin(pin['path'])==pin,'UNCHANGED_LEADING_CODE')
        out.update(leading_entry_qualification_pin=QUALIFIED_PIN,leading_metadata_contract_tests_passed=leading.contracts(),
            post_source_metadata_executor_pins=[q.pin(n) for n in (SELF,TEST,leading.SELF,leading.TEST)],
            post_source_metadata_executor_claimed_in_original_Native_scope=False)
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
        m.g.complete(out,owner,proposed,lambda doc:validate(doc,root,body,source,names,expected,exe,original,extras,legacy,base,previous_failed=previous_failed))
        out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:
            writer=m.r.packed.dump if out['state']==PASS else m.r.compact.dump
            writer(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','compound_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
