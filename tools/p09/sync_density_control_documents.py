"""P247: 두 STOP·소규모 밀도 제어 지원·r99 문서 bytes 상태 snapshot."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import qualify_metadata_read_entry_pacing as entry
import sync_post_stop_runtime_documents as prior_docs
r=entry.r
native_review=r.acquisition
meta_review=entry.reviewed
SELF='tools/p09/sync_density_control_documents.py'
TEST='tools/p09/tests/test_density_control_documents.py'
REPORT='implementation/p09/P09-247_CPU_STOP_DENSITY_CONTROL_R0100_REPORT.md'
PREVIOUS=dict(path=r.p.DIR+'/p240-post-stop-status-doc-r0099-run01.v1.json',bytes=22730,
    sha256='77bbab276c830a841c13f4e1dc57920b32b2e4f022fdd4ff990f87527179bfe1')
ENTRY_SUPPORT=dict(path=r.p.DIR+'/p246-metadata-entry32-support-run01.v1.json',bytes=10741,
    sha256='f44f9c27d569213536cfadc14969f6ef5195f4b883cecc451609b87e859bc261')
EARLY_REVIEW_FAILURE=dict(path=r.p.DIR+'/p245-metadata-read-stop-review-run01.v1.json',bytes=4069,
    sha256='5b5b57c6a4a14b4cd2bfbf80612f853788c1c4957fe6c139c9b2b54214a6f226')
DOCS=(dict(path='CURRENT_STATE.md',bytes=443794,
    sha256='20af87971fd5da64820f39734e616d921c2ea1b58900104e879ba8d8c5826ed2'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=537426,
    sha256='60d72f6158daf93e05d538528838a32df9a8701cc1e10a861bd9b9eb0dae1cfe'))
PASS='PASS_DENSITY_CONTROL_STOP_STATUS_DOCUMENT_SNAPSHOT_NOT_RUNTIME_OR_GATE'


def require(ok,code):r.require(ok,'DENSITY_DOC_'+code)


def prefix(before,after):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'EXACT_R99_SUFFIX')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith('> 2026-10-09 P241~P247 runtime-r100 ')
        and all(word in text for word in ('runtime 수용73/249','잔여176(일반170+corpus6)','미closing후보0',
            '다음index80','whole재조정대기70','P09·A12·A13 OPEN','원 STOP/FAILED 보존',
            'CPU 보호 중단 시 자동 재시도 금지','통과 본문 재실행 없음','PC 프리즈 원인·해결 미확정',
            'Native20 전체 실제 검증 NOT_RUN','metadata32 전체 실행기 연결 NOT_RUN',
            'P239 실제 pre-GO CPU STOP 경계 NOT_RUN','실패한 P241/P244 caller 재실행 금지')),'EXACT_NOT_RUN_STATUS')
    return text


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DENSITY_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DENSITY_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DENSITY_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_density_control_documents'))
    require(checked.wasSuccessful() and checked.testsRun==10 and not checked.skipped,'CONTRACT10')
    return 10


def unchanged(q,doc,names):
    pins=r.p.v.pins(doc['bound_input_pins'])
    for name in names:require(q.pin(name)==pins[name],'SEALED_SUPPORT_SOURCE_UNCHANGED')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p247-density-control-status-doc-r0100-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-density-control-status-document-snapshot/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),product_body_or_full_source_frame_reexecuted=False,
        Native20_actual_full_runtime_qualified=False,metadata32_actual_runtime_connected=False,
        actual_pre_GO_CPU_STOP_branch_qualified=False,original_STOP_FAILED_preserved=True,
        previous_document_receipt_pin=PREVIOUS)
    try:
        owner.admit();q=r.Reader(owner,context)
        old=r.review.bound_json(q,PREVIOUS)
        require(old['state']==prior_docs.PASS and old['document_revision']==99
            and old['resource_stop_reason'] is None and old['resource_watcher_cleanup_confirmed'] is True,'SEALED_R99')
        plan=old['runtime_plan']
        require(plan['runtime_source_qualified_individual_cases']==73 and plan['next_runtime_index']==80
            and plan['runtime_remaining_individual_cases']==176 and plan['runtime_remaining_regular_cases']==170
            and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==70,'UNCHANGED73_NEXT80')
        old_pins=r.p.v.pins(old['bound_input_pins'])
        require(all(old_pins[pin['path']]==pin for pin in DOCS),'SEALED_R99_DOCUMENT_PINS')
        native_failure=r.review.bound_json(q,native_review.ROOT_PIN)
        native_light=r.review.bound_json(q,native_review.LIGHT_PIN)
        native_checked=r.review.bound_json(q,r.ACQUISITION_REVIEW)
        require(native_checked['state']==native_review.PASS
            and native_checked['review']==native_review.review(native_failure)
            and native_checked['stop_review_contract_tests_passed']==20
            and native_checked['peak_summary_contract_tests_passed']==8
            and native_checked['resource_stop_reason'] is None and native_checked['resource_watcher_cleanup_confirmed'] is True
            and native_light['prior_runtime_plan']==plan,'NATIVE_STOP_NOT_PRODUCT_ACCEPTANCE')
        unchanged(q,native_checked,(native_review.SELF,native_review.TEST))
        native_pins=r.p.v.pins(native_light['extra_frame_controller_pins'])
        for name in (r.previous.SELF,r.previous.TEST):require(q.pin(name)==native_pins[name],'P241_FROZEN_SOURCE')
        native_support=r.review.bound_json(q,r.LOWER_SUPPORT);r.lower_support.validate(native_support)
        require(native_support['state']==r.lower_support.PASS and native_support['resource_stop_reason'] is None
            and native_support['resource_watcher_cleanup_confirmed'] is True,'NATIVE_SMALL_NOT_RUNTIME')
        unchanged(q,native_support,(r.lower.SELF,r.lower.TEST,r.lower_support.SELF))
        light=r.review.bound_json(q,meta_review.LIGHT_PIN)
        require(light['state']==r.LIGHT and light['prior_runtime_plan']==plan and light['selected_test_index']==80
            and light['current_queue_runtime_contract_tests_passed']==156 and light['post_stop_runtime_contract_tests_passed']==18
            and light['uncreated_borrower_connection_contract_tests_passed']==8
            and light['lower_native_runtime_contract_tests_passed']==8
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True
            and light['preparation_IO']['finished'] is True
            and light['preparation_IO']['bound_inputs']==light['preparation_IO']['final_fresh_hashes']==228,'LIGHT190_NOT_RUNTIME')
        pins=r.p.v.pins(light['extra_frame_controller_pins'])
        for name in (r.SELF,r.TEST):require(q.pin(name)==pins[name],'P244_FROZEN_SOURCE')
        metadata_failure=r.review.bound_json(q,meta_review.ROOT_PIN)
        metadata_checked=r.review.bound_json(q,entry.REVIEW)
        require(metadata_checked['state']==meta_review.PASS
            and metadata_checked['review']==meta_review.review(metadata_failure)
            and metadata_checked['metadata_stop_contract_tests_passed']==12
            and metadata_checked['peak_summary_contract_tests_passed']==8
            and metadata_checked['resource_stop_reason'] is None
            and metadata_checked['resource_watcher_cleanup_confirmed'] is True,'METADATA_STOP_NOT_NATIVE20_SUCCESS')
        unchanged(q,metadata_checked,(meta_review.SELF,meta_review.TEST,meta_review.peak.SELF,meta_review.peak.TEST))
        early=r.review.bound_json(q,EARLY_REVIEW_FAILURE)
        require(early['state']=='FAILED_NOT_ACCEPTED'
            and early['error_code']=='P208_POST_STOP_RUNTIME_METADATA_STOP_CONTRACT12'
            and early['resource_stop_reason'] is None and early['original_failed_root_pin']==meta_review.ROOT_PIN,
            'EARLY_NEGATIVE_FIXTURE_FAILURE_PRESERVED')
        checked=r.review.bound_json(q,ENTRY_SUPPORT);entry.validate(checked)
        require(checked['state']==entry.PASS and checked['actual_runtime_connection_qualified'] is False
            and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True
            and checked['combined_future_budget']==entry.pacing.estimate_budget(native_support['rate_budget']),
            'ENTRY25_SMALL_NOT_RUNTIME_CONNECTION')
        unchanged(q,checked,(entry.pacing.SELF,entry.pacing.TEST,entry.SELF))
        require(not list((r.p.c.ROOT/r.p.DIR/'cases').glob('p241-*080*.json'))
            and not list((r.p.c.ROOT/r.p.DIR/'cases').glob('p244-*080*.json'))
            and not list((r.p.c.ROOT/r.p.DIR).glob('p244-case-*-run*.v1.json')),'NO_UNRUN_BODY_OR_PLACEHOLDER')
        for pin in (r.review.ROOT_PIN,r.review.BODY_PIN,r.review.ZERO_PIN):
            require(q.pin(pin['path'])==pin,'ORIGINAL78_FAILURE_AND_ZERO_PRESERVED')
        prefixes=[]
        for pin in DOCS:
            archive='implementation/p09/evidence/runtime-progress-r99/'+pin['path'].split('/')[-1]
            before=prior_docs.docs.bound_bytes(q,archive)
            require(q.reader.snapshots[archive]==dict(pin,path=archive),'EXACT_R99_ARCHIVE')
            prefixes.append(prefix(before,prior_docs.docs.bound_bytes(q,pin['path'])))
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
        report=bytes(prior_docs.docs.bound_bytes(q,REPORT)).decode('utf-8')
        for pin in (PREVIOUS,native_review.ROOT_PIN,native_review.LIGHT_PIN,r.ACQUISITION_REVIEW,r.LOWER_SUPPORT,
                meta_review.ROOT_PIN,meta_review.LIGHT_PIN,entry.REVIEW,ENTRY_SUPPORT,EARLY_REVIEW_FAILURE):
            require(pin['sha256'] in report,'REPORT_EXACT_PROOF_HASH')
        require(all(word in report for word in ('runtime 수용 73/249','case80 본문 NOT_RUN',
            'metadata32 전체 실행기 연결 NOT_RUN','프리즈 원인·해결 미확정','새 문서 상태 snapshot')),'REPORT_BOUNDARY')
        out['metadata_peak_review']=meta_review.peak.summarize(metadata_failure['metadata_observation']['samples'])
        out['document_contract_tests_passed']=contracts();out['peak_summary_contract_tests_passed']=meta_review.peak.contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(document_revision=100,runtime_plan=plan,exact_r99_document_bytes_preserved=True,
            report_pin=q.reader.snapshots[REPORT],combined_future_budget=checked['combined_future_budget'])
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==36
            and doc['document_contract_tests_passed']==10 and doc['peak_summary_contract_tests_passed']==8,'FRESH36_CONTRACT18'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','document_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
