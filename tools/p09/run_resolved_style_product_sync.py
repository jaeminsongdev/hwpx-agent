"""Selected v9 code/document closure; no Cargo/tests or639-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_resolved_style_product_components as product
from run_style_replacement_sync import good_step
shared,c,a=product.shared,product.c,product.a
OUTPUT='implementation/p09/evidence/p09-361-resolved-style-product-sync151.v1.json'
PROFILE='protocol/migrations/p09-resolved-style-product-v9.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-resolved-formatting-v1.md','protocol/migrations/p09-review-selector-style-product-v7.md',
    'protocol/migrations/p09-source-definition-style-search-v3.md'}
RETAINED={'crates/product-cli/src/form_product_request/stored_source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/navigation.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector/styles.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search/review_styles.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector/resolved_styles.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions/resolved.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs',
    'crates/hwpx-package/src/document_import/search/navigation.rs','crates/hwpx-package/tests/document_import_resolved_style_search.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_resolved_style_product_components.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py',product.prior.prior.CAPTURE}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'RESOLVED_STYLE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=product.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_RESOLVED_STYLE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(product.OUTPUT);source=q.json(product.prior.OUTPUT)
        c.require(q.snapshots[product.OUTPUT]['sha256']=='5e421a1580b6b0b0830a685eb7cd0cdcf427d886762a6fe07964a6a4ec33a33d'
            and passed['state']=='PASS_RESOLVED_STYLE_TWENTY_PRODUCTS_NOT_FULL_CASCADE_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==639
            and passed['new_product_cases']==passed['total_executed_cases']==20 and passed['retained_original_products']==104
            and passed['retained_source_resolution_cases']==18 and not passed['previous_product_source_and_unrelated_cases_reexecuted']
            and not passed['full_effective_cascade_or_visibility_qualified'],'EXACT_TWENTY_NEW_PRODUCTS_WITH_TERMINAL_INPUT_CLOSURE')
        c.require(q.snapshots[product.prior.OUTPUT]['sha256']=='e6b9b79a4f241f9510edf6aaa8d46364765439a80a81be842f99475752ab16a1'
            and source['cleanup']and source['new_resolution_cases']==18,'EXACT_PRIOR_RESOLUTION_CORE_NOT_NEW_PRODUCT_EXECUTION')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(product.NEW|product.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_PRODUCTS_SOURCE_PARSERS_NAVIGATION_GUARDS_AND_TESTS_MATCH_PASS')
        product.inverse(q,old);cases=product.expected(q);good_step(passed['steps'][0],cases)
        c.require(len(passed['steps'])==1 and passed['steps'][0]['diagnostics']==[]
            and passed['steps'][0]['bounded_output_observation']['safe_warning_locations']==[],
            'EXACT_TWENTY_PASSES_WITHOUT_ERRORS_WARNINGS_OR_SKIPS')
        c.require(len(product.legacy_expected(q))==47 and len(product.run_expected(q))==18 and len(product.text_expected(q))==18
            and len(product.paragraph_expected(q))==21,'ALL_104_PRIOR_PRODUCT_IDENTITIES_RETAINED_NOT_REEXECUTED')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('product-source-search-request/v9','not complete SEARCH-003 effective formatting',
            'kind=find_resolved_style','original typed Resolution/Unresolved error','original recursive unique JSON/object parser enforces16 KiB',
            'old v1 through v8 schemas reject the new operation','original finish_search, fresh_json, verify and with_verified_json',
            'no clone/reimport','Retained-result delivery does not repeat query or resolution','strict next parser',
            'Components150 passes20 new product cases with639 fresh/final639','Original products104 and resolution source18',
            '121.843 seconds','39.422 seconds','6.42 seconds','37.875 seconds','1694.85 MiB','5.3195%','41.02%','23.9416%',
            'Next is authoritative text-style precedence','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_V9_CONTRACT_ACCESS_NAVIGATION_COUNTS_RESOURCE_AND_REMAINING_BOUNDARY')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_PRESERVED')
        for marker in('직접 서식 해석 core/현재 저장/v9 JSON·cursor 통과','cascade/visibility·전체 계약 미완료',
            '150 신규제품20pass·639fresh/final639','기존제품104·해석source18·공식249','typed Resolution/Unresolved'):
            c.require(marker in progress,'V9_SEARCH_CURSOR_COMPLETION_NOT_FULL_NATIVE_CASCADE')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 선택 범위 직접 서식 해석',1)[0]
        for marker in('components150 신규제품20pass·639fresh/final639','기존제품104·해석source18·공식249',
            '다음은 text-style 우선순위·누락 축·Native 숨김','공식158/249','잔여91','next165','P09/A12/A13 OPEN',
            '목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_V9_PRODUCT_AND_UNCHANGED_PHASE_QUEUE_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-resolved-style-product-v9.md'in q.text(name),'RELATED_SOURCE_AND_PRODUCT_PROFILES_LINK_V9_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_API_V12_STAYS_INCOMPLETE_WITH_FOUR_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_RESOLVED_STYLE_PRODUCT_CODE_DOCUMENT_SYNC_NOT_FULL_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=20,retained_original_products=104,retained_resolution_source_cases=18,tests_reexecuted=False,entire_639_input_set_reaudited=False,
            next_work='Qualified_text_style_precedence_missing_axes_native_visibility_then_full_scope_filter_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'RESOLVED_STYLE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_RESOLVED_STYLE_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
