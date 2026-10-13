"""P226 STOP notice: 이전 문서 byte 보존과 실패·지원 한계만 동기화. 재개 승인 아님."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_packed_pressure_runtime as r
import sync_generic_runtime_document_delta as documents

SELF='tools/p09/sync_packed_stop_notice.py'
TEST='tools/p09/tests/test_packed_stop_notice.py'
REPORT='implementation/p09/P09-226_CPU_STOP_FAILURE_WRITER_REPORT.md'
REVIEW=dict(path=r.p.DIR+'/p226-stop-review-run01.v1.json',bytes=14694,
    sha256='f1ee9b8c0250cecd2ec51852f5a8dcfc8c9ff5ca9499f39ddc57a75d4a3eb530')
PREVIOUS=dict(path=r.p.DIR+'/p216-generic-doc-delta-r0091-run01.v1.json',bytes=314452,
    sha256='30d087a42ca86f1f8cb4c32f264302e9192d25f787ce099c8e76af309257081c')
PASS='PASS_PACKED_STOP_DOCUMENT_NOTICE_NOT_RUNTIME_RESUME_OR_GATE'


def check_review(review):
    r.require(review['state']=='PASS_BOUNDED_STOP_REVIEW_AND_FAILURE_WRITER_SUPPORT_NOT_RUNTIME_OR_GATE'
        and review.get('error_code') is None and review['resource_stop_reason'] is None
        and review['resource_watcher_cleanup_confirmed'] is True
        and review['IO']['finished'] is True
        and review['IO']['bound_inputs']==review['IO']['final_fresh_hashes']==12
        and review['failure_writer_contract_tests_passed']==16
        and review['peak_summary_contract_tests_passed']==8
        and review['failure_writer_actual_connection'] is False
        and review['runtime_resume_authorized'] is False
        and review['original_failure_preserved'] is True
        and review['empty_body_semantic_or_job_result_established'] is False
        and review['product_body_reexecuted'] is False,'STOP_NOTICE_SUPPORT_NOT_RESUME')
    plan=review['runtime_plan']
    r.require(plan['runtime_source_qualified_individual_cases']==53
        and plan['runtime_remaining_individual_cases']==196
        and plan['next_runtime_index']==60,'STOP_NOTICE_EXACT_PLAN')
    return plan


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_packed_stop_notice as tests
    with patch('subprocess.Popen',side_effect=AssertionError('NO_NOTICE_CHILD')), \
         patch('subprocess.run',side_effect=AssertionError('NO_NOTICE_CHILD')), \
         patch('threading.Thread.start',side_effect=AssertionError('NO_NOTICE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    r.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'STOP_NOTICE_CONTRACT6')
    return 6


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,required=True);args=parser.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'STOP_NOTICE_CWD_RUN')
    destination=r.p.c.ROOT/f'{r.p.DIR}/p226-stop-notice-run{args.run:02}.v1.json'
    r.require(not destination.exists(),'STOP_NOTICE_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-packed-stop-document-notice/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),new_product_or_full_source_frame_executed=False,runtime_resume_authorized=False,
        failure_writer_actual_connection=False)
    try:
        owner.admit();q=r.Reader(owner,context)
        for pin in (REVIEW,PREVIOUS):r.require(q.pin(pin['path'])==pin,'STOP_NOTICE_LITERAL_PIN')
        review=q.json(REVIEW['path']);previous=q.json(PREVIOUS['path']);plan=check_review(review)
        pins=documents.prior(previous,92)
        r.require(len(review['bound_input_pins'])==12 and
            all(q.pin(pin['path'])==pin for pin in review['bound_input_pins']),'STOP_NOTICE_SUPPORT_SOURCE_FRESH')
        for pin in (review['original_stop_pin'],review['empty_body_pin'],review['last_accepted_pin']):
            r.require(q.pin(pin['path'])==pin,'STOP_NOTICE_EVIDENCE_UNCHANGED')
        prefixes=[]
        for name,pin in pins.items():
            archived='implementation/p09/evidence/runtime-progress-r91/'+name.split('/')[-1]
            r.require(q.pin(archived)==dict(pin,path=archived),'STOP_NOTICE_OLD_BYTE_PIN')
            before=q.text(archived);after=q.text(name)
            r.require(after.endswith(before) and len(after)>len(before),'STOP_NOTICE_OLD_SUFFIX')
            prefixes.append(after[:-len(before)])
        r.require(prefixes[0]==prefixes[1] and prefixes[0].startswith('> 2026-10-09 P226 CPU_STOP_NOTICE '),
            'STOP_NOTICE_IDENTICAL_PREFIX')
        report=q.text(REPORT)
        for word in (*documents.words(plan),'CPU 보호 중단 시 자동 재시도 금지'):
            r.require(word in report and word in prefixes[0],'STOP_NOTICE_DERIVED_WORDS')
        r.require(REVIEW['sha256'] in report and '실제 parent에 아직 연결되지 않은' in report
            and '0bytes' in report and 'Job 값 없음은 0이 아님' in report,'STOP_NOTICE_LIMITS')
        out['notice_contract_tests_passed']=contracts()
        for path in (SELF,TEST,documents.SELF):q.pin(path)
        q.finish();candidate=dict(state=PASS,document_revision=92,runtime_plan=plan,
            original_stop_preserved=True,exact_prior_document_bytes_preserved=True,
            support_review_pin=REVIEW,previous_document_receipt_pin=PREVIOUS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=r.p.b.run.original.closed_error(e)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda row:r.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']
            and row['notice_contract_tests_passed']==6,'STOP_NOTICE_ALL_FRESH'))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({key:out.get(key) for key in ('state','error_code','resource_stop_reason',
            'resource_watcher_cleanup_confirmed','notice_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
