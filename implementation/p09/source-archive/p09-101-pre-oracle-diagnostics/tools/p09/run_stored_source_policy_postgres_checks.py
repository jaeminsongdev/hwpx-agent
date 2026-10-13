"""Owned PostgreSQL20 / real disk AEAD / original source consumer; no Hwp or operational DB."""
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
from tools.p09.run_stored_full_request_postgres_checks import CONTEXT

ROOT = h.ROOT
LABEL = 'hwpx-agent.p09-policy-service-test'
PROBE = 'crates/product-cli/examples/stored_source_policy_postgres_probe.rs'
def require(ok, code):
    if not ok:
        raise ValueError(code)
def run(args, env=None, timeout=90):
    return subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=timeout, check=False)
def main():
    require(Path.cwd().resolve() == ROOT.resolve(), 'p84_wrong_root')
    migrations = []
    for n in range(1, 21):
        names = list((ROOT/'migrations/postgres').glob(f'{n:04}_*.up.sql'))
        require(len(names) == 1, 'p84_migration_identity')
        migrations.append(names[0].relative_to(ROOT).as_posix())
    files = migrations + ['Cargo.toml', 'Cargo.lock', 'crates/product-cli/Cargo.toml', PROBE,
        'crates/product-cli/examples/stored_source_policy_postgres_probe/worker.rs',
        'crates/product-cli/src/form_stored_provider.rs', 'crates/product-cli/src/form_stored_provider/actual_import.rs',
        'crates/product-cli/src/form_stored_provider/actual_import/source_policy.rs',
        'crates/product-cli/src/form_stored_provider/actual_import/source_policy/wire.rs',
        'crates/product-cli/src/form_stored_provider/actual_import/source_policy/postgres.rs',
        'crates/artifact-service/src/store/postgres_repository.rs',
        'crates/artifact-service/src/store/postgres_repository/source_form_policy.rs',
        'crates/artifact-service/src/store.rs', 'crates/artifact-service/src/service.rs', 'crates/artifact-service/src/crypto.rs',
        'crates/revision-service/src/postgres.rs', 'crates/revision-service/src/postgres/source_form_policy.rs',
        'crates/revision-service/src/types.rs', 'crates/revision-service/src/service.rs',
        'crates/hwpx-package/src/document_import/forms/policies.rs',
        'crates/hwpx-package/examples/document_import_form_policies_support/mod.rs',
        'tools/p09/run_stored_source_policy_postgres_checks.py', 'tools/p09/run_stored_full_request_postgres_checks.py',
        'tools/p09/run_postgres_revision_graph_checks.py', 'tools/p14/test_postgres_migrations.py',
        'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql', 'tools/p09/fixtures/authorized_full_ir_intent.sql',
        'tools/p09/fixtures/source_form_policy.sql',
        'fixtures/target-build/p09-42-product-form-values-01/output/fixture-manifest.json']
    manifest = files[-1]
    require(h.sha256(ROOT/manifest) == '8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e', 'p84_fixture_identity')
    fixtures = json.loads(h.load_bounded_text(ROOT/manifest, 1024*1024))
    for row in fixtures['cases']:
        for kind in ['source', 'output']:
            path = str(Path(manifest).parent/row[kind]['path']).replace('\\', '/')
            require(h.sha256(ROOT/path) == row[kind]['sha256'], 'p84_original_fixture_changed')
            files.append(path)
    files = list(dict.fromkeys(files))
    for path in files:
        source = ROOT/path
        require(source.is_file() and not source.is_symlink() and not source.is_junction(), 'p84_source_link')
    pins = {p: h.sha256(ROOT/p) for p in files}
    texts = {p: h.load_bounded_text(ROOT/p, 1024*1024) for p in migrations}
    docker = shutil.which('docker'); cargo = shutil.which('cargo')
    require(docker and cargo, 'p84_missing_tool')
    image = h.ensure_image(docker, h.DEFAULT_IMAGE, False)
    build = run([cargo, 'build', '--offline', '--locked', '-p', 'hwpx-agent-cli', '--example', 'stored_source_policy_postgres_probe'], timeout=180)
    require(build.returncode == 0, 'p84_build_failed')
    exe = ROOT/'target/debug/examples'/('stored_source_policy_postgres_probe.exe' if os.name == 'nt' else 'stored_source_policy_postgres_probe')
    require(exe.is_file(), 'p84_probe_missing')
    run_id = str(uuid.uuid4()); suffix = run_id.replace('-', '')[:12]
    container = 'hwpx-agent-p09-policy-service-'+suffix
    temp_base = Path(tempfile.gettempdir()).resolve()
    blob_root = Path(tempfile.mkdtemp(prefix='hwpx-agent-p84-'+suffix+'-', dir=temp_base))
    require(blob_root.resolve() == blob_root and blob_root.parent == temp_base, 'p84_blob_owner')
    passwords = [secrets.token_hex(32) for _ in range(3)]
    receipt = {'schema': 'hwpx-agent.p09-84-stored-policy-postgres-checks/v1', 'state': 'pending', 'run_id': run_id,
        'container': container, 'image': h.DEFAULT_IMAGE, 'image_id': image['Id'], 'source_sha256': pins,
        'probe_executable_sha256': h.sha256(exe), 'host_binding': '127.0.0.1_only_ephemeral', 'host_file_mounts': False,
        'storage': 'owned_postgres_tmpfs_and_owned_host_encrypted_test_directory', 'probe_runs': [], 'checks': [],
        'native_executed': False, 'real_scanner_or_issuer_qualified': False, 'p09_complete': False}
    stage = 'create_owned_container'; error = None; child = None
    def sql(text):
        nonlocal child
        child = h.psql(docker, container, text, check=False)
        require(child.returncode == 0, 'p84_sql_failed')
        return child.stdout.strip()
    def inspect():
        return json.loads(h.run(docker, ['inspect', container]).stdout)[0]
    def environment():
        state = inspect()
        require(state['Config']['Labels'].get(LABEL) == run_id and state['Name'] == '/'+container and state['Config']['Image'] == h.DEFAULT_IMAGE, 'p84_container_identity')
        bindings = state['NetworkSettings']['Ports'].get('5432/tcp')
        require(isinstance(bindings, list) and len(bindings) == 1 and bindings[0]['HostIp'] == '127.0.0.1', 'p84_loopback')
        port = bindings[0]['HostPort']
        require(re.fullmatch(r'[1-9][0-9]{0,4}', port) and int(port) <= 65535, 'p84_port')
        require(state['Mounts'] == [] and state['HostConfig']['Tmpfs'] == {'/var/lib/postgresql': 'rw,noexec,nosuid,size=512m'}, 'p84_no_host_mount')
        return dict(os.environ, P84_DB_PORT=port, P84_ARTIFACT_PASSWORD=passwords[1], P84_REVISION_PASSWORD=passwords[2], P84_BLOB_ROOT=str(blob_root))
    def probe(mode, expected):
        nonlocal child
        child = run([str(exe)], env=dict(environment(), P84_MODE=mode), timeout=180)
        require(child.returncode == 0, 'p84_probe_failed')
        result = json.loads(child.stdout.strip())
        require(result['state'] == 'pass' and result['mode'] == mode and result['checks'] == expected, 'p84_probe_protocol')
        if mode == 'verify':
            earlier = receipt['probe_runs'][0]
            require(result['receipt_sha256'] == earlier['receipt_sha256'], 'p84_fresh_receipt_drift')
        receipt['probe_runs'].append(result)
    try:
        child = run([docker, 'run', '--detach', '--pull', 'never', '--name', container, '--label', LABEL+'='+run_id,
            '--publish', '127.0.0.1::5432', '--memory', '512m', '--cpus', '2', '--pids-limit', '128',
            '--tmpfs', '/var/lib/postgresql:rw,noexec,nosuid,size=512m', '--env', 'POSTGRES_PASSWORD', h.DEFAULT_IMAGE],
            env=dict(os.environ, POSTGRES_PASSWORD=passwords[0]))
        require(child.returncode == 0, 'p84_create_failed'); h.wait_until_ready(docker, container)
        environment()
        for path in migrations:
            stage = 'apply_'+Path(path).stem
            sql("SELECT set_config('hwpx_agent.migration_sha256','"+pins[path]+"',false);\n"+texts[path])
        receipt['schema_versions'] = sql("SELECT string_agg(version::text,',' ORDER BY version) FROM hwpx_agent.schema_versions;")
        require(receipt['schema_versions'] == ','.join(map(str, range(1, 21))), 'p84_schema_versions')
        for path, marker in [('tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql', 'assertions=28'),
            ('tools/p09/fixtures/authorized_full_ir_intent.sql', 'assertions=25'),
            ('tools/p09/fixtures/source_form_policy.sql', 'assertions=32')]:
            stage = 'original_sql_'+Path(path).stem
            require(marker in sql(h.load_bounded_text(ROOT/path, 1024*1024)), 'p84_original_sql_checks')
        receipt['unchanged_SQL_metadata_checks'] = 85
        stage = 'provision_owned_context_roles'
        sql(CONTEXT.replace('p65-owned-test', 'p84-owned-test').replace('generate_series(0,3)', 'generate_series(0,9)'))
        sql("CREATE ROLE p84_revision_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 32 PASSWORD '"+passwords[2]+"';\n"+GRANTS.replace('p09_revision_app', 'p84_revision_app'))
        for table in READ_TABLES:
            sql('GRANT SELECT ON hwpx_agent.'+table+' TO p84_revision_app;')
        sql("""GRANT EXECUTE ON FUNCTION
hwpx_agent.claim_idempotent_job_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character),
hwpx_agent.read_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint),
hwpx_agent.register_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character),
hwpx_agent.revoke_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)
TO p84_revision_app;""")
        sql("CREATE ROLE p84_artifact_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 32 PASSWORD '"+passwords[1]+"';\n"+"""
GRANT USAGE ON SCHEMA hwpx_agent TO p84_artifact_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p84_artifact_app;
GRANT SELECT ON hwpx_agent.schema_versions TO p84_artifact_app;
GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts TO p84_artifact_app;
GRANT SELECT,INSERT,UPDATE,DELETE ON hwpx_agent.artifact_acl TO p84_artifact_app;
GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit TO p84_artifact_app;
GRANT USAGE ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq TO p84_artifact_app;
""")
        stage = 'real_encrypted_policy_sealed_source_seed'; probe('seed', 70)
        stage = 'fresh_process_exact_policy'; probe('verify', 40)
        receipt['checks'].append('ten_real_postgres_artifacts_source_policy_and_encrypted_disk_paths')
        for name, mutate, restore in [
            ('changed_migration_digest', "UPDATE hwpx_agent.schema_versions SET migration_sha256=repeat('0',64) WHERE version=20;", "UPDATE hwpx_agent.schema_versions SET migration_sha256='"+pins[migrations[-1]]+"' WHERE version=20;"),
            ('future_schema', "INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256) VALUES(21,'synthetic_future',repeat('0',64));", "DELETE FROM hwpx_agent.schema_versions WHERE version=21;")]:
            # Owned disposable admin fault injection only: restore registry immutability
            # inside the same transaction BEFORE either application connector runs.
            stage = name
            def registry_fault(statement):
                sql('BEGIN; ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable; '
                    + statement + ' ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable; COMMIT;')
                require(sql("SELECT tgenabled FROM pg_trigger WHERE tgrelid='hwpx_agent.schema_versions'::regclass AND tgname='schema_versions_immutable';") == 'O', 'p84_registry_guard_not_restored')
            registry_fault(mutate)
            try: probe('admission_denied', 2)
            finally: registry_fault(restore)
            receipt['checks'].append(name)
        for name, mutate, restore in [
            ('policy_direct_table_grant', 'GRANT SELECT ON hwpx_agent.source_form_policy_versions TO p84_revision_app;', 'REVOKE SELECT ON hwpx_agent.source_form_policy_versions FROM p84_revision_app;'),
            ('policy_force_rls_disabled', 'ALTER TABLE hwpx_agent.source_form_policy_versions NO FORCE ROW LEVEL SECURITY;', 'ALTER TABLE hwpx_agent.source_form_policy_versions FORCE ROW LEVEL SECURITY;'),
            ('policy_helper_execute', 'GRANT EXECUTE ON FUNCTION hwpx_agent.require_source_form_policy_role_v1(uuid,uuid,character,boolean) TO p84_revision_app;', 'REVOKE EXECUTE ON FUNCTION hwpx_agent.require_source_form_policy_role_v1(uuid,uuid,character,boolean) FROM p84_revision_app;')]:
            stage = name; sql(mutate)
            try: probe('revision_admission_denied', 1)
            finally: sql(restore)
            receipt['checks'].append(name)
        stage = 'policy_acl_revoke_and_append_only_revocations'; probe('safety', 80)
        stage = 'independent_revoked_policy_no_fallback'; probe('denied', 10)
        require(pins == {p: h.sha256(ROOT/p) for p in files}, 'p84_sources_changed')
        require(sql("SELECT count(*) FROM hwpx_agent.source_form_policy_versions WHERE tenant_id='00000000-0000-0000-0000-000000000001';") == '10', 'p84_policy_version_count')
        require(sql("SELECT count(*) FROM hwpx_agent.source_form_policy_revocations WHERE tenant_id='00000000-0000-0000-0000-000000000001';") == '10', 'p84_revocation_count')
        receipt['state'] = 'pass'
    except Exception as caught:
        error = caught; receipt['state'] = 'fail'; receipt['failed_stage'] = stage
        receipt['error_type'] = type(caught).__name__
        receipt['error_code'] = str(caught) if re.fullmatch(r'[a-z0-9_]+', str(caught)) else 'redacted_error'
        if child:
            receipt['child_exit_code'] = child.returncode
            receipt['child_stdout_sha256'] = hashlib.sha256(child.stdout.encode()).hexdigest()
            receipt['child_stderr_sha256'] = hashlib.sha256(child.stderr.encode()).hexdigest()
            receipt['safe_probe_diagnostics'] = re.findall(r'P84_DB_ERROR code=([A-Z0-9_]+)', child.stderr)
            receipt['safe_closed_reasons'] = re.findall(r'P84_DB_CLOSED_REASON code=(IDEMPOTENCY_COMMITTED_ORACLE_FAILED)', child.stderr)
            receipt['safe_sql_fixture_reasons'] = sorted(set(re.findall(r'\b(?:FORM_POLICY|TEST_POLICY|IDEMPOTENCY|TEST_AUTHORIZED_IR)_[A-Z0-9_]{1,96}\b', child.stderr)))
        if stage == 'real_encrypted_policy_sealed_source_seed':
            # Read-only Boolean diagnostics for this run's synthetic tenant only.
            diagnostic = h.psql(docker, container, """
SELECT coalesce(json_agg(json_build_object(
 'source', hwpx_agent.idempotency_v2_artifact_qualified(r.tenant_id,r.subject_sha256,r.source_artifact_id,'source',r.source_artifact_sha256),
 'receipt', EXISTS(SELECT 1 FROM hwpx_agent.artifacts a WHERE a.tenant_id=r.tenant_id AND a.artifact_kind='receipt' AND a.content_sha256=r.transaction_receipt_sha256),
 'head', b.head_revision_id IS NOT NULL AND b.head_generation=1,
 'seal', s.transaction_receipt_sha256=r.transaction_receipt_sha256,
 'commit', c.transaction_receipt_sha256=r.transaction_receipt_sha256,
 'effect', a.content_sha256=r.expected_effect_sha256,
 'job_validating',j.state='validating'
)), '[]'::json)::text
FROM hwpx_agent.idempotency_records r
JOIN hwpx_agent.jobs j USING(tenant_id,project_id,job_id)
JOIN hwpx_agent.branches b ON b.tenant_id=r.tenant_id AND b.project_id=r.project_id AND b.branch_id=r.branch_id
LEFT JOIN hwpx_agent.revisions v ON v.tenant_id=b.tenant_id AND v.project_id=b.project_id AND v.revision_id=b.head_revision_id
LEFT JOIN hwpx_agent.revision_graph_seals s ON s.tenant_id=v.tenant_id AND s.project_id=v.project_id AND s.revision_id=v.revision_id
LEFT JOIN hwpx_agent.revision_commit_receipts c ON c.tenant_id=v.tenant_id AND c.project_id=v.project_id AND c.committed_revision_id=v.revision_id
LEFT JOIN hwpx_agent.artifacts a ON a.tenant_id=v.tenant_id AND a.artifact_id=v.result_artifact_id
WHERE r.tenant_id='00000000-0000-0000-0000-000000000001';
""", check=False)
            if diagnostic.returncode == 0:
                receipt['owned_oracle_boolean_diagnostics'] = json.loads(diagnostic.stdout.strip())
    finally:
        status = h.run(docker, ['inspect', container], check=False)
        if status.returncode == 0:
            state = json.loads(status.stdout)[0]
            require(state['Config']['Labels'].get(LABEL) == run_id and state['Name'] == '/'+container and state['Config']['Image'] == h.DEFAULT_IMAGE, 'p84_cleanup_owner')
            h.run(docker, ['rm', '--force', container], timeout=60)
        receipt['container_removed'] = h.run(docker, ['inspect', container], check=False).returncode != 0
        require(blob_root.resolve() == blob_root and blob_root.parent == temp_base and blob_root.name.startswith('hwpx-agent-p84-'+suffix+'-') and not blob_root.is_symlink() and not blob_root.is_junction(), 'p84_cleanup_blob_owner')
        paths = list(blob_root.rglob('*'))
        require(not any(p.is_symlink() or p.is_junction() for p in paths), 'p84_cleanup_blob_links')
        receipt['owned_ciphertext_files'] = sum(p.is_file() for p in paths)
        receipt['owned_blob_bytes'] = sum(p.stat().st_size for p in paths if p.is_file())
        shutil.rmtree(blob_root); receipt['owned_blob_root_removed'] = not blob_root.exists()
        require(receipt['container_removed'] and receipt['owned_blob_root_removed'], 'p84_cleanup_failed')
    print(json.dumps(receipt, sort_keys=True)); return 0 if error is None else 2
if __name__ == '__main__':
    raise SystemExit(main())
