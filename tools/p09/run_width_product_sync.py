"""Selected width-product/source/docs closure; no24-product/24-source/688-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_width_product_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-width-product-sync179.v1.json'
PROFILE='protocol/migrations/p09-width-product-request-v1.md'
DOCS={PROFILE,'protocol/migrations/p09-source-width-conversion-v1.md','protocol/migrations/p09-case-product-request-v1.md',
    'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED={target.prior.CORE,target.prior.MAPPING,target.prior.TABLE,target.prior.LICENSE,target.prior.FIXTURE,
    SOURCE+'search/replacement/atoms/unicode/plan.rs',SOURCE+'search/replacement/atoms/readback.rs',SOURCE+'search/replacement/atoms/review.rs',
    SOURCE+'search/reviews/selector.rs',SOURCE+'search/reviews/selector/styles.rs',SOURCE+'search/inspection/definitions.rs',SOURCE+'forms.rs',SOURCE+'fields.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'tools/p09/run_width_product_components.py','tools/p09/run_width_components.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WIDTH_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WIDTH_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);source=q.json(target.prior.OUTPUT);failed=q.json(target.FAILED)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='37e2065b5df76f9ff8732911e647e1d563ef0b720fe827f298b5543c562ce41c'
            and passed['state']=='PASS_WIDTH_TWENTY_FOUR_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==688 and passed['new_product_cases']==24
            and not passed['source24_reexecuted']and not passed['old194_products_reexecuted'],'EXACT24_WIDTH_PRODUCTS_AND688_INPUT_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='257fc7d6b1d0398ff2e8329ddb590e220c7483933945c84628dcc321fb754e7f'
            and source['state']=='PASS_WIDTH24_ALL226_PAIRS28_KANA_NOT_STORED_PRODUCT_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==683 and source['new_source_cases']==24,'EXACT_PRIOR24_WIDTH_SOURCE_CASES_RETAINED')
        c.require(q.snapshots[target.FAILED]['sha256']=='ed25c0b72c00e0cd9b83ce4887b5acb09bb51c1ae9e112a385cc7b7be8bd90eb'
            and failed['state']=='FAILED_WIDTH_PRODUCT_COMPONENTS'and failed['cleanup']and not failed['steps'],'ORIGINAL177_STATIC_FAILURE_RETAINED_WITH_ZERO_CARGO_OR_PRODUCT_TESTS')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_WIDTH_STORE_REQUEST_TABLES_SOURCE_SECURITY_AND_TESTS_MATCH_PASS178')
        target.inverse(q,old);target.prior.tables(q);cases=target.expected(q);target.good_step(passed['steps'][0],cases)
        c.require(passed['original_product_and_source_test_bodies_inverse_verified']and passed['one_current_source_proof_width_compiler_and_no_query_replay_on_delivery']
            and passed['short_prefix_with_exact_all24_observed_identities_verified'],'ORIGINAL_ACCESS_BOUNDARIES_ONE_WIDTH_COMPILER_AND_EXACT_ALL24_IDENTITIES_RETAINED')
        failed_pins={p['path']:p for p in failed['source_pins']};product=q.text(target.PRODUCT)
        c.require(product.count('enum Kind {ConvertWidthMatches}')==1,'ONE_WIDTH_KIND_ENUM_CORRECTION')
        target.audit.inverse(product.replace('enum Kind {ConvertWidthMatches}','enum Kind {ConvertCaseMatches}'),failed_pins[target.PRODUCT],
            'ENTIRE177_PRODUCT_RESTORED_BY_UNDOING_ONLY_CORRECTED_ENUM')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 원본 일치 전각 반각 변환',1)[0]
        for marker in('product-width-conversion-request/v1','convert_width_matches','width_policy','run_policy','RouteUnqualified','ConvertWidthMatches',
            '688fresh/final688','신규제품24pass','source24·기존제품194·공식249','138.422','50.219','12.04','1720.37MiB','40.52%',
            'SEARCH-023','P09/A12/A13 OPEN','Native011 미승인/미실행'):
            c.require(marker in profile,'PRECISE_WIDTH_PRODUCT_CONTRACT_FAILURE_COUNTS_RESOURCES_NEXT_WORK_AND_OPEN_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-014 | 전각·반각 변환 | Unicode17 폭226쌍·가타카나28쌍·원본24개·현재 저장/엄격한 제품 JSON 신규24개 검증, 전체 통합/target 계약 미완료 |'in progress,
            'ALL19_FEATURE_ROWS_WITH_CURRENT_WIDTH_PRODUCT_AND_REMAINING_FULL_CONTRACT')
        for marker in('688fresh/final688','신규제품24pass','다음 접근허용 불필요 작업은 SEARCH-023','공식158/249',
            'P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_WIDTH_PRODUCT_PROGRESS_AND_ORIGINAL_NATIVE_AND_PHASE_BOUNDARIES')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-width-product-request-v1.md'in q.text(name),'SOURCE_WIDTH_AND_PREVIOUS_CASE_PROFILE_LINK_CURRENT_WIDTH_PRODUCT')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_WIDTH_PRODUCT_SELECTED_SOURCE_DOCS_SYNC_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_cases=24,source_cases_retained=24,old_product_cases_retained=194,source688_or_Cargo_or_tests_reexecuted=False,
            next_work='SEARCH023_explicit_whitespace_control_normalization_policy_and_original_source_compiler_with_remaining_SEARCH014_integration_target_gates_preserved')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WIDTH_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WIDTH_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
