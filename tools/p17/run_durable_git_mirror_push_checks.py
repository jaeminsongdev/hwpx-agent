"""Disposable PostgreSQL + local bare-Git durable push/recovery acceptance."""

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
LABEL = "hwpx-agent.p17-durable-git-push-test"
MIGRATIONS = tuple(
    f"{number:04d}_{name}"
    for number, name in (
        (1, "p14_metadata"),
        (2, "p14_artifact_service"),
        (3, "p14_revision_cas"),
        (4, "p14_history_checkpoints"),
        (5, "p14_job_state_machine"),
        (6, "p14_worker_lease_fencing"),
        (7, "p14_idempotency_reconciliation"),
        (8, "p14_cancel_cleanup"),
        (9, "p14_retention_local_mirror"),
        (10, "p16_artifact_repository"),
        (11, "p16_plan_source"),
        (12, "p16_durable_plan_store"),
        (13, "p16_plan_review_evidence"),
        (14, "p17_history_checkpoint_note"),
        (15, "p17_atomic_mirror_checkpoint"),
        (16, "p17_durable_git_mirror_push"),
    )
)
TENANT_UUID = "d1000000-0000-0000-0000-000000000001"
PROJECT_UUID = "d2000000-0000-0000-0000-000000000001"
BRANCH_UUID = "d3000000-0000-0000-0000-000000000001"
MIRROR_UUID = "d7000000-0000-0000-0000-000000000001"
PROJECT = "prj_d2000000000000000000000000000001"
BRANCH = "brn_d3000000000000000000000000000001"
MIRROR = "mir_d7000000000000000000000000000001"
GIT_REF = "refs/heads/hwpx-agent/d3000000000000000000000000000001"
INITIAL_SNAPSHOT = "ed685a0de881a84828b3a46573afd4458419ea758367e7e5351c47746471cbbc"
RESULT_SNAPSHOT_1 = "50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f"
RESULT_SNAPSHOT_2 = "6" * 64
PLAN_1 = hashlib.sha256(b"p17 durable git push plan 1").hexdigest()
PLAN_2 = hashlib.sha256(b"p17 durable git push plan 2").hexdigest()
PLAN_DRIFT = hashlib.sha256(b"p17 durable git push plan drift").hexdigest()
ISSUER = "https://identity.hwpx-agent.example"
RESOURCE = "https://mcp.hwpx-agent.example"
KEY_ID = "local-key-01"
SERVICE_ID = "p17-durable-git-push-probe"
APP_ROLE = "hwpx_p17_durable_git_push_app"
FINALIZE_SIGNATURE = (
    "hwpx_agent.finalize_git_mirror_push_v1("
    "uuid,uuid,character,uuid,character,uuid,bigint,character,character)"
)
MARK_DIVERGED_SIGNATURE = (
    "hwpx_agent.mark_git_mirror_push_diverged_v1("
    "uuid,uuid,character,uuid,character,uuid,bigint)"
)


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def executable(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise CheckFailure(f"{name}_missing")
    path = Path(value)
    if not path.is_absolute():
        raise CheckFailure(f"{name}_not_absolute")
    return str(path)


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


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def subject_sha256() -> str:
    framed = f"service:{len(ISSUER)}:{ISSUER}:{len(SERVICE_ID)}:{SERVICE_ID}"
    return hashlib.sha256(framed.encode("utf-8")).hexdigest()


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
        "tenant_id": TENANT_UUID,
        "service_id": SERVICE_ID,
    }
    encoded_header = base64url(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_claims = base64url(
        json.dumps(claims, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_claims}"
    signature = base64url(
        hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    )
    return f"Bearer {signing_input}.{signature}"


def read_line(process: subprocess.Popen[str], timeout: float) -> str:
    require(process.stdout is not None, "host_stdout_missing")
    received: queue.Queue[str] = queue.Queue(maxsize=1)

    def reader() -> None:
        assert process.stdout is not None
        received.put(process.stdout.readline())

    threading.Thread(target=reader, daemon=True).start()
    try:
        line = received.get(timeout=timeout)
    except queue.Empty as error:
        raise CheckFailure("host_ready_timeout") from error
    require(bool(line), "host_closed_before_ready")
    return line.strip()


def revision_uuid(value: str) -> str:
    require(re.fullmatch(r"rev_[0-9a-f]{32}", value) is not None, "revision_id_invalid")
    return str(uuid.UUID(hex=value.removeprefix("rev_")))


def main() -> int:
    docker = executable("docker")
    cargo = executable("cargo")
    git = executable("git")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p17/durable-git-mirror-push/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    bare_repository = run_root / "repository.git"
    container = f"hwpx-p17-durable-git-push-{run_id}"
    volume = f"hwpx-p17-durable-git-push-data-{run_id}"
    contract_path = ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    image = contract["database"]["container_image"]
    require(
        re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image)
        is not None,
        "unpinned_image",
    )
    image_state = json.loads(invoke([docker, "image", "inspect", image]).stdout)[0]
    migration_paths = [
        ROOT / "migrations/postgres" / f"{name}.up.sql" for name in MIGRATIONS
    ]
    require(all(path.is_file() for path in migration_paths), "migration_missing")
    down_path = ROOT / "migrations/postgres/0016_p17_durable_git_mirror_push.down.sql"
    setup_path = ROOT / "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql"
    host_source = (
        ROOT / "crates/remote-sync-host/examples/postgres_durable_git_push_host.rs"
    )
    client_source = (
        ROOT / "crates/remote-sync-host/examples/postgres_durable_git_push_client.rs"
    )
    coordinator_source = ROOT / "crates/remote-sync-host/src/durable_git_push.rs"
    git_source = ROOT / "crates/remote-sync-host/src/git_mirror.rs"
    invoke(
        [cargo, "build", "--locked", "--offline", "-p", "remote-sync-host", "--examples"],
        timeout=180,
    )
    suffix = ".exe" if os.name == "nt" else ""
    host_program = (
        ROOT / "target/debug/examples" / f"postgres_durable_git_push_host{suffix}"
    )
    client_program = (
        ROOT / "target/debug/examples" / f"postgres_durable_git_push_client{suffix}"
    )
    require(host_program.is_file() and client_program.is_file(), "probe_not_built")

    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    cleaned = False
    hosts: list[subprocess.Popen[str]] = []
    admin_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    hmac_secret_text = secrets.token_hex(32)
    service_subject = subject_sha256()
    docker_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)

    def sql(
        statement: str, *, expected: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return invoke(
            [
                docker,
                "exec",
                "-i",
                container,
                "psql",
                "-X",
                "--no-align",
                "--tuples-only",
                "--quiet",
                "--set",
                "ON_ERROR_STOP=1",
                "--username",
                "postgres",
                "--dbname",
                "postgres",
            ],
            data=statement,
            expected=expected,
        )

    def ready() -> None:
        deadline = time.monotonic() + 45
        consecutive = 0
        while time.monotonic() < deadline:
            result = invoke(
                [docker, "exec", container, "pg_isready", "--username", "postgres"],
                expected=False,
                timeout=5,
            )
            if result.returncode == 0:
                consecutive += 1
                if consecutive == 3:
                    return
            else:
                consecutive = 0
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def database_port() -> str:
        state = json.loads(invoke([docker, "inspect", container]).stdout)[0]
        require(
            state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
            "container_ownership_mismatch",
        )
        bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
        require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port")
        require(bindings[0].get("HostIp") == "127.0.0.1", "non_loopback_port")
        return bindings[0]["HostPort"]

    def apply_migration(path: Path) -> None:
        prefix = (
            "SELECT set_config('hwpx_agent.migration_sha256',"
            f"'{digest(path)}',false);\n"
        )
        sql(prefix + path.read_text(encoding="utf-8"))

    def grant_functions() -> None:
        sql(
            f"""
GRANT USAGE ON SCHEMA hwpx_agent TO {APP_ROLE};
GRANT SELECT ON TABLE hwpx_agent.schema_versions TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION hwpx_agent.inspect_git_mirror_push_v1(
 uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,
 uuid,character,character) TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION hwpx_agent.store_git_mirror_push_plan_v1(
 uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,
 character,uuid,character,character,character,bytea,text,text,
 character,character,character,character,uuid,integer) TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION hwpx_agent.acquire_git_mirror_push_lease_v1(
 uuid,uuid,character,uuid,character,uuid,integer) TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION hwpx_agent.mark_git_mirror_push_diverged_v1(
 uuid,uuid,character,uuid,character,uuid,bigint) TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} TO {APP_ROLE};
"""
        )

    def host_environment(exchanges: int) -> dict[str, str]:
        return dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc-durable-git-push",
            HWPX_P17_PG_PORT=database_port(),
            HWPX_P17_PG_DATABASE="postgres",
            HWPX_P17_PG_USER=APP_ROLE,
            HWPX_P17_PG_PASSWORD=app_password,
            HWPX_P17_BIND_PORT="0",
            HWPX_P17_EXCHANGES=str(exchanges),
            HWPX_P17_LEASE_SECONDS="3",
            HWPX_P17_TENANT_UUID=TENANT_UUID,
            HWPX_P17_BARE_REPOSITORY=str(bare_repository.resolve()),
            HWPX_P17_GIT_PROGRAM=git,
            HWPX_P17_AUTH_HMAC_SECRET=hmac_secret_text,
        )

    def client_environment(
        port: int,
        bearer: str,
        *,
        generation: int,
        revision_id: str | None,
        initial_snapshot: str,
        result_snapshot: str,
        operation_plan: str,
        idempotency_key: str,
    ) -> dict[str, str]:
        result = dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc-durable-git-push-client",
            HWPX_P17_HOST_PORT=str(port),
            HWPX_P17_GENERATION=str(generation),
            HWPX_P17_PROJECT_ID=PROJECT,
            HWPX_P17_BRANCH_ID=BRANCH,
            HWPX_P17_MIRROR_ID=MIRROR,
            HWPX_P17_AUTHORIZATION=bearer,
            HWPX_P17_INITIAL_SNAPSHOT_SHA256=initial_snapshot,
            HWPX_P17_RESULT_SNAPSHOT_SHA256=result_snapshot,
            HWPX_P17_OPERATION_PLAN_SHA256=operation_plan,
            HWPX_P17_IDEMPOTENCY_KEY=idempotency_key,
        )
        if revision_id is not None:
            result["HWPX_P17_REVISION_ID"] = revision_id
        return result

    def start_host(exchanges: int) -> tuple[subprocess.Popen[str], int]:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [str(host_program)],
            env=host_environment(exchanges),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )
        hosts.append(process)
        event = json.loads(read_line(process, 15))
        require(
            event
            == {
                "schema_version": "hwpx-agent.p17-durable-git-push-host-probe/v1",
                "event": "ready",
                "port": event.get("port"),
                "expected_exchanges": exchanges,
            },
            "host_ready_event_mismatch",
        )
        port = event.get("port")
        require(isinstance(port, int) and 1 <= port <= 65535, "host_port_invalid")
        return process, port

    def finish_host(
        process: subprocess.Popen[str], expected_counts: tuple[int, int, int]
    ) -> None:
        output, error = process.communicate(timeout=20)
        require(process.returncode == 0 and error == "", "host_completion_failed")
        event = json.loads(output.strip())
        succeeded, rejected, unavailable = expected_counts
        require(
            event
            == {
                "schema_version": "hwpx-agent.p17-durable-git-push-host-probe/v1",
                "event": "complete",
                "succeeded": succeeded,
                "rejected": rejected,
                "unavailable": unavailable,
            },
            "host_complete_event_mismatch",
        )

    token_counter = 0
    token_time = int(time.time())

    def exchange(
        port: int,
        *,
        generation: int,
        revision_id: str | None,
        initial_snapshot: str,
        result_snapshot: str,
        operation_plan: str,
        idempotency_key: str,
        expected: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal token_counter
        token_counter += 1
        bearer = authorization(
            hmac_secret_text.encode("ascii"),
            f"p17-durable-git-token-{token_counter:04d}",
            token_time,
        )
        return invoke(
            [str(client_program)],
            env=client_environment(
                port,
                bearer,
                generation=generation,
                revision_id=revision_id,
                initial_snapshot=initial_snapshot,
                result_snapshot=result_snapshot,
                operation_plan=operation_plan,
                idempotency_key=idempotency_key,
            ),
            expected=expected,
            timeout=20,
        )

    def wait_for_expired_lease() -> None:
        deadline = time.monotonic() + 8
        consecutive = 0
        while time.monotonic() < deadline:
            expired = sql(
                "SELECT bool_and(lease_expires_at <= clock_timestamp()) "
                "FROM hwpx_agent.git_mirror_push_effects WHERE state='executing';"
            ).stdout.strip()
            if expired == "t":
                consecutive += 1
                if consecutive == 3:
                    return
            else:
                consecutive = 0
            time.sleep(0.1)
        raise CheckFailure("lease_did_not_expire")

    def reject_host_for_database_drift() -> None:
        result = invoke(
            [str(host_program)], env=host_environment(1), expected=False, timeout=15
        )
        require(result.returncode != 0, "database_drift_host_started")
        require(
            result.stderr.strip() == "PROBE_DATABASE_UNAVAILABLE",
            "database_drift_category_mismatch",
        )

    try:
        stage = "container"
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke(
            [
                docker,
                "run",
                "--detach",
                "--pull",
                "never",
                "--name",
                container,
                "--label",
                f"{LABEL}={run_id}",
                "--publish",
                "127.0.0.1::5432",
                "--memory",
                "512m",
                "--cpus",
                "2",
                "--pids-limit",
                "128",
                "--mount",
                f"type=volume,source={volume},target=/var/lib/postgresql",
                "--env",
                "POSTGRES_PASSWORD",
                image,
            ],
            env=docker_environment,
        )
        ready()
        checks.append("pinned_postgres_loopback_container")

        stage = "migrations"
        for migration_path in migration_paths:
            stage = migration_path.name
            apply_migration(migration_path)
        require(
            sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip()
            == "16",
            "migration_count_mismatch",
        )
        checks.append("all_sixteen_exact_migrations")

        stage = "empty_rollback"
        down_sql = down_path.read_text(encoding="utf-8")
        require(
            sql(down_sql, expected=False).returncode != 0,
            "ungated_empty_rollback_accepted",
        )
        sql(
            "SELECT set_config("
            "'hwpx_agent.allow_p17_durable_git_mirror_push_rollback','yes',false);\n"
            + down_sql
        )
        require(
            sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip()
            == "15",
            "empty_rollback_schema_count_mismatch",
        )
        apply_migration(migration_paths[-1])
        checks.extend(
            ["empty_rollback_requires_explicit_gate", "empty_rollback_and_reapply"]
        )

        stage = "seed"
        setup = setup_path.read_text(encoding="utf-8")
        require(
            setup.count("__P17_SERVICE_SUBJECT_SHA256__") == 4,
            "setup_subject_placeholder_drift",
        )
        sql(setup.replace("__P17_SERVICE_SUBJECT_SHA256__", service_subject))
        sql(
            f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{app_password}' "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT "
            "NOREPLICATION NOBYPASSRLS;"
        )
        grant_functions()
        privileges = sql(
            f"""
SELECT has_function_privilege('{APP_ROLE}',
 'hwpx_agent.inspect_git_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,uuid,character,character)',
 'EXECUTE') || '|' || has_function_privilege('{APP_ROLE}',
 '{FINALIZE_SIGNATURE}','EXECUTE') || '|' || has_function_privilege('{APP_ROLE}',
 'hwpx_agent.commit_revision_cas(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)',
 'EXECUTE') || '|' || has_table_privilege('{APP_ROLE}',
 'hwpx_agent.git_mirror_push_effects','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER');
"""
        ).stdout.strip()
        require(privileges == "true|true|false|false", "least_privilege_shape_mismatch")
        invoke([git, "init", "--bare", "--object-format=sha1", str(bare_repository)])
        require(
            invoke(
                [git, "--git-dir", str(bare_repository), "rev-parse", "--is-bare-repository"]
            ).stdout.strip()
            == "true",
            "bare_repository_invalid",
        )
        checks.extend(["dedicated_function_only_role", "exact_local_bare_git_repository"])

        stage = "artifact_acl_admission"
        sql(
            "INSERT INTO hwpx_agent.artifact_acl "
            "(tenant_id,artifact_id,subject_sha256,can_manage) "
            "SELECT artifact.tenant_id,artifact.artifact_id,repeat('e',64),true "
            "FROM hwpx_agent.artifacts AS artifact "
            f"WHERE artifact.tenant_id='{TENANT_UUID}' "
            f"AND artifact.content_sha256='{RESULT_SNAPSHOT_1}' "
            "ON CONFLICT DO NOTHING;"
            "UPDATE hwpx_agent.artifact_acl AS acl "
            "SET can_read=false,can_manage=false,can_read_quarantine=true "
            "FROM hwpx_agent.artifacts AS artifact "
            "WHERE acl.tenant_id=artifact.tenant_id AND acl.artifact_id=artifact.artifact_id "
            f"AND artifact.tenant_id='{TENANT_UUID}' "
            f"AND artifact.content_sha256='{RESULT_SNAPSHOT_1}' "
            f"AND acl.subject_sha256='{service_subject}';"
        )
        denied_host, denied_port = start_host(1)
        denied = exchange(
            denied_port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_1,
            idempotency_key="durable-git-push-denied-0001",
            expected=False,
        )
        require(
            denied.returncode != 0
            and denied.stdout == ""
            and denied.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "artifact_acl_denial_not_rejected",
        )
        finish_host(denied_host, (1, 0, 0))
        require(
            sql("SELECT count(*) FROM hwpx_agent.git_mirror_push_effects;").stdout.strip()
            == "0",
            "artifact_acl_denial_stored_effect",
        )
        require(
            invoke(
                [git, "--git-dir", str(bare_repository), "show-ref", "--verify", GIT_REF],
                expected=False,
            ).returncode
            != 0,
            "artifact_acl_denial_created_ref",
        )
        sql(
            "UPDATE hwpx_agent.artifact_acl AS acl "
            "SET can_read=true,can_manage=true,can_read_quarantine=false "
            "FROM hwpx_agent.artifacts AS artifact "
            "WHERE acl.tenant_id=artifact.tenant_id AND acl.artifact_id=artifact.artifact_id "
            f"AND artifact.tenant_id='{TENANT_UUID}' "
            f"AND artifact.content_sha256='{RESULT_SNAPSHOT_1}' "
            f"AND acl.subject_sha256='{service_subject}';"
            "DELETE FROM hwpx_agent.artifact_acl AS acl USING hwpx_agent.artifacts AS artifact "
            "WHERE acl.tenant_id=artifact.tenant_id AND acl.artifact_id=artifact.artifact_id "
            f"AND artifact.tenant_id='{TENANT_UUID}' "
            f"AND artifact.content_sha256='{RESULT_SNAPSHOT_1}' "
            "AND acl.subject_sha256=repeat('e',64);"
        )
        checks.append("verified_artifact_acl_required_before_plan_or_git_effect")

        stage = "committed_effect_interruption"
        first_host, first_port = start_host(1)
        sql(f"REVOKE EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} FROM {APP_ROLE};")
        interrupted = exchange(
            first_port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_1,
            idempotency_key="durable-git-push-0001",
            expected=False,
        )
        require(
            interrupted.returncode != 0
            and interrupted.stdout == ""
            and interrupted.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "interrupted_push_not_uncertain",
        )
        finish_host(first_host, (0, 0, 1))
        interrupted_state = sql(
            "SELECT state || '|' || lease_fencing_token || '|' || "
            "CASE WHEN effect_receipt_sha256 IS NULL THEN 'clear' ELSE 'set' END || '|' || "
            "(SELECT count(*) FROM hwpx_agent.revisions WHERE tenant_id="
            f"'{TENANT_UUID}' AND project_id='{PROJECT_UUID}') "
            "FROM hwpx_agent.git_mirror_push_effects;"
        ).stdout.strip()
        require(interrupted_state == "executing|1|clear|0", "interrupted_state_mismatch")
        git_result_1 = invoke(
            [git, "--git-dir", str(bare_repository), "rev-parse", GIT_REF]
        ).stdout.strip()
        require(re.fullmatch(r"[0-9a-f]{40}", git_result_1) is not None, "git_effect_missing")
        stored_git_result_1 = sql(
            "SELECT result_git_oid FROM hwpx_agent.git_mirror_push_effects;"
        ).stdout.strip()
        require(stored_git_result_1 == git_result_1, "stored_git_result_mismatch")
        blocked = sql(
            f"UPDATE hwpx_agent.branches SET head_generation=1 WHERE tenant_id='{TENANT_UUID}' "
            f"AND project_id='{PROJECT_UUID}' AND branch_id='{BRANCH_UUID}';",
            expected=False,
        )
        require(blocked.returncode != 0, "reserved_branch_mutation_accepted")
        wrong_head_with_fence = sql(
            "BEGIN;"
            "SELECT set_config('hwpx_agent.git_push_id',(SELECT push_id::text FROM "
            "hwpx_agent.git_mirror_push_effects),true);"
            "SELECT set_config('hwpx_agent.git_push_fencing_token',(SELECT "
            "lease_fencing_token::text FROM hwpx_agent.git_mirror_push_effects),true);"
            f"UPDATE hwpx_agent.branches SET head_generation=1 WHERE tenant_id='{TENANT_UUID}' "
            f"AND project_id='{PROJECT_UUID}' AND branch_id='{BRANCH_UUID}';"
            "COMMIT;",
            expected=False,
        )
        require(
            wrong_head_with_fence.returncode != 0,
            "reserved_branch_wrong_head_with_fence_accepted",
        )
        checks.extend(
            [
                "git_committed_database_finalize_interrupted_is_unavailable",
                "canonical_plan_precedes_git_effect",
                "executing_reservation_blocks_branch_mutation",
                "exact_fence_cannot_authorize_wrong_branch_head",
            ]
        )

        stage = "committed_effect_recovery"
        grant_functions()
        wait_for_expired_lease()
        recovery_host, recovery_port = start_host(3)
        recovered = exchange(
            recovery_port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_1,
            idempotency_key="durable-git-push-0001",
            expected=False,
        )
        if recovered.returncode != 0:
            recovery_state = sql(
                "SELECT state || '|' || lease_fencing_token || '|' || "
                "(lease_expires_at > clock_timestamp())::text || '|' || "
                "(SELECT count(*) FROM hwpx_agent.revisions) "
                "FROM hwpx_agent.git_mirror_push_effects;"
            ).stdout.strip()
            database_log = invoke([docker, "logs", container], expected=False)
            categories = re.findall(
                r"(?:GIT_MIRROR_PUSH|IDEMPOTENCY|P14_09|P17)_[A-Z0-9_]{3,80}",
                database_log.stdout + database_log.stderr,
            )
            category = categories[-1] if categories else "no_database_category"
            raise CheckFailure(
                f"recovery_failed state={recovery_state} category={category}"
            )
        replayed = exchange(
            recovery_port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_1,
            idempotency_key="durable-git-push-0001",
        )
        drifted = exchange(
            recovery_port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_DRIFT,
            idempotency_key="durable-git-push-0001",
            expected=False,
        )
        require(
            drifted.returncode != 0
            and drifted.stdout == ""
            and drifted.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "idempotency_drift_not_rejected",
        )
        finish_host(recovery_host, (3, 0, 0))
        recovered_event = json.loads(recovered.stdout)
        replayed_event = json.loads(replayed.stdout)
        require(recovered_event == replayed_event, "replay_response_drift")
        require(
            recovered_event.get("outcome") == "succeeded"
            and recovered_event.get("generation") == 1
            and recovered_event.get("snapshot_sha256") == RESULT_SNAPSHOT_1,
            "recovery_response_mismatch",
        )
        revision_1 = recovered_event.get("revision_id")
        require(isinstance(revision_1, str), "recovery_revision_missing")
        revision_uuid_1 = revision_uuid(revision_1)
        durable = sql(
            f"""
SELECT state || '|' || lease_fencing_token || '|' ||
       CASE WHEN effect_receipt_sha256 ~ '^[0-9a-f]{{64}}$' THEN 'receipt' ELSE 'bad' END
FROM hwpx_agent.git_mirror_push_effects;
SELECT count(*) || '|' || count(*) FILTER (WHERE revision_id='{revision_uuid_1}')
FROM hwpx_agent.revisions WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}';
SELECT count(*) FROM hwpx_agent.revision_graph_seals
WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}';
SELECT count(*) FROM hwpx_agent.revision_commit_receipts
WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}';
SELECT count(*) FROM hwpx_agent.audit_events
WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}'
  AND event_type='revision.cas_committed';
SELECT state || '|' || observed_revision_id || '|' || observed_generation || '|' ||
       snapshot_sha256 || '|' || CASE WHEN pending_plan_sha256 IS NULL THEN 'clear' ELSE 'set' END
FROM hwpx_agent.project_local_mirrors
WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}' AND mirror_id='{MIRROR_UUID}';
"""
        ).stdout.strip().splitlines()
        require(
            durable
            == [
                "finalized|2|receipt",
                "1|1",
                "1",
                "1",
                "1",
                f"clean|{revision_uuid_1}|1|{RESULT_SNAPSHOT_1}|clear",
            ],
            "durable_final_state_mismatch",
        )
        require(
            invoke(
                [git, "--git-dir", str(bare_repository), "rev-list", "--count", GIT_REF]
            ).stdout.strip()
            == "1",
            "git_replay_created_extra_commit",
        )
        immutable = sql(
            "UPDATE hwpx_agent.git_mirror_push_effects SET git_plan_bytes = git_plan_sha256;",
            expected=False,
        )
        require(immutable.returncode != 0, "finalized_effect_mutation_accepted")
        checks.extend(
            [
                "expired_lease_reacquired_with_higher_fence",
                "committed_git_observed_and_database_finalized_once",
                "exact_request_replay_has_no_extra_commit_or_revision",
                "same_key_changed_payload_rejected",
                "finalized_effect_is_immutable",
            ]
        )

        stage = "divergence_interruption"
        second_host, second_port = start_host(1)
        sql(f"REVOKE EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} FROM {APP_ROLE};")
        second_interrupted = exchange(
            second_port,
            generation=1,
            revision_id=revision_1,
            initial_snapshot=RESULT_SNAPSHOT_1,
            result_snapshot=RESULT_SNAPSHOT_2,
            operation_plan=PLAN_2,
            idempotency_key="durable-git-push-0002",
            expected=False,
        )
        require(
            second_interrupted.returncode != 0
            and second_interrupted.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "second_interruption_not_uncertain",
        )
        finish_host(second_host, (0, 0, 1))
        git_result_2 = invoke(
            [git, "--git-dir", str(bare_repository), "rev-parse", GIT_REF]
        ).stdout.strip()
        require(git_result_2 != git_result_1, "second_git_effect_missing")
        tree = invoke(
            [git, "--git-dir", str(bare_repository), "rev-parse", f"{git_result_2}^{{tree}}"]
        ).stdout.strip()
        competing_environment = dict(
            os.environ,
            GIT_AUTHOR_NAME="P17 competing writer",
            GIT_AUTHOR_EMAIL="p17-competing@example.invalid",
            GIT_COMMITTER_NAME="P17 competing writer",
            GIT_COMMITTER_EMAIL="p17-competing@example.invalid",
            GIT_AUTHOR_DATE="2001-01-01T00:00:00Z",
            GIT_COMMITTER_DATE="2001-01-01T00:00:00Z",
        )
        competing_oid = invoke(
            [
                git,
                "--git-dir",
                str(bare_repository),
                "commit-tree",
                tree,
                "-p",
                git_result_2,
                "-m",
                "bounded competing ref state",
            ],
            env=competing_environment,
        ).stdout.strip()
        invoke(
            [
                git,
                "--git-dir",
                str(bare_repository),
                "update-ref",
                GIT_REF,
                competing_oid,
                git_result_2,
            ]
        )
        grant_functions()
        wait_for_expired_lease()
        divergence_interrupted_host, divergence_interrupted_port = start_host(1)
        sql(
            f"REVOKE EXECUTE ON FUNCTION {MARK_DIVERGED_SIGNATURE} FROM {APP_ROLE};"
        )
        divergence_interrupted = exchange(
            divergence_interrupted_port,
            generation=1,
            revision_id=revision_1,
            initial_snapshot=RESULT_SNAPSHOT_1,
            result_snapshot=RESULT_SNAPSHOT_2,
            operation_plan=PLAN_2,
            idempotency_key="durable-git-push-0002",
            expected=False,
        )
        require(
            divergence_interrupted.returncode != 0
            and divergence_interrupted.stdout == ""
            and divergence_interrupted.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "divergence_transition_interruption_not_uncertain",
        )
        finish_host(divergence_interrupted_host, (0, 0, 1))
        require(
            sql(
                f"SELECT state || '|' || lease_fencing_token FROM "
                "hwpx_agent.git_mirror_push_effects WHERE "
                f"result_snapshot_sha256='{RESULT_SNAPSHOT_2}';"
            ).stdout.strip()
            == "executing|2",
            "divergence_transition_interruption_state_mismatch",
        )
        grant_functions()
        wait_for_expired_lease()
        diverged_host, diverged_port = start_host(1)
        diverged = exchange(
            diverged_port,
            generation=1,
            revision_id=revision_1,
            initial_snapshot=RESULT_SNAPSHOT_1,
            result_snapshot=RESULT_SNAPSHOT_2,
            operation_plan=PLAN_2,
            idempotency_key="durable-git-push-0002",
            expected=False,
        )
        require(
            diverged.returncode != 0
            and diverged.stdout == ""
            and diverged.stderr.strip() == "PROBE_EXCHANGE_FAILED",
            "divergence_not_rejected",
        )
        finish_host(diverged_host, (1, 0, 0))
        divergence_state = sql(
            f"""
SELECT state || '|' || lease_fencing_token FROM hwpx_agent.git_mirror_push_effects
WHERE result_snapshot_sha256='{RESULT_SNAPSHOT_2}';
SELECT state || '|' || observed_revision_id || '|' || observed_generation || '|' ||
       CASE WHEN pending_plan_sha256 IS NULL THEN 'clear' ELSE 'set' END
FROM hwpx_agent.project_local_mirrors WHERE tenant_id='{TENANT_UUID}' AND mirror_id='{MIRROR_UUID}';
SELECT count(*) FROM hwpx_agent.revisions
WHERE tenant_id='{TENANT_UUID}' AND project_id='{PROJECT_UUID}';
"""
        ).stdout.strip().splitlines()
        require(
            divergence_state
            == [
                "diverged|3",
                f"manual_merge_required|{revision_uuid_1}|1|set",
                "1",
            ],
            "divergence_state_mismatch",
        )
        require(
            invoke(
                [git, "--git-dir", str(bare_repository), "rev-parse", GIT_REF]
            ).stdout.strip()
            == competing_oid,
            "competing_ref_overwritten",
        )
        checks.extend(
            [
                "divergence_database_transition_interruption_is_unavailable",
                "external_ref_divergence_detected_after_interruption",
                "competing_ref_never_overwritten",
                "divergence_enters_manual_merge_without_database_revision",
            ]
        )

        stage = "retained_rollback"
        require(
            sql(
                "SELECT set_config("
                "'hwpx_agent.allow_p17_durable_git_mirror_push_rollback','yes',false);\n"
                + down_sql,
                expected=False,
            ).returncode
            != 0,
            "retained_effect_rollback_accepted",
        )
        checks.append("rollback_refuses_retained_effects")

        stage = "admission_drift_migration_digest"
        v16_digest = digest(migration_paths[-1])
        sql(
            "ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            "UPDATE hwpx_agent.schema_versions SET migration_sha256=repeat('f',64) "
            "WHERE version=16;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;"
        )
        reject_host_for_database_drift()
        sql(
            "ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            f"UPDATE hwpx_agent.schema_versions SET migration_sha256='{v16_digest}' "
            "WHERE version=16;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;"
        )
        stage = "admission_drift_effect_rls"
        sql("ALTER TABLE hwpx_agent.git_mirror_push_effects DISABLE ROW LEVEL SECURITY;")
        reject_host_for_database_drift()
        sql(
            "ALTER TABLE hwpx_agent.git_mirror_push_effects ENABLE ROW LEVEL SECURITY;"
            "ALTER TABLE hwpx_agent.git_mirror_push_effects FORCE ROW LEVEL SECURITY;"
        )
        stage = "admission_drift_application_execute"
        sql(f"REVOKE EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} FROM {APP_ROLE};")
        reject_host_for_database_drift()
        grant_functions()
        stage = "admission_drift_public_execute"
        sql(f"GRANT EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} TO PUBLIC;")
        reject_host_for_database_drift()
        sql(f"REVOKE EXECUTE ON FUNCTION {FINALIZE_SIGNATURE} FROM PUBLIC;")
        stage = "admission_drift_search_path"
        sql(f"ALTER FUNCTION {FINALIZE_SIGNATURE} RESET search_path;")
        reject_host_for_database_drift()
        sql(
            f"ALTER FUNCTION {FINALIZE_SIGNATURE} "
            "SET search_path = pg_catalog, hwpx_agent;"
        )
        stage = "admission_drift_security_definer"
        sql(f"ALTER FUNCTION {FINALIZE_SIGNATURE} SECURITY INVOKER;")
        reject_host_for_database_drift()
        sql(f"ALTER FUNCTION {FINALIZE_SIGNATURE} SECURITY DEFINER;")
        checks.extend(
            [
                "migration_digest_drift_rejected",
                "effect_rls_drift_rejected",
                "execute_privilege_drift_rejected",
                "public_execute_drift_rejected",
                "fixed_search_path_drift_rejected",
                "security_definer_drift_rejected",
            ]
        )

        stage = "receipt"
        effect_receipts = sql(
            "SELECT string_agg(request_sha256 || ':' || git_plan_sha256 || ':' || "
            "git_state_sha256 || ':' || state, ',' ORDER BY result_generation) "
            "FROM hwpx_agent.git_mirror_push_effects;"
        ).stdout.strip()
        receipt = {
            "schema_version": "hwpx-agent.p17-durable-git-mirror-push-run/v1",
            "run_id": run_id,
            "scope": "current_pc_postgresql_local_bare_git_loopback",
            "checks": checks,
            "check_count": len(checks),
            "all_passed": True,
            "database": {
                "image": image,
                "image_id": image_state.get("Id"),
                "migration_count": len(migration_paths),
                "migration_sha256": [digest(path) for path in migration_paths],
            },
            "effect": {
                "first_revision_id": revision_1,
                "first_result_git_oid": git_result_1,
                "second_result_git_oid": git_result_2,
                "competing_git_oid": competing_oid,
                "bounded_state_sha256": hashlib.sha256(
                    effect_receipts.encode("ascii")
                ).hexdigest(),
                "committed_recovered": True,
                "exact_replay": True,
                "divergence_preserved": True,
            },
            "source_sha256": {
                "migration_up": digest(migration_paths[-1]),
                "migration_down": digest(down_path),
                "setup": digest(setup_path),
                "host_probe": digest(host_source),
                "client_probe": digest(client_source),
                "coordinator": digest(coordinator_source),
                "git_effect_host": digest(git_source),
                "harness": digest(Path(__file__)),
                "database_contract": digest(contract_path),
            },
            "secrets_persisted": False,
            "authenticated_loopback": True,
            "durable_git_plan_before_effect": True,
            "database_and_git_exactly_once_recovery": True,
            "actual_remote_network": False,
            "actual_hangul": False,
            "production": False,
        }
        (run_root / "receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception as error:  # noqa: BLE001 - boundary emits a closed local category
        failure = f"{type(error).__name__}:{error}"
        (run_root / "receipt.json").write_text(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.p17-durable-git-mirror-push-run/v1",
                    "run_id": run_id,
                    "scope": "current_pc_postgresql_local_bare_git_loopback",
                    "all_passed": False,
                    "failed_stage": stage,
                    "failure": failure[:240],
                    "secrets_persisted": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    finally:
        for host in hosts:
            if host.poll() is None:
                host.terminate()
                try:
                    host.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    host.kill()
                    host.wait(timeout=5)
        container_state = invoke([docker, "inspect", container], expected=False)
        if container_state.returncode == 0:
            state = json.loads(container_state.stdout)[0]
            require(
                state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
                "cleanup_container_ownership_mismatch",
            )
            invoke([docker, "rm", "--force", container])
        volume_state = invoke([docker, "volume", "inspect", volume], expected=False)
        if volume_state.returncode == 0:
            state = json.loads(volume_state.stdout)[0]
            require(
                state.get("Labels", {}).get(LABEL) == run_id,
                "cleanup_volume_ownership_mismatch",
            )
            invoke([docker, "volume", "rm", volume])
        cleaned = True

    receipt_path = run_root / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["resources_cleaned"] = cleaned
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if failure is not None:
        print(f"P17_DURABLE_GIT_MIRROR_PUSH_CHECKS_FAILED stage={stage}")
        return 1
    print(
        "P17_DURABLE_GIT_MIRROR_PUSH_CHECKS_OK "
        f"run_id={run_id} checks={len(checks)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
