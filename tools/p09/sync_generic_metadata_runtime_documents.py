"""P254: 실제81의 상태 snapshot. 제품 재실행·전체/Gate 수용은 하지 않는다."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_generic_metadata_runtime_r2 as m
import sync_metadata_entry_runtime_documents as previous_docs
import sync_current_stop_compound_documents as bytes_docs
import review_packed_cpu_peak_r2 as peak

SELF='tools/p09/sync_generic_metadata_runtime_documents.py'
TEST='tools/p09/tests/test_generic_metadata_runtime_documents.py'
REPORT='implementation/p09/P09-254_GENERIC_METADATA_RUNTIME_R0102_REPORT.md'
PREVIOUS=dict(path=m.p.DIR+'/p251-metadata-entry-status-doc-r0101-run01.v1.json',bytes=23578,
    sha256='f717f7e05dc4ae518e1d27e28c206478bd96a0ca50d340724e1300d1f55f816f')
ROOT_PIN=dict(path=m.p.DIR+'/p253-case-081-run003.v1.json',bytes=615984,
    sha256='22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246')
LIGHT_PIN=dict(path=m.p.DIR+'/p253-light-run002.v1.json',bytes=52654,
    sha256='251416aca6b7e1bc84771447f51a5e3f9b8cc36fecd8b18181f95daca8295c06')
DOCS=(dict(path='CURRENT_STATE.md',bytes=447687,
    sha256='8794e91359b1f09eeb0a0a6cee261d19d2509b08681d385fab401e51dc466e79'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=541319,
    sha256='2b2ee98911041d9cc1dd998e4a71b565991207230099c5529355286ad8f3fe64'))
PASS='PASS_GENERIC_METADATA_ACTUAL81_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'
WORDS=('runtime 수용75/249','잔여174(일반168+corpus6)','미closing후보0','다음index82',
    'whole재조정대기72','P09·A12·A13 OPEN','원 STOP/FAILED 보존',
    'CPU 보호 중단 시 자동 재시도 금지','통과 본문 재실행 없음',
    'PC 프리즈 원인·해결 미확정','P239 실제 pre-GO CPU STOP 경계 NOT_RUN',
    '원600초·CPU/RAM 기준은 변경하지 않음','index82 NOT_RUN','중복 호출 검토·최적화 후 재개')


def require(ok,code):m.require(ok,'GENERIC_DOC_'+code)


def prefix(before,after):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'EXACT_R101_SUFFIX')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith('> 2026-10-09 P252~P254 runtime-r102 ')
        and all(word in text for word in WORDS),'ACTUAL75_NOT_WHOLE_OR_GATE')
    return text


def next_read_projection(preparation_reads):
    require(type(preparation_reads) is int and preparation_reads==715,'EXACT_MEASURED715')
    # progress의 새 root JSON·본문 JSON 각1 + 최종 fresh 각1. 원 parent 후속2 유지.
    return dict(measured_actual81_preparation_reads=preparation_reads,
        new_root_and_body_first_reads=2,new_root_and_body_final_fresh_reads=2,
        original_post_body_metadata_reads=2,projected_actual82_shared_reads=preparation_reads+4+2,
        unchanged_shared_read_limit=m.META_READ_LIMIT,
        next_fits_current_controller=(preparation_reads+4+2<=m.META_READ_LIMIT),
        projection_not_observed_STOP=True,actual82_executed=False,
        accepted_controllers_not_rewritten=True,CPU_RAM_or600_second_guards_extended=False)


def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_GENERIC_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_GENERIC_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_GENERIC_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_generic_metadata_runtime_documents'))
    require(checked.wasSuccessful() and checked.testsRun==14 and not checked.skipped,'CONTRACT14')
    return 14


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=m.p.c.ROOT/f'{m.p.DIR}/p254-generic-metadata-status-doc-r0102-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-generic-metadata-runtime-status-document-snapshot/v1',
        state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),product_body_or_full_source_reexecuted=False,
        root_actual_pair_pin=ROOT_PIN,previous_document_receipt_pin=PREVIOUS)
    try:
        owner.admit();q=m.Reader(owner,context)
        previous=m.review.bound_json(q,PREVIOUS)
        require(previous['state']==previous_docs.PASS and previous['document_revision']==101
            and previous['resource_stop_reason'] is None and previous['resource_watcher_cleanup_confirmed'] is True,
            'SEALED_R101')
        root=m.review.bound_json(q,ROOT_PIN);m.closed_attempt(root)
        body=m.review.bound_json(q,root['case_receipt_pin'])
        compiled=m.review.bound_json(q,m.p.m.PARENT);compound=m.review.bound_json(q,m.COMPOUND)
        required=m.p.v.pins(root['closing_component']['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        extras=m.p.v.pins(root['extra_frame_controller_pins'])
        require(root['prior_runtime_plan']==previous['runtime_plan'] and root['selected_test_index']==81
            and required[m.p.m.EXE['path']]==m.p.m.EXE==compiled['compiled_test_executable_pin'],'EXACT_PRIOR74_FIXED_EXE')
        plan=m.record(root,body,root['case_receipt_pin'],required,root['binding'],extras,
            compiled['source_test_names'],compound['legacy_plan'],previous['runtime_plan'])
        require(plan['runtime_source_qualified_individual_cases']==75 and plan['next_runtime_index']==82
            and plan['runtime_remaining_individual_cases']==174 and plan['runtime_remaining_regular_cases']==168
            and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==72,'EXACT75_NEXT82')
        light=m.review.bound_json(q,LIGHT_PIN);m.closed_attempt(light)
        require(light['state']==m.LIGHT and light['prior_runtime_plan']==previous['runtime_plan']
            and light['selected_test_index']==81 and light['historical_support_contract_tests_passed']==204
            and light['current_queue_runtime_contract_tests_passed']==156
            and light['generic_queue_runtime_contract_tests_passed']==light['synthetic_following_queue_contract_tests_passed']==19
            and light['preparation_IO']['finished'] is True
            and light['preparation_IO']['bound_inputs']==light['preparation_IO']['final_fresh_hashes']==261,
            'LIGHT398_NOT_PRODUCT_OR_FOLLOWING_ACTUAL')
        require(set(extras)==set(m.EXTRAS) and len(extras)==76,'EXACT_EXECUTED_CONTROLLER_SET')
        for name,pin in extras.items():require(q.pin(name)==pin==required[name],'EXECUTED_CONTROLLERS_UNCHANGED')
        m.review_admission(m.review.bound_json(q,m.ADMISSION_FAILURE))
        m.reviewed_state_protocol(q,{name:pin for name,pin in extras.items() if name not in m.NEW})
        m.reviewed_decode_error(q)
        old_pins=m.p.v.pins(previous['bound_input_pins'])
        require(all(old_pins[pin['path']]==pin for pin in DOCS),'SEALED_R101_DOCUMENT_PINS')
        prefixes=[]
        for pin in DOCS:
            archive='implementation/p09/evidence/runtime-progress-r101/'+pin['path'].split('/')[-1]
            before=bytes_docs.bound_bytes(q,archive)
            require(q.reader.snapshots[archive]==dict(pin,path=archive),'EXACT_R101_ARCHIVE')
            prefixes.append(prefix(before,bytes_docs.bound_bytes(q,pin['path'])))
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
        report=bytes(bytes_docs.bound_bytes(q,REPORT)).decode('utf-8')
        for pin in (PREVIOUS,ROOT_PIN,LIGHT_PIN,root['case_receipt_pin'],m.ADMISSION_FAILURE,
                m.PROTOTYPE_LIGHT,m.PROTOTYPE_ADMISSION,m.REPAIRED_DECODE,*m.DECODE_SOURCE_ARCHIVES):
            require(pin['sha256'] in report,'REPORT_EXACT_PROOF_HASH')
        require(all(word in report for word in ('runtime 수용 75/249','통과 본문 재실행 없음',
            '새 문서 상태 snapshot','PC 프리즈 원인·해결 미확정',
            'P239 실제 pre-GO CPU STOP 경계 NOT_RUN','index82 NOT_RUN')),'REPORT_BOUNDARY')
        out['metadata_peak_review']=peak.summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review']=peak.summarize(body['samples'])
        out['next_metadata_scope_projection']=next_read_projection(root['preparation_IO']['read_passes'])
        out['document_contract_tests_passed']=contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(document_revision=102,runtime_plan=plan,exact_r101_document_bytes_preserved=True,
            report_pin=q.reader.snapshots[REPORT],repaired_preflight_not_promoted=True,
            required_bound_input_names=sorted(q.reader.snapshots))
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:
            q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(pin['path'] for pin in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['document_contract_tests_passed']==14,'EVERY_BOUND_INPUT_FRESH_CONTRACT14')
        m.g.complete(out,owner,proposed,validate)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','document_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
