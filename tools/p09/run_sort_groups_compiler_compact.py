"""Recover missing248 publication with lossless bounded layout, fresh25 cases; no Native retry."""
import importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_groups_compiler_components as base
import compact_receipt_json as compact
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-compiler-compact249.v1.json'
DRIVER='tools/p09/run_sort_groups_compiler_compact.py'
MODULE='tools/p09/compact_receipt_json.py'
TEST='tools/p09/tests/test_compact_receipt_json.py'
OBSERVED='implementation/p09/evidence/p09-361-sort-groups-compiler-publication-failure248.v1.json'


def inventory(check):return base.inventory(check)|{DRIVER,MODULE,TEST,OBSERVED}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_COMPACT_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_COMPACT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True,
        publication_format=compact.PROFILE,prior248_case_acceptance=False,reexecution_required_because_full248_evidence_unavailable=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=q.json(base.base.OUTPUT);docs=q.json(base.DOC_BASE);observed=q.json(OBSERVED)
        c.require(not(c.ROOT/base.OUTPUT).exists()and observed['observed_error']=='WORKSPACE_BOUNDED_RECEIPT'
            and not observed['complete_case_list_and_terminal_job_accounting_recovered']and observed['accepted_component_cases_from_this_observation']==0,
            'MISSING248_COMPLETE_EVIDENCE_NOT_PROMOTED_OR_FABRICATED')
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='96a937a14719cf4d88e6540d8c3fedc08ed0e93ce1cfe57ae8044515fd879630'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==824,'EXACT246_CURRENT_MULTIGROUP_PRODUCT20')
        c.require(q.snapshots[base.DOC_BASE]['sha256']=='191f667a921804505d3db4d181283081c94e959992cbe25954dd1e92053b2a04'
            and docs['cleanup'],'EXACT247_PREVIOUS_DOCS')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in base.NEW|base.CHANGED|{DRIVER,MODULE,TEST,OBSERVED}:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_PRODUCTS_OWNERS_ROUTER_SECURITY_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        base.inverse(q,old);core,products,affected=base.expected(q)
        spec=importlib.util.spec_from_file_location('p09_compact_receipt_contracts',c.ROOT/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        c.require(result.testsRun==4 and not result.skipped and result.wasSuccessful(),'FOUR_LOSSLESS_LAYOUT_STATE_TAMPER_AND_SIZE_CONTRACTS')
        row['compact_layout_contracts_passed']=4
        print(json.dumps(dict(state='MULTIGROUP_COMPACT_PREFLIGHT',inputs=len(q.snapshots),layout_contracts=4,source_cases=6,product_cases=19,receipt_cap_unchanged=262144)),flush=True)
        snapshot=base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        harness.run_one('six_actual_source_multigroup_moved_slot_inventory_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_paragraph_sort_groups','--message-format=short','--','splices_v1::','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],core)
        harness.run_one('fourteen_multigroup_compiler_manifest_and_five_affected_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(products|affected),'--exact','--test-threads=1'],products|affected,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],products|affected);q.finish();guard.check(force=True)
        row.update(state='PASS_MULTIGROUP_SOURCE_SPLICES6_COMPILER_MANIFEST14_AFFECTED5_COMPACT4_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=25,new_source_cases=6,new_product_cases=14,affected_legacy_cases=5,
            all18_closed_families_and_original17_bodies_retained=True,actual_moved_slots_bound_to_original_compiler_and_manifest=True,
            old_multigroup_source16_product20_and_official249_reexecuted=False,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_nested_structured_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_COMPACT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_MULTIGROUP_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        packet=compact.pack(row)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,packet,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','compact_layout_contracts_passed','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
