"""P232: current 큐 문서 revision의 엄격한 재사용 delta. 이전 실제 pin/원문 보존 필수."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_current_queue_runtime as runtime
import sync_generic_runtime_document_delta as documents
import sync_current_queue_documents as prior_driver

p=runtime.p;g=runtime.g
SELF='tools/p09/sync_current_queue_document_delta.py'
TEST='tools/p09/tests/test_current_queue_document_delta.py'
PASS='PASS_CURRENT_QUEUE_REUSABLE_DOCUMENT_DELTA_NOT_WHOLE_OR_GATE'


def previous(doc, revision):
    runtime.require(type(revision) is int and 95<=revision<=9999
        and (doc['schema_version'],doc['state']) in (
            ('hwpx-agent.p09-current-queue-document-delta/v1',prior_driver.PASS),
            ('hwpx-agent.p09-current-queue-reusable-document-delta/v1',PASS))
        and doc['document_revision']==revision-1 and doc.get('error_code') is None
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['IO']['finished'] is True and type(doc['IO']['bound_inputs']) is int
        and 1<=doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']<=4096
        and doc['current_queue_runtime_contract_tests_passed']==156
        and doc['document_contract_tests_passed']==(16 if revision==95 else 24)
        and doc['new_product_or_full_source_frame_executed'] is False
        and doc['exact_prior_document_bytes_preserved'] is True
        and doc['original_STOP_and_zero_body_preserved'] is True
        and doc['runtime_plan']['runtime_successful_candidates_requiring_closing']==0
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[key] is False for key in ('product_complete','PC_freeze_resolved',
            'whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified')),
        'DOCUMENT_PREVIOUS_SEALED_CURRENT_NOT_PRODUCT')
    pins={}
    for name in documents.ROOT_DOCS:
        matches=[pin for pin in doc['bound_input_pins'] if pin['path']==name]
        runtime.require(len(matches)==1,'DOCUMENT_PREVIOUS_ROOT_PIN');pins[name]=matches[0]
    return pins


def paths(args):
    import re
    runtime.require(type(args.revision) is int and 95<=args.revision<=9999
        and type(args.bytes) is int and 1<=args.bytes<=runtime.packed.MAX_BYTES
        and re.fullmatch('[0-9a-f]{64}',args.sha) is not None,
        'DOCUMENT_BOUNDED_EXPECTED_PRIOR_PIN')
    expected=(p.DIR+'/p231-current-doc-r0094-run01.v1.json' if args.revision==95 else
        f'{p.DIR}/p232-current-doc-delta-r{args.revision-1:04}-run01.v1.json')
    runtime.require(args.previous==expected and args.report==
        f'implementation/p09/P09-232_CURRENT_QUEUE_RUNTIME_R{args.revision:04}_REPORT.md',
        'DOCUMENT_EXACT_PRIOR_AND_REPORT')
    return dict(path=args.previous,bytes=args.bytes,sha256=args.sha)


def contracts():
    original=prior_driver.contracts()
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_current_queue_document_delta as tests
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CURRENT_DOCUMENT_CHILD')), \
         patch('subprocess.run',side_effect=AssertionError('NO_CURRENT_DOCUMENT_CHILD')), \
         patch('threading.Thread.start',side_effect=AssertionError('NO_CURRENT_DOCUMENT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    runtime.require(original==16 and result.wasSuccessful() and result.testsRun==8 and not result.skipped,
        'DOCUMENT_CONTRACT16_PLUS8')
    return 24


def main():
    parser=argparse.ArgumentParser()
    for name in ('revision','bytes','run'):parser.add_argument('--'+name,type=int,required=True)
    for name in ('previous','sha','report'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();prior_pin=paths(args)
    runtime.require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'DOCUMENT_CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p232-current-doc-delta-r{args.revision:04}-run{args.run:02}.v1.json'
    runtime.require(not destination.exists(),'DOCUMENT_FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-current-queue-reusable-document-delta/v1',state='FAILED_NOT_ACCEPTED',
        **p.r.flags(),new_product_or_full_source_frame_executed=False,
        synthetic_STOP_connection_only_not_live_CPU_stress_test=True,PC_freeze_resolution_established=False)
    try:
        owner.admit();q=runtime.Reader(owner,context)
        runtime.require(q.pin(prior_pin['path'])==prior_pin,'DOCUMENT_LITERAL_PREVIOUS')
        old=q.json(prior_pin['path']);oldpins=previous(old,args.revision)
        legacy,base,names,expected,exe,required,extras=runtime.anchor(q)
        binding=p.v.identity(names,expected,exe)
        plan=runtime.progress(q,legacy,base,names,required,binding,extras)
        delta=plan['runtime_source_qualified_individual_cases']-old['runtime_plan']['runtime_source_qualified_individual_cases']
        runtime.require(1<=delta<=8 and plan['runtime_successful_candidates_requiring_closing']==0,
            'DOCUMENT_BOUNDED_NEW_ACTUAL_NOT_STOP_RECLASSIFIED')
        # 과거 STOP next60은 감사 fixture, 현재 next는 별도 current fixture로 검증한다.
        out['current_queue_runtime_contract_tests_passed']=runtime.contracts((legacy,plan,names,q.json(runtime.STOP_PIN['path'])))
        out['document_contract_tests_passed']=contracts()
        prefixes=[]
        for name,pin in oldpins.items():
            archive=f'implementation/p09/evidence/runtime-progress-r{args.revision-1}/'+name.split('/')[-1]
            runtime.require(q.pin(archive)==dict(pin,path=archive),'DOCUMENT_ARCHIVE_EXACT_PIN')
            before=q.text(archive);after=q.text(name)
            runtime.require(after.endswith(before) and len(after)>len(before),'DOCUMENT_OLD_SUFFIX')
            prefixes.append(after[:-len(before)])
            runtime.require(q.reader._read(name,parse=True)[1].endswith(q.reader._read(archive,parse=True)[1]),
                'DOCUMENT_EXACT_BYTE_SUFFIX')
        runtime.require(prefixes[0]==prefixes[1] and prefixes[0].startswith(f'> 2026-10-09 P232 runtime-r{args.revision} '),
            'DOCUMENT_IDENTICAL_PREFIX')
        report=q.text(args.report)
        for word in (*documents.words(plan),'CPU 보호 중단 시 자동 재시도 금지'):
            runtime.require(word in report and word in prefixes[0],'DOCUMENT_DERIVED_WORDS')
        runtime.require('실제 Native pressure frame 연결' in report and '실제 packed parent/root writer 연결' in report
            and '실제 CPU STOP 재현은 NOT_RUN' in report and runtime.STOP_PIN['sha256'] in report
            and runtime.CONNECTION_PIN['sha256'] in report,'DOCUMENT_REAL_AND_SYNTHETIC_BOUNDARIES')
        prior_names=set(old['runtime_plan']['runtime_qualified_test_names']);new=[]
        for path in sorted((p.c.ROOT/p.DIR).glob('p230-case-*-run*.v1.json')):
            doc=q.json(path.relative_to(p.c.ROOT).as_posix())
            if doc['selected_test_name'] not in prior_names:
                pin=q.pin(path.relative_to(p.c.ROOT).as_posix());runtime.require(pin['sha256'] in report,'DOCUMENT_NEW_SHA')
                new.append(pin)
        runtime.require(len(new)==delta,'DOCUMENT_EXACT_NEW_PAIRS')
        for name in (SELF,TEST,prior_driver.SELF,prior_driver.TEST,documents.SELF,documents.TEST):q.pin(name)
        q.finish();candidate=dict(state=PASS,document_revision=args.revision,runtime_plan=plan,
            previous_document_receipt_pin=prior_pin,new_actual_runtime_pair_pins=new,
            exact_prior_document_bytes_preserved=True,original_STOP_and_zero_body_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=p.b.run.original.closed_error(e)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=g.observation.summary(owner)
        g.complete(out,owner,candidate,lambda row:runtime.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']
            and row['current_queue_runtime_contract_tests_passed']==156 and row['document_contract_tests_passed']==24,
            'DOCUMENT_ALL_FRESH'))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({key:out.get(key) for key in ('state','document_revision','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
