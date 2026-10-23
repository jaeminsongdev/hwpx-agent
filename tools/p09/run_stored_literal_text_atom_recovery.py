"""Six unrun stored atom tests after one test-only fully-qualified permission name repair."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_literal_text_atom_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-literal-text-atom-recovery077.v1.json'
FAILED=base.OUTPUT


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_LITERAL_ATOM_RECOVERY_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_LITERAL_TEXT_ATOM_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(base.PRIOR);c.require(q.snapshots[base.PRIOR]['sha256']=='feb3a50059ad8c85d2c29a1964e378d1e02d48d9749e9362ff5695e2bd24d29b'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==22,'EXACT_TWENTY_TWO_CORE_PASSES_NOT_REEXECUTED')
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='aea8bdc4813d41bffb57bb5972b7c9687d08cfe7a40a21fc56aa5264c2c67bfd'
            and failed['state']=='FAILED_STORED_LITERAL_TEXT_ATOM_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['tests']==[] and any('E0433'in v for v in failed['steps'][0]['diagnostics']),'ORIGINAL_TEST_PERMISSION_NAME_COMPILATION_FAILURE_ZERO_TESTS_PRESERVED')
        initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==initial[name],'NO_PRODUCTION_OR_OTHER_INPUT_CHANGE_AFTER_PERMISSION_TEST_COMPILE_FAILURE')
        text=q.text(base.TEST);current='artifact_service::ArtifactPermission::Read';original='ArtifactPermission::Read'
        c.require(text.count(current)==1,'ONE_TEST_ONLY_FULLY_QUALIFIED_PERMISSION_TYPE')
        base.base.prior.base.prior.prior.base.inverse(text.replace(current,original),initial[base.TEST],'ALL_SIX_TEST_BODIES_EXACT_EXCEPT_PERMISSION_TYPE_QUALIFICATION')
        base.inverse(q,old)
        tests={'actual_import::literal_text_atom_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)}
        c.require(len(tests)==6,'EXACT_SIX_PREVIOUSLY_UNRUN_STORED_ATOM_CASES')
        env=base.base.prior.base.prior.prior.base.environment()
        print(json.dumps(dict(state='STORED_LITERAL_ATOM_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),unrun_cases=6,core_passes_retained=22,only_test_type_name_repaired=True)),flush=True)
        harness.run_one('six_current_stored_literal_atom_candidate_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(tests),'--exact','--test-threads=1'],tests,guard,env,row)
        c.require(base.inventory(guard.check)==names,'FINAL_STORED_LITERAL_ATOM_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_LITERAL_TEXT_ATOM_SIX_NEW_TWENTY_TWO_CORE_RETAINED_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_stored_cases=6,total_executed_cases=6,retained_core_cases=22,
            original_access_source_writer_and_final_head_method_bodies_verified=True,existing_v1_literal_api_and_product_json_unchanged=True,
            current_acl_quarantine_aead_and_three_final_head_boundaries_exercised=True,
            query_or_lowering_repeated_during_retained_output_delivery=False,idempotency_key_claimed=False,
            test_only_permission_name_repaired=True,original_zero_test_compilation_failure_preserved=True,
            product_json_or_command_line_or_server_route_added=False,next_work='Explicit_strict_v2_literal_product_JSON_and_owned_source_handoff')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_LITERAL_ATOM_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORED_LITERAL_ATOM_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
