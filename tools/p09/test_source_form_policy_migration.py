"""Owned isolated PostgreSQL metadata checks; no Hwp, policy plaintext, production DB or native claims."""
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
UP = 'migrations/postgres/0020_p09_source_form_policy.up.sql'
DOWN = 'migrations/postgres/0020_p09_source_form_policy.down.sql'
FIXTURE = 'tools/p09/fixtures/source_form_policy.sql'
LEGACY = 'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql'
IR = 'tools/p09/fixtures/authorized_full_ir_intent.sql'

def require(ok, code):
    if not ok:
        raise ValueError(code)

def load(path):
    source = ROOT / path
    for ancestor in source.parents:
        require(not ancestor.is_symlink() and not ancestor.is_junction(), 'p82_linked_input')
    return h.load_bounded_text(source, 256 * 1024)

def main():
    require(Path.cwd().resolve() == ROOT.resolve(), 'p82_wrong_root')
    names = []
    for number in range(1, 21):
        files = list((ROOT / 'migrations/postgres').glob(f'{number:04}_*.up.sql'))
        require(len(files) == 1, 'p82_ambiguous_migration')
        names.append(files[0].relative_to(ROOT).as_posix())
    sources = names + [DOWN, FIXTURE, LEGACY, IR, 'tools/p09/test_source_form_policy_migration.py', 'tools/p14/test_postgres_migrations.py']
    texts = {name: load(name) for name in sources}
    pins = {name: h.sha256(ROOT / name) for name in sources}
    docker = shutil.which('docker')
    require(docker is not None, 'p82_docker_missing')
    image = h.ensure_image(docker, h.DEFAULT_IMAGE, False)
    run_id = str(uuid.uuid4())
    container = 'hwpx-agent-p09-policy-' + run_id.replace('-', '')[:12]
    receipt = {'schema': 'hwpx-agent.p09-source-form-policy-migration/v1', 'state': 'pending',
        'source_sha256': pins, 'run_id': run_id, 'container': container, 'image': h.DEFAULT_IMAGE, 'image_id': image['Id'],
        'network': 'none', 'host_ports_or_volumes': False, 'policy_values_in_sql': False,
        'actual_blob_or_cipher_qualified': False, 'policy_decoder_or_stored_product_provider_qualified': False,
        'real_scanner_or_issuer_qualified': False, 'native_executed': False, 'p09_complete': False,
        'applied_schema_versions': [], 'checks': []}
    stage = 'container_create'
    error = None
    child = None
    def sql(text, code, expected=None):
        nonlocal child
        child = h.psql(docker, container, text, check=False)
        if expected:
            require(child.returncode != 0 and expected in child.stderr, code)
        else:
            require(child.returncode == 0, code)
        return child.stdout.strip()
    try:
        h.run(docker, ['run', '--detach', '--pull', 'never', '--name', container, '--label', f'{h.LABEL_KEY}={run_id}',
            '--network', 'none', '--tmpfs', '/var/lib/postgresql:rw,noexec,nosuid,size=512m',
            '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', h.DEFAULT_IMAGE])
        h.wait_until_ready(docker, container)
        state = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
        require(state['Config']['Image'] == h.DEFAULT_IMAGE and state['Name'] == '/' + container
            and state['HostConfig']['NetworkMode'] == 'none' and not state['HostConfig'].get('PortBindings')
            and all(m['Type'] == 'tmpfs' for m in state.get('Mounts', [])), 'p82_container_identity')
        receipt['postgres_version'] = sql('SHOW server_version;', 'p82_server_version')
        require(receipt['postgres_version'].startswith('18.4'), 'p82_server_version_changed')
        for number, name in enumerate(names, 1):
            stage = f'migration_{number}'
            sql("SELECT set_config('hwpx_agent.migration_sha256','" + pins[name] + "',false);\n" + texts[name], 'p82_apply_failed')
            receipt['applied_schema_versions'].append(number)
        require(sql("SELECT string_agg(version::text,',' ORDER BY version) FROM hwpx_agent.schema_versions;", 'p82_registry_read')
            == ','.join(map(str, range(1, 21))), 'p82_registry_mismatch')
        stage = 'no_gate_rollback'
        sql(texts[DOWN], 'p82_no_gate_rollback_accepted', 'FORM_POLICY_ROLLBACK_REQUIRES_EXPLICIT_GATE')
        receipt['checks'].append('explicit_rollback_gate_required')
        stage = 'empty_rollback_reapply'
        sql("SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], 'p82_empty_rollback_failed')
        sql("SELECT set_config('hwpx_agent.migration_sha256','" + pins[UP] + "',false);\n" + texts[UP], 'p82_reapply_failed')
        receipt['checks'].append('empty_explicit_rollback_reapply')
        stage = 'frozen_legacy_regression'
        require('P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28' in sql(texts[LEGACY], 'p82_legacy_failed'), 'p82_legacy_coverage')
        receipt['unchanged_legacy_assertions'] = 28
        stage = 'frozen_authorized_ir_regression'
        require(sql(texts[IR], 'p82_ir_failed').splitlines()[-1] == 'P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25', 'p82_ir_coverage')
        receipt['unchanged_authorized_ir_assertions'] = 25
        stage = 'source_policy_fixture'
        require(sql(texts[FIXTURE], 'p82_fixture_failed').splitlines()[-1] == 'P09_SOURCE_FORM_POLICY_METADATA_PASS assertions=32', 'p82_fixture_coverage')
        receipt['actual_policy_metadata_assertions'] = 32
        stage = 'data_preserving_rollback'
        sql("SELECT set_config('hwpx_agent.allow_destructive_rollback','on',false);\n" + texts[DOWN], 'p82_data_loss_rollback_accepted', 'FORM_POLICY_ROLLBACK_REFUSES_DATA_LOSS')
        require(sql('SELECT count(*) FROM hwpx_agent.source_form_policy_versions;', 'p82_preserved_history') == '2', 'p82_history_changed')
        receipt['checks'].append('rollback_refuses_existing_history')
        require(pins == {name: h.sha256(ROOT/name) for name in sources}, 'p82_source_drift')
        receipt['state'] = 'pass'
    except Exception as caught:
        error = caught
        receipt.update(state='fail', failed_stage=stage, error_type=type(caught).__name__,
            error_code=str(caught) if re.fullmatch(r'p82_[a-z0-9_]+', str(caught)) else 'redacted_error')
        if child is not None:
            receipt['failed_child_exit_code'] = child.returncode
            receipt['failed_stdout_sha256'] = hashlib.sha256(child.stdout.encode()).hexdigest()
            receipt['failed_stderr_sha256'] = hashlib.sha256(child.stderr.encode()).hexdigest()
            receipt['constant_error_codes'] = sorted(set(re.findall(r'(?:FORM_POLICY_|TEST_POLICY_)[A-Z_]+', child.stderr)))
            receipt['sql_identifier_diagnostics'] = sorted(set(re.findall(r'(?:column|relation|constraint) "([a-z_][a-z_0-9]{0,80})"', child.stderr)))
            receipt['redacted_first_error'] = next((re.sub(r'"[^"\n]*"|\x27[^\x27\n]*\x27', '<redacted>', line)[:180]
                for line in child.stderr.splitlines() if line.startswith('ERROR:')), 'no_error_line')
    finally:
        if h.inspect_owned_container(docker, container, run_id):
            state = json.loads(h.run(docker, ['inspect', container]).stdout)[0]
            require(state['Config']['Image'] == h.DEFAULT_IMAGE and state['Name'] == '/' + container, 'p82_cleanup_identity')
            h.run(docker, ['rm', '--force', '--volumes', container])
        receipt['container_removed'] = not h.inspect_owned_container(docker, container, run_id)
        require(receipt['container_removed'], 'p82_cleanup_failed')
    print(json.dumps(receipt, sort_keys=True))
    return 0 if error is None else 2

if __name__ == '__main__':
    raise SystemExit(main())
