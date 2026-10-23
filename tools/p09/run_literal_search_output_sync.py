"""Actual literal candidate code/result/docs closure; no test, Cargo or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_search_output_components as base
shared,c,a=base.shared,base.c,base.a
PASSED=base.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-literal-search-output-sync069.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-search-scalar-patch-prerequisite-v1.md','protocol/migrations/p09-source-literal-replacement-output-v1.md')
RETAINED={'crates/hwpx-package/src/document_import/search/extract.rs','crates/hwpx-package/src/document_import/search/scope.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs','crates/hwpx-package/src/patch.rs',
    'crates/hwpx-package/src/patch/leaf_scalar_ranges.rs','crates/hwpx-package/src/writer.rs','crates/product-cli/src/form_stored_provider.rs',
    base.scalar.base.HEADER,'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_SEARCH_OUTPUT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed,failed,prior=q.json(PASSED),q.json(base.FAILED),q.json(base.PRIOR)
        for name,sha in ((PASSED,'86542bf1921e5a80ef75202b3cfa1009b0eb99a6036475c6d72386d1ce9735fd'),
            (base.FAILED,'d2c2cc523c2aca5bb33053068bd7c76bcb182aead3d9db61f7008ba9bae4a79d'),
            (base.PRIOR,'e0ec9bcd90899043bd2fedc3fcef2466430f18d2dbf31027d9ed1168a45af715')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_LITERAL_PASS_FAILURE_AND_SCALAR_BASELINE')
        c.require(passed['state']=='PASS_ACTUAL_LITERAL_SEARCH_OUTPUT_ONE_CORE_NINE_RETAINED_SIX_STORED_NOT_FULL_PROTECTION_PRODUCT_NATIVE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==472 and passed['cleanup']and passed['total_executed_cases']==7
            and passed['prior_core_passes_preserved']==9 and passed['distinct_validated_cases']==16,'EXACT_SEVEN_CURRENT_NINE_RETAINED_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        sources={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        original={n for n in old if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(sources-original==base.NEW,'EXACT_FIVE_NEW_LITERAL_SOURCE_AND_TEST_FILES')
        for name in sources-base.NEW-base.CHANGED:c.require(tested[name]==old[name],'OTHER_SOURCE_TEST_AND_HEADER_INPUTS_RETAINED')
        lower='crates/hwpx-package/src/document_import/search/replacement.rs'
        for name in sources-{base.TEST,base.TEXT_FLOW,lower}:c.require(tested[name]==initial[name],'NO_OTHER_PRODUCTION_OR_TEST_CHANGE_DURING_RECOVERY')
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_LITERAL_AND_RETAINED_SHARED_INPUTS_MATCH_PASS')
        base.inverse(q,old)
        text=q.text(lower);addition='        crate::text_flow::validate_text(replacement).map_err(|_|E::Value)?;\n'
        c.require(text.count(addition)==1,'ONE_ORIGINAL_TYPED_TEXT_POLICY_PRECONDITION');base.base.inverse(text.replace(addition,''),initial[lower],'ORIGINAL_LOWERING_BODY_UNCHANGED_AFTER_NEW_INPUT_REJECTION')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        product={'actual_import::literal_search_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.PRODUCT))}
        c.require(len(core)==10 and len(product)==6 and len(passed['steps'])==2 and len(failed['steps'])==1,'EXACT_SIXTEEN_LITERAL_CASE_IDENTITIES')
        statuses=dict(failed['steps'][0]['tests']);c.require(set(statuses)==(core-{base.RECOVERED})|{base.OLD_FAILED}
            and statuses[base.OLD_FAILED]=='FAILED'and sum(s=='ok'for s in statuses.values())==9 and failed['cleanup'],'ORIGINAL_NINE_PASSES_AND_CR_BODY_IMPORT_FAILURE_PRESERVED')
        for step,expected in zip(passed['steps'],({base.RECOVERED},product),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['exit_code']==0 and step['panic_locations']==[],'EXACT_ONE_RECOVERED_AND_SIX_STORED_PASSES')
        c.require(passed['steps'][0]['diagnostics']==[] and passed['steps'][1]['diagnostics']==[
            'warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning'],
            'ONE_EXISTING_DISCLOSED_FIXTURE_HELPER_WARNING_ONLY')
        for step in (*failed['steps'],*passed['steps']):
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_LITERAL_JOBS_TERMINAL_EMPTY_CLOSED')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('고유16개','472 fresh/final472','기존9개 본문','필드 cached text','제어 문자','다음은 이 실제 치환 후보'):
            c.require(marker in progress,'LITERAL_PROGRESS_QUALIFIED_CANDIDATE_AND_REMAINING_REQUEST_BOUNDARY')
        profile=q.text(DOCS[3])
        for marker in ('There is','no service JSON/schema migration','field_cached_content_edit_qualified=false',
            'full_protection_native_or_execution_authority=false','for16 distinct validated cases','472 fresh/final472',
            'P09/A12/A13 OPEN','Native011 unapproved/unexecuted','P10 not started'):
            c.require(marker in profile,'LITERAL_OUTPUT_SOURCE_ACCESS_AND_UNQUALIFIED_FULL_PRODUCT_BOUNDARIES')
        c.require('p09-source-literal-replacement-output-v1.md'in q.text(DOCS[2]),'SCALAR_PREREQUISITE_AND_ACTUAL_CANDIDATE_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 원본 범위 편집 기반',1)[0]
        for marker in ('2026-10-20','고유16개','472fresh/final472','36.74%','30.8222%','5.0373%','미사용 경고1종',
            '잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작','엄격한 제품 요청'):
            c.require(marker in state,'CURRENT_LITERAL_RESULT_RESOURCES_WARNING_AND_UNCHANGED_GATE')
        runner='tools/p09/run_literal_search_output_components.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_LITERAL_RECOVERY_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_LITERAL_OUTPUT_CODE_DOCUMENT_SYNC_SIXTEEN_DISTINCT_CASES_NOT_FULL_SEARCH_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=7,prior_core_passes_preserved=9,
            original_search_provider_reader_protection_bodies_inverse_verified=True,only_typed_policy_precondition_added_during_recovery=True,
            existing_fixture_helper_warning_disclosed=True,entire_472_inputs_reaudited=False,full_literal_search_product_or_native_qualified=False,
            next_work='Strict_literal_replacement_product_JSON_original_head_key_plan_scope_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
