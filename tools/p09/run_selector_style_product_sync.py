"""Scoped45-case v7 style product code/document closure, no Cargo or test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_style_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-selector-style-product-sync106.v1.json'
PROFILE='protocol/migrations/p09-review-selector-style-product-v7.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-review-selector-style-core-v1.md','protocol/migrations/p09-source-search-inspection-v2.md',
    'protocol/migrations/p09-source-definition-style-search-v3.md','protocol/migrations/p09-review-selector-product-requests.md',
    'protocol/migrations/p09-stored-review-selector-candidates-v1.md','protocol/migrations/p09-selector-result-navigation-v1.md'}
RETAINED={base.OLD_SEARCH,base.OLD_NAV,base.prior.TEST,base.prior.STYLE,base.prior.REVIEW,base.prior.INSPECT,base.prior.DEFINITION,
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/selector.rs','crates/hwpx-package/src/document_import/search/navigation.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs','crates/product-cli/src/form_product_request/stored_source_search/navigation.rs',
    'tools/p09/run_selector_style_product_components.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_STYLE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_STYLE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='c19fabf88bccd64796e973d48d1eaff7e6ca69d0cdb0a6dc7622f8576271527d'
            and passed['state']=='PASS_SELECTOR_STYLE_V7_TWELVE_NEW_THIRTY_THREE_AFFECTED_NOT_CONTROL_COORDINATES_NATIVE_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==45 and passed['new_product_cases']==12 and passed['affected_cases']==33
            and passed['fresh_inputs']==passed['final_fresh_hashes']==559,'EXACT_FORTY_FIVE_PRODUCT_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='1b06a32b67977b36b32eef0f9db9bf6044be64c6795414eaff1eafbf0af42119'
            and previous['cleanup']and previous['total_executed_cases']==35,'EXACT_RETAINED_THIRTY_FIVE_CORE_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_PRODUCT_STYLE_CORE_AUTH_SOURCE_AND_TESTS_MATCH_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_PRODUCT_TEST_BINARY');step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==45 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_EXPECTED_PRODUCT_CASES_PASS_WITHOUT_IGNORES_OR_FILTERS')
        c.require(step['diagnostics']==['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "selector_style_product") generated 1 warning'],
            'ONLY_KNOWN_LEGACY_FIXTURE_UNUSED_PACKAGE_WARNING')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'JOB_TERMINAL_WITH_ORIGINAL_RESOURCE_READBACK')
        c.require(not passed['full_control_coordinate_or_native_qualification_added']and not passed['previous_thirty_five_style_core_and_other_completed_suites_reexecuted']
            and passed['original_service_finish_fresh_crypto_authorization_and_final_head_inverse_verified']and passed['old_product_schemas_and_navigation_preserved']
            and passed['retained_output_and_next_do_not_repeat_query_or_definition_lookup']and passed['all_four_source_scopes_and_explicit_policies_bound'],
            'CURRENT_V7_STYLE_PRODUCT_NOT_CONTROL_COORDINATES_EFFECTIVE_STYLE_OR_NATIVE')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('45pass·559fresh/final559','4종 selector·review 서식 core/현재 저장/v7 JSON·cursor 통과','다음은 컨트롤의 정확한 위치 투영',
            '원 finish_search/fresh_json/verify','핵심35·다른 완료 suite·공식249 대기열은 재실행하지 않았다'):
            c.require(marker in progress,'CURRENT_PROGRESS_V7_STYLE_PRODUCT_AND_REMAINING_CONTROL_PROJECTION')
        profile=q.text(PROFILE)
        for marker in('product-source-search-request/v7','regex is an explicit Boolean','Both body-policy Booleans are mandatory',
            'selector.revision_id must','before any source read','original16 KiB unique JSON/object parser','45 total with559 fresh/final559',
            'The existing unused fixture package helper warning remains','Exact control_anchor position','Native011 is unapproved/unexecuted'):
            c.require(marker in profile,'PRECISE_V7_SCHEMA_AUTH_CURSOR_RESOURCE_AND_OPEN_CONTROL_NATIVE_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-review-selector-style-product-v7.md'in q.text(name),'RELATED_SOURCE_AND_PRODUCT_PROFILES_LINK_CURRENT_V7_QUALIFICATION')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 선택 범위 서식 core',1)[0]
        for marker in('45pass·559fresh/final559','product-source-search-request/v7','컨트롤의 실제 control_anchor 위치와 선택 경계','112.203초','40.344초','10.71초','38.250초',
            '18.01%','33.8018%','5.1125%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_V7_PRODUCT_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_STYLE_V7_CODE_DOCUMENT_SYNC_NOT_CONTROL_COORDINATES_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_product_cases=45,new_product_cases=12,affected_cases=33,
            entire_559_input_set_reaudited=False,tests_reexecuted=False,full_control_coordinates_native_or_execution_qualified=False,
            next_work='Exact_control_anchor_scope_projection_without_paragraph_widening_then_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_STYLE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_STYLE_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
