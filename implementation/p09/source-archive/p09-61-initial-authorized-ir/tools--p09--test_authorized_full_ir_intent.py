"""Actual full-schema PostgreSQL18.4 authorized IR intent metadata tests. Never imports/activates Hwp."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import uuid
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p14 import test_postgres_migrations as h
from tools.p09 import test_stored_full_ir_migration as predecessor

ROOT = h.ROOT
UP = 'migrations/postgres/0019_p09_authorized_full_ir_intent.up.sql'
DOWN = 'migrations/postgres/0019_p09_authorized_full_ir_intent.down.sql'
FIXTURE = 'tools/p09/fixtures/authorized_full_ir_intent.sql'
DERIVATIONS = json.loads(r'''[["claim_idempotent_job_v2","claim_idempotent_job_with_full_ir_v1",[["CREATE FUNCTION hwpx_agent.claim_idempotent_job_v2(","CREATE FUNCTION hwpx_agent.claim_idempotent_job_with_full_ir_v1("],["    p_event_sha256 character(64)\n)","    p_event_sha256 character(64),\n    p_full_document_ir_artifact_id uuid,\n    p_full_document_ir_artifact_sha256 character(64),\n    p_full_document_ir_result_package_sha256 character(64),\n    p_full_document_ir_graph_sha256 character(64)\n)"],["    IF p_branch_id =","    PERFORM hwpx_agent.require_full_ir_intent_artifact_v1(\n        p_tenant_id, p_subject_sha256, p_full_document_ir_artifact_id,\n        p_full_document_ir_artifact_sha256, p_full_document_ir_graph_sha256\n    );\n    IF p_full_document_ir_artifact_id IS NOT DISTINCT FROM p_source_artifact_id\n       OR p_full_document_ir_result_package_sha256 IS DISTINCT FROM p_expected_effect_sha256 THEN\n        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_IR_INTENT_REQUEST_INVALID';\n    END IF;\n    IF p_branch_id ="],["        RETURN QUERY SELECT 'replay'::text, v_record.job_id, v_record.state,","        IF NOT EXISTS (\n            SELECT 1 FROM hwpx_agent.full_document_ir_intents AS intent\n            WHERE intent.tenant_id = p_tenant_id AND intent.project_id = p_project_id\n              AND intent.idempotency_key = p_idempotency_key\n              AND ROW(intent.artifact_id, intent.artifact_sha256,\n                  intent.result_package_sha256, intent.graph_sha256)\n              IS NOT DISTINCT FROM ROW(p_full_document_ir_artifact_id,\n                  p_full_document_ir_artifact_sha256,\n                  p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256)\n        ) THEN\n            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'FULL_IR_INTENT_KEY_CONFLICT';\n        END IF;\n        RETURN QUERY SELECT 'replay'::text, v_record.job_id, v_record.state,"],["    RETURN QUERY SELECT 'new'::text, p_job_id, 'claimed'::text,","    INSERT INTO hwpx_agent.full_document_ir_intents (\n        tenant_id, project_id, idempotency_key, artifact_id,\n        artifact_sha256, result_package_sha256, graph_sha256\n    ) VALUES (\n        p_tenant_id, p_project_id, p_idempotency_key, p_full_document_ir_artifact_id,\n        p_full_document_ir_artifact_sha256, p_full_document_ir_result_package_sha256,\n        p_full_document_ir_graph_sha256\n    );\n    RETURN QUERY SELECT 'new'::text, p_job_id, 'claimed'::text,"]]],["commit_idempotent_revision_cas_v2","commit_idempotent_revision_cas_with_full_ir_v1",[["CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(","CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1("],["    p_commit_receipt_sha256 character(64)\n)","    p_commit_receipt_sha256 character(64),\n    p_full_document_ir_artifact_id uuid,\n    p_full_document_ir_artifact_sha256 character(64),\n    p_full_document_ir_result_package_sha256 character(64),\n    p_full_document_ir_graph_sha256 character(64)\n)"],["    IF p_commit_authorization_id =","    PERFORM hwpx_agent.require_full_ir_intent_artifact_v1(\n        p_tenant_id, p_subject_sha256, p_full_document_ir_artifact_id,\n        p_full_document_ir_artifact_sha256, p_full_document_ir_graph_sha256\n    );\n    IF NOT EXISTS (\n        SELECT 1 FROM hwpx_agent.full_document_ir_intents AS intent\n        WHERE intent.tenant_id = p_tenant_id AND intent.project_id = p_project_id\n          AND intent.idempotency_key = p_idempotency_key\n          AND ROW(intent.artifact_id, intent.artifact_sha256,\n              intent.result_package_sha256, intent.graph_sha256)\n          IS NOT DISTINCT FROM ROW(p_full_document_ir_artifact_id,\n              p_full_document_ir_artifact_sha256,\n              p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256)\n    ) THEN\n        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_IR_COMMIT_INTENT_MISMATCH';\n    END IF;\n    IF p_commit_authorization_id ="],["RETURN QUERY SELECT * FROM hwpx_agent.commit_revision_cas(","RETURN QUERY SELECT * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1("],["        p_commit_request_sha256, p_commit_receipt_sha256\n    );","        p_commit_request_sha256, p_commit_receipt_sha256,\n        p_full_document_ir_artifact_id, p_full_document_ir_artifact_sha256,\n        p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256\n    );"]]]]''')
LEGACY = 'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql'


def require(value, code):
    if not value:
        raise ValueError(code)


def load(name):
    path = ROOT / name
    for ancestor in path.parents:
        require(not ancestor.is_symlink() and not ancestor.is_junction(), 'p61_sql_ancestor_link')
    return h.load_bounded_text(path, 256 * 1024)


def function(text, name):
    start = text.index('CREATE FUNCTION hwpx_agent.' + name + '(')
    end = text.index('\n$$;', start) + 4
    return text[start:end]


def main():
    require(Path.cwd().resolve() == ROOT.resolve(), 'p61_sql_wrong_root')
    files = []
    for number in range(1, 20):
        paths = list((ROOT / 'migrations/postgres').glob(f'{number:04}_*.up.sql'))
        require(len(paths) == 1, 'p61_sql_ambiguous_up')
        files.append(paths[0].relative_to(ROOT).as_posix())
    sources = tuple(files) + (DOWN, FIXTURE, LEGACY, predecessor.FIXTURE,
        'tools/p09/test_authorized_full_ir_intent.py', 'tools/p09/test_stored_full_ir_migration.py',
        'tools/p14/test_postgres_migrations.py')
    texts = {name: load(name) for name in sources}
    pins = {name: h.sha256(ROOT / name) for name in sources}
    for old_name, new_name, edits in DERIVATIONS:
        derived = function(texts[files[6]], old_name)
        for old, new in edits:
            require(derived.count(old) == 1, 'p61_sql_derivation_occurrence')
            derived = derived.replace(old, new)
        require(derived == function(texts[UP], new_name), 'p61_sql_original_v2_control_flow_changed')
    derived = function(texts[files[2]], 'commit_revision_cas')
    for old, new in predecessor.EDITS:
        require(derived.count(old) == 1, 'p61_sql_original_leaf_derivation_occurrence')
        derived = derived.replace(old, new)
    require(derived == function(texts[predecessor.UP], 'commit_revision_cas_with_full_ir_v1'),
        'p61_sql_frozen_leaf_control_flow_changed')
    docker = shutil.which('docker')
    require(docker is not None, 'p61_sql_docker_missing')
    image = h.ensure_image(docker, h.DEFAULT_IMAGE, False)
    run_id = str(uuid.uuid4())
    container = 'hwpx-agent-p09-ir-auth-' + run_id.replace('-', '')[:12]
    receipt = {'schema': 'hwpx-agent.p09-authorized-full-ir-intent-migration/v1', 'state': 'pending',
        'scope': 'isolated_actual_sql_metadata_not_native_import_or_full_product', 'source_sha256': pins,
        'image': h.DEFAULT_IMAGE, 'image_id': image['Id'], 'run_id': run_id, 'container': container,
        'network': 'none', 'host_ports_or_host_volumes': False, 'native_activated': False,
        'original_claim_and_commit_control_flow_exact_under_five_additions_each': True, 'container_removed': False,
        'applied_schema_versions': [], 'p09_complete': False}
    error = None
    stage = 'container_create'
    try:
        h.run(docker, ['run', '--detach', '--name', container, '--label', f'{h.LABEL_KEY}={run_id}',
            '--network', 'none', '--tmpfs', '/var/lib/postgresql:rw,noexec,nosuid,size=512m',
            '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', h.DEFAULT_IMAGE], timeout=60)
        h.wait_until_ready(docker, container)
        receipt['postgres_version'] = h.psql(docker, container, 'SHOW server_version;').stdout.strip()
        require(receipt['postgres_version'].startswith('18.4'), 'p61_sql_server_version')
        inspection = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
        require(inspection['HostConfig']['NetworkMode'] == 'none'
            and not inspection['HostConfig'].get('PortBindings')
            and all(m['Type'] == 'tmpfs' for m in inspection.get('Mounts', [])), 'p61_sql_container_isolation')
        for number, name in enumerate(files, 1):
            stage = 'migration_' + str(number)
            child = h.psql(docker, container, "SELECT set_config('hwpx_agent.migration_sha256','" + pins[name] + "',false);\n" + texts[name], check=False)
            require(child.returncode == 0, 'p61_sql_up_failed_' + str(number))
            receipt['applied_schema_versions'].append(number)
        receipt['actual_registry_versions'] = h.psql(docker, container, 'SELECT string_agg(version::text,\',\' ORDER BY version) FROM hwpx_agent.schema_versions;').stdout.strip()
        require(receipt['actual_registry_versions'] == ','.join(map(str, range(1,20))), 'p61_sql_registry_versions')
        stage = 'rollback_without_gate'
        child = h.psql(docker, container, texts[DOWN], check=False)
        require(child.returncode != 0 and 'FULL_IR_INTENT_ROLLBACK_REQUIRES_EXPLICIT_GATE' in child.stderr, 'p61_sql_no_gate_rollback_accepted')
        receipt['rollback_without_gate_rejected'] = True
        stage = 'empty_ir_rollback_reapply'
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], check=False)
        require(child.returncode == 0, 'p61_sql_empty_ir_rollback_failed')
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.migration_sha256','" + pins[UP] + "',false);\n" + texts[UP], check=False)
        require(child.returncode == 0, 'p61_sql_reapply_failed')
        receipt['empty_ir_explicit_rollback_and_reapply_passed'] = True
        stage = 'frozen_predecessor_failure_remains'
        child = h.psql(docker, container, texts[predecessor.FIXTURE], check=False)
        require(child.returncode != 0 and 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED' in child.stderr,
            'p61_sql_original_unauthorized_leaf_not_rejected')
        receipt['frozen_p60_full_fixture_still_refuses_missing_authority'] = True
        receipt['frozen_p60_fixture_child_exit_code'] = child.returncode
        receipt['frozen_p60_fixture_stderr_sha256'] = hashlib.sha256(child.stderr.encode()).hexdigest()
        stage = 'actual_legacy_regression'
        child = h.psql(docker, container, texts[LEGACY], check=False)
        require(child.returncode == 0 and 'P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28'
            in child.stdout, 'p61_sql_legacy_regression_failed')
        receipt['unchanged_legacy_actual_assertions'] = 28
        stage = 'actual_metadata_fixture'
        child = h.psql(docker, container, texts[FIXTURE], check=False)
        require(child.returncode == 0 and child.stdout.splitlines()[-1] == 'P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25', 'p61_sql_fixture_failed')
        receipt['actual_metadata_fixture_assertions'] = 25
        stage = 'data_preserving_rollback_rejection'
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], check=False)
        require(child.returncode != 0 and 'FULL_IR_INTENT_ROLLBACK_REFUSES_DATA_LOSS' in child.stderr, 'p61_sql_ir_data_loss_not_rejected')
        count = h.psql(docker, container, 'SELECT count(*) FROM hwpx_agent.revisions WHERE full_document_ir_artifact_id IS NOT NULL;').stdout.strip()
        require(count == '1', 'p61_sql_refused_rollback_changed_ir')
        receipt['rollback_with_ir_data_refused_and_link_preserved'] = True
        require(pins == {name: h.sha256(ROOT/name) for name in sources}, 'p61_sql_sources_changed')
        receipt['state'] = 'pass'
    except Exception as caught:
        error = caught
        receipt['state'] = 'fail'; receipt['failed_stage'] = stage
        receipt['error_type'] = type(caught).__name__
        receipt['error_code'] = str(caught) if re.fullmatch(r'[a-z0-9_]+', str(caught)) else 'redacted_error'
        if 'child' in locals():
            receipt['actual_child_exit_code'] = child.returncode
            receipt['actual_child_stdout_sha256'] = hashlib.sha256(child.stdout.encode()).hexdigest()
            receipt['actual_child_stderr_sha256'] = hashlib.sha256(child.stderr.encode()).hexdigest()
            receipt['constant_diagnostic_codes'] = sorted(set(re.findall(r'(?:FULL_IR_|FULL_DOCUMENT_IR_|TEST_|REVISION_|IDEMPOTENCY_)[A-Z_]+', child.stderr)))
            receipt['sql_identifier_diagnostics'] = sorted(set(re.findall(r'(?:column|relation|constraint) "([a-z_][a-z_0-9]{0,80})"', child.stderr)))
            receipt['sql_function_line_diagnostics'] = re.findall(r'PL/pgSQL function ([a-z_][a-z_0-9]*)\([^\n]*\) line ([0-9]+)', child.stderr)
            receipt['redacted_first_sql_error'] = next((re.sub(r'"[^"\n]*"|\x27[^\x27\n]*\x27', '<redacted>', line)[:180]
                for line in child.stderr.splitlines() if line.startswith('ERROR:')), 'no_error_line')
    finally:
        if h.inspect_owned_container(docker, container, run_id):
            inspected = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
            require(inspected['Config']['Image'] == h.DEFAULT_IMAGE and inspected['Name'] == '/' + container, 'p61_sql_cleanup_identity')
            h.run(docker, ['rm', '--force', '--volumes', container], timeout=60)
        receipt['container_removed'] = not h.inspect_owned_container(docker, container, run_id)
        require(receipt['container_removed'], 'p61_sql_owned_cleanup_failed')
    print(json.dumps(receipt, sort_keys=True))
    return 0 if error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
