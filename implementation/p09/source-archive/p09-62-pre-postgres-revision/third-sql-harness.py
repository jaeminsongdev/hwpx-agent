"""Actual Rust -> schema19 PostgreSQL revision adapter, owned loopback DB only; never Hwp."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import uuid
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p14 import test_postgres_migrations as h
ROOT = h.ROOT
FIXTURE = 'tools/p09/fixtures/postgres_revision_adapter.sql'
LEGACY = 'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql'
IR_FIXTURE = 'tools/p09/fixtures/authorized_full_ir_intent.sql'
INITIAL_SEED = 'implementation/p09/source-archive/p09-62-pre-postgres-revision/initial-sql-seed.sql'
LABEL = 'hwpx-agent.p09-revision-adapter-test'
READ_TABLES = ['branches','project_acl','revisions','revision_parents','revision_graph_seals',
    'revision_commit_receipts','full_document_ir_intents']
WRITE_CHECKS = ['empty_real_db_head','no_lease_write_denied','fake_uuid_is_not_real_authority',
    'received_real_first_lease','prevalidation_commit_denied','denied_attempts_preserve_head',
    'lease_bound_to_whole_typed_request','actual_authorized_rust_ir_commit',
    'consumed_real_token_cannot_commit_again','real_success_completion',
    'durable_exact_head','durable_sealed_full_ir_link','read_only_repository_cannot_commit',
    'different_subject_service_read_denied']
READ_CHECKS = WRITE_CHECKS[-4:]
GRANTS = """
GRANT USAGE ON SCHEMA hwpx_agent TO p09_revision_app;
GRANT SELECT ON hwpx_agent.schema_versions TO p09_revision_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id(),hwpx_agent.current_subject_sha256(),
hwpx_agent.register_scheduler_worker(uuid,character,uuid,text,character,text,integer,character),
hwpx_agent.claim_idempotent_job_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character,uuid,character,character,character),
hwpx_agent.lease_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,character),
hwpx_agent.advance_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,text,character),
hwpx_agent.complete_idempotent_job_success_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,character),
hwpx_agent.commit_idempotent_revision_cas_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character),
hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character,uuid,character,character,character)
TO p09_revision_app;
"""
def require(ok,code):
    if not ok:
        raise ValueError(code)
def run(command,env=None,timeout=60):
    return subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=timeout,check=False)
def endpoint(state,run_id):
    require(state['Config']['Labels'].get(LABEL)==run_id,'p62_endpoint_owner')
    bindings=state['NetworkSettings']['Ports'].get('5432/tcp')
    require(isinstance(bindings,list) and len(bindings)==1 and bindings[0]['HostIp']=='127.0.0.1',
        'p62_endpoint_not_exact_loopback')
    port=bindings[0]['HostPort']
    require(re.fullmatch(r'[1-9][0-9]{0,4}',port) is not None and int(port)<=65535,'p62_endpoint_port')
    return port
def main():
    require(Path.cwd().resolve()==ROOT.resolve(),'p62_wrong_root')
    names=[]
    for n in range(1,20):
        files=list((ROOT/'migrations/postgres').glob(f'{n:04}_*.up.sql'))
        require(len(files)==1,'p62_ambiguous_migration')
        names.append(files[0].relative_to(ROOT).as_posix())
    source_names=names+[FIXTURE,LEGACY,IR_FIXTURE,INITIAL_SEED,'Cargo.toml','Cargo.lock',
        'crates/revision-service/Cargo.toml','crates/revision-service/src/lib.rs',
        'crates/revision-service/src/types.rs','crates/revision-service/src/store.rs',
        'crates/revision-service/src/service.rs','crates/revision-service/src/postgres.rs',
        'crates/revision-service/examples/postgres_revision_probe.rs',
        'tools/p09/run_postgres_revision_checks.py','tools/p14/test_postgres_migrations.py']
    texts={p:h.load_bounded_text(ROOT/p,256*1024) for p in source_names}
    pins={p:h.sha256(ROOT/p) for p in source_names}
    docker=shutil.which('docker');cargo=shutil.which('cargo')
    require(docker is not None and cargo is not None,'p62_missing_tools')
    image=h.ensure_image(docker,h.DEFAULT_IMAGE,False)
    build=run([cargo,'build','--offline','--locked','-p','revision-service','--example','postgres_revision_probe'],timeout=180)
    require(build.returncode==0,'p62_probe_build_failed')
    exe=ROOT/'target/debug/examples'/('postgres_revision_probe.exe' if os.name=='nt' else 'postgres_revision_probe')
    require(exe.is_file(),'p62_probe_missing')
    run_id=str(uuid.uuid4())
    container='hwpx-agent-p09-revision-'+run_id.replace('-','')[:12]
    volume='hwpx-agent-p09-revision-data-'+run_id.replace('-','')[:12]
    admin_password=secrets.token_urlsafe(32);app_password=secrets.token_urlsafe(32)
    receipt={'schema':'hwpx-agent.p09-rust-postgres-revision-checks/v1','state':'pending',
        'source_sha256':pins,'image':h.DEFAULT_IMAGE,'image_id':image['Id'],
        'actual_probe_executable_sha256':h.sha256(exe),'run_id':run_id,'container':container,'volume':volume,
        'host_binding':'127.0.0.1_only_ephemeral','host_file_mounts':False,
        'native_activated':False,'p09_complete':False,'checks':[],'probe_runs':[]}
    stage='owned_volume_create';error=None;child=None
    def sql(text):
        nonlocal child
        child=h.psql(docker,container,text,check=False)
        require(child.returncode==0,'p62_sql_stage_failed')
        return child.stdout.strip()
    def inspect_container():
        return json.loads(h.run(docker,['inspect',container]).stdout)[0]
    def probe(mode,environment):
        nonlocal child
        child=run([str(exe)],env=dict(environment,P09_REVISION_PROBE_MODE=mode),timeout=45)
        require(child.returncode==0,'p62_actual_probe_failed')
        value=json.loads(child.stdout.strip())
        expected=WRITE_CHECKS if mode=='write' else READ_CHECKS if mode=='verify' else ['unsafe_database_admission_denied']
        require(value['state']=='pass' and value['mode']==mode and value['checks']==expected
            and value['actual_assertions']==len(expected) and not value['native_activated']
            and not value['p09_complete'],'p62_probe_protocol_mismatch')
        receipt['probe_runs'].append(value)
    try:
        h.run(docker,['volume','create','--label',LABEL+'='+run_id,volume])
        stage='owned_container_create'
        child=run([docker,'run','--detach','--pull','never','--name',container,'--label',LABEL+'='+run_id,
            '--publish','127.0.0.1::5432','--memory','512m','--cpus','2','--pids-limit','128',
            '--mount','type=volume,source='+volume+',target=/var/lib/postgresql',
            '--env','POSTGRES_PASSWORD',h.DEFAULT_IMAGE],env=dict(os.environ,POSTGRES_PASSWORD=admin_password))
        require(child.returncode==0,'p62_container_create_failed')
        h.wait_until_ready(docker,container)
        state=inspect_container()
        port=endpoint(state,run_id)
        require(state['Config']['Image']==h.DEFAULT_IMAGE and state['Name']=='/'+container
            and len(state['Mounts'])==1 and state['Mounts'][0]['Type']=='volume'
            and state['Mounts'][0]['Name']==volume,'p62_container_identity')
        receipt['postgres_version']=sql('SHOW server_version;')
        require(receipt['postgres_version'].startswith('18.4'),'p62_server_version')
        for p in names:
            stage='apply_'+Path(p).stem
            sql("SELECT set_config('hwpx_agent.migration_sha256','"+pins[p]+"',false);\n"+texts[p])
        receipt['schema_versions']=sql("SELECT string_agg(version::text,',' ORDER BY version) FROM hwpx_agent.schema_versions;")
        require(receipt['schema_versions']==','.join(map(str,range(1,20))),'p62_registry_versions')
        stage='original_sql_reconciliation'
        require('P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28' in sql(texts[LEGACY]),'p62_original_sql_assertions')
        receipt['original_sql_assertions']=28
        stage='authorized_ir_sql'
        require(sql(texts[IR_FIXTURE]).splitlines()[-1]=='P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25',
            'p62_authorized_ir_sql_assertions')
        receipt['authorized_ir_sql_assertions']=25
        stage='frozen_initial_seed_failure_reproduction'
        child=h.psql(docker,container,texts[INITIAL_SEED],check=False)
        require(child.returncode==3 and 'artifact_acl_pkey' in child.stderr,'p62_initial_seed_failure_not_reproduced')
        receipt['initial_seed_duplicate_acl_failure_reproduced']=True
        receipt['initial_seed_failure_stderr_sha256']=hashlib.sha256(child.stderr.encode()).hexdigest()
        stage='synthetic_seed_and_role'
        sql(texts[FIXTURE])
        sql("CREATE ROLE p09_revision_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '"+app_password+"';\n"+GRANTS
            +'\nGRANT SELECT ON '+','.join('hwpx_agent.'+t for t in READ_TABLES)+' TO p09_revision_app;')
        environment=dict(os.environ,P09_REVISION_DB_PORT=port,P09_REVISION_DB_PASSWORD=app_password)
        stage='actual_rust_write';probe('write',environment)
        stage='independent_process_reopen';probe('verify',environment)
        receipt['checks'].append('independent_rust_process_seal_hash_ir_link_roundtrip')
        stage='owned_database_restart'
        require(inspect_container()['Config']['Labels'].get(LABEL)==run_id,'p62_restart_owner')
        h.run(docker,['restart',container],timeout=60)
        h.wait_until_ready(docker,container)
        environment['P09_REVISION_DB_PORT']=endpoint(inspect_container(),run_id)
        probe('verify',environment)
        receipt['checks'].append('postgres_restart_retains_exact_typed_request_receipt_and_full_ir_link')
        mutations=[
            ('bypass_role',"ALTER ROLE p09_revision_app BYPASSRLS;","ALTER ROLE p09_revision_app NOBYPASSRLS;"),
            ('disabled_force_rls',"ALTER TABLE hwpx_agent.revisions NO FORCE ROW LEVEL SECURITY;","ALTER TABLE hwpx_agent.revisions FORCE ROW LEVEL SECURITY;"),
            ('disabled_original_commit_guard',"ALTER TABLE hwpx_agent.revision_commit_receipts DISABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;","ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;"),
            ('disabled_new_intent_guard',"ALTER TABLE hwpx_agent.revision_commit_receipts DISABLE TRIGGER revision_commit_receipts_full_ir_intent_guard;","ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE TRIGGER revision_commit_receipts_full_ir_intent_guard;"),
            ('direct_auth_write_grant',"GRANT INSERT ON hwpx_agent.idempotency_commit_authorizations TO p09_revision_app;","REVOKE INSERT ON hwpx_agent.idempotency_commit_authorizations FROM p09_revision_app;"),
        ]
        for code,mutate,restore in mutations:
            stage='admission_'+code
            sql(mutate)
            try:probe('reject-admission',environment)
            finally:sql(restore)
            receipt['checks'].append(code+'_rejected_by_actual_adapter')
        stage='restored_guard_final_reopen'
        probe('verify',environment)
        receipt['checks'].append('all_owned_test_mutations_restored_before_final_fresh_read')
        require(pins=={p:h.sha256(ROOT/p) for p in source_names},'p62_sources_changed')
        receipt['state']='pass'
    except Exception as caught:
        error=caught;receipt['state']='fail';receipt['failed_stage']=stage
        receipt['error_type']=type(caught).__name__
        receipt['error_code']=str(caught) if re.fullmatch(r'[a-z0-9_]+',str(caught)) else 'redacted_error'
        if child is not None:
            receipt['actual_child_exit_code']=child.returncode
            receipt['actual_child_stdout_sha256']=hashlib.sha256(child.stdout.encode()).hexdigest()
            receipt['actual_child_stderr_sha256']=hashlib.sha256(child.stderr.encode()).hexdigest()
            receipt['safe_probe_diagnostics']=re.findall(r'P09_POSTGRES_REVISION_(?:PROBE_FAILED code|CHECK_FAILED check)=([A-Za-z0-9_]+)',child.stderr)
            receipt['safe_connect_stages']=re.findall(r'P09_POSTGRES_REVISION_CONNECT_FAILED stage=([A-Z_]+)',child.stderr)
            receipt['constant_sql_diagnostics']=sorted(set(re.findall(r'(?:FULL_IR_|IDEMPOTENCY_|REVISION_)[A-Z_]+',child.stderr)))
            receipt['sql_identifier_diagnostics']=sorted(set(re.findall(r'(?:column|relation|constraint) "([a-z_][a-z_0-9]{0,80})"',child.stderr)))
    finally:
        status=h.run(docker,['inspect',container],check=False)
        if status.returncode==0:
            state=json.loads(status.stdout)[0]
            require(state['Config']['Labels'].get(LABEL)==run_id and state['Name']=='/'+container
                and state['Config']['Image']==h.DEFAULT_IMAGE,'p62_cleanup_container_owner')
            h.run(docker,['rm','--force',container],timeout=60)
        status=h.run(docker,['volume','inspect',volume],check=False)
        if status.returncode==0:
            state=json.loads(status.stdout)[0]
            require(state['Labels'].get(LABEL)==run_id and state['Name']==volume,'p62_cleanup_volume_owner')
            h.run(docker,['volume','rm',volume],timeout=60)
        receipt['container_removed']=h.run(docker,['inspect',container],check=False).returncode!=0
        receipt['volume_removed']=h.run(docker,['volume','inspect',volume],check=False).returncode!=0
        require(receipt['container_removed'] and receipt['volume_removed'],'p62_owned_cleanup_failed')
    print(json.dumps(receipt,sort_keys=True))
    return 0 if error is None else 2
if __name__=='__main__':
    raise SystemExit(main())

