"""Scoped35-case style core code/document closure without repeating tests or the whole input audit."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_styles_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-selector-styles-sync104.v1.json'
PROFILE='protocol/migrations/p09-review-selector-style-core-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-search-inspection-v2.md','protocol/migrations/p09-source-definition-style-search-v3.md',
    'protocol/migrations/p09-review-selector-product-requests.md','protocol/migrations/p09-stored-review-selector-candidates-v1.md',
    'protocol/migrations/p09-selector-result-navigation-v1.md'}
RETAINED={'crates/hwpx-package/tests/'+n+'.rs'for n in base.TARGETS[1:]}|{
    'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/forms.rs',
    'crates/hwpx-package/src/document_import/search/selector.rs','crates/hwpx-package/src/document_import/search/extract.rs',
    'crates/hwpx-package/src/document_import/search/navigation.rs','crates/hwpx-package/src/document_import/search/reviews.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector/review.rs',
    'tools/p09/run_selector_styles_components.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_STYLES_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_STYLES_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='1b06a32b67977b36b32eef0f9db9bf6044be64c6795414eaff1eafbf0af42119'
            and passed['state']=='PASS_SELECTOR_STYLE_EIGHT_NEW_TWENTY_SEVEN_AFFECTED_NOT_STORED_CONTROL_NATIVE_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==35 and passed['new_core_cases']==8 and passed['affected_cases']==27
            and passed['fresh_inputs']==passed['final_fresh_hashes']==552,'EXACT_THIRTY_FIVE_STYLE_CORE_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='01bde329542d9c59a77e9457a7e74af803c4fed0bf99e3d0085e49c4a3276fd2'
            and previous['cleanup']and previous['total_executed_cases']==33,'EXACT_RETAINED_NAVIGATION_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_STYLE_PREDICATES_WINDOWS_SOURCE_HEADER_TESTS_AND_UNCHANGED_PRODUCT_MATCH_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_STYLE_CORE_TEST_BINARY');step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==35 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_EXPECTED_STYLE_CORE_CASES_PASS_WITHOUT_IGNORES_OR_FILTERS')
        c.require(step['diagnostics']==['warning: function `package` is never used','warning: function `with_body` is never used','warning: `hwpx-package` (test "selector_styles_bundle") generated 2 warnings'],
            'TWO_UNSUPPRESSED_SHARED_FIXTURE_HELPER_WARNINGS')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'JOB_TERMINAL_WITH_ORIGINAL_RESOURCE_READBACK')
        c.require(not passed['stored_product_control_or_native_qualification_added']and not passed['previous_thirty_three_navigation_and_other_completed_suites_reexecuted']
            and passed['original_predicates_review_resolution_exclusion_hash_and_bounds_inverse_verified']and passed['all_four_selector_windows_and_policy_before_style_match_caps']
            and not passed['effective_cascade_or_control_coordinate_semantics_inferred'],'EXACT_STYLE_CORE_WITH_PRODUCT_CONTROL_AND_NATIVE_REMAINING')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('35pass·552fresh/final552','4종 selector·review 서식 core 통과','새 결합 저장/JSON','저장/제품 연결, 이후 컨트롤의 정확한 위치 투영',
            '없는 위치도 있어 선택 문단이라는 이유만으로 허용하지 않으며'):
            c.require(marker in progress,'CURRENT_PROGRESS_DISTINGUISHES_CORE_STORED_PRODUCT_AND_CONTROL_COORDINATES')
        profile=q.text(PROFILE)
        for marker in('not a current stored-service or strict product JSON route','Every original scalar contributing to an NFC match',
            'Definition admission resolves all present indexed references','source-review-selector-style-search/v1','35 total with552 fresh/final552',
            'two warnings; they are not suppressed','Some controls','does not substitute that paragraph fallback',
            'Native011 is unapproved/unexecuted','P09/A12/A13 stay OPEN'):
            c.require(marker in profile,'PRECISE_PREDICATES_SCOPE_POLICY_BOUNDS_WARNINGS_AND_OPEN_PRODUCT_CONTROL_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-review-selector-style-core-v1.md'in q.text(name),'RELATED_STYLE_SOURCE_AND_PRODUCT_PROFILES_LINK_NEW_CORE_QUALIFICATION')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 선택 범위 다시 찾기',1)[0]
        for marker in('35pass·552fresh/final552','저장 서비스·엄격한 제품 요청·컨트롤 좌표 결속은 아직 추가하지 않았다','149.640초','77.047초','2.33초','28.031초',
            '20.83%','35.5548%','5.0859%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_STYLE_CORE_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_STYLE_CORE_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_CONTROL_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_core_cases=35,new_core_cases=8,affected_cases=27,
            entire_552_input_set_reaudited=False,tests_reexecuted=False,stored_product_control_native_or_execution_qualified=False,
            next_work='Stored_and_strict_product_binding_of_review_selector_styles_then_exact_control_scope_projection')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_STYLES_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_STYLES_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
