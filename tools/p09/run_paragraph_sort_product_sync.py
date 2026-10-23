"""Selected20 actual stored/product cases and docs closure; no Cargo, old802 replay or execution promotion."""
import json,re,time
from types import SimpleNamespace as NS
import run_paragraph_sort_product_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-paragraph-sort-product-sync236.v1.json'
DRIVER='tools/p09/run_paragraph_sort_product_sync.py'
PROFILE='protocol/migrations/p09-paragraph-sort-product-request-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.NEW|base.CHANGED|{base.prior.base.MODEL,base.prior.base.ORDER,base.prior.base.VERIFY,base.prior.base.TEST,
    'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request.rs','crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs','crates/product-cli/src/form_stored_provider.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/document_import/forms.rs'}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 명시적 NFC/단일 형제 그룹 원본 후보19개 검증, 다중/중첩·구조적 키·현재 저장/제품 요청·실행/전체 계약 미완료 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 형제 그룹 원본19개·현재 저장/엄격한 제품 요청20개 검증, 다중/중첩·구조적 키·공통 compiler/실제 실행/전체 계약 미완료 |'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_SORT_PRODUCT_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,common_dispatcher_compiler_or_route_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);docs=q.json(base.DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='af2133b3d4387533375c28d2dcf40b850f7f34b0c039288f9f10286a557affbe'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==802 and passed['total_executed_cases']==20,
            'EXACT235_ACTUAL_STORED_SORT20_AND802_SOURCE_CLOSURE')
        c.require(q.snapshots[base.DOC_BASE]['sha256']=='cfd7c53d05a0c7086aee95823b6075c4a9b53e1999f5aca2891585b2ea48a754'and docs['cleanup'],'EXACT234_PREVIOUS_SOURCE_SORT19_DOCS')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_CURRENT_PRODUCT_AND_ORIGINAL_SOURCE_GUARDS_DECLARED_BY235')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_SOURCE_SORT_PRODUCT_REQUEST_SCOPE_AND_ACCESS_INPUTS_MATCH235')
        cases=base.expected(q);tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'235_OWNED_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(passed['system_CPU_max']==25.0 and job['last_job_accounting']['peak_job_private_mib']==1801.05,'EXACT235_RESOURCE_METRICS')
        original=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='52c2dd96601597e716d8b5310c80848ad26194c14b01d202fcc9ada18e095f7b','EXACT232_ORIGINAL_SOURCE_AND_PRODUCT_BASELINE')
        base.inverse(q,{p['path']:p for p in original['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in docs['source_pins']};current=q.text('CURRENT_STATE.md')
        at=current.index('> 2026-10-20 P09 ACTIVE 최신 선택한 원본 형제 문단 정렬')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_SOURCE_PATCH_CRYPTO_PROTECTION_NATIVE_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 문단 정렬의 현재 저장과 제품 요청\n');end=progress.index('## 선택한 원본 형제 문단 정렬\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_SEARCH021_CURRENT_PRODUCT_ROW_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_ROWS_AND_ENTIRE_PREVIOUS_COMPONENT_HISTORY_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('StoredParagraphSortProductRequest::prepare_json','hwpx-agent.product-paragraph-sort-request/v1','원본 읽기 전에',
                '현재 document.write','제품20pass','802fresh/final802','진단/경고없음','cleanupTrue','정확한16KiB','외부5scope','head 경합',
                'source 정렬19·patch18·공식249는 반복하지 않았','152.296','49.090','6.90','46.734','25.00%','1801.05MiB/5.65285%',
                '26.7660%','active0/empty/handle closed','RouteUnqualified'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_ACTUAL_STORED_PRODUCT20_METRICS_REUSE_AND_CLOSED_ROUTE')
        profile=norm(q.text(PROFILE))
        for marker in('sort_sibling_paragraphs','max_comparison_bytes','32MiB','idempotency_key_claimed=false',
            'full_sort_native_cas_execution_publication_authority=false','공통 dispatcher/compiler','다중/중첩 그룹','CPU cap6.25%',
            'private8%/stop7%','RAM/commit95%','158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_REQUEST_SCOPE_LIMITS_AND_REMAINING_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_PARAGRAPH_SORT_PRODUCT20_DOC_SYNC_NOT_FULL_SEARCH021_DISPATCH_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases_retained=20,actual_cases_reexecuted=0,
            full802_inputs_replayed=False,previous_docs_other_rows_and_original_source_failures_preserved=True,
            next_work='source_sort_anchors_and_common_operation_compiler_dispatch_then_actual_execution_and_multi_group_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_PRODUCT_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
