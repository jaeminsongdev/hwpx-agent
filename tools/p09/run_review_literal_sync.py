"""Scoped review-v3 source/stored/result/document closure, without Cargo or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_review_literal_focused as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-review-literal-sync087.v1.json'
CORE=base.base.PRIOR
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-review-literal-output-v3.md',
    'protocol/migrations/p09-source-literal-text-atom-output-v2.md',
    'protocol/migrations/p09-literal-replacement-product-request-v2.md')
RETAINED={base.LEGACY,base.FIXTURE,base.TARGET,base.WRAPPER,base.base.MODULE,base.base.TEST,
    base.base.PARENT,base.base.SOURCE,base.HARNESS,'tools/p09/run_stored_review_literal_focused.py',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs',
    'crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_LITERAL_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_LITERAL_SYNC',actual_Cargo_or_tests=False,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        core,stored,failed=q.json(CORE),q.json(base.OUTPUT),q.json(base.FAILED)
        for name,digest in ((CORE,'4ce628eb5aa3ebc2cfd8b5a604502a1548ce81264fdbeb7811088cd03936e8c2'),
            (base.OUTPUT,'2d5c00db901cdfba93a072f5a42132ce195075f1fc354dce2fd7ca45a5ef18ed'),
            (base.FAILED,'a3a5315831e670bc28b40e7d341b4413dca8e2a10711ee6085d0558d9aadc697')):
            c.require(q.snapshots[name]['sha256']==digest,'EXACT_CORE_STORED_PASS_AND_ORIGINAL_DEADLINE_RECORDS')
        c.require(core['state'].startswith('PASS_')and core['total_executed_cases']==32 and core['cleanup']
            and core['fresh_inputs']==core['final_fresh_hashes']==495,'CORE_THIRTY_TWO_PASS_INPUT_CLOSURE')
        c.require(stored['state']=='PASS_FOCUSED_STORED_REVIEW_LITERAL_SIX_CASES_LEGACY_TYPECHECK_CORE32_RETAINED_NOT_JSON_NATIVE_OR_GATE'
            and stored['current_stored_cases']==6 and stored['retained_core_cases']==32 and stored['cleanup']
            and stored['fresh_inputs']==stored['final_fresh_hashes']==502,'SIX_CURRENT_STORED_PASS_INPUT_CLOSURE')
        old={p['path']:p for p in failed['source_pins']};tested={p['path']:p for p in stored['source_pins']}
        prior={p['path']:p for p in core['source_pins']}
        core_runner=base.base.prior
        names=RETAINED|core_runner.NEW|core_runner.CHANGED|{core_runner.V2_TEST,core_runner.SEARCH_TEST}
        for name in sorted(names):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_REVIEW_SOURCE_STORED_SIX_TESTS_AND_OWNER_MATCH_SUCCESS')
        for name in core_runner.NEW|core_runner.CHANGED|{core_runner.V2_TEST,core_runner.SEARCH_TEST}:
            c.require(tested[name]==prior[name],'THIRTY_TWO_CORE_INPUTS_RETAINED_NOT_REEXECUTED')
        base.extraction(q,old)
        expected={'actual_import::review_literal_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.base.TEST))}
        c.require(len(expected)==6 and len(stored['steps'])==2,'EXACT_STORED_SIX_AND_SEPARATE_LEGACY_TYPECHECK')
        first,check=stored['steps']
        c.require(first['exit_code']==0 and first['diagnostics']==[] and len(first['tests'])==6
            and {n for n,s in first['tests']}==expected and all(s=='ok'for n,s in first['tests']),
            'ALL_ORIGINAL_SIX_PASS_WITH_NO_SKIPS_OR_NEW_DIAGNOSTICS')
        c.require(check['exit_code']==0 and check['tests']==[] and check['diagnostics']==[
            'warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning'],
            'LEGACY_TYPECHECK_NOT_TEST_EXECUTION_AND_PREEXISTING_HELPER_WARNING')
        for step in stored['steps']:
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0 and limits['verified']
                and limits['affinity_mask']==1 and limits['cpu_hard_cap_machine_percent']==6.25
                and limits['priority_class']==16384 and limits['kill_on_close'],'OWNED_JOBS_TERMINAL_AND_ORIGINAL_RESOURCE_POLICY')
        c.require(failed['state'].startswith('FAILED_')and failed['error_code']=='STOP_SOURCE_NOTE_API_COMMAND_DEADLINE'
            and 'tests'not in failed['steps'][0]and failed['cleanup'],'ORIGINAL_MISSING_TEST_RESULTS_NOT_ZERO_OR_PASS')
        for suffix,error in (('083','KeyError'),('084','ValueError')):
            record=q.json(f'implementation/p09/evidence/p09-361-stored-review-literal-focused{suffix}.v1.json')
            c.require(record['state']=='FAILED_FOCUSED_STORED_REVIEW_LITERAL'and record['steps']==[]and record['cleanup']
                and record['error_type']==error,'ORIGINAL_PREFLIGHT_FAILURES_PRESERVED_NOT_RELABELED')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'NINETEEN_SEARCH_BOUNDARIES_RETAINED')
        for marker in ('32pass·495fresh/final495','6pass·502fresh/final502','고유38개',
            'v3 JSON/전체 transaction 미완료','cargo check만','clone/소유권 전달용 reimport'):
            c.require(marker in progress,'PROGRESS_VERIFIED_SOURCE_STORED_COUNTS_NOT_STRICT_JSON_OR_GATE')
        profile=q.text(DOCS[2])
        for marker in ('candidate/v3','exact direct subList','Other and enclosing field intervals stay intact',
            '32 retained core plus6 stored equals38','Missing results are not proof of zero execution',
            'legacy form_stored_provider target passes cargo check only','strict v3 product JSON',
            'P09/A12/A13 OPEN','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'V3_PROFILE_PRECISE_MEMO_EXCEPTION_FAILURES_AND_OPEN_PRODUCT_BOUNDARY')
        for name in DOCS[3:]:c.require('p09-source-review-literal-output-v3.md'in q.text(name),'EXISTING_V2_LINKS_SEPARATE_V3_WITHOUT_WIDENING')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 ACTIVE 최신 상태 —',1)[0]
        for marker in ('신규core12+영향20=32pass','원래저장6pass·502fresh/final502','160.188초','31.05%',
            '26.7908%','5.0788%','엄격한 제품 JSON과 owned 원본 연결','공식158/249','잔여91','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_SOURCE_STORED_PASS_AND_NATIVE_EXECUTION_REMAINDER')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_LITERAL_SOURCE_STORED_CODE_DOCUMENT_SYNC_THIRTY_EIGHT_CASES_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_distinct_component_cases=38,
            core_cases_retained=32,stored_cases=6,legacy_target_typechecked_not_executed=True,
            full_502_input_set_reaudited=False,original_failed_results_preserved=True,resource_policy_unchanged=True,
            strict_v3_json_or_owned_source_handoff_qualified=False,full_search_native_cas_execution_publication_qualified=False,
            next_work='Strict_v3_review_literal_product_JSON_and_owned_source_handoff')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_LITERAL_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
