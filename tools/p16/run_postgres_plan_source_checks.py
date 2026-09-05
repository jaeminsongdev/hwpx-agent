"""Disposable PostgreSQL acceptance for the authoritative P16 plan-source adapter."""
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
LABEL = "hwpx-agent.p16-plan-source-test"
MIGRATIONS = (
    "0001_p14_metadata", "0002_p14_artifact_service", "0003_p14_revision_cas",
    "0004_p14_history_checkpoints", "0005_p14_job_state_machine", "0006_p14_worker_lease_fencing",
    "0007_p14_idempotency_reconciliation", "0008_p14_cancel_cleanup", "0009_p14_retention_local_mirror",
    "0010_p16_artifact_repository", "0011_p16_plan_source",
)
TENANT = "00000000-0000-0000-0000-000000000001"
FOREIGN_TENANT = "00000000-0000-0000-0000-000000000002"
PROJECT = "00000000-0000-0000-0000-000000000101"
BRANCH = "00000000-0000-0000-0000-000000000102"
REVISION = "00000000-0000-0000-0000-000000000201"
COMMIT = "00000000-0000-0000-0000-000000000202"
SOURCE_ARTIFACT = "00000000-0000-0000-0000-000000000301"
RESULT_ARTIFACT = "00000000-0000-0000-0000-000000000302"


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def invoke(command: list[str], *, data: str | None = None, env: dict[str, str] | None = None,
           expected: bool = True, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, input=data, env=env, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if expected and result.returncode != 0:
        codes = re.findall(r"^P16_POSTGRES_PLAN_SOURCE_PROBE_FAILED code=([A-Z_]+)$",
                           result.stderr, re.MULTILINE)
        stages = re.findall(r"^P16_POSTGRES_PLAN_SOURCE_CONNECT_FAILED stage=([A-Z_]+)$",
                            result.stderr, re.MULTILINE)
        safe_codes = {"FIXTURE", "ASSERTION", "NOT_FOUND", "ACCESS_DENIED", "STALE_SOURCE",
                      "SOURCE_UNAVAILABLE", "ADAPTER"}
        safe_stages = {"TRANSPORT", "ROLE", "MIGRATIONS", "POLICIES", "PRIVILEGES"}
        code = codes[-1] if codes and codes[-1] in safe_codes else None
        stage = stages[-1] if stages and stages[-1] in safe_stages else None
        raise CheckFailure(f"child_failed exit={result.returncode}"
                           + (f" code={code}" if code else "")
                           + (f" connect_stage={stage}" if stage else ""))
    return result


def loopback_port(state: dict, run_id: str) -> str:
    require(state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
            "endpoint_ownership_mismatch")
    bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
    require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port_binding")
    binding = bindings[0]
    require(isinstance(binding, dict) and binding.get("HostIp") == "127.0.0.1",
            "non_loopback_binding")
    port = binding.get("HostPort")
    require(isinstance(port, str) and re.fullmatch(r"[1-9][0-9]{0,4}", port) is not None
            and int(port) <= 65535, "invalid_port")
    return port


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
    cargo = shutil.which("cargo")
    require(docker is not None, "docker_missing")
    require(cargo is not None, "cargo_missing")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p16/postgres-plan-source/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    container = f"hwpx-p16-plan-source-{run_id}"
    volume = f"hwpx-p16-plan-source-data-{run_id}"
    contract = json.loads((ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json").read_text(encoding="utf-8"))
    image = contract["database"]["container_image"]
    require(re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image) is not None,
            "unpinned_image")
    invoke([docker, "image", "inspect", image])
    invoke([cargo, "build", "--locked", "-p", "mcp-control-plane", "--example",
            "postgres_plan_source_probe"], timeout=180)
    probe = ROOT / "target/debug/examples" / ("postgres_plan_source_probe.exe" if os.name == "nt" else "postgres_plan_source_probe")
    require(probe.is_file(), "probe_not_built")
    migration_paths = [ROOT / "migrations/postgres" / f"{name}.up.sql" for name in MIGRATIONS]
    source_paths = migration_paths + [
        ROOT / "migrations/postgres/0010_p16_artifact_repository.down.sql",
        ROOT / "migrations/postgres/0011_p16_plan_source.down.sql", ROOT / "Cargo.toml", ROOT / "Cargo.lock",
        ROOT / "crates/mcp-control-plane/Cargo.toml", ROOT / "crates/mcp-control-plane/src/lib.rs",
        ROOT / "crates/mcp-control-plane/src/stored_plan.rs",
        ROOT / "crates/mcp-control-plane/src/postgres_plan_source.rs",
        ROOT / "crates/mcp-control-plane/examples/postgres_plan_source_probe.rs", Path(__file__),
        ROOT / "tools/p16/tests/test_postgres_plan_source_checks.py",
    ]
    source_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path)
                     for path in source_paths}
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
            result = invoke([docker, "exec", container, "pg_isready", "--username", "postgres"],
                            expected=False, timeout=5)
            if result.returncode == 0:
                return
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def up(path: Path) -> None:
        sql(f"SELECT set_config('hwpx_agent.migration_sha256','{digest(path)}',false);\n"
            + path.read_text(encoding="utf-8"))

    def probe_run(mode: str, endpoint: str, check_name: str | None = None) -> None:
        environment = dict(os.environ, HWPX_P16_PLAN_SOURCE_MODE=mode,
                           HWPX_P16_PG_PORT=endpoint, HWPX_P16_PG_USER="hwpx_p16_plan_reader",
                           HWPX_P16_PG_PASSWORD=app_password)
        result = invoke([str(probe)], env=environment, timeout=45)
        require(result.stdout.strip() == f"P16_POSTGRES_PLAN_SOURCE_PROBE_PASS mode={mode}",
                "probe_marker_mismatch")
        checks.append(check_name or f"rust_{mode}")

    try:
        identity = invoke([str(probe)], env=dict(os.environ, HWPX_P16_PLAN_SOURCE_MODE="identity"))
        match = re.fullmatch(
            r"P16_POSTGRES_PLAN_SOURCE_IDENTITY subject_sha256=([0-9a-f]{64}) graph_sha256=([0-9a-f]{64})\s*",
            identity.stdout,
        )
        require(match is not None, "identity_marker_mismatch")
        subject_sha256, graph_sha256 = match.groups()
        checks.append("synthetic_identity_derived_by_product_code")
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke([docker, "run", "--detach", "--pull", "never", "--name", container,
                "--label", f"{LABEL}={run_id}", "--publish", "127.0.0.1::5432", "--memory", "512m",
                "--cpus", "2", "--pids-limit", "128",
                "--mount", f"type=volume,source={volume},target=/var/lib/postgresql",
                "--env", "POSTGRES_PASSWORD", image], env=child_environment)
        ready()
        port = loopback_port(json.loads(invoke([docker, "inspect", container]).stdout)[0], run_id)
        for path in migration_paths:
            stage = path.name
            up(path)
        checks.append("all_eleven_migrations_applied")

        stage = "empty_v11_rollback"
        down = (ROOT / "migrations/postgres/0011_p16_plan_source.down.sql").read_text(encoding="utf-8")
        history_query = "SELECT version,migration_name,migration_sha256 FROM hwpx_agent.schema_versions WHERE version < 11 ORDER BY version;"
        history_before = sql(history_query).stdout
        require(sql(down, expected=False).returncode != 0, "unguarded_rollback_accepted")
        sql("SELECT set_config('hwpx_agent.allow_p16_plan_source_rollback','yes',false);\n" + down)
        require(sql(history_query).stdout == history_before, "predecessor_migration_history_changed")
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "10",
                "rollback_schema_count_mismatch")
        up(migration_paths[-1])
        checks.append("guarded_empty_v11_rollback_reapply")

        stage = "seed_metadata"
        source_content = "1" * 64
        result_content = "2" * 64
        operation_plan = "3" * 64
        validation_summary = "4" * 64
        commit_request = "5" * 64
        transaction_receipt = "6" * 64
        commit_receipt = "7" * 64
        sql(f"""
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES
    ('{TENANT}','plan-source-one'),('{FOREIGN_TENANT}','plan-source-two');
INSERT INTO hwpx_agent.projects(
    tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id
) VALUES ('{TENANT}','{PROJECT}','synthetic-plan','Synthetic Plan','hancom-2020','retention.local');
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
VALUES ('{TENANT}','{PROJECT}','{subject_sha256}','owner');
INSERT INTO hwpx_agent.branches(
    tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT}','{BRANCH}','main',true,'{subject_sha256}');
INSERT INTO hwpx_agent.artifacts(
    tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,storage_state,
    encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
    encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
    scanner_engine_ref,scanner_signature_version,authorization_generation
) VALUES
    ('{TENANT}','{SOURCE_ARTIFACT}','{source_content}',128,'application/octet-stream','source','available',
     'kms.synthetic',transaction_timestamp(),1,'source.hwpx',
     'artifacts/v1/00000000000000000000000000000001/source/available/{source_content}.aes256gcm',
     'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified',
     'scanner.synthetic','probe-v1',1),
    ('{TENANT}','{RESULT_ARTIFACT}','{result_content}',128,'application/octet-stream','result','available',
     'kms.synthetic',transaction_timestamp(),1,'result.hwpx',
     'artifacts/v1/00000000000000000000000000000001/result/available/{result_content}.aes256gcm',
     'AES-256-GCM',decode(repeat('02',12),'hex'),repeat('a',64),repeat('b',64),'verified',
     'scanner.synthetic','probe-v1',1);
INSERT INTO hwpx_agent.artifact_acl(
    tenant_id,artifact_id,subject_sha256,can_read,can_manage
) VALUES
    ('{TENANT}','{SOURCE_ARTIFACT}','{subject_sha256}',true,true),
    ('{TENANT}','{RESULT_ARTIFACT}','{subject_sha256}',true,true);
COMMIT;
""")
        stage = "seed_revision_cas"
        sql(f"""
BEGIN;
ALTER TABLE hwpx_agent.revision_commit_receipts
    DISABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
SELECT set_config('hwpx_agent.tenant_id','{TENANT}',true);
SELECT set_config('hwpx_agent.subject_sha256','{subject_sha256}',true);
SELECT outcome FROM hwpx_agent.commit_revision_cas(
    '{TENANT}','{PROJECT}','{BRANCH}','{subject_sha256}','{COMMIT}',NULL,0,'{REVISION}',ARRAY[]::uuid[],
    '{SOURCE_ARTIFACT}','{RESULT_ARTIFACT}',NULL,'{operation_plan}','verified','{validation_summary}',
    '{transaction_receipt}','{commit_request}','{commit_receipt}'
);
ALTER TABLE hwpx_agent.revision_commit_receipts
    ENABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
COMMIT;
""")
        stage = "seed_graph_binding"
        sql(f"""
INSERT INTO hwpx_agent.revision_graph_bindings(
    tenant_id,project_id,revision_id,source_artifact_id,graph_sha256,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT}','{REVISION}','{SOURCE_ARTIFACT}','{graph_sha256}','{subject_sha256}');
""")
        checks.append("service_revision_receipt_and_graph_binding_seeded")
        stage = "binding_creator_mismatch"
        require(sql(f"""INSERT INTO hwpx_agent.revision_graph_bindings(
tenant_id,project_id,revision_id,source_artifact_id,graph_sha256,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT}','{REVISION}','{SOURCE_ARTIFACT}','{graph_sha256}',repeat('d',64));""",
                    expected=False).returncode != 0, "binding_creator_mismatch_accepted")
        checks.append(stage)

        stage = "least_privilege_role"
        sql(f"""
CREATE ROLE hwpx_p16_plan_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION
    CONNECTION LIMIT 8 PASSWORD '{app_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_plan_reader;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_plan_reader;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.projects,hwpx_agent.branches,
    hwpx_agent.tenants,hwpx_agent.project_acl,hwpx_agent.artifacts,hwpx_agent.revisions,
    hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,
    hwpx_agent.revision_graph_bindings TO hwpx_p16_plan_reader;
""")
        probe_run("verify", port)
        probe_run("expect-stale", port)

        stage = "restart"
        require(owned(docker, "container", container, run_id), "container_missing_before_restart")
        invoke([docker, "restart", container])
        ready()
        restarted_port = loopback_port(json.loads(invoke([docker, "inspect", container]).stdout)[0], run_id)
        checks.append("restart_owned_loopback_endpoint_revalidated")
        probe_run("verify", restarted_port)
        checks.append("postgres_restart_preserves_authoritative_source")
        port = restarted_port

        stage = "non_member_hidden"
        sql(f"DELETE FROM hwpx_agent.project_acl WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND subject_sha256='{subject_sha256}';")
        probe_run("expect-not-found", port)
        sql(f"INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role) VALUES ('{TENANT}','{PROJECT}','{subject_sha256}','owner');")
        stage = "suspended_tenant_hidden"
        sql(f"UPDATE hwpx_agent.tenants SET state='suspended' WHERE tenant_id='{TENANT}';")
        probe_run("expect-not-found", port)
        sql(f"UPDATE hwpx_agent.tenants SET state='active' WHERE tenant_id='{TENANT}';")
        stage = "cross_tenant_rls"
        visible = sql(f"BEGIN; SET ROLE hwpx_p16_plan_reader; SELECT set_config('hwpx_agent.tenant_id','{FOREIGN_TENANT}',true); SELECT count(*) FROM hwpx_agent.projects; ROLLBACK;")
        require(visible.stdout.strip().splitlines()[-1] == "0", "cross_tenant_project_leak")
        checks.append(stage)

        stage = "source_quarantine"
        sql(f"""UPDATE hwpx_agent.artifacts SET storage_state='quarantined',validation_state='quarantined',
quarantine_reason_code='TEST_QUARANTINE',authorization_generation=authorization_generation+1,
object_key=replace(object_key,'/available/','/quarantined/')
WHERE tenant_id='{TENANT}' AND artifact_id='{SOURCE_ARTIFACT}';""")
        probe_run("expect-source-unavailable", port)
        sql(f"""UPDATE hwpx_agent.artifacts SET storage_state='available',validation_state='verified',
quarantine_reason_code=NULL,authorization_generation=authorization_generation+1,
object_key=replace(object_key,'/quarantined/','/available/')
WHERE tenant_id='{TENANT}' AND artifact_id='{SOURCE_ARTIFACT}';""")
        probe_run("verify", port)

        stage = "head_and_project_drift"
        sql(f"UPDATE hwpx_agent.projects SET state='archived' WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}';")
        probe_run("expect-not-found", port)
        sql(f"UPDATE hwpx_agent.projects SET state='active',head_generation=2 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}';")
        probe_run("expect-not-found", port)
        sql(f"UPDATE hwpx_agent.projects SET head_generation=1 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}';")
        probe_run("verify", port)

        stage = "role_rejected"
        sql("ALTER ROLE hwpx_p16_plan_reader BYPASSRLS;")
        probe_run("reject-role", port, "bypass_rls_role_rejected")
        sql("ALTER ROLE hwpx_p16_plan_reader NOBYPASSRLS;")
        stage = "replication_role_rejected"
        sql("ALTER ROLE hwpx_p16_plan_reader REPLICATION;")
        probe_run("reject-role", port, "replication_role_rejected")
        sql("ALTER ROLE hwpx_p16_plan_reader NOREPLICATION;")
        stage = "disabled_rls_rejected"
        sql("ALTER TABLE hwpx_agent.revision_commit_receipts DISABLE ROW LEVEL SECURITY;")
        probe_run("reject-policies", port)
        sql("ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE ROW LEVEL SECURITY;")
        stage = "mutated_policy_rejected"
        sql("ALTER POLICY tenant_isolation ON hwpx_agent.revision_graph_bindings USING (true) WITH CHECK (true);")
        probe_run("reject-policies", port)
        sql("ALTER POLICY tenant_isolation ON hwpx_agent.revision_graph_bindings USING (tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK (tenant_id=hwpx_agent.current_tenant_id());")
        stage = "excessive_privilege_rejected"
        sql("GRANT UPDATE ON hwpx_agent.artifacts TO hwpx_p16_plan_reader;")
        probe_run("reject-privileges", port)
        sql("REVOKE UPDATE ON hwpx_agent.artifacts FROM hwpx_p16_plan_reader;")
        stage = "missing_function_privilege_rejected"
        sql("REVOKE EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() FROM hwpx_p16_plan_reader;")
        probe_run("reject-privileges", port)
        sql("GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_plan_reader;")

        stage = "settable_owner_rejected"
        sql("""
CREATE ROLE hwpx_p16_plan_owner NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;
ALTER TABLE hwpx_agent.revision_graph_bindings OWNER TO hwpx_p16_plan_owner;
GRANT hwpx_p16_plan_owner TO hwpx_p16_plan_reader WITH INHERIT FALSE, SET TRUE;
""")
        probe_run("reject-policies", port)
        sql("""
REVOKE hwpx_p16_plan_owner FROM hwpx_p16_plan_reader;
ALTER TABLE hwpx_agent.revision_graph_bindings OWNER TO postgres;
DROP ROLE hwpx_p16_plan_owner;
""")

        stage = "migration_digest_drift_rejected"
        expected_v11_digest = digest(migration_paths[-1])
        sql("ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            "UPDATE hwpx_agent.schema_versions SET migration_sha256=repeat('f',64) WHERE version=11;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;")
        probe_run("reject-migrations", port)
        sql("ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;"
            f"UPDATE hwpx_agent.schema_versions SET migration_sha256='{expected_v11_digest}' WHERE version=11;"
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;")

        stage = "binding_immutable"
        require(sql(f"UPDATE hwpx_agent.revision_graph_bindings SET graph_sha256=repeat('e',64) WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}';", expected=False).returncode != 0,
                "binding_update_accepted")
        require(sql(f"DELETE FROM hwpx_agent.revision_graph_bindings WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}';", expected=False).returncode != 0,
                "binding_delete_accepted")
        checks.append(stage)

        stage = "nonempty_rollback_rejected"
        require(sql("SELECT set_config('hwpx_agent.allow_p16_plan_source_rollback','yes',false);\n" + down,
                    expected=False).returncode != 0, "nonempty_rollback_accepted")
        checks.append(stage)
        probe_run("verify", port)
        require(source_hashes == {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path)
                                  for path in source_paths}, "source_changed_during_acceptance")
    except (CheckFailure, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        failure = str(error) if isinstance(error, CheckFailure) else type(error).__name__
    finally:
        try:
            if owned(docker, "container", container, run_id):
                invoke([docker, "rm", "--force", "--volumes", container])
            if owned(docker, "volume", volume, run_id):
                invoke([docker, "volume", "rm", volume])
            cleaned = not owned(docker, "container", container, run_id) and not owned(docker, "volume", volume, run_id)
        except (CheckFailure, OSError, subprocess.SubprocessError, ValueError) as error:
            failure = failure or f"cleanup_{type(error).__name__}"
    report = {
        "schema_version": "hwpx-agent.p16-postgres-plan-source-acceptance/v1", "run_id": run_id,
        "decision": "PASS" if failure is None and cleaned else "FAIL",
        "scope": "current_pc_disposable_postgres_plan_source_only", "image": image, "checks": checks,
        "failed_stage": stage if failure else None, "failure": failure,
        "owned_resources_removed": cleaned, "source_sha256": source_hashes,
        "probe_sha256": digest(probe), "actual_hangul": False, "registered_host": False,
        "durable_plan_store": False, "actual_renderer": False,
    }
    with (run_root / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in (
        "decision", "run_id", "failed_stage", "failure", "owned_resources_removed")}, sort_keys=True))
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
