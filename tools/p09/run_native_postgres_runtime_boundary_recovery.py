"""Preserve278 two model failures/no network; fix raw ZIP names and complete file-parent collisions."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_native_postgres_runtime_qualification as origin
shared,c,a,tools,compact=origin.shared,origin.c,origin.a,origin.tools,origin.compact
audit=origin.core.audit
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-runtime-boundary-recovery279.v1.json'
DRIVER='tools/p09/run_native_postgres_runtime_boundary_recovery.py'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PG_BOUNDARY_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None;row=dict(state='FAILED_NATIVE_POSTGRES_RUNTIME_BOUNDARY_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_database_or_service_started=False,actual_SQL_executed=False,SQL23_applied=False,actual_Docker_or_WSL_started=False,
        system_or_security_settings_changed=False,PostgreSQL_binary_version_only_not_SQL_or_product_qualification=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(origin.OUTPUT))
        c.require(q.snapshots[origin.OUTPUT]['sha256']=='9d6bafa0c489db2114d6eb045005213443fd8e3b94d98ca1cee7c11d19587c3b'
            and failed['cleanup']and len(failed['steps'])==1 and failed['steps'][0]['result']['tests_run']==12
            and len(failed['steps'][0]['result']['failures'])==2,'ORIGINAL278_TWO_MODEL_FAILURES_NO_NETWORK_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for path in(origin.WORKER,origin.TEST,DRIVER):q.pin(path)
        worker=q.text(origin.WORKER)
        for after,before in[
            ("    name=info.orig_filename\n    require(name==info.filename,'PG_ARCHIVE_NORMALIZED_NAME_OR_NUL')\n","    name=info.filename\n"),
            ('    seen=set();files=set();selected=[];total=0\n','    seen=set();selected=[];total=0\n'),
            ('        if not info.is_dir():files.add(key)\n',''),('    folded_files=files\n','    folded_files={x.casefold()for x in paths}\n')]:
            c.require(worker.count(after)==1,'EXACT_RAW_NAME_AND_ALL_FILE_PARENT_FIX');worker=worker.replace(after,before)
        audit.inverse(worker,old[origin.WORKER],'ALL_OTHER_VENDOR_BYTE_QUOTAS_EXTRACTION_VERSION_ONLY_AND_NO_DB_LOGIC_UNCHANGED')
        text=q.text(origin.TEST);after=",'pgsql/bin/x\\0hidden'";c.require(text.count(after)==1,'ADDITIONAL_RAW_NUL_NEGATIVE_CASE')
        audit.inverse(text.replace(after,''),old[origin.TEST],'ALL_PREVIOUS_MODEL_TEST_BODIES_AND_ORIGINAL_FAILURE_CASES_RETAINED')
        for path,pin in old.items():
            q.pin(path)
            if path not in(origin.WORKER,origin.TEST):c.require(q.snapshots[path]==pin,'ALL_OTHER_RUNNER_GUARDS_CODE_AND_PRODUCT_STATE_UNCHANGED')
        import native_postgres_runtime as runtime
        asset=c.ROOT/runtime.ASSET;scratch=c.ROOT/'target/p09-native-postgres-model-scratch-279';parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not asset.exists()and not scratch.exists()
            and asset.resolve().is_relative_to(parent.resolve())and scratch.resolve().is_relative_to(parent.resolve()),'FRESH279_SCRATCH_AND_NEVER_CREATED278_ASSET')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch.mkdir();environment=dict(os.environ,PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1',TEMP=str(scratch),TMP=str(scratch))
        models=origin.run_owned('repaired_archive_models12',[sys.executable,str(c.ROOT/origin.TEST)],guard,environment,row,60)
        c.require(models==dict(state='PASS_NATIVE_PG_RUNTIME_MODELS12',tests_run=12,failures=[],actual_network_or_database=False),'EXACT12_REPAIRED_ARCHIVE_MODELS')
        c.require(not any(scratch.iterdir()),'MODEL_SCRATCH_EMPTY_BEFORE_NETWORK')
        result=origin.run_owned('one_vendor_archive_and_three_version_commands',[sys.executable,str(c.ROOT/origin.WORKER),'--acquire-version-only'],guard,environment,row,300)
        c.require(result['state']=='ACQUIRED_VERSION_ONLY_NOT_DATABASE'and result['actual_database_or_service_started']is False,'PG_VERSION_ONLY_NO_DATABASE')
        manifest_path=runtime.ASSET+'/runtime-manifest.json';c.require(result['manifest_path']==manifest_path,'PG_MANIFEST_OWNED_LOCATION')
        manifest=q.json(manifest_path);c.require(q.snapshots[manifest_path]['sha256']==result['manifest_sha256']and q.snapshots[manifest_path]['bytes']==result['manifest_bytes'],'PG_RUNTIME_MANIFEST_EXACT_HASH')
        c.require(manifest['url']==runtime.URL and manifest['archive_bytes']==runtime.EXPECTED_BYTES and manifest['archive_observed_sha256']==result['archive_observed_sha256']
            and manifest['archive_extract_files']==len(manifest['runtime_pins'])and manifest['actual_SQL_executed']is False
            and manifest['vendor_signed_checksum_available']is False and manifest['https_origin_only_not_vendor_hash_attestation']is True,'PG_INVENTORY_NOT_VENDOR_SIGNATURE_OR_DATABASE_PROOF')
        for version in manifest['versions']:
            path=runtime.ASSET+'/pgsql/bin/'+version['binary'];q.pin(path)
            c.require(q.snapshots[path]['sha256']==version['sha256']and runtime.version_line(version['binary'],version['version']),'PG_THREE_BINARIES_FRESH_VERSION_EXACT')
        c.require(len(manifest['versions'])==3 and not any(scratch.iterdir()),'THREE_VERSION_ONLY_PROCESSES_AND_EMPTY_SCRATCH')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE_POSTGRES18_6_RUNTIME_MODELS12_AND_VERSION3_NOT_DATABASE_SQL_P09_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            runtime_acquisition=result,model_cases=12,versions_checked=3,asset_root=runtime.ASSET,partial_or_original_archives_deleted=False,
            vendor_checksum_qualification=False,actual_database_qualification=False,
            next_work='qualify_owned_native_cluster_auth_loopback_lifecycle_then_execute_actual_SQL23_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PG_RUNTIME_BOUNDARY_RECOVERY_FAILURE_NO_RAW_VALUES')
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
