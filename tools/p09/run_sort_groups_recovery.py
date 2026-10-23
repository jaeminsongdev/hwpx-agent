"""Preserve242 compile failure; redact new group Debug, first run of16 source contracts."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_groups_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-recovery243.v1.json'
DRIVER='tools/p09/run_sort_groups_recovery.py'
OLD='#[derive(Clone,Debug,Eq,PartialEq,Serialize)]\npub struct SourceParagraphSortGroup {'
NEW='#[derive(Clone,Eq,PartialEq,Serialize)]\npub struct SourceParagraphSortGroup {'
DEBUG='''impl fmt::Debug for SourceParagraphSortGroup {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortGroup(<redacted>)")}
}
'''


def inventory(check):return base.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,
        structured_or_nested_selected_subtree_composition_qualified=False,multigroup_current_stored_or_product_request_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='cb97054c0c0099657697e0a3c622a5d8c8ce2865b6b393830e5d2d45fcfafed7'
            and failed['cleanup']and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101 and not failed['steps'][0]['tests']
            and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0277'],'EXACT242_COMPILE_FAILURE_NO_SOURCE_CASES_RUN')
        job=failed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'FAILED242_JOB_TERMINAL_EMPTY_CLOSED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,base.MODEL}:c.require(q.snapshots[name]==old[name],'ALL_SOURCE_PROTECTION_PATCH_READBACK_PRODUCTS_TESTS_AND_NATIVE_GUARDS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        text=q.text(base.MODEL);c.require(text.count(NEW)==1 and text.count(DEBUG)==1,'ONLY_NEW_GROUP_NONDISCLOSING_DEBUG_REPAIR')
        audit.inverse(text.replace(NEW,OLD).replace(DEBUG,''),old[base.MODEL],'ALL_NEW_GROUP_SELECTION_SORT_PROTECTION_OUTPUT_AND_RECEIPT_LOGIC_UNCHANGED')
        previous=q.json(base.base.OUTPUT);c.require(q.snapshots[base.base.OUTPUT]['sha256']=='c06a8d1482b21cc0d753d943faf948affbfb41984a4502fa5204c692af174619','EXACT238_ORIGINAL_SORT_LINEAGE')
        base.inverse(q,{p['path']:p for p in previous['source_pins']});cases=base.expected(q)
        print(json.dumps(dict(state='SORT_GROUPS_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),first16_source_cases=True,old_passes_reexecuted=False)),flush=True)
        harness.run_one('first_sixteen_actual_multigroup_source_contracts',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','source_paragraph_sort_groups','--message-format=short','--','--test-threads=1'],
            cases,guard,audit.environment(),row,observe_capture=base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_MULTIPARENT_MULTIPART_PARAGRAPH_SORT16_NOT_CURRENT_PRODUCT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=16,
            one_original_transaction_and_output_admission=True,global_comparison_budget_and_all_selected_protection=True,
            old_sort19_product20_compiler21_and_official249_reexecuted=False,
            next_work='current_store_strict_multigroup_request_actual_splices_common_compiler_then_nested_structured_keys_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_GROUPS_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
