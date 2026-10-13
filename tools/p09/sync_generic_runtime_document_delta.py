"""P216: 고정 검증기로 원 runtime 큐와 다음 문서 revision을 대조한다.

문서 작성/제품 실행은 하지 않는다. 이전 문서 receipt의 실제 pin과 보존본,
원 strict runtime 검사, 최종 fresh hash 및 정리 뒤에만 새 결과를 수용한다.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_generic_locked_runtime as g

p=g.p
SELF='tools/p09/sync_generic_runtime_document_delta.py'
TEST='tools/p09/tests/test_generic_runtime_document_delta.py'
SCHEMA='hwpx-agent.p09-generic-runtime-document-delta/v1'
PASS='PASS_GENERIC_RUNTIME_DOCUMENT_DELTA_NOT_WHOLE_OR_GATE'
PREVIOUS_SCHEMA='hwpx-agent.p09-generic-locked-progress-doc/v1'
PREVIOUS_PASS='PASS_GENERIC_RUNTIME15_DOC_SYNC_NOT_WHOLE_OR_GATE'
ROOT_DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')


def require(ok,code):p.require(ok,'GENERIC_DELTA_'+code)


def paths(revision,previous,report):
    require(type(revision) is int and 80<=revision<=9999,'REVISION')
    require(isinstance(previous,str) and re.fullmatch(re.escape(p.DIR)+
        r'/(?:p215-generic-doc-sync|p216-generic-doc-delta-r[0-9]{4})-run[0-9]{2}\.v1\.json',previous),
        'OWN_PRIOR_DOCUMENT_RECEIPT_PATH')
    require(isinstance(report,str) and re.fullmatch(r'implementation/p09/P09-216_GENERIC_RUNTIME_R[0-9]{4}_REPORT\.md',report),
        'OWN_REPORT_PATH')
    require(report==f'implementation/p09/P09-216_GENERIC_RUNTIME_R{revision:04}_REPORT.md','EXACT_REPORT_REVISION')
    return f'implementation/p09/evidence/runtime-progress-r{revision-1}/'


def prior(doc,revision):
    require((doc['schema_version'],doc['state']) in ((PREVIOUS_SCHEMA,PREVIOUS_PASS),(SCHEMA,PASS))
        and doc.get('error_code') is None and doc['document_revision']==revision-1
        and doc['new_product_or_full_source_frame_executed'] is False
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('product_complete','full249_current_qualified',
            'whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'signed16_current_qualified','PC_freeze_resolved')),'COMPLETE_PREVIOUS_DOCUMENT_NOT_PRODUCT')
    rows=doc['bound_input_pins'];require(isinstance(rows,list) and len(rows)<=4096,'BOUNDED_PREVIOUS_PINS')
    pins={}
    for name in ROOT_DOCS:
        matches=[row for row in rows if row['path']==name]
        require(len(matches)==1,'EXACT_PREVIOUS_ROOT_DOC_PIN');pins[name]=matches[0]
    return pins


def words(plan):
    return (f"runtime 수용{plan['runtime_source_qualified_individual_cases']}/249",
        f"잔여{plan['runtime_remaining_individual_cases']}(일반{plan['runtime_remaining_regular_cases']}+corpus{plan['runtime_remaining_corpus_cases']})",
        '미closing후보0',f"다음index{plan['next_runtime_index']}",
        f"whole재조정대기{plan['all_successful_bodies_pending_whole_reconciliation']}",
        'P09·A12·A13 OPEN','PC 프리즈 원인·해결 미확정','원 STOP/FAILED 보존')


def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_generic_runtime_document_delta as tests
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DELTA_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DELTA_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DELTA_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==8 and not result.skipped,'CONTRACT8')
    return 8


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',type=int,required=True)
    ap.add_argument('--previous',required=True);ap.add_argument('--report',required=True)
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    history=paths(args.revision,args.previous,args.report)
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p216-generic-doc-delta-r{args.revision:04}-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=None;candidate=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        new_product_or_full_source_frame_executed=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        previous=q.json(args.previous);old_pins=prior(previous,args.revision)
        legacy,base,names,expected,exe,required,extras=g.anchor(q)
        binding=p.v.identity(names,expected,exe);plan=g.progress(q,legacy,base,names,required,binding,extras)
        require(plan['runtime_source_qualified_individual_cases']>previous['runtime_plan']['runtime_source_qualified_individual_cases']
            and plan['runtime_successful_candidates_requiring_closing']==0,'ACTUAL_NEW_RUNTIME_PROGRESS')
        out.update(generic_contract_tests_passed=g.contracts((legacy,plan,names)),document_delta_contract_tests_passed=contracts())
        prefixes=[]
        for name,pin in old_pins.items():
            archived=history+name.split('/')[-1]
            require(q.pin(archived)==dict(pin,path=archived),'EXACT_PREVIOUS_DOCUMENT_PIN')
            before=q.text(archived);after=q.text(name)
            require(after.endswith(before) and len(after)>len(before),'OLD_DOCUMENT_HISTORY_PRESERVED')
            prefixes.append(after[:-len(before)])
            require(q.reader._read(name,parse=True)[1].endswith(q.reader._read(archived,parse=True)[1]),'EXACT_OLD_BYTE_SUFFIX')
        require(prefixes[0]==prefixes[1]
            and re.match(r'^> [0-9]{4}-[0-9]{2}-[0-9]{2} P216 generic-runtime-r'+str(args.revision)+r' ',prefixes[0]),
            'IDENTICAL_CURRENT_PREFIX')
        require(all(s in prefixes[0] for s in words(plan)),'DERIVED_RUNTIME_COUNTS_AND_NO_GATE')
        report=q.text(args.report)
        require(all(s in report for s in words(plan)) and 'CPU 보호 중단 시 자동 재시도 금지' in report,
            'REPORT_PROGRESS_AND_PROTECTION_BOUNDARIES')
        new_receipts=[];before=previous['runtime_plan']['runtime_source_qualified_individual_cases']
        prior_names=set(previous['runtime_plan']['runtime_qualified_test_names'])
        for path in sorted((p.c.ROOT/p.DIR).glob('p215-case-*-run*.v1.json')):
            match=g.FILE.fullmatch(path.name);require(match is not None,'EXACT_GENERIC_FILENAME')
            index=int(match[1]);require(1<=index<=len(names),'EXACT_INVENTORY_INDEX')
            if names[index-1] in prior_names:continue
            name=path.relative_to(p.c.ROOT).as_posix();pin=q.pin(name)
            require(pin['sha256'] in report,'REPORTED_NEW_ACTUAL_RECEIPT_SHA');new_receipts.append(pin)
        require(len(new_receipts)==plan['runtime_source_qualified_individual_cases']-before,'EXACT_NEW_PAIR_COUNT')
        for name in (SELF,TEST,args.previous):q.pin(name)
        q.finish()
        candidate=dict(state=PASS,document_revision=args.revision,runtime_plan=plan,
            previous_document_receipt_pin=q.reader.snapshots[args.previous],new_actual_runtime_pair_pins=new_receipts,
            exact_prior_document_bytes_preserved=True,original_failure_receipts_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes'],'FINAL_ALL_FRESH')
        g.complete(out,owner,candidate,validate)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','document_revision','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
