"""PG18 portable archive/path models + one resource-owned acquisition/version batch, never DB."""
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_job_coordinator_components as previous
core=previous.core
shared,c,a,tools,compact=core.shared,core.c,core.a,core.tools,core.compact
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-runtime-qualification278.v1.json'
DRIVER='tools/p09/run_native_postgres_runtime_qualification.py'
WORKER='tools/p09/native_postgres_runtime.py'
TEST='tools/p09/tests/test_native_postgres_runtime.py'
LAST='implementation/p09/evidence/p09-361-stored-job-coordinator-doc-recovery277.v1.json'

def run_owned(stage,args,guard,environment,row,seconds):
    step=dict(stage=stage,cleanup=False);row['steps'].append(step);owned=capture=None;started=announcement=time.monotonic()
    try:
        owned=shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[sys.executable],cwd=c.ROOT,checkpoint=guard.check,env=environment)
        capture=shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<seconds,'STOP_NATIVE_POSTGRES_OWNED_COMMAND_DEADLINE')
            try:
                out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();account=owned.observe()
                if time.monotonic()-announcement>=15:
                    print(json.dumps(dict(stage=stage,elapsed=round(time.monotonic()-started,1),system_CPU=guard.samples[-1]['system_cpu_percent'],
                        available_RAM_percent=guard.samples[-1]['available_ram_percent'],job_private_percent=account['peak_job_private_percent'],job_cpu_seconds=account['job_cpu_seconds'])),flush=True)
                    announcement=time.monotonic()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        c.require(not err.strip(),'NATIVE_POSTGRES_WORKER_STDERR_NOT_EMPTY')
        try:result=json.loads(out)
        except json.JSONDecodeError:raise ValueError('NATIVE_POSTGRES_WORKER_CLOSED_JSON_REQUIRED')from None
        step['result']=result;c.require(owned.returncode==0,'NATIVE_POSTGRES_WORKER_FAILED')
        return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NATIVE_POSTGRES_RUNTIME_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None;row=dict(state='FAILED_NATIVE_POSTGRES_RUNTIME_QUALIFICATION',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_database_or_service_started=False,actual_SQL_executed=False,SQL23_applied=False,actual_Docker_or_WSL_started=False,
        system_or_security_settings_changed=False,PostgreSQL_binary_version_only_not_SQL_or_product_qualification=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        last=q.json(LAST);c.require(q.snapshots[LAST]['sha256']=='797dffe3d8535703536d5d99e976976d885693d2f0ceb5b4cc5e7ac04ce3db6d'
            and last['cleanup']and last['fresh_inputs']==last['final_fresh_hashes']==101,'EXACT277_COORDINATOR_AND_DOCUMENT_CLOSURE')
        for path in(DRIVER,WORKER,TEST,'tools/p09/owned_sql_job.py','tools/p09/bounded_process_progress.py',
            'CURRENT_STATE.md','protocol/migrations/p09-stored-revision-jobs-v1.md'):q.pin(path)
        import native_postgres_runtime as runtime
        asset=c.ROOT/runtime.ASSET;scratch=c.ROOT/'target/p09-native-postgres-model-scratch-278'
        parent=c.ROOT/'target';c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
            and not asset.exists()and not scratch.exists()and asset.resolve().is_relative_to(parent.resolve())
            and scratch.resolve().is_relative_to(parent.resolve()),'UNIQUE278_NATIVE_RUNTIME_AND_MODEL_SCRATCH')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch.mkdir();environment=dict(os.environ,PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1',TEMP=str(scratch),TMP=str(scratch))
        models=run_owned('native_pg_runtime_models12',[sys.executable,str(c.ROOT/TEST)],guard,environment,row,60)
        c.require(models==dict(state='PASS_NATIVE_PG_RUNTIME_MODELS12',tests_run=12,failures=[],actual_network_or_database=False),'EXACT12_RUNTIME_MODELS_NO_SKIPS')
        c.require(not any(scratch.iterdir()),'MODEL_SCRATCH_EMPTY_BEFORE_ARCHIVE_ACQUISITION')
        result=run_owned('one_vendor_archive_and_three_version_commands',[sys.executable,str(c.ROOT/WORKER),'--acquire-version-only'],guard,environment,row,300)
        c.require(result['state']=='ACQUIRED_VERSION_ONLY_NOT_DATABASE'and result['actual_database_or_service_started']is False,'PG_VERSION_ONLY_NO_DATABASE')
        manifest_path=runtime.ASSET+'/runtime-manifest.json';c.require(result['manifest_path']==manifest_path,'PG_MANIFEST_OWNED_LOCATION')
        manifest=q.json(manifest_path);c.require(q.snapshots[manifest_path]['sha256']==result['manifest_sha256']and q.snapshots[manifest_path]['bytes']==result['manifest_bytes'],'PG_RUNTIME_MANIFEST_EXACT_HASH')
        c.require(manifest['url']==runtime.URL and manifest['archive_bytes']==runtime.EXPECTED_BYTES and manifest['archive_observed_sha256']==result['archive_observed_sha256']
            and manifest['archive_extract_files']==len(manifest['runtime_pins'])and manifest['actual_SQL_executed']is False
            and manifest['vendor_signed_checksum_available']is False and manifest['https_origin_only_not_vendor_hash_attestation']is True,'PG_ARCHIVE_INVENTORY_NOT_VENDOR_SIGNATURE_OR_DATABASE_PROOF')
        for version in manifest['versions']:
            path=runtime.ASSET+'/pgsql/bin/'+version['binary'];q.pin(path)
            c.require(q.snapshots[path]['sha256']==version['sha256']and runtime.version_line(version['binary'],version['version']),'PG_THREE_BINARIES_FRESH_AND_VERSION_EXACT')
        c.require(len(manifest['versions'])==3 and not any(scratch.iterdir()),'EXACT_THREE_VERSION_ONLY_PROCESSES_AND_EMPTY_MODEL_SCRATCH')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE_POSTGRES18_6_RUNTIME_MODELS12_AND_VERSION3_NOT_DATABASE_SQL_P09_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            runtime_acquisition=result,model_cases=12,versions_checked=3,asset_root=runtime.ASSET,partial_or_original_archives_deleted=False,
            vendor_checksum_qualification=False,actual_database_qualification=False,
            next_work='qualify_owned_native_cluster_auth_loopback_lifecycle_then_execute_actual_SQL23_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NATIVE_POSTGRES_RUNTIME_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'LOSSLESS_NATIVE_PG_RUNTIME_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','result','cleanup','elapsed_seconds')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
