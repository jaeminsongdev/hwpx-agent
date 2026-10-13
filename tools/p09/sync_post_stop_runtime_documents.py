"""P240: 실제 P238 case079·P239 지원 증거·r98 bytes의 상태 snapshot.

제품/전체 source 재실행 없음. 원 validator로 실제 새 pair를 확인하고 source
검증과 문서 상태를 구분한다. 문서 bytes·텍스트를 한 번의 읽기로 검사한다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_post_stop_compound_runtime as r
import qualify_uncreated_borrower_failure as support
import review_packed_cpu_peak_r2 as peak
import sync_current_stop_compound_documents as docs
SELF='tools/p09/sync_post_stop_runtime_documents.py'
TEST='tools/p09/tests/test_post_stop_runtime_documents.py'
REPORT='implementation/p09/P09-240_POST_STOP_RUNTIME_R0099_REPORT.md'
ROOT_PIN=dict(path=r.p.DIR+'/p238-case-079-run002.v1.json',bytes=587604,
    sha256='a26dbc68b08b95a4b4f124f3e5ccb19377b27c4f8a19e5f88acb802288ad9b31')
LIGHT_PIN=dict(path=r.p.DIR+'/p238-light-run001.v1.json',bytes=45762,
    sha256='040d552b8b923a845b9a2672c2a926c8f04201251283f7ccfc7048c883fd8399')
SUPPORT_PIN=dict(path=r.p.DIR+'/p239-uncreated-borrower-support-run01.v1.json',bytes=4694,
    sha256='c05d84929932d7b99ec988eaef0137ec53b75869f115ae5e69b625fd83a5cfc4')
PREVIOUS=dict(path=r.p.DIR+'/p237-compound-status-doc-r0098-run01.v1.json',bytes=17363,
    sha256='0814a03940aecb2102a3afa85d912ded6f1f3e55d1a1a2bac5c063218e7cedfb')
PEAK_SUPPORT=dict(path=r.p.DIR+'/p224-cpu-peak-review-run01.v1.json',bytes=8727,
    sha256='659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254')
DOCS=(dict(path='CURRENT_STATE.md',bytes=442172,
    sha256='a9eb3fa55b8a1d1869f08556b9dc2bc9d785767a17defba1ccce98b7ae08fd87'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=535804,
    sha256='c716bf7b6b22c8203622cbd933570ad3cd83cdbe4d02485fba8187e40b473fd9'))
PASS='PASS_POST_STOP_ACTUAL_PAIR_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'


def require(ok,code):r.require(ok,'POST_STOP_DOC_'+code)


def prefix(before,after):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'OLD_R98_BYTES_PRESERVED')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith('> 2026-10-09 P238~P240 runtime-r99 ')
        and all(word in text for word in ('runtime 수용73/249','잔여176(일반170+corpus6)',
            '미closing후보0','다음index80','whole재조정대기70','P09·A12·A13 OPEN',
            '원 STOP/FAILED 보존','CPU 보호 중단 시 자동 재시도 금지','PC 프리즈 원인·해결 미확정',
            'P239 실제 실행기 연결 NOT_RUN')),'EXACT_DERIVED_WORDS_AND_SUPPORT_BOUNDARY')
    return text


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_post_stop_runtime_documents'))
    require(checked.wasSuccessful() and checked.testsRun==8 and not checked.skipped,'CONTRACT8')
    return 8


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p240-post-stop-status-doc-r0099-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-post-stop-runtime-status-document-snapshot/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),product_body_or_full_source_frame_reexecuted=False,source_only_support_not_runtime_promoted=True,
        root_actual_pair_pin=ROOT_PIN,previous_document_receipt_pin=PREVIOUS,
        uncreated_borrower_support_pin=SUPPORT_PIN,uncreated_borrower_actual_runtime_connected=False)
    try:
        owner.admit();q=r.Reader(owner,context)
        root=r.review.bound_json(q,ROOT_PIN);r.closed_attempt(root)
        body=r.review.bound_json(q,root['case_receipt_pin'])
        prior=r.review.bound_json(q,r.COMPOUND);compiled=r.review.bound_json(q,r.p.m.PARENT)
        frame=root['closing_component']['source_frame']
        required=r.p.v.pins(frame['actual_byte_boundaries'][0]['actual_byte_pins'])
        extras=r.p.v.pins(root['extra_frame_controller_pins'])
        require(root['prior_runtime_plan']==prior['runtime_plan'] and root['binding']==prior['binding']
            and prior['state']==r.accepted.PASS and root['selected_test_index']==79,'EXACT_PREVIOUS72_AND_ACTUAL79')
        plan=r.record(root,body,root['case_receipt_pin'],required,root['binding'],extras,
            compiled['source_test_names'],prior['legacy_plan'],prior['runtime_plan'])
        require(required[r.p.m.EXE['path']]==r.p.m.EXE==compiled['compiled_test_executable_pin'],
            'EXACT_FIXED_EXE_AND_COMPILED_MANIFEST')
        for name in (r.SELF,r.TEST):require(q.pin(name)==required[name],'UNCHANGED_ACTUAL_EXECUTED_DRIVER')
        light=r.review.bound_json(q,LIGHT_PIN)
        require(light['state']==r.LIGHT and light['selected_test_index']==79
            and light['post_stop_runtime_contract_tests_passed']==18
            and light['current_queue_runtime_contract_tests_passed']==156
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True,
            'EXACT174_PREFLIGHT_NOT_PRODUCT')
        checked=r.review.bound_json(q,SUPPORT_PIN)
        require(checked['state']==support.PASS and checked['support_contract_tests_passed']==52
            and checked['runtime_connection_qualified'] is False
            and checked['actual_product_body_executed'] is False and checked['actual_Native_frame_or_CPU_STOP_executed'] is False
            and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True
            and checked['IO']['finished'] is True and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==12,
            'SUPPORT52_NOT_ACTUAL_CONNECTION')
        for pin in checked['bound_input_pins']:require(q.pin(pin['path'])==pin,'SUPPORT_ALL_SOURCES_UNCHANGED')
        old=r.review.bound_json(q,PREVIOUS)
        require(old['state']==docs.PASS and old['document_revision']==98
            and old['runtime_plan']==prior['runtime_plan'] and old['resource_stop_reason'] is None
            and old['resource_watcher_cleanup_confirmed'] is True,'EXACT_R98_DOCUMENT_SNAPSHOT')
        old_pins=r.p.v.pins(old['bound_input_pins'])
        require(all(old_pins[pin['path']]==pin for pin in DOCS),'OLD_DOCUMENT_PINS')
        r.review.bound_json(q,r.review.ROOT_PIN);r.review.bound_json(q,r.review.BODY_PIN)
        require(q.pin(r.review.ZERO_PIN['path'])==r.review.ZERO_PIN,'ORIGINAL_STOP_AND_ZERO_PRESERVED')
        peak_support=r.review.bound_json(q,PEAK_SUPPORT)
        require(peak_support['state']==peak.PASS and peak_support['resource_stop_reason'] is None
            and peak_support['resource_watcher_cleanup_confirmed'] is True,'SEALED_PEAK_REVIEW')
        peak_pins=r.p.v.pins(peak_support['bound_input_pins'])
        for name in (peak.SELF,peak.TEST):require(q.pin(name)==peak_pins[name],'UNCHANGED_NULL_SAFE_PEAK_SOURCE')
        out['metadata_peak_review']=peak.summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review']=peak.summarize(body['samples'])
        out['peak_summary_contract_tests_passed']=peak.contracts()
        prefixes=[]
        for pin in DOCS:
            archive='implementation/p09/evidence/runtime-progress-r98/'+pin['path'].split('/')[-1]
            before=docs.bound_bytes(q,archive)
            require(q.reader.snapshots[archive]==dict(pin,path=archive),'EXACT_R98_ARCHIVE')
            prefixes.append(prefix(before,docs.bound_bytes(q,pin['path'])))
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
        report=bytes(docs.bound_bytes(q,REPORT)).decode('utf-8')
        for pin in (ROOT_PIN,LIGHT_PIN,SUPPORT_PIN,PREVIOUS,r.COMPOUND,r.review.ROOT_PIN,r.review.BODY_PIN):
            require(pin['sha256'] in report,'REPORT_LITERAL_PROOF_HASH')
        require(all(word in report for word in ('runtime 수용 73/249','P239 실제 실행기 연결 NOT_RUN',
            '프리즈 원인·해결 미확정','제품 본문 재실행 없음','새 문서 상태 snapshot')),'REPORT_SCOPE')
        out['document_contract_tests_passed']=contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(document_revision=99,runtime_plan=plan,exact_r98_document_bytes_preserved=True,
            original_STOP_FAILED_and_zero_preserved=True,report_pin=q.reader.snapshots[REPORT])
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==34
            and doc['document_contract_tests_passed']==doc['peak_summary_contract_tests_passed']==8,'ALL34_FRESH16_CONTRACTS'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','document_contract_tests_passed','error_code',
            'resource_stop_reason','metadata_peak_review','original_parent_peak_review')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
