"""One new-test coordinate type fix, same52 bundled cases and unchanged production/guards."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_selector_bundle as prior
base=prior.base
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-review-selector-recovery096.v1.json'
TEST='crates/hwpx-package/tests/document_import_review_selector.rs'
FIXED='assert_eq!(found.result().matches()[0].pieces[0].start_scalar,u32::try_from(scalar)?);'
ORIGINAL='assert_eq!(found.result().matches()[0].pieces[0].start_scalar,scalar);'


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SELECTOR_RECOVERY_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_SELECTOR_RECOVERY',steps=[],actual_Hangul_or_COM=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=prior.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='b742c982f04c1b6cb6a6c7a3082997512033c2d7e91b68ce9915dc48ac520bc5'
            and failed['state']=='FAILED_REVIEW_SELECTOR_BUNDLE'and failed['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED'and failed['cleanup']
            and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['tests']==[],'ORIGINAL_BUNDLE_COMPILER_FAILURE_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_OTHER_TESTS_BUNDLE_AND_INPUTS_UNCHANGED')
        text=q.text(TEST);c.require(text.count(FIXED)==1 and ORIGINAL not in text,'ONE_CHECKED_NEW_TEST_SCALAR_TYPE_CONVERSION')
        audit.inverse(text.replace(FIXED,ORIGINAL),old[TEST],'WHOLE_TEST_FILE_EXACT_INVERSE_EXCEPT_U32_USIZE_ASSERTION')
        stopped=q.json(base.OUTPUT);c.require(q.snapshots[base.OUTPUT]['sha256']=='1942162a4dbc91d274984125884dc06fe24394682a4040c6541660e89ca78b54'
            and stopped['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'and stopped['cleanup'],'ORIGINAL_CPU_STOP_NOT_RELABELED')
        previous=q.json(base.prior.OUTPUT);c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='98214dc9224d34ad162616ea8a8184078332147401c2574e5e8cad8177f33c7e','EXACT_PREVIOUS_PRODUCT_BASELINE')
        base.inverse(q,{p['path']:p for p in previous['source_pins']})
        expected=set();counts=[];mapping=[]
        for target,module in zip(base.TESTS+base.OLD,prior.MODULES,strict=True):
            tests=base.test_names(q,target);counts.append(len(tests));expected.update(module+'::'+name for name in tests)
            mapping.append(dict(path='crates/hwpx-package/tests/'+target+'.rs',namespace=module,test_count=len(tests)))
        c.require(tuple(counts)==(8,8,12,4,8,12)and len(expected)==52,'EXACT_FIFTY_TWO_ORIGINAL_CASES_UNFILTERED')
        row.update(original_pressure_and_compiler_failures_preserved=True,only_test_coordinate_type_assertion_changed=True,
            production_and_resource_policy_unchanged=True,test_identity_namespace_map=mapping,
            cpu_spike_cause_or_defender_cause_proven=False,requested_test_binaries_before=6,requested_test_binaries_after=1)
        print(json.dumps(dict(state='REVIEW_SELECTOR_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),cases=52,one_test_type_fix=True,production_unchanged=True)),flush=True)
        harness.run_one('same_fifty_two_bundled_cases_after_one_test_type_fix',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','review_selector_bundle','--','--test-threads=1'],expected,guard,audit.environment(),row,observe_capture=base.base.prior.prior.snapshot)
        c.require(prior.inventory(guard.check)==names,'FINAL_REVIEW_SELECTOR_RECOVERY_INPUT_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_SELECTOR_RECOVERY_SIXTEEN_NEW_THIRTY_SIX_AFFECTED_NOT_STORED_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_review_scope_cases=8,new_selector_literal_cases=8,affected_cases=36,total_executed_cases=52,
            original_compiler_review_protection_and_none_bodies_inverse_verified=True,stored_json_or_native_qualification_added=False,
            next_work='Stored_review_selector_and_literal_window_candidates_with_strict_product_requests')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SELECTOR_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SELECTOR_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
