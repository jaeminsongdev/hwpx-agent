"""Real Rust SQL23 profile admission/fault campaign, owned fresh ASCII DB only.

The fixed Rust fixture loader preserves compiled SQL bytes and creates synthetic metadata.
No HWPX execution, scanner/issuer qualification, worker lease or revision CAS is performed.
"""
import ctypes,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
from native_postgres_ascii_campaign import copy_exact
ROOT=cluster.ROOT
PARENT=Path('D:/devdata')
OWNED=PARENT/'hwpx-agent-p09-pg18-role-284'
ASSET=PARENT/'hwpx-agent-p09-pg18-ascii-282/runtime'
PROBE=ROOT/'target/debug/examples/p09_sql23_admission.exe'
OBSERVATION='target/p09-sql23-role-observations-284.json'
ART='p09_artifact_284';REV='p09_revision_284'

def campaign(receipt):
    cluster.require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_ROLE_WINDOWS_REPO_SCOPE')
    cluster.require(PARENT.is_dir()and not PARENT.is_symlink()and not PARENT.is_junction()and not OWNED.exists()
        and OWNED.resolve().parent==PARENT.resolve()and str(OWNED).isascii(),'PG_ROLE_NEW_ASCII_OWNER_SCOPE')
    cluster.require(PROBE.is_file()and not PROBE.is_symlink()and not PROBE.is_junction()and cluster.runtime.sha_file(PROBE)==os.environ.get('P09_ROLE_PROBE_SHA256'),'PG_ROLE_EXACT_COMPILED_PROBE')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    cluster.require(cluster.runtime.sha_file(ROOT/cluster.MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_ROLE_EXACT_RUNTIME_MANIFEST')
    manifest=json.loads((ROOT/cluster.MANIFEST).read_text(encoding='utf-8'))
    for pin in manifest['runtime_pins']:
        path=ASSET/pin['path'];cluster.require(path.is_file()and not path.is_symlink()and not path.is_junction()
            and path.stat().st_size==pin['bytes']and cluster.runtime.sha_file(path)==pin['sha256'],'PG_ROLE_CURRENT_ASCII_RUNTIME_BYTES')
    OWNED.mkdir();root=OWNED/'cluster';root.mkdir();data=root/'data';hba=OWNED/'native_postgres_hba.conf';original_hba=ROOT/cluster.HBA
    copy_exact(original_hba,hba,cluster.runtime.sha_file(original_hba),original_hba.stat().st_size)
    binary=ASSET/'pgsql/bin';cluster.CLUSTER=str(root);cluster.HBA=str(hba)
    cluster.SETTINGS.update(io_method='sync',max_wal_senders='0',max_logical_replication_workers='0',max_parallel_workers_per_gather='0',max_parallel_maintenance_workers='0')
    env=cluster.runtime.clean_environment(binary);password,art_password,rev_password=[secrets.token_hex(32)for _ in range(3)]
    process=capture=None
    try:
        receipt['stage']='new_ascii_role_cluster_init'
        cluster.invoke(cluster.init_args(binary,data),env,receipt['stage'],receipt,timeout=60)
        cluster.invoke(cluster.bootstrap_args(binary,data),env,'new_ascii_role_admin_bootstrap',receipt,f"ALTER ROLE {cluster.USER} PASSWORD '{password}';\n",timeout=15)
        admin=dict(env,PGPASSWORD=password,PGCONNECT_TIMEOUT='2',PGCLIENTENCODING='UTF8')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM)as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        receipt['loopback_port']=port;process,capture=cluster.start(binary,data,port,env,receipt);receipt['actual_owned_postmaster_started']=True
        cluster.ready(process,capture,binary,port,env,receipt);cluster.attest_cluster(binary,data,port,admin,receipt,'role_cluster_before_fixture')
        def sql(text,label):
            receipt['stage']=label;_,out=cluster.invoke(cluster.psql_args(binary,port),admin,label,receipt,text,timeout=30);return out.strip()
        def probe(mode,label):
            receipt['stage']=label
            app=dict(env,P09_SQL23_PORT=str(port),P09_SQL23_ARTIFACT_PASSWORD=art_password,P09_SQL23_REVISION_PASSWORD=rev_password)
            if mode in('--fixture-load','--claim-body-fault','--claim-body-restore'):app.update(P09_SQL23_ADMIN_USER=cluster.USER,P09_SQL23_ADMIN_PASSWORD=password,P09_SQL23_OWNED_DATA=str(data))
            code,out=cluster.invoke([str(PROBE),mode],app,label,receipt,timeout=30,check=False)
            try:result=json.loads(out)
            except json.JSONDecodeError:raise ValueError('PG_ROLE_PROBE_CLOSED_JSON_REQUIRED')from None
            receipt['probes'].append(dict(label=label,**result));cluster.require(code==0 and result['state'].startswith('PASS_'),'PG_ROLE_PROBE_EXPECTATION_FAILED')
            return result
        fixture=probe('--fixture-load','compiled_exact23_fixture_load')
        cluster.require(fixture['migrations']==23 and fixture['synthetic_tenants']==2,'PG_ROLE_EXACT23_SYNTHETIC_FIXTURE')
        receipt['actual_SQL23_applied_in_owned_test_database']=True
        sql(f"ALTER ROLE {ART} PASSWORD '{art_password}'; ALTER ROLE {REV} PASSWORD '{rev_password}';\n",'set_ephemeral_application_passwords')
        probe('--baseline','actual_artifact_and_revision_baseline')
        behavior=probe('--behavior','actual_metadata_scope_and_tenant_RLS')
        cluster.require(behavior['actual_metadata_scope_checks']==6,'PG_ROLE_ACTUAL_SIX_METADATA_SCOPE_CHECKS')
        # All fault injections/roles belong only to this newly created disposable DB.
        def signature(name):
            cluster.require(re.fullmatch('[a-z_0-9]{1,90}',name),'PG_ROLE_CLOSED_FUNCTION_NAME')
            value=json.loads(sql("SELECT json_agg(p.oid::regprocedure::text) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='hwpx_agent' AND p.proname='"+name+"';\n",'read_owned_function_signature'))
            cluster.require(isinstance(value,list)and len(value)==1,'PG_ROLE_UNIQUE_OWNED_FUNCTION_SIGNATURE');return value[0]
        claim=signature('claim_stored_revision_job_v1');legacy=signature('claim_idempotent_job_v2');control=signature('advance_idempotent_job_v2')
        cases=[
            ('artifact_job_select','--artifact-denied',f'GRANT SELECT ON hwpx_agent.jobs TO {ART};',f'REVOKE SELECT ON hwpx_agent.jobs FROM {ART};'),
            ('artifact_job_column_select','--artifact-denied',f'GRANT SELECT(job_id) ON hwpx_agent.jobs TO {ART};',f'REVOKE SELECT(job_id) ON hwpx_agent.jobs FROM {ART};'),
            ('artifact_job_execute','--artifact-denied',f'GRANT EXECUTE ON FUNCTION {claim} TO {ART};',f'REVOKE EXECUTE ON FUNCTION {claim} FROM {ART};'),
            ('artifact_replication_role','--artifact-denied',f'ALTER ROLE {ART} REPLICATION;',f'ALTER ROLE {ART} NOREPLICATION;'),
            ('revision_column_update','--revision-denied',f'GRANT UPDATE(branch_id) ON hwpx_agent.branches TO {REV};',f'REVOKE UPDATE(branch_id) ON hwpx_agent.branches FROM {REV};'),
            ('revision_direct_intent_read','--revision-denied',f'GRANT SELECT ON hwpx_agent.stored_revision_commit_intents TO {REV};',f'REVOKE SELECT ON hwpx_agent.stored_revision_commit_intents FROM {REV};'),
            ('revision_missing_claim','--revision-denied',f'REVOKE EXECUTE ON FUNCTION {claim} FROM {REV};',f'GRANT EXECUTE ON FUNCTION {claim} TO {REV};'),
            ('revision_legacy_source_claim','--revision-denied',f'GRANT EXECUTE ON FUNCTION {legacy} TO {REV};',f'REVOKE EXECUTE ON FUNCTION {legacy} FROM {REV};'),
            ('revision_control_search_path','--revision-denied',f'ALTER FUNCTION {control} SET search_path=public;',f'ALTER FUNCTION {control} SET search_path=pg_catalog,hwpx_agent;'),
            ('revision_stored_intent_trigger','--revision-denied','ALTER TABLE hwpx_agent.revision_commit_receipts DISABLE TRIGGER revision_commit_receipts_stored_intent_guard;',
                'ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE TRIGGER revision_commit_receipts_stored_intent_guard;'),
            ('revision_stored_intent_RLS','--revision-denied','ALTER TABLE hwpx_agent.stored_revision_commit_intents DISABLE ROW LEVEL SECURITY;',
                'ALTER TABLE hwpx_agent.stored_revision_commit_intents ENABLE ROW LEVEL SECURITY;'),
        ]
        for name,mode,mutate,restore in cases:
            sql(mutate+'\n','inject_'+name)
            probe(mode,'deny_'+name)
            sql(restore+'\n','restore_'+name)
            probe('--baseline','restored_'+name)
            receipt['faults_verified'].append(name)
        # Change actual prosrc without broadening function rights, then restore the exact definition.
        probe('--claim-body-fault','inject_revision_function_body_hash')
        probe('--revision-denied','deny_revision_function_body_hash');probe('--claim-body-restore','restore_revision_function_body_hash')
        probe('--baseline','restored_revision_function_body_hash');receipt['faults_verified'].append('revision_function_body_hash')
        # Preserve the schema registry's immutable trigger across every administrator fault transaction.
        actual_name=json.loads(sql("SELECT to_json(migration_name) FROM hwpx_agent.schema_versions WHERE version=23;\n",'read_exact_schema23_name'))
        actual_sha=json.loads(sql("SELECT to_json(migration_sha256::text) FROM hwpx_agent.schema_versions WHERE version=23;\n",'read_exact_schema23_sha'))
        def registry(statement,label):sql('BEGIN; ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable; '+statement+
            ' ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable; COMMIT;\n',label)
        for name,mutate,restore in[
            ('schema23_name',"UPDATE hwpx_agent.schema_versions SET migration_name='owned.altered_name' WHERE version=23;","UPDATE hwpx_agent.schema_versions SET migration_name='"+actual_name+"' WHERE version=23;"),
            ('schema23_sha',"UPDATE hwpx_agent.schema_versions SET migration_sha256=repeat('0',64) WHERE version=23;","UPDATE hwpx_agent.schema_versions SET migration_sha256='"+actual_sha+"' WHERE version=23;"),
            ('future_schema24',"INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256) VALUES(24,'owned.future',repeat('0',64));","DELETE FROM hwpx_agent.schema_versions WHERE version=24;")]:
            registry(mutate,'inject_'+name);probe('--both-denied','deny_'+name);registry(restore,'restore_'+name);probe('--baseline','restored_'+name);receipt['faults_verified'].append(name)
        cluster.catalogue(binary,port,admin,cluster.migration_rows(),receipt,'final_role_campaign_catalogue23')
        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None
        for pin in manifest['runtime_pins']:cluster.require(cluster.runtime.sha_file(ASSET/pin['path'])==pin['sha256'],'PG_ROLE_FINAL_RUNTIME_BYTES')
        cluster.require(cluster.runtime.sha_file(PROBE)==os.environ.get('P09_ROLE_PROBE_SHA256'),'PG_ROLE_FINAL_PROBE_BYTES')
        receipt.update(state='PASS_ACTUAL_SQL23_ARTIFACT_REVISION_ADMISSION_SCOPE6_AND_FAULTS15_NOT_JOB_CAS_OR_P09_GATE',stage='finished',
            actual_service_profiles_admitted=True,actual_metadata_scope_checks=6,actual_product_worker_or_CAS=False,all_owned_postmasters_normal_stop=True)
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
    receipt=dict(state='FAILED_ACTUAL_SQL23_ROLE_ADMISSION',stage='preflight',commands=[],probes=[],faults_verified=[],
        database_root=str(OWNED/'cluster'),actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,
        actual_service_profiles_admitted=False,actual_product_worker_or_CAS=False,operational_database_accessed=False)
    try:
        cluster.require(sys.argv[1:]==['--owned-sql23-role-admission'],'PG_ROLE_CLOSED_WORKER_MODE');campaign(receipt)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,100}',code)else'PG_ROLE_CAMPAIGN_FAILURE_NO_RAW_DETAIL')
    payload=json.dumps(receipt,separators=(',',':')).encode('utf-8');cluster.require(len(payload)<=262144,'PG_ROLE_OBSERVATION_BYTE_LIMIT')
    target=ROOT/OBSERVATION;cluster.require(not target.exists()and target.parent.is_dir()and not target.parent.is_symlink()and not target.parent.is_junction(),'PG_ROLE_IMMUTABLE_OBSERVATION_PATH')
    with target.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']),fault_count=len(receipt['faults_verified']),
        actual_service_profiles_admitted=receipt['actual_service_profiles_admitted'])),flush=True)
    raise SystemExit(0 if receipt['state'].startswith('PASS_')else 2)
