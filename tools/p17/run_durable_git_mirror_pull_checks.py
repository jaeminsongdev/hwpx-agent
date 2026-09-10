"""Disposable PostgreSQL 18.4 + local bare-Git durable pull acceptance."""

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
LABEL = "hwpx-agent.p17-durable-git-pull-test"
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
        (17, "p17_durable_git_mirror_pull"),
    )
)
TENANT_UUID = "d1000000-0000-0000-0000-000000000001"
PROJECT_UUID = "d2000000-0000-0000-0000-000000000001"
BRANCH_UUID = "d3000000-0000-0000-0000-000000000001"
PUSH_MIRROR_UUID = "d7000000-0000-0000-0000-000000000001"
CLEAN_MIRROR_UUID = "d7000000-0000-0000-0000-000000000002"
AHEAD_MIRROR_UUID = "d7000000-0000-0000-0000-000000000003"
DRIFT_MIRROR_UUID = "d7000000-0000-0000-0000-000000000004"
PROJECT = "prj_d2000000000000000000000000000001"
BRANCH = "brn_d3000000000000000000000000000001"
PUSH_MIRROR = "mir_d7000000000000000000000000000001"
CLEAN_MIRROR = "mir_d7000000000000000000000000000002"
AHEAD_MIRROR = "mir_d7000000000000000000000000000003"
DRIFT_MIRROR = "mir_d7000000000000000000000000000004"
GIT_REF = "refs/heads/hwpx-agent/d3000000000000000000000000000001"
INITIAL_SNAPSHOT = "ed685a0de881a84828b3a46573afd4458419ea758367e7e5351c47746471cbbc"
RESULT_SNAPSHOT_1 = "50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f"
RESULT_SNAPSHOT_2 = "6" * 64
LOCAL_SNAPSHOT = "8" * 64
LOCAL_PLAN = "9" * 64
PLAN_1 = hashlib.sha256(b"p17 durable git pull seed plan 1").hexdigest()
PLAN_2 = hashlib.sha256(b"p17 durable git pull seed plan 2").hexdigest()
ISSUER = "https://identity.hwpx-agent.example"
RESOURCE = "https://mcp.hwpx-agent.example"
KEY_ID = "local-key-01"
PUSH_SERVICE_ID = "p17-durable-git-push-probe"
PULL_SERVICE_ID = "p17-durable-git-pull-probe"
APP_ROLE = "hwpx_p17_durable_git_pull_app"
PULL_FUNCTION = (
    "hwpx_agent.reconcile_git_mirror_pull_v1("
    "uuid,uuid,character,uuid,uuid,uuid,character,uuid,bigint,character,"
    "uuid,bigint,character,text,character)"
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


def subject_sha256(service_id: str) -> str:
    framed = f"service:{len(ISSUER)}:{ISSUER}:{len(service_id)}:{service_id}"
    return hashlib.sha256(framed.encode("utf-8")).hexdigest()


def authorization(secret: bytes, service_id: str, token_id: str, now: int) -> str:
    header = {"alg": "HS256", "kid": KEY_ID, "typ": "hwpx-service+jwt"}
    claims = {
        "iss": ISSUER,
        "sub": service_id,
        "aud": RESOURCE,
        "exp": now + 120,
        "nbf": now - 10,
        "iat": now - 10,
        "jti": token_id,
        "scope": "mirror.sync",
        "token_kind": "service",
        "tenant_id": TENANT_UUID,
        "service_id": service_id,
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
    run_root = ROOT / "artifacts/p17/durable-git-mirror-pull/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    bare_repository = run_root / "repository.git"
    receipt_path = run_root / "receipt.json"
    container = f"hwpx-p17-durable-git-pull-{run_id}"
    volume = f"hwpx-p17-durable-git-pull-data-{run_id}"
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
    down_path = ROOT / "migrations/postgres/0017_p17_durable_git_mirror_pull.down.sql"
    push_setup_path = ROOT / "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql"
    pull_seed_path = ROOT / "tools/p17/fixtures/p17_durable_git_mirror_pull_seed.sql"
    sources = [
        ROOT / "crates/local-sync/src/adapter.rs",
        ROOT / "crates/local-sync/src/lib.rs",
        ROOT / "crates/remote-sync-host/src/durable_git_pull.rs",
        ROOT / "crates/remote-sync-host/src/durable_git_push.rs",
        ROOT / "crates/remote-sync-host/src/git_mirror.rs",
        ROOT / "crates/remote-sync-host/examples/postgres_durable_git_pull_host.rs",
        ROOT / "crates/remote-sync-host/examples/postgres_durable_git_pull_client.rs",
        push_setup_path,
        pull_seed_path,
        ROOT / "tools/p17/run_durable_git_mirror_pull_checks.py",
        contract_path,
        *migration_paths,
        down_path,
    ]
    require(all(path.is_file() for path in sources), "source_missing")
    invoke(
        [cargo, "build", "--locked", "--offline", "-p", "remote-sync-host", "--examples"],
        timeout=180,
    )
    suffix = ".exe" if os.name == "nt" else ""
    examples = ROOT / "target/debug/examples"
    push_host = examples / f"postgres_durable_git_push_host{suffix}"
    push_client = examples / f"postgres_durable_git_push_client{suffix}"
    pull_host = examples / f"postgres_durable_git_pull_host{suffix}"
    pull_client = examples / f"postgres_durable_git_pull_client{suffix}"
    require(
        all(path.is_file() for path in [push_host, push_client, pull_host, pull_client]),
        "probe_not_built",
    )

    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    failure_category: str | None = None
    failure_detail: str | None = None
    cleaned = False
    receipt: dict[str, object] | None = None
    hosts: list[subprocess.Popen[str]] = []
    admin_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    hmac_secret_text = secrets.token_hex(32)
    push_subject = subject_sha256(PUSH_SERVICE_ID)
    pull_subject = subject_sha256(PULL_SERVICE_ID)
    docker_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)

    def sql(statement: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
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
GRANT EXECUTE ON FUNCTION hwpx_agent.finalize_git_mirror_push_v1(
 uuid,uuid,character,uuid,character,uuid,bigint,character,character) TO {APP_ROLE};
GRANT EXECUTE ON FUNCTION {PULL_FUNCTION} TO {APP_ROLE};
"""
        )

    def host_environment(kind: str, exchanges: int) -> dict[str, str]:
        mode = f"isolated-current-pc-durable-git-{kind}"
        result = dict(
            os.environ,
            HWPX_P17_PROBE_MODE=mode,
            HWPX_P17_PG_PORT=database_port(),
            HWPX_P17_PG_DATABASE="postgres",
            HWPX_P17_PG_USER=APP_ROLE,
            HWPX_P17_PG_PASSWORD=app_password,
            HWPX_P17_BIND_PORT="0",
            HWPX_P17_EXCHANGES=str(exchanges),
            HWPX_P17_TENANT_UUID=TENANT_UUID,
            HWPX_P17_BARE_REPOSITORY=str(bare_repository.resolve()),
            HWPX_P17_GIT_PROGRAM=git,
            HWPX_P17_AUTH_HMAC_SECRET=hmac_secret_text,
        )
        if kind == "push":
            result["HWPX_P17_LEASE_SECONDS"] = "30"
        return result

    def start_host(kind: str, exchanges: int) -> tuple[subprocess.Popen[str], int]:
        program = push_host if kind == "push" else pull_host
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [str(program)],
            env=host_environment(kind, exchanges),
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
        require(event.get("event") == "ready", "host_ready_event_mismatch")
        require(event.get("expected_exchanges") == exchanges, "host_exchange_count_mismatch")
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
        actual_counts = (
            event.get("succeeded"),
            event.get("rejected"),
            event.get("unavailable"),
        )
        require(
            actual_counts == (succeeded, rejected, unavailable),
            f"host_complete_event_mismatch_{actual_counts}_{expected_counts}",
        )

    token_counter = 0
    token_time = int(time.time())

    def bearer(service_id: str) -> str:
        nonlocal token_counter
        token_counter += 1
        return authorization(
            hmac_secret_text.encode("ascii"),
            service_id,
            f"p17-durable-git-pull-token-{token_counter:04d}",
            token_time,
        )

    def push_exchange(
        port: int,
        *,
        generation: int,
        revision_id: str | None,
        initial_snapshot: str,
        result_snapshot: str,
        operation_plan: str,
        idempotency_key: str,
    ) -> dict[str, object]:
        environment = dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc-durable-git-push-client",
            HWPX_P17_HOST_PORT=str(port),
            HWPX_P17_GENERATION=str(generation),
            HWPX_P17_PROJECT_ID=PROJECT,
            HWPX_P17_BRANCH_ID=BRANCH,
            HWPX_P17_MIRROR_ID=PUSH_MIRROR,
            HWPX_P17_AUTHORIZATION=bearer(PUSH_SERVICE_ID),
            HWPX_P17_INITIAL_SNAPSHOT_SHA256=initial_snapshot,
            HWPX_P17_RESULT_SNAPSHOT_SHA256=result_snapshot,
            HWPX_P17_OPERATION_PLAN_SHA256=operation_plan,
            HWPX_P17_IDEMPOTENCY_KEY=idempotency_key,
        )
        if revision_id is not None:
            environment["HWPX_P17_REVISION_ID"] = revision_id
        result = invoke([str(push_client)], env=environment, timeout=20)
        return json.loads(result.stdout)

    def pull_exchange(
        port: int,
        *,
        mirror_id: str,
        generation: int,
        revision_id: str,
        initial_snapshot: str,
        state: str,
        expected: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        environment = dict(
            os.environ,
            HWPX_P17_PROBE_MODE="isolated-current-pc-durable-git-pull-client",
            HWPX_P17_HOST_PORT=str(port),
            HWPX_P17_GENERATION=str(generation),
            HWPX_P17_PROJECT_ID=PROJECT,
            HWPX_P17_BRANCH_ID=BRANCH,
            HWPX_P17_MIRROR_ID=mirror_id,
            HWPX_P17_REVISION_ID=revision_id,
            HWPX_P17_AUTHORIZATION=bearer(PULL_SERVICE_ID),
            HWPX_P17_INITIAL_SNAPSHOT_SHA256=initial_snapshot,
            HWPX_P17_CLIENT_STATE=state,
            HWPX_P17_LOCAL_SNAPSHOT_SHA256=LOCAL_SNAPSHOT,
            HWPX_P17_OPERATION_PLAN_SHA256=LOCAL_PLAN,
        )
        return invoke([str(pull_client)], env=environment, expected=expected, timeout=20)

    def reject_pull_host_for_database_drift() -> None:
        result = invoke(
            [str(pull_host)], env=host_environment("pull", 1), expected=False, timeout=15
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
            sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "17",
            "migration_count_mismatch",
        )
        checks.append("all_seventeen_exact_migrations")

        stage = "empty_rollback"
        down_sql = down_path.read_text(encoding="utf-8")
        require(sql(down_sql, expected=False).returncode != 0, "ungated_rollback_accepted")
        sql(
            "SELECT set_config("
            "'hwpx_agent.allow_p17_durable_git_mirror_pull_rollback','yes',false);\n"
            + down_sql
        )
        require(
            sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "16",
            "empty_rollback_schema_count_mismatch",
        )
        apply_migration(migration_paths[-1])
        checks.append("rollback_requires_gate_and_empty_reapply_succeeds")

        stage = "seed"
        push_setup = push_setup_path.read_text(encoding="utf-8")
        sql(push_setup.replace("__P17_SERVICE_SUBJECT_SHA256__", push_subject))
        sql(
            f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{app_password}' "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT "
            "NOREPLICATION NOBYPASSRLS;"
        )
        grant_functions()
        privileges = sql(
            f"""
SELECT has_function_privilege('{APP_ROLE}','{PULL_FUNCTION}','EXECUTE') || '|'
 || has_table_privilege('{APP_ROLE}','hwpx_agent.git_mirror_pull_observations',
    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER');
"""
        ).stdout.strip()
        require(privileges == "true|false", "least_privilege_shape_mismatch")
        invoke([git, "init", "--bare", "--object-format=sha1", str(bare_repository)])
        checks.extend(["dedicated_function_only_role", "exact_local_bare_git_repository"])

        stage = "seed_generation_one"
        host, port = start_host("push", 1)
        first = push_exchange(
            port,
            generation=0,
            revision_id=None,
            initial_snapshot=INITIAL_SNAPSHOT,
            result_snapshot=RESULT_SNAPSHOT_1,
            operation_plan=PLAN_1,
            idempotency_key="pull-seed-push-key-0001",
        )
        finish_host(host, (1, 0, 0))
        revision_one = str(first["revision_id"])
        require(first["generation"] == 1, "first_generation_mismatch")

        pull_seed = pull_seed_path.read_text(encoding="utf-8")
        sql(
            pull_seed.replace("__P17_PULL_SUBJECT_SHA256__", pull_subject).replace(
                "__P17_REVISION_ONE_UUID__", revision_uuid(revision_one)
            )
        )
        checks.append("exact_observed_snapshot_backfill_and_seed")

        stage = "seed_generation_two"
        host, port = start_host("push", 1)
        second = push_exchange(
            port,
            generation=1,
            revision_id=revision_one,
            initial_snapshot=RESULT_SNAPSHOT_1,
            result_snapshot=RESULT_SNAPSHOT_2,
            operation_plan=PLAN_2,
            idempotency_key="pull-seed-push-key-0002",
        )
        finish_host(host, (1, 0, 0))
        revision_two = str(second["revision_id"])
        require(second["generation"] == 2, "second_generation_mismatch")
        sql(
            f"""
INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT tenant_id, artifact_id, '{pull_subject}', true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = '{TENANT_UUID}'
  AND content_sha256 = '{RESULT_SNAPSHOT_2}'
ON CONFLICT (tenant_id, artifact_id, subject_sha256) DO UPDATE
SET can_read = EXCLUDED.can_read, can_manage = EXCLUDED.can_manage;
"""
        )
        require(
            sql(
                f"""
SELECT count(*) FROM hwpx_agent.artifact_acl AS acl
JOIN hwpx_agent.artifacts AS artifact
  ON artifact.tenant_id = acl.tenant_id
 AND artifact.artifact_id = acl.artifact_id
WHERE acl.tenant_id = '{TENANT_UUID}'
  AND acl.subject_sha256 = '{pull_subject}'
  AND artifact.content_sha256 = '{RESULT_SNAPSHOT_2}'
  AND acl.can_read AND acl.can_manage;
"""
            ).stdout.strip()
            == "1",
            "second_generation_pull_acl_mismatch",
        )
        checks.append("git_and_database_seeded_by_durable_push")

        stage = "pull_exchanges"
        host, port = start_host("pull", 5)
        updated = json.loads(
            pull_exchange(
                port,
                mirror_id=CLEAN_MIRROR,
                generation=1,
                revision_id=revision_one,
                initial_snapshot=RESULT_SNAPSHOT_1,
                state="clean",
            ).stdout
        )
        replay_updated = json.loads(
            pull_exchange(
                port,
                mirror_id=CLEAN_MIRROR,
                generation=1,
                revision_id=revision_one,
                initial_snapshot=RESULT_SNAPSHOT_1,
                state="clean",
            ).stdout
        )
        conflict = json.loads(
            pull_exchange(
                port,
                mirror_id=AHEAD_MIRROR,
                generation=1,
                revision_id=revision_one,
                initial_snapshot=RESULT_SNAPSHOT_1,
                state="ahead",
            ).stdout
        )
        replay_conflict = json.loads(
            pull_exchange(
                port,
                mirror_id=AHEAD_MIRROR,
                generation=1,
                revision_id=revision_one,
                initial_snapshot=RESULT_SNAPSHOT_1,
                state="ahead",
            ).stdout
        )
        unchanged = json.loads(
            pull_exchange(
                port,
                mirror_id=PUSH_MIRROR,
                generation=2,
                revision_id=revision_two,
                initial_snapshot=RESULT_SNAPSHOT_2,
                state="clean",
            ).stdout
        )
        finish_host(host, (5, 0, 0))
        require(
            updated["outcome"] == "updated"
            and updated["phase"] == "clean"
            and updated["observed_generation"] == 2,
            "clean_update_mismatch",
        )
        require(updated == replay_updated, "updated_replay_mismatch")
        require(
            conflict["outcome"] == "conflict"
            and conflict["phase"] == "conflict"
            and conflict["conflict_generation"] == 2
            and conflict["snapshot_preserved"],
            "ahead_conflict_mismatch",
        )
        require(conflict == replay_conflict, "conflict_replay_mismatch")
        require(
            unchanged["outcome"] == "unchanged"
            and unchanged["observed_generation"] == 2,
            "unchanged_mismatch",
        )
        checks.extend(
            [
                "clean_remote_advance_is_atomic",
                "updated_response_replays_without_second_observation",
                "ahead_remote_advance_records_conflict",
                "conflict_preserves_local_snapshot_and_plan",
                "conflict_response_replays_exactly",
                "same_head_same_snapshot_is_unchanged",
            ]
        )

        stage = "database_state"
        state = sql(
            f"""
SELECT
 (SELECT count(*) FROM hwpx_agent.git_mirror_pull_observations) || '|'
 || (SELECT count(*) FROM hwpx_agent.local_mirror_conflicts) || '|'
 || (SELECT state || ':' || observed_generation || ':' || snapshot_sha256 || ':'
       || observed_snapshot_sha256
     FROM hwpx_agent.project_local_mirrors WHERE mirror_id='{CLEAN_MIRROR_UUID}') || '|'
 || (SELECT state || ':' || observed_generation || ':' || snapshot_sha256 || ':'
       || pending_plan_sha256 || ':' || observed_snapshot_sha256
     FROM hwpx_agent.project_local_mirrors WHERE mirror_id='{AHEAD_MIRROR_UUID}');
"""
        ).stdout.strip()
        require(
            state
            == f"3|1|clean:2:{RESULT_SNAPSHOT_2}:{RESULT_SNAPSHOT_2}"
            f"|conflict:1:{LOCAL_SNAPSHOT}:{LOCAL_PLAN}:{RESULT_SNAPSHOT_1}",
            "durable_state_mismatch",
        )
        checks.append("three_immutable_observations_and_one_conflict")

        stage = "immutable_observation"
        require(
            sql(
                "UPDATE hwpx_agent.git_mirror_pull_observations "
                "SET outcome='unchanged' WHERE outcome='updated';",
                expected=False,
            ).returncode
            != 0,
            "observation_mutation_accepted",
        )
        checks.append("terminal_observation_is_immutable")

        stage = "git_database_drift"
        original_oid = invoke(
            [git, "--git-dir", str(bare_repository), "rev-parse", GIT_REF]
        ).stdout.strip()
        drift_state = json.dumps(
            {
                "schema_version": "hwpx-agent.git-mirror-state/v1",
                "project_id": PROJECT,
                "branch_id": BRANCH,
                "revision_id": "rev_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "generation": 3,
                "snapshot_sha256": "b" * 64,
                "operation_plan_sha256": "c" * 64,
                "request_sha256": "d" * 64,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        blob = invoke(
            [git, "--git-dir", str(bare_repository), "hash-object", "-w", "--stdin"],
            data=drift_state.decode("utf-8"),
        ).stdout.strip()
        tree = invoke(
            [git, "--git-dir", str(bare_repository), "mktree", "-z"],
            data=f"100644 blob {blob}\tmirror-state.json\0",
        ).stdout.strip()
        drift_oid = invoke(
            [git, "--git-dir", str(bare_repository), "commit-tree", tree, "-p", original_oid],
            data="drift\n",
            env=dict(
                os.environ,
                GIT_AUTHOR_NAME="pull drift",
                GIT_AUTHOR_EMAIL="pull@invalid",
                GIT_COMMITTER_NAME="pull drift",
                GIT_COMMITTER_EMAIL="pull@invalid",
            ),
        ).stdout.strip()
        invoke(
            [git, "--git-dir", str(bare_repository), "update-ref", GIT_REF, drift_oid, original_oid]
        )
        host, port = start_host("pull", 1)
        failed = pull_exchange(
            port,
            mirror_id=DRIFT_MIRROR,
            generation=1,
            revision_id=revision_one,
            initial_snapshot=RESULT_SNAPSHOT_1,
            state="clean",
            expected=False,
        )
        require(failed.returncode != 0, "git_database_drift_accepted")
        require(
            failed.stderr.strip() == "PROBE_REMOTE_UNAVAILABLE",
            f"git_database_drift_category_mismatch_{failed.stderr.strip()}",
        )
        finish_host(host, (0, 0, 1))
        invoke(
            [git, "--git-dir", str(bare_repository), "update-ref", GIT_REF, original_oid, drift_oid]
        )
        require(
            sql("SELECT count(*) FROM hwpx_agent.git_mirror_pull_observations;")
            .stdout.strip()
            == "3",
            "drift_created_observation",
        )
        checks.append("git_database_drift_is_unavailable_without_mutation")

        stage = "admission_drift"
        sql(f"REVOKE EXECUTE ON FUNCTION {PULL_FUNCTION} FROM {APP_ROLE};")
        reject_pull_host_for_database_drift()
        sql(f"GRANT EXECUTE ON FUNCTION {PULL_FUNCTION} TO {APP_ROLE};")
        sql(f"GRANT EXECUTE ON FUNCTION {PULL_FUNCTION} TO PUBLIC;")
        reject_pull_host_for_database_drift()
        sql(f"REVOKE EXECUTE ON FUNCTION {PULL_FUNCTION} FROM PUBLIC;")
        sql(
            "ALTER TABLE hwpx_agent.git_mirror_pull_observations "
            "DISABLE TRIGGER git_mirror_pull_observation_guard;"
        )
        reject_pull_host_for_database_drift()
        sql(
            "ALTER TABLE hwpx_agent.git_mirror_pull_observations "
            "ENABLE TRIGGER git_mirror_pull_observation_guard;"
        )
        checks.extend(
            [
                "missing_execute_privilege_rejected",
                "public_execute_drift_rejected",
                "observation_trigger_drift_rejected",
            ]
        )

        stage = "retained_rollback"
        require(
            sql(
                "SELECT set_config("
                "'hwpx_agent.allow_p17_durable_git_mirror_pull_rollback','yes',false);\n"
                + down_sql,
                expected=False,
            ).returncode
            != 0,
            "retained_observation_rollback_accepted",
        )
        checks.append("retained_observation_rollback_refused")

        stage = "receipt"
        require(len(checks) == 20 and len(set(checks)) == 20, "check_count_mismatch")
        receipt = {
            "schema_version": "hwpx-agent.p17-durable-git-mirror-pull-run/v1",
            "run_id": run_id,
            "state": "pass",
            "scope": "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
            "checks": checks,
            "check_count": len(checks),
            "postgres": {
                "version": sql("SHOW server_version;").stdout.strip(),
                "image": image,
                "image_id": image_state.get("Id"),
                "loopback_only": True,
            },
            "git": {
                "object_format": invoke(
                    [git, "--git-dir", str(bare_repository), "rev-parse", "--show-object-format"]
                ).stdout.strip(),
                "bare": True,
                "remote_network": False,
            },
            "claims": {
                "authenticated_loopback": True,
                "durable_pull": True,
                "persistent_credential_custody": False,
                "production": False,
                "registered_host": False,
                "secrets_persisted": False,
                "actual_remote_network": False,
                "actual_hangul": False,
                "p17_06_complete": False,
                "product_complete": False,
            },
            "effect": {
                "first_revision_id": revision_one,
                "second_revision_id": revision_two,
                "remote_generation": 2,
                "remote_git_oid": original_oid,
                "observation_count": 3,
                "conflict_count": 1,
                "bounded_state_sha256": hashlib.sha256(
                    state.encode("utf-8")
                ).hexdigest(),
                "updated_response_replayed": updated == replay_updated,
                "conflict_response_replayed": conflict == replay_conflict,
                "local_conflict_state_preserved": conflict["snapshot_preserved"],
            },
            "source_sha256": {
                path.relative_to(ROOT).as_posix(): digest(path) for path in sources
            },
        }
    except (CheckFailure, subprocess.TimeoutExpired, OSError, ValueError) as error:
        failure = f"{stage}:{type(error).__name__}:{error}"
    finally:
        for process in hosts:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
        try:
            inspect = invoke([docker, "inspect", container], expected=False, timeout=15)
            if inspect.returncode == 0:
                if failure is not None:
                    container_log = invoke(
                        [docker, "logs", container], expected=False, timeout=15
                    )
                    safe_categories = re.findall(
                        r"(?:GIT_MIRROR_PULL|MIRROR_OBSERVED_SNAPSHOT)_[A-Z_]+"
                        r"|RETENTION_RESOURCE_NOT_FOUND|P14_09_IDENTITY_IMMUTABLE",
                        container_log.stdout + container_log.stderr,
                    )
                    if safe_categories:
                        failure_category = safe_categories[-1]
                    error_details = re.findall(
                        r"ERROR:\s+([^\r\n]{1,240})",
                        container_log.stdout + container_log.stderr,
                    )
                    if error_details:
                        failure_detail = re.sub(
                            r"[0-9a-f]{8}-[0-9a-f-]{27,35}|[0-9a-f]{32,64}",
                            "<redacted-id>",
                            error_details[-1],
                            flags=re.IGNORECASE,
                        )
                state = json.loads(inspect.stdout)[0]
                if state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id:
                    invoke([docker, "rm", "--force", container], timeout=30)
            volume_inspect = invoke(
                [docker, "volume", "inspect", volume], expected=False, timeout=15
            )
            if volume_inspect.returncode == 0:
                state = json.loads(volume_inspect.stdout)[0]
                if state.get("Labels", {}).get(LABEL) == run_id:
                    invoke([docker, "volume", "rm", volume], timeout=30)
            cleaned = (
                invoke([docker, "inspect", container], expected=False, timeout=10).returncode
                != 0
                and invoke(
                    [docker, "volume", "inspect", volume], expected=False, timeout=10
                ).returncode
                != 0
            )
        except (CheckFailure, subprocess.TimeoutExpired, OSError, ValueError) as error:
            if failure is None:
                failure = f"cleanup:{type(error).__name__}:{error}"
    if failure is not None:
        print(
            "P17_DURABLE_GIT_MIRROR_PULL_FAIL "
            f"{failure} database_category={failure_category or 'not_classified'} "
            f"database_detail={json.dumps(failure_detail or 'not_available')}"
        )
        return 1
    require(cleaned, "owned_resource_cleanup_failed")
    require(receipt is not None, "receipt_missing")
    receipt["resources_cleaned"] = True
    encoded = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")) + "\n"
    require(
        all(
            secret not in encoded
            for secret in [admin_password, app_password, hmac_secret_text, "Bearer "]
        ),
        "secret_in_receipt",
    )
    receipt_path.write_text(encoded, encoding="utf-8", newline="\n")
    print(
        "P17_DURABLE_GIT_MIRROR_PULL_PASS "
        f"checks={len(checks)} receipt={receipt_path.relative_to(ROOT).as_posix()} "
        f"sha256={digest(receipt_path)} cleanup=pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
