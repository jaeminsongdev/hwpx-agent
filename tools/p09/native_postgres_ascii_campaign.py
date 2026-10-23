"""ASCII-only owned copy/cluster comparison for initdb's observed UTF8 path failure.

Keep the original vendor ZIP, verified runtime, failed280/281 data and all product inputs.
Only this fresh explicit D:/devdata child is written. No junction/subst/locale/security change.
"""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
ROOT=cluster.ROOT
PARENT=Path('D:/devdata')
OWNED=PARENT/'hwpx-agent-p09-pg18-ascii-282'
def copy_exact(source,destination,sha,size):
    cluster.require(source.is_file()and not source.is_symlink()and not source.is_junction()and source.stat().st_size==size
        and cluster.runtime.sha_file(source)==sha and not destination.exists(),'PG_ASCII_COPY_SOURCE_AND_FRESH_DESTINATION')
    destination.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
    with source.open('rb')as src,destination.open('xb')as dst:
        for block in iter(lambda:src.read(1048576),b''):
            count+=len(block);cluster.require(count<=size,'PG_ASCII_COPY_BYTE_CAP');h.update(block);dst.write(block)
    cluster.require(count==size and h.hexdigest()==sha and cluster.runtime.sha_file(destination)==sha,'PG_ASCII_COPY_EXACT_CONTENT')
def campaign(receipt):
    cluster.require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_ASCII_WORKER_WINDOWS_SCOPE')
    cluster.require(PARENT.is_dir()and not PARENT.is_symlink()and not PARENT.is_junction()and not OWNED.exists()
        and OWNED.resolve().parent==PARENT.resolve()and str(OWNED).isascii(),'PG_ASCII_NEW_EXPLICIT_DEVDATA_CHILD')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    manifest_path=ROOT/cluster.MANIFEST
    cluster.require(cluster.runtime.sha_file(manifest_path)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_ASCII_EXACT279_RUNTIME_MANIFEST')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'));OWNED.mkdir();asset=OWNED/'runtime';asset.mkdir()
    for pin in manifest['runtime_pins']:
        # Original archive names were fully checked before extraction; still recheck path containment.
        source=ROOT/cluster.runtime.ASSET/pin['path'];destination=asset/pin['path']
        cluster.require(destination.resolve().is_relative_to(asset.resolve()),'PG_ASCII_COPIED_RUNTIME_CONTAINMENT')
        copy_exact(source,destination,pin['sha256'],pin['bytes'])
    original_hba=ROOT/cluster.HBA;hba=OWNED/'native_postgres_hba.conf';hba_sha=cluster.runtime.sha_file(original_hba)
    copy_exact(original_hba,hba,hba_sha,original_hba.stat().st_size)
    receipt.update(runtime_files_copied=len(manifest['runtime_pins']),runtime_bytes_copied=sum(p['bytes']for p in manifest['runtime_pins']),
        original_runtime_and_failures_preserved=True,auth_fixture_sha256=hba_sha)
    binary=asset/'pgsql/bin';root=OWNED/'cluster';data=root/'data';root.mkdir()
    cluster.CLUSTER=str(root);cluster.HBA=str(hba)
    # Child-local native PG settings only. Synchronous I/O avoids unnecessary PG18 I/O workers.
    cluster.SETTINGS.update(io_method='sync',max_wal_senders='0',max_logical_replication_workers='0',
        max_parallel_workers_per_gather='0',max_parallel_maintenance_workers='0')
    rows=cluster.migration_rows();receipt['migration_inputs']=[{k:v for k,v in r.items()if k!='text'}for r in rows]
    env=cluster.runtime.clean_environment(binary);password=secrets.token_hex(32);process=capture=None
    try:
        receipt['stage']='ascii_initdb_new_reject_cluster'
        cluster.invoke(cluster.init_args(binary,data),env,receipt['stage'],receipt,timeout=60)
        receipt['initdb_ascii_succeeded']=True;receipt['stage']='ascii_ephemeral_credential_bootstrap'
        cluster.invoke(cluster.bootstrap_args(binary,data),env,receipt['stage'],receipt,
            input_text=f"ALTER ROLE {cluster.USER} PASSWORD '{password}';\n",timeout=15)
        client_env=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reservation:
            reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
        receipt['loopback_port']=port;receipt['stage']='ascii_first_owned_start'
        process,capture=cluster.start(binary,data,port,env,receipt);receipt['actual_owned_postmaster_started']=True
        cluster.ready(process,capture,binary,port,env,receipt);cluster.attest_cluster(binary,data,port,client_env,receipt,'ascii_attest_before_migrations')
        for number,row in enumerate(rows,1):
            receipt['stage']=f'apply_migration_{number:04}'
            cluster.require(cluster.runtime.sha_file(ROOT/row['path'])==row['sha256'],'PG_ASCII_MIGRATION_FRESH_BYTES')
            cluster.invoke(cluster.psql_args(binary,port),client_env,receipt['stage'],receipt,"SELECT set_config('hwpx_agent.migration_sha256','"+row['sha256']+"',false);\n"+row['text'],timeout=30)
            receipt['migrations_applied'].append(number)
            if number==23:receipt['actual_SQL23_applied_in_owned_test_database']=True
        cluster.catalogue(binary,port,client_env,rows,receipt,'ascii_catalogue_before_restart')
        marker=hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        cluster.invoke(cluster.psql_args(binary,port),client_env,'ascii_create_restart_marker',receipt,
            "CREATE SCHEMA p09_runtime_probe; CREATE TABLE p09_runtime_probe.restart_marker(value text NOT NULL); INSERT INTO p09_runtime_probe.restart_marker VALUES('"+marker+"');\n")
        receipt['stage']='ascii_clean_stop_and_restart';cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
        cluster.attest_cluster(binary,data,port,client_env,receipt,'ascii_attest_after_restart');cluster.catalogue(binary,port,client_env,rows,receipt,'ascii_catalogue_after_restart')
        _,out=cluster.invoke(cluster.psql_args(binary,port),client_env,'ascii_read_restart_marker',receipt,'SELECT value FROM p09_runtime_probe.restart_marker;\n')
        cluster.require(out.strip()==marker,'PG_ASCII_RESTART_MARKER_EXACT');receipt['restart_marker_sha256']=marker;receipt['normal_restart_verified']=True
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        for pin in manifest['runtime_pins']:
            cluster.require(cluster.runtime.sha_file(asset/pin['path'])==pin['sha256']and cluster.runtime.sha_file(ROOT/cluster.runtime.ASSET/pin['path'])==pin['sha256'],'PG_ASCII_ORIGINAL_AND_COPY_FINAL_BYTES')
        for row in rows:cluster.require(cluster.runtime.sha_file(ROOT/row['path'])==row['sha256'],'PG_ASCII_FINAL_MIGRATION_BYTES')
        receipt.update(state='PASS_ASCII_OWNED_PG18_6_MIGRATIONS23_CATALOGUE_RESTART_NOT_APPLICATION_JOB_OR_PRODUCT',stage='finished',
            all_owned_postmasters_normal_stop=True,actual_application_role_admission_or_job_functions=False)
    finally:
        password=None
        if process is not None:
            if process.poll()is None:
                try:cluster.stop(process,capture,binary,data,env,receipt)
                except(ValueError,OSError,subprocess.SubprocessError):
                    process.kill();process.wait(timeout=2);receipt['normal_stop_failed_job_teardown_required']=True
                    if capture is not None:capture.close()
            elif capture is not None:capture.close()
if __name__=='__main__':
    receipt=dict(state='FAILED_ASCII_NATIVE_POSTGRES_CAMPAIGN',stage='preflight',commands=[],migrations_applied=[],normal_restart_verified=False,
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,initdb_ascii_succeeded=False,
        database_root=str(OWNED/'cluster'),operational_database_accessed=False,service_or_Docker_WSL_started=False)
    try:
        cluster.require(sys.argv[1:]==['--owned-ascii-migration23-and-restart'],'PG_ASCII_CLOSED_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        text=str(error);receipt.update(error_type=type(error).__name__,error_code=text if re.fullmatch('PG_[A-Z0-9_]{1,100}',text)else'PG_ASCII_CAMPAIGN_FAILURE_NO_RAW_DETAIL')
    print(json.dumps(receipt,separators=(',',':')),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
