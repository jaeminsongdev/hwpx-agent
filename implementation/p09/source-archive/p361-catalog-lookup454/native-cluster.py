"""Small owned foreground PG18 cluster + exact migration23 catalogue/restart campaign.

No service installation, Docker/WSL, operational database, product/Native execution or grants.
Single-user bootstrap is restricted to a newly initialized OWNED cluster, never existing data.
An ephemeral SCRAM password travels only through stdin/environment, not a file or argument.
"""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys,time
from pathlib import Path
import native_postgres_runtime as runtime
from bounded_process_progress import BoundedProcessCapture

ROOT=runtime.ROOT
CLUSTER='target/p09-native-postgres-cluster-280'
HBA='tools/p09/fixtures/native_postgres_hba.conf'
MANIFEST=runtime.ASSET+'/runtime-manifest.json'
USER='p09_owned_280'
SETTINGS={'shared_buffers':'16MB','work_mem':'1MB','maintenance_work_mem':'16MB','max_connections':'12',
    'max_worker_processes':'0','max_parallel_workers':'0','autovacuum':'off','jit':'off','fsync':'on','synchronous_commit':'on',
    'full_page_writes':'on','min_wal_size':'32MB','max_wal_size':'128MB','logging_collector':'off','log_min_messages':'fatal',
    'log_statement':'none','log_min_error_statement':'panic','statement_timeout':'5000','lock_timeout':'1000',
    'idle_in_transaction_session_timeout':'5000','transaction_timeout':'10000','temp_file_limit':'16384','timezone':'UTC'}
def require(ok,code):runtime.require(ok,code)
def settings():return [v for k,value in SETTINGS.items()for v in('-c',k+'='+value)]
def init_args(binary,data):
    require(Path(data).name=='data'and Path(data).parent.name==Path(CLUSTER).name,'PG_CLUSTER_DATA_SCOPE')
    return [str(binary/'initdb.exe'),'-D',str(data),'--username='+USER,'--auth=reject','--encoding=UTF8','--locale=C','--no-instructions','--no-clean',
        '--set','shared_buffers=16MB','--set','max_connections=12']
def bootstrap_args(binary,data):
    require(Path(data).name=='data'and Path(data).parent.name==Path(CLUSTER).name,'PG_CLUSTER_DATA_SCOPE')
    return [str(binary/'postgres.exe'),'--single','-D',str(data),'-c','log_min_messages=fatal','-c','log_min_error_statement=panic','postgres']
def start_args(binary,data,port,hba):
    require(isinstance(port,int)and not isinstance(port,bool)and 1024<=port<=65535,'PG_CLUSTER_PORT_SCOPE')
    require(Path(data).name=='data'and Path(data).parent.name==Path(CLUSTER).name,'PG_CLUSTER_DATA_SCOPE')
    return [str(binary/'postgres.exe'),'-D',str(data),'-h','127.0.0.1','-p',str(port),'-c','hba_file='+str(hba),*settings()]
def psql_args(binary,port):
    require(1024<=port<=65535,'PG_PSQL_PORT_SCOPE')
    return [str(binary/'psql.exe'),'-X','-q','-A','-t','--no-password','--set','ON_ERROR_STOP=1','--set','VERBOSITY=sqlstate',
        '-h','127.0.0.1','-p',str(port),'-U',USER,'-d','postgres']
def migration_rows():
    paths=sorted((ROOT/'migrations/postgres').glob('*.up.sql'))
    require(len(paths)==23 and [p.name[:4]for p in paths]==[f'{n:04}'for n in range(1,24)],'PG_EXACT23_MIGRATION_INPUTS')
    rows=[]
    for path in paths:
        require(path.is_file()and not path.is_symlink()and not path.is_junction()and 0<path.stat().st_size<=1048576,'PG_MIGRATION_FILE_SCOPE')
        raw=path.read_bytes();rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),text=raw.decode('utf-8')))
    return rows
def invoke(args,env,stage,receipt,input_text=None,timeout=30,check=True):
    child=capture=None;started=time.monotonic()
    try:
        child=subprocess.Popen(args,cwd=Path(args[0]).parent,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        capture=BoundedProcessCapture(child,input_text=input_text,output_limit=32768,parse_markers=False)
        out,err=capture.communicate(timeout=timeout)
        receipt['commands'].append(dict(stage=stage,exit_code=child.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            sqlstates=sorted(set(re.findall(r'\b(?:ERROR|FATAL):\s+([0-9A-Z]{5})\b',err))),elapsed_seconds=round(time.monotonic()-started,3)))
        if check:require(child.returncode==0,'PG_CLUSTER_COMMAND_FAILED')
        return child.returncode,out
    finally:
        if child is not None:
            if child.poll()is None:child.kill()
            child.wait(timeout=2)
            if capture is not None:capture.close()

def attest_cluster(binary,data,port,env,receipt,stage):
    _,out=invoke(psql_args(binary,port),env,stage,receipt,"""SELECT json_build_object(
      'data_directory',current_setting('data_directory'),'port',current_setting('port')::int,
      'listen',current_setting('listen_addresses'),'version',current_setting('server_version_num')::int,
      'user',current_user,'fsync',current_setting('fsync'),'sync_commit',current_setting('synchronous_commit'),
      'hba_clean',NOT EXISTS(SELECT 1 FROM pg_hba_file_rules WHERE error IS NOT NULL),
      'scram_local',EXISTS(SELECT 1 FROM pg_hba_file_rules WHERE type='host' AND address='127.0.0.1' AND auth_method='scram-sha-256'),
      'no_trust',NOT EXISTS(SELECT 1 FROM pg_hba_file_rules WHERE auth_method NOT IN ('scram-sha-256','reject')));
""")
    result=json.loads(out.strip());require(Path(result['data_directory']).resolve()==data.resolve()and result['port']==port
        and result['listen']=='127.0.0.1'and result['version']==180006 and result['user']==USER and result['fsync']=='on'
        and result['sync_commit']=='on'and result['hba_clean']and result['scram_local']and result['no_trust'],'PG_CLUSTER_ATTESTATION')
    receipt.setdefault('cluster_attestations',[]).append(result)

def start(binary,data,port,env,receipt):
    process=subprocess.Popen(start_args(binary,data,port,ROOT/HBA),cwd=binary,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    capture=BoundedProcessCapture(process,output_limit=32768,parse_markers=False)
    # The caller owns this exact handle even if readiness fails.
    return process,capture
def ready(process,capture,binary,port,env,receipt):
    deadline=time.monotonic()+10
    while True:
        capture.progress();require(process.poll()is None,'PG_OWNED_POSTMASTER_EXITED')
        code,_=invoke([str(binary/'pg_isready.exe'),'-h','127.0.0.1','-p',str(port),'-U',USER,'-d','postgres','--timeout=1'],env,'readiness',receipt,timeout=3,check=False)
        if code==0:return
        require(time.monotonic()<deadline,'PG_OWNED_POSTMASTER_READY_DEADLINE');time.sleep(.1)
def stop(process,capture,binary,data,env,receipt):
    require(process.poll()is None,'PG_STOP_EXACT_HANDLE_NOT_LIVE')
    pid_path=data/'postmaster.pid';require(pid_path.is_file()and not pid_path.is_symlink()and not pid_path.is_junction(),'PG_STOP_PID_FILE_SCOPE')
    require(pid_path.read_text(encoding='utf-8').splitlines()[0]==str(process.pid),'PG_STOP_PID_EQUALS_OWN_LIVE_HANDLE')
    invoke([str(binary/'pg_ctl.exe'),'-D',str(data),'stop','-m','fast','-w','-t','10'],env,'stop_owned_postmaster',receipt,timeout=15)
    out,err=capture.communicate(timeout=3);require(process.returncode==0,'PG_POSTMASTER_CLEAN_STOP_EXIT')
    receipt.setdefault('postmasters',[]).append(dict(pid=process.pid,normal_stop=True,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
        stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest()))
    capture.close()
def catalogue(binary,port,env,rows,receipt,stage):
    _,out=invoke(psql_args(binary,port),env,stage,receipt,"SELECT coalesce(json_agg(json_build_array(version,migration_sha256::text) ORDER BY version),'[]') FROM hwpx_agent.schema_versions;\n")
    actual=json.loads(out.strip());require(actual==[[n,row['sha256']]for n,row in enumerate(rows,1)],'PG_ACTUAL_CATALOGUE_EXACT23_HASHES')
    return actual

def campaign(receipt):
    require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_CLUSTER_WINDOWS_REPO_SCOPE')
    # Suppress only this worker's loader/crash dialogs; no global Windows setting is changed.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.SetErrorMode(0x0001|0x0002|0x8000)
    asset=ROOT/runtime.ASSET;binary=asset/'pgsql/bin';root=ROOT/CLUSTER;data=root/'data';parent=ROOT/'target'
    require(not root.exists()and parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
        and root.resolve().is_relative_to(parent.resolve()),'PG_CLUSTER_NEW_OWNED_DATA_ONLY')
    manifest=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
    require(runtime.sha_file(ROOT/MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce'
        and manifest['state']=='ACQUIRED_VERSION_ONLY_NOT_DATABASE'and manifest['archive_extract_files']==1583,'PG_CLUSTER_EXACT_QUALIFIED_RUNTIME_MANIFEST')
    for pin in manifest['runtime_pins']:
        path=asset/pin['path'];require(path.is_file()and not path.is_symlink()and not path.is_junction()and path.stat().st_size==pin['bytes']
            and runtime.sha_file(path)==pin['sha256'],'PG_CLUSTER_FRESH_RUNTIME_BYTES')
    rows=migration_rows();receipt['migration_inputs']=[{k:v for k,v in row.items()if k!='text'}for row in rows]
    root.mkdir();env=runtime.clean_environment(binary);password=secrets.token_hex(32)
    process=capture=None
    try:
        receipt['stage']='initialize_new_reject_auth_cluster'
        invoke(init_args(binary,data),env,'initdb_new_owned_reject_cluster',receipt,timeout=60)
        receipt['stage']='ephemeral_password_new_cluster_only'
        # No -E echo, no credential file, no password in process arguments or persisted raw logs.
        invoke(bootstrap_args(binary,data),
            env,'bootstrap_new_owned_scram_credential',receipt,input_text=f"ALTER ROLE {USER} PASSWORD '{password}';\n",timeout=15)
        client_env=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reservation:
            reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
        receipt['loopback_port']=port;receipt['stage']='first_foreground_start'
        process,capture=start(binary,data,port,env,receipt);ready(process,capture,binary,port,env,receipt)
        receipt['actual_owned_postmaster_started']=True
        attest_cluster(binary,data,port,client_env,receipt,'attest_before_any_migration')
        for number,row in enumerate(rows,1):
            receipt['stage']=f'apply_migration_{number:04}'
            require(runtime.sha_file(ROOT/row['path'])==row['sha256'],'PG_MIGRATION_FRESH_BEFORE_EXECUTION')
            invoke(psql_args(binary,port),client_env,receipt['stage'],receipt,"SELECT set_config('hwpx_agent.migration_sha256','"+row['sha256']+"',false);\n"+row['text'],timeout=30)
            receipt['migrations_applied'].append(number)
            if number==23:receipt['actual_SQL23_applied_in_owned_test_database']=True
        receipt['stage']='verify_exact_catalogue23';catalogue(binary,port,client_env,rows,receipt,'catalogue_before_restart')
        marker=hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        invoke(psql_args(binary,port),client_env,'create_owned_restart_marker',receipt,
            "CREATE SCHEMA p09_runtime_probe; CREATE TABLE p09_runtime_probe.restart_marker(value text NOT NULL); INSERT INTO p09_runtime_probe.restart_marker VALUES('"+marker+"');\n")
        receipt['stage']='clean_stop_and_restart';stop(process,capture,binary,data,env,receipt);process=capture=None
        process,capture=start(binary,data,port,env,receipt);ready(process,capture,binary,port,env,receipt)
        attest_cluster(binary,data,port,client_env,receipt,'attest_after_restart');catalogue(binary,port,client_env,rows,receipt,'catalogue_after_restart')
        _,out=invoke(psql_args(binary,port),client_env,'read_owned_restart_marker',receipt,'SELECT value FROM p09_runtime_probe.restart_marker;\n')
        require(out.strip()==marker,'PG_DURABLE_RESTART_MARKER_EXACT');receipt['restart_marker_sha256']=marker;receipt['normal_restart_verified']=True
        stop(process,capture,binary,data,env,receipt);process=capture=None
        for pin in manifest['runtime_pins']:
            require(runtime.sha_file(asset/pin['path'])==pin['sha256'],'PG_CLUSTER_FINAL_RUNTIME_BYTES')
        for row in rows:require(runtime.sha_file(ROOT/row['path'])==row['sha256'],'PG_CLUSTER_FINAL_MIGRATION_BYTES')
        receipt.update(state='PASS_OWNED_PG18_6_MIGRATIONS23_CATALOGUE_AND_CLEAN_RESTART_NOT_APPLICATION_PRIVILEGES_OR_PRODUCT',stage='finished',
            actual_SQL23_applied_in_owned_test_database=True,all_owned_postmasters_normal_stop=True,
            actual_application_role_admission_or_job_functions=False,actual_product_or_Native_execution=False)
    finally:
        password=None
        if process is not None:
            if process.poll()is None:
                try:stop(process,capture,binary,data,env,receipt)
                except(ValueError,OSError,subprocess.SubprocessError):
                    # Only this exact handle; the parent Job always tears down its remaining tree.
                    process.kill();process.wait(timeout=2);receipt['normal_stop_failed_job_teardown_required']=True
                    if capture is not None:capture.close()
            elif capture is not None:capture.close()

if __name__=='__main__':
    receipt=dict(state='FAILED_NATIVE_POSTGRES_CLUSTER',stage='preflight',commands=[],migrations_applied=[],normal_restart_verified=False,actual_owned_postmaster_started=False,
        database_root=CLUSTER,actual_SQL23_applied_in_owned_test_database=False,operational_database_accessed=False,service_or_Docker_WSL_started=False)
    try:
        require(sys.argv[1:]==['--owned-migration23-and-restart'],'PG_CLUSTER_CLOSED_WORKER_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        text=str(error);receipt.update(error_type=type(error).__name__,error_code=text if re.fullmatch('PG_[A-Z0-9_]{1,100}',text)else'PG_CLUSTER_FAILURE_NO_RAW_DETAIL')
    print(json.dumps(receipt,separators=(',',':')),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
