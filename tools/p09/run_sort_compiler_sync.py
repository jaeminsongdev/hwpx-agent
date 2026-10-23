"""Selected21-case source/17-family plan/manifest lineage and docs closure; no Cargo or full810 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_sort_compiler_recovery as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-compiler-sync239.v1.json'
DRIVER='tools/p09/run_sort_compiler_sync.py'
PROFILE='protocol/migrations/p09-sort-operation-compiler-v1.md'
MANIFEST='protocol/migrations/p09-source-search-execution-manifest-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,MANIFEST,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.base.NEW|base.base.CHANGED|{base.DRIVER,'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/owners.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/build.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
    'crates/product-cli/src/form_product_request/stored_operations/request.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/compiler_view.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/compiler_view.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/sibling_permutation.rs','crates/hwpx-package/src/writer.rs',
    'crates/domain-ir/src/capability_router.rs'}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 형제 그룹 원본19개·현재 저장/엄격한 제품 요청20개 검증, 다중/중첩·구조적 키·공통 compiler/실제 실행/전체 계약 미완료 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 원본19·제품20·이동목록/공통 compiler/manifest 신규18개 검증, 다중/중첩·구조적 키·실제 실행/전체 계약 미완료 |'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_COMPILER_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_COMPILER_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);failed=q.json(base.base.OUTPUT);docs=q.json(base.base.DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='c06a8d1482b21cc0d753d943faf948affbfb41984a4502fa5204c692af174619'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==810 and passed['total_executed_cases']==15,'EXACT238_PRODUCT15_AND810_SOURCE_CLOSURE')
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='ef1a767cce07209e25dddd97fcb145ee8b9ce2106159dbe45cd85115d2ffcccf'
            and failed['cleanup']and not failed['steps'][1]['tests'],'EXACT237_SOURCE6_AND_PRODUCT_TEST_COMPILER_FAILURE_PRESERVED')
        c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='a6580d59025c64f0370878aab906a23ae39531641e45d752a71645252d6fb8f2'and docs['cleanup'],'EXACT236_PREVIOUS_SORT_PRODUCT20_DOCS')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_SOURCE_SORT_DISPATCH_OWNER_COMPILER_ROUTER_AND_TESTS_DECLARED_BY238')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_SORT_PLAN_INVENTORY_SOURCE_AND_ORIGINAL_GUARDS_MATCH238')
        core,products,affected=base.base.expected(q);tools.good_step(failed['steps'][0],core);tools.good_step(passed['steps'][0],products|affected)
        c.require(len(core)==6 and len(products)==12 and len(affected)==3,'EXACT21_DISTINCT_CASES_NOT21_CURRENT_REEXECUTIONS')
        for record in (passed,failed):
            for step in record['steps']:
                job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                    and job['last_job_accounting']['active_processes']==0,'ALL_THREE_SORT_COMPILER_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(max(passed['system_CPU_max'],failed['system_CPU_max'])==34.09
            and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for r in(passed,failed)for s in r['steps'])==1804.04,'EXACT_RESOURCE_MAXIMA')
        original=q.json(base.base.prior.OUTPUT)
        c.require(q.snapshots[base.base.prior.OUTPUT]['sha256']=='af2133b3d4387533375c28d2dcf40b850f7f34b0c039288f9f10286a557affbe','EXACT235_ORIGINAL_PRODUCT_AND_SOURCE_BASELINE')
        base.base.inverse(q,{p['path']:p for p in original['source_pins']})
        text=q.text(base.base.COMPILED_TEST);c.require(text.count(base.IMPORT)==1,'ONE_TEST_PARENT_IMPORT_REPAIR_ONLY')
        audit.inverse(text.replace(base.IMPORT,''),{p['path']:p for p in failed['source_pins']}[base.base.COMPILED_TEST],'ALL_NEW_COMPILER_CASES_UNCHANGED_OUTSIDE_REQUIRED_IMPORT')
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in docs['source_pins']};current=q.text('CURRENT_STATE.md')
        at=current.index('> 2026-10-20 P09 ACTIVE 최신 문단 정렬의 현재 저장과 제품 요청')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_PRODUCT_SOURCE_PATCH_CRYPTO_NATIVE_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 문단 정렬의 실제 이동 목록과 공통 계획\n');end=progress.index('## 문단 정렬의 현재 저장과 제품 요청\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_SEARCH021_PLAN_ROW_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PREVIOUS_COMPONENT_HISTORY_PRESERVED')
        manifest=q.text(MANIFEST);heading='\n## 문단 정렬의 실제 이동 목록과 공통 계획\n';c.require(manifest.count(heading)==1,'ONE_ADDITIVE_ORIGINAL_MANIFEST_PROFILE_EXTENSION')
        audit.inverse(manifest[:manifest.index(heading)],tested[MANIFEST],'ENTIRE_ORIGINAL_ROUTE_PROTECTION_AND_P02_POLICY_MANIFEST_CONTRACT_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('SourceParagraphSortSpliceInventory','final_permutation_splices','17번째','12개 잠금 argument','원본6pass','E0432','제품 시험0',
                '시험 import 한 줄만 추가','810fresh/final810','고유21개','현재21개 단일 실행이 아니다','source 정렬19/제품20·공식249는 반복하지 않았',
                '113.844/125.110','26.110/34.656/20.063','0.37/7.16','34.09%','1804.04MiB/5.66222%','33.8663%',
                'active0/empty/handle closed','routing_allowed=false','RouteUnqualified'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_ACTUAL_MOVED_SLOTS17_FAMILIES21_CASE_LINEAGE_METRICS_AND_NONAUTHORITY')
        profile=norm(q.text(PROFILE))
        for marker in('hwpx-agent.source-paragraph-sort-splices/v1','SourceParagraphSortReceipt','source_order[destination]==destination',
            '원자적 순열 후보 전체','이 단계는 실행기를 제공하지 않는다','합성 fixture','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
            '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_SPLICE_ATOMICITY_AND_REMAINING_REAL_EXECUTION_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SORT_SPLICES6_COMPILER_MANIFEST12_AFFECTED3_DOC_SYNC_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases_retained=6,new_product_cases_retained=12,affected_cases_retained=3,
            actual_cases_reexecuted=0,full810_inputs_replayed=False,previous_docs_other_rows_and_original_failure_preserved=True,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_multi_group_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_COMPILER_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
