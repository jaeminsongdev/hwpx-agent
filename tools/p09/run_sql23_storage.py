"""Build one storage probe and run real AEAD + SQL23 coordinator; never repeat old tests."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sql23_job_lifecycle as previous
native,shared,c,a,tools,compact=previous.native,previous.shared,previous.c,previous.a,previous.tools,previous.compact
harness,audit=previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-real-storage-compile290.v1.json'
FAILED='implementation/p09/evidence/p09-361-sql23-real-storage288.v1.json'
FAILED_COMPILE='implementation/p09/evidence/p09-361-sql23-real-storage-recovery289.v1.json'
DRIVER='tools/p09/run_sql23_storage.py'
WORKER='tools/p09/native_postgres_storage.py'
PROBE='crates/product-cli/examples/sql23_storage.rs'
NEW={DRIVER,WORKER,PROBE,'crates/product-cli/examples/sql23_storage/setup.rs','crates/product-cli/examples/sql23_storage/pipeline.rs',FAILED,FAILED_COMPILE}
MANIFEST='crates/product-cli/tests/support/stored_commit_manifest.rs'
EXE='target/debug/examples/sql23_storage.exe'
CODE='implementation/p09/evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json'
SCRATCH='target/p09-sql23-storage-scratch-290'
def inventory(check):
    names=previous.previous.inventory(check)|NEW|{MANIFEST}
    for package in('product-cli','operation-engine','domain-ir','hwpx-package','equation-engine'):
        names.add(f'crates/{package}/Cargo.toml');root=c.ROOT/f'crates/{package}/src'
        c.require(root.is_dir()and not root.is_symlink()and not root.is_junction(),'STORAGE_COMPILE_SOURCE_ROOT')
        for directory,dirs,files in os.walk(root,followlinks=False):
            check()
            for name in dirs:c.require(not(Path(directory)/name).is_symlink()and not(Path(directory)/name).is_junction(),'STORAGE_SOURCE_NOT_REPARSE')
            names|={(Path(directory)/f).relative_to(c.ROOT).as_posix()for f in files if f.endswith('.rs')};c.require(len(names)<=1536,'STORAGE_SOURCE_BOUND')
    return names
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SQL23_STORAGE_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;observations=None;started=time.monotonic();row=dict(state='FAILED_SQL23_REAL_STORAGE',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,
        actual_P09_product_or_Native_execution=False,synthetic_route_scanner_validator_and_bytes=True,parent_retained_ephemeral_test_keys=True,
        system_or_security_settings_changed=False,operational_database_accessed=False,previously_passed_tests_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);last=compact.unpack(q.json(previous.OUTPUT));code=compact.unpack(q.json(CODE))
        failed=compact.unpack(q.json(FAILED));c.require(q.snapshots[FAILED]['sha256']=='108de12adbdcaa58402b556ca5ac65c0d8fb58979e43ea3af3c9246b362e3e54'
            and failed['cleanup']and failed['steps']==[],'EXACT288_OBSERVER_ATTRIBUTE_FAILURE_BEFORE_CARGO_OR_DATABASE_RETAINED')
        frozen={p['path']:p for p in failed['source_pins']}
        for name in NEW-{DRIVER,FAILED,FAILED_COMPILE,PROBE}:q.pin(name);c.require(q.snapshots[name]==frozen[name],'ALL_STORAGE_SETUP_PIPELINE_AND_NATIVE_WORKER_SOURCES_UNCHANGED_SINCE288')
        q.pin(PROBE);text=q.text(PROBE)
        audit.inverse(text.replace('type Result<T,E=Box<dyn Error>>=std::result::Result<T,E>;','type Result<T>=std::result::Result<T,Box<dyn Error>>;')
            .replace('    RevisionRequestContext,RevisionService,RevisionValidationState,','    RevisionRepository,RevisionRequestContext,RevisionService,RevisionValidationState,'),
            frozen[PROBE],'ONLY_NEW_PROBE_RESULT_ALIAS_AND_UNUSED_IMPORT_CORRECTED')
        compilation=compact.unpack(q.json(FAILED_COMPILE));c.require(q.snapshots[FAILED_COMPILE]['sha256']=='a61e26188cf46142604caf4605caa0c9931f8ba02f9ee652ff6da015277a6fb2'
            and compilation['cleanup']and len(compilation['steps'])==1 and compilation['steps'][0]['exit_code']==101
            and compilation['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0107'],'EXACT289_FIXTURE_RESULT_ALIAS_FAILURE_BEFORE_DB_RETAINED')
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='17fc9b845c7d8106e56331f7910c9a703cd65e5dcfd2d561c2184a8213ac1454'
            and last['cleanup']and last['fresh_inputs']==last['final_fresh_hashes']==228,'EXACT286_ACTUAL_JOB_LIFECYCLE_CLOSURE')
        c.require(q.snapshots[CODE]['sha256']=='f7f8d8d21f6b30665222d40672d2bb2ff129441b2210108dea542833377e87b7'and code['cleanup'],'EXACT275_COORDINATOR_COMPILE_SOURCE_CLOSURE')
        old={p['path']:p for p in code['source_pins']};old.update({p['path']:p for p in last['source_pins']})
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW:c.require(name in old and q.snapshots[name]==old[name],'ALL_PREVIOUS_SERVICE_ENGINE_PACKAGE_ROUTE_CRYPTO_SQL_SOURCES_UNCHANGED')
        import native_postgres_storage as candidate
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()and not candidate.OWNED.exists()
            and not(c.ROOT/candidate.OBSERVATION).exists(),'STORAGE_NEW_BUILD_DATABASE_BLOB_AND_OBSERVATION')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        for name in('tools/p09/fixtures/native_postgres_hba.conf','target/p09-native-postgres-18.6-5-278/runtime-manifest.json'):q.pin(name)
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='SQL23_STORAGE_PREFLIGHT',source_inputs=len(q.snapshots),old_tests_replayed=False)),flush=True)
        harness.run_one('compile_sql23_real_storage_probe',[harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example','sql23_storage','--message-format=short'],
            set(),guard,env,row,observe_capture=snapshot)
        c.require(row['steps'][-1]['diagnostics']==[],'STORAGE_PROBE_BUILD_NO_DIAGNOSTICS');q.pin(EXE);env['P09_STORAGE_PROBE_SHA256']=q.snapshots[EXE]['sha256']
        try:result=native.runner.run_owned('actual_disk_AEAD_SQL23_registered_CAS_completion_restart',[sys.executable,str(c.ROOT/WORKER),'--owned-real-storage-campaign'],guard,env,row,300)
        finally:
            if(c.ROOT/candidate.OBSERVATION).is_file():observations=q.json(candidate.OBSERVATION)
        c.require(result['observation_path']==candidate.OBSERVATION and result['observation_sha256']==q.snapshots[candidate.OBSERVATION]['sha256']
            and result['observation_bytes']==q.snapshots[candidate.OBSERVATION]['bytes'],'STORAGE_EXACT_OBSERVATION')
        c.require(observations['state']=='PASS_REAL_DISK_AEAD_SQL23_REGISTERED_CAS_COMPLETION_AND_RESTART_NOT_PRODUCT_OR_P09_GATE'
            and len(observations['probes'])==5 and len(observations['snapshots'])==2 and observations['snapshots'][0]==observations['snapshots'][1]
            and observations['blob_snapshots'][0]==observations['blob_snapshots'][1]and len(observations['blob_snapshots'][0])==6
            and len(observations['postmasters'])==2 and observations['all_owned_postmasters_normal_stop'],'STORAGE_ACTUAL_AEAD_SIX_REGISTERED_CAS_COMPLETE_RESTART_AND_NO_REEXECUTION')
        c.require(not any(scratch.iterdir()),'STORAGE_BUILD_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_REAL_DISK_AEAD_SQL23_REGISTERED_CAS_COMPLETION_RESTART_NOT_PRODUCT_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_disk_AEAD_artifacts=6,actual_SQL23_registered_CAS_and_success_completion=True,actual_wrong_key_denial=True,
            actual_DB_restart_replay_and_readonly_commit_recovery=True,next_work='actual_ack_loss_recovery_negative_boundaries_and_qualified_P09_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'SQL23_STORAGE_FAILURE_NO_RAW_VALUES')
    finally:
        if observations is not None:row.update(actual_database_stage=observations['stage'],last_probe=None if not observations['probes']else observations['probes'][-1])
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'STORAGE_LOSSLESS_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_database_stage','last_probe')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','result','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
