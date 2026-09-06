"""Disposable PostgreSQL and separate-process P17 checkpoint-host acceptance."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import subprocess
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
LABEL = "hwpx-agent.p17-postgres-checkpoint-host-test"
MIGRATIONS = tuple(f"{number:04d}_{name}" for number, name in (
    (1, "p14_metadata"), (2, "p14_artifact_service"), (3, "p14_revision_cas"),
    (4, "p14_history_checkpoints"), (5, "p14_job_state_machine"),
    (6, "p14_worker_lease_fencing"), (7, "p14_idempotency_reconciliation"),
    (8, "p14_cancel_cleanup"), (9, "p14_retention_local_mirror"),
    (10, "p16_artifact_repository"), (11, "p16_plan_source"),
    (12, "p16_durable_plan_store"), (13, "p16_plan_review_evidence"),
    (14, "p17_history_checkpoint_note"),
))
TENANT = "d1000000-0000-0000-0000-000000000001"
PROJECT = "prj_d2000000000000000000000000000001"
BRANCH = "brn_d3000000000000000000000000000001"
MIRROR = "mir_d7000000000000000000000000000001"
REVISION = "rev_d5000000000000000000000000000001"
GENERATION = "1"
ISSUER = "https://identity.hwpx-agent.example"
RESOURCE = "https://mcp.hwpx-agent.example"
KEY_ID = "local-key-01"
SERVICE_ID = "p17-checkpoint-probe"
APP_ROLE = "hwpx_p17_checkpoint_app"
LABEL_TEXT = "P17 durable checkpoint"
NOTE_TEXT = "한글 2020 PostgreSQL checkpoint note"


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def invoke(
    command: list[str],
    *,
    data: str | None = None,
    env: dict[str, str] | None = None,
    expected: bool = True,
    timeout: int = 90,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=data,
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if expected and result.returncode != 0:
        safe = re.findall(r"^PROBE_[A-Z_]{3,64}$", result.stderr, re.MULTILINE)
        category = safe[-1] if safe else "child_failed"
        raise CheckFailure(f"child_failed exit={result.returncode} category={category}")
    return result


def service_subject_sha256() -> str:
    framed = f"service:{len(ISSUER)}:{ISSUER}:{len(SERVICE_ID)}:{SERVICE_ID}"
    return hashlib.sha256(framed.encode("utf-8")).hexdigest()


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def authorization(secret: bytes, token_id: str, now: int) -> str:
    header = {"alg": "HS256", "kid": KEY_ID, "typ": "hwpx-service+jwt"}
    claims = {
        "iss": ISSUER,
        "sub": SERVICE_ID,
        "aud": RESOURCE,
        "exp": now + 120,
        "nbf": now - 10,
        "iat": now - 10,
        "jti": token_id,
        "scope": "mirror.sync",
        "token_kind": "service",
        "tenant_id": TENANT,
        "service_id": SERVICE_ID,
    }
    encoded_header = base64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_claims = base64url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_claims}"
    signature = base64url(hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest())
    return f"Bearer {signing_input}.{signature}"


def read_line(process: subprocess.Popen[str], timeout: float) -> str:
    require(process.stdout is not None, "host_stdout_missing")
    received: queue.Queue[str] = queue.Queue(maxsize=1)

    def reader() -> None:
        received.put(process.stdout.readline())

    threading.Thread(target=reader, daemon=True).start()
    try:
        line = received.get(timeout=timeout)
    except queue.Empty as error:
        raise CheckFailure("host_ready_timeout") from error
    require(bool(line), "host_closed_before_ready")
    return line.strip()


def main() -> int:
    docker = shutil.which("docker")
    cargo = shutil.which("cargo")
    require(docker is not None, "docker_missing")
    require(cargo is not None, "cargo_missing")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p17/postgres-checkpoint-host/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    container = f"hwpx-p17-checkpoint-{run_id}"
    volume = f"hwpx-p17-checkpoint-data-{run_id}"
    contract_path = ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    image = contract["database"]["container_image"]
    require(re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image) is not None,
            "unpinned_image")
    inspected_image = json.loads(invoke([docker, "image", "inspect", image]).stdout)[0]
    migration_paths = [ROOT / "migrations/postgres" / f"{name}.up.sql"
                       for name in MIGRATIONS]
    require(all(path.is_file() for path in migration_paths), "migration_missing")
    setup_path = ROOT / "tools/p17/fixtures/p17_postgres_checkpoint_setup.sql"
    host_source = ROOT / "crates/remote-sync-host/examples/postgres_checkpoint_host.rs"
    client_source = ROOT / "crates/remote-sync-host/examples/postgres_checkpoint_client.rs"
    invoke([cargo, "build", "--locked", "-p", "remote-sync-host", "--examples"], timeout=180)
    executable_suffix = ".exe" if os.name == "nt" else ""
    host_program = ROOT / "target/debug/examples" / f"postgres_checkpoint_host{executable_suffix}"
    client_program = ROOT / "target/debug/examples" / f"postgres_checkpoint_client{executable_suffix}"
    require(host_program.is_file() and client_program.is_file(), "probe_not_built")

    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    cleaned = False
    host: subprocess.Popen[str] | None = None
    admin_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    hmac_secret = secrets.token_bytes(32)
    hmac_secret_text = hmac_secret.hex()
    subject_sha256 = service_subject_sha256()
    child_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)

    def sql(statement: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
        return invoke([
            docker, "exec", "-i", container, "psql", "-X", "--no-align",
            "--tuples-only", "--quiet", "--set", "ON_ERROR_STOP=1",
            "--username", "postgres", "--dbname", "postgres",
        ], data=statement, expected=expected)

    def ready() -> None:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            result = invoke([docker, "exec", container, "pg_isready", "--username", "postgres"],
                            expected=False, timeout=5)
            if result.returncode == 0:
                return
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def database_port() -> str:
        state = json.loads(invoke([docker, "inspect", container]).stdout)[0]
        require(state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
                "container_ownership_mismatch")
        bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
        require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port")
        binding = bindings[0]
        require(binding.get("HostIp") == "127.0.0.1", "non_loopback_port")
        return binding["HostPort"]

    def up(path: Path) -> None:
        prefix = f"SELECT set_config('hwpx_agent.migration_sha256','{digest(path)}',false);\n"
        sql(prefix + path.read_text(encoding="utf-8"))

    def host_environment(exchanges: int) -> dict[str, str]:
        return dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc",
            HWPX_P17_PG_PORT=database_port(),
            HWPX_P17_PG_DATABASE="postgres",
            HWPX_P17_PG_USER=APP_ROLE,
            HWPX_P17_PG_PASSWORD=app_password,
            HWPX_P17_BIND_PORT="0",
            HWPX_P17_EXCHANGES=str(exchanges),
            HWPX_P17_GENERATION=GENERATION,
            HWPX_P17_TENANT_UUID=TENANT,
            HWPX_P17_PROJECT_ID=PROJECT,
            HWPX_P17_BRANCH_ID=BRANCH,
            HWPX_P17_MIRROR_ID=MIRROR,
            HWPX_P17_REVISION_ID=REVISION,
            HWPX_P17_AUTH_HMAC_SECRET=hmac_secret_text,
        )

    def client_environment(port: int, bearer: str, note: str) -> dict[str, str]:
        return dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc",
            HWPX_P17_HOST_PORT=str(port),
            HWPX_P17_GENERATION=GENERATION,
            HWPX_P17_PROJECT_ID=PROJECT,
            HWPX_P17_BRANCH_ID=BRANCH,
            HWPX_P17_MIRROR_ID=MIRROR,
            HWPX_P17_REVISION_ID=REVISION,
            HWPX_P17_AUTHORIZATION=bearer,
            HWPX_P17_IDEMPOTENCY_KEY="checkpoint-postgres-0001",
            HWPX_P17_LABEL=LABEL_TEXT,
            HWPX_P17_NOTE=note,
        )

    def reject_host_for_database_drift() -> None:
        result = invoke([str(host_program)], env=host_environment(1), expected=False, timeout=15)
        require(result.returncode != 0, "database_drift_host_started")
        require(result.stderr.strip() == "PROBE_DATABASE_UNAVAILABLE",
                "database_drift_category_mismatch")

    try:
        stage = "container"
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke([
            docker, "run", "--detach", "--pull", "never", "--name", container,
            "--label", f"{LABEL}={run_id}", "--publish", "127.0.0.1::5432",
            "--memory", "512m", "--cpus", "2", "--pids-limit", "128",
            "--mount", f"type=volume,source={volume},target=/var/lib/postgresql",
            "--env", "POSTGRES_PASSWORD", image,
        ], env=child_environment)
        ready()
        checks.append("pinned_postgres_loopback_container")

        stage = "migrations"
        for migration_path in migration_paths:
            stage = migration_path.name
            up(migration_path)
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "14",
                "migration_count_mismatch")
        checks.append("all_fourteen_exact_migrations")

        stage = "empty_rollback"
        down = ROOT / "migrations/postgres/0014_p17_history_checkpoint_note.down.sql"
        down_sql = down.read_text(encoding="utf-8")
        require(sql(down_sql, expected=False).returncode != 0,
                "ungated_empty_rollback_accepted")
        sql("SELECT set_config("
            "'hwpx_agent.allow_p17_history_checkpoint_note_rollback','yes',false);\n"
            + down_sql)
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "13",
                "empty_rollback_schema_count_mismatch")
        up(migration_paths[-1])
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "14",
                "migration_reapply_count_mismatch")
        checks.extend(["empty_rollback_requires_explicit_gate", "empty_rollback_and_reapply"])

        stage = "seed"
        setup = setup_path.read_text(encoding="utf-8")
        require(setup.count("__P17_SERVICE_SUBJECT_SHA256__") == 3,
                "setup_subject_placeholder_drift")
        sql(setup.replace("__P17_SERVICE_SUBJECT_SHA256__", subject_sha256))
        sql(f"""
CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{app_password}'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
GRANT USAGE ON SCHEMA hwpx_agent TO {APP_ROLE};
GRANT SELECT ON TABLE hwpx_agent.schema_versions TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION hwpx_agent.create_history_checkpoint_v2(
    uuid,uuid,character,uuid,character,uuid,uuid,text,text
) TO {APP_ROLE};
""")
        privileges = sql(f"""
SELECT has_function_privilege('{APP_ROLE}',
 'hwpx_agent.create_history_checkpoint_v2(uuid,uuid,character,uuid,character,uuid,uuid,text,text)',
 'EXECUTE') || '|' || has_function_privilege('{APP_ROLE}',
 'hwpx_agent.create_history_checkpoint(uuid,uuid,character,uuid,character,uuid,uuid,text)',
 'EXECUTE') || '|' || has_table_privilege('{APP_ROLE}',
 'hwpx_agent.history_checkpoint_requests','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER');
""").stdout.strip()
        require(privileges == "true|false|false", "least_privilege_shape_mismatch")
        checks.append("dedicated_v2_execute_only_role")

        stage = "separate_process"
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        host = subprocess.Popen(
            [str(host_program)],
            env=host_environment(4),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )
        ready_event = json.loads(read_line(host, 15))
        require(ready_event == {
            "schema_version": "hwpx-agent.p17-postgres-host-probe/v1",
            "event": "ready",
            "port": ready_event.get("port"),
            "expected_exchanges": 4,
        }, "host_ready_event_mismatch")
        host_port = ready_event.get("port")
        require(isinstance(host_port, int) and 1 <= host_port <= 65535,
                "host_port_invalid")
        token_time = int(time.time())
        first = invoke(
            [str(client_program)],
            env=client_environment(host_port, authorization(
                hmac_secret_text.encode("ascii"), "p17-probe-token-0001", token_time), NOTE_TEXT),
            timeout=15,
        )
        second = invoke(
            [str(client_program)],
            env=client_environment(host_port, authorization(
                hmac_secret_text.encode("ascii"), "p17-probe-token-0002", token_time), NOTE_TEXT),
            timeout=15,
        )
        drift = invoke(
            [str(client_program)],
            env=client_environment(host_port, authorization(
                hmac_secret_text.encode("ascii"), "p17-probe-token-0003", token_time),
                                   "changed PostgreSQL checkpoint note"),
            expected=False,
            timeout=15,
        )
        first_event = json.loads(first.stdout)
        second_event = json.loads(second.stdout)
        require(first_event.get("outcome") == "succeeded" and
                first_event.get("replayed") is False, "first_create_mismatch")
        require(second_event.get("outcome") == "succeeded" and
                second_event.get("replayed") is True, "replay_mismatch")
        require(first_event.get("checkpoint_id") == second_event.get("checkpoint_id") and
                first_event.get("revision_id") == REVISION and
                second_event.get("revision_id") == REVISION, "checkpoint_identity_drift")
        require(drift.returncode != 0 and drift.stdout == "" and
                drift.stderr.strip() == "PROBE_EXCHANGE_FAILED", "note_drift_not_rejected")
        checkpoint_public_id = first_event["checkpoint_id"]
        require(re.fullmatch(r"chk_[0-9a-f]{32}", checkpoint_public_id) is not None,
                "checkpoint_id_invalid")
        checkpoint_uuid = str(uuid.UUID(hex=checkpoint_public_id.removeprefix("chk_")))
        sql("ALTER TABLE hwpx_agent.checkpoints DISABLE TRIGGER "
            "checkpoints_immutable;"
            f"UPDATE hwpx_agent.checkpoints SET label='corrupted' WHERE checkpoint_id="
            f"'{checkpoint_uuid}';"
            "ALTER TABLE hwpx_agent.checkpoints ENABLE TRIGGER checkpoints_immutable;")
        corrupted = invoke(
            [str(client_program)],
            env=client_environment(host_port, authorization(
                hmac_secret_text.encode("ascii"), "p17-probe-token-0004", token_time), NOTE_TEXT),
            expected=False,
            timeout=15,
        )
        require(corrupted.returncode != 0 and corrupted.stdout == "" and
                corrupted.stderr.strip() == "PROBE_EXCHANGE_FAILED",
                "corrupt_checkpoint_replay_accepted")
        sql("ALTER TABLE hwpx_agent.checkpoints DISABLE TRIGGER "
            "checkpoints_immutable;"
            f"UPDATE hwpx_agent.checkpoints SET label='{LABEL_TEXT}' WHERE checkpoint_id="
            f"'{checkpoint_uuid}';"
            "ALTER TABLE hwpx_agent.checkpoints ENABLE TRIGGER checkpoints_immutable;")
        remaining_stdout, host_stderr = host.communicate(timeout=15)
        require(host.returncode == 0 and host_stderr == "", "host_completion_failed")
        complete_event = json.loads(remaining_stdout.strip())
        require(complete_event == {
            "schema_version": "hwpx-agent.p17-postgres-host-probe/v1",
            "event": "complete",
            "succeeded": 3,
            "rejected": 0,
            "unavailable": 1,
        }, "host_complete_event_mismatch")
        checks.extend([
            "separate_host_and_four_client_processes",
            "one_time_tokens_cross_loopback_frame",
            "postgres_create_then_exact_replay",
            "same_key_changed_note_rejected",
            "corrupt_checkpoint_replay_fails_unavailable",
        ])

        stage = "durable_state"
        state = sql(f"""
SELECT count(*) || '|' || min(request_sha256) || '|' ||
       count(*) FILTER (WHERE note='{NOTE_TEXT}')
FROM hwpx_agent.history_checkpoint_requests
WHERE tenant_id='{TENANT}' AND project_id='{PROJECT.removeprefix('prj_')}'
  AND checkpoint_id='{checkpoint_uuid}';
SELECT count(*) || '|' || count(*) FILTER (WHERE note='{NOTE_TEXT}')
FROM hwpx_agent.checkpoints
WHERE tenant_id='{TENANT}' AND project_id='{PROJECT.removeprefix('prj_')}'
  AND checkpoint_id='{checkpoint_uuid}';
SELECT count(*) FROM hwpx_agent.audit_events
WHERE tenant_id='{TENANT}' AND project_id='{PROJECT.removeprefix('prj_')}'
  AND event_type='history.checkpoint_created'
  AND payload_sha256=(SELECT request_sha256 FROM hwpx_agent.history_checkpoint_requests
      WHERE tenant_id='{TENANT}' AND project_id='{PROJECT.removeprefix('prj_')}'
        AND checkpoint_id='{checkpoint_uuid}');
""").stdout.strip().splitlines()
        require(len(state) == 3 and re.fullmatch(r"1\|[0-9a-f]{64}\|1", state[0]) is not None
                and state[1] == "1|1" and state[2] == "1", "durable_state_mismatch")
        request_sha256 = state[0].split("|")[1]
        require(sql(f"UPDATE hwpx_agent.checkpoints SET note=note WHERE checkpoint_id="
                    f"'{checkpoint_uuid}';", expected=False).returncode != 0,
                "immutable_checkpoint_update_accepted")
        require(sql(f"DELETE FROM hwpx_agent.history_checkpoint_requests WHERE checkpoint_id="
                    f"'{checkpoint_uuid}';", expected=False).returncode != 0,
                "immutable_request_delete_accepted")
        checks.extend(["one_durable_request_checkpoint_audit", "immutable_rows_reject_changes"])

        stage = "rollback_guard"
        require(sql("SELECT set_config("
                    "'hwpx_agent.allow_p17_history_checkpoint_note_rollback','yes',false);\n"
                    + down_sql, expected=False).returncode != 0,
                "note_data_rollback_accepted")
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions WHERE version=14;")
                .stdout.strip() == "1", "rollback_guard_changed_schema")
        checks.append("data_loss_rollback_refused")

        stage = "admission_drift"
        v14_digest = digest(migration_paths[-1])
        sql("ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            "UPDATE hwpx_agent.schema_versions SET migration_sha256=repeat('f',64) WHERE version=14;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;")
        reject_host_for_database_drift()
        sql("ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            f"UPDATE hwpx_agent.schema_versions SET migration_sha256='{v14_digest}' WHERE version=14;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;")
        sql("REVOKE EXECUTE ON FUNCTION hwpx_agent.create_history_checkpoint_v2("
            f"uuid,uuid,character,uuid,character,uuid,uuid,text,text) FROM {APP_ROLE};")
        reject_host_for_database_drift()
        sql("GRANT EXECUTE ON FUNCTION hwpx_agent.create_history_checkpoint_v2("
            f"uuid,uuid,character,uuid,character,uuid,uuid,text,text) TO {APP_ROLE};")
        checks.extend(["migration_digest_drift_rejected", "execute_privilege_drift_rejected"])

        stage = "receipt"
        receipt = {
            "schema_version": "hwpx-agent.p17-postgres-checkpoint-host-run/v1",
            "run_id": run_id,
            "scope": "current_pc_disposable_postgres_separate_process_checkpoint",
            "checks": checks,
            "check_count": len(checks),
            "all_passed": True,
            "separate_processes": True,
            "host_pid": host.pid,
            "client_process_count": 4,
            "database": {
                "image": image,
                "image_id": inspected_image.get("Id"),
                "migration_count": len(migration_paths),
                "migration_sha256": [digest(path) for path in migration_paths],
            },
            "checkpoint": {
                "checkpoint_id": checkpoint_public_id,
                "revision_id": REVISION,
                "request_sha256": request_sha256,
                "note_sha256": hashlib.sha256(NOTE_TEXT.encode("utf-8")).hexdigest(),
                "created": True,
                "replayed": True,
                "drift_rejected": True,
            },
            "source_sha256": {
                "migration_up": digest(migration_paths[-1]),
                "migration_down": digest(down),
                "setup": digest(setup_path),
                "host_probe": digest(host_source),
                "client_probe": digest(client_source),
                "harness": digest(Path(__file__)),
                "database_contract": digest(contract_path),
            },
            "secrets_persisted": False,
            "actual_hangul": False,
            "production": False,
        }
        (run_root / "receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except Exception as error:  # noqa: BLE001 - boundary converts to a closed local category
        failure = f"{type(error).__name__}:{error}"
        safe_failure = {
            "schema_version": "hwpx-agent.p17-postgres-checkpoint-host-run/v1",
            "run_id": run_id,
            "scope": "current_pc_disposable_postgres_separate_process_checkpoint",
            "all_passed": False,
            "failed_stage": stage,
            "failure": failure[:240],
            "secrets_persisted": False,
        }
        (run_root / "receipt.json").write_text(
            json.dumps(safe_failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        if host is not None and host.poll() is None:
            host.terminate()
            try:
                host.wait(timeout=5)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait(timeout=5)
        container_state = invoke([docker, "inspect", container], expected=False)
        if container_state.returncode == 0:
            state = json.loads(container_state.stdout)[0]
            require(state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
                    "cleanup_container_ownership_mismatch")
            invoke([docker, "rm", "--force", container])
        volume_state = invoke([docker, "volume", "inspect", volume], expected=False)
        if volume_state.returncode == 0:
            state = json.loads(volume_state.stdout)[0]
            require(state.get("Labels", {}).get(LABEL) == run_id,
                    "cleanup_volume_ownership_mismatch")
            invoke([docker, "volume", "rm", volume])
        cleaned = True

    receipt_path = run_root / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["resources_cleaned"] = cleaned
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    if failure is not None:
        print(f"P17_POSTGRES_CHECKPOINT_HOST_CHECKS_FAILED stage={stage}")
        return 1
    print(f"P17_POSTGRES_CHECKPOINT_HOST_CHECKS_PASS run_id={run_id} checks={len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
