"""P229: P226 STOP notice에서 P228 새 actual 증거로 문서 delta. 원 STOP는 보존."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_deferred_failure_runtime as runtime
import sync_generic_runtime_document_delta as documents

p=runtime.p;g=runtime.g
SELF='tools/p09/sync_deferred_runtime_documents.py'
TEST='tools/p09/tests/test_deferred_runtime_documents.py'
PREVIOUS=dict(path=p.DIR+'/p226-stop-notice-run01.v1.json',bytes=14737,
    sha256='df2713cd6b0461108bfa486ca13d3196f990034702252d74004efebe133ce1a7')
REPORT='implementation/p09/P09-229_DEFERRED_FAILURE_RUNTIME_R0093_REPORT.md'
PASS='PASS_DEFERRED_RUNTIME_DOCUMENT_DELTA_NOT_WHOLE_OR_GATE'


def previous(doc):
    runtime.require(doc['schema_version']=='hwpx-agent.p09-packed-stop-document-notice/v1'
        and doc['state']=='PASS_PACKED_STOP_DOCUMENT_NOTICE_NOT_RUNTIME_RESUME_OR_GATE'
        and doc['document_revision']==92 and doc.get('error_code') is None
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==22
        and doc['runtime_resume_authorized'] is False and doc['failure_writer_actual_connection'] is False
        and doc['original_stop_preserved'] is True
        and doc['runtime_plan']['runtime_source_qualified_individual_cases']==53,
        'DOCUMENT_PREVIOUS_STOP_NOTICE_NOT_PRODUCT')
    pins={}
    for name in documents.ROOT_DOCS:
        matches=[pin for pin in doc['bound_input_pins'] if pin['path']==name]
        runtime.require(len(matches)==1,'DOCUMENT_PREVIOUS_ROOT_PIN');pins[name]=matches[0]
    return pins


def contracts():
    original=documents.contracts()
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_deferred_runtime_documents as tests
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DEFERRED_DOCUMENT_CHILD')), \
         patch('subprocess.run',side_effect=AssertionError('NO_DEFERRED_DOCUMENT_CHILD')), \
         patch('threading.Thread.start',side_effect=AssertionError('NO_DEFERRED_DOCUMENT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    runtime.require(original==8 and result.wasSuccessful() and result.testsRun==4 and not result.skipped,
        'DOCUMENT_CONTRACT8_PLUS4')
    return 12


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,required=True);args=parser.parse_args()
    runtime.require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'DOCUMENT_CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p229-deferred-doc-r0093-run{args.run:02}.v1.json'
    runtime.require(not destination.exists(),'DOCUMENT_FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-deferred-runtime-document-delta/v1',state='FAILED_NOT_ACCEPTED',
        **p.r.flags(),new_product_or_full_source_frame_executed=False,
        synthetic_STOP_connection_only_not_live_CPU_stress_test=True,PC_freeze_resolution_established=False)
    try:
        owner.admit();q=runtime.Reader(owner,context)
        runtime.require(q.pin(PREVIOUS['path'])==PREVIOUS,'DOCUMENT_LITERAL_PREVIOUS')
        old=q.json(PREVIOUS['path']);oldpins=previous(old)
        legacy,base,names,expected,exe,required,extras=runtime.anchor(q)
        binding=p.v.identity(names,expected,exe)
        plan=runtime.progress(q,legacy,base,names,required,binding,extras)
        runtime.require(plan['runtime_source_qualified_individual_cases']==54
            and plan['runtime_source_qualified_individual_cases']==old['runtime_plan']['runtime_source_qualified_individual_cases']+1
            and plan['next_runtime_index']==61 and plan['runtime_successful_candidates_requiring_closing']==0,
            'DOCUMENT_ONE_NEW_ACTUAL_NOT_STOP_RECLASSIFIED')
        # P228의 첫 재개 계약은 감사된 과거 next60/base53에 고정돼 있다.
        # 현재54는 위 progress/record로 검증하고 계약 scope를 미래 재사용으로 넓히지 않는다.
        out['deferred_runtime_contract_tests_passed']=runtime.contracts((legacy,base,names,q.json(runtime.STOP_PIN['path'])))
        out['document_contract_tests_passed']=contracts()
        prefixes=[]
        for name,pin in oldpins.items():
            archive='implementation/p09/evidence/runtime-progress-r92/'+name.split('/')[-1]
            runtime.require(q.pin(archive)==dict(pin,path=archive),'DOCUMENT_ARCHIVE_EXACT_PIN')
            before=q.text(archive);after=q.text(name)
            runtime.require(after.endswith(before) and len(after)>len(before),'DOCUMENT_OLD_SUFFIX')
            prefixes.append(after[:-len(before)])
            runtime.require(q.reader._read(name,parse=True)[1].endswith(q.reader._read(archive,parse=True)[1]),
                'DOCUMENT_EXACT_BYTE_SUFFIX')
        runtime.require(prefixes[0]==prefixes[1] and prefixes[0].startswith('> 2026-10-09 P229 runtime-r93 '),
            'DOCUMENT_IDENTICAL_PREFIX')
        report=q.text(REPORT)
        for word in (*documents.words(plan),'CPU 보호 중단 시 자동 재시도 금지'):
            runtime.require(word in report and word in prefixes[0],'DOCUMENT_DERIVED_WORDS')
        runtime.require('실제 Native pressure frame 연결' in report and '실제 packed parent/root writer 연결' in report
            and '실제 CPU STOP 재현은 NOT_RUN' in report and runtime.STOP_PIN['sha256'] in report
            and runtime.CONNECTION_PIN['sha256'] in report,'DOCUMENT_REAL_AND_SYNTHETIC_BOUNDARIES')
        prior_names=set(old['runtime_plan']['runtime_qualified_test_names']);new=[]
        for path in sorted((p.c.ROOT/p.DIR).glob('p228-case-*-run*.v1.json')):
            doc=q.json(path.relative_to(p.c.ROOT).as_posix())
            if doc['selected_test_name'] not in prior_names:
                pin=q.pin(path.relative_to(p.c.ROOT).as_posix());runtime.require(pin['sha256'] in report,'DOCUMENT_NEW_SHA')
                new.append(pin)
        runtime.require(len(new)==1,'DOCUMENT_ONE_NEW_PAIR')
        for name in (SELF,TEST,documents.SELF,documents.TEST):q.pin(name)
        q.finish();candidate=dict(state=PASS,document_revision=93,runtime_plan=plan,
            previous_document_receipt_pin=PREVIOUS,new_actual_runtime_pair_pins=new,
            exact_prior_document_bytes_preserved=True,original_STOP_and_zero_body_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=p.b.run.original.closed_error(e)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        g.complete(out,owner,candidate,lambda row:runtime.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']
            and row['deferred_runtime_contract_tests_passed']==144 and row['document_contract_tests_passed']==12,
            'DOCUMENT_ALL_FRESH'))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({key:out.get(key) for key in ('state','document_revision','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
