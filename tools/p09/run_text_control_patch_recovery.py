"""Keep189 original zero-test API-name failure; change only the test's PackageGraph builder call."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_control_patch_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-text-control-patch-recovery190.v1.json'


def repair(q,old):
    text=q.text(base.TEST);new='let graph=PackageGraph::build(&mut reader,Default::default())?;';original='let graph=PackageGraph::parse(&mut reader)?;'
    c.require(text.count(new)==1,'ONE_TEST_PACKAGE_GRAPH_BUILDER_API_CORRECTION')
    audit.inverse(text.replace(new,original),old[base.TEST],'ENTIRE189_TEST_BODY_RESTORED_EXCEPT_ONE_CORRECT_EXISTING_GRAPH_API_CALL')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_CONTROL_PATCH_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_CONTROL_PATCH_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,text_control_source_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='8f722fdc7a45aa209c505740fd421fcc10ae59f3cf81417cb572d0ac89f899fc'
            and failed['state']=='FAILED_TEXT_CONTROL_PATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL189_FAILURE_PRESERVED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and not step['tests']and step['cleanup']and step['owned_job']['owned_tree_empty']
            and step['owned_job']['job_handle_closed']and step['bounded_output_observation']['rust_error_codes']==['E0599'],'EXACT189_GRAPH_API_TEST_ERROR_ZERO_TESTS_TERMINAL_JOB')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_GUARDS_OTHER_TESTS_AND_FIXTURES_UNCHANGED_AFTER189')
        repair(q,old);base.inverse(q,{p['path']:p for p in baseline['source_pins']});cases=base.expected(q)
        print(json.dumps(dict(state='TEXT_CONTROL_PATCH_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_patch_cases=18,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_typed_original_text_control_patch_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','patch_text_control_atoms','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        base.prior.prior.base.prior.base.good_step(row['steps'][0],cases);c.require(base.inventory(guard.check)==names,'FINAL_TEXT_CONTROL_PATCH_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_CONTROL_PATCH18_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_patch_cases=18,old_patch_and_source_products242_or_official249_reexecuted=False,all_old_patch_and_whitespace_bodies_inverse_verified=True,
            old_intents_early_zero_budget_and_original_control_rejection_preserved=True,all_four_range_families_share_joint_budgets_and_target_exclusion=True,
            production_unchanged_after189=True,original189_failure_preserved=True,
            next_work='SEARCH009_exact_original_control_search_selection_protection_compiler_and_readback_then_other_control_families_and_full_product_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_CONTROL_PATCH_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_CONTROL_PATCH_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
