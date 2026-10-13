"""P251: 실제80/74수용과 원 preflight/CPU 실패 보존의 상태 snapshot."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_metadata_entry_runtime_r3 as m
import sync_density_control_documents as prior
import review_packed_cpu_peak_r2 as peak
SELF='tools/p09/sync_metadata_entry_runtime_documents.py'
TEST='tools/p09/tests/test_metadata_entry_runtime_documents.py'
REPORT='implementation/p09/P09-251_METADATA_ENTRY_RUNTIME_R0101_REPORT.md'
PREVIOUS=dict(path=m.p.DIR+'/p247-density-control-status-doc-r0100-run01.v1.json',bytes=22362,
    sha256='e8cac0eeb28af2e3e7a7e89b09862a5f1428fcc7f2317bcad7ed368554500341')
ROOT_PIN=dict(path=m.p.DIR+'/p250-case-080-run003.v1.json',bytes=612696,
    sha256='b353add7c8a0e49134d0a7f2983e3a8083192f47151f15f5364a9cdf2fe8e4cd')
LIGHT_PIN=dict(path=m.p.DIR+'/p250-light-run002.v1.json',bytes=51626,
    sha256='a345e59325b199403e4d0261e364ac054c787455c03074644f5b28bb02a9ed13')
DOCS=(dict(path='CURRENT_STATE.md',bytes=445736,
    sha256='1cf831a2d8d8af284b17ed9ba7bd04f6309e56457080b860bf3d610b0403bf81'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=539368,
    sha256='611bc14ef4d68250cf946d952e74c3a333e8603cd3e29fb1a9df8ef667b702f6'))
PASS='PASS_METADATA_ENTRY_ACTUAL80_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'


def require(ok,code):m.require(ok,'ENTRY_DOC_'+code)


def prefix(before,after):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'EXACT_R100_SUFFIX')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith('> 2026-10-09 P248~P251 runtime-r101 ')
        and all(word in text for word in ('runtime 수용74/249','잔여175(일반169+corpus6)','미closing후보0',
            '다음index81','whole재조정대기71','P09·A12·A13 OPEN','원 STOP/FAILED 보존',
            'CPU 보호 중단 시 자동 재시도 금지','통과 본문 재실행 없음','PC 프리즈 원인·해결 미확정',
            'P239 실제 pre-GO CPU STOP 경계 NOT_RUN','원600초·CPU/RAM 기준은 변경하지 않음')),
        'ACTUAL74_NOT_WHOLE_OR_GATE')
    return text


def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_ENTRY_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_ENTRY_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_ENTRY_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_metadata_entry_runtime_documents'))
    require(checked.wasSuccessful() and checked.testsRun==10 and not checked.skipped,'CONTRACT10')
    return 10


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=m.p.c.ROOT/f'{m.p.DIR}/p251-metadata-entry-status-doc-r0101-run{args.run:02}.v1.json'
    require(not path.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-metadata-entry-runtime-status-document-snapshot/v1',
        state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),product_body_or_full_source_reexecuted=False,
        root_actual_pair_pin=ROOT_PIN,previous_document_receipt_pin=PREVIOUS,
        actual_Native20_metadata32_pair_connected=True,actual_pre_GO_CPU_STOP_branch_qualified=False)
    try:
        owner.admit();q=m.Reader(owner,context)
        previous=m.review.bound_json(q,PREVIOUS)
        require(previous['state']==prior.PASS and previous['document_revision']==100
            and previous['resource_stop_reason'] is None and previous['resource_watcher_cleanup_confirmed'] is True,'SEALED_R100')
        root=m.review.bound_json(q,ROOT_PIN);m.closed_attempt(root)
        body=m.review.bound_json(q,root['case_receipt_pin'])
        compiled=m.review.bound_json(q,m.p.m.PARENT);compound=m.review.bound_json(q,m.COMPOUND)
        frame=root['closing_component']['source_frame']
        required=m.p.v.pins(frame['actual_byte_boundaries'][0]['actual_byte_pins'])
        extras=m.p.v.pins(root['extra_frame_controller_pins'])
        require(root['prior_runtime_plan']==previous['runtime_plan'] and root['selected_test_index']==80
            and required[m.p.m.EXE['path']]==m.p.m.EXE==compiled['compiled_test_executable_pin'],'EXACT_PRIOR73_FIXED_EXE')
        plan=m.record(root,body,root['case_receipt_pin'],required,root['binding'],extras,
            compiled['source_test_names'],compound['legacy_plan'],previous['runtime_plan'])
        require(plan['runtime_source_qualified_individual_cases']==74 and plan['next_runtime_index']==81
            and plan['runtime_remaining_individual_cases']==175 and plan['runtime_remaining_regular_cases']==169
            and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==71,'EXACT74_NEXT81')
        light=m.review.bound_json(q,LIGHT_PIN);m.closed_attempt(light)
        require(light['state']==m.LIGHT and light['prior_runtime_plan']==previous['runtime_plan']
            and light['selected_test_index']==80 and light['current_queue_runtime_contract_tests_passed']==156
            and light['post_stop_runtime_contract_tests_passed']==18
            and light['uncreated_borrower_connection_contract_tests_passed']==8
            and light['lower_native_runtime_contract_tests_passed']==8
            and light['metadata_entry_runtime_contract_tests_passed']==14
            and light['preparation_IO']['finished'] is True
            and light['preparation_IO']['bound_inputs']==light['preparation_IO']['final_fresh_hashes']==248,
            'LIGHT204_NOT_PRODUCT')
        for name in m.NEW:require(q.pin(name)==required[name],'ALL_EXECUTED_NEW_CONTROLLERS_UNCHANGED')
        old_required={name:pin for name,pin in required.items() if name not in m.NEW}
        old_extras={name:pin for name,pin in extras.items() if name not in m.NEW}
        m.reviewed_metadata_stop(q,previous['runtime_plan'],old_required,old_extras)
        m.reviewed_prototype_error(q);m.reviewed_budget_failure(q);m.reviewed_preflight_protocol_error(q)
        old_pins=m.p.v.pins(previous['bound_input_pins'])
        require(all(old_pins[pin['path']]==pin for pin in DOCS),'SEALED_R100_DOCUMENT_PINS')
        prefixes=[]
        for pin in DOCS:
            archive='implementation/p09/evidence/runtime-progress-r100/'+pin['path'].split('/')[-1]
            before=prior.prior_docs.docs.bound_bytes(q,archive)
            require(q.reader.snapshots[archive]==dict(pin,path=archive),'EXACT_R100_ARCHIVE')
            prefixes.append(prefix(before,prior.prior_docs.docs.bound_bytes(q,pin['path'])))
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
        report=bytes(prior.prior_docs.docs.bound_bytes(q,REPORT)).decode('utf-8')
        for pin in (PREVIOUS,ROOT_PIN,LIGHT_PIN,root['case_receipt_pin'],m.PROTOTYPE_FAILURE,m.BUDGET_FAILURE,m.REPAIRED_PREFLIGHT):
            require(pin['sha256'] in report,'REPORT_EXACT_PROOF_HASH')
        require(all(word in report for word in ('runtime 수용 74/249','통과 본문 재실행 없음',
            '새 문서 상태 snapshot','PC 프리즈 원인·해결 미확정','P239 실제 pre-GO CPU STOP 경계 NOT_RUN')),'REPORT_BOUNDARY')
        out['metadata_peak_review']=peak.summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review']=peak.summarize(body['samples'])
        out['document_contract_tests_passed']=contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(document_revision=101,runtime_plan=plan,exact_r100_document_bytes_preserved=True,
            report_pin=q.reader.snapshots[REPORT],repaired_preflight_not_promoted=True)
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:
            q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        m.g.complete(out,owner,proposed,lambda doc:require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==39
            and doc['document_contract_tests_passed']==10,'FRESH39_CONTRACT10'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','document_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
