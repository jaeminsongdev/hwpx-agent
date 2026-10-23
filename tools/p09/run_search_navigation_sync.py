"""Navigation source/result/docs closure without test, Cargo, queue or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_navigation_components as base
shared,c,a=base.shared,base.c,base.a
PASSED=base.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-search-navigation-sync060.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-review-text-search-v4.md','protocol/migrations/p09-source-search-navigation-v1.md')
RETAINED={base.base.HEADER,base.base.EXTRACT,'crates/hwpx-package/src/document_import/search/normalization.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/product-cli/src/form_stored_provider.rs',base.base.PRODUCT,
    base.base.TEST,'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/search_review_fixture.rs'}
RETAINED|={'crates/hwpx-package/tests/'+n+'.rs'for n in base.base.RETAINED}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAVIGATION_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_NAVIGATION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed,failed,prior=q.json(PASSED),q.json(base.FAILED),q.json(base.PRIOR)
        for name,sha in ((PASSED,'bc4535b330d9a3a82b948d2080d56988aaf51ad643765e437ec062a2aeeb729a'),
            (base.FAILED,'cc4396db8157b9d0514d73d90db8f963d9fd14321dc8fe55a4b347545b820767'),
            (base.PRIOR,'2e1ca12d71eaead27bf18e42db72072505696813467583e2a0f9349914b3a692')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_NAVIGATION_PASS_FAILURE_AND_PRIOR_RESULTS')
        c.require(passed['state']=='PASS_RETAINED_SEARCH_NAVIGATION_ONE_RECOVERED_NINE_RETAINED_SEVEN_PRODUCT_NOT_NATIVE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==461 and passed['cleanup']and passed['total_executed_cases']==8
            and passed['prior_core_passes_preserved']==9 and passed['only_invalid_response_size_test_expectation_repaired']
            and not passed['production_changed_after_initial_failure'],'EXACT_CURRENT_EIGHT_AND_RETAINED_NINE_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        sources={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        originals={n for n in old if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(sources-originals==base.NEW,'EXACT_FIVE_NEW_NAVIGATION_SOURCE_AND_TEST_FILES')
        for name in sources-base.NEW-base.CHANGED:c.require(tested[name]==old[name],'OTHER_SOURCE_TEST_AND_HEADER_PINS_RETAINED_IN_NAVIGATION_PASS')
        for name in sources-{base.TEST}:c.require(tested[name]==initial[name],'NO_PRODUCTION_OR_OTHER_INPUT_CHANGE_AFTER_INITIAL_FAILURE')
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_NAVIGATION_AND_RETAINED_INPUTS_MATCH_PASS')
        base.inverse(q,old)
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        product={'actual_import::source_search_navigation::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.PRODUCT))}
        c.require(len(core)==10 and len(product)==7 and len(passed['steps'])==2 and len(failed['steps'])==1,'EXACT_SEVENTEEN_CURRENT_NAVIGATION_CASES')
        statuses=dict(failed['steps'][0]['tests']);c.require(set(statuses)==core and statuses[base.RECOVERED]=='FAILED'
            and sum(s=='ok'for s in statuses.values())==9 and failed['cleanup'],'PRESERVED_ORIGINAL_NINE_PASSES_AND_FAILURE')
        for step,expected in zip(passed['steps'],({base.RECOVERED},product),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and not step['panic_locations']and step['exit_code']==0,'EXACT_RECOVERED_ONE_AND_NEW_SEVEN_PASSES')
        c.require(passed['steps'][0]['diagnostics']==[] and passed['steps'][1]['diagnostics']==[
            'warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning'],
            'ONE_DISCLOSED_REUSABLE_FIXTURE_UNUSED_HELPER_WARNING_ONLY')
        for step in (*failed['steps'],*passed['steps']):
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_THREE_NAVIGATION_JOBS_TERMINAL_EMPTY_CLOSED')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('고유17개','461 fresh/final461','기존9개','package 함수 미사용 경고1종','끝에서 wrap=false','다음은 SEARCH-006'):
            c.require(marker in progress,'NAVIGATION_PROGRESS_REUSE_WARNING_AND_NEXT_BOUNDARY')
        profile=q.text(DOCS[3])
        for marker in ('unsigned selection coordinates','without rerunning','current source or service authorization','total_matches',
            'eight pass with461 fresh/final461','for17 distinct validated cases','One unused package helper warning',
            'P09/A12/A13 OPEN','Native011 unapproved/unexecuted','P10 not started'):
            c.require(marker in profile,'NAVIGATION_REQUEST_CURSOR_CURRENT_ACCESS_AND_GATE_BOUNDARIES')
        c.require('p09-source-search-navigation-v1.md'in q.text(DOCS[2]),'REVIEW_AND_NAVIGATION_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 숨은 설명과 메모 검색',1)[0]
        for marker in ('2026-10-20','고유17개','461fresh/final461','20.64%','21.2149%','5.0134%','미사용 경고1종',
            '잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작','다음은 SEARCH-006'):
            c.require(marker in state,'CURRENT_NAVIGATION_PASS_RESOURCES_WARNING_AND_UNCHANGED_GATE')
        runner='tools/p09/run_search_navigation_components.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_NAVIGATION_RECOVERY_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_RETAINED_SEARCH_NAVIGATION_CODE_DOCUMENT_SYNC_SEVENTEEN_DISTINCT_CASES_NOT_FULL_TARGET_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=8,prior_core_passes_preserved=9,
            original_search_code_and_test_bodies_inverse_verified=True,production_changed_after_initial_failure=False,
            harmless_fixture_helper_warning_disclosed=True,entire_461_inputs_reaudited=False,
            full_search_target_or_native_qualified=False,next_work='SEARCH_006_original_literal_replacement_ranges_protection_diff_and_transaction_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NAVIGATION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NAVIGATION_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
