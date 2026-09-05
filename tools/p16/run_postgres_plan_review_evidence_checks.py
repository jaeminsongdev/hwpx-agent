"""Disposable PostgreSQL acceptance for encrypted P16 plan-review evidence."""
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
LABEL = "hwpx-agent.p16-plan-review-evidence-test"
MIGRATIONS = tuple(f"{number:04d}_{name}" for number, name in (
    (1, "p14_metadata"), (2, "p14_artifact_service"), (3, "p14_revision_cas"),
    (4, "p14_history_checkpoints"), (5, "p14_job_state_machine"),
    (6, "p14_worker_lease_fencing"), (7, "p14_idempotency_reconciliation"),
    (8, "p14_cancel_cleanup"), (9, "p14_retention_local_mirror"),
    (10, "p16_artifact_repository"), (11, "p16_plan_source"),
    (12, "p16_durable_plan_store"), (13, "p16_plan_review_evidence"),
))
TENANT = "00000000-0000-0000-0000-000000000001"
FOREIGN_TENANT = "00000000-0000-0000-0000-000000000002"
PROJECT = "00000000-0000-0000-0000-000000000101"
BRANCH = "00000000-0000-0000-0000-000000000102"
REVISION = "00000000-0000-0000-0000-000000000201"
COMMIT = "00000000-0000-0000-0000-000000000202"
SOURCE_ARTIFACT = "00000000-0000-0000-0000-000000000301"
RESULT_ARTIFACT = "00000000-0000-0000-0000-000000000302"
PLAN = "plan_00000000000000000000000000000301"


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def invoke(command: list[str], *, data: str | None = None, env: dict[str, str] | None = None,
           expected: bool = True, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, input=data, env=env, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if expected and result.returncode != 0:
        safe = re.findall(
            r"^P16_POSTGRES_PLAN_REVIEW_EVIDENCE_PROBE_FAILED category=([A-Za-z_: -]{1,160})$",
            result.stderr, re.MULTILINE)
        category = safe[-1] if safe else None
        raise CheckFailure(f"child_failed exit={result.returncode}"
                           + (f" category={category}" if category else ""))
    return result


def main() -> int:
    docker = shutil.which("docker")
    cargo = shutil.which("cargo")
    require(docker is not None, "docker_missing")
    require(cargo is not None, "cargo_missing")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p16/postgres-plan-review-evidence/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    container = f"hwpx-p16-plan-review-{run_id}"
    volume = f"hwpx-p16-plan-review-data-{run_id}"
    contract = json.loads((ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json")
                          .read_text(encoding="utf-8"))
    image = contract["database"]["container_image"]
    require(re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image) is not None,
            "unpinned_image")
    invoke([docker, "image", "inspect", image])
    invoke([cargo, "build", "--locked", "-p", "mcp-control-plane", "--example",
            "postgres_plan_review_evidence_probe"], timeout=180)
    probe = ROOT / "target/debug/examples" / (
        "postgres_plan_review_evidence_probe.exe" if os.name == "nt"
        else "postgres_plan_review_evidence_probe")
    require(probe.is_file(), "probe_not_built")
    migration_paths = [ROOT / "migrations/postgres" / f"{name}.up.sql" for name in MIGRATIONS]
    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    cleaned = False
    admin_password = secrets.token_urlsafe(32)
    plan_password = secrets.token_urlsafe(32)
    review_password = secrets.token_urlsafe(32)
    plan_key = secrets.token_hex(32)
    evidence_key_v1 = secrets.token_hex(32)
    evidence_key_v2 = secrets.token_hex(32)
    child_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)

    def sql(statement: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
        return invoke([docker, "exec", "-i", container, "psql", "-X", "--no-align",
                       "--tuples-only", "--quiet", "--set", "ON_ERROR_STOP=1",
                       "--username", "postgres", "--dbname", "postgres"], data=statement,
                      expected=expected)

    def ready() -> None:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if invoke([docker, "exec", container, "pg_isready", "--username", "postgres"],
                      expected=False, timeout=5).returncode == 0:
                return
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def port() -> str:
        state = json.loads(invoke([docker, "inspect", container]).stdout)[0]
        require(state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
                "container_ownership_mismatch")
        bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
        require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port")
        binding = bindings[0]
        require(binding.get("HostIp") == "127.0.0.1", "non_loopback_port")
        return binding["HostPort"]

    def up(path: Path) -> None:
        sql(f"SELECT set_config('hwpx_agent.migration_sha256','{digest(path)}',false);\n"
            + path.read_text(encoding="utf-8"))

    def probe_run(mode: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, HWPX_P16_PLAN_REVIEW_MODE=mode,
                           HWPX_P16_PG_PORT=port(), HWPX_P16_PG_DATABASE="postgres",
                           HWPX_P16_PLAN_PG_USER="hwpx_p16_plan_store",
                           HWPX_P16_PLAN_PG_PASSWORD=plan_password,
                           HWPX_P16_REVIEW_PG_USER="hwpx_p16_review_store",
                           HWPX_P16_REVIEW_PG_PASSWORD=review_password,
                           HWPX_P16_PLAN_KEY=plan_key,
                           HWPX_P16_EVIDENCE_KEY_V1=evidence_key_v1,
                           HWPX_P16_EVIDENCE_KEY_V2=evidence_key_v2)
        result = invoke([str(probe)], env=environment, expected=expected, timeout=45)
        if expected:
            require(result.stdout.strip() ==
                    f"P16_POSTGRES_PLAN_REVIEW_EVIDENCE_PROBE_PASS mode={mode}",
                    "probe_marker_mismatch")
            checks.append(f"rust_{mode}")
        return result

    try:
        facts_result = invoke([str(probe)], env=dict(os.environ,
                              HWPX_P16_PLAN_REVIEW_MODE="facts"))
        facts = json.loads(facts_result.stdout)
        owner_sha256 = facts["owner_sha256"]
        graph_sha256 = facts["graph_sha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", owner_sha256) is not None,
                "owner_digest_invalid")
        require(re.fullmatch(r"[0-9a-f]{64}", graph_sha256) is not None,
                "graph_digest_invalid")
        checks.append("product_identity_and_graph_derived")
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke([docker, "run", "--detach", "--pull", "never", "--name", container,
                "--label", f"{LABEL}={run_id}", "--publish", "127.0.0.1::5432",
                "--memory", "512m", "--cpus", "2", "--pids-limit", "128", "--mount",
                f"type=volume,source={volume},target=/var/lib/postgresql", "--env",
                "POSTGRES_PASSWORD", image], env=child_environment)
        ready()
        for path in migration_paths:
            stage = path.name
            up(path)
        require(sql("SELECT count(*) FROM hwpx_agent.schema_versions;").stdout.strip() == "13",
                "migration_count_mismatch")
        checks.append("all_thirteen_migrations_applied")

        stage = "rollback_guard"
        down = (ROOT / "migrations/postgres/0013_p16_plan_review_evidence.down.sql")
        require(sql(down.read_text(encoding="utf-8"), expected=False).returncode != 0,
                "unguarded_rollback_accepted")
        checks.append("rollback_requires_explicit_gate")

        stage = "seed_metadata"
        sql(f"""
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES
 ('{TENANT}','plan-review-one'),('{FOREIGN_TENANT}','plan-review-two');
INSERT INTO hwpx_agent.projects(
 tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id
) VALUES ('{TENANT}','{PROJECT}','synthetic-plan-review','Synthetic Plan Review',
          'hancom-2020','retention.local');
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
 VALUES ('{TENANT}','{PROJECT}','{owner_sha256}','owner');
INSERT INTO hwpx_agent.branches(
 tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT}','{BRANCH}','main',true,'{owner_sha256}');
INSERT INTO hwpx_agent.artifacts(
 tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,storage_state,
 encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation
) VALUES
 ('{TENANT}','{SOURCE_ARTIFACT}',repeat('1',64),128,'application/octet-stream','source','available',
  'kms.synthetic',transaction_timestamp(),1,'source.hwpx',
  'artifacts/v1/00000000000000000000000000000001/source/available/'||repeat('1',64)||'.aes256gcm',
  'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified',
  'scanner.synthetic','probe-v1',1),
 ('{TENANT}','{RESULT_ARTIFACT}',repeat('2',64),128,'application/octet-stream','result','available',
  'kms.synthetic',transaction_timestamp(),1,'result.hwpx',
  'artifacts/v1/00000000000000000000000000000001/result/available/'||repeat('2',64)||'.aes256gcm',
  'AES-256-GCM',decode(repeat('02',12),'hex'),repeat('a',64),repeat('b',64),'verified',
  'scanner.synthetic','probe-v1',1);
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
 VALUES ('{TENANT}','{SOURCE_ARTIFACT}','{owner_sha256}',true,true),
        ('{TENANT}','{RESULT_ARTIFACT}','{owner_sha256}',true,true);
COMMIT;
BEGIN;
ALTER TABLE hwpx_agent.revision_commit_receipts DISABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
SELECT set_config('hwpx_agent.tenant_id','{TENANT}',true);
SELECT set_config('hwpx_agent.subject_sha256','{owner_sha256}',true);
SELECT outcome FROM hwpx_agent.commit_revision_cas(
 '{TENANT}','{PROJECT}','{BRANCH}','{owner_sha256}','{COMMIT}',NULL,0,'{REVISION}',
 ARRAY[]::uuid[],'{SOURCE_ARTIFACT}','{RESULT_ARTIFACT}',NULL,repeat('3',64),'verified',
 repeat('4',64),repeat('6',64),repeat('5',64),repeat('7',64));
ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
COMMIT;
INSERT INTO hwpx_agent.revision_graph_bindings(
 tenant_id,project_id,revision_id,source_artifact_id,graph_sha256,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT}','{REVISION}','{SOURCE_ARTIFACT}',
          '{graph_sha256}','{owner_sha256}');
""")
        checks.append("authorized_source_seeded")

        stage = "least_privilege_role"
        sql(f"""
CREATE ROLE hwpx_p16_plan_store LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
 NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '{plan_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_plan_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_plan_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.purge_expired_compiled_plan_records()
 TO hwpx_p16_plan_store;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.projects,hwpx_agent.branches,
 hwpx_agent.tenants,hwpx_agent.project_acl,hwpx_agent.artifacts,hwpx_agent.revisions,
 hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,
 hwpx_agent.revision_graph_bindings TO hwpx_p16_plan_store;
GRANT SELECT,INSERT ON hwpx_agent.compiled_plan_records TO hwpx_p16_plan_store;
CREATE ROLE hwpx_p16_review_store LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
 NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '{review_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_review_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_review_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.purge_expired_plan_review_evidence_records()
 TO hwpx_p16_review_store;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.compiled_plan_records
 TO hwpx_p16_review_store;
GRANT SELECT,INSERT ON hwpx_agent.plan_review_evidence_records TO hwpx_p16_review_store;
""")
        probe_run("seed")
        ciphertext_only = sql(f"""SELECT count(*) FROM hwpx_agent.plan_review_evidence_records
WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND plan_id='{PLAN}'
AND position(convert_to('hwpx-agent.plan-review-evidence-storage/v1','UTF8') in ciphertext)=0
AND position(convert_to('PRIVATE','UTF8') in ciphertext)=0;""").stdout.strip()
        require(ciphertext_only == "1", "evidence_plaintext_found_or_row_missing")
        checks.append("ciphertext_only_at_rest")
        probe_run("verify")
        probe_run("wrong-key")

        stage = "restart"
        invoke([docker, "restart", container])
        ready()
        probe_run("verify")
        checks.append("database_restart_restore")

        stage = "tamper"
        sql(f"""ALTER TABLE hwpx_agent.plan_review_evidence_records
 DISABLE TRIGGER plan_review_evidence_records_immutable;
UPDATE hwpx_agent.plan_review_evidence_records
 SET ciphertext=set_byte(ciphertext,0,get_byte(ciphertext,0) # 1)
 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND plan_id='{PLAN}';
ALTER TABLE hwpx_agent.plan_review_evidence_records
 ENABLE TRIGGER plan_review_evidence_records_immutable;""")
        probe_run("expect-unavailable")
        sql(f"""ALTER TABLE hwpx_agent.plan_review_evidence_records
 DISABLE TRIGGER plan_review_evidence_records_immutable;
UPDATE hwpx_agent.plan_review_evidence_records
 SET ciphertext=set_byte(ciphertext,0,get_byte(ciphertext,0) # 1)
 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND plan_id='{PLAN}';
ALTER TABLE hwpx_agent.plan_review_evidence_records
 ENABLE TRIGGER plan_review_evidence_records_immutable;""")
        probe_run("verify")
        checks.append("ciphertext_tamper_rejected")

        stage = "aad_tamper"
        sql(f"""ALTER TABLE hwpx_agent.plan_review_evidence_records
 DISABLE TRIGGER plan_review_evidence_records_immutable;
UPDATE hwpx_agent.plan_review_evidence_records SET route_set_sha256=repeat('f',64)
 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND plan_id='{PLAN}';
ALTER TABLE hwpx_agent.plan_review_evidence_records
 ENABLE TRIGGER plan_review_evidence_records_immutable;""")
        probe_run("expect-unavailable")
        checks.append("binding_metadata_tamper_rejected")

        stage = "immutable"
        require(sql(f"UPDATE hwpx_agent.plan_review_evidence_records SET stored_at_unix_seconds=1 "
                    f"WHERE tenant_id='{TENANT}' AND project_id='{PROJECT}' AND plan_id='{PLAN}';",
                    expected=False).returncode != 0, "immutable_update_accepted")
        require(sql(f"DELETE FROM hwpx_agent.plan_review_evidence_records WHERE tenant_id='{TENANT}' "
                    f"AND project_id='{PROJECT}' AND plan_id='{PLAN}';",
                    expected=False).returncode != 0, "immutable_delete_accepted")
        checks.append("create_once_immutability")

        stage = "cross_tenant_rls"
        visible = sql(f"""BEGIN; SET ROLE hwpx_p16_review_store;
SELECT set_config('hwpx_agent.tenant_id','{FOREIGN_TENANT}',true);
SELECT count(*) FROM hwpx_agent.plan_review_evidence_records; ROLLBACK;""")
        require(visible.stdout.strip().splitlines()[-1] == "0", "cross_tenant_evidence_leak")
        checks.append("cross_tenant_rls")

        stage = "admission_drift"
        sql("ALTER ROLE hwpx_p16_review_store BYPASSRLS;")
        require(probe_run("verify", expected=False).returncode != 0, "bypassrls_role_accepted")
        sql("ALTER ROLE hwpx_p16_review_store NOBYPASSRLS;")
        sql("GRANT UPDATE ON hwpx_agent.plan_review_evidence_records TO hwpx_p16_review_store;")
        require(probe_run("verify", expected=False).returncode != 0,
                "evidence_update_privilege_accepted")
        sql("REVOKE UPDATE ON hwpx_agent.plan_review_evidence_records FROM hwpx_p16_review_store;")
        sql("ALTER TABLE hwpx_agent.plan_review_evidence_records DISABLE ROW LEVEL SECURITY;")
        require(probe_run("verify", expected=False).returncode != 0, "missing_rls_accepted")
        sql("ALTER TABLE hwpx_agent.plan_review_evidence_records ENABLE ROW LEVEL SECURITY;")
        checks.append("role_policy_privilege_drift_rejected")

        stage = "evidence_row_blocks_rollback"
        gated_down = ("SELECT set_config('hwpx_agent.allow_p16_plan_review_evidence_rollback',"
                      "'yes',false);\n" + down.read_text(encoding="utf-8"))
        require(sql(gated_down, expected=False).returncode != 0, "nonempty_rollback_accepted")
        checks.append("nonempty_rollback_rejected")
    except Exception as error:  # noqa: BLE001 - bounded receipt below
        failure = f"{type(error).__name__}:{error}"
    finally:
        inspect = invoke([docker, "inspect", container], expected=False)
        if inspect.returncode == 0:
            values = json.loads(inspect.stdout)
            if len(values) == 1 and values[0].get("Config", {}).get("Labels", {}).get(LABEL) == run_id:
                invoke([docker, "rm", "--force", container], expected=False)
        volume_inspect = invoke([docker, "volume", "inspect", volume], expected=False)
        if volume_inspect.returncode == 0:
            values = json.loads(volume_inspect.stdout)
            if len(values) == 1 and values[0].get("Labels", {}).get(LABEL) == run_id:
                invoke([docker, "volume", "rm", volume], expected=False)
        cleaned = (invoke([docker, "inspect", container], expected=False).returncode != 0
                   and invoke([docker, "volume", "inspect", volume], expected=False).returncode != 0)

    receipt = {
        "schema_version": "hwpx-agent.p16-plan-review-evidence-check/v1",
        "run_id": run_id,
        "scope": "current_pc_disposable_postgres_plan_review_evidence_only",
        "passed": failure is None and cleaned,
        "checks": checks,
        "check_count": len(checks),
        "failed_stage": stage if failure else None,
        "failure": failure,
        "resources_cleaned": cleaned,
        "actual_hangul": False,
    }
    (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if not receipt["passed"]:
        print(f"P16_POSTGRES_PLAN_REVIEW_EVIDENCE_CHECK_FAILED stage={stage}")
        return 1
    print(f"P16_POSTGRES_PLAN_REVIEW_EVIDENCE_CHECK_PASS run_id={run_id} checks={len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
