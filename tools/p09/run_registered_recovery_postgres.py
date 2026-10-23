"""One fresh real DB probe for the newly implemented registered read API; no old suites replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_registered_recovery_components as components
shared,c,a,tools,compact,harness,audit=components.shared,components.c,components.a,components.tools,components.compact,components.harness,components.audit
native=components.previous.native
OUTPUT='implementation/p09/evidence/p09-361-registered-recovery-postgres298.v1.json'
DRIVER='tools/p09/run_registered_recovery_postgres.py'
PROBE='crates/product-cli/examples/sql23_storage.rs';PIPE='crates/product-cli/examples/sql23_storage/pipeline.rs';WORKER='tools/p09/native_postgres_storage.py'
CHANGED={PROBE,PIPE,WORKER};NEW={DRIVER};EXE='target/debug/examples/sql23_storage.exe';SCRATCH='target/p09-registered-recovery-db-scratch-298'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGISTERED_DB_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;observations=None;started=time.monotonic();row=dict(state='FAILED_REGISTERED_RECOVERY_DB',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_P09_product_or_Native_execution=False,Native011_executed=False,prior_Native_replayed=False,old_Rust249_or_ack4_tests_replayed=False,
        parent_retained_ephemeral_test_keys=True,synthetic_route_scanner_validator_and_bytes=True,system_or_security_settings_changed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(components.OUTPUT))
        c.require(q.snapshots[components.OUTPUT]['sha256']=='ee60ee3fcb2fe75189fdd1139bc24f91f1fc63d1fab662a8811c41b37b413c71'and passed['cleanup']
            and passed['new_cases']==10 and passed['affected_original_cases']==12,'EXACT297_NEW10_AND_AFFECTED12')
        old={p['path']:p for p in passed['source_pins']}
        for n in CHANGED|NEW:q.pin(n)
        text=q.text(PROBE).replace('hwpx-agent-p09-pg18-storage-298','hwpx-agent-p09-pg18-storage-288')
        audit.inverse(text.replace('"--restart-registered"=>pipeline::restart_registered(),',''),old[PROBE],'ONLY_FIXED_NEW_ROOT_AND_NEW_RECOVERY_MODE_LINK')
        text=q.text(PIPE);at=text.index('pub fn restart_registered()');audit.inverse(text[:at],old[PIPE],'ALL_ORIGINAL_STORAGE_WORKER_SETUP_SUCCESS_AND_OLD_RECOVERY_BODY_UNCHANGED')
        text=q.text(WORKER).replace('hwpx-agent-p09-pg18-storage-298','hwpx-agent-p09-pg18-storage-288').replace('observations-298','observations-288').replace("probe('--restart-registered')","probe('--restart-observe')")
        audit.inverse(text,old[WORKER],'ORIGINAL_OWNED_POSTGRES_LIMITS_CIPHERTEXT_AND_SINGLE_ATTEMPT_ASSERTIONS_UNCHANGED')
        for n in sorted(components.previous.previous.inventory(guard.check)|components.CHANGED|components.NEW|CHANGED|NEW|{components.OLD_TEST,'crates/product-cli/tests/stored_revision_commit.rs'}):
            q.pin(n)
            if n not in CHANGED|NEW:c.require(q.snapshots[n]==old[n],'ALL_QUALIFIED297_PRODUCTION_AND_TEST_INPUTS_UNCHANGED')
        import native_postgres_storage as worker
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'REGISTERED_DB_NEW_OWNED_SCOPE')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                p=Path(value).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        for n in('tools/p09/fixtures/native_postgres_hba.conf','target/p09-native-postgres-18.6-5-278/runtime-manifest.json'):q.pin(n)
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='REGISTERED_DB_PREFLIGHT',source_inputs=len(q.snapshots),prior_suites_replayed=False)),flush=True)
        harness.run_one('compile_new_registered_DB_recovery',[harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example','sql23_storage','--message-format=short'],set(),guard,env,row,observe_capture=snapshot)
        c.require(row['steps'][-1]['diagnostics']==[],'REGISTERED_DB_NO_BUILD_DIAGNOSTICS');q.pin(EXE);env['P09_STORAGE_PROBE_SHA256']=q.snapshots[EXE]['sha256']
        try:result=native.runner.run_owned('actual_registered_receipts_only_restart',[sys.executable,str(c.ROOT/WORKER),'--owned-real-storage-campaign'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observations=q.json(worker.OBSERVATION)
        c.require(result['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']and result['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'REGISTERED_DB_EXACT_OBSERVATION')
        probe=observations['probes'][-1]
        c.require(probe['state']=='PASS_REAL_REGISTERED_RECOVERY_WITHOUT_SAVED_REQUEST_NO_DOMAIN_MUTATIONS'and probe['registered_recovery_checks']==3
            and probe['request_fixture_preserved']and probe['retained_request_file_used']is False and probe['execution_retried']is False
            and observations['snapshots'][0]==observations['snapshots'][1]and observations['blob_snapshots'][0]==observations['blob_snapshots'][1]
            and len(observations['postmasters'])==2 and observations['all_owned_postmasters_normal_stop'],'ACTUAL_NEW_API_WITHOUT_RETAINED_REQUEST_AND_NO_DOMAIN_MUTATIONS')
        c.require(not any(scratch.iterdir()),'REGISTERED_DB_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_REGISTERED_READONLY_RECOVERY3_WITHOUT_RETAINED_REQUEST_NOT_PRODUCT_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_registered_DB_checks=3,next_work='qualified_product_dispatch_and_remaining_negative_boundaries')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'REGISTERED_DB_FAILURE_NO_RAW_VALUES')
    finally:
        if observations is not None:row.update(actual_database_stage=observations['stage'],last_probe=observations['probes'][-1]if observations['probes']else None)
        guard.close();s=guard.samples;row.update(cleanup=guard.cleanup and all(x['cleanup']for x in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=s,
            system_CPU_max=max((x['system_cpu_percent']for x in s),default=None),available_RAM_min_percent=min((x['available_ram_percent']for x in s),default=None))
        if s and all(list(x)==list(s[0])for x in s):
            keys=list(s[0]);rows=[[x[k]for k in keys]for x in s];c.require([dict(zip(keys,x))for x in rows]==s,'REGISTERED_DB_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=rows)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_database_stage','last_probe')},
            'steps':[{k:x.get(k)for k in('stage','exit_code','diagnostics','result','cleanup')}for x in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
