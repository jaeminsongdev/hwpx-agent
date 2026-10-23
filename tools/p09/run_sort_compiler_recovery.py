"""Preserve237 source6 and original E0432 failure; one test-only parent import, first execution of product15."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_compiler_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-compiler-recovery238.v1.json'
DRIVER='tools/p09/run_sort_compiler_recovery.py'
IMPORT='use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::PinnedP02RegistryBytes;\n'


def inventory(check):return base.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_COMPILER_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_COMPILER_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='ef1a767cce07209e25dddd97fcb145ee8b9ce2106159dbe45cd85115d2ffcccf'and failed['cleanup']
            and failed['steps'][0]['exit_code']==0 and failed['steps'][1]['exit_code']==101
            and failed['steps'][1]['bounded_output_observation']['rust_error_codes']==['E0432'],'EXACT237_SOURCE6_AND_TEST_PARENT_IMPORT_COMPILER_FAILURE_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,base.COMPILED_TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_SOURCE_SORT_INVENTORY_DISPATCH_COMPILER_ROUTER_AND_OTHER_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        text=q.text(base.COMPILED_TEST);c.require(text.count(IMPORT)==1,'ONE_TEST_ONLY_PINNED_FIXTURE_PARENT_TYPE_IMPORT')
        audit.inverse(text.replace(IMPORT,''),old[base.COMPILED_TEST],'ALL_EIGHT_NEW_COMPILER_TEST_BODIES_UNCHANGED')
        base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        core,products,affected=base.expected(q);tools.good_step(failed['steps'][0],core)
        for step in failed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH237_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(not failed['steps'][1]['tests'],'NO_PRIOR_PRODUCT_CASE_EXECUTED_OR_REPLAYED')
        print(json.dumps(dict(state='SORT_COMPILER_PRODUCT_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained_source6=True,new_compiler_manifest_cases=12,affected_legacy_cases=3,production_unchanged=True)),flush=True)
        harness.run_one('first_product_execution_twelve_sort_compiler_manifest_and_three_affected_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(products|affected),'--exact','--test-threads=1'],products|affected,guard,audit.environment(),row,
            observe_capture=base.prior.prior.base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],products|affected);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SORT_SPLICES6_SHARED_COMPILER_MANIFEST12_AFFECTED3_RETAINED6_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=15,retained_source_cases=6,distinct_component_cases=21,
            original_product_source_and_compiler_guards_unchanged=True,source6_sort_source19_product20_and_official249_reexecuted=False,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_multi_group_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_COMPILER_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_COMPILER_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
