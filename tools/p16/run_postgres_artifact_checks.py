"""Real local PostgreSQL + encrypted-blob adapter acceptance, using disposable owned resources."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
LABEL = "hwpx-agent.p16-artifact-adapter-test"
MIGRATIONS = (
    "0001_p14_metadata", "0002_p14_artifact_service", "0003_p14_revision_cas",
    "0004_p14_history_checkpoints", "0005_p14_job_state_machine", "0006_p14_worker_lease_fencing",
    "0007_p14_idempotency_reconciliation", "0008_p14_cancel_cleanup", "0009_p14_retention_local_mirror",
    "0010_p16_artifact_repository",
)


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def loopback_port(state: dict, run_id: str) -> str:
    """Read the current endpoint of this exact owned container, including after a restart."""
    require(state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id, "endpoint_ownership_mismatch")
    bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
    require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port_binding")
    binding = bindings[0]
    require(isinstance(binding, dict) and binding.get("HostIp") == "127.0.0.1", "non_loopback_binding")
    port = binding.get("HostPort")
    require(isinstance(port, str) and re.fullmatch(r"[1-9][0-9]{0,4}", port) is not None
            and int(port) <= 65535, "invalid_port")
    return port


def invoke(command: list[str], *, data: str | None = None, env: dict[str, str] | None = None,
           expected: bool = True, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, input=data, env=env, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if expected and result.returncode != 0:
        # Never print SQL, configuration, process environment or raw backend diagnostics.
        code = re.search(r"P16_POSTGRES_ARTIFACT_PROBE_FAILED code=([A-Z_]+)", result.stderr)
        stages = re.findall(r"^P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=([A-Z_]+)$", result.stderr, re.MULTILINE)
        safe_stages = {"CONFIG", "CONNECT", "SEED_LOOKUP", "SEED_INGEST", "SEED_DOWNLOAD"}
        stage = stages[-1] if stages and stages[-1] in safe_stages else None
        connect_stages = re.findall(r"^P16_POSTGRES_ARTIFACT_CONNECT_FAILED stage=([A-Z_]+)$", result.stderr, re.MULTILINE)
        safe_connect_stages = {"TRANSPORT", "ROLE", "MIGRATIONS", "POLICIES", "PRIVILEGES"}
        connect_stage = connect_stages[-1] if connect_stages and connect_stages[-1] in safe_connect_stages else None
        raise CheckFailure(f"child_failed exit={result.returncode}" + (f" code={code[1]}" if code else "")
                           + (f" probe_stage={stage}" if stage else "")
                           + (f" connect_stage={connect_stage}" if connect_stage else ""))
    return result


def owned(docker: str, kind: str, name: str, run_id: str) -> bool:
    command = [docker, "inspect", name] if kind == "container" else [docker, "volume", "inspect", name]
    result = invoke(command, expected=False)
    if result.returncode != 0:
        return False
    values = json.loads(result.stdout)
    require(isinstance(values, list) and len(values) == 1, "ambiguous_owned_resource")
    labels = values[0].get("Config", {}).get("Labels", {}) if kind == "container" else values[0].get("Labels", {})
    require(labels.get(LABEL) == run_id, "resource_ownership_mismatch")
    return True


def main() -> int:
    docker = shutil.which("docker")
    require(docker is not None, "docker_missing")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p16/postgres-artifacts/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    container = f"hwpx-p16-artifact-{run_id}"
    volume = f"hwpx-p16-artifact-data-{run_id}"
    contract = json.loads((ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json").read_text(encoding="utf-8"))
    image = contract["database"]["container_image"]
    require(re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image) is not None, "unpinned_image")
    invoke([docker, "image", "inspect", image])  # No pull or external installation.
    probe = ROOT / "target/debug/examples" / ("postgres_artifact_probe.exe" if os.name == "nt" else "postgres_artifact_probe")
    require(probe.is_file(), "probe_not_built")
    migration_paths = [ROOT / "migrations/postgres" / f"{name}.up.sql" for name in MIGRATIONS]
    source_paths = migration_paths + [
        ROOT / "migrations/postgres/0010_p16_artifact_repository.down.sql", ROOT / "Cargo.toml", ROOT / "Cargo.lock",
        ROOT / "crates/artifact-service/Cargo.toml", ROOT / "crates/artifact-service/src/store.rs",
        ROOT / "crates/artifact-service/src/store/postgres_repository.rs", ROOT / "crates/artifact-service/src/service.rs",
        ROOT / "crates/artifact-service/src/lib.rs", ROOT / "crates/artifact-service/examples/postgres_artifact_probe.rs",
        Path(__file__), ROOT / "tools/p16/tests/test_postgres_artifact_checks.py",
    ]
    source_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in source_paths}
    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    cleaned = False
    admin_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    child_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)

    def sql(statement: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
        return invoke([docker, "exec", "-i", container, "psql", "-X", "--no-align", "--tuples-only",
                       "--quiet", "--set", "ON_ERROR_STOP=1", "--username", "postgres", "--dbname", "postgres"],
                      data=statement, expected=expected)

    def ready() -> None:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            result = invoke([docker, "exec", container, "pg_isready", "--username", "postgres"], expected=False, timeout=5)
            if result.returncode == 0:
                return
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def up(path: Path) -> None:
        sql(f"SELECT set_config('hwpx_agent.migration_sha256','{digest(path)}',false);\n" + path.read_text(encoding="utf-8"))

    try:
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke([docker, "run", "--detach", "--pull", "never", "--name", container, "--label", f"{LABEL}={run_id}",
                "--publish", "127.0.0.1::5432", "--memory", "512m", "--cpus", "2", "--pids-limit", "128",
                "--mount", f"type=volume,source={volume},target=/var/lib/postgresql", "--env", "POSTGRES_PASSWORD", image],
               env=child_environment)
        ready()
        state = json.loads(invoke([docker, "inspect", container]).stdout)[0]
        port = loopback_port(state, run_id)
        for path in migration_paths:
            stage = path.name
            up(path)
        checks.append("all_ten_migrations_applied")
        stage = "empty_rollback"
        down = (ROOT / "migrations/postgres/0010_p16_artifact_repository.down.sql").read_text(encoding="utf-8")
        history_query = "SELECT version,migration_name,migration_sha256 FROM hwpx_agent.schema_versions WHERE version < 10 ORDER BY version;"
        history_before = sql(history_query).stdout
        require(sql(down, expected=False).returncode != 0, "unguarded_rollback_accepted")
        sql("SELECT set_config('hwpx_agent.allow_p16_artifact_repository_rollback','yes',false);\n" + down)
        require(sql(history_query).stdout == history_before, "predecessor_migration_history_changed")
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "9", "rollback_schema_count_mismatch")
        require(sql("SELECT tgenabled FROM pg_catalog.pg_trigger WHERE tgrelid='hwpx_agent.schema_versions'::regclass AND tgname='schema_versions_immutable';").stdout.strip() == "O", "schema_history_trigger_not_restored")
        sql("""
DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.schema_versions SET migration_name=migration_name WHERE version=9;
        RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='schema history guard unexpectedly disabled';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        NULL;
    END;
END
$$;
""")
        checks.append("rollback_preserves_predecessors_and_restores_immutable_guard")
        up(migration_paths[-1])
        checks.append("guarded_empty_rollback_reapply")
        stage = "least_privilege_role"
        sql(f"""
CREATE ROLE hwpx_p16_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 8 PASSWORD '{app_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_app;
GRANT SELECT ON hwpx_agent.schema_versions TO hwpx_p16_app;
GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts TO hwpx_p16_app;
GRANT SELECT,INSERT,UPDATE,DELETE ON hwpx_agent.artifact_acl TO hwpx_p16_app;
GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit TO hwpx_p16_app;
GRANT USAGE ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq TO hwpx_p16_app;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES ('00000000-0000-0000-0000-000000000001','probe-one'),('00000000-0000-0000-0000-000000000002','probe-two');
""")
        environment = dict(os.environ, HWPX_P16_PG_PORT=port, HWPX_P16_PG_USER="hwpx_p16_app",
                           HWPX_P16_PG_PASSWORD=app_password, HWPX_P16_BLOB_ROOT=str(run_root / "objects"))

        def probe_run(mode: str) -> None:
            result = invoke([str(probe)], env=dict(environment, HWPX_P16_PROBE_MODE=mode), timeout=45)
            require(result.stdout.strip() == f"P16_POSTGRES_ARTIFACT_PROBE_PASS mode={mode}", "probe_marker_mismatch")
            checks.append(f"rust_{mode}")

        for mode in ("seed", "verify"):
            stage = mode
            probe_run(mode)
        stage = "database_restart"
        require(owned(docker,"container",container,run_id),"container_missing_before_restart")
        invoke([docker,"restart",container])
        ready()
        # Docker may assign a new host port to an ephemeral publish on restart. Never reuse
        # a cached endpoint, and never turn this into a retry of a possibly committed operation.
        restarted_port = loopback_port(json.loads(invoke([docker, "inspect", container]).stdout)[0], run_id)
        if restarted_port != port:
            checks.append("restart_ephemeral_port_reassigned")
        environment["HWPX_P16_PG_PORT"] = restarted_port
        checks.append("restart_owned_loopback_endpoint_revalidated")
        probe_run("verify")
        checks.append("postgres_restart_preserves_encrypted_roundtrip")
        stage = "acl_and_quarantine"
        probe_run("acl-quarantine")
        probe_run("verify-quarantine")
        stage = "bypassrls_role_rejected"
        sql("ALTER ROLE hwpx_p16_app BYPASSRLS;")
        probe_run("reject-role")
        sql("ALTER ROLE hwpx_p16_app NOBYPASSRLS;")
        checks.append(stage)
        stage = "disabled_rls_rejected"
        sql("ALTER TABLE hwpx_agent.artifact_acl DISABLE ROW LEVEL SECURITY;")
        probe_run("reject-policies")
        sql("ALTER TABLE hwpx_agent.artifact_acl ENABLE ROW LEVEL SECURITY;")
        checks.append(stage)
        stage = "permissive_policy_rejected"
        sql("ALTER POLICY tenant_isolation ON hwpx_agent.artifact_acl USING (true) WITH CHECK (true);")
        probe_run("reject-policies")
        sql("ALTER POLICY tenant_isolation ON hwpx_agent.artifact_acl USING (tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK (tenant_id=hwpx_agent.current_tenant_id());")
        checks.append(stage)
        stage = "excessive_schema_privileges_rejected"
        sql("GRANT CREATE ON SCHEMA hwpx_agent TO hwpx_p16_app;")
        probe_run("reject-privileges")
        sql("REVOKE CREATE ON SCHEMA hwpx_agent FROM hwpx_p16_app;")
        checks.append(stage)
        stage = "settable_owner_role_rejected"
        sql("""
CREATE ROLE hwpx_p16_owner NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
ALTER TABLE hwpx_agent.artifact_acl OWNER TO hwpx_p16_owner;
GRANT hwpx_p16_owner TO hwpx_p16_app WITH INHERIT FALSE, SET TRUE;
""")
        require(sql("SELECT pg_has_role('hwpx_p16_app','hwpx_p16_owner','USAGE')::int,pg_has_role('hwpx_p16_app','hwpx_p16_owner','SET')::int;").stdout.strip() == "0|1",
                "owner_role_negative_precondition_failed")
        probe_run("reject-policies")
        sql("""
REVOKE hwpx_p16_owner FROM hwpx_p16_app;
ALTER TABLE hwpx_agent.artifact_acl OWNER TO postgres;
DROP ROLE hwpx_p16_owner;
""")
        checks.append(stage)
        stage = "cross_tenant_rls"
        result = sql("BEGIN; SET ROLE hwpx_p16_app; SELECT set_config('hwpx_agent.tenant_id','00000000-0000-0000-0000-000000000002',true); SELECT count(*) FROM hwpx_agent.artifacts; ROLLBACK;")
        require(result.stdout.strip().splitlines()[-1] == "0", "cross_tenant_query_leak")
        checks.append(stage)
        stage = "immutable_ciphertext_metadata"
        result = sql("BEGIN; SET ROLE hwpx_p16_app; SELECT set_config('hwpx_agent.tenant_id','00000000-0000-0000-0000-000000000001',true); UPDATE hwpx_agent.artifacts SET ciphertext_sha256=repeat('0',64); COMMIT;", expected=False)
        require(result.returncode != 0,"ciphertext_metadata_overwrite_accepted")
        checks.append(stage)
        stage = "nonempty_rollback_rejected"
        require(sql("SELECT set_config('hwpx_agent.allow_p16_artifact_repository_rollback','yes',false);\n" + down, expected=False).returncode != 0, "audit_data_removed_by_rollback")
        checks.append(stage)
        stage = "final_readback"
        probe_run("verify-quarantine")
        require(source_hashes == {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in source_paths}, "source_changed_during_acceptance")
    except (CheckFailure, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        failure = str(error) if isinstance(error, CheckFailure) else type(error).__name__
    finally:
        try:
            if owned(docker,"container",container,run_id):
                invoke([docker,"rm","--force","--volumes",container])
            if owned(docker,"volume",volume,run_id):
                invoke([docker,"volume","rm",volume])
            cleaned = not owned(docker,"container",container,run_id) and not owned(docker,"volume",volume,run_id)
        except (CheckFailure, OSError, subprocess.SubprocessError, ValueError) as error:
            failure = failure or f"cleanup_{type(error).__name__}"
    report = {"schema_version":"hwpx-agent.p16-postgres-artifact-acceptance/v1", "run_id":run_id,
              "decision":"PASS" if failure is None and cleaned else "FAIL", "scope":"current_pc_disposable_postgres_only",
              "image":image, "checks":checks, "failed_stage":stage if failure else None,
              "failure":failure, "owned_resources_removed":cleaned, "source_sha256":source_hashes,
              "probe_sha256":digest(probe), "actual_hangul":False, "registered_host":False}
    with (run_root / "report.json").open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,sort_keys=True)
        stream.write("\n")
    print(json.dumps({key:report[key] for key in ("decision","run_id","failed_stage","failure","owned_resources_removed")}))
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
