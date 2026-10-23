"""Selected width-source/table/docs closure; no24-case/Cargo/683-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_width_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-width-sync176.v1.json'
PROFILE='protocol/migrations/p09-source-width-conversion-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-case-product-request-v1.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED={SOURCE+'search/replacement/atoms/unicode/plan.rs',SOURCE+'search/replacement/atoms/unicode/transform.rs',
    SOURCE+'search/replacement/atoms/readback.rs',SOURCE+'search/replacement/atoms/review.rs',
    SOURCE+'search/replacement/atoms/styles/text/output.rs',SOURCE+'search/replacement/atoms/case.rs',
    SOURCE+'search/reviews/selector.rs',SOURCE+'search/reviews/selector/styles.rs',SOURCE+'search/inspection/definitions.rs',
    SOURCE+'forms.rs',SOURCE+'fields.rs','crates/product-cli/src/reference_validation_product/source.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs','crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
    'tools/p09/run_width_components.py','tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WIDTH_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WIDTH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);baseline=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='257fc7d6b1d0398ff2e8329ddb590e220c7483933945c84628dcc321fb754e7f'
            and passed['state']=='PASS_WIDTH24_ALL226_PAIRS28_KANA_NOT_STORED_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==683 and passed['new_source_cases']==24
            and passed['width_pairs']==226 and passed['kana_pairs']==28 and not passed['old194_products_and64_source_reexecuted'],
            'EXACT24_WIDTH_PASSES_ALL226_AND28_TABLES_AND683_INPUT_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='51fdcd507529732e6916085630859511c9fa93541988356d2cd67cbba9744a00',
            'EXACT_PRIOR173_CASE_PRODUCT_SOURCE_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_WIDTH_TABLES_LICENSE_SOURCE_GUARDS_AND_TESTS_MATCH_PASS175')
        target.inverse(q,old);cases=target.expected(q);target.good_step(passed['steps'][0],cases)
        c.require(passed['all_shared_plan_guard_and_writer_bodies_unchanged']and passed['width_only_mapping_not_general_normalization_or_display_width']
            and passed['same_atom_changes_coalesced_and_cross_run_first_contributor_explicit'],'EXACT_WIDTH_ONLY_MAPPING_SHARED_UNCHANGED_GUARDS_AND_BOUNDED_PATCHES')
        c.require(q.snapshots[target.FIXTURE]['sha256']=='5c5f8907d369cd1fd2187bd9e3a6fe1f677949fd61bb5196b0e18f98ae5fc239',
            'EXACT_UCD17_EXTRACTED_ORACLE_FIXTURE_NOT_A_REPEATED_NETWORK_DOWNLOAD')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 대소문자 변환 저장과 제품 연결',1)[0]
        for marker in('source-match-width-conversion/v1','Unicode17WidthPairsWithKanaPairs','FirstOriginalRunRetainAllRuns',target.UCD_SHA,
            '2198209bytes','226개','가타카나28개','신규원본24pass','683fresh/final683','기존제품194·원본64·공식249',
            '120.656','33.172','7.69','1710.41MiB','54.09%','P09/A12/A13 OPEN','Native011 미승인/미실행'):
            c.require(marker in profile,'PRECISE_WIDTH_POLICY_UCD_IDENTITY_COUNTS_RESOURCES_AND_OPEN_NATIVE_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-014 | 전각·반각 변환 | Unicode17 폭226쌍·가타카나28쌍과 원본 신규24개 검증, 현재 저장/엄격한 제품 JSON·전체 계약/Native 미완료 |'in progress,
            'ALL19_FEATURE_ROWS_WITH_EXACT_WIDTH_SOURCE_ONLY_COMPLETION_BOUNDARY')
        for marker in('683fresh/final683','신규원본24pass','다음 접근허용 불필요 작업은 SEARCH-014 현재 저장 서비스',
            '공식158/249','P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_STATE_WIDTH_SOURCE_PROGRESS_AND_REMAINING_PRODUCT_AND_NATIVE_BOUNDARIES')
        c.require('p09-source-width-conversion-v1.md'in q.text('protocol/migrations/p09-case-product-request-v1.md'),
            'PREVIOUS_CASE_PRODUCT_LINKS_WIDTH_SOURCE_WITHOUT_WIDENING_CASE_SEMANTICS')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_WIDTH_SOURCE_SELECTED_DOCS_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            source_cases=24,width_pairs=226,kana_pairs=28,source683_or_Cargo_or_tests_reexecuted=False,
            next_work='Current_stored_and_strict_product_binding_of_explicit_width_conversion_then_remaining_P09_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WIDTH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WIDTH_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
