"""P261: 불변P260의 실제pair와 문서snapshot. 본문/전체source 재실행 없음."""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_checkpoint_compound_runtime as m
import sync_current_stop_compound_documents as byte_docs
import review_packed_cpu_peak_r2 as peak
SELF='tools/p09/sync_checkpoint_compound_runtime_documents.py'
TEST='tools/p09/tests/test_checkpoint_compound_runtime_documents.py'
SCHEMA='hwpx-agent.p09-checkpoint-compound-runtime-status-document-snapshot/v1'
PASS='PASS_CHECKPOINT_COMPOUND_RUNTIME_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'
FILE=re.compile(r'p261-checkpoint-compound-status-doc-r([0-9]{4})-run([0-9]{2})\.v1\.json')


def require(ok,code):m.require(ok,'COMPOUND_DOC_'+code)


def words(plan):
    return (f"runtime 수용{plan['runtime_source_qualified_individual_cases']}/249",
        f"잔여{plan['runtime_remaining_individual_cases']}(일반{plan['runtime_remaining_regular_cases']}+corpus{plan['runtime_remaining_corpus_cases']})",
        f"다음index{plan['next_runtime_index']}",
        f"whole재조정대기{plan['all_successful_bodies_pending_whole_reconciliation']}",
        f"독립source 마감대기{plan['runtime_successful_candidates_requiring_closing']}",
        'P09·A12·A13 OPEN','원 STOP/FAILED 보존','본문 재실행 없음',
        '원600초·CPU/RAM 기준은 변경하지 않음','PC 프리즈 원인·해결 미확정')


def prefix(before,after,plan,revision):
    require(isinstance(before,(bytes,bytearray)) and isinstance(after,(bytes,bytearray))
        and len(after)>len(before)>0 and after.endswith(before),'EXACT_PREVIOUS_BYTES_SUFFIX')
    text=bytes(after[:-len(before)]).decode('utf-8')
    require(text.startswith(f'> P260~P261 runtime-r{revision} ') and all(w in text for w in words(plan)),
        'CURRENT_QUALIFIED_PLAN_PREFIX')
    return text


def counters(doc):
    require(type(doc['runtime_contract_executions']) is int and doc['runtime_contract_executions']==498
        and doc['original_retained_contract_executions']==450 and doc['own_queue_contract_tests_passed']==24
        and doc['synthetic_following_queue_contract_tests_passed']==24
        and doc['old_contract_scope']=='ORIGINAL1545_NO_BODY_REEXECUTION'
        and doc['new_contract_scope']=='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1555'
        and doc['receipt_serialization_policy']==m.r.policy(),'TOTAL498_SCOPE_AND_ORIGINAL_SERIALIZATION')


def projection(preparation_reads):
    require(type(preparation_reads) is int and 0<preparation_reads<=m.m.META_READ_LIMIT-2,'ORIGINAL_SHARED_SCOPE')
    return dict(measured_preparation_reads=preparation_reads,new_root_body_first_and_final_reads=4,
        original_post_body_reads=2,projected_next_shared_reads=preparation_reads+6,
        unchanged_shared_limit=m.m.META_READ_LIMIT,next_fits_current_controller=preparation_reads+6<=m.m.META_READ_LIMIT,
        forecast_not_observed_STOP=True,CPU_RAM_or600_guard_extended=False)


def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DOC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DOC_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_checkpoint_compound_runtime_documents'))
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped,'CONTRACT18')
    return 18


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',type=int,required=True);ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--previous',default=m.COMPOUND['path']);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 108<=args.revision<=9999 and 1<=args.run<=99,'CWD_REVISION_RUN')
    old_name=args.previous;match=FILE.fullmatch(old_name.split('/')[-1])
    require(old_name==m.COMPOUND['path'] or (old_name.startswith(m.p.DIR+'/') and match is not None),'PREVIOUS_NAMESPACE')
    dest=m.p.c.ROOT/f'{m.p.DIR}/p261-checkpoint-compound-status-doc-r{args.revision:04}-run{args.run:02}.v1.json'
    require(not dest.exists(),'FRESH_ONLY')
    report_name=f'implementation/p09/P09-261_CHECKPOINT_COMPOUND_RUNTIME_R{args.revision:04}_REPORT.md'
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),document_revision=args.revision,
        product_body_or_full_source_reexecuted=False,compound_anchor_pin=m.COMPOUND)
    try:
        owner.admit();q=m.m.Reader(owner,context)
        if old_name==m.COMPOUND['path']:
            previous=m.m.review.bound_json(q,m.COMPOUND)
            require(previous['schema_version']==m.compound.SCHEMA and previous['state']==m.compound.PASS
                and previous['status_revision']==107 and previous['runtime_plan']['runtime_source_qualified_individual_cases']==84,
                'PREVIOUS_LITERAL_COMPOUND84')
            previous_revision=107
        else:
            previous=q.json(old_name);require(previous['schema_version']==SCHEMA and previous['state']==PASS
                and previous['document_revision']==int(match.group(1)),'PREVIOUS_DOCUMENT_SNAPSHOT')
            previous_revision=previous['document_revision'];old_code=m.p.v.pins(previous['bound_input_pins'])
            for name in (SELF,TEST):require(q.pin(name)==old_code[name],'PREVIOUS_DOC_HELPERS_UNCHANGED')
        require(previous_revision==args.revision-1 and previous['resource_stop_reason'] is None
            and previous['resource_watcher_cleanup_confirmed'] is True and previous['IO']['finished'] is True
            and previous['IO']['bound_inputs']==previous['IO']['final_fresh_hashes'],'PREVIOUS_CLOSED_CONSECUTIVE')
        legacy,base,names,expected,exe,required,extras,*unused=m.anchor(q);binding=m.p.v.identity(names,expected,exe)
        plan=m.progress(q,legacy,base,names,required,binding,extras)
        require(plan['runtime_source_qualified_individual_cases']>previous['runtime_plan']['runtime_source_qualified_individual_cases']
            and plan['runtime_successful_candidates_requiring_closing']==0,'NEW_ACTUAL_PROGRESS_NO_UNCLOSED')
        roots=sorted((m.p.c.ROOT/m.p.DIR).glob('p260-case-*-run*.v1.json'));require(bool(roots),'ACTUAL_PAIR_REQUIRED')
        for file in roots:counters(q.json(file.relative_to(m.p.c.ROOT).as_posix()))
        root_name=roots[-1].relative_to(m.p.c.ROOT).as_posix();root=q.json(root_name)
        body=m.m.review.bound_json(q,root['case_receipt_pin'])
        require(root['runtime_plan']==plan and m.record(root,body,root['case_receipt_pin'],required,binding,extras,
            names,legacy,root['prior_runtime_plan'])==plan,'LATEST_EXACT_PAIR')
        proof=[q.reader.snapshots[n] for n in sorted(q.reader.snapshots)
            if n.startswith(m.p.DIR+'/p260-case-') or n.startswith(m.p.DIR+'/cases/p260-case-')]
        require(len(proof)==2*(plan['runtime_source_qualified_individual_cases']-84),'ALL_NEW_ROOT_BODY_PAIRS')
        old_pins=m.p.v.pins(previous['bound_input_pins']);prefixes=[]
        for name in m.m.MUTABLE_DOCS:
            archive=f'implementation/p09/evidence/runtime-progress-r{previous_revision}/'+name.split('/')[-1]
            before=bytes(byte_docs.bound_bytes(q,archive));after=bytes(byte_docs.bound_bytes(q,name))
            require(q.reader.snapshots[archive]==dict(old_pins[name],path=archive),'EXACT_PREVIOUS_ARCHIVE')
            prefixes.append(prefix(before,after,plan,args.revision))
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIXES')
        report=bytes(byte_docs.bound_bytes(q,report_name)).decode('utf-8')
        require(all(pin['sha256'] in report for pin in (q.reader.snapshots[old_name],m.COMPOUND,*proof))
            and all(w in report for w in words(plan)),'REPORT_EXACT_PROOF_AND_PLAN')
        out.update(document_contract_tests_passed=contracts(),runtime_counter_consistency_verified=True,
            next_metadata_scope_projection=projection(root['preparation_IO']['read_passes']),
            root_peak=peak.summarize(root['metadata_observation']['samples']),parent_peak=peak.summarize(body['samples']))
        for name in (SELF,TEST):q.pin(name)
        q.finish();out.update(runtime_plan=plan,previous_document_receipt_pin=q.reader.snapshots[old_name],
            latest_actual_pair_pin=q.reader.snapshots[root_name],actual_pair_pins=proof,
            actual_cases_added_since_previous_snapshot=plan['runtime_source_qualified_individual_cases']-previous['runtime_plan']['runtime_source_qualified_individual_cases'],
            exact_previous_document_bytes_preserved=True,report_pin=q.reader.snapshots[report_name],
            required_bound_input_names=sorted(q.reader.snapshots))
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(p['path'] for p in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['document_contract_tests_passed']==18,'ALL_BOUND_FRESH_AND18')
        m.g.complete(out,owner,proposed,validate)
        with dest.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','document_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
