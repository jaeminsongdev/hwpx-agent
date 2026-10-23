"""Scoped v5 discovery/search code,47-case result and document closure, no test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_scope_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-source-scope-product-sync093.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-scope-product-request-v5.md','protocol/migrations/p09-source-index-scope-selector-v1.md')
RETAINED={base.OLD_SEARCH,base.OLD_NAV,base.base.TEST,base.base.CORE,
    'crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/hwpx-package/src/document_import/search/scope.rs','crates/hwpx-package/src/document_import/search/extract.rs',
    'crates/hwpx-package/src/document_import/search/normalization.rs','crates/hwpx-package/src/document_import/search/reviews.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/structure.rs',
    'tools/p09/run_source_scope_product_components.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SCOPE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_SCOPE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);old_result=q.json(base.base.OUTPUT);recovery=q.json(base.prior.OUTPUT)
        for name,digest in ((base.OUTPUT,'98214dc9224d34ad162616ea8a8184078332147401c2574e5e8cad8177f33c7e'),
            (base.base.OUTPUT,'f20ba266c903118cbaac7e74f6dfd4747a0b007621be2ca617601f4bd5c08f95'),
            (base.prior.OUTPUT,'12855c79ece143d3b4435a2258ce494c565d9485ae7a4bd35ba5cd8517339bfd')):
            c.require(q.snapshots[name]['sha256']==digest,'EXACT_V5_PRODUCT_PREVIOUS_FIFTY_AND_WARNING_FREE_CLOSURE_RESULTS')
        c.require(passed['state']=='PASS_SCOPE_INVENTORY_FOUR_CORE_TEN_PRODUCT_THIRTY_THREE_AFFECTED_NOT_FULL_SELECTOR_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==522 and passed['total_executed_cases']==47
            and passed['new_core_cases']==4 and passed['new_product_cases']==10 and passed['affected_cases']==33,'EXACT_FORTY_SEVEN_CURRENT_CASE_INPUT_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in old_result['source_pins']};recovered={p['path']:p for p in recovery['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_INVENTORY_V5_BOUNDARY_SERVICE_AND_TEST_INPUTS_MATCH_PASS')
        base.inverse(q,old,recovered)
        groups=(base.test_names(q,base.CORE_TEST),base.test_names(q,base.TEST,'actual_import::source_scope_product::'),
            base.test_names(q,base.OLD_SEARCH,'actual_import::source_search::'),base.test_names(q,base.OLD_NAV,'actual_import::source_search_navigation::'))
        c.require(tuple(map(len,groups))==(4,10,26,7)and len(passed['steps'])==2,'EXACT_FOUR_TEN_TWENTY_SIX_SEVEN_CURRENT_CASE_IDENTITIES')
        warnings=['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "source_scope_product") generated 1 warning']
        for step,expected,diagnostics in zip(passed['steps'],(groups[0],set().union(*groups[1:])),([],warnings),strict=True):
            c.require(step['exit_code']==0 and len(step['tests'])==len(expected)and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['diagnostics']==diagnostics and step['panic_locations']==[],'ALL_FORTY_SEVEN_PASS_ONLY_PREEXISTING_FIXTURE_WARNING')
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
                and limits['verified']and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
                'BOTH_OWNED_JOBS_TERMINAL_ORIGINAL_RESOURCE_LIMITS')
        c.require(passed['original_search_authorization_finish_and_final_head_bodies_preserved']and passed['selector_revision_bound_to_requested_current_source_and_head']
            and passed['descriptors_without_raw_text_from_one_operation_local_index']and passed['retained_verify_does_not_rebuild_inventory_or_search']
            and passed['legacy_v1_v4_parsers_and_navigation_preserved']and not passed['previous_fifty_scope_cases_reexecuted']
            and not passed['idempotency_claim_or_cas_or_dispatcher_added']and not passed['review_policy_editing_or_native_flow_scope_qualified'],
            'CURRENT_SOURCE_DISCOVERY_NOT_FULL_REVIEW_EDITING_OR_EXECUTION')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in ('47pass·522fresh/final522','inventory core4+신규제품10+영향검색26/이동7','별도 Form/graph import 없이',
            'review 정책과 문자열 치환에 같은 선택 창','현재 stored revision/head/source','범위·인증된 조회/v5 revision 결속 통과'):
            c.require(marker in progress,'PROGRESS_CURRENT_V5_BOUNDARY_AND_REVIEW_WINDOW_REMAINDER')
        profile=q.text(DOCS[2])
        for marker in ('product-source-search-request/v5','selector.revision_id is mandatory','before any source read',
            'scope_inventory has no query/options','not a new registered capability','source handles','47 total,522 fresh/final522',
            'V5 cursor navigation is not','No unchecked accessor','Native011 unapproved/unexecuted','P09/A12/A13 OPEN'):
            c.require(marker in profile,'PRECISE_V5_SCHEMA_DISCOVERY_REVISION_AND_OPEN_NATIVE_BOUNDARY')
        c.require('p09-source-scope-product-request-v5.md'in q.text(DOCS[3]),'SOURCE_SELECTOR_PROFILE_LINKS_SEPARATE_CURRENT_V5_PRODUCT')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 ACTIVE 최신 source 범위',1)[0]
        for marker in ('47pass·522fresh/final522','57.735초','33.093초','70.10%','26.7706%','5.0981%',
            'V5 cursor는 아직 노출하지 않으며','공식158/249','잔여91','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_V5_COUNTS_RESOURCES_AND_UNCHANGED_NATIVE_SCOPE')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SCOPE_V5_CODE_DOCUMENT_SYNC_FORTY_SEVEN_CASES_NOT_FULL_SELECTOR_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=47,new_core_cases=4,new_product_cases=10,affected_cases=33,
            original_legacy_scope_source_authorization_and_navigation_preserved=True,entire_522_input_set_reaudited=False,
            resource_policy_unchanged=True,full_selector_native_cas_execution_publication_qualified=False,
            next_work='Explicit_review_policy_and_literal_replacement_use_same_validated_selector_windows')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SCOPE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SCOPE_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
