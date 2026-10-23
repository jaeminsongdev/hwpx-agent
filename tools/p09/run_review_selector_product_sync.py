"""Scoped strict selector product code/document closure; no Cargo, test or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_selector_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-review-selector-product-sync100.v1.json'
PROFILE='protocol/migrations/p09-review-selector-product-requests.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-stored-review-selector-candidates-v1.md','protocol/migrations/p09-source-index-scope-selector-v1.md',
    'protocol/migrations/p09-source-scope-product-request-v5.md','protocol/migrations/p09-source-review-literal-output-v3.md'}
RETAINED={base.OLD_SCOPE,base.OLD_LITERAL,base.prior.SERVICE,base.prior.NAV,base.prior.SEARCH,base.prior.REVIEW,base.prior.LITERAL,
    'crates/product-cli/src/form_product_request/stored_literal_replacement/review.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review/product.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/selector.rs','crates/hwpx-package/src/document_import/search/reviews/selector.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review/selector.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','tools/p09/run_review_selector_product_components.py',
    'tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SELECTOR_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_SELECTOR_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='592c485efebf36cdb45431215b18c4b9de7d55087c1a98004aa2f38af97e136f'
            and passed['state']=='PASS_REVIEW_SELECTOR_STRICT_SEARCH_V6_LITERAL_V4_SIXTEEN_NEW_TWENTY_AFFECTED_NOT_FULL_SELECTOR_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==36 and passed['new_product_cases']==16 and passed['affected_cases']==20
            and passed['fresh_inputs']==passed['final_fresh_hashes']==542,'EXACT_THIRTY_SIX_PRODUCT_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='7bfd4197c6ddab3ce115fc208da5fca5063a8762f9401e8ee3a8d6ede1f11740'
            and previous['cleanup']and previous['total_executed_cases']==61,'EXACT_RETAINED_STORED_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_PRODUCT_PARSER_SERVICE_COMPILER_AND_TESTS_MATCH_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_TEST_BINARY')
        step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==36 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['diagnostics']==[]and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_EXPECTED_CASES_PASS_NO_DIAGNOSTICS_IGNORES_OR_FILTERS')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'OWNED_JOB_TERMINAL_AND_RESOURCE_POLICY_READBACK_UNCHANGED')
        c.require(not passed['previous_fifty_two_core_and_sixty_one_stored_cases_reexecuted']and not passed['full_selector_or_native_qualified']
            and passed['original_selector_shape_value_and_legacy_parser_bodies_inverse_verified']and passed['current_write_source_acl_aead_head_and_final_consumer_shared']
            and passed['query_lowering_or_inventory_not_replayed_on_retained_delivery'],'QUALIFIED_STRICT_REQUESTS_NOT_FULL_CONTRACT_OR_EXECUTION_AUTHORITY')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('신규제품16+기존v5범위10/v3치환10=36pass·542fresh/final542','선택 범위 결과의 다시 찾기와 서식/컨트롤 필터 계약 보완',
            'review 선택 창/저장/v6 JSON 통과','selector 창 core/저장/v4 JSON 통과','전체 계약/transaction 미완료'):
            c.require(marker in progress,'CURRENT_PROGRESS_DISTINGUISHES_STRICT_PRODUCTS_AND_FULL_CONTRACT')
        profile=q.text(PROFILE)
        for marker in('product-source-search-request/v6','product-literal-replacement-request/v4','must equal base_revision before any source read',
            'no query, options or review_policy','both Boolean fields','Duplicate decoded keys including escaped names',
            'v1/v2/v3 parser file changes only','cases:36 total,542 fresh/final542','239.813 seconds','CPU12.531',
            'Selector-result cursor navigation','Native011 is unapproved/unexecuted','P09/A12/A13 stay OPEN'):
            c.require(marker in profile,'PRECISE_SCHEMA_SHAPES_RESOURCE_OBSERVATIONS_AND_NATIVE_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-review-selector-product-requests.md'in q.text(name),'RELATED_PROFILES_LINK_CURRENT_STRICT_REQUESTS')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 review 선택 범위와 저장 연결',1)[0]
        for marker in('36pass·542fresh/final542','product-source-search-request/v6','product-literal-replacement-request/v4','311.547초',
            '239.813초','6.50초','12.531초','26.43%','39.8378%','2.2072%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_PRODUCT_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_REVIEW_SELECTOR_PRODUCT_CODE_DOCUMENT_SYNC_NOT_FULL_SELECTOR_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_product_cases=36,new_product_cases=16,affected_cases=20,
            entire_542_input_set_reaudited=False,tests_reexecuted=False,full_selector_native_or_execution_qualified=False,
            next_work='Selector_result_navigation_and_style_control_filter_contract_completion')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SELECTOR_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SELECTOR_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
