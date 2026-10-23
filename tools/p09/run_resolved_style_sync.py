"""Selected resolution-code/document closure; no test or635-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_resolved_style_components as product
from run_style_replacement_sync import good_step
shared,c,a=product.shared,product.c,product.a
OUTPUT='implementation/p09/evidence/p09-361-resolved-style-sync149.v1.json'
PROFILE='protocol/migrations/p09-source-resolved-formatting-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-definition-style-search-v3.md','protocol/migrations/p09-review-selector-style-core-v1.md',
    'protocol/migrations/p09-paragraph-style-product-request-v1.md'}
RETAINED={'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/inspection.rs',
    'crates/hwpx-package/src/document_import/search/reviews.rs','crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs',
    'crates/hwpx-package/src/document_import/search/scope.rs','crates/hwpx-package/src/document_import/search/selector.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog.rs','crates/hwpx-package/src/character_style.rs',
    'crates/hwpx-package/src/paragraph_style.rs','crates/hwpx-package/src/document_import/search/navigation.rs',
    'crates/hwpx-package/tests/document_import_search_definitions.rs','crates/hwpx-package/tests/document_import_selector_styles.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_resolved_style_components.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py',product.prior.CAPTURE}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'RESOLVED_STYLE_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=product.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_RESOLVED_STYLE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(product.OUTPUT);baseline=q.json(product.BASELINE)
        c.require(q.snapshots[product.OUTPUT]['sha256']=='e6b9b79a4f241f9510edf6aaa8d46364765439a80a81be842f99475752ab16a1'
            and passed['state']=='PASS_RESOLVED_DIRECT_STYLE_EIGHTEEN_NEW_NOT_FULL_CASCADE_STORED_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==635
            and passed['new_resolution_cases']==passed['total_executed_cases']==18
            and not passed['previous_product_source_and_unrelated_cases_reexecuted']
            and not passed['full_effective_cascade_or_visibility_qualified'],'EXACT_EIGHTEEN_NEW_RESOLUTION_CASES_WITH_TERMINAL_INPUT_CLOSURE')
        c.require(q.snapshots[product.BASELINE]['sha256']=='989da55b913541ad97bf16fe68a8d1d5b98bdeacb6b13134349aa065a92b3e6f'
            and baseline['cleanup']and baseline['new_product_cases']==21,'EXACT_PRIOR_PARAGRAPH_PRODUCT_BASELINE_RETAINED')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        for name in sorted(product.NEW|product.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_RESOLVER_MATCHER_READERS_GUARDS_AND_TESTS_MATCH_PASS')
        product.inverse(q,old);cases=product.expected(q);good_step(passed['steps'][0],cases)
        c.require(len(passed['steps'])==1 and passed['steps'][0]['diagnostics']==[]
            and passed['steps'][0]['bounded_output_observation']['safe_warning_locations']==[],
            'EXACT_EIGHTEEN_PASSES_NO_ERRORS_WARNINGS_OR_SKIPS')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('source-resolved-direct-formatting/v1','not complete Native effective-style/cascade/visibility',
            'https://tech.hancom.com/python-hwpx-parsing-2/',
            '1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/t.h',
            'storage declaration is not a precedence rule','including ID0 or a coincidentally equal value',
            'An unrequested axis need not be resolved','before query matching, even when the query would find nothing',
            'Hidden-explanation/MEMO policy exclusion happens before coverage','deduplicated segment set is assessed once',
            'An empty scalar window selects0','Components148 passes18 new tests with635 fresh/final635',
            '108.484 seconds','27.094 seconds','2.19 seconds','25.422 seconds','1684.28 MiB','5.2864%','69.14%','23.8824%',
            'Next is current stored/strict product binding','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_RESOLUTION_SOURCE_SCOPE_UNRESOLVED_COUNTS_RESOURCE_AND_REMAINING_BOUNDARY')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_PRESERVED')
        for marker in('직접 서식 요청축 해석 core 통과','해석 경로 저장/제품·cascade/visibility·전체 계약 미완료',
            '148에서 신규18pass·635fresh/final635','검색어가 없어도 Unresolved 오류이며 일치0이 아니다'):
            c.require(marker in progress,'DIRECT_RESOLUTION_PROGRESS_NOT_FULL_EFFECTIVE_STYLE_OR_PRODUCT_COMPLETION')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 문단 스타일 치환 저장과 제품 연결',1)[0]
        for marker in('components148 신규18pass·635fresh/final635','다음은 이 해석 결과의 현재 저장/엄격한 제품 요청 연결',
            '전체 유효 cascade/숨김 완료로 승격하지 않는다','공식158/249','잔여91','next165','P09/A12/A13 OPEN',
            '목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_RESOLUTION_AND_UNCHANGED_PHASE_QUEUE_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-resolved-formatting-v1.md'in q.text(name),'RELATED_PROFILES_LINK_NEW_REQUIRED_AXIS_RESOLUTION_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_API_V12_STAYS_INCOMPLETE_WITH_FOUR_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_RESOLVED_STYLE_CODE_DOCUMENT_SYNC_NOT_FULL_CASCADE_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_resolution_cases=18,tests_reexecuted=False,entire_635_input_set_reaudited=False,
            next_work='Current_stored_strict_product_binding_and_qualified_text_precedence_visibility_then_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'RESOLVED_STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_RESOLVED_STYLE_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
