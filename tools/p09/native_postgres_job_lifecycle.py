"""Actual SQL23 claim/lease/stage guards and restart, one fresh owned ASCII cluster.

Existing DBs/runtime are read-only. Synthetic metadata is never blob/AEAD/product evidence.
"""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
from native_postgres_ascii_campaign import copy_exact
ROOT=cluster.ROOT
PARENT=Path('D:/devdata')
OWNED=PARENT/'hwpx-agent-p09-pg18-job-286'
ASSET=PARENT/'hwpx-agent-p09-pg18-ascii-282/runtime'
PROBE=ROOT/'target/debug/examples/p09_sql23_jobs.exe'
OBSERVATION='target/p09-sql23-job-observations-286.json'

def campaign(receipt):
    cluster.require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_JOB_WINDOWS_REPO_SCOPE')
    cluster.require(PARENT.is_dir()and not PARENT.is_symlink()and not PARENT.is_junction()and not OWNED.exists()
        and OWNED.resolve().parent==PARENT.resolve()and str(OWNED).isascii(),'PG_JOB_FRESH_ASCII_SCOPE')
    cluster.require(PROBE.is_file()and not PROBE.is_symlink()and not PROBE.is_junction()
        and cluster.runtime.sha_file(PROBE)==os.environ.get('P09_JOB_PROBE_SHA256'),'PG_JOB_EXACT_COMPILED_PROBE')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    cluster.require(cluster.runtime.sha_file(ROOT/cluster.MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_JOB_EXACT_RUNTIME_MANIFEST')
    manifest=json.loads((ROOT/cluster.MANIFEST).read_text(encoding='utf-8'))
    def runtime_pins():
        for pin in manifest['runtime_pins']:
            path=ASSET/pin['path'];cluster.require(path.is_file()and not path.is_symlink()and not path.is_junction()
                and path.stat().st_size==pin['bytes']and cluster.runtime.sha_file(path)==pin['sha256'],'PG_JOB_RUNTIME_BYTES')
    runtime_pins();OWNED.mkdir();root=OWNED/'cluster';root.mkdir();data=root/'data';hba=OWNED/'native_postgres_hba.conf'
    original=ROOT/cluster.HBA;copy_exact(original,hba,cluster.runtime.sha_file(original),original.stat().st_size)
    binary=ASSET/'pgsql/bin';cluster.CLUSTER=str(root);cluster.HBA=str(hba)
    cluster.SETTINGS.update(io_method='sync',max_wal_senders='0',max_logical_replication_workers='0',max_parallel_workers_per_gather='0',max_parallel_maintenance_workers='0')
    env=cluster.runtime.clean_environment(binary);password,art_password,rev_password=[secrets.token_hex(32)for _ in range(3)]
    process=capture=None
    try:
        receipt['stage']='new_ascii_job_cluster_init';cluster.invoke(cluster.init_args(binary,data),env,receipt['stage'],receipt,timeout=60)
        cluster.invoke(cluster.bootstrap_args(binary,data),env,'fresh_job_admin_bootstrap',receipt,f"ALTER ROLE {cluster.USER} PASSWORD '{password}';\n",timeout=15)
        admin=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        receipt['loopback_port']=port
        def sql(text,label):
            receipt['stage']=label;_,out=cluster.invoke(cluster.psql_args(binary,port),admin,label,receipt,text,timeout=30);return out.strip()
        def probe(mode):
            receipt['stage']=mode
            app=dict(env,P09_SQL23_PORT=str(port),P09_SQL23_REVISION_PASSWORD=rev_password)
            if mode=='--fixture':app.update(P09_SQL23_ADMIN_USER=cluster.USER,P09_SQL23_ADMIN_PASSWORD=password,P09_SQL23_OWNED_DATA=str(data))
            code,out=cluster.invoke([str(PROBE),mode],app,'sql23_job'+mode,receipt,timeout=30,check=False)
            try:result=json.loads(out)
            except json.JSONDecodeError:raise ValueError('PG_JOB_PROBE_CLOSED_JSON_REQUIRED')from None
            receipt['probes'].append(result);cluster.require(code==0 and result['state'].startswith('PASS_'),'PG_JOB_PROBE_FAILED')
            return result
        def snapshot(label):
            result=json.loads(sql("SELECT json_build_object('job_state',j.state,'attempt',j.attempt_count,'fence',j.fencing_token,'record_state',r.state,"
                "'attempt_rows',(SELECT count(*) FROM hwpx_agent.job_attempts WHERE job_id=j.job_id),"
                "'authorization_rows',(SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations WHERE job_id=j.job_id),"
                "'intent_rows',(SELECT count(*) FROM hwpx_agent.stored_revision_commit_intents),"
                "'revisions',(SELECT count(*) FROM hwpx_agent.revisions),'all_jobs',(SELECT count(*) FROM hwpx_agent.jobs)) "
                "FROM hwpx_agent.jobs j JOIN hwpx_agent.idempotency_records r USING(tenant_id,project_id,job_id) "
                "WHERE j.job_id='00000000-0000-0000-0000-000000000066';\n",label))
            expected=dict(job_state='validating',attempt=1,fence=1,record_state='in_progress',attempt_rows=1,authorization_rows=1,intent_rows=0,revisions=1,all_jobs=2)
            cluster.require(result==expected,'PG_JOB_PERSISTED_EXACT_SINGLE_ATTEMPT_NO_FALSE_COMPLETION');receipt['snapshots'].append(result)
        process,capture=cluster.start(binary,data,port,env,receipt);receipt['actual_owned_postmaster_started']=True
        cluster.ready(process,capture,binary,port,env,receipt);cluster.attest_cluster(binary,data,port,admin,receipt,'job_before_fixture')
        fixture=probe('--fixture');cluster.require(fixture['migrations']==23 and not fixture['guards_disabled']and not fixture['direct_seal_or_revision_insertion']
            and not fixture['legacy_rights_granted_to_application'],'PG_JOB_REAL_BOOTSTRAP_NOT_DIRECT_SEALS')
        receipt['actual_SQL23_applied_in_owned_test_database']=True
        sql(f"ALTER ROLE p09_artifact_284 PASSWORD '{art_password}'; ALTER ROLE p09_revision_284 PASSWORD '{rev_password}';\n",'ephemeral_job_role_passwords')
        exercise=probe('--exercise');cluster.require(len(exercise['checks'])==15 and len(set(exercise['checks']))==15,'PG_JOB_EXACT15_CHECKS')
        snapshot('single_attempt_before_restart');cluster.catalogue(binary,port,admin,cluster.migration_rows(),receipt,'job_catalogue_before_restart')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
        cluster.attest_cluster(binary,data,port,admin,receipt,'job_after_restart');probe('--restart-observe');snapshot('single_attempt_after_restart')
        cluster.catalogue(binary,port,admin,cluster.migration_rows(),receipt,'job_catalogue_after_restart')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        runtime_pins();cluster.require(cluster.runtime.sha_file(PROBE)==os.environ.get('P09_JOB_PROBE_SHA256'),'PG_JOB_FINAL_PROBE_BYTES')
        receipt.update(state='PASS_ACTUAL_SQL23_WORKER_CLAIM_LEASE_STAGE15_AND_RESTART_NOT_AEAD_CAS_OR_P09_GATE',stage='finished',
            actual_SQL23_worker_lease=True,checks=exercise['checks'],all_owned_postmasters_normal_stop=True)
    finally:
        password=art_password=rev_password=None
        if process is not None:
            if process.poll()is None:
                try:cluster.stop(process,capture,binary,data,env,receipt)
                except(ValueError,OSError,subprocess.SubprocessError):
                    process.kill();process.wait(timeout=2);receipt['normal_stop_failed_job_teardown_required']=True
                    if capture is not None:capture.close()
            elif capture is not None:capture.close()

if __name__=='__main__':
    receipt=dict(state='FAILED_ACTUAL_SQL23_JOB_LIFECYCLE',stage='preflight',commands=[],probes=[],snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_worker_lease=False,
        actual_blob_AEAD_or_product_execution=False,SQL23_result_CAS_or_completion=False,operational_database_accessed=False)
    try:
        cluster.require(sys.argv[1:]==['--owned-sql23-job-lifecycle'],'PG_JOB_CLOSED_WORKER_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,100}',code)else'PG_JOB_FAILURE_NO_RAW_DETAIL')
    payload=json.dumps(receipt,separators=(',',':')).encode();cluster.require(len(payload)<=262144,'PG_JOB_OBSERVATION_BYTE_LIMIT')
    path=ROOT/OBSERVATION;cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_JOB_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
