"""Scoped code/document closure of58 retained plus1 recovered cases; no Cargo or test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_controls_recovery as base
shared,c,a=base.shared,base.c,base.a
core=base.base
OUTPUT='implementation/p09/evidence/p09-361-selector-controls-sync109.v1.json'
PROFILE='protocol/migrations/p09-review-selector-control-core-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-search-inspection-v2.md','protocol/migrations/p09-selector-result-navigation-v1.md',
    'protocol/migrations/p09-review-selector-style-product-v7.md'}
RETAINED={'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/extract.rs',
    'crates/hwpx-package/src/document_import/search/reviews.rs','crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/structure.rs','crates/hwpx-package/src/text_flow.rs',
    'crates/hwpx-package/src/text_flow/source_text_span.rs','crates/hwpx-package/src/patch/text_atom_ranges.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'tools/p09/run_selector_controls_components.py','tools/p09/run_selector_controls_recovery.py','tools/p09/run_source_note_api_components.py'}
TESTS={'crates/hwpx-package/tests/'+n+'.rs'for n in('document_import_search_selector','document_import_review_selector',
    'document_import_selector_styles','document_import_search_inspection','document_import_search_navigation')}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_CONTROLS_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_CONTROLS_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);failed=q.json(core.OUTPUT);previous=q.json(core.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='2f5616d4cff11495fcfb2455284a4cc698147a70f4c0f2b353b5934bd585b1e2'
            and passed['state']=='PASS_SELECTOR_CONTROLS_FIFTY_EIGHT_RETAINED_ONE_RECOVERED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==566 and passed['total_distinct_core_cases']==59
            and passed['retained_passes']==58 and passed['actual_reexecuted_cases']==1,'EXACT_RECOVERY_CLOSURE_WITH_FIFTY_EIGHT_REUSED_PASSES')
        c.require(q.snapshots[core.OUTPUT]['sha256']=='f80a3b2b13a31eb81365d8e02dbce27295a50879c01150c51d3e02abf3e941ae'
            and failed['state']=='FAILED_SELECTOR_CONTROLS_COMPONENTS'and failed['cleanup'],'ORIGINAL_FAILURE_RETAINED_WITHOUT_PROMOTION')
        c.require(q.snapshots[core.prior.OUTPUT]['sha256']=='c19fabf88bccd64796e973d48d1eaff7e6ca69d0cdb0a6dc7622f8576271527d'
            and previous['total_executed_cases']==45 and previous['cleanup'],'ORIGINAL_V7_PRODUCT_BASELINE_PRESERVED')
        tested={p['path']:p for p in passed['source_pins']};initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(core.NEW|core.CHANGED|RETAINED|TESTS):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_CONTROL_CODE_TEST_FIXTURES_AND_RUNNERS_MATCH_RECOVERY_INPUTS')
        base.correction(q,initial);core.inverse(q,old);expected=core.expected(q);first=failed['steps'][0];second=passed['steps'][0]
        c.require(first['exit_code']==101 and len(first['tests'])==59 and {n for n,s in first['tests']}==expected
            and [(n,s)for n,s in first['tests']if s!='ok']==[(base.FAILED_CASE,'FAILED')]
            and second['exit_code']==0 and second['tests']==[[base.FAILED_CASE,'ok']]and second['panic_locations']==[]and second['safe_error_variants']==[],
            'ALL_FIFTY_NINE_IDENTITIES_COVERED_WITH_ONLY_ONE_RECOVERY_EXECUTION')
        for step in(first,second):
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
                and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
                'BOTH_OWNED_JOBS_TERMINAL_WITH_ORIGINAL_RESOURCE_BOUNDS')
        c.require(second['diagnostics']==['warning: function `package` is never used','warning: function `with_body` is never used',
            'warning: `hwpx-package` (test "selector_controls_bundle") generated 2 warnings'],'ONLY_TWO_KNOWN_REUSED_FIXTURE_WARNINGS')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');profile=q.text(PROFILE)
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_FEATURE_ROWS_RETAINED')
        for marker in('신규12+영향기존47=고유59개','566fresh/final566','실제 control_anchor의 4종 범위·review 정책·region cursor core 통과',
            '다음은 정확한 컨트롤 범위의 현재 저장/엄격한 제품 JSON 연결'):
            c.require(marker in progress,'CURRENT_CONTROL_CORE_SCOPE_COUNTS_AND_NEXT_PRODUCT_BOUNDARY')
        for marker in('control_anchor START','No element occurs inside a text atom','at most once each','raw CR/LF and control-character references',
            'executes only that one case','566 fresh/final566','58 previous passes','stored-service and strict product JSON binding',
            'Source API v12 is incomplete','Native011 is unapproved/unexecuted'):
            c.require(marker in profile,'PRECISE_ORIGINAL_CONTROL_START_NFC_POLICY_RECOVERY_AND_OPEN_PRODUCT_PROFILE')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-review-selector-control-core-v1.md'in q.text(name),'RELATED_INSPECTION_STYLE_AND_NAVIGATION_LINK_CONTROL_CORE_WITHOUT_WIDENING_LEGACY_SCHEMAS')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 선택 범위 서식 제품 v7',1)[0]
        for marker in('총 고유59개(신규12+영향기존47)','566fresh/final566','현재 저장 서비스·엄격한 제품 JSON/next 연결',
            '74.719초','2.016초','0.02초','1.922초','11.64%','40.4980%','1.7969%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_CONTROL_CORE_AND_UNCHANGED_NATIVE_QUEUE_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_CONTROL_CORE_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_distinct_core_cases=59,new_core_cases=12,affected_cases=47,
            retained_passes=58,recovery_executed_cases=1,entire_566_input_set_reaudited=False,tests_reexecuted=False,
            stored_product_or_native_qualified=False,next_work='Current_stored_service_and_strict_product_binding_of_exact_review_selector_controls')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_CONTROLS_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_CONTROLS_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
