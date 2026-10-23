"""Scoped strict-v2 product code/result/document closure; no test or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_text_atom_product_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-literal-text-atom-product-sync080.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-literal-replacement-product-request-v2.md','protocol/migrations/p09-literal-replacement-product-request-v1.md',
    'protocol/migrations/p09-source-literal-text-atom-output-v2.md','protocol/migrations/p09-source-text-atom-patch-v1.md')
RETAINED={'crates/hwpx-package/src/document_import/search/replacement.rs',
    'crates/hwpx-package/src/document_import/search/replacement/output.rs','crates/hwpx-package/src/document_import/search/replacement/atoms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs','crates/hwpx-package/src/document_import/forms.rs',
    'crates/hwpx-package/src/patch/text_atom_ranges.rs','crates/hwpx-package/src/text_flow/source_text_span.rs',
    'crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request.rs','crates/product-cli/src/form_product_request/stored_source_search.rs',
    'crates/hwpx-package/tests/document_import_search_atom_replacement.rs','crates/hwpx-package/tests/document_import_search_replacement.rs',
    base.V1_TEST,base.prior.base.TEST}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_ATOM_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_TEXT_ATOM_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed,prior=q.json(base.OUTPUT),q.json(base.PRIOR)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='1fcfe918bac8737dc57a41b5a2246b3cc457d2504941e828a15f6c7618f63b4c'
            and q.snapshots[base.PRIOR]['sha256']=='d824977e51989932c03e16d591f11bd90a40928a713c4cf69fab62b3f58f75c5','EXACT_STRICT_V2_PRODUCT_AND_PREVIOUS_STORED_PASS_RESULTS')
        c.require(passed['state']=='PASS_STRICT_V2_LITERAL_PRODUCT_TEN_NEW_FIFTEEN_AFFECTED_CORE_RETAINED_NOT_FULL_SEARCH_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==492 and passed['total_executed_cases']==25
            and passed['new_product_cases']==10 and passed['affected_cases']==15,'EXACT_TEN_NEW_FIFTEEN_AFFECTED_PRODUCT_INPUT_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_V2_PRODUCT_OWNER_PARSER_AND_RETAINED_CORE_INPUTS_MATCH_PASS')
        for name in RETAINED:c.require(tested[name]==old[name],'CORE_PROOF_READER_V1_OWNER_PROVIDER_AND_EXISTING_TESTS_EXACTLY_RETAINED')
        base.inverse(q,old)
        def tests(path,prefix):return {prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}
        new=tests(base.TEST,'actual_import::literal_text_atom_product::')
        v1=tests(base.V1_TEST,'actual_import::literal_replacement_product::')
        borrowed=tests(base.prior.base.TEST,'actual_import::literal_text_atom_output::')
        c.require((len(new),len(v1),len(borrowed))==(10,9,6),'EXACT_TWENTY_FIVE_CURRENT_PRODUCT_TEST_IDENTITIES')
        warning=['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning']
        for step,expected in zip(passed['steps'],(new,v1|borrowed),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['exit_code']==0 and step['diagnostics']==warning and step['panic_locations']==[],'ALL_TWENTY_FIVE_PASS_WITH_ONLY_PREEXISTING_FIXTURE_HELPER_WARNING')
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_V2_PRODUCT_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(passed['source_ownership_transferred_without_clone_or_reimport']and passed['v1_v2_schema_and_semantic_boundaries_separate']
            and passed['invalid_request_rejected_before_artifact_reads']and not passed['idempotency_key_claimed']
            and not passed['command_line_or_server_dispatcher_added']and not passed['core_scalar_and_unrelated_stored_tests_reexecuted'],
            'PRODUCT_PREPARATION_NOT_CLONE_QUERY_REPLAY_DURABLE_CLAIM_OR_DISPATCHER')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in ('25pass·492 fresh/final492','영향 v1제품9/v2저장6','원본을 move','기존 v1 외부 계약과 plain-only 의미',
            '엄격한 제품 JSON 통과, 확장 본문/전체 transaction 미완료','숨은 설명/MEMO의 원본 본문과 필드 캐시·보호 경계'):
            c.require(marker in progress,'PROGRESS_V2_PRODUCT_COUNTS_OWNERSHIP_AND_PENDING_REVIEW_BODY_WORK')
        profile=q.text(DOCS[2])
        for marker in ('product-literal-replacement-request/v2','private schema parameter','All25 pass,492 fresh/final492',
            'not described as only one original import','Existing v1 remains plain-only','idempotency_key_claimed',
            'No CLI/server dispatcher','Source API v12','P09/A12/A13 OPEN','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'STRICT_V2_SCHEMA_OWNERSHIP_PROOF_BOUNDARIES_AND_OPEN_GATE')
        for name in DOCS[3:]:c.require('p09-literal-replacement-product-request-v2.md'in q.text(name),'PRIOR_PROFILES_LINK_EXPLICIT_V2_NOT_WIDEN_V1')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 혼합 v2 후보와 저장 연결',1)[0]
        for marker in ('신규 v2 제품10','25pass·492fresh/final492','140.359초','10.797초','33.16%','27.2722%','3.0762%',
            '소유권 전달 때문에 추가하는 reimport','기존 필드 캐시/제어 편집 거부를 일괄 해제하지 않는다',
            '공식158/249','잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_V2_PRODUCT_EVIDENCE_RESOURCES_AND_UNCHANGED_NATIVE_BOUNDARY')
        runner='tools/p09/run_literal_text_atom_product_components.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_V2_PRODUCT_RUNNER_SOURCE_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_V2_LITERAL_PRODUCT_CODE_DOCUMENT_SYNC_TWENTY_FIVE_CASES_NOT_FULL_SEARCH_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=25,new_product_cases=10,affected_cases=15,
            original_v1_parser_scope_and_v2_service_methods_preserved=True,entire_492_input_set_reaudited=False,
            source_ownership_handoff_without_clone_or_extra_import=True,resource_policy_unchanged=True,
            full_search_native_cas_execution_publication_qualified=False,
            next_work='Extended_review_body_literal_replacement_with_explicit_hidden_and_MEMO_policy')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_ATOM_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_V2_PRODUCT_SYNC_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
