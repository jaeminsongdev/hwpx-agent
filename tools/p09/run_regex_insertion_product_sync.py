"""Selected source/product/document closure for47 products; no tests or full598-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_product_recovery as product
base=product.base
shared,c,a=product.shared,product.c,product.a
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-product-sync125.v1.json'
PROFILE='protocol/migrations/p09-regex-insertion-product-request-v2.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-selector-regex-insertion-v2.md','protocol/migrations/p09-source-selector-regex-replacement-v1.md',
    'protocol/migrations/p09-regex-replacement-product-request-v1.md'}
RETAINED={'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement.rs','crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/review_selector_product.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/product-cli/tests/regex_replacement_product.rs','crates/product-cli/tests/regex_replacement_product/actual_import.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search/replacement/atoms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/regex.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/regex/insertions.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/regex/template.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs','crates/product-cli/src/reference_validation_product/source.rs',
    'tools/p09/run_regex_insertion_product_components.py','tools/p09/run_regex_insertion_product_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py','tools/p09/bounded_process_progress.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.prior.base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(product.OUTPUT);failed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[product.OUTPUT]['sha256']=='7e4e9727580a7c6dbc2ca335b10aa40e7f387990907dd2251816d5a0ddb1f3b9'
            and passed['state']=='PASS_REGEX_INSERTION_PRODUCT_EIGHTEEN_NEW_TWENTY_NINE_AFFECTED_NOT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==598 and passed['total_executed_cases']==47,'EXACT_CURRENT_FORTY_SEVEN_PRODUCT_RESULTS_AND_COMPLETE_INPUT_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='30811ec1f348ca5f03dfc13223c4b9f71dc54cfd24f900391cdedbbf4b4fbae0'
            and failed['error_code']=='live_progress_output_limit'and failed['cleanup']and not passed['output_or_resource_limit_raised'],
            'ORIGINAL_OUTPUT_STOP_UNCONFIRMED_EXECUTION_AND_UNCHANGED_LIMITS_PRESERVED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_CODE_AUTH_PROOF_WRITER_GUARDS_FIXTURES_AND_TESTS_MATCH_PRODUCT_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_PRODUCT_BINARY_NOT_QUEUE_OR_NATIVE');step=passed['steps'][0]
        c.require(step['exit_code']==0 and {n for n,s in step['tests']}==expected and len(step['tests'])==47 and all(s=='ok'for n,s in step['tests'])
            and step['diagnostics']==[]and step['panic_locations']==[]and step['safe_error_variants']==[],'EXACT_FORTY_SEVEN_CASES_NO_IGNORES_FILTERS_OR_DIAGNOSTICS')
        job=step['owned_job'];limits=job['limits_readback'];account=job['last_job_accounting']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and account['active_processes']==0
            and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'ONE_CPU2_ORIGINAL_CAP_PRIORITY_AND_ACTUALLY_TERMINAL_OWNED_JOB')
        c.require(passed['system_CPU_max']==75.2 and round(passed['available_RAM_min_percent'],4)==38.2103 and account['peak_job_private_mib']==691.26
            and account['job_cpu_seconds']==7.312 and step['elapsed_seconds']==8.484,'SYSTEM_CPU_NOT_CONFUSED_WITH_OWNED_JOB_MEASUREMENTS')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('product-regex-replacement-request/v2','insertion_policy=','has no default','before source reads',
            '(v2 schema, policy, complete typed request)','without an ownership-transfer clone or reimport','final head check remains inside the writer callback',
            'does not rerun search','RouteUnqualified','18 new insertion products and29 affected original','47 total, 598 fresh/final598',
            'no diagnostics','85.266 seconds','8.484 seconds','3.79 seconds','7.312 seconds','691.26 MiB','2.1696%','75.2%',
            'whole-system sample','38.2103%','SEARCH-008','unapproved/unexecuted'):
            c.require(marker in flat,'EXACT_V2_POLICY_OWNERSHIP_AUTHORIZATION_COUNTS_RESOURCES_AND_REMAINING_NATIVE_CONTRACT')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and '빈 일치 source v2·현재 저장/엄격한 v2 JSON 통과'in progress
            and 'recovery124는신규18+영향기존29=47pass·598fresh/final598'in progress and '다음은 SEARCH-008 실제 서식 선택·치환·보존 경로다'in progress,
            'ALL_NINETEEN_ROWS_AND_PRECISE_SOURCE_PRODUCT_NEXT_WORK_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-regex-insertion-product-request-v2.md'in q.text(name),'SOURCE_AND_LEGACY_PROFILES_LINK_SEPARATE_V2_PRODUCT_WITHOUT_WIDENING_V1')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 정규식 빈 일치 원본 삽입',1)[0]
        for marker in('47pass·598fresh/final598','product-regex-replacement-request/v2','75.2%','691.26MiB','SEARCH-008',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_PRODUCT_STATE_AND_UNCHANGED_OFFICIAL_QUEUE_GATE_BOUNDARY')
        source=q.text('crates/product-cli/src/reference_validation_product/source.rs');c.require('reference-source-assessment/v12'in source and 'validation_report: None'in source
            and all('UnresolvedReferenceStage::'+n in source for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_SOURCE_API_REMAINS_INCOMPLETE_WITH_FOUR_UNRESOLVED_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_PRODUCT_CODE_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_product_cases=47,new_product_cases=18,affected_product_cases=29,entire_598_input_set_reaudited=False,tests_reexecuted=False,
            next_work='SEARCH_008_actual_source_style_selection_replacement_and_preservation_then_remaining_full_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
