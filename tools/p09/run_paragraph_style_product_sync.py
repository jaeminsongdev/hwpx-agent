"""Selected current paragraph product/document closure; no Cargo or635-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_paragraph_style_product_components as product
from run_style_replacement_sync import good_step
shared,c,a=product.shared,product.c,product.a
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-product-sync147.v1.json'
PASSED='implementation/p09/evidence/p09-361-paragraph-style-product-compile-recovery146.v1.json'
FAILED='implementation/p09/evidence/p09-361-paragraph-style-product-count-recovery145.v1.json'
PROFILE='protocol/migrations/p09-paragraph-style-product-request-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-paragraph-style-replacement-v1.md',
    'protocol/migrations/p09-text-style-product-request-v1.md','protocol/migrations/p09-character-style-product-request-v1.md',
    'protocol/migrations/p09-source-definition-style-search-v3.md'}
RETAINED={'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/styles.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/text_styles.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs/verify.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector/styles/paragraphs.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/text/output.rs',
    'crates/hwpx-package/src/id_index.rs','crates/hwpx-package/tests/document_import_paragraph_style_replacement.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_paragraph_style_product_components.py',
    'tools/p09/run_paragraph_style_product_count_recovery.py','tools/p09/run_paragraph_style_product_compile_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py',product.CAPTURE}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PARAGRAPH_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=product.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(PASSED);source=q.json(product.prior.OUTPUT)
        c.require(q.snapshots[PASSED]['sha256']=='989da55b913541ad97bf16fe68a8d1d5b98bdeacb6b13134349aa065a92b3e6f'
            and passed['state']=='PASS_PARAGRAPH_PRODUCT_TWENTY_ONE_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==635 and passed['new_product_cases']==passed['total_executed_cases']==21
            and passed['retained_original_products']==83 and not passed['original_products_reexecuted']
            and not passed['source_core_and_unrelated_suites_reexecuted'],'EXACT_TWENTY_ONE_PRODUCT_PASSES_AND_TERMINAL_WHOLE_INPUT_CLOSURE')
        c.require(q.snapshots[product.prior.OUTPUT]['sha256']=='8d96f12627a043474a009552c0c51ee29f73f9b41c6eb5b62c66afc2cbb9eb91'
            and source['total_distinct_cases']==38 and source['actual_current_cases']==1 and source['retained_cases']==37
            and source['cleanup'],'EXACT_PARAGRAPH_SOURCE_ONE_CURRENT_THIRTY_SEVEN_RETAINED_NOT_NEW_EXECUTION')
        failed=q.json(product.OUTPUT);compile_failed=q.json(FAILED)
        c.require(q.snapshots[product.OUTPUT]['sha256']=='31ca429ecbfcc1d0b6c6626a49530458f0b3998786ce1e6173998fee7e607c54'
            and failed['state']=='FAILED_PARAGRAPH_PRODUCT_COMPONENTS'and failed['cleanup']and failed['steps']==[]
            and failed['error_code']=='EXACT_TWENTY_NEW_PARAGRAPH_PRODUCT_CASE_IDENTITIES','FAILED_COUNT_PREFLIGHT_PRESERVED_NOT_PROMOTED')
        c.require(q.snapshots[FAILED]['sha256']=='0d40b60047d1d573a67cd853400db117fe7e22796590f2237c33a974c4bdbe81'
            and compile_failed['state']=='FAILED_PARAGRAPH_PRODUCT_COMPONENTS'and compile_failed['cleanup']
            and compile_failed['steps'][0]['exit_code']==101 and compile_failed['steps'][0]['tests']==[]
            and compile_failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0433'],
            'FAILED_TEST_ORACLE_COMPILE_WITH_ZERO_TESTS_PRESERVED_NOT_PROMOTED')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(product.NEW|product.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_PRODUCT_CORE_GUARD_WRITER_AND_TEST_INPUTS_MATCH_PASS')
        product.inverse(q,old);cases=product.expected(q);good_step(passed['steps'][0],cases)
        c.require(len(passed['steps'])==1 and passed['steps'][0]['diagnostics']==[]
            and passed['steps'][0]['bounded_output_observation']['safe_warning_locations']==[],
            'EXACT_COMPLETED_PRODUCT_CASES_NO_ERRORS_WARNINGS_FAILURES_OR_IGNORES')
        c.require(len(product.legacy_expected(q))==47 and len(product.run_expected(q))==18 and len(product.text_expected(q))==18,
            'ALL_EIGHTY_THREE_PREVIOUS_PRODUCT_IDENTITIES_RETAINED_NOT_REEXECUTED')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('product-paragraph-style-replacement-request/v1','not a full SEARCH-008',
            'kind=replace_paragraph_style_reference','axis=paragraph_property','axis=paragraph_style',
            'whole_matched_paragraph_within_scope','existing source typed catalog','original recursive unique JSON/object parser',
            'enforces16 KiB','Ownership transfer adds no clone or reimport','integrity callback before consumer access',
            'Search/paragraph lowering is not repeated','Components144 stopped before Cargo','Count recovery145',
            'Recovery146 passes21 new product cases with635 fresh/final635','Original products83 and paragraph source38',
            '103.156 seconds','21.078 seconds','13.91 seconds','18.922 seconds','749.05 MiB','2.3510%','56.44%','24.3988%',
            'Next is effective cascade/visibility','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_PARAGRAPH_PRODUCT_CONTRACT_FAILURES_COUNTS_RESOURCE_AND_REMAINING_BOUNDARY')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_PRESERVED')
        for marker in('부분 run/text-style·문단/이름 스타일 core·현재 저장/엄격한 v1 제품 통과',
            '유효 서식/전체 계약 미완료','신규제품21pass·635fresh/final635','기존제품83·문단source38·공식249',
            '다음은 유효 cascade/숨김과 전체 selector/filter 계약'):
            c.require(marker in progress,'SOURCE_PRODUCT_COMPLETION_SEPARATE_FROM_EFFECTIVE_STYLE_AND_WHOLE_CONTRACT')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 문단 모양과 이름 있는 문단 스타일 원본 치환',1)[0]
        for marker in('신규제품21pass·635fresh/final635','기존제품83·문단source38·공식249','공식158/249','잔여91','next165',
            'P09/A12/A13 OPEN','목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_PRODUCT_AND_UNCHANGED_PHASE_QUEUE_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-paragraph-style-product-request-v1.md'in q.text(name),'RELATED_STYLE_PROFILES_LINK_CURRENT_PRODUCT_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_API_V12_STAYS_INCOMPLETE_WITH_FOUR_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_PARAGRAPH_STYLE_PRODUCT_CODE_DOCUMENT_SYNC_NOT_FULL_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=21,retained_original_products=83,retained_paragraph_source_components=38,tests_reexecuted=False,entire_635_input_set_reaudited=False,
            next_work='Effective_cascade_visibility_then_full_scope_filter_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PARAGRAPH_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PARAGRAPH_PRODUCT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
