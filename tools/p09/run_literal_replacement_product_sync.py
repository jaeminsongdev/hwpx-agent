"""Strict product source/result/docs closure, no Cargo, test, queue or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_replacement_product_components as base
shared,c,a=base.shared,base.c,base.a
PASSED=base.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-literal-replacement-product-sync071.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-literal-replacement-output-v1.md','protocol/migrations/p09-literal-replacement-product-request-v1.md')
RETAINED={'crates/hwpx-package/src/document_import/search/replacement/output.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/extract.rs','crates/hwpx-package/src/document_import/search/scope.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/patch/leaf_scalar_ranges.rs','crates/hwpx-package/src/text_flow.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs','crates/product-cli/src/form_stored_provider.rs',
    base.prior.TEST,base.prior.PRODUCT,base.prior.base.HEADER,'crates/hwpx-package/tests/support/search_definition_fixture.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_REPLACEMENT_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed,prior=q.json(PASSED),q.json(base.PRIOR)
        c.require(q.snapshots[PASSED]['sha256']=='cacd9b8ef647792299c661d3a5f107fa9b5e516b081e8485c653f4e6900449df'
            and q.snapshots[base.PRIOR]['sha256']=='86542bf1921e5a80ef75202b3cfa1009b0eb99a6036475c6d72386d1ce9735fd','EXACT_LITERAL_PRODUCT_AND_PREVIOUS_OUTPUT_PASS_RESULTS')
        c.require(passed['state']=='PASS_STRICT_LITERAL_REPLACEMENT_PRODUCT_NINE_NEW_SIX_AFFECTED_CORE_TEN_RETAINED_NOT_FULL_SEARCH_NATIVE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==475 and passed['cleanup']and passed['total_executed_cases']==15
            and not passed['prior_core_cases_reexecuted'],'EXACT_FIFTEEN_CURRENT_AND_CORE_REUSE_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        sources={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        original={n for n in old if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(sources-original==base.NEW,'ONLY_THREE_NEW_STRICT_LITERAL_PRODUCT_FILES')
        for name in sources-base.NEW-base.CHANGED:c.require(tested[name]==old[name],'OTHER_SOURCE_CORE_TEST_AND_HEADER_PINS_RETAINED')
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_LITERAL_PRODUCT_AND_RETAINED_INPUTS_MATCH_PASS')
        base.inverse(q,old)
        product={'actual_import::literal_replacement_product::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.PRODUCT))}
        borrowed={'actual_import::literal_search_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.prior.PRODUCT))}
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.prior.TEST)))
        c.require(len(product)==9 and len(borrowed)==6 and len(core)==10 and len(passed['steps'])==2,'EXACT_NEW_NINE_AFFECTED_SIX_AND_RETAINED_TEN_CASES')
        expected_warning=['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning']
        for step,expected in zip(passed['steps'],(product,borrowed),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['exit_code']==0 and step['panic_locations']==[]and step['diagnostics']==expected_warning,'ALL_FIFTEEN_PASS_WITH_ONLY_EXISTING_DISCLOSED_HELPER_WARNING')
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_LITERAL_PRODUCT_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(prior['cleanup']and prior['distinct_validated_cases']==16 and prior['prior_core_passes_preserved']==9
            and prior['steps'][0]['tests']==[[base.prior.RECOVERED,'ok']],'ORIGINAL_CORE_PASS_REUSE_NOT_RELABELED_AS_CURRENT_EXECUTION')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('15개 PASS','475 fresh/final475','기존 core10개','Borrowed/Owned','fixture 미사용 경고1종','mixed leaf'):
            c.require(marker in progress,'LITERAL_PRODUCT_PROGRESS_CURRENT_REQUEST_REUSE_WARNING_AND_NEXT_BOUNDARY')
        profile=q.text(DOCS[3])
        for marker in ('before original artifact reads','preview_only','idempotency_key_claimed=false',
            'full_search_native_cas_execution_publication_authority=false','15 pass,475 fresh/final475',
            'P09/A12/A13 OPEN','Native011 unapproved/unexecuted','P10 not started'):
            c.require(marker in profile,'STRICT_LITERAL_PRODUCT_INPUT_ACCESS_AND_GATE_BOUNDARIES')
        c.require('p09-literal-replacement-product-request-v1.md'in q.text(DOCS[2]),'ORIGINAL_CANDIDATE_AND_NEW_PRODUCT_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 실제 문자열 치환 후보',1)[0]
        for marker in ('2026-10-20','15개 PASS','475fresh/final475','32.81%','28.5142%','5.0349%','미사용 경고1종',
            '잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작','mixed leaf'):
            c.require(marker in state,'CURRENT_LITERAL_PRODUCT_RESULT_RESOURCES_AND_UNCHANGED_GATE')
        runner='tools/p09/run_literal_replacement_product_components.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_LITERAL_PRODUCT_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_LITERAL_PRODUCT_CODE_DOCUMENT_SYNC_FIFTEEN_CURRENT_TEN_CORE_RETAINED_NOT_FULL_SEARCH_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=15,prior_core_cases_not_reexecuted=10,
            original_core_value_policy_and_stored_access_methods_inverse_verified=True,ownership_handoff_without_clone_or_extra_import=True,
            existing_fixture_helper_warning_disclosed=True,entire_475_inputs_reaudited=False,full_literal_search_product_or_native_qualified=False,
            next_work='Mixed_leaf_text_atom_replacement_preserving_original_tab_and_linebreak_controls')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_PRODUCT_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
