"""Selected case-product/source/docs closure; no22-product/64-source/676-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_case_product_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-case-product-sync174.v1.json'
PROFILE='protocol/migrations/p09-case-product-request-v1.md'
DOCS={PROFILE,'protocol/migrations/p09-source-case-conversion-v1.md','CURRENT_STATE.md',
    'implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED={SOURCE+'search/replacement/atoms/case.rs',SOURCE+'search/replacement/atoms/case/mapping.rs',
    SOURCE+'search/replacement/atoms/unicode/plan.rs',SOURCE+'search/replacement/atoms/readback.rs',SOURCE+'search/replacement/atoms/review.rs',
    SOURCE+'search/reviews/selector.rs',SOURCE+'search/reviews/selector/styles.rs',SOURCE+'search/inspection/definitions.rs',
    SOURCE+'forms.rs',SOURCE+'fields.rs','crates/hwpx-package/tests/document_import_case_conversion.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'tools/p09/run_case_product_components.py','tools/p09/run_case_conversion_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CASE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CASE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);source=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='51fdcd507529732e6916085630859511c9fa93541988356d2cd67cbba9744a00'
            and passed['state']=='PASS_CASE_TWENTY_TWO_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==676 and passed['new_product_cases']==22
            and not passed['source64_reexecuted']and not passed['old172_products_reexecuted'],'EXACT22_CASE_PRODUCTS_AND676_INPUT_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='9052f0f34c12c073122b4ed0cf1f13c111a0baef83720e151675db6ef6b738b5'
            and source['state']=='PASS_CASE1_REPAIRED63_RETAINED_NOT_CASE_STORED_PRODUCT_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==673 and source['total_distinct_cases']==64,'EXACT_PRIOR64_SOURCE_CASES_RETAINED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_CASE_STORE_REQUEST_SOURCE_SECURITY_AND_TESTS_MATCH_PASS173')
        target.inverse(q,old);cases=target.expected(q);target.good_step(passed['steps'][0],cases)
        c.require(passed['original_product_and_source_test_bodies_inverse_verified']and passed['one_current_source_proof_case_compiler_and_no_query_replay_on_delivery'],
            'ORIGINAL_PRODUCT_SOURCE_ACCESS_BOUNDARIES_AND_ONE_CASE_COMPILER_RETAINED')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 원본 일치 대소문자 변환',1)[0]
        for marker in('product-case-conversion-request/v1','convert_case_matches','case_policy','RouteUnqualified','676fresh/final676',
            '신규제품22pass','source64·기존제품172·공식249','133.891','47.687','11.79','1716.68MiB','40.82%',
            'SEARCH-014','P09/A12/A13 OPEN','Native011 미승인/미실행'):
            c.require(marker in profile,'PRECISE_CASE_PRODUCT_CONTRACT_COUNTS_RESOURCES_NEXT_WORK_AND_OPEN_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-013 | 대소문자 변환 | 명시적 Unicode17 기본 upper/lower source 고유64개·현재 저장/엄격한 제품 JSON 신규22개 검증, 전체 통합/target 계약 미완료 |'in progress,
            'ALL19_FEATURE_ROWS_WITH_CURRENT_CASE_PRODUCT_AND_REMAINING_FULL_CONTRACT')
        for marker in('676fresh/final676','신규제품22pass','다음 접근허용 불필요 작업은 SEARCH-014','공식158/249',
            'P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_CASE_PRODUCT_PROGRESS_AND_ORIGINAL_NATIVE_AND_PHASE_BOUNDARIES')
        c.require('p09-case-product-request-v1.md'in q.text('protocol/migrations/p09-source-case-conversion-v1.md'),
            'CASE_SOURCE_LINKS_CURRENT_STORE_PRODUCT_WITHOUT_CLAIMING_FULL_EXECUTION')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_CASE_PRODUCT_SELECTED_SOURCE_DOCS_SYNC_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_cases=22,source_cases_retained=64,old_product_cases_retained=172,source676_or_Cargo_or_tests_reexecuted=False,
            next_work='SEARCH014_explicit_width_conversion_policy_and_original_source_compiler_with_remaining_SEARCH013_integration_target_gates_preserved')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CASE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CASE_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
