"""Selected25 component/4 layout contracts and lossless249 receipt/docs, no Cargo/full836 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_sort_groups_compiler_compact as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-compiler-sync250.v1.json'
DRIVER='tools/p09/run_sort_groups_compiler_sync.py'
PROFILE='protocol/migrations/p09-sort-groups-operation-compiler-v1.md'
MANIFEST='protocol/migrations/p09-source-search-execution-manifest-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,MANIFEST,PROGRESS,'CURRENT_STATE.md',DRIVER}
RETAINED=base.base.NEW|base.base.CHANGED|{base.DRIVER,base.MODULE,base.TEST,base.OBSERVED,
    'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/owners.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/build.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/sibling_permutation.rs','crates/hwpx-package/src/writer.rs',
    'crates/domain-ir/src/capability_router.rs',base.base.base.TEST}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 그룹 원본16·제품20개 검증, 새 다중 공통 계획·중첩·구조적 키·실제 실행/전체 계약 미완료 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 원본16·제품20·공통연결 신규20개 검증, 중첩·구조적 키·실제 실행/전체 계약 미완료 |'


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_COMPILER_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_COMPILER_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);packet=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='0e118e7c6d12be8bb8792793e9eb4c4ed08974542f96a940bbd1b1911245e324'
            and q.snapshots[base.OUTPUT]['bytes']==191499,'EXACT249_FULL_LOSSLESS_RESULT_ENVELOPE')
        passed=base.compact.unpack(packet)
        c.require(passed['state']=='PASS_MULTIGROUP_SOURCE_SPLICES6_COMPILER_MANIFEST14_AFFECTED5_COMPACT4_NOT_EXECUTION_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==836 and passed['total_executed_cases']==25
            and passed['compact_layout_contracts_passed']==4,'EXACT249_25_COMPONENTS4_LAYOUT_CONTRACTS_AND836_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_SOURCE_SPLICES18_SCHEMAS_COMPILER_OWNERS_ROUTER_AND_RECORDING_MATCH249')
        core,products,affected=base.base.expected(q);tools.good_step(passed['steps'][0],core);tools.good_step(passed['steps'][1],products|affected)
        c.require((len(core),len(products),len(affected))==(6,14,5),'EXACT20_NEW_AND5_AFFECTED_NOT25_NEW_CASES')
        for step in passed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH249_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(passed['system_CPU_max']==23.24 and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in passed['steps'])==53.91,
            'EXACT249_WARM_RUN_METRICS_NOT248_FIRST_BUILD_RECONSTRUCTION')
        observed=q.json(base.OBSERVED);c.require(not(c.ROOT/base.base.OUTPUT).exists()and observed['accepted_component_cases_from_this_observation']==0
            and not observed['complete_case_list_and_terminal_job_accounting_recovered'],'FAILED248_PUBLICATION_NOT_FALSE_COMPONENT_ACCEPTANCE')
        origin=q.json(base.base.base.OUTPUT);c.require(q.snapshots[base.base.base.OUTPUT]['sha256']=='96a937a14719cf4d88e6540d8c3fedc08ed0e93ce1cfe57ae8044515fd879630','EXACT246_ORIGINAL_CURRENT_PRODUCT_BASELINE')
        base.base.inverse(q,{p['path']:p for p in origin['source_pins']})
        docs=q.json(base.base.DOC_BASE);c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='191f667a921804505d3db4d181283081c94e959992cbe25954dd1e92053b2a04'
            and docs['cleanup'],'EXACT247_ORIGINAL_CURRENT_STORE_DOCS')
        old={p['path']:p for p in docs['source_pins']}
        for name in sorted(DOCS):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 다중 그룹 정렬의 현재 저장과 제품 요청')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_RETAINED')
        progress=q.text(PROGRESS);start=progress.index('## 다중 그룹 정렬의 공통 계획 연결\n');end=progress.index('## 다중 그룹 정렬의 현재 저장과 제품 요청\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_COMMON_PLAN_SEARCH021_ROW_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_ROWS_AND_PRIOR_SEARCH_PRODUCT_SOURCE_HISTORY_RETAINED')
        manifest=q.text(MANIFEST);heading='\n## 다중 그룹 정렬의 공통 계획 연결\n';c.require(manifest.count(heading)==1,'ONE_ADDITIVE_MULTIGROUP_MANIFEST_PROFILE_SECTION')
        audit.inverse(manifest[:manifest.index(heading)],tested[MANIFEST],'ORIGINAL_MANIFEST_ROUTE_PROTECTION_AND_P02_POLICY_PROFILE_RETAINED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_P09_SEARCH_FEATURES_RETAINED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('hwpx-agent.source-paragraph-sort-group-splices/v1','18번째','final_permutation_splices','12개 잠금 argument',
                'WORKSPACE_BOUNDED_RECEIPT','수용0','262144byte','compact_receipt_json.unpack','형식4계약',
                '원본6+신규 compiler/manifest14+영향기존5=25pass','836fresh/final836','191499bytes','다중 원본16/제품20·공식249',
                'warm 재실행','121.188','0.875/10.375','0.65/10.14','0.828/10.156','53.91MiB/0.16919%','23.24%','48.8148%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%','routing_allowed=false','RouteUnqualified',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE25_PLUS4_SCOPE_LOSSLESS_STORAGE_FAILURE_AND_NATIVE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_MULTIGROUP_SPLICES6_COMPILER_MANIFEST14_AFFECTED5_COMPACT4_DOC_SYNC_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases_retained=6,new_product_cases_retained=14,affected_cases_retained=5,
            compact_layout_contracts_retained=4,actual_cases_reexecuted=0,full836_inputs_replayed=False,prior248_failure_and_previous_docs_preserved=True,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_nested_structured_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_COMPILER_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
