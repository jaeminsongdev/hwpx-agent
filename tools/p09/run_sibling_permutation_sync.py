"""Selected18-case lineage/docs audit; no Cargo, old786 replay, native execution or Gate promotion."""
import json,re,time
from types import SimpleNamespace as NS
import run_sibling_permutation_recovery as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sibling-permutation-sync229.v1.json'
DRIVER='tools/p09/run_sibling_permutation_sync.py'
PROFILE='protocol/migrations/p09-sibling-permutation-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.base.NEW|base.base.CHANGED|{base.DRIVER,'Cargo.toml','Cargo.lock','crates/hwpx-package/Cargo.toml',
    'crates/hwpx-package/src/preserving_xml.rs','crates/hwpx-package/src/safe_xml.rs','crates/hwpx-package/src/id_index.rs',
    'crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/preservation.rs'}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERMUTATION_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SIBLING_PERMUTATION_DOC_SYNC',actual_Cargo_or_tests=False,
        actual_Hangul_or_COM=False,own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,SEARCH021_complete=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);failed=q.json(base.base.OUTPUT);docs=q.json(base.base.DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='70cc6ee303f59feff83bc97d2f4b9c9c28b393ad72222196dd2595c1b28d80ed'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==786,'EXACT228_ONE_RECOVERED_CASE_AND786_INPUT_CLOSURE')
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='5657dfe281d800f1283ecee64da07cafa03541b2b3e781aa410f5380b51206df'
            and failed['cleanup'],'EXACT227_SEVENTEEN_PASSES_ONE_FIXTURE_FAILURE_PRESERVED')
        c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='12125ef9aba5daf24218348b1ab90b8d49baea996ebfed6978d94811422013b4'
            and docs['cleanup'],'EXACT226_PREVIOUS_PINNED_CRYPTO_DOCS')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_SOURCE_PARSER_WRITER_GUARDS_AND_TESTS_DECLARED_BY228')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_PERMUTATION_SOURCE_TEST_AND_GUARD_INPUTS_MATCH228')
        all_cases=base.base.expected(q);previous={n for n,s in failed['steps'][0]['tests']if s=='ok'};repaired={n for n,s in passed['steps'][0]['tests']if s=='ok'}
        c.require(len(previous)==17 and len(repaired)==1 and not(previous&repaired)and previous|repaired==all_cases,
            'EXACT18_DISTINCT_CASES_NOT_EIGHTEEN_CURRENT_REEXECUTIONS')
        tools.good_step(passed['steps'][0],repaired)
        for record in (passed,failed):
            job=record['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_PERMUTATION_JOBS_TERMINAL_EMPTY_CLOSED')
        original=q.json(base.base.prior.OUTPUT)
        c.require(q.snapshots[base.base.prior.OUTPUT]['sha256']=='a4bff4e76e3beba1bc050d3a5d71c8f9e8297bc38f226fa083d6062faf3460bb','EXACT225_ORIGINAL_PATCH_BASELINE')
        base.base.inverse(q,{p['path']:p for p in original['source_pins']})
        text=q.text(base.base.TEST);c.require(text.count(base.ASSERTION)==1 and text.count('<!--SECOND-->')==2,'ONE_STRONG_PI_REJECTION_AND_TWO_VALID_GAP_FIXTURES')
        audit.inverse(text.replace(base.ASSERTION,'').replace('<!--SECOND-->','<?keep yes?>'),
            {p['path']:p for p in failed['source_pins']}[base.base.TEST],'ALL_OTHER17_CASES_AND_TEST_HELPERS_RETAINED')
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in docs['source_pins']};current=q.text('CURRENT_STATE.md')
        at=current.index('> 2026-10-20 P09 ACTIVE 최신 보존된 P02 registry의 실제 서명 검증')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_CRYPTO_PROTECTION_COMPILER_AND_NATIVE_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 원본 형제 요소 순서 변경\n');end=progress.index('## 보존된 P02 registry의 실제 서명 검증\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_ENTIRE_PREVIOUS_COMPONENT_HISTORY_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('PatchIntent::PermuteSiblingElements','ProcessingInstructionForbidden','17pass/1fail','그1개만pass','786fresh/final786',
                '고유18개','현재18개 단일 실행이 아니다','제품·보안 파서는 변경하지 않았','통과17개','77.312/104.297','26.312/3.000','1784.83MiB/5.60195%',
                '18.89%','26.1195%','active0/empty/handle closed','SEARCH-021'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_SOURCE_BYTES_CASE_LINEAGE_RESOURCES_AND_INCOMPLETE_SORT_BOUNDARY')
        profile=norm(q.text(PROFILE))
        for marker in('source_order[destination]','최소2개','항등 순열','제자리에','고정 slot','max_intents','max_fragment_bytes','permutation_targets',
            'permutation_bytes','1000개','CPU cap6.25%','private8%/stop7%','RAM/commit95%','158/249','잔여91','next165','P09/A12/A13 OPEN',
            'CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_PERMUTATION_CONTRACT_LIMITS_AND_UNCHANGED_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SIBLING_PERMUTATION18_DOC_SYNC_NOT_SOURCE_SORT_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_patch_cases_retained=12,affected_patch_cases_retained=6,
            actual_cases_reexecuted=0,full786_inputs_replayed=False,all_previous_doc_history_and_original_failure_preserved=True,
            next_work='actual_source_SEARCH021_sort_scope_comparator_protection_then_product_execution_and_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PERMUTATION_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
