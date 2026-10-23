"""Scoped29-case regex product code/document closure; no Cargo or completed core/product replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-regex-product-sync117.v1.json'
PROFILE='protocol/migrations/p09-regex-replacement-product-request-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-selector-regex-replacement-v1.md','protocol/migrations/p09-review-selector-product-requests.md',
    'protocol/migrations/p09-source-literal-text-atom-output-v2.md','protocol/migrations/p09-source-review-literal-output-v3.md'}
RETAINED={base.OLD,'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/tests/support/stored_source_fixture.rs','crates/hwpx-package/src/document_import/forms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/regex.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/regex/template.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs','crates/hwpx-package/src/document_import/search/captures.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','tools/p09/run_regex_product_components.py','tools/p09/run_regex_replacement_focused.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='3a778f5ec5f29813a07755065b51f4f61935a163caf7ea3a35a3a7b80659608a'
            and passed['state']=='PASS_REGEX_PRODUCT_THIRTEEN_NEW_SIXTEEN_AFFECTED_NOT_ZERO_WIDTH_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==586 and passed['total_executed_cases']==29 and passed['new_product_cases']==13 and passed['affected_cases']==16,
            'EXACT_TWENTY_NINE_PRODUCT_CASES_AND_FULL_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='478e21869b593aeefd331fc7d115a6d214151e6fdac901a39bec968751ca86eb'
            and previous['cleanup']and previous['total_distinct_core_cases']==89,'EXACT_PRIOR_REGEX_CORE_BASELINE_NOT_REPLAYED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_REGEX_PRODUCT_AUTH_CORE_WRITER_AND_TESTS_MATCH_PASS')
        base.inverse(q,old);expected=base.expected(q);c.require(len(passed['steps'])==1,'ONE_ACTUAL_PRODUCT_TEST_BINARY');step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==29 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['diagnostics']==[]and step['panic_locations']==[]and step['safe_error_variants']==[],'ALL_PRODUCT_IDENTITIES_PASS_WITHOUT_IGNORES_FILTERS_OR_DIAGNOSTICS')
        job=step['owned_job'];limits=job['limits_readback']
        c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
            'OWNED_JOB_TERMINAL_WITH_ONE_CPU2_ORIGINAL_HARD_CAP_AND_PRIORITY')
        c.require(not passed['zero_width_native_or_full_product_qualification_added']and not passed['previous_eighty_nine_core_and_unaffected_suites_reexecuted']
            and passed['original_literal_root_and_strict_v4_selector_inverse_verified']and passed['one_call_local_whole_proof_capture_compiler_and_owned_transfer_without_reimport']
            and passed['current_output_does_not_repeat_query_capture_or_lowering']and passed['template_and_expansion_bindings_kept_distinct'],
            'CURRENT_REGEX_SOURCE_DELIVERY_NOT_ZERO_WIDTH_OR_FULL_EXECUTION')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');profile=q.text(PROFILE)
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('29pass·586fresh/final586','NFC capture/템플릿·4종 범위/review 정책·현재 저장/regex JSON 통과',
            '빈 일치 삽입·전체 계약 미완료','이전core89·무관한suite·공식249 대기열은 반복하지 않았다','다음은 빈 일치의 정확한 원본 삽입 경계'):
            c.require(marker in progress,'CURRENT_REGEX_STORED_PRODUCT_COUNTS_AND_REMAINING_ZERO_WIDTH_BOUNDARY')
        for marker in('product-regex-replacement-request/v1','regex=true','Template SHA/bytes are distinct','before source reads',
            'original v4 selector16 KiB unique JSON/object parser','without cloning','not rerun','29 total','586 fresh/final586',
            'no diagnostics','RouteUnqualified','Exact zero-width source insertion is next','unapproved/unexecuted'):
            c.require(marker in profile,'PRECISE_REGEX_SCHEMA_CURRENT_ACCESS_OWNERSHIP_BINDINGS_AND_OPEN_NATIVE_CONTRACT')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-regex-replacement-product-request-v1.md'in q.text(name),'RELATED_CORE_AND_LITERAL_PROFILES_LINK_ADDITIVE_REGEX_PRODUCT')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 정규식 치환 core',1)[0]
        for marker in('29pass·586fresh/final586','product-regex-replacement-request/v1','109.250초','34.140초','2.46초','32.062초',
            '29.55%','35.8753%','5.1831%','affinity4 한 bit','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_REGEX_PRODUCT_RESOURCES_AND_UNCHANGED_QUEUE_PHASE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_PRODUCT_CODE_DOCUMENT_SYNC_NOT_ZERO_WIDTH_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_product_cases=29,new_product_cases=13,affected_cases=16,entire_586_input_set_reaudited=False,tests_reexecuted=False,
            next_work='Exact_zero_width_source_insertions_then_remaining_style_control_conversion_and_full_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
