"""P256: 불변 P255 판정기로 누적 실제 pair를 소비하는 재사용 가능한 문서 snapshot."""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_checkpoint_metadata_runtime as m
import sync_current_stop_compound_documents as bytes_docs
import review_packed_cpu_peak_r2 as peak

SELF='tools/p09/sync_checkpoint_metadata_runtime_documents.py'
TEST='tools/p09/tests/test_checkpoint_metadata_runtime_documents.py'
SCHEMA='hwpx-agent.p09-checkpoint-metadata-runtime-status-document-snapshot/v1'
PASS='PASS_CHECKPOINT_METADATA_RUNTIME_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'
PREVIOUS_FILE=re.compile(r'p256-checkpoint-metadata-status-doc-r([0-9]{4})-run([0-9]{2})\.v1\.json')


def require(ok,code):m.require(ok,'CHECKPOINT_DOC_'+code)


def words(plan):
    return (f"runtime 수용{plan['runtime_source_qualified_individual_cases']}/249",
        f"잔여{plan['runtime_remaining_individual_cases']}(일반{plan['runtime_remaining_regular_cases']}+corpus{plan['runtime_remaining_corpus_cases']})",
        f"미closing후보{plan['runtime_successful_candidates_requiring_closing']}",
        f"다음index{plan['next_runtime_index']}",
        f"whole재조정대기{plan['all_successful_bodies_pending_whole_reconciliation']}",
        'P09·A12·A13 OPEN','원 STOP/FAILED 보존','통과 본문 재실행 없음',
        'CPU 보호 중단 시 자동 재시도 금지','PC 프리즈 원인·해결 미확정',
        'P239 실제 pre-GO CPU STOP 경계 NOT_RUN','원600초·CPU/RAM 기준은 변경하지 않음')


def prefix(before,after,plan,revision):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before) and after.endswith(before),'EXACT_PREVIOUS_SUFFIX')
    try:text=bytes(after[:-len(before)]).decode('utf-8')
    except UnicodeDecodeError:require(False,'PREFIX_UTF8')
    require(text.startswith(f'> P255~P256 runtime-r{revision} ')
        and all(word in text for word in words(plan)),'VALIDATED_DYNAMIC_PLAN_NOT_GATE')
    return text


def next_read_projection(preparation_reads):
    require(type(preparation_reads) is int and 0<preparation_reads<=m.META_READ_LIMIT-2,'ACTUAL_SHARED_SCOPE')
    return dict(measured_preparation_reads=preparation_reads,new_root_body_first_and_final_reads=4,
        original_post_body_metadata_reads=2,projected_next_shared_reads=preparation_reads+6,
        unchanged_shared_read_limit=m.META_READ_LIMIT,next_fits_current_controller=preparation_reads+6<=m.META_READ_LIMIT,
        projection_not_observed_STOP=True,CPU_RAM_or600_second_guards_extended=False)


def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CHECKPOINT_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHECKPOINT_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_CHECKPOINT_DOC_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_checkpoint_metadata_runtime_documents'))
    require(checked.wasSuccessful() and checked.testsRun==14 and not checked.skipped,'CONTRACT14')
    return 14


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',type=int,required=True)
    ap.add_argument('--run',type=int,required=True);ap.add_argument('--previous',default=m.CHECKPOINT['path']);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 103<=args.revision<=9999 and 1<=args.run<=99,'CWD_REVISION_RUN')
    old_name=args.previous;match=PREVIOUS_FILE.fullmatch(old_name.split('/')[-1])
    require(old_name==m.CHECKPOINT['path'] or (old_name.startswith(m.p.DIR+'/') and match is not None),'PREVIOUS_NAMESPACE')
    path=m.p.c.ROOT/f'{m.p.DIR}/p256-checkpoint-metadata-status-doc-r{args.revision:04}-run{args.run:02}.v1.json'
    report_name=f'implementation/p09/P09-256_CHECKPOINT_METADATA_RUNTIME_R{args.revision:04}_REPORT.md'
    require(not path.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
        product_body_or_full_source_reexecuted=False,document_revision=args.revision,
        metadata_checkpoint_pin=m.CHECKPOINT,metadata_checkpoint_actual_pair_pin=m.HEAD)
    try:
        owner.admit();q=m.Reader(owner,context)
        if old_name==m.CHECKPOINT['path']:
            previous=m.review.bound_json(q,m.CHECKPOINT);m.checkpoint_contract(previous)
        else:
            previous=q.json(old_name)
            require(previous['schema_version']==SCHEMA and previous['state']==PASS
                and previous.get('error_code') is None and previous['resource_stop_reason'] is None
                and previous['resource_watcher_cleanup_confirmed'] is True
                and previous['IO']['finished'] is True
                and previous['IO']['bound_inputs']==previous['IO']['final_fresh_hashes']
                and previous['document_revision']==int(match.group(1)),'PREVIOUS_CLOSED_SNAPSHOT')
            old_code=m.p.v.pins(previous['bound_input_pins'])
            for name in (SELF,TEST):require(q.pin(name)==old_code[name],'PREVIOUS_EXECUTED_DOC_CODE_UNCHANGED')
        require(previous['document_revision']==args.revision-1,'CONSECUTIVE_DOCUMENT_REVISIONS')
        legacy,base,names,expected,exe,required,extras,*unused=m.anchor(q)
        binding=m.p.v.identity(names,expected,exe)
        plan=m.progress(q,legacy,base,names,required,binding,extras)
        require(plan['runtime_source_qualified_individual_cases']>previous['runtime_plan']['runtime_source_qualified_individual_cases']
            and plan['runtime_successful_candidates_requiring_closing']==0,'NEW_ACTUAL_PROGRESS_NOT_RESTATEMENT')
        files=sorted((m.p.c.ROOT/m.p.DIR).glob('p255-case-*-run*.v1.json'));require(bool(files),'ACTUAL_PAIR_REQUIRED')
        root_name=files[-1].relative_to(m.p.c.ROOT).as_posix();root=q.json(root_name);m.closed_attempt(root)
        body=m.review.bound_json(q,root['case_receipt_pin'])
        require(root['runtime_plan']==plan and m.record(root,body,root['case_receipt_pin'],required,binding,extras,
            names,legacy,root['prior_runtime_plan'])==plan,'LATEST_EXACT_PAIR_NOT_SYNTHETIC')
        proof_pins=[q.reader.snapshots[name] for name in sorted(q.reader.snapshots)
            if name.startswith(m.p.DIR+'/p255-case-') or name.startswith(m.p.DIR+'/cases/p255-case-')]
        require(len(proof_pins)==2*(plan['runtime_source_qualified_individual_cases']-base['runtime_source_qualified_individual_cases']),
            'ALL_NEW_ROOT_BODY_PINS')
        old_pins=m.p.v.pins(previous['bound_input_pins']);prefixes=[]
        for name in m.MUTABLE_DOCS:
            archive=f"implementation/p09/evidence/runtime-progress-r{args.revision-1}/"+name.split('/')[-1]
            before=bytes_docs.bound_bytes(q,archive)
            require(q.reader.snapshots[archive]==dict(old_pins[name],path=archive),'EXACT_PREVIOUS_DOCUMENT_ARCHIVE')
            prefixes.append(prefix(before,bytes_docs.bound_bytes(q,name),plan,args.revision))
        require(prefixes[0]==prefixes[1],'IDENTICAL_STATUS_PREFIXES')
        report=bytes(bytes_docs.bound_bytes(q,report_name)).decode('utf-8')
        for pin in (q.reader.snapshots[old_name],m.CHECKPOINT,m.HEAD,*proof_pins):
            require(pin['sha256'] in report,'REPORT_EXACT_PROOF_HASH')
        require(all(word in report for word in words(plan)) and '새 문서 상태 snapshot' in report,'REPORT_DYNAMIC_BOUNDARY')
        out['metadata_peak_review']=peak.summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review']=peak.summarize(body['samples'])
        out['next_metadata_scope_projection']=next_read_projection(root['preparation_IO']['read_passes'])
        out['document_contract_tests_passed']=contracts()
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(runtime_plan=plan,previous_document_receipt_pin=q.reader.snapshots[old_name],
            latest_actual_pair_pin=q.reader.snapshots[root_name],actual_pair_pins=proof_pins,
            actual_cases_added_since_previous_snapshot=plan['runtime_source_qualified_individual_cases']-previous['runtime_plan']['runtime_source_qualified_individual_cases'],
            exact_previous_document_bytes_preserved=True,report_pin=q.reader.snapshots[report_name],
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
                and doc['document_contract_tests_passed']==14,'EVERY_BOUND_INPUT_FINAL_FRESH')
        m.g.complete(out,owner,proposed,validate)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','document_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
