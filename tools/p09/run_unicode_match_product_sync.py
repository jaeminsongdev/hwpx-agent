"""Selected v2 match-product/source/docs closure, no22-product/42-source/666-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_match_product_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-unicode-match-product-sync167.v1.json'
PROFILE='protocol/migrations/p09-unicode-match-product-request-v2.md'
DOCS={PROFILE,'protocol/migrations/p09-source-unicode-match-normalization-v1.md','protocol/migrations/p09-unicode-product-request-v1.md',
    'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
SOURCE='crates/hwpx-package/src/document_import/search/'
RETAINED={SOURCE+'replacement/atoms/unicode.rs',SOURCE+'replacement/atoms/unicode/matches.rs',SOURCE+'replacement/atoms/unicode/plan.rs',
    SOURCE+'replacement/atoms/unicode/transform.rs',SOURCE+'replacement/atoms/readback.rs',SOURCE+'replacement/atoms/review.rs',
    SOURCE+'reviews/selector.rs',SOURCE+'reviews/selector/styles.rs',SOURCE+'inspection/definitions.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/hwpx-package/tests/document_import_unicode_match_normalization.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'tools/p09/run_unicode_match_product_components.py','tools/p09/run_unicode_match_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_MATCH_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_MATCH_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);source=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='e2a13d4286f7890d0b6eed330b1b1c0c33ecbb3505eef2fb85724f6c18199133'
            and passed['state']=='PASS_UNICODE_MATCH_TWENTY_TWO_V2_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==666 and passed['new_product_cases']==22
            and not passed['source42_reexecuted']and not passed['old150_products_reexecuted'],'EXACT22_MATCH_PRODUCT_PASSES_AND666_INPUT_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='f4e9af5273787ab26e600dcc5e7c9c9302a076f4b264813325b6ba5d10bdf86d'
            and source['state']=='PASS_UNICODE_MATCH1_REPAIRED_41_RETAINED_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==663 and source['total_distinct_cases']==42,'EXACT_PRIOR42_SOURCE_CASES_RETAINED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_STORE_V2_REQUEST_SOURCE_COMPILER_SECURITY_AND_TESTS_MATCH_PASS166')
        target.inverse(q,old);cases=target.expected(q);target.good_step(passed['steps'][0],cases)
        c.require(passed['original_v1_scope_product_and_source_test_bodies_inverse_verified']and passed['one_current_source_proof_match_compiler_and_no_query_replay_on_delivery'],
            'ORIGINAL_V1_SOURCE_ACCESS_BOUNDARIES_AND_ONE_MATCH_COMPILER_RETAINED')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 검색 일치 원본 Unicode 정규화',1)[0]
        for marker in('product-unicode-normalization-request/v2','normalize_unicode_matches','max_matches','RouteUnqualified','666fresh/final666',
            '신규제품22pass','source42·제품150·공식249','129.718','44.547','10.91','1703.56MiB','32.33%','SEARCH-013','P09/A12/A13 OPEN','Native011'):
            c.require(marker in profile,'PRECISE_V2_PRODUCT_CONTRACT_COUNTS_RESOURCES_NEXT_WORK_AND_OPEN_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-022 | Unicode 정규화 | 선택 범위 v1 제품20개·일치 source 고유42개·현재 저장/엄격한 검색·서식 v2 제품22개 검증, 전체 통합/target 계약 미완료 |'in progress,
            'ALL19_ROWS_WITH_CURRENT_MATCH_PRODUCT_AND_REMAINING_FULL_CONTRACT')
        for marker in('666fresh/final666','신규제품22pass','다음 접근허용 불필요 작업은 SEARCH-013','공식158/249','P09/A12/A13 OPEN',
            '목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_PRECISE_PROGRESS_NEXT_SOURCE_OPERATION_AND_ORIGINAL_NATIVE_PHASE_BOUNDARIES')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-unicode-match-product-request-v2.md'in q.text(name),'SOURCE_MATCH_AND_OLD_SCOPE_PRODUCT_LINK_DISTINCT_V2_WITHOUT_WIDENING_V1')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_MATCH_PRODUCT_SELECTED_SOURCE_DOCS_SYNC_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_cases=22,source_cases_retained=42,old_product_cases_retained=150,source666_or_Cargo_or_tests_reexecuted=False,
            next_work='SEARCH013_explicit_case_conversion_policy_and_original_source_compiler_with_remaining_SEARCH022_integration_target_gates_preserved')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_MATCH_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_MATCH_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
