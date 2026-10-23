"""Scoped v3 product code/result/document closure; no Cargo, Native or queue replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_literal_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-review-literal-product-sync089.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-review-literal-product-request-v3.md','protocol/migrations/p09-source-review-literal-output-v3.md',
    'protocol/migrations/p09-literal-replacement-product-request-v2.md','protocol/migrations/p09-source-literal-text-atom-output-v2.md')
RETAINED={base.V1,base.V2,base.prior.base.TEST,base.prior.FIXTURE,
    'crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs',
    'crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/product.rs',
    'crates/hwpx-package/src/document_import/search/reviews.rs',
    'crates/hwpx-package/src/document_import/structure/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs',
    'crates/hwpx-package/tests/document_import_search_review_replacement.rs',
    'crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_LITERAL_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_LITERAL_PRODUCT_SYNC',actual_Cargo_or_tests=False,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed,previous=q.json(base.OUTPUT),q.json(base.PRIOR)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='3905c914aea2a4f55b241675b7fa120615a0530b619c9763979b0dc80cd392c4'
            and q.snapshots[base.PRIOR]['sha256']=='2d5c00db901cdfba93a072f5a42132ce195075f1fc354dce2fd7ca45a5ef18ed','EXACT_V3_PRODUCT_AND_PREVIOUS_BORROWED_PASS_RESULTS')
        c.require(passed['state']=='PASS_STRICT_V3_REVIEW_LITERAL_PRODUCT_TEN_NEW_TWENTY_FIVE_AFFECTED_NOT_FULL_SEARCH_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==508
            and passed['total_executed_cases']==35 and passed['new_product_cases']==10 and passed['affected_cases']==25,'EXACT_THIRTY_FIVE_PASS_INPUT_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_PRODUCT_OWNER_PARSER_CORE_AND_AFFECTED_TESTS_MATCH_PASS')
        for name in RETAINED:c.require(tested[name]==old[name],'CORE_PROVIDER_SHARED_FIXTURE_AND_OLD_TEST_BODIES_RETAINED')
        base.inverse(q,old)
        groups=(base.test_names(q,base.TEST,'review_literal_product'),base.test_names(q,base.V1,'literal_replacement_product'),
            base.test_names(q,base.V2,'literal_text_atom_product'),base.test_names(q,base.prior.base.TEST,'review_literal_output'))
        c.require(tuple(map(len,groups))==(10,9,10,6),'EXACT_CURRENT_TEST_IDENTITIES_NEW_TEN_AFFECTED_TWENTY_FIVE')
        expected=set().union(*groups);c.require(len(passed['steps'])==1,'ONE_SERIAL_FOCUSED_PRODUCT_JOB')
        step=passed['steps'][0];c.require(step['exit_code']==0 and step['diagnostics']==[] and step['panic_locations']==[]
            and len(step['tests'])==35 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests']),
            'ALL_THIRTY_FIVE_PASS_NO_IGNORED_OR_DIAGNOSTICS')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0 and limits['verified']and limits['affinity_mask']==1
            and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'ORIGINAL_ONE_CORE_JOB_RESOURCE_LIMITS_AND_TERMINAL_CLEANUP')
        c.require(passed['original_v1_v2_parser_and_canonical_provider_scope_bodies_inverse_verified']
            and passed['original_v3_current_access_writer_and_final_head_bodies_unchanged']
            and passed['source_ownership_transferred_without_clone_or_reimport']and passed['explicit_both_policy_booleans_and_version_bound_digests']
            and not passed['idempotency_key_claimed']and not passed['core_scalar_and_unrelated_stored_tests_reexecuted']
            and not passed['command_line_or_server_dispatcher_added'],'SOURCE_POLICY_OWNERSHIP_AND_PREPARATION_NOT_FULL_EXECUTION')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_SEARCH_CONTRACT_ROWS_PRESERVED')
        for marker in ('35pass·508fresh/final508','v1/v2제품19/v3저장6','16KiB','Borrowed/Owned','전체 범위/transaction 미완료',
            'document/section/selection/node_set','revision_id·section_ids·range'):
            c.require(marker in progress,'PROGRESS_PRODUCT_VERIFICATION_AND_REMAINING_FULL_SCOPE_CONTRACT')
        profile=q.text(DOCS[2])
        for marker in ('product-literal-replacement-request/v3','Both Booleans are mandatory','before source reads',
            'ownership-driven reimport','35 passes,508 fresh/final508','Core32','No unchecked accessor',
            'document/section/selection/node_set','P09/A12/A13 OPEN','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'V3_PRODUCT_PROFILE_EXACT_POLICY_COUNTS_OWNERSHIP_AND_OPEN_GATE')
        for name in DOCS[3:]:c.require('p09-review-literal-product-request-v3.md'in q.text(name),'PREVIOUS_PROFILES_LINK_SEPARATE_QUALIFIED_V3_PREPARATION')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 ACTIVE 최신 review 치환',1)[0]
        for marker in ('신규 v3 제품10','35pass·508fresh/final508','36.234초','46.88%','28.9834%','2.1868%',
            '전체 SearchScopeSelector','공식158/249','잔여91','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_V3_PRODUCT_EVIDENCE_RESOURCES_AND_NATIVE_REMAINDER')
        runner='tools/p09/run_review_literal_product_components.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_COMPONENT_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_V3_REVIEW_LITERAL_PRODUCT_CODE_DOCUMENT_SYNC_THIRTY_FIVE_CASES_NOT_FULL_SEARCH_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=35,new_product_cases=10,affected_cases=25,
            original_v1_v2_parser_and_v3_current_access_preserved=True,entire_508_input_set_reaudited=False,
            source_ownership_handoff_without_clone_or_extra_import=True,resource_policy_unchanged=True,
            full_search_native_cas_execution_publication_qualified=False,next_work='Full_SearchScopeSelector_document_section_selection_node_set')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_LITERAL_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_V3_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
