"""Preserve213/214; exact duplicate admission plus source child containment, only1 unit and30 new products."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_search_operation_compiler_recovery as prior
base=prior.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-search-owner-admission-recovery215.v1.json'
DRIVER='tools/p09/run_source_search_owner_admission_recovery.py'
OLD='    assert_eq!(error,domain_ir::DocumentGraphError::DuplicateIdentifier);assert_eq!(anchor,f.graph().sections()[0].body.children[0].common().source_anchor.clone().ok_or("anchor")?);Ok(())\n'
NEW='''    assert_eq!(error,domain_ir::DocumentGraphError::DuplicateIdentifier);
    let owner=f.graph().sections()[0].body.children[0].common().source_anchor.as_ref().ok_or("owner")?;
    let outer=f.source().resolve_anchor(owner)?.element().and_then(|e|e.outer_span()).ok_or("outer")?;
    let inner=f.source().resolve_anchor(&anchor)?.element().and_then(|e|e.outer_span()).ok_or("inner")?;
    assert!(outer.start()<=inner.start()&&inner.end()<=outer.end());Ok(())
'''


def inventory(check):return prior.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_OWNER_ADMISSION_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_OWNER_ADMISSION_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,trusted_route_full_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(prior.OUTPUT);original=q.json(base.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='2e3d2b168ebc257418f978361e1cdad76a0a7856f2b4cfd407d66c32bdbf0d4a'
            and failed['cleanup']and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101,'EXACT214_TEST_ONLY_WRONG_ANCHOR_EQUALITY_AND_NO_PRODUCT_EXECUTION')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='30d6a01aa8e88be436d9ec8a468a1929ffb8f5b99ac4786d355ccac28d7fe694'and original['cleanup'],'ORIGINAL213_FIVE_PASSES_AND_FAILURE_PRESERVED')
        units,products=base.expected(q);retained={n for n,s in original['steps'][0]['tests']if s=='ok'};recovered={n for n,s in failed['steps'][0]['tests']if s!='ok'}
        c.require(len(retained)==5 and len(recovered)==1 and retained|recovered==units,'FIVE_RETAINED_AND_ONE_FAILED_OWNER_CASE_NOT_REPLAYED')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{DRIVER,base.UNIT}:c.require(q.snapshots[name]==old[name],'ALL_COMPILER_PRODUCTION_SOURCE_OTHER_UNITS_AND30_PRODUCT_CASES_UNCHANGED')
        text=q.text(base.UNIT);c.require(text.count(NEW)==1,'EXACT_DUPLICATE_GRAPH_REJECTION_AND_ACTUAL_PARENT_CHILD_CONTAINMENT')
        audit.inverse(text.replace(NEW,OLD),old[base.UNIT],'ONLY_WRONG_TEXT_VS_PARAGRAPH_IDENTITY_ASSERTION_CORRECTED_TO_SOURCE_CONTAINMENT')
        base.inverse(q,{p['path']:p for p in q.json(base.BASELINE)['source_pins']})
        print(json.dumps(dict(state='SOURCE_OWNER_ADMISSION_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_owner_units=5,recovery_owner_units=1,not_yet_run_products=30)),flush=True)
        harness.run_one('one_duplicate_anchor_admission_and_actual_child_containment',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--lib','--message-format=short','--',*sorted(recovered),'--exact','--test-threads=1'],recovered,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],recovered)
        harness.run_one('thirty_actual_sixteen_family_compiled_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',base.PREFIX,'--test-threads=1'],products,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],products);q.finish();guard.check(force=True)
        row.update(state='PASS_SIXTEEN_FAMILY_SOURCE_OPERATION_COMPILER30_OWNER6_RETAINED5_NOT_TRUSTED_ROUTE_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=30,distinct_actual_owner_unit_cases=6,
            retained_owner_unit_cases=5,recovered_owner_unit_cases=1,total_executed_cases=31,distinct_component_cases=36,
            original_five_owner_units_reexecuted=False,old50_products_reexecuted=False,original16_parsers_source_security_delivery_and_route_bodies_inverse_verified=True,
            one_borrowed_source_graph_selected_part_parent_maps_original_snapshot_and_operation_compiler=True,
            no_candidate_clone_reimport_matcher_replay_or_invented_owner=True,
            next_work='real_target_registry_route_manifest_and_durable_transaction_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_OWNER_ADMISSION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_OWNER_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
