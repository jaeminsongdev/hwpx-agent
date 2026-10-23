"""Real disk AEAD and SQL23 registered CAS/completion, owned cluster only, no Native.

The parent retains ephemeral test keys across fresh Rust processes and DB restart.
That does not qualify production key custody, scanner, validator or product routing.
"""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
from native_postgres_ascii_campaign import copy_exact
ROOT=cluster.ROOT;PARENT=Path('D:/devdata');OWNED=PARENT/'hwpx-agent-p09-pg18-storage-298'
ASSET=PARENT/'hwpx-agent-p09-pg18-ascii-282/runtime'
PROBE=ROOT/'target/debug/examples/sql23_storage.exe'
OBSERVATION='target/p09-sql23-storage-observations-298.json'

def artifact_probe_environment(env,port,rev_password,art_password,mode,windows_keys,aes,hmac):
    if windows_keys:
        env={k:v for k,v in env.items()if not k.startswith('P09_SQL23_')and k not in('P09_STORAGE_AES_HEX','P09_STORAGE_HMAC_HEX')}
    if mode=='--custody-install-keys':
        cluster.require(windows_keys,'PG_STORAGE_INSTALLER_ONLY_FOR_OWNED_WINDOWS_KEYS');return dict(env)
    app=dict(env,P09_SQL23_PORT=str(port),P09_SQL23_REVISION_PASSWORD=rev_password,P09_SQL23_ARTIFACT_PASSWORD=art_password)
    if not windows_keys:app.update(P09_STORAGE_AES_HEX=secrets.token_hex(32)if mode=='--wrong-key'else aes,P09_STORAGE_HMAC_HEX=hmac)
    return app
def campaign(receipt,schema_version=23,after_execute=None,artifact_key_mode='parent_ephemeral'):
    cluster.require(artifact_key_mode in('parent_ephemeral','windows_owned'),'PG_STORAGE_EXPLICIT_ARTIFACT_KEY_MODE')
    windows_keys=artifact_key_mode=='windows_owned'
    cluster.require(type(schema_version)is int and schema_version in(23,24),'PG_STORAGE_EXPLICIT_SCHEMA_SCOPE')
    cluster.require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_STORAGE_WINDOWS_REPO_SCOPE')
    cluster.require(PARENT.is_dir()and not PARENT.is_symlink()and not PARENT.is_junction()and not OWNED.exists()
        and OWNED.resolve().parent==PARENT.resolve()and str(OWNED).isascii(),'PG_STORAGE_FRESH_ASCII_OWNER')
    cluster.require(PROBE.is_file()and not PROBE.is_symlink()and not PROBE.is_junction()
        and cluster.runtime.sha_file(PROBE)==os.environ.get('P09_STORAGE_PROBE_SHA256'),'PG_STORAGE_EXACT_COMPILED_PROBE')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    cluster.require(cluster.runtime.sha_file(ROOT/cluster.MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_STORAGE_RUNTIME_MANIFEST')
    manifest=json.loads((ROOT/cluster.MANIFEST).read_text(encoding='utf-8'))
    def runtime_pins():
        for pin in manifest['runtime_pins']:
            path=ASSET/pin['path'];cluster.require(path.is_file()and not path.is_symlink()and not path.is_junction()
                and path.stat().st_size==pin['bytes']and cluster.runtime.sha_file(path)==pin['sha256'],'PG_STORAGE_RUNTIME_BYTES')
    runtime_pins();OWNED.mkdir();root=OWNED/'cluster';root.mkdir();data=root/'data';hba=OWNED/'native_postgres_hba.conf';original=ROOT/cluster.HBA
    copy_exact(original,hba,cluster.runtime.sha_file(original),original.stat().st_size)
    binary=ASSET/'pgsql/bin';cluster.CLUSTER=str(root);cluster.HBA=str(hba)
    cluster.SETTINGS.update(io_method='sync',max_wal_senders='0',max_logical_replication_workers='0',max_parallel_workers_per_gather='0',max_parallel_maintenance_workers='0')
    env=cluster.runtime.clean_environment(binary);password,art_password,rev_password=[secrets.token_hex(32)for _ in range(3)]
    aes,hmac=[secrets.token_hex(32)for _ in range(2)]if not windows_keys else(None,None)
    if windows_keys:
        cluster.require(re.fullmatch('[0-9a-f]{32}',os.environ.get('P09_OWNED_ARTIFACT_CUSTODY_NONCE',''))is not None,'PG_STORAGE_OWNED_CUSTODY_NONCE_REQUIRED')
        env={k:v for k,v in env.items()if not k.startswith('P09_SQL23_')and k not in('P09_STORAGE_AES_HEX','P09_STORAGE_HMAC_HEX')}
    process=capture=None
    try:
        receipt['stage']='fresh_storage_cluster_init';cluster.invoke(cluster.init_args(binary,data),env,receipt['stage'],receipt,timeout=60)
        cluster.invoke(cluster.bootstrap_args(binary,data),env,'fresh_storage_admin_password',receipt,f"ALTER ROLE {cluster.USER} PASSWORD '{password}';\n",timeout=15)
        admin=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        receipt['loopback_port']=port
        def sql(text,label):
            receipt['stage']=label;_,out=cluster.invoke(cluster.psql_args(binary,port),admin,label,receipt,text,timeout=30);return out.strip()
        def probe(mode):
            receipt['stage']=mode
            app=artifact_probe_environment(env,port,rev_password,art_password,mode,windows_keys,aes,hmac)
            if mode in('--fixture','--seed'):app.update(P09_SQL23_ADMIN_USER=cluster.USER,P09_SQL23_ADMIN_PASSWORD=password)
            code,out=cluster.invoke([str(PROBE),mode],app,'storage'+mode,receipt,timeout=45,check=False)
            try:result=json.loads(out)
            except json.JSONDecodeError:raise ValueError('PG_STORAGE_PROBE_JSON_REQUIRED')from None
            receipt['probes'].append(result);cluster.require(code==0 and result['state'].startswith('PASS_'),'PG_STORAGE_PROBE_FAILED');return result
        def snapshot(label):
            result=json.loads(sql("SELECT json_build_object('artifacts',(SELECT count(*) FROM hwpx_agent.artifacts),"
                "'available',(SELECT count(*) FROM hwpx_agent.artifacts WHERE storage_state='available' AND validation_state='verified'),"
                "'jobs',(SELECT count(*) FROM hwpx_agent.jobs),'succeeded_jobs',(SELECT count(*) FROM hwpx_agent.jobs WHERE state='succeeded'),"
                "'successful_records',(SELECT count(*) FROM hwpx_agent.idempotency_records WHERE state='terminal_success' AND attempt_count=1 AND last_fencing_token=1),"
                "'attempts',(SELECT count(*) FROM hwpx_agent.job_attempts),'authorizations',(SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations),"
                "'intents',(SELECT count(*) FROM hwpx_agent.stored_revision_commit_intents),'revisions',(SELECT count(*) FROM hwpx_agent.revisions),"
                "'seals',(SELECT count(*) FROM hwpx_agent.revision_graph_seals WHERE seal_kind='service_v1'),'head',(SELECT head_generation FROM hwpx_agent.branches));\n",label))
            expected=dict(artifacts=6,available=6,jobs=2,succeeded_jobs=2,successful_records=2,attempts=2,authorizations=0,intents=1,revisions=2,seals=2,head=2)
            cluster.require(result==expected,'PG_STORAGE_EXACT_COMPLETED_SINGLE_ATTEMPTS_AND_SEALED_HEAD');receipt['snapshots'].append(result)
        def blobs(label):
            rows=json.loads(sql("SELECT json_agg(json_build_object('object_key',object_key,'sha256',ciphertext_sha256::text,'plaintext_bytes',size_bytes)) FROM hwpx_agent.artifacts;\n",label))
            cluster.require(isinstance(rows,list)and len(rows)==6,'PG_STORAGE_SIX_REAL_ENCRYPTED_ARTIFACTS');pins=[]
            for row in rows:
                key=row['object_key'];cluster.require(isinstance(key,str)and re.fullmatch(r'artifacts/v1/[0-9a-f]{32}/[a-z_]+/available/[0-9a-f]{64}\.aes256gcm',key),'PG_STORAGE_CLOSED_BLOB_KEY')
                path=OWNED/'blobs/output'/key
                cluster.require(path.resolve().is_relative_to((OWNED/'blobs').resolve()),'PG_STORAGE_BLOB_SCOPE')
                for current in(path,*path.parents):
                    cluster.require(not current.is_symlink()and not current.is_junction(),'PG_STORAGE_BLOB_NOT_REPARSE')
                    if current==OWNED:break
                cluster.require(path.is_file()and path.stat().st_size==row['plaintext_bytes']+16 and cluster.runtime.sha_file(path)==row['sha256'],'PG_STORAGE_ACTUAL_DISK_CIPHERTEXT_BINDING')
                pins.append(dict(path=path.relative_to(OWNED).as_posix(),bytes=path.stat().st_size,sha256=row['sha256']))
            pins.sort(key=lambda p:p['path']);receipt['blob_snapshots'].append(pins)
        process,capture=cluster.start(binary,data,port,env,receipt);receipt['actual_owned_postmaster_started']=True
        cluster.ready(process,capture,binary,port,env,receipt);cluster.attest_cluster(binary,data,port,admin,receipt,'storage_before_fixture')
        fixture=probe('--fixture');cluster.require(fixture['migrations']==schema_version and fixture['metadata_artifacts_seeded']==0,'PG_STORAGE_NO_SYNTHETIC_ARTIFACT_ROWS')
        receipt['actual_SQL23_applied_in_owned_test_database']=True
        sql(f"ALTER ROLE p09_artifact_284 PASSWORD '{art_password}'; ALTER ROLE p09_revision_284 PASSWORD '{rev_password}';\n",'fresh_storage_ephemeral_role_passwords')
        if windows_keys:
            installed=probe('--custody-install-keys')
            cluster.require(installed['credential_entries']==3 and installed['keys_in_output_or_environment']is False and installed['database_credentials_received']is False,'PG_STORAGE_CLOSED_INSTALLER_EXIT_NO_KEY_EXPORT')
        probe('--seed');probe('--execute')
        if after_execute is not None:after_execute(sql,probe)
        snapshot('completed_before_restart');blobs('ciphertext_before_restart')
        probe('--wrong-key');cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
        cluster.attest_cluster(binary,data,port,admin,receipt,'storage_after_restart');probe('--restart-registered')
        snapshot('completed_after_restart');blobs('ciphertext_after_restart');cluster.require(receipt['blob_snapshots'][0]==receipt['blob_snapshots'][1],'PG_STORAGE_CIPHERTEXT_UNCHANGED_ACROSS_RESTART')
        cluster.catalogue(binary,port,admin,cluster.migration_rows(schema_version),receipt,'storage_final_catalogue_selected_schema')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        runtime_pins();cluster.require(cluster.runtime.sha_file(PROBE)==os.environ.get('P09_STORAGE_PROBE_SHA256'),'PG_STORAGE_FINAL_PROBE_BYTES')
        receipt.update(state='PASS_REAL_DISK_AEAD_SQL23_REGISTERED_CAS_COMPLETION_AND_RESTART_NOT_PRODUCT_OR_P09_GATE',stage='finished',
            actual_SQL23_registered_CAS_and_success_completion=True,actual_disk_AEAD_readback=True,all_owned_postmasters_normal_stop=True)
    finally:
        password=art_password=rev_password=aes=hmac=None
        if process is not None:
            if process.poll()is None:
                try:cluster.stop(process,capture,binary,data,env,receipt)
                except(ValueError,OSError,subprocess.SubprocessError):
                    process.kill();process.wait(timeout=2);receipt['normal_stop_failed_job_teardown_required']=True
                    if capture is not None:capture.close()
            elif capture is not None:capture.close()
if __name__=='__main__':
    receipt=dict(state='FAILED_SQL23_REAL_STORAGE',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,synthetic_route_scanner_validator_and_bytes=True,
        parent_retained_ephemeral_test_keys=True,operational_database_accessed=False)
    try:cluster.require(sys.argv[1:]==['--owned-real-storage-campaign'],'PG_STORAGE_CLOSED_WORKER_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_STORAGE_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();cluster.require(len(payload)<=262144,'PG_STORAGE_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_STORAGE_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
