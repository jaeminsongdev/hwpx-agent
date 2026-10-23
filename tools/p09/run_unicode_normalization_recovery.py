"""Preserve157 compile failure; repair one missing test-fixture module, not production."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_normalization_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-normalization-recovery158.v1.json'
REPAIR='#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;\n'


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_NORMALIZATION_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search022_product_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='fcbc3a339e33875dc8c63230fcb5699ba0bd5e760e4e1c5e284ba9d0facc4000'
            and failed['state']=='FAILED_UNICODE_NORMALIZATION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0432'],
            'EXACT_ORIGINAL_COMPILE_FAILURE_NO_TESTS_PRODUCTION_ERROR_OR_NATIVE_EXECUTION')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_AND_PRIOR_TEST_FIXTURES_UNCHANGED_AFTER157')
        text=q.text(base.TEST);c.require(text.count(REPAIR)==1,'ONE_MISSING_TEST_ONLY_FIXTURE_MODULE')
        audit.inverse(text.replace(REPAIR,''),old[base.TEST],'ENTIRE_NEW_TEST_FILE_UNCHANGED_EXCEPT_MISSING_FIXTURE_IMPORT')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='bc2c563a3074e79bd4d6f7630f99ca5491b2247fbe997ea26ac2cbd66c6fd622','EXACT_PRIOR155_RETAINED')
        base.inverse(q,{p['path']:p for p in baseline['source_pins']});cases=base.expected(q)
        print(json.dumps(dict(state='UNICODE_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,affected_original_cases=57,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_normalization_and_fifty_seven_affected_originals_after_test_import_repair',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','unicode_normalization_focused','--message-format=short','--','--test-threads=1'],
            cases,guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],cases);c.require(base.inventory(guard.check)==names,'FINAL_UNICODE_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_NORMALIZATION_24_NEW_57_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,affected_source_cases=57,total_executed_cases=81,production_unchanged_after157=True,
            original_common_code_and_test_bodies_inverse_verified=True,explicit_four_forms_and_minimal_original_components=True,original_nfc_index_unchanged=True,
            next_work='Current_stored_service_strict_product_request_and_full_SEARCH022_contract_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
