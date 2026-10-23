"""Nine scalar cases after linear endpoint construction; retain five original patch passes."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_scalar_patch_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-search-scalar-linear-recovery065.v1.json'
COMPILE_FAILED='implementation/p09/evidence/p09-361-search-scalar-linear-recovery064.v1.json'
STOPPED='implementation/p09/evidence/p09-361-search-scalar-alias-boundary063.v1.json'
PASSED=base.OUTPUT
TESTS={'scalar_ranges_collision_key_aliases_cannot_duplicate_one_leaf_scan',
    'scalar_ranges_reject_overlap_unsorted_duplicate_targets_empty_and_foreign_scalar_ranges_atomically'}
HELPER='crates/hwpx-package/src/patch/leaf_scalar_ranges.rs'


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCALAR_ALIAS_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_SCALAR_ALIAS_BOUNDARY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,search_replacement_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        passed=q.json(PASSED);c.require(q.snapshots[PASSED]['sha256']=='046bd4d4a12c456580b0ca931e58e3c624fc54d103bbc769dd634abee3c7cad9'
            and passed['state'].startswith('PASS_')and passed['cleanup']and passed['total_executed_cases']==13,'EXACT_SCALAR_THIRTEEN_PASSES')
        old={p['path']:p for p in passed['source_pins']}
        for name in names-{HELPER,base.TEST}:c.require(q.snapshots[name]==old[name],'NO_OTHER_SCALAR_SOURCE_INPUT_CHANGE')
        text=q.text(HELPER);current='seen.insert((target.part.collision_key(),target.element_index))';original='seen.insert((&target.part,target.element_index))'
        c.require(text.count(current)==1,'ONE_PACKAGE_COLLISION_KEY_DUPLICATE_REPAIR');text=text.replace(current,original)
        linear=('        // Preflight already requires ordered disjoint ranges; retain unique\n'
            '        // endpoints linearly instead of sorting the same metadata again.\n'
            '        for range in ranges {for point in [range.start,range.end] {if points.last()!=Some(&point){points.push(point);}}}\n')
        sorted_points='        for range in ranges {points.push(range.start);points.push(range.end);}points.sort_unstable();points.dedup();\n'
        c.require(text.count(linear)==1,'ONE_LINEAR_ORDERED_ENDPOINT_OPTIMIZATION');base.base.inverse(text.replace(linear,sorted_points),old[HELPER],'SCALAR_HELPER_OTHER_BODY_EXACT_INVERSE')
        tests=q.text(base.TEST);prefix=tests.split('#[test]\nfn scalar_ranges_collision_key_aliases_',1)[0]
        base.base.inverse(prefix,old[base.TEST],'ORIGINAL_EIGHT_SCALAR_TEST_BODIES_UNCHANGED')
        compile_failed=q.json(COMPILE_FAILED);c.require(q.snapshots[COMPILE_FAILED]['sha256']=='63e3db4a6bf305edc9cb0049b98d67a165d3e3620ecfb9af72d39ae79f54651a'
            and compile_failed['state']=='FAILED_SEARCH_SCALAR_ALIAS_BOUNDARY'and compile_failed['cleanup']
            and compile_failed['steps'][0]['tests']==[],'ORIGINAL_TEST_PRIVATE_API_COMPILE_FAILURE_PRESERVED')
        before={p['path']:p for p in compile_failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==before[name],'NO_PRODUCTION_OR_OTHER_INPUT_CHANGE_FOR_TEST_API_REPAIR')
        repaired='assert_eq!(path.as_str().to_ascii_lowercase(),alias.as_str().to_ascii_lowercase());'
        original='assert_eq!(path.collision_key(),alias.collision_key());'
        c.require(tests.count(repaired)==1,'ONE_TEST_ONLY_PUBLIC_ASCII_PATH_ASSERTION');base.base.inverse(tests.replace(repaired,original),before[base.TEST],'TEST_ONLY_PRIVATE_API_REPAIR_EXACT_INVERSE')
        declared=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',tests));c.require(len(declared)==9 and TESTS<=declared,'EXACT_NINE_CORE_TWO_TARGETED_CASES')
        prior_core=dict(passed['steps'][0]['tests']);c.require(len(prior_core)==8 and all(s=='ok'for s in prior_core.values())
            and all(s=='ok'for step in passed['steps'][1:]for n,s in step['tests']),'RETAIN_ORIGINAL_THIRTEEN_INCLUDING_DUPLICATE_BASELINE')
        stopped=q.json(STOPPED);c.require(q.snapshots[STOPPED]['sha256']=='9b46bb687f50d2362398ba10dc3fcf042cf330618f4f3107ab81b8ee0234b708'
            and stopped['state']=='FAILED_SEARCH_SCALAR_ALIAS_BOUNDARY'and stopped['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'
            and stopped['cleanup'],'ORIGINAL_SYSTEM_CPU_STOP_NOT_PROMOTED_TO_SUCCESS')
        job=stopped['steps'][0]['owned_job'];c.require(job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0 and job['last_job_accounting']['job_cpu_seconds']==0.172,
            'STOPPED_OWNED_JOB_LOW_CPU_AND_TERMINAL_NOT_CAUSAL_ATTRIBUTION')
        env=base.base.environment();args=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','patch_leaf_scalar_ranges','--','--test-threads=1']
        harness.run_one('nine_scalar_alias_and_linear_endpoint_cases',args,declared,guard,env,row)
        c.require(base.inventory(guard.check)==names,'FINAL_SCALAR_ALIAS_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SCALAR_COLLISION_ALIAS_LINEAR_ENDPOINT_NINE_CURRENT_FIVE_RETAINED_NOT_SEARCH_REPLACEMENT_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=9,prior_passes_preserved=5,
            distinct_validated_cases=14,only_collision_key_guard_and_linear_endpoints_changed=True,original_scalar_parser_writer_and_test_bodies_preserved=True,
            stopped_system_CPU_source_causally_identified=False,resource_policy_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SCALAR_ALIAS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SCALAR_ALIAS_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
