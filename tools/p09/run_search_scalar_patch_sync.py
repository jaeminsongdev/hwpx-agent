"""Original scalar patch evidence/source/docs closure, never Cargo or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_scalar_alias_boundary as current
base,shared,c,a=current.base,current.shared,current.c,current.a
PASSED=current.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-search-scalar-patch-sync066.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-search-scalar-patch-prerequisite-v1.md')
RETAINED={'crates/hwpx-package/src/patch/leaf_text.rs','crates/hwpx-package/src/preserving_xml.rs',
    'crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/path.rs',*base.LEGACY}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCALAR_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_SCALAR_PATCH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed,initial,prior=q.json(PASSED),q.json(current.PASSED),q.json(base.PRIOR)
        for name,sha in ((PASSED,'e0ec9bcd90899043bd2fedc3fcef2466430f18d2dbf31027d9ed1168a45af715'),
            (current.PASSED,'046bd4d4a12c456580b0ca931e58e3c624fc54d103bbc769dd634abee3c7cad9'),
            (base.PRIOR,'bc4535b330d9a3a82b948d2080d56988aaf51ad643765e437ec062a2aeeb729a')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_SCALAR_CURRENT_PRIOR_COMPONENT_AND_NAVIGATION_RESULTS')
        c.require(passed['state']=='PASS_SCALAR_COLLISION_ALIAS_LINEAR_ENDPOINT_NINE_CURRENT_FIVE_RETAINED_NOT_SEARCH_REPLACEMENT_PRODUCT_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==468 and passed['cleanup']and passed['current_executed_cases']==9
            and passed['prior_passes_preserved']==5 and passed['distinct_validated_cases']==14,'EXACT_NINE_CURRENT_FIVE_RETAINED_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in initial['source_pins']};original={p['path']:p for p in prior['source_pins']}
        sources={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        for name in sources-base.NEW:c.require(tested[name]==old[name],'OTHER_SOURCE_TEST_AND_PATCH_INPUTS_RETAINED_IN_CURRENT_PASS')
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_SCALAR_AND_RETAINED_INPUTS_MATCH_PASS')
        base.inverse(q,original)
        text=q.text(current.HELPER);guard_change='seen.insert((target.part.collision_key(),target.element_index))';old_guard='seen.insert((&target.part,target.element_index))'
        linear=('        // Preflight already requires ordered disjoint ranges; retain unique\n'
            '        // endpoints linearly instead of sorting the same metadata again.\n'
            '        for range in ranges {for point in [range.start,range.end] {if points.last()!=Some(&point){points.push(point);}}}\n')
        before='        for range in ranges {points.push(range.start);points.push(range.end);}points.sort_unstable();points.dedup();\n'
        c.require(text.count(guard_change)==1 and text.count(linear)==1,'ONLY_ALIAS_GUARD_AND_LINEAR_ENDPOINT_OPTIMIZATIONS')
        base.base.inverse(text.replace(guard_change,old_guard).replace(linear,before),old[current.HELPER],'ORIGINAL_SCALAR_SOURCE_PARSER_AND_WRITER_BODY_EXACT_INVERSE')
        tests=q.text(base.TEST);prefix=tests.split('#[test]\nfn scalar_ranges_collision_key_aliases_',1)[0]
        base.base.inverse(prefix,old[base.TEST],'ORIGINAL_EIGHT_SCALAR_BODIES_UNCHANGED')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',tests));c.require(len(core)==9 and len(passed['steps'])==1,'EXACT_NINE_CURRENT_SCALAR_CASES')
        c.require({n for n,s in passed['steps'][0]['tests']}==core and all(s=='ok'for n,s in passed['steps'][0]['tests'])
            and passed['steps'][0]['diagnostics']==[],'ALL_NINE_CURRENT_SCALAR_CASES_PASS_WITHOUT_DIAGNOSTICS')
        c.require(initial['state'].startswith('PASS_')and initial['fresh_inputs']==initial['final_fresh_hashes']==466 and initial['cleanup'],
            'ORIGINAL_THIRTEEN_CASE_INPUT_CLOSURE')
        legacy=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.LEGACY[0])))
        for step,expected in zip(initial['steps'][1:],(legacy,base.TARGETED),strict=True):
            c.require({n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])and step['diagnostics']==[],
                'EXACT_FIVE_UNCHANGED_ORIGINAL_PATCH_PASSES')
        for step in (*initial['steps'],*passed['steps']):
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_SCALAR_PASS_JOBS_TERMINAL_EMPTY_CLOSED')
        failures=((base.FAILED,'807b6b6919b176e66dcfdcca457cdc4ff6750cfe1cdf68ca982389dda8125826'),
            (current.STOPPED,'9b46bb687f50d2362398ba10dc3fcf042cf330618f4f3107ab81b8ee0234b708'),
            (current.COMPILE_FAILED,'63e3db4a6bf305edc9cb0049b98d67a165d3e3620ecfb9af72d39ae79f54651a'))
        for name,sha in failures:
            failed=q.json(name);c.require(q.snapshots[name]['sha256']==sha and failed['state'].startswith('FAILED_')and failed['cleanup'],'ORIGINAL_COMPILE_FAILURES_AND_SYSTEM_CPU_STOP_PRESERVED')
            if name==current.STOPPED:
                c.require(failed['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'and failed['system_CPU_max']==96.35,'SYSTEM_CPU_STOP_NOT_CHANGED_TO_SUCCESS')
                job=failed['steps'][0]['owned_job'];c.require(job['last_job_accounting']['job_cpu_seconds']==0.172 and job['last_job_accounting']['active_processes']==0
                    and job['cleanup_confirmed']and job['job_handle_closed'],'STOPPED_LOW_OWNED_LOAD_NOT_CAUSAL_PROCESS_ATTRIBUTION')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('고유14개','468 fresh/final468','기존 patch 회귀5개','CPU96.35%','원인을 확정하지 않는다','다음은 SEARCH-006 원본 match'):
            c.require(marker in progress,'SCALAR_PROGRESS_COUNTS_CPU_STOP_AND_REMAINING_PRODUCT_JOIN')
        profile=q.text(DOCS[2])
        for marker in ('does not','no service JSON schema','14 distinct validated cases','468 fresh/final468','not causally identified',
            'P09/A12/A13 OPEN','Native011 unapproved/unexecuted','P10 not started'):
            c.require(marker in profile,'SCALAR_PREREQUISITE_NOT_PRODUCT_OR_NATIVE_PROFILE_BOUNDARIES')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 다시 찾기',1)[0]
        for marker in ('2026-10-20','고유14개','468fresh/final468','18.62%','34.9148%','1.7572%','CPU96.35%',
            '잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작','다음은 SEARCH-006 원본 match'):
            c.require(marker in state,'CURRENT_SCALAR_RESULT_RESOURCES_FAILURES_AND_UNCHANGED_GATE')
        runner='tools/p09/run_search_scalar_alias_boundary.py';q.pin(runner);c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_LINEAR_SCALAR_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_SCALAR_PATCH_CODE_DOCUMENT_SYNC_FOURTEEN_DISTINCT_CASES_NOT_SEARCH_REPLACEMENT_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=9,prior_patch_passes_preserved=5,
            original_patch_and_scalar_parser_writer_body_inverse_verified=True,entire_468_inputs_reaudited=False,
            system_CPU_stop_cause_identified=False,resource_policy_unchanged=True,search_replacement_product_route_qualified=False,
            next_work='SEARCH_006_actual_match_NFC_contiguity_multi_run_protection_candidate_and_output_semantic_readback')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SCALAR_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SCALAR_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
