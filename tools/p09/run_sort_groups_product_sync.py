"""Selected current stored20 lineage and docs closure; no Cargo/source16 or full824 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_sort_groups_product_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-product-sync247.v1.json'
DRIVER='tools/p09/run_sort_groups_product_sync.py'
PROFILE='protocol/migrations/p09-paragraph-sort-groups-product-request-v1.md'
SOURCE_PROFILE='protocol/migrations/p09-paragraph-sort-groups-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,SOURCE_PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER}
RETAINED=base.NEW|base.CHANGED|{
    'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml',
    base.STORED_ROOT[:-3]+'/sort.rs',base.PRODUCT_ROOT[:-3]+'/sort.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    base.prior.base.ROOT,base.prior.base.HASH,base.prior.base.MODEL,base.prior.base.READBACK,
    base.prior.base.ROOT[:-3]+'/order.rs',base.prior.base.ROOT[:-3]+'/verify.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/sibling_permutation.rs','crates/hwpx-package/src/writer.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs',
    'crates/hwpx-package/tests/source_paragraph_sort_groups.rs'}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 그룹 원본16개 검증, 새 다중 제품 연결·중첩·구조적 키·실제 실행/전체 계약 미완료 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 그룹 원본16·제품20개 검증, 새 다중 공통 계획·중첩·구조적 키·실제 실행/전체 계약 미완료 |'


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_PRODUCT_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,multigroup_common_dispatcher_compiler_or_execution_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='96a937a14719cf4d88e6540d8c3fedc08ed0e93ce1cfe57ae8044515fd879630'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==824 and passed['total_executed_cases']==20,'EXACT246_CURRENT_STORED_GROUPS20_AND824_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'ALL_SELECTED_CURRENT_STORED_SOURCE_SECURITY_PRODUCTS_AND_TESTS_MATCH246')
        cases=base.expected(q);tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'SUCCESS246_JOB_TERMINAL_EMPTY_CLOSED')
        source=q.json(base.prior.OUTPUT);c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='cbda1142d600e2054606f2d402412ab24521c89c34c725155492649a1376e779'
            and source['cleanup']and source['total_executed_cases']==16,'EXACT244_SOURCE16_RETAINED_WITHOUT_REPLAY')
        base.inverse(q,{p['path']:p for p in source['source_pins']})
        docs=q.json(base.DOC_BASE);c.require(q.snapshots[base.DOC_BASE]['sha256']=='a1f1ba526da2298097011642339365c87b2ba5a7a6c576408155e229fe6f7d04'
            and docs['cleanup'],'EXACT245_PREVIOUS_SOURCE_GROUP_DOCS')
        old={p['path']:p for p in docs['source_pins']}
        for name in sorted(DOCS):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 다중 부모와 다중 part 문단 정렬')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_NATIVE_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 다중 그룹 정렬의 현재 저장과 제품 요청\n');end=progress.index('## 다중 부모와 다중 part 문단 정렬\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_MULTIGROUP_CURRENT_STORE_SEARCH021_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PREVIOUS_SOURCE_GROUP_SORT_HISTORY_PRESERVED')
        text=q.text(SOURCE_PROFILE);heading='\n## 현재 저장과 제품 요청 연결\n';c.require(text.count(heading)==1,'ONE_ADDITIVE_CURRENT_STORE_UPDATE_ON_ORIGINAL_SOURCE_PROFILE')
        audit.inverse(text[:text.index(heading)],tested[SOURCE_PROFILE],'WHOLE_PREVIOUS_SOURCE_SORT_GROUP_PROFILE_AND_FAILURE_RECORD_PRESERVED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_P09_SEARCH_FEATURES_RETAINED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('StoredParagraphSortGroupsProductRequest::prepare_json','hwpx-agent.product-paragraph-sort-groups-request/v1',
                'sort_paragraph_groups','Borrowed/Owned','신규 제품20pass','824fresh/final824','진단/경고없음','cleanupTrue',
                '다중 원본16·단일 source19/제품20/공통연결21·공식249','159.687','52.782','8.14','50.344','1809.18MiB/5.67837%',
                '59.72%','46.6415%','active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE_CURRENT_STORED_PRODUCT20_RESOURCES_AND_NONAUTHORITY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_CURRENT_STORED_MULTIGROUP_PRODUCT20_DOC_SYNC_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,product_cases_retained=20,source_cases_retained=16,
            actual_cases_reexecuted=0,full824_inputs_replayed=False,previous_docs_other_rows_and_original_failures_preserved=True,
            next_work='sealed_exact_multigroup_moved_slots_and_shared_compiler_dispatch_manifest_then_actual_trusted_execution_and_remaining_sort_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_PRODUCT_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
