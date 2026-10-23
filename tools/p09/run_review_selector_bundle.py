"""Same52 test bodies in one binary, original CPU/RAM/time guards, immutable pressure stop kept."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_selector_components as base
harness,shared,c,a,audit=base.harness,base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-review-selector-bundle095.v1.json'
BUNDLE='crates/hwpx-package/tests/review_selector_bundle.rs'
MODULES=('review_selector','review_selector_replacement','source_selector','source_inventory','review_text','review_literal')


def inventory(check):return base.inventory(check)|{BUNDLE}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SELECTOR_BUNDLE_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_SELECTOR_BUNDLE',steps=[],actual_Hangul_or_COM=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        stopped=q.json(base.OUTPUT);c.require(q.snapshots[base.OUTPUT]['sha256']=='1942162a4dbc91d274984125884dc06fe24394682a4040c6541660e89ca78b54'
            and stopped['state']=='FAILED_REVIEW_SELECTOR_COMPONENTS'and stopped['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'
            and stopped['cleanup']and len(stopped['steps'])==1 and 'tests'not in stopped['steps'][0],'ORIGINAL_CPU_PRESSURE_STOP_AND_UNKNOWN_TEST_COMPLETION_PRESERVED')
        old={p['path']:p for p in stopped['source_pins']}
        for name in names-{BUNDLE}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_AND_FIFTY_TWO_ORIGINAL_TEST_BODIES_UNCHANGED')
        previous=q.json(base.prior.OUTPUT);c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='98214dc9224d34ad162616ea8a8184078332147401c2574e5e8cad8177f33c7e','ORIGINAL_PRODUCT_PASS_BASELINE')
        base.inverse(q,{p['path']:p for p in previous['source_pins']})
        expected=set();mapping=[];counts=[]
        for target,module in zip(base.TESTS+base.OLD,MODULES,strict=True):
            tests=base.test_names(q,target);counts.append(len(tests));expected.update(module+'::'+name for name in tests)
            mapping.append(dict(path='crates/hwpx-package/tests/'+target+'.rs',namespace=module,test_count=len(tests)))
        c.require(tuple(counts)==(8,8,12,4,8,12)and len(expected)==52,'EXACT_ORIGINAL_FIFTY_TWO_CASES_NO_FILTER_OR_SKIP')
        text='//! Same52 source cases in one integration binary; original test bodies and guards stay intact.\n'+''.join(
            f'#[path="{target}.rs"] mod {module};\n'for target,module in zip(base.TESTS+base.OLD,MODULES,strict=True))
        c.require(q.text(BUNDLE)==text,'BUNDLE_ONLY_REUSES_SIX_EXISTING_TEST_MODULES')
        old_job=stopped['steps'][0]['owned_job'];observation=stopped['steps'][0]['bounded_output_observation']
        c.require(old_job['cleanup_confirmed']and old_job['owned_tree_empty']and old_job['job_handle_closed']
            and old_job['last_job_accounting']['active_processes']==0 and old_job['limits_readback']['cpu_hard_cap_machine_percent']==6.25
            and observation['phase']=='BUILD_ACTIVITY_OBSERVED'and not observation['observed_harness_started'],'STOP_IN_BUILD_PHASE_WITH_OWNED_JOB_CLOSED_NOT_CAUSAL_ATTRIBUTION')
        row.update(original_pressure_stop_preserved=True,old_job_cpu_seconds=old_job['last_job_accounting']['job_cpu_seconds'],
            stop_had_no_observed_test_harness=True,prior_attempt_test_execution_count_unproven=True,
            cpu_spike_cause_or_defender_cause_proven=False,test_identity_namespace_map=mapping,
            requested_test_binaries_before=6,requested_test_binaries_after=1,production_and_test_bodies_unchanged=True,resource_time_and_52_case_conditions_unchanged=True)
        print(json.dumps(dict(state='REVIEW_SELECTOR_BUNDLE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),unchanged_cases=52,test_binaries=1,policy_unchanged=True)),flush=True)
        harness.run_one('same_fifty_two_cases_one_integration_binary',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','review_selector_bundle','--','--test-threads=1'],expected,guard,audit.environment(),row,observe_capture=base.base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_SELECTOR_BUNDLE_INPUT_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_SELECTOR_BUNDLE_FIFTY_TWO_UNCHANGED_CASES_NOT_STORED_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_review_scope_cases=8,new_selector_literal_cases=8,affected_cases=36,total_executed_cases=52,
            original_review_writer_nfc_protection_and_optional_none_bodies_inverse_verified=True,stored_json_or_native_qualification_added=False,
            next_work='Stored_review_selector_and_literal_window_candidates_with_strict_product_requests')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SELECTOR_BUNDLE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_BUNDLE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
