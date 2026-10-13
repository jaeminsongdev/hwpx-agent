"""Actual isolated PostgreSQL18.4 migration/CAS metadata tests. Never imports/activates Hwp."""
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

ROOT = h.ROOT
UP = 'migrations/postgres/0018_p09_full_document_ir.up.sql'
DOWN = 'migrations/postgres/0018_p09_full_document_ir.down.sql'
FIXTURE = 'tools/p09/fixtures/stored_full_ir_migration.sql'
EDITS = (
    ('CREATE FUNCTION hwpx_agent.commit_revision_cas(', 'CREATE FUNCTION hwpx_agent.commit_revision_cas_with_full_ir_v1('),
    ('    p_commit_receipt_sha256 character(64)\n)', '    p_commit_receipt_sha256 character(64),\n    p_full_document_ir_artifact_id uuid,\n    p_full_document_ir_artifact_sha256 character(64),\n    p_full_document_ir_result_package_sha256 character(64),\n    p_full_document_ir_graph_sha256 character(64)\n)'),
    ('BEGIN\n    IF ', "BEGIN\n    IF p_full_document_ir_artifact_id IS NULL THEN\n        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_DOCUMENT_IR_REQUIRED';\n    END IF;\n    IF "),
    ('        validation_summary_sha256, created_by_subject_sha256\n    ) VALUES (', '        validation_summary_sha256, created_by_subject_sha256,\n        full_document_ir_artifact_id, full_document_ir_artifact_sha256,\n        full_document_ir_result_package_sha256, full_document_ir_graph_sha256\n    ) VALUES ('),
    ('        p_validation_state, p_validation_summary_sha256, p_subject_sha256\n    );', '        p_validation_state, p_validation_summary_sha256, p_subject_sha256,\n        p_full_document_ir_artifact_id, p_full_document_ir_artifact_sha256,\n        p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256\n    );'),
)

def require(value, code):
    if not value:
        raise ValueError(code)


def load(name):
    path = ROOT / name
    for ancestor in path.parents:
        require(not ancestor.is_symlink() and not ancestor.is_junction(), 'p60_sql_ancestor_link')
    return h.load_bounded_text(path, 256 * 1024)


def function(text, name):
    start = text.index('CREATE FUNCTION hwpx_agent.' + name + '(')
    end = text.index('\n$$;', start) + 4
    return text[start:end]


def main():
    require(Path.cwd().resolve() == ROOT.resolve(), 'p60_sql_wrong_root')
    files = []
    for number in range(1, 19):
        paths = list((ROOT / 'migrations/postgres').glob(f'{number:04}_*.up.sql'))
        require(len(paths) == 1, 'p60_sql_ambiguous_up')
        files.append(paths[0].relative_to(ROOT).as_posix())
    sources = tuple(files) + (DOWN, FIXTURE, 'tools/p09/test_stored_full_ir_migration.py', 'tools/p14/test_postgres_migrations.py')
    texts = {name: load(name) for name in sources}
    pins = {name: h.sha256(ROOT / name) for name in sources}
    derived = function(texts[files[2]], 'commit_revision_cas')
    for old, new in EDITS:
        require(derived.count(old) == 1, 'p60_sql_derivation_occurrence')
        derived = derived.replace(old, new)
    require(derived == function(texts[UP], 'commit_revision_cas_with_full_ir_v1'), 'p60_sql_original_cas_control_flow_changed')
    docker = shutil.which('docker')
    require(docker is not None, 'p60_sql_docker_missing')
    image = h.ensure_image(docker, h.DEFAULT_IMAGE, False)
    run_id = str(uuid.uuid4())
    container = 'hwpx-agent-p09-ir-' + run_id.replace('-', '')[:12]
    receipt = {'schema': 'hwpx-agent.p09-stored-full-ir-migration/v1', 'state': 'pending',
        'scope': 'isolated_actual_sql_metadata_not_native_import_or_full_product', 'source_sha256': pins,
        'image': h.DEFAULT_IMAGE, 'image_id': image['Id'], 'run_id': run_id, 'container': container,
        'network': 'none', 'host_ports_or_host_volumes': False, 'native_activated': False,
        'original_cas_control_flow_exact_under_five_additions': True, 'container_removed': False,
        'applied_schema_versions': [], 'p09_complete': False}
    error = None
    stage = 'container_create'
    try:
        h.run(docker, ['run', '--detach', '--name', container, '--label', f'{h.LABEL_KEY}={run_id}',
            '--network', 'none', '--tmpfs', '/var/lib/postgresql:rw,noexec,nosuid,size=512m',
            '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', h.DEFAULT_IMAGE], timeout=60)
        h.wait_until_ready(docker, container)
        receipt['postgres_version'] = h.psql(docker, container, 'SHOW server_version;').stdout.strip()
        require(receipt['postgres_version'].startswith('18.4'), 'p60_sql_server_version')
        inspection = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
        require(inspection['HostConfig']['NetworkMode'] == 'none'
            and not inspection['HostConfig'].get('PortBindings')
            and all(m['Type'] == 'tmpfs' for m in inspection.get('Mounts', [])), 'p60_sql_container_isolation')
        for number, name in enumerate(files, 1):
            stage = 'migration_' + str(number)
            child = h.psql(docker, container, "SELECT set_config('hwpx_agent.migration_sha256','" + pins[name] + "',false);\n" + texts[name], check=False)
            require(child.returncode == 0, 'p60_sql_up_failed_' + str(number))
            receipt['applied_schema_versions'].append(number)
        receipt['actual_registry_versions'] = h.psql(docker, container, 'SELECT string_agg(version::text,\',\' ORDER BY version) FROM hwpx_agent.schema_versions;').stdout.strip()
        require(receipt['actual_registry_versions'] == ','.join(map(str, range(1,19))), 'p60_sql_registry_versions')
        stage = 'rollback_without_gate'
        child = h.psql(docker, container, texts[DOWN], check=False)
        require(child.returncode != 0 and 'FULL_DOCUMENT_IR_ROLLBACK_REQUIRES_EXPLICIT_GATE' in child.stderr, 'p60_sql_no_gate_rollback_accepted')
        receipt['rollback_without_gate_rejected'] = True
        stage = 'empty_ir_rollback_reapply'
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], check=False)
        require(child.returncode == 0, 'p60_sql_empty_ir_rollback_failed')
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.migration_sha256','" + pins[UP] + "',false);\n" + texts[UP], check=False)
        require(child.returncode == 0, 'p60_sql_reapply_failed')
        receipt['empty_ir_explicit_rollback_and_reapply_passed'] = True
        stage = 'actual_metadata_fixture'
        child = h.psql(docker, container, texts[FIXTURE], check=False)
        require(child.returncode == 0 and child.stdout.splitlines()[-1] == 'P09_STORED_FULL_IR_METADATA_PASS assertions=9', 'p60_sql_fixture_failed')
        receipt['actual_metadata_fixture_assertions'] = 9
        stage = 'data_preserving_rollback_rejection'
        child = h.psql(docker, container, "SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], check=False)
        require(child.returncode != 0 and 'FULL_DOCUMENT_IR_ROLLBACK_REFUSES_IR_DATA_LOSS' in child.stderr, 'p60_sql_ir_data_loss_not_rejected')
        count = h.psql(docker, container, 'SELECT count(*) FROM hwpx_agent.revisions WHERE full_document_ir_artifact_id IS NOT NULL;').stdout.strip()
        require(count == '1', 'p60_sql_refused_rollback_changed_ir')
        receipt['rollback_with_ir_data_refused_and_link_preserved'] = True
        require(pins == {name: h.sha256(ROOT/name) for name in sources}, 'p60_sql_sources_changed')
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
            receipt['constant_diagnostic_codes'] = sorted(set(re.findall(r'\b(?:FULL_DOCUMENT_IR_[A-Z_]+|TEST_[A-Z_]+|REVISION_[A-Z_]+)\b', child.stderr)))
    finally:
        if h.inspect_owned_container(docker, container, run_id):
            inspected = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
            require(inspected['Config']['Image'] == h.DEFAULT_IMAGE and inspected['Name'] == '/' + container, 'p60_sql_cleanup_identity')
            h.run(docker, ['rm', '--force', '--volumes', container], timeout=60)
        receipt['container_removed'] = not h.inspect_owned_container(docker, container, run_id)
        require(receipt['container_removed'], 'p60_sql_owned_cleanup_failed')
    print(json.dumps(receipt, sort_keys=True))
    return 0 if error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
