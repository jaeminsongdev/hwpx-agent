"""Strengthen two boundary tests, retain41 unchanged passes and preserve all failed originals."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_patch_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-whitespace-patch-strengthening182.v1.json'
CASES={'whitespace::whitespace_and_both_old_range_families_share_one_count_budget',
    'whitespace::whitespace_output_atom_count_and_cross_family_duplicate_targets_are_bounded'}
OLD_COUNT='''    let bytes=package("<hp:t>  </hp:t>")?;let specs=vec![(0,vec![Range::text(0,0,2,vec![text(" ")?])?])];
    assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:2,..Default::default()})?,3).is_err());assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:3,..Default::default()})?,3).is_ok());Ok(())
'''
NEW_COUNT='''    let bytes=package("<hp:t>  </hp:t>")?;let specs=vec![(0,vec![Range::text(0,0,1,vec![])?,Range::text(0,1,2,vec![text(" ")?])?])];
    // Three top-level intents fit cap3, but their four scalar/atom ranges must not.
    assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:3,..Default::default()})?,3).is_err());assert!(apply(&bytes,&specs,PatchLimits::new(PatchLimitConfig{max_intents:4,..Default::default()})?,3).is_ok());Ok(())
'''
OLD_DUP='''    assert!(apply(&bytes,&[(1,vec![Range::text(0,0,0,vec![text(" ")?])?])],Default::default(),3).is_err());Ok(())
'''
NEW_DUP='''    // The old edit at0..1 and insertion at2 are byte-disjoint; shared target rejection is required.
    assert!(apply(&bytes,&[(1,vec![Range::text(0,2,2,vec![text(" ")?])?])],Default::default(),3).is_err());Ok(())
'''


def repair(q,pins):
    text=q.text(base.TEST)
    for new,old in[(NEW_COUNT,OLD_COUNT),(NEW_DUP,OLD_DUP)]:c.require(text.count(new)==1,'EXACT_ONE_STRENGTHENED_BOUNDARY_ASSERTION');text=text.replace(new,old)
    audit.inverse(text,pins[base.TEST],'ENTIRE181_TEST_SUITE_RESTORED_EXCEPT_TWO_STRONGER_JOINT_COUNT_AND_NONOVERLAPPING_TARGET_CASES')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_STRENGTHENING_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_PATCH_STRENGTHENING',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,whitespace_source_compiler_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='25377b3cccff818059d57940c4f2badaa0470d81832857e3631c086fa51f374f'
            and previous['state']=='PASS_WHITESPACE_PATCH24_RANGE19_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE'and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==692 and previous['total_executed_cases']==43,'EXACT181_FULL43_PASSES_AND_INPUT_CLOSURE')
        pins={p['path']:p for p in previous['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_GUARDS_OTHER_TESTS_AND_FIXTURES_UNCHANGED_AFTER181')
        repair(q,pins);base.inverse(q,{p['path']:p for p in baseline['source_pins']});expected=base.expected(q)
        base.good_step(previous['steps'][0],expected);c.require(CASES<expected and len(expected-CASES)==41,'EXACT43_IDENTITIES_WITH_TWO_STRENGTHENED_AND41_RETAINED')
        print(json.dumps(dict(state='WHITESPACE_STRENGTHENING_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),current_cases=2,retained_cases=41,one_cpu_mask=4)),flush=True)
        harness.run_one('two_stronger_joint_budget_and_disjoint_shared_target_tests',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','whitespace_patch_focused','--message-format=short','--',*sorted(CASES),'--exact','--test-threads=1'],CASES,guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],CASES);c.require(base.inventory(guard.check)==names,'FINAL_WHITESPACE_STRENGTHENING_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE2_STRENGTHENED41_RETAINED_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=2,retained_cases=41,new_patch_cases=24,affected_range_cases=19,total_distinct_cases=43,production_unchanged_after181=True,
            unchanged41_cases_reexecuted=False,old218_products_and_unrelated_source_reexecuted=False,original_patch_engine_and_all_old_range_bodies_inverse_verified=True,
            next_work='SEARCH023_original_source_whitespace_policy_selection_protection_compiler_and_readback_then_current_store_product_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_STRENGTHENING_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WHITESPACE_STRENGTHENING_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
