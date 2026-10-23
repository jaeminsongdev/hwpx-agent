"""Selected actual19 source-sort lineage and documentation audit; no Cargo/full796 replay or promotion."""
import json,re,time
from types import SimpleNamespace as NS
import run_source_paragraph_sort_recovery as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-paragraph-sort-sync233.v1.json'
DRIVER='tools/p09/run_source_paragraph_sort_sync.py'
PROFILE='protocol/migrations/p09-source-paragraph-sort-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.base.NEW|base.base.CHANGED|{base.DRIVER,'tools/p09/inspect_source_paragraph_sort_failures.py',
    'Cargo.toml','Cargo.lock','crates/hwpx-package/Cargo.toml','crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/sibling_permutation.rs',
    'crates/hwpx-package/src/safe_xml.rs','crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/id_index.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search/selector.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/text/output.rs','crates/hwpx-package/src/document_import/structure/caption_text_batch.rs'}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 정렬 기준·범위·구조 보존 검증 필요 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 명시적 NFC/단일 형제 그룹 원본 후보19개 검증, 다중/중첩·구조적 키·현재 저장/제품 요청·실행/전체 계약 미완료 |'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SORT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PARAGRAPH_SORT_DOC_SYNC',actual_Cargo_or_tests=False,
        actual_Hangul_or_COM=False,own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,SEARCH021_complete=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);failed=q.json(base.base.OUTPUT);diag=q.json(base.DIAG);docs=q.json(base.base.DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='52c2dd96601597e716d8b5310c80848ad26194c14b01d202fcc9ada18e095f7b'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==796,'EXACT232_TWO_RECOVERED_SOURCE_SORT_CASES_AND796_CLOSURE')
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='72a57c2be2e2e8f0704454ccad91f7e6f417039f33b3465de5d8f6e7ea3ce7be'and failed['cleanup']
            and q.snapshots[base.DIAG]['sha256']=='3b18175bf9890134a45d73016b79d3c41eb1ab32694fac34d18eedbdb519d5d1'and diag['cleanup'],
            'EXACT230_SEVENTEEN_PASSES_TWO_FAILURES_AND231_DIAGNOSTIC_FAILURE_PRESERVED')
        c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='dada1b71b13ef7bde88b2b81a7656eed2df333d249c4cf51a0a3a64f79c92b36'and docs['cleanup'],'EXACT229_PREVIOUS_SORT_BASE_DOCS')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_SORT_SOURCE_TESTS_AND_ORIGINAL_GUARDS_DECLARED_BY232')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_SOURCE_SORT_AND_ORIGINAL_SCOPE_PROTECTION_PATCH_WRITER_INPUTS_MATCH232')
        all_cases=base.base.expected(q);previous={n for n,s in failed['steps'][0]['tests']if s=='ok'};repaired={n for n,s in passed['steps'][0]['tests']if s=='ok'}
        c.require(len(previous)==17 and len(repaired)==2 and not(previous&repaired)and previous|repaired==all_cases,'EXACT19_DISTINCT_SOURCE_CASES_NOT_NINETEEN_CURRENT_REEXECUTIONS')
        tools.good_step(passed['steps'][0],repaired)
        for record in (passed,failed,diag):
            job=record['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_THREE_SOURCE_SORT_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(max(passed['system_CPU_max'],failed['system_CPU_max'],max(s['system_cpu_percent']for s in diag['resource_samples']))==29.1
            and max(r['steps'][0]['owned_job']['last_job_accounting']['peak_job_private_mib']for r in(passed,failed,diag))==1791.06,'EXACT_THREE_RUN_RESOURCE_MAXIMA')
        original=q.json(base.base.prior.OUTPUT)
        c.require(q.snapshots[base.base.prior.OUTPUT]['sha256']=='70cc6ee303f59feff83bc97d2f4b9c9c28b393ad72222196dd2595c1b28d80ed','EXACT228_ORIGINAL_ATOMS_BASELINE')
        base.base.inverse(q,{p['path']:p for p in original['source_pins']});base.inverse(q,{p['path']:p for p in failed['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in docs['source_pins']};current=q.text('CURRENT_STATE.md')
        at=current.index('> 2026-10-20 P09 ACTIVE 최신 원본 형제 요소 순서 변경')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_PATCH_CRYPTO_PROTECTION_NATIVE_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 선택한 원본 형제 문단 정렬\n');end=progress.index('## 원본 형제 요소 순서 변경\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_SEARCH021_ROW_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_ROWS_AND_PREVIOUS_COMPONENT_HISTORY_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('lower_selector_paragraph_sort_candidate','17pass/2fail','id_index_validation_failed','UnsupportedShape','그2개만pass','796fresh/final796',
                '고유19개','현재19개 단일 실행이 아니다','제품·reader·ID 검사는 변경하지 않았','통과17개','79.906/107.500','26.985/3.360',
                '1791.06MiB/5.62150%','29.10%','26.6083%','active0/empty/handle closed','SEARCH-021'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_ACTUAL_SOURCE_SORT19_LINEAGE_RESOURCES_AND_PARTIAL_PRODUCT_BOUNDARY')
        profile=norm(q.text(PROFILE))
        for marker in('NfcUnicodeScalarLexicographic','max_comparison_bytes','32MiB','VerifiedFormReconstruction','ReviewWriteContext','ComparisonLimit',
            'locale_native_full_protection_or_execution_authority=false','128문단','다중 부모/중첩','현재 저장 서비스/엄격한 제품 요청','CPU cap6.25%',
            'private8%/stop7%','RAM/commit95%','158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_SORT_SCOPE_LIMITS_AND_REMAINING_PRODUCT_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SOURCE_PARAGRAPH_SORT19_DOC_SYNC_NOT_FULL_SEARCH021_PRODUCT_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases_retained=19,actual_cases_reexecuted=0,
            full796_inputs_replayed=False,previous_docs_other_rows_and_original_failures_preserved=True,
            next_work='multi_parent_nested_and_structured_keys_then_current_store_strict_product_request_and_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SORT_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
