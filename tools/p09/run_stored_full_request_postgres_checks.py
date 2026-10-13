"""Actual stored-full-IR request against owned PostgreSQL19 + host encrypted fixture files; no Hwp."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p14 import test_postgres_migrations as h
from tools.p09.run_postgres_revision_graph_checks import GRANTS, READ_TABLES

ROOT=h.ROOT
LABEL='hwpx-agent.p09-full-request-test'
CASES=['five-kinds','empty-text','reset-defaults','clear-selections']
COMMON=['strict_request_whole_output','full_graph_digest_plan','fresh_verify_exact','whole_non_state_graph_fields_exact',
        'route_denied_no_publication','encrypted_package_ir_not_plaintext']
SEED=['baseline_artifacts_ingested','real_authorized_sealed_root']
SAFETY=['ir_acl_revocation_precedes_route','source_survives_ir_acl_revocation','ir_acl_restore_fresh_verify',
        'wrong_aes_key_denied_from_actual_files','head_and_ingest_counts_unchanged','ir_quarantine_fresh_verify_denied',
        'source_survives_ir_quarantine','ir_quarantine_storage_state_persisted']
ACTUAL_IMPORT=['actual_locked_source_digest','actual_whole_graph_observations_exact','fresh_actual_import_verify_exact',
              'actual_complete_policy_graph_state_exact','fresh_actual_bound_policy_verify_exact','actual_partial_product_denied',
              'actual_head_and_ingest_unchanged','actual_source_encrypted_not_plaintext']
ACTUAL_IMPORT_SAFETY=['actual_result_acl_revocation_import_denied','actual_result_acl_revocation_cached_import_denied',
                     'actual_result_acl_revocation_cached_policy_denied','actual_result_acl_restore_exact',
                     'actual_source_wrong_aes_key_denied','actual_safety_head_ingest_unchanged','actual_cached_receipt_stays_partial']
CONTEXT="""
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES ('00000000-0000-0000-0000-000000000001','p65-owned-test');
INSERT INTO hwpx_agent.retention_policies(tenant_id,retention_policy_id,tombstone_grace_seconds,created_by_subject_sha256)
VALUES ('00000000-0000-0000-0000-000000000001','retention.p65-owned-test',0,repeat('a',64));
INSERT INTO hwpx_agent.projects(tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
'p65-owned-test','Synthetic baseline','hancom-hangul-2020-secondary','retention.p65-owned-test');
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',repeat('a',64),'owner');
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
SELECT '00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
('00000000-0000-0000-0000-'||lpad(to_hex(100+n),12,'0'))::uuid,'p65-'||n::text,n=0,repeat('a',64)
FROM generate_series(0,3) n;
COMMIT;
"""

def require(ok,code):
    if not ok:raise ValueError(code)
def run(args,env=None,timeout=60):
    return subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,
                          encoding='utf-8',errors='replace',timeout=timeout,check=False)
def endpoint(state,run_id):
    require(state['Config']['Labels'].get(LABEL)==run_id,'p65_endpoint_owner')
    value=state['NetworkSettings']['Ports'].get('5432/tcp')
    require(isinstance(value,list) and len(value)==1 and value[0]['HostIp']=='127.0.0.1','p65_loopback')
    port=value[0]['HostPort']
    require(re.fullmatch(r'[1-9][0-9]{0,4}',port) and int(port)<=65535,'p65_port')
    return port
def main():
    require(Path.cwd().resolve()==ROOT.resolve(),'p65_root')
    migrations=[]
    for version in range(1,20):
        files=list((ROOT/'migrations/postgres').glob(f'{version:04}_*.up.sql'))
        require(len(files)==1,'p65_migration_identity')
        migrations.append(files[0].relative_to(ROOT).as_posix())
    files=migrations+[
        'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml','crates/product-cli/src/lib.rs',
        'crates/product-cli/src/form_product_request.rs','crates/product-cli/src/form_product_request/stored.rs',
        'crates/product-cli/src/form_product_request/stored_full_document.rs','crates/product-cli/src/form_stored_provider.rs',
        'crates/product-cli/src/form_stored_provider/full_document.rs','crates/product-cli/src/form_value_operation.rs',
        'crates/product-cli/src/form_value_operation/full_document.rs','crates/product-cli/src/form_value_preparation.rs',
        'crates/product-cli/examples/stored_full_document_request_probe.rs',
        'crates/product-cli/examples/support/stored_full_request_fixture.rs','crates/product-cli/examples/support/stored_full_request_worker.rs',
        'crates/product-cli/examples/support/stored_full_request_safety.rs',
        'crates/product-cli/tests/form_stored_provider.rs','crates/artifact-service/src/service.rs',
        'crates/artifact-service/src/store.rs','crates/artifact-service/src/store/postgres_repository.rs',
        'crates/artifact-service/src/crypto.rs','crates/artifact-service/src/types.rs',
        'crates/revision-service/src/postgres.rs','crates/revision-service/src/service.rs',
        'crates/revision-service/src/types.rs','crates/revision-service/src/store.rs',
        'tools/p14/test_postgres_migrations.py','tools/p09/run_postgres_revision_graph_checks.py',
        'tools/p09/run_stored_full_request_postgres_checks.py','tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql',
        'tools/p09/fixtures/authorized_full_ir_intent.sql',
        'fixtures/target-build/p09-42-product-form-values-01/output/fixture-manifest.json']
    manifest_path='fixtures/target-build/p09-42-product-form-values-01/output/fixture-manifest.json'
    require(h.sha256(ROOT/manifest_path)=='8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e','p65_fixture_manifest')
    fixture=json.loads(h.load_bounded_text(ROOT/manifest_path,1024*1024))
    for row in fixture['cases']:
        if row['case'] in CASES:
            for key in ['source','output']:files.append(str(Path(manifest_path).parent/row[key]['path']).replace('\\','/'))
    files=list(dict.fromkeys(files));pins={p:h.sha256(ROOT/p) for p in files}
    for path in ['crates/product-cli/examples/support/stored_actual_import.rs',
                 'crates/product-cli/src/form_stored_provider/actual_import.rs',
                 'crates/hwpx-package/src/document_import.rs','crates/hwpx-package/src/document_import/structure.rs',
                 'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/forms/policies.rs',
                 'crates/hwpx-package/examples/document_import_form_policies_support/mod.rs']:
        require(path not in files,'p71_duplicate_source_pin');files.append(path);pins[path]=h.sha256(ROOT/path)
    texts={p:h.load_bounded_text(ROOT/p,1024*1024) for p in migrations}
    docker=shutil.which('docker');cargo=shutil.which('cargo')
    require(docker and cargo,'p65_missing_tools');image=h.ensure_image(docker,h.DEFAULT_IMAGE,False)
    build=run([cargo,'build','--offline','--locked','-p','hwpx-agent-cli','--example','stored_full_document_request_probe'],timeout=180)
    require(build.returncode==0,'p65_build_failed')
    exe=ROOT/'target/debug/examples'/('stored_full_document_request_probe.exe' if os.name=='nt' else 'stored_full_document_request_probe')
    require(exe.is_file(),'p65_executable_missing')
    run_id=str(uuid.uuid4());suffix=run_id.replace('-','')[:12]
    container='hwpx-agent-p09-full-request-'+suffix;volume='hwpx-agent-p09-full-request-data-'+suffix
    temp_base=Path(tempfile.gettempdir()).resolve()
    blob_root=Path(tempfile.mkdtemp(prefix='hwpx-agent-p65-'+suffix+'-',dir=temp_base))
    require(blob_root.resolve()==blob_root and blob_root.parent==temp_base,'p65_owned_blob_root')
    admin_password=secrets.token_urlsafe(32);artifact_password=secrets.token_urlsafe(32);revision_password=secrets.token_urlsafe(32)
    receipt={'schema':'hwpx-agent.p09-stored-full-request-postgres-checks/v2','state':'pending','run_id':run_id,
             'source_sha256':pins,'actual_probe_executable_sha256':h.sha256(exe),'container':container,'volume':volume,
             'image':h.DEFAULT_IMAGE,'image_id':image['Id'],'host_binding':'127.0.0.1_only_ephemeral','host_file_mounts':False,
             'fixture_scanner_graph_and_baseline_authority':'synthetic_not_native_or_signed_execution',
             'native_activated':False,'p09_complete':False,'checks':[],'probe_runs':[]}
    receipt['actual_source_import_scope']='actual_Result_PG_and_AEAD_file_read_partial_graph_explicit_TEST_policy_not_full_IR_persistence_or_issuer'
    stage='owned_volume';error=None;child=None
    def sql(text):
        nonlocal child
        child=h.psql(docker,container,text,check=False);require(child.returncode==0,'p65_sql_failed');return child.stdout.strip()
    def inspect():return json.loads(h.run(docker,['inspect',container]).stdout)[0]
    def probe(mode,environment):
        nonlocal child
        child=run([str(exe)],env=dict(environment,P65_MODE=mode),timeout=90)
        require(child.returncode==0,'p65_probe_failed');value=json.loads(child.stdout.strip())
        if mode=='seed':expected=[[label,name] for label in CASES for name in SEED]+[[label,name] for label in CASES for name in COMMON]
        elif mode=='verify':expected=[[label,name] for label in CASES for name in COMMON]
        elif mode=='denied':expected=[[label,'project_acl_denied'] for label in CASES]
        elif mode=='safety':expected=[[CASES[0],name] for name in SAFETY]
        elif mode=='actual_import':expected=[[label,name] for label in CASES for name in ACTUAL_IMPORT]
        elif mode=='actual_import_denied':expected=[[label,'actual_project_acl_denied'] for label in CASES]
        elif mode=='actual_import_safety':expected=[[CASES[0],name] for name in ACTUAL_IMPORT_SAFETY]
        else:raise ValueError('p65_unknown_mode')
        require(value['state']=='pass' and value['mode']==mode and value['checks']==expected and value['actual_assertions']==len(expected)
                and value['native_activated'] is False and value['p09_complete'] is False,'p65_protocol_mismatch')
        if mode=='verify':require(value['receipt_sha256']==receipt['probe_runs'][0]['receipt_sha256'] and value['candidate_sha256']==receipt['probe_runs'][0]['candidate_sha256'],'p65_fresh_identity_drift')
        if mode=='actual_import':
            require(value['candidate_sha256']==[] and len(value['receipt_sha256'])==4,'p71_actual_receipt_scope')
            earlier=next((r for r in receipt['probe_runs'] if r['mode']=='actual_import'),None)
            if earlier:require(value['receipt_sha256']==earlier['receipt_sha256'],'p71_actual_fresh_receipt_drift')
        receipt['probe_runs'].append(value)
    try:
        h.run(docker,['volume','create','--label',LABEL+'='+run_id,volume])
        stage='owned_container'
        child=run([docker,'run','--detach','--pull','never','--name',container,'--label',LABEL+'='+run_id,
                   '--publish','127.0.0.1::5432','--memory','512m','--cpus','2','--pids-limit','128',
                   '--mount','type=volume,source='+volume+',target=/var/lib/postgresql',
                   '--env','POSTGRES_PASSWORD',h.DEFAULT_IMAGE],env=dict(os.environ,POSTGRES_PASSWORD=admin_password))
        require(child.returncode==0,'p65_container_create');h.wait_until_ready(docker,container)
        state=inspect();port=endpoint(state,run_id)
        require(state['Config']['Image']==h.DEFAULT_IMAGE and state['Name']=='/'+container and len(state['Mounts'])==1 and state['Mounts'][0]['Type']=='volume' and state['Mounts'][0]['Name']==volume,'p65_container_identity')
        receipt['postgres_version']=sql('SHOW server_version;');require(receipt['postgres_version'].startswith('18.4'),'p65_server_version')
        for path in migrations:
            stage='apply_'+Path(path).stem;sql("SELECT set_config('hwpx_agent.migration_sha256','"+pins[path]+"',false);\n"+texts[path])
        receipt['schema_versions']=sql("SELECT string_agg(version::text,',' ORDER BY version) FROM hwpx_agent.schema_versions;")
        require(receipt['schema_versions']==','.join(map(str,range(1,20))),'p65_schema_versions')
        stage='original_sql28';require('P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28' in sql(h.load_bounded_text(ROOT/'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql',1024*1024)),'p65_original_sql')
        stage='original_authorized_ir25';require(sql(h.load_bounded_text(ROOT/'tools/p09/fixtures/authorized_full_ir_intent.sql',1024*1024)).splitlines()[-1]=='P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25','p65_original_ir_sql')
        receipt['original_sql_assertions']=53
        stage='context_and_least_privilege_roles';sql(CONTEXT)
        sql("CREATE ROLE p09_revision_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 8 PASSWORD '"+revision_password+"';\n"+GRANTS)
        for table in READ_TABLES:sql('GRANT SELECT ON hwpx_agent.'+table+' TO p09_revision_app;')
        sql("CREATE ROLE p65_artifact_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 8 PASSWORD '"+artifact_password+"';\n"+"""
GRANT USAGE ON SCHEMA hwpx_agent TO p65_artifact_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p65_artifact_app;
GRANT SELECT ON hwpx_agent.schema_versions TO p65_artifact_app;
GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts TO p65_artifact_app;
GRANT SELECT,INSERT,UPDATE,DELETE ON hwpx_agent.artifact_acl TO p65_artifact_app;
GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit TO p65_artifact_app;
GRANT USAGE ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq TO p65_artifact_app;
""")
        environment=dict(os.environ,P65_DB_PORT=port,P65_REVISION_PASSWORD=revision_password,
                         P65_ARTIFACT_PASSWORD=artifact_password,P65_BLOB_ROOT=str(blob_root))
        stage='actual_artifacts_worker_commit_request';probe('seed',environment)
        stage='actual_source_import_after_seed';probe('actual_import',environment)
        stage='independent_process';probe('verify',environment)
        receipt['checks'].append('actual_four_request_package_ir_encrypted_file_service_paths')
        stage='database_restart';require(inspect()['Config']['Labels'].get(LABEL)==run_id,'p65_restart_owner')
        h.run(docker,['restart',container],timeout=60);h.wait_until_ready(docker,container)
        environment['P65_DB_PORT']=endpoint(inspect(),run_id);probe('verify',environment)
        stage='actual_source_import_after_database_restart';probe('actual_import',environment)
        receipt['checks'].append('independent_process_and_postgres_restart_exact_receipt_candidate_hashes')
        stage='actual_project_acl_revoke';sql("DELETE FROM hwpx_agent.project_acl WHERE project_id='00000000-0000-0000-0000-000000000002' AND subject_sha256=repeat('a',64);")
        try:
            probe('denied',environment)
            probe('actual_import_denied',environment)
        finally:sql("INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role) VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',repeat('a',64),'owner');")
        stage='acl_restored_fresh_process';probe('verify',environment)
        stage='actual_source_import_after_acl_restore';probe('actual_import',environment)
        receipt['checks'].append('actual_project_acl_denied_four_requests_and_restored')
        stage='actual_ir_acl_wrong_key_quarantine';probe('safety',environment)
        stage='actual_source_import_result_acl_and_wrong_key';probe('actual_import_safety',environment)
        stage='actual_source_import_survives_unrelated_ir_quarantine';probe('actual_import',environment)
        receipt['checks'].append('actual_source_import_restart_ACL_wrong_key_and_independent_of_synthetic_IR')
        receipt['checks'].append('actual_ir_acl_restore_wrong_key_and_encrypted_ir_quarantine')
        stage='read_only_sql_postconditions'
        tenant="tenant_id='00000000-0000-0000-0000-000000000001'"
        counts=[]
        for table in ['revisions','revision_graph_seals','revision_commit_receipts','full_document_ir_intents']:
            value=sql('SELECT count(*) FROM hwpx_agent.'+table+' WHERE '+tenant+';');require(value=='4','p65_exact_root_graph_count');counts.append(table)
        require(sql("SELECT count(*) FROM hwpx_agent.jobs WHERE "+tenant+" AND state='succeeded';")=='4','p65_jobs_terminal')
        receipt['sql_postconditions']=counts+['exact_terminal_jobs_four']
        require(pins=={p:h.sha256(ROOT/p) for p in files},'p65_sources_changed')
        receipt['state']='pass'
    except Exception as caught:
        error=caught;receipt['state']='fail';receipt['failed_stage']=stage;receipt['error_type']=type(caught).__name__
        receipt['error_code']=str(caught) if re.fullmatch('[a-z0-9_]+',str(caught)) else 'redacted_error'
        if child is not None:
            receipt['actual_child_exit_code']=child.returncode
            receipt['actual_child_stdout_sha256']=hashlib.sha256(child.stdout.encode()).hexdigest()
            receipt['actual_child_stderr_sha256']=hashlib.sha256(child.stderr.encode()).hexdigest()
            receipt['safe_probe_diagnostics']=re.findall(r'P65_(?:PROBE_FAILED code|CHECK_FAILED check|CONNECT_FAILED stage|DB_ERROR code)=([A-Za-z0-9_]+)',child.stderr)
            receipt['safe_database_constraints']=re.findall(r'P65_DB_CONSTRAINT name=([a-z_0-9]+)',child.stderr)
            receipt['safe_failure_phases']=re.findall(r'P65_PHASE_FAILED phase=([A-Z_]+)',child.stderr)
    finally:
        status=h.run(docker,['inspect',container],check=False)
        if status.returncode==0:
            state=json.loads(status.stdout)[0];require(state['Config']['Labels'].get(LABEL)==run_id and state['Name']=='/'+container and state['Config']['Image']==h.DEFAULT_IMAGE,'p65_cleanup_container_owner')
            h.run(docker,['rm','--force',container],timeout=60)
        status=h.run(docker,['volume','inspect',volume],check=False)
        if status.returncode==0:
            state=json.loads(status.stdout)[0];require(state['Labels'].get(LABEL)==run_id and state['Name']==volume,'p65_cleanup_volume_owner');h.run(docker,['volume','rm',volume],timeout=60)
        receipt['container_removed']=h.run(docker,['inspect',container],check=False).returncode!=0
        receipt['volume_removed']=h.run(docker,['volume','inspect',volume],check=False).returncode!=0
        require(blob_root.resolve()==blob_root and blob_root.parent==temp_base and blob_root.name.startswith('hwpx-agent-p65-'+suffix+'-') and not blob_root.is_symlink(),'p65_cleanup_blob_owner')
        receipt['owned_ciphertext_files']=sum(p.is_file() for p in blob_root.rglob('*'))
        receipt['owned_blob_tree_bytes']=sum(p.stat().st_size for p in blob_root.rglob('*') if p.is_file())
        shutil.rmtree(blob_root);receipt['owned_blob_root_removed']=not blob_root.exists()
        require(receipt['container_removed'] and receipt['volume_removed'] and receipt['owned_blob_root_removed'],'p65_cleanup_failed')
    print(json.dumps(receipt,sort_keys=True));return 0 if error is None else 2
if __name__=='__main__':raise SystemExit(main())
