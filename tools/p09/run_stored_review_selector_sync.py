"""Scoped52-core/61-stored evidence and code/document closure, no Cargo or test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_review_selector_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-review-selector-sync098.v1.json'
PROFILE='protocol/migrations/p09-stored-review-selector-candidates-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-index-scope-selector-v1.md','protocol/migrations/p09-source-scope-product-request-v5.md',
    'protocol/migrations/p09-source-review-literal-output-v3.md'}
RETAINED={'crates/product-cli/tests/support/stored_source_fixture.rs','crates/product-cli/src/form_stored_provider.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_stored_provider/actual_import/source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review/product.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/extract.rs','crates/hwpx-package/src/document_import/search/normalization.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms.rs','crates/hwpx-package/tests/review_selector_bundle.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_REVIEW_SELECTOR_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVIEW_SELECTOR_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);core=q.json(base.prior.OUTPUT)
        for name,digest in((base.OUTPUT,'7bfd4197c6ddab3ce115fc208da5fca5063a8762f9401e8ee3a8d6ede1f11740'),
            (base.prior.OUTPUT,'cab7ad4d39fcba40f3ddb492d82347a2a4549d6bded1c31479a89df7d4f56f32')):
            c.require(q.snapshots[name]['sha256']==digest,'EXACT_CURRENT_CORE_AND_STORED_PASS_RECORDS')
        c.require(passed['state']=='PASS_STORED_REVIEW_SELECTOR_TWELVE_NEW_FORTY_NINE_AFFECTED_NOT_PRODUCT_JSON_NATIVE_OR_GATE'
            and passed['cleanup']and passed['total_executed_cases']==61 and passed['new_stored_cases']==12 and passed['affected_cases']==49
            and passed['fresh_inputs']==passed['final_fresh_hashes']==536,'EXACT_SIXTY_ONE_STORED_CASES_AND_INPUT_CLOSURE')
        c.require(core['state']=='PASS_REVIEW_SELECTOR_RECOVERY_SIXTEEN_NEW_THIRTY_SIX_AFFECTED_NOT_STORED_JSON_NATIVE_OR_GATE'
            and core['cleanup']and core['total_executed_cases']==52 and core['fresh_inputs']==core['final_fresh_hashes']==532,'EXACT_FIFTY_TWO_CORE_CASES_AND_INPUT_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']};previous={p['path']:p for p in core['source_pins']}
        old_tests={'crates/product-cli/tests/form_stored_provider/actual_import/'+name+'.rs'for name in base.MODULES[1:]}
        source=base.prior.base
        core_tests={'crates/hwpx-package/tests/'+name+'.rs'for name in source.TESTS+source.OLD}
        pins=base.NEW|base.CHANGED|source.NEW|source.CHANGED|RETAINED|old_tests|core_tests|{'tools/p09/run_stored_review_selector_components.py'}
        for name in sorted(pins):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_CODE_AND_DECLARED_TEST_BODIES_MATCH_STORED_PASS')
        base.inverse(q,previous);expected=base.expected(q)
        c.require(len(passed['steps'])==1 and len(core['steps'])==1,'ONE_BINARY_PER_ACTUAL_RUN')
        step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==61 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_SIXTY_ONE_EXPECTED_TESTS_PASS_WITH_NO_IGNORES_OR_FILTERS')
        c.require(step['diagnostics']==['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "review_selector_stored") generated 1 warning'],
            'ONLY_KNOWN_UNUSED_FIXTURE_HELPER_WARNING')
        core_expected=set()
        for target,module in zip(source.TESTS+source.OLD,base.prior.prior.MODULES,strict=True):
            core_expected.update(module+'::'+name for name in source.test_names(q,target))
        core_step=core['steps'][0]
        c.require(core_step['exit_code']==0 and len(core_step['tests'])==52 and {n for n,s in core_step['tests']}==core_expected
            and all(s=='ok'for n,s in core_step['tests']),'ALL_FIFTY_TWO_RETAINED_CORE_TEST_IDENTITIES')
        for step in(passed['steps'][0],core_step):
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
                and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
                'BOTH_JOBS_TERMINAL_AND_ORIGINAL_RESOURCE_PROTECTION_READBACK')
        c.require(not passed['previous_fifty_two_core_cases_reexecuted']and not passed['strict_product_json_or_native_qualified']
            and passed['original_search_finish_fresh_authorization_and_final_head_bodies_preserved']and passed['original_v3_literal_bodies_and_owned_transfer_preserved']
            and passed['retained_verify_does_not_repeat_query_lowering_or_review_import'],'STORED_BOUNDARY_WITHOUT_REPLAY_OR_NEW_JSON_AUTHORITY')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('신규16+영향36=52pass·532fresh/final532','신규12+영향49=61pass·536fresh/final536','다음은 엄격한 제품 JSON 연결',
            'review 범위 JSON/전체 계약 미완료','selector JSON/전체 계약/transaction 미완료'):
            c.require(marker in progress,'CURRENT_SEARCH_PROGRESS_DISTINGUISHES_CORE_STORED_JSON_AND_FULL_CONTRACT')
        profile=q.text(PROFILE)
        for marker in('actual graph/source anchors','before the explicit include_hidden_explanations','hwpx-agent.stored-source-search/v6',
            'not a product-source-search-request/v6 schema','hwpx-agent.stored-selector-literal-candidate/v1','There is no source clone',
            '52 total,532 fresh/final532','61 total,536 fresh/final536','Strict review-selector search','Native011 is unapproved/unexecuted'):
            c.require(marker in profile,'PRECISE_SOURCE_WINDOW_STORED_AND_PENDING_PRODUCT_BOUNDARIES')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-stored-review-selector-candidates-v1.md'in q.text(name),'RELATED_PROFILES_LINK_CURRENT_STORED_BOUNDARY')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 인증된 범위 요청',1)[0]
        for marker in('52pass·532fresh/final532','61pass·536fresh/final536','엄격한 제품 JSON 요청 연결','269.953초','196.813초','25.18초',
            '26.70%','35.6382%','5.1055%','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_STATE_COUNTS_RESOURCES_AND_UNCHANGED_PHASE_NATIVE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_SELECTOR_CORE_STORED_CODE_DOCUMENT_SYNC_NOT_STRICT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,retained_core_cases=52,current_stored_cases=61,
            entire_536_input_set_reaudited=False,tests_reexecuted=False,strict_product_json_or_native_qualified=False,
            next_work='Strict_review_scope_search_and_selector_literal_product_JSON_requests')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVIEW_SELECTOR_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORED_REVIEW_SELECTOR_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
