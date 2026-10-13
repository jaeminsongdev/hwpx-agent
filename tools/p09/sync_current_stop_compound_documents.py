"""P237: 검증된 P236 결합 상태의 문서 snapshot. runtime 재검증 아님.

원 failed/STOP와 r97 문서 bytes를 보존한다. source 전체나 통과 본문을 다시
실행하지 않는다. 문서의 raw-byte suffix와 텍스트는 같은 byte 읽기에서 검사.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import accept_current_stop_compound as a
r=a.r;review=a.review;closing=a.closing
SELF='tools/p09/sync_current_stop_compound_documents.py'
TEST='tools/p09/tests/test_current_stop_compound_documents.py'
REPORT='implementation/p09/P09-237_CPU_STOP_REVIEW_AND_COMPOUND_R0098_REPORT.md'
COMPOUND=dict(path=r.p.DIR+'/p236-case078-compound-run01.v1.json',bytes=355396,
    sha256='1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462')
PREVIOUS=dict(path=r.p.DIR+'/p232-current-doc-delta-r0097-run01.v1.json',bytes=349552,
    sha256='45c2c83a326b87dc603fadc89958c5849ff9b6da6629947177565c3a081f6cbe')
DOCS=(dict(path='CURRENT_STATE.md',bytes=440591,
    sha256='aef7833bc55b3826726217a222a0af2c630d7d6b3c4199b13888578fc687baec'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=534223,
    sha256='68aa3b06b4abb641d0530f21edfe4604de43688dc2df7d2217c7dfe53bd4b2e8'))
PASS='PASS_COMPOUND_STATUS_DOCUMENT_SNAPSHOT_NOT_RUNTIME_REQUALIFICATION_OR_GATE'


def require(ok,code):r.require(ok,'COMPOUND_DOC_'+code)


def bound_bytes(q,name):
    with q.context.scope('document_read'):
        actual,buffer=q.reader._read(q.name(name),parse=True)
        q.reader._bind(name,actual)
    return buffer


def prefix(before,after):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'EXACT_OLD_BYTES_SUFFIX')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith('> 2026-10-09 P234~P237 runtime-r98 ')
        and all(word in text for word in ('runtime 수용72/249','잔여177(일반171+corpus6)',
            '미closing후보0','다음index79','whole재조정대기69','P09·A12·A13 OPEN',
            '원 STOP/FAILED 보존','CPU 보호 중단 시 자동 재시도 금지','PC 프리즈 원인·해결 미확정',
            '후속 실행 caller NOT_RUN','원 P230 caller 자체는 78 FAILED로 차단')),
        'EXACT_STATUS_AND_UNIMPLEMENTED_CALLER_BOUNDARY')
    return text


def document_contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_current_stop_compound_documents'))
    require(checked.wasSuccessful() and checked.testsRun==8 and not checked.skipped,'CONTRACT8')
    return 8


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p237-compound-status-doc-r0098-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-compound-status-document-snapshot/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_or_full_source_executed=False,runtime_requalification_performed=False,
        queue_execution_driver_ready=False,compound_receipt_pin=COMPOUND,previous_document_receipt_pin=PREVIOUS)
    try:
        owner.admit();q=r.Reader(owner,context)
        compound=review.bound_json(q,COMPOUND);previous=review.bound_json(q,PREVIOUS)
        require(compound['state']==a.PASS and compound.get('error_code') is None
            and compound['resource_stop_reason'] is None and compound['resource_watcher_cleanup_confirmed'] is True
            and compound['IO']['finished'] is True and compound['IO']['bound_inputs']==compound['IO']['final_fresh_hashes']==206
            and compound['compound_contract_tests_passed']==20
            and compound['actual_new_product_body_executed'] is False
            and compound['additional_full_source_frame_executed'] is False,'COMPLETE_FROZEN_COMPOUND')
        require(previous['state'].startswith('PASS_') and previous['document_revision']==97
            and previous['runtime_plan']['runtime_source_qualified_individual_cases']==69
            and previous['resource_stop_reason'] is None and previous['resource_watcher_cleanup_confirmed'] is True,
            'EXACT_R97_SNAPSHOT')
        previous_pins=r.p.v.pins(previous['bound_input_pins'])
        require(all(previous_pins[pin['path']]==pin for pin in DOCS),'R97_DOCUMENT_PIN_BINDING')
        root=review.bound_json(q,review.ROOT_PIN);body=review.bound_json(q,review.BODY_PIN)
        source=review.bound_json(q,a.SOURCE_PIN);prior=review.bound_json(q,closing.REVIEW_PIN)
        require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'ORIGINAL_ZERO_BYTES')
        checked=review.review(root,body)
        require(prior['state']==review.PASS and prior['review']==source['review']==checked
            and compound['compound']['original_STOP_receipt_accepted'] is False
            and compound['compound']['original_body_not_reexecuted'] is True
            and compound['compound']['separate_full_source_frame_verified'] is True,'NO_ORIGINAL_FAILURE_PROMOTION')
        sealed=r.p.v.pins(compound['bound_input_pins'])
        for name in (*closing.EXTRAS,a.SELF,a.TEST):require(q.pin(name)==sealed[name],'UNCHANGED_COMPOUND_HELPERS')
        required=r.p.v.pins(source['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        closing.validate(source,required)
        # 원 compiled inventory/수용은 literal P236 proof의 책임이다. 이 도구는
        # 전체 runtime 재검증 없이 그 검증된 상태의 snapshot만 문서화한다.
        plan=compound['runtime_plan']
        require(plan['runtime_source_qualified_individual_cases']==72 and plan['next_runtime_index']==79
            and plan['runtime_remaining_individual_cases']==177 and plan['runtime_remaining_regular_cases']==171
            and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==69,'EXACT_COMPOUND_STATUS_ONLY')
        old_names=set(previous['runtime_plan']['runtime_qualified_test_names'])
        new_names=set(plan['runtime_qualified_test_names'])
        require(len(old_names)==69 and len(new_names)==72 and old_names<new_names
            and review.NAME in new_names-old_names,'EXACT_R97_DELTA3_NO_DUPLICATE')
        prefixes=[]
        for pin in DOCS:
            archive='implementation/p09/evidence/runtime-progress-r97/'+pin['path'].split('/')[-1]
            before=bound_bytes(q,archive);require(q.reader.snapshots[archive]==dict(pin,path=archive),'EXACT_R97_ARCHIVE_BYTES')
            after=bound_bytes(q,pin['path']);prefixes.append(prefix(before,after))
        require(prefixes[0]==prefixes[1],'IDENTICAL_TWO_DOCUMENT_PREFIXES')
        report=bytes(bound_bytes(q,REPORT)).decode('utf-8')
        for pin in (COMPOUND,PREVIOUS,review.ROOT_PIN,review.BODY_PIN,closing.REVIEW_PIN,a.SOURCE_PIN):
            require(pin['sha256'] in report,'REPORT_EXACT_PROOF_HASH')
        require(all(word in report for word in ('runtime 수용 72/249','후속 실행 caller NOT_RUN',
            '프리즈 원인·해결 미확정','제품 본문 재실행 없음','새 문서 상태 snapshot')),'REPORT_NO_PROMOTION')
        out['document_contract_tests_passed']=document_contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(document_revision=98,runtime_plan=plan,exact_r97_document_bytes_preserved=True,
            original_STOP_FAILED_and_zero_preserved=True,report_pin=q.reader.snapshots[REPORT])
        candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==20
            and doc['document_contract_tests_passed']==8,'ALL20_FRESH_CONTRACT8'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','document_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
