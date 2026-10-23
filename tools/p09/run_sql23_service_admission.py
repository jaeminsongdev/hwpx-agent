"""Build one small Rust probe, then actual role admission/RLS/faults in an owned ASCII DB."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_native_postgres_cluster_qualification as native
import run_stored_job_coordinator_components as prior_code
shared,c,a,tools,compact=native.shared,native.c,native.a,native.tools,native.compact
harness,audit=prior_code.harness,prior_code.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-service-admission284.v1.json'
DRIVER='tools/p09/run_sql23_service_admission.py'
WORKER='tools/p09/native_postgres_role_admission.py'
PROBE='crates/revision-service/examples/p09_sql23_admission.rs'
FIXTURE='tools/p09/fixtures/sql23_service_roles.sql'
SEED='tools/p09/fixtures/postgres_revision_adapter.sql'
EXE='target/debug/examples/p09_sql23_admission.exe'
DOC_BASE='implementation/p09/evidence/p09-361-native-postgres-progress-sync283.v1.json'
CODE_BASE='implementation/p09/evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json'
SCRATCH='target/p09-sql23-admission-scratch-284'
NEW={DRIVER,WORKER,PROBE,FIXTURE}
def inventory(check):
    names={'Cargo.toml','Cargo.lock','rust-toolchain.toml',SEED}|NEW
    for package in('artifact-service','revision-service','foundation'):
        names.add(f'crates/{package}/Cargo.toml');root=c.ROOT/f'crates/{package}/src'
        c.require(root.is_dir()and not root.is_symlink()and not root.is_junction(),'SQL23_SERVICE_COMPILE_ROOT')
        for directory,dirs,files in os.walk(root,followlinks=False):
            check()
            for name in dirs:c.require(not(Path(directory)/name).is_symlink()and not(Path(directory)/name).is_junction(),'SQL23_COMPILE_SOURCE_NOT_LINKED')
            names|={(Path(directory)/f).relative_to(c.ROOT).as_posix()for f in files if f.endswith('.rs')}
            c.require(len(names)<=512,'SQL23_SERVICE_SOURCE_INVENTORY_BOUND')
    names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
    return names
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SERVICE_ADMISSION_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();observations=None;row=dict(state='FAILED_SQL23_SERVICE_ADMISSION',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_worker_or_registered_CAS=False,actual_product_execution=False,actual_Docker_WSL_or_service_started=False,
        system_or_security_settings_changed=False,all_previously_passed249_or_Rust_tests_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);docs=q.json(DOC_BASE)
        c.require(q.snapshots[DOC_BASE]['sha256']=='c8a8c7e3e39091f3ea396edacdc3536d307e47962a6dcebc5af7c1f8166f8420'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==187,'EXACT283_ACTUAL_SQL23_RESTART_DOC_CLOSURE')
        code=compact.unpack(q.json(CODE_BASE));c.require(q.snapshots[CODE_BASE]['sha256']=='f7f8d8d21f6b30665222d40672d2bb2ff129441b2210108dea542833377e87b7'
            and code['cleanup'],'EXACT275_SERVICE_IMPLEMENTATION_SOURCE_CLOSURE')
        old={p['path']:p for p in code['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name in old:c.require(q.snapshots[name]==old[name],'ALL_EXISTING_COMPILED_SERVICE_CRYPTO_SQL_AND_DEPENDENCY_SOURCES_UNCHANGED')
        import native_postgres_role_admission as candidate
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()and not candidate.OWNED.exists()
            and not(c.ROOT/candidate.OBSERVATION).exists()and candidate.OWNED.parent==candidate.PARENT and str(candidate.OWNED).isascii(),'FRESH284_BUILD_TEMP_DATABASE_AND_OBSERVATION')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        for name in('tools/p09/fixtures/native_postgres_hba.conf','target/p09-native-postgres-18.6-5-278/runtime-manifest.json'):q.pin(name)
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        snapshot=prior_code.core.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='SQL23_ROLE_PREFLIGHT',source_inputs=len(q.snapshots),compile_packages3_only=True,old_tests_replayed=False)),flush=True)
        harness.run_one('compile_sql23_admission_probe',[harness.CARGO,'build','--offline','--locked','-j','1','-p','revision-service','--example','p09_sql23_admission','--message-format=short'],
            set(),guard,env,row,observe_capture=snapshot)
        c.require(row['steps'][-1]['diagnostics']==[],'PROBE_BUILD_NO_DIAGNOSTICS');q.pin(EXE);env['P09_ROLE_PROBE_SHA256']=q.snapshots[EXE]['sha256']
        try:
            result=native.runner.run_owned('actual_sql23_role_admission',[sys.executable,str(c.ROOT/WORKER),'--owned-sql23-role-admission'],guard,env,row,300)
        finally:
            if(c.ROOT/candidate.OBSERVATION).is_file():observations=q.json(candidate.OBSERVATION)
        c.require(result['observation_path']==candidate.OBSERVATION and q.snapshots[candidate.OBSERVATION]['sha256']==result['observation_sha256']
            and q.snapshots[candidate.OBSERVATION]['bytes']==result['observation_bytes'],'EXACT_OWNED_NATIVE_OBSERVATION_BYTES')
        c.require(observations['state']=='PASS_ACTUAL_SQL23_ARTIFACT_REVISION_ADMISSION_SCOPE6_AND_FAULTS15_NOT_JOB_CAS_OR_P09_GATE'
            and len(observations['probes'])==35 and len(observations['faults_verified'])==15 and observations['actual_metadata_scope_checks']==6
            and observations['all_owned_postmasters_normal_stop']and observations['actual_product_worker_or_CAS']is False,'ACTUAL_BOTH_PROFILES_SCOPE6_FAULT15_RESTORATIONS_NOT_JOB_OR_PRODUCT')
        c.require(not any(scratch.iterdir()),'SQL23_BUILD_AND_PROBE_TEMP_SCRATCH_EMPTY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_SQL23_SERVICE_ADMISSION_SCOPE6_FAULT15_NOT_JOB_CAS_P09_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_profile_probe_calls=35,actual_fault_cases=15,actual_metadata_scope_checks=6,
            next_work='genuine_worker_and_SQL23_job_claim_lease_registered_CAS_completion_unknown_restart_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SQL23_ROLE_CAMPAIGN_FAILURE_NO_RAW_VALUES')
    finally:
        if observations is not None:row.update(actual_database_stage=observations['stage'],last_probe=None if not observations['probes']else observations['probes'][-1],
            actual_owned_postmaster_started=observations['actual_owned_postmaster_started'],actual_SQL23_applied_in_owned_test_database=observations['actual_SQL23_applied_in_owned_test_database'])
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'LOSSLESS_SQL23_ROLE_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_database_stage','last_probe')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','bounded_output_observation','result','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
