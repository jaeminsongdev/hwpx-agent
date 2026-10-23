"""Selected Unicode product/source/docs closure; no20-product/81-source/657-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_product_components as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-unicode-product-sync162.v1.json'
PROFILE='protocol/migrations/p09-unicode-product-request-v1.md'
DOCS={PROFILE,'protocol/migrations/p09-source-unicode-normalization-v1.md','CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
RETAINED={'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs',
    'crates/hwpx-package/src/document_import/forms.rs',
    'crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/document_import/search.rs',
    base.ROOT+'normalization.rs',base.ROOT+'replacement/atoms/review.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/product-cli/tests/regex_replacement_product.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'tools/p09/run_unicode_product_components.py','tools/p09/run_unicode_normalization_failed_cases.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.toml','Cargo.lock'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);source=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='1e3606982c37b493d59756f55daca0e7b029439fcaa3f4734881a43525b537af'
            and passed['state']=='PASS_UNICODE_TWENTY_SCOPE_PRODUCTS_NOT_QUERY_FILTER_FULL_TRANSACTION_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==657 and passed['new_product_cases']==20
            and not passed['source81_reexecuted']and not passed['original130_products_reexecuted'],'EXACT_TWENTY_PRODUCT_PASSES_AND657_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='d8b44843bb5ecc8959625c7614d3ac126d5b75f927dd2347173ccda29fe7899a'
            and source['state']=='PASS_UNICODE_3_REPAIRED_78_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==654 and source['total_distinct_cases']==81,'EXACT_PRIOR_SOURCE81_RETAINED_NOT_REEXECUTED')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_STORE_PRODUCT_CORE_PROOF_POLICY_HELPER_AND_TESTS_MATCH_PASS161')
        target.inverse(q,old);cases=target.expected(q);base.good_step(passed['steps'][0],cases)
        c.require(passed['original_common_access_request_parser_and_test_bodies_inverse_verified']and passed['explicit_unimplemented_query_filter_rejected_not_ignored'],
            'ORIGINAL_SECURITY_BOUNDARIES_AND_EXPLICIT_SCOPE_ONLY_CONTRACT')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 실제 원본 Unicode 정규화',1)[0]
        for marker in('product-unicode-normalization-request/v1','normalize_unicode_scope','16KiB','Borrowed/Owned','RouteUnqualified',
            '657fresh/final657','신규제품20pass','source81·기존제품130·공식249','127.188','43.297','8.20','1705.17MiB','31.84%',
            '다음은 검색어·서식 필터','P09/A12/A13 OPEN','Native011'):
            c.require(marker in profile,'PRECISE_UNICODE_SCOPE_PRODUCT_CONTRACT_COUNTS_RESOURCES_AND_REMAINING_BOUNDARY')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-022 | Unicode 정규화 | 실제 원본 core 고유81개·현재 저장/엄격한 선택 범위 v1 제품20개 검증, query/filter·전체 계약 미완료 |'in progress,
            'ALL19_ROWS_AND_PRECISE_CURRENT_STORED_SCOPE_PRODUCT_SEARCH022_STATUS')
        for marker in('657fresh/final657','신규제품20pass','다음은 전체 SEARCH-022의 검색어·서식 필터 결합',
            '공식158/249','P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_PROGRESS_NEXT_TASK_AND_ORIGINAL_PHASE_AND_NATIVE_BOUNDARIES')
        c.require('p09-unicode-product-request-v1.md'in q.text('protocol/migrations/p09-source-unicode-normalization-v1.md'),'SOURCE_PROFILE_LINKS_CURRENT_SCOPE_PRODUCT_WITHOUT_PROMOTING_FULL_CONTRACT')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_PRODUCT_SELECTED_SOURCE_DOCS_SYNC_NOT_FULL_QUERY_FILTER_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_cases=20,source_cases_retained=81,old_product_cases_retained=130,source657_or_Cargo_or_tests_reexecuted=False,
            next_work='Full_SEARCH022_query_style_filter_semantics_then_remaining_P09_operations_and_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
