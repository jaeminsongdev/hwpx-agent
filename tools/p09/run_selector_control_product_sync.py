"""Scoped46-case v8 control product code/document closure; no Cargo or completed test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_control_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-selector-control-product-sync111.v1.json'
PROFILE='protocol/migrations/p09-review-selector-control-product-v8.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-review-selector-control-core-v1.md','protocol/migrations/p09-source-search-inspection-v2.md',
    'protocol/migrations/p09-selector-result-navigation-v1.md','protocol/migrations/p09-review-selector-style-product-v7.md'}
RETAINED={base.OLD_SEARCH,base.OLD_NAV,base.prior.base.TEST,base.prior.base.GEOMETRY,base.prior.base.CONTROL,base.prior.base.CORE,
    base.prior.base.REVIEW,base.prior.base.INSPECT,base.prior.base.NAV,
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/navigation.rs','crates/product-cli/src/form_product_request/stored_source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector/styles.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search/review_styles.rs',
    'tools/p09/run_selector_control_product_components.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_CONTROL_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_CONTROL_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='4965fe2b5d8e247f4ab7849a7aee4e1e2fb7d2cb980747f85d72cd67a8d383f3'
            and passed['state']=='PASS_SELECTOR_CONTROL_V8_THIRTEEN_NEW_THIRTY_THREE_AFFECTED_NOT_CONTROL_PARAMETER_SEMANTICS_NATIVE_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==46 and passed['new_product_cases']==13 and passed['affected_cases']==33
            and passed['fresh_inputs']==passed['final_fresh_hashes']==571,'EXACT_FORTY_SIX_PRODUCT_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='2f5616d4cff11495fcfb2455284a4cc698147a70f4c0f2b353b5934bd585b1e2'
            and previous['cleanup']and previous['total_distinct_core_cases']==59,'EXACT_RETAINED_FIFTY_NINE_CORE_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_CONTROL_PRODUCT_CORE_AUTH_SOURCE_FIXTURES_AND_TESTS_MATCH_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_CONTROL_PRODUCT_TEST_BINARY');step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==46 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_EXPECTED_PRODUCT_CASES_PASS_WITHOUT_IGNORES_OR_FILTERS')
        c.require(step['diagnostics']==['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "selector_control_product") generated 1 warning'],
            'ONLY_KNOWN_LEGACY_FIXTURE_UNUSED_PACKAGE_WARNING')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'JOB_TERMINAL_WITH_ORIGINAL_RESOURCE_READBACK')
        c.require(not passed['full_control_parameter_semantics_or_native_qualification_added']and not passed['previous_fifty_nine_core_and_other_completed_suites_reexecuted']
            and passed['original_service_finish_fresh_crypto_authorization_and_final_head_inverse_verified']and passed['old_product_schemas_and_navigation_preserved']
            and passed['retained_output_and_next_do_not_repeat_query_or_index']and passed['all_four_actual_control_scopes_and_explicit_policies_bound'],
            'CURRENT_V8_CONTROL_REQUEST_NOT_NATIVE_SEMANTICS_OR_FULL_EXECUTION')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('46pass·571fresh/final571','실제 control_anchor의 4종 범위·review 정책·현재 저장/v8 JSON·region cursor 통과',
            'v7 서식/v8 컨트롤 cursor','핵심59·기존v7제품45·공식249 대기열은 재실행하지 않았고','다음은 전체 검색 계약과 정규식/서식/컨트롤 치환'):
            c.require(marker in progress,'CURRENT_V8_CONTROL_PRODUCT_COUNTS_SCOPE_CURSOR_AND_REMAINING_CONTRACT')
        profile=q.text(PROFILE)
        for marker in('product-source-search-request/v8','regex=false, case_sensitive=true','both include_hidden_explanations and',
            'selector.revision_id must equal base_revision','before any source read','original16 KiB unique JSON/object parser',
            '46 total with571 fresh/final571','One existing unused fixture package helper warning remains','require_current_product_route',
            'RouteUnqualified','unapproved/unexecuted'):
            c.require(marker in profile,'PRECISE_V8_SCHEMA_AUTH_CURSOR_RESOURCE_AND_OPEN_FULL_PRODUCT_NATIVE_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-review-selector-control-product-v8.md'in q.text(name),'RELATED_SOURCE_INSPECTION_STYLE_AND_NAVIGATION_PROFILES_LINK_CURRENT_V8')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 컨트롤 선택 범위 core',1)[0]
        for marker in('46pass·571fresh/final571','product-source-search-request/v8','177.953초','103.079초','5.19초','36.844초',
            '23.83%','36.9131%','5.1601%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_V8_PRODUCT_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_CONTROL_V8_CODE_DOCUMENT_SYNC_NOT_CONTROL_PARAMETER_SEMANTICS_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_product_cases=46,new_product_cases=13,affected_cases=33,
            entire_571_input_set_reaudited=False,tests_reexecuted=False,full_control_parameter_semantics_native_or_execution_qualified=False,
            next_work='Full_search_contract_and_regex_style_control_replacement_conversion_source_edit_protection_paths')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_CONTROL_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_CONTROL_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
