"""Four serial actual SQL/AEAD cases, synthetic caller acknowledgement loss, no network fault."""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
from native_postgres_ascii_campaign import copy_exact
ROOT=cluster.ROOT;PARENT=Path('D:/devdata');OWNED=PARENT/'hwpx-agent-p09-pg18-ack-295'
ASSET=PARENT/'hwpx-agent-p09-pg18-ascii-282/runtime'
PROBE=ROOT/'target/debug/examples/sql23_ack_loss.exe'
OBSERVATION='target/p09-sql23-ack-observations-295.json'
CASES=('register_after','cas_before','cas_after','complete_after')
ACTIVE_CASES=CASES[1:]
def case_campaign(name,receipt,env,binary,password):
    owner=OWNED/name;cluster.require(name in CASES and not owner.exists()and owner.resolve().parent==OWNED.resolve(),'PG_ACK_FRESH_CASE_OWNER')
    owner.mkdir();root=OWNED/'cluster';data=root/'data'
    art_password,rev_password,aes,hmac=[secrets.token_hex(32)for _ in range(4)];process=capture=None
    observations=dict(case=name,probes=[],snapshots=[],blob_snapshots=[]);receipt['cases'].append(observations)
    try:
        admin=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        tenant=f'00000000-0000-0000-0000-{1+0x100*CASES.index(name):012x}'
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        def sql(text,label):
            receipt['stage']=name+'_'+label;_,out=cluster.invoke(cluster.psql_args(binary,port),admin,receipt['stage'],receipt,text,timeout=30);return out.strip()
        def probe(mode):
            receipt['stage']=name+mode
            app=dict(env,P09_ACK_CASE=name,P09_SQL23_PORT=str(port),P09_SQL23_REVISION_PASSWORD=rev_password,P09_SQL23_ARTIFACT_PASSWORD=art_password,
                P09_STORAGE_AES_HEX=aes,P09_STORAGE_HMAC_HEX=hmac)
            if mode in('--fixture','--provision','--seed'):app.update(P09_SQL23_ADMIN_USER=cluster.USER,P09_SQL23_ADMIN_PASSWORD=password)
            code,out=cluster.invoke([str(PROBE),mode],app,receipt['stage'],receipt,timeout=45,check=False)
            try:r=json.loads(out)
            except json.JSONDecodeError:raise ValueError('PG_ACK_PROBE_JSON_REQUIRED')from None
            observations['probes'].append(r);cluster.require(code==0 and r['state'].startswith('PASS_'),'PG_ACK_PROBE_FAILED');return r
        def snapshot(recovered):
            result=json.loads(sql("SELECT json_build_object('job_state',j.state,'record_state',r.state,'attempt',j.attempt_count,'fence',j.fencing_token,"
                "'attempt_state',(SELECT state FROM hwpx_agent.job_attempts WHERE job_id=j.job_id AND tenant_id=j.tenant_id),"
                "'artifacts',(SELECT count(*) FROM hwpx_agent.artifacts WHERE tenant_id=j.tenant_id AND storage_state='available' AND validation_state='verified'),"
                "'jobs',(SELECT count(*) FROM hwpx_agent.jobs WHERE tenant_id=j.tenant_id),'attempts',(SELECT count(*) FROM hwpx_agent.job_attempts WHERE tenant_id=j.tenant_id),"
                "'authorizations',(SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations WHERE tenant_id=j.tenant_id),'intents',(SELECT count(*) FROM hwpx_agent.stored_revision_commit_intents WHERE tenant_id=j.tenant_id),"
                "'revisions',(SELECT count(*) FROM hwpx_agent.revisions WHERE tenant_id=j.tenant_id),'head',(SELECT head_generation FROM hwpx_agent.branches WHERE tenant_id=j.tenant_id)) "
                "FROM hwpx_agent.jobs j JOIN hwpx_agent.idempotency_records r USING(tenant_id,project_id,job_id) "
                "WHERE j.job_id='00000000-0000-0000-0000-000000000066' AND j.tenant_id='"+tenant+"';\n",'snapshot_after_recovery'if recovered else'snapshot_before_restart'))
            committed=name in('cas_after','complete_after');terminal=name=='complete_after'or(name=='cas_after'and recovered)
            expected=dict(job_state='succeeded'if terminal else'unknown_outcome',record_state='terminal_success'if terminal else'outcome_unknown',
                attempt=1,fence=1,attempt_state='succeeded'if name=='complete_after'else'unknown_outcome',artifacts=6,jobs=2,attempts=2,authorizations=0,intents=1,
                revisions=2 if committed else 1,head=2 if committed else 1)
            cluster.require(result==expected,'PG_ACK_EXACT_PERSISTED_EFFECT_UNKNOWN_OR_SUCCESS_WITH_ONE_ATTEMPT');observations['snapshots'].append(result)
        def blobs(label):
            rows=json.loads(sql("SELECT json_agg(json_build_object('object_key',object_key,'sha256',ciphertext_sha256::text,'size',size_bytes)) FROM hwpx_agent.artifacts WHERE tenant_id='"+tenant+"';\n",label))
            cluster.require(isinstance(rows,list)and len(rows)==6,'PG_ACK_SIX_REAL_ARTIFACTS_PER_CASE');pins=[]
            for r in rows:
                key=r['object_key'];cluster.require(isinstance(key,str)and re.fullmatch(r'artifacts/v1/[0-9a-f]{32}/[a-z_]+/available/[0-9a-f]{64}\.aes256gcm',key),'PG_ACK_CLOSED_KEY')
                p=owner/'blobs/output'/key;cluster.require(p.resolve().is_relative_to((owner/'blobs').resolve()),'PG_ACK_BLOB_SCOPE')
                for current in(p,*p.parents):
                    cluster.require(not current.is_symlink()and not current.is_junction(),'PG_ACK_BLOB_NOT_REPARSE')
                    if current==owner:break
                cluster.require(p.is_file()and p.stat().st_size==r['size']+16 and cluster.runtime.sha_file(p)==r['sha256'],'PG_ACK_REAL_CIPHERTEXT_METADATA_BINDING')
                pins.append(dict(path=p.relative_to(OWNED).as_posix(),bytes=p.stat().st_size,sha256=r['sha256']))
            pins.sort(key=lambda p:p['path']);observations['blob_snapshots'].append(pins)
        process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
        cluster.attest_cluster(binary,data,port,admin,receipt,name+'_before_fixture')
        fixture=probe('--fixture'if name==CASES[0]else'--provision');cluster.require(fixture['metadata_artifacts_seeded']==0,'PG_ACK_NO_SYNTHETIC_METADATA_ROWS')
        sql(f"ALTER ROLE p09_artifact_284 PASSWORD '{art_password}'; ALTER ROLE p09_revision_284 PASSWORD '{rev_password}';\n",'ephemeral_role_passwords')
        probe('--seed');probe('--execute-loss');snapshot(False);blobs('ciphertext_before_restart')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
        cluster.attest_cluster(binary,data,port,admin,receipt,name+'_after_restart');recovery=probe('--recover');snapshot(True);blobs('ciphertext_after_recovery')
        cluster.require(observations['blob_snapshots'][0]==observations['blob_snapshots'][1]and recovery['execution_retried']is False,'PG_ACK_NO_REEXECUTION_OR_CIPHERTEXT_LOSS')
        cluster.catalogue(binary,port,admin,cluster.migration_rows(),receipt,name+'_final_catalogue23')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None;observations['complete']=True
    finally:
        art_password=rev_password=aes=hmac=None
        if process is not None:
            if process.poll()is None:
                try:cluster.stop(process,capture,binary,data,env,receipt)
                except(ValueError,OSError,subprocess.SubprocessError):
                    process.kill();process.wait(timeout=2);receipt['normal_stop_failed_job_teardown_required']=True
                    if capture is not None:capture.close()
            elif capture is not None:capture.close()
def campaign(receipt):
    cluster.require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_ACK_WINDOWS_REPO_SCOPE')
    cluster.require(PARENT.is_dir()and not PARENT.is_symlink()and not PARENT.is_junction()and not OWNED.exists()and OWNED.resolve().parent==PARENT.resolve(),'PG_ACK_FRESH_ASCII_ROOT')
    cluster.require(PROBE.is_file()and not PROBE.is_symlink()and not PROBE.is_junction()and cluster.runtime.sha_file(PROBE)==os.environ.get('P09_ACK_PROBE_SHA256'),'PG_ACK_EXACT_PROBE')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    cluster.require(cluster.runtime.sha_file(ROOT/cluster.MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_ACK_EXACT_MANIFEST')
    manifest=json.loads((ROOT/cluster.MANIFEST).read_text(encoding='utf-8'))
    def pins():
        for r in manifest['runtime_pins']:
            p=ASSET/r['path'];cluster.require(p.is_file()and not p.is_symlink()and not p.is_junction()and p.stat().st_size==r['bytes']and cluster.runtime.sha_file(p)==r['sha256'],'PG_ACK_RUNTIME_BYTES')
    pins();OWNED.mkdir();binary=ASSET/'pgsql/bin';env=cluster.runtime.clean_environment(binary)
    cluster.SETTINGS.update(io_method='sync',max_wal_senders='0',max_logical_replication_workers='0',max_parallel_workers_per_gather='0',max_parallel_maintenance_workers='0')
    root=OWNED/'cluster';root.mkdir();data=root/'data';hba=OWNED/'native_postgres_hba.conf';original=ROOT/cluster.HBA
    copy_exact(original,hba,cluster.runtime.sha_file(original),original.stat().st_size);cluster.CLUSTER=str(root);cluster.HBA=str(hba)
    password=secrets.token_hex(32)
    try:
        cluster.invoke(cluster.init_args(binary,data),env,'single_cluster_init_once',receipt,timeout=60)
        cluster.invoke(cluster.bootstrap_args(binary,data),env,'single_cluster_admin_password',receipt,f"ALTER ROLE {cluster.USER} PASSWORD '{password}';\n",timeout=15)
        # Original register_after is closed by294. Only provision its inert tenant in this
        # new cluster so the shared original fixture can create schema/roles once; no seed/job.
        (OWNED/CASES[0]).mkdir();process=capture=None
        try:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
            process,capture=cluster.start(binary,data,port,env,receipt);cluster.ready(process,capture,binary,port,env,receipt)
            app=dict(env,P09_ACK_CASE=CASES[0],P09_SQL23_PORT=str(port),P09_SQL23_ADMIN_USER=cluster.USER,P09_SQL23_ADMIN_PASSWORD=password)
            code,out=cluster.invoke([str(PROBE),'--fixture'],app,'schema23_once_no_replayed_case',receipt,timeout=30,check=False)
            setup=json.loads(out);receipt['setup_probe']=setup;cluster.require(code==0 and setup['metadata_artifacts_seeded']==0,'PG_ACK_SCHEMA_ONLY_NO_PRIOR_CASE_EXECUTION')
            cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        finally:
            if process is not None:
                if process.poll()is None:
                    try:cluster.stop(process,capture,binary,data,env,receipt)
                    except(ValueError,OSError,subprocess.SubprocessError):
                        process.kill();process.wait(timeout=2)
                        if capture is not None:capture.close()
                elif capture is not None:capture.close()
        receipt['case_checkpoint_pins']=[]
        for name in ACTIVE_CASES:
            before=len(receipt.get('postmasters',[]));case_campaign(name,receipt,env,binary,password)
            evidence=dict(state='COMPLETED_CASE_RUNTIME_EVIDENCE_REQUIRES_PARENT_SOURCE_CLOSURE',case=receipt['cases'][-1],
                postmasters=receipt['postmasters'][before:],compiled_probe_sha256=os.environ.get('P09_ACK_PROBE_SHA256'),actual_network_fault=False)
            payload=json.dumps(evidence,separators=(',',':')).encode();cluster.require(len(payload)<=32768,'PG_ACK_CASE_CHECKPOINT_BOUND')
            relative=f'target/p09-sql23-ack-case-295-{name}.json';destination=ROOT/relative
            cluster.require(not destination.exists()and not destination.parent.is_symlink()and not destination.parent.is_junction(),'PG_ACK_FRESH_CASE_CHECKPOINT')
            with destination.open('xb')as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
            receipt['case_checkpoint_pins'].append(dict(path=relative,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
    finally:password=None
    pins();cluster.require(cluster.runtime.sha_file(PROBE)==os.environ.get('P09_ACK_PROBE_SHA256'),'PG_ACK_FINAL_PROBE')
    cluster.require(len(receipt['postmasters'])==7 and all(p['normal_stop']for p in receipt['postmasters']),'PG_ACK_ALL_SEVEN_POSTMASTERS_NORMAL_STOP')
    receipt.update(state='PASS_REAL_SQL23_APPLICATION_ACK_LOSS4_RESTART_RECOVERY_NOT_NETWORK_PRODUCT_OR_P09_GATE',stage='finished',all_owned_postmasters_normal_stop=True,
        actual_initdb_count=1,actual_schema23_application_count=1,isolated_tenants=4,prior_register_after_executed=False)
if __name__=='__main__':
    receipt=dict(state='FAILED_SQL23_ACK_LOSS',stage='preflight',commands=[],cases=[],actual_network_fault=False,actual_P09_product_or_Native_execution=False,
        synthetic_route_scanner_validator_and_bytes=True,parent_retained_ephemeral_test_keys=True,operational_database_accessed=False,database_root=str(OWNED))
    try:cluster.require(sys.argv[1:]==['--owned-ack-loss4'],'PG_ACK_CLOSED_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_ACK_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();cluster.require(len(payload)<=262144,'PG_ACK_OBSERVATION_BOUND')
    p=ROOT/OBSERVATION;cluster.require(not p.exists()and p.parent.is_dir()and not p.parent.is_symlink()and not p.parent.is_junction(),'PG_ACK_IMMUTABLE_OBSERVATION')
    with p.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),case_count=len(receipt['cases']))),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
