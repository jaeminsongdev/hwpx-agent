"""Scoped33-case selector navigation code/document closure without test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_navigation_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-selector-navigation-sync102.v1.json'
PROFILE='protocol/migrations/p09-selector-result-navigation-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-search-navigation-v1.md','protocol/migrations/p09-source-scope-product-request-v5.md',
    'protocol/migrations/p09-review-selector-product-requests.md','protocol/migrations/p09-stored-review-selector-candidates-v1.md',
    'protocol/migrations/p09-source-index-scope-selector-v1.md'}
RETAINED={base.OLD_CORE,base.OLD_PRODUCT,'crates/hwpx-package/src/document_import/search/navigation.rs',
    'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/forms.rs',
    'crates/hwpx-package/src/document_import/search/scope.rs','crates/hwpx-package/src/document_import/search/reviews.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'tools/p09/run_selector_navigation_components.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_NAVIGATION_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_NAVIGATION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='01bde329542d9c59a77e9457a7e74af803c4fed0bf99e3d0085e49c4a3276fd2'
            and passed['state']=='PASS_SELECTOR_NAVIGATION_SIX_CORE_TEN_PRODUCT_SEVENTEEN_AFFECTED_NOT_FULL_SELECTOR_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==33 and passed['new_core_cases']==6 and passed['new_product_cases']==10
            and passed['affected_cases']==17 and passed['fresh_inputs']==passed['final_fresh_hashes']==548,'EXACT_THIRTY_THREE_NAVIGATION_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='592c485efebf36cdb45431215b18c4b9de7d55087c1a98004aa2f38af97e136f'
            and previous['cleanup']and previous['total_executed_cases']==36,'EXACT_RETAINED_PRODUCT_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_NAVIGATION_ENGINE_ADAPTER_AUTH_AND_TESTS_MATCH_PASS')
        base.inverse(q,old);groups=base.expected(q);c.require(len(passed['steps'])==2,'TWO_SERIAL_TEST_BINARIES')
        for step,expected in zip(passed['steps'],groups,strict=True):
            c.require(step['exit_code']==0 and len(step['tests'])==len(expected)and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_EXPECTED_NAVIGATION_CASES_PASS_WITHOUT_IGNORES_OR_FILTERS')
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
                and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
                'BOTH_JOBS_TERMINAL_WITH_ORIGINAL_RESOURCE_READBACK')
        c.require(passed['steps'][0]['diagnostics']==[]and passed['steps'][1]['diagnostics']==['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "selector_navigation_product") generated 1 warning'],
            'ONLY_KNOWN_PRODUCT_FIXTURE_UNUSED_HELPER_WARNING')
        c.require(not passed['previous_fifty_two_core_sixty_one_stored_thirty_six_product_cases_reexecuted']and not passed['full_selector_or_native_qualified']
            and passed['original_navigation_engine_parsers_current_authorization_and_final_consumer_preserved']and passed['selector_and_policy_bound_cursor_without_query_reexecution']
            and passed['original_full_result_serialization_and_fresh_checks_retained']and passed['inventory_navigation_rejected_before_source_access'],
            'QUALIFIED_SELECTOR_FIND_NAVIGATION_NOT_FULL_SEARCH_OR_EXECUTION')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('총33pass·548fresh/final548','4종 selector의 v5/v6 cursor','다음은 selector와 서식/컨트롤 필터 조합',
            '전체 결과의 유한 직렬화·해시 무결성 검사는 유지','제품36·공식249 대기열은 재실행하지 않았다'):
            c.require(marker in progress,'CURRENT_PROGRESS_NAVIGATION_AND_OPEN_FULL_CONTRACT')
        profile=q.text(PROFILE)
        for marker in('product-source-search-next-request/v1','Inventory is not a Find result','before artifact access',
            'without rerunning the query or rebuilding an index','Overall navigation is not constant-time','cases:33 total,548 fresh/final548',
            '38.343/test0.25','30.266/test2.66','Native011 is unapproved/unexecuted','P09/A12/A13 remain OPEN'):
            c.require(marker in profile,'PRECISE_CURSOR_FIND_AUTH_RESOURCE_AND_NATIVE_BOUNDARIES')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-selector-result-navigation-v1.md'in q.text(name),'RELATED_SOURCE_PRODUCT_NAVIGATION_PROFILES_LINK_CURRENT_QUALIFICATION')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 review 범위 제품 요청',1)[0]
        for marker in('총33pass·548fresh/final548','product-source-search-next-request/v1','inventory는 읽기 전에 Request로 거부',
            '139.547초','38.343초','30.266초','25.19%','37.1637%','5.1099%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_NAVIGATION_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_NAVIGATION_CODE_DOCUMENT_SYNC_NOT_FULL_SELECTOR_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_navigation_cases=33,new_core_cases=6,new_product_cases=10,affected_cases=17,
            entire_548_input_set_reaudited=False,tests_reexecuted=False,full_selector_native_or_execution_qualified=False,
            next_work='Selector_style_and_control_filter_combinations_and_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_NAVIGATION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_NAVIGATION_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
