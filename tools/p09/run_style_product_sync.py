"""Selected product/source/document closure; no Cargo, product or608-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_product_components as product
from run_style_replacement_sync import good_step
shared,c,a=product.shared,product.c,product.a
OUTPUT='implementation/p09/evidence/p09-361-style-product-sync130.v1.json'
PROFILE='protocol/migrations/p09-character-style-product-request-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-character-style-replacement-v1.md','protocol/migrations/p09-regex-insertion-product-request-v2.md'}
RETAINED={'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/review_selector_product.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/regex_insertion_product.rs',
    'crates/product-cli/tests/regex_replacement_product.rs','crates/product-cli/tests/regex_replacement_product/actual_import.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search/replacement/atoms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/render.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/verify.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_style_product_components.py',
    'tools/p09/run_style_replacement_target.py','tools/p09/run_style_replacement_components.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py','tools/p09/bounded_process_progress.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=product.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(product.OUTPUT);source=q.json(product.prior.OUTPUT)
        c.require(q.snapshots[product.OUTPUT]['sha256']=='bfcece3d80b9a8cf588ca019744537554c51328f401d165c95f30bb8ce8d5c56'
            and passed['state']=='PASS_STYLE_PRODUCT_EIGHTEEN_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==608 and passed['new_product_cases']==passed['total_executed_cases']==18
            and passed['original_products_retained']==47 and not passed['original_products_reexecuted']
            and not passed['source_core_and_unrelated_suites_reexecuted'],'EXACT_EIGHTEEN_NEW_PRODUCTS_WITH_CURRENT_INPUT_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[product.prior.OUTPUT]['sha256']=='d2eec58ff9c8fbd2c73d929c4fd8889c842e406434d23916dbf3e72cd17bd75c'
            and source['total_distinct_cases']==59 and source['cleanup'],'EXACT_PRIOR_SOURCE_CORE_NOT_NEW_PRODUCT_EXECUTION')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(product.NEW|product.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_PRODUCT_CORE_AND_ORIGINAL_INPUTS_MATCH_QUALIFIED_RUN')
        product.inverse(q,old);cases=product.expected(q);good_step(passed['steps'][0],cases)
        c.require(len(passed['steps'])==1 and passed['steps'][0]['diagnostics']==[]
            and passed['steps'][0]['bounded_output_observation']['safe_warning_locations']==[],
            'ONLY_EIGHTEEN_EXACT_COMPLETED_PRODUCT_CASES_WITHOUT_DIAGNOSTICS_OR_WARNINGS')
        c.require(len(product.original_product_expected(q))==47,'ORIGINAL_FORTY_SEVEN_TEST_IDENTITIES_RETAINED_NOT_REEXECUTED')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('product-character-style-replacement-request/v1','not a full SEARCH-008','axis=run_character_property',
            'same original typed catalog','recursive unique JSON/object parser','16 KiB','no clone or reimport',
            'does not repeat search or style lowering','inside the integrity callback before calling the consumer',
            '18 new product tests with608 fresh/final608','Original products47 and source core59','120.844 seconds',
            '42.610 seconds','10.31 seconds','40.516 seconds','1668.69 MiB','5.2374%','28.12%','28.3665%',
            'Next is paragraph/named/text-style replacement','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_PARTIAL_STYLE_PRODUCT_OWNERSHIP_ACCESS_RESOURCES_AND_REMAINING_BOUNDARY')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_SEARCH_ROWS_RETAINED')
        for marker in('부분 run 글자 모양 참조·4범위/review core·현재 저장/엄격한 v1 제품 통과',
            '문단/이름/text-style·유효 서식/전체 계약 미완료','신규제품18pass·608fresh/final608',
            '기존제품47개와source59개','다음은 문단/이름/text-style 축의 실제 원본 치환'):
            c.require(marker in progress,'SEARCH008_COMPLETED_PRODUCT_AND_REMAINING_AXES_ARE_SEPARATE')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 부분 run 글자 모양 원본 치환',1)[0]
        for marker in('신규제품18pass·608fresh/final608','기존제품47개·source59개','공식158/249','잔여91','next165',
            'P09/A12/A13 OPEN','목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_PRODUCT_RESULT_WITH_UNCHANGED_QUEUE_PHASE_AND_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-character-style-product-request-v1.md'in q.text(name),'RELATED_PROFILES_LINK_CURRENT_PRODUCT_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_API_V12_REMAINS_INCOMPLETE_WITH_FOUR_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_PRODUCT_CODE_DOCUMENT_SYNC_NOT_FULL_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=18,retained_original_products=47,retained_source_components=59,tests_reexecuted=False,entire_608_input_set_reaudited=False,
            next_work='Paragraph_named_text_style_replacement_then_effective_style_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
