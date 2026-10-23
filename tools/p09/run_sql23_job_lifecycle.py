"""Compile one small new probe, execute genuine SQL23 lifecycle, no old suite/Native replay."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sql23_service_admission as previous
native,shared,c,a,tools,compact=previous.native,previous.shared,previous.c,previous.a,previous.tools,previous.compact
harness,audit=previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-job-lifecycle286.v1.json'
DRIVER='tools/p09/run_sql23_job_lifecycle.py'
WORKER='tools/p09/native_postgres_job_lifecycle.py'
PROBE='crates/revision-service/examples/p09_sql23_jobs.rs'
CHILDREN={'crates/revision-service/examples/p09_sql23_jobs/setup.rs','crates/revision-service/examples/p09_sql23_jobs/negative.rs'}
EXE='target/debug/examples/p09_sql23_jobs.exe'
BASE='implementation/p09/evidence/p09-361-sql23-service-admission284.v1.json'
NEW={DRIVER,WORKER,PROBE}|CHILDREN
SCRATCH='target/p09-sql23-job-scratch-286'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SQL23_JOB_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;observations=None;started=time.monotonic();row=dict(state='FAILED_SQL23_JOB_LIFECYCLE',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,
        actual_blob_AEAD_or_product_execution=False,SQL23_result_CAS_or_completion=False,system_or_security_settings_changed=False,
        operational_database_accessed=False,all_previously_passed249_or_Rust_tests_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);last=compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='9aa1b8178204f93d533e4166b57bd67c779379aff011e5209895d6fbb93cf5e8'
            and last['cleanup']and last['fresh_inputs']==last['final_fresh_hashes']==224,'EXACT284_ADMISSION_SOURCE_CLOSURE')
        old={p['path']:p for p in last['source_pins']}
        for name in sorted(previous.inventory(guard.check)|NEW):
            q.pin(name)
            if name in old:c.require(q.snapshots[name]==old[name],'UNCHANGED_SERVICE_ADMISSION_CRYPTO_SQL_AND_DEPENDENCIES')
        import native_postgres_job_lifecycle as candidate
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()and not candidate.OWNED.exists()
            and not(c.ROOT/candidate.OBSERVATION).exists(),'SQL23_JOB_FRESH_BUILD_DATABASE_OBSERVATION')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        for name in('tools/p09/fixtures/native_postgres_hba.conf','target/p09-native-postgres-18.6-5-278/runtime-manifest.json'):q.pin(name)
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        snapshot=previous.prior_code.core.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='SQL23_JOB_PREFLIGHT',source_inputs=len(q.snapshots),compile_packages3_only=True,old_tests_replayed=False)),flush=True)
        harness.run_one('compile_sql23_job_probe',[harness.CARGO,'build','--offline','--locked','-j','1','-p','revision-service','--example','p09_sql23_jobs','--message-format=short'],
            set(),guard,env,row,observe_capture=snapshot)
        c.require(row['steps'][-1]['diagnostics']==[],'SQL23_JOB_BUILD_NO_DIAGNOSTICS');q.pin(EXE);env['P09_JOB_PROBE_SHA256']=q.snapshots[EXE]['sha256']
        try:result=native.runner.run_owned('actual_sql23_job_lifecycle',[sys.executable,str(c.ROOT/WORKER),'--owned-sql23-job-lifecycle'],guard,env,row,300)
        finally:
            if(c.ROOT/candidate.OBSERVATION).is_file():observations=q.json(candidate.OBSERVATION)
        c.require(result['observation_path']==candidate.OBSERVATION and result['observation_sha256']==q.snapshots[candidate.OBSERVATION]['sha256']
            and result['observation_bytes']==q.snapshots[candidate.OBSERVATION]['bytes'],'SQL23_JOB_EXACT_OBSERVATION')
        c.require(observations['state']=='PASS_ACTUAL_SQL23_WORKER_CLAIM_LEASE_STAGE15_AND_RESTART_NOT_AEAD_CAS_OR_P09_GATE'
            and len(observations['probes'])==3 and len(observations['checks'])==15 and len(observations['snapshots'])==2
            and observations['snapshots'][0]==observations['snapshots'][1]and observations['actual_SQL23_worker_lease']
            and len(observations['postmasters'])==2 and observations['all_owned_postmasters_normal_stop'],'SQL23_JOB_ACTUAL15_SINGLE_ATTEMPT_AND_CLEAN_RESTART')
        c.require(not any(scratch.iterdir()),'SQL23_JOB_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_SQL23_JOB15_AND_RESTART_NOT_AEAD_CAS_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_SQL23_worker_lease=True,actual_job_checks=observations['checks'],actual_job_restart_observed=True,
            next_work='actual_blob_AEAD_stored_intent_registered_CAS_completion_unknown_recovery_and_qualified_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'SQL23_JOB_FAILURE_NO_RAW_VALUES')
    finally:
        if observations is not None:row.update(actual_database_stage=observations['stage'],last_probe=None if not observations['probes']else observations['probes'][-1])
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'SQL23_JOB_LOSSLESS_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_database_stage','last_probe')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','result','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
