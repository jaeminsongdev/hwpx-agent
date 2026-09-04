from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "implementation" / "p14" / "postgres" / "p14-revision-cas-v1.json"
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_postgres_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-revision-test"
LEGACY_TENANT_ID = "b1000000-0000-0000-0000-000000000001"
RACE_TENANT_ID = "a1000000-0000-0000-0000-000000000001"
RACE_PROJECT_ID = "a2000000-0000-0000-0000-000000000001"
RACE_BRANCH_ID = "a3000000-0000-0000-0000-000000000002"
RACE_BASE_REVISION_ID = "a5000000-0000-0000-0000-000000000004"


class HarnessError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise HarnessError(message)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_contract_document(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        fail("revision CAS contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_revision_cas_migration.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_revision_cas_migration", module_path
    )
    if specification is None or specification.loader is None:
        fail("revision CAS migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("revision CAS migration contract did not validate")
    return validated


def inspect_owned_container(docker: str, container: str, run_id: str) -> bool:
    result = SUPPORT.run(docker, ["inspect", container], check=False)
    if result.returncode != 0:
        return False
    document = json.loads(result.stdout)
    if not isinstance(document, list) or len(document) != 1:
        fail("Docker returned an ambiguous container inspection result")
    labels = document[0].get("Config", {}).get("Labels", {})
    if not isinstance(labels, dict) or labels.get(LABEL_KEY) != run_id:
        fail("refusing to remove a container without the exact owned-run label")
    return True


def assert_version_state(docker: str, container: str, expected: str) -> None:
    versions = SUPPORT.scalar(
        docker,
        container,
        "SELECT string_agg(version::text, ',' ORDER BY version) "
        "FROM hwpx_agent.schema_versions;\n",
    )
    if versions != expected:
        fail(f"schema version set differs: expected {expected}, got {versions}")


def seed_legacy_revision(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        f"""
BEGIN;
INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES ('{LEGACY_TENANT_ID}', 'legacy-revision');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    '{LEGACY_TENANT_ID}', 'b2000000-0000-0000-0000-000000000001',
    'legacy-revision-project', 'Legacy Revision', 'hancom-hangul-2020-secondary',
    'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role)
VALUES (
    '{LEGACY_TENANT_ID}', 'b2000000-0000-0000-0000-000000000001',
    repeat('b', 64), 'owner'
);
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version, authorization_generation
) VALUES
    (
        '{LEGACY_TENANT_ID}', 'b4000000-0000-0000-0000-000000000001', repeat('1', 64), 1,
        'application/octet-stream', 'source', 'available', 'kms.legacy-revision',
        transaction_timestamp(), 1, 'legacy-source.bin',
        'artifacts/v1/b1000000000000000000000000000001/source/available/' ||
            repeat('1', 64) || '.aes256gcm',
        'AES-256-GCM', decode(repeat('01', 12), 'hex'), repeat('2', 64), repeat('3', 64),
        'verified', 'scanner.legacy-revision', 'v1', 1
    ),
    (
        '{LEGACY_TENANT_ID}', 'b4000000-0000-0000-0000-000000000002', repeat('4', 64), 1,
        'application/octet-stream', 'result', 'available', 'kms.legacy-revision',
        transaction_timestamp(), 1, 'legacy-result.bin',
        'artifacts/v1/b1000000000000000000000000000001/result/available/' ||
            repeat('4', 64) || '.aes256gcm',
        'AES-256-GCM', decode(repeat('02', 12), 'hex'), repeat('5', 64), repeat('6', 64),
        'verified', 'scanner.legacy-revision', 'v1', 1
    );
INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT '{LEGACY_TENANT_ID}', artifact_id, repeat('b', 64), true, true
FROM hwpx_agent.artifacts WHERE tenant_id = '{LEGACY_TENANT_ID}';
INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
    operation_plan_sha256, validation_state, validation_summary_sha256,
    created_by_subject_sha256
) VALUES (
    '{LEGACY_TENANT_ID}', 'b2000000-0000-0000-0000-000000000001',
    'b5000000-0000-0000-0000-000000000001',
    'b4000000-0000-0000-0000-000000000001',
    'b4000000-0000-0000-0000-000000000002',
    repeat('7', 64), 'verified', repeat('8', 64), repeat('b', 64)
);
UPDATE hwpx_agent.projects
SET head_revision_id = 'b5000000-0000-0000-0000-000000000001'
WHERE tenant_id = '{LEGACY_TENANT_ID}'
  AND project_id = 'b2000000-0000-0000-0000-000000000001';
INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, head_revision_id, is_default,
    created_by_subject_sha256
) VALUES (
    '{LEGACY_TENANT_ID}', 'b2000000-0000-0000-0000-000000000001',
    'b3000000-0000-0000-0000-000000000001', 'main',
    'b5000000-0000-0000-0000-000000000001', true, repeat('b', 64)
);
COMMIT;
""",
    )


def assert_legacy_heads_fail_closed(docker: str, container: str) -> None:
    value = SUPPORT.scalar(
        docker,
        container,
        f"""
SELECT count(*)
FROM hwpx_agent.projects AS project
JOIN hwpx_agent.branches AS branch
  ON branch.tenant_id = project.tenant_id
 AND branch.project_id = project.project_id
JOIN hwpx_agent.revision_graph_seals AS seal
  ON seal.tenant_id = project.tenant_id
 AND seal.project_id = project.project_id
 AND seal.revision_id = project.head_revision_id
WHERE project.tenant_id = '{LEGACY_TENANT_ID}'
  AND project.head_generation = -1
  AND branch.head_generation = -1
  AND seal.seal_kind = 'legacy_unqualified'
  AND seal.committed_generation IS NULL;
""",
    )
    if value != "1":
        fail(f"legacy revision head was not forced unqualified: {value}")


def race_sql(candidate: int, *, hold_lock: bool) -> str:
    artifact_start = 13 if candidate == 5 else 16
    prefix = ""
    if hold_lock:
        prefix = f"""
SELECT head_generation FROM hwpx_agent.branches
WHERE tenant_id = '{RACE_TENANT_ID}'
  AND project_id = '{RACE_PROJECT_ID}'
  AND branch_id = '{RACE_BRANCH_ID}'
FOR UPDATE;
SELECT pg_advisory_xact_lock(1403);
SELECT pg_sleep(2);
"""
    role = "" if hold_lock else "SET LOCAL ROLE hwpx_agent_revision_test_app;\n"
    return f"""
BEGIN;
{role}SELECT set_config('hwpx_agent.tenant_id', '{RACE_TENANT_ID}', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
{prefix}SELECT * FROM hwpx_agent.commit_revision_cas(
    '{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', '{RACE_BRANCH_ID}', repeat('a', 64),
    'a6000000-0000-0000-0000-{candidate:012d}', '{RACE_BASE_REVISION_ID}', 1,
    'a5000000-0000-0000-0000-{candidate:012d}', ARRAY['{RACE_BASE_REVISION_ID}']::uuid[],
    'a4000000-0000-0000-0000-{artifact_start:012d}',
    'a4000000-0000-0000-0000-{artifact_start + 1:012d}',
    'a4000000-0000-0000-0000-{artifact_start + 2:012d}',
    lpad(to_hex({candidate} + 300), 64, '0'), 'verified',
    lpad(to_hex({candidate} + 400), 64, '0'),
    lpad(to_hex({candidate} + 500), 64, '0'),
    lpad(to_hex({candidate} + 600), 64, '0'),
    lpad(to_hex({candidate} + 700), 64, '0')
);
COMMIT;
"""


def run_race(docker: str, container: str) -> dict[str, object]:
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        holder = executor.submit(
            SUPPORT.psql, docker, container, race_sql(5, hold_lock=True), timeout=30
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            lock_count = SUPPORT.scalar(
                docker,
                container,
                "SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND granted;\n",
            )
            if lock_count == "1":
                break
            time.sleep(0.05)
        else:
            fail("race holder did not publish its lock before the contender started")
        contender_started = time.monotonic()
        contender = executor.submit(
            SUPPORT.psql, docker, container, race_sql(6, hold_lock=False), timeout=30
        )
        holder_result = holder.result(timeout=35)
        contender_result = contender.result(timeout=35)
        contender_seconds = time.monotonic() - contender_started
    elapsed = time.monotonic() - started

    committed_pattern = re.compile(r"(?m)^committed\|.*\|2\|.*\|2\|")
    conflict_pattern = re.compile(r"(?m)^conflict\|.*\|2\|\|\|$")
    outputs = [holder_result.stdout, contender_result.stdout]
    committed = sum(bool(committed_pattern.search(output)) for output in outputs)
    conflicted = sum(bool(conflict_pattern.search(output)) for output in outputs)
    if committed != 1 or conflicted != 1:
        fail(f"concurrent CAS outcomes differ: committed={committed} conflict={conflicted}")
    if contender_seconds < 1.0:
        fail(f"contender did not wait on the held branch row: {contender_seconds:.3f}s")

    winner_count = SUPPORT.scalar(
        docker,
        container,
        f"""
SELECT count(*)
FROM hwpx_agent.revisions
WHERE tenant_id = '{RACE_TENANT_ID}'
  AND project_id = '{RACE_PROJECT_ID}'
  AND revision_id IN (
      'a5000000-0000-0000-0000-000000000005',
      'a5000000-0000-0000-0000-000000000006'
  );
""",
    )
    loser_count = SUPPORT.scalar(
        docker,
        container,
        f"""
SELECT count(*)
FROM hwpx_agent.revision_commit_receipts
WHERE tenant_id = '{RACE_TENANT_ID}'
  AND project_id = '{RACE_PROJECT_ID}'
  AND commit_id IN (
      'a6000000-0000-0000-0000-000000000005',
      'a6000000-0000-0000-0000-000000000006'
  );
""",
    )
    head_generation = SUPPORT.scalar(
        docker,
        container,
        f"""
SELECT head_generation FROM hwpx_agent.branches
WHERE tenant_id = '{RACE_TENANT_ID}'
  AND project_id = '{RACE_PROJECT_ID}'
  AND branch_id = '{RACE_BRANCH_ID}';
""",
    )
    if winner_count != "1" or loser_count != "1" or head_generation != "2":
        fail(
            "concurrent CAS persistence differs: "
            f"nodes={winner_count} receipts={loser_count} generation={head_generation}"
        )
    return {
        "committed": committed,
        "conflicted": conflicted,
        "contender_wait_seconds": round(contender_seconds, 3),
        "elapsed_seconds": round(elapsed, 3),
    }


def assert_version_3_removed(docker: str, container: str) -> None:
    table_count = SUPPORT.scalar(
        docker,
        container,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='hwpx_agent' "
        "AND table_name IN ('revision_graph_seals','revision_commit_receipts');\n",
    )
    column_count = SUPPORT.scalar(
        docker,
        container,
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='hwpx_agent' AND column_name='head_generation' "
        "AND table_name IN ('projects','branches');\n",
    )
    if table_count != "0" or column_count != "0":
        fail(f"version 3 rollback left objects: tables={table_count} columns={column_count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--allow-pull", action="store_true")
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docker = shutil.which("docker")
    if docker is None:
        fail("docker executable is unavailable")
    validated = validate_contract(args.contract)
    contract = load_contract_document(args.contract.resolve())
    image = str(validated["container_image"])
    prerequisites = contract["prerequisites"]
    migration = contract["migration"]
    smoke = contract["smoke_fixture"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 2:
        fail("validated prerequisite shape differs")
    if not isinstance(migration, dict) or not isinstance(smoke, dict):
        fail("validated contract sections have unexpected shapes")

    prerequisite_sql: list[tuple[str, str, str]] = []
    for value in prerequisites:
        if not isinstance(value, dict):
            fail("validated prerequisite entry differs")
        prerequisite_sql.append(
            (
                SUPPORT.load_bounded_text(ROOT / str(value["up_path"]), 256 * 1024),
                SUPPORT.load_bounded_text(ROOT / str(value["down_path"]), 128 * 1024),
                str(value["up_sha256"]),
            )
        )
    up3 = SUPPORT.load_bounded_text(ROOT / str(migration["up_path"]), 256 * 1024)
    down3 = SUPPORT.load_bounded_text(ROOT / str(migration["down_path"]), 128 * 1024)
    smoke_sql = SUPPORT.load_bounded_text(ROOT / str(smoke["path"]), 256 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = SUPPORT.git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(Path(__file__).with_name("validate_revision_cas_migration.py"))
    support_digest = sha256(SUPPORT_PATH)
    contract_digest = sha256(args.contract.resolve())
    inspected_image = SUPPORT.ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-rev-{run_id.replace('-', '')[:12]}"
    cleanup_verified = False
    primary_error: BaseException | None = None
    receipt: dict[str, object] = {}
    try:
        SUPPORT.run(
            docker,
            [
                "run",
                "--detach",
                "--name",
                container,
                "--label",
                f"{LABEL_KEY}={run_id}",
                "--network",
                "none",
                "--env",
                "POSTGRES_HOST_AUTH_METHOD=trust",
                image,
            ],
            timeout=120,
        )
        SUPPORT.wait_until_ready(docker, container)
        version = SUPPORT.scalar(docker, container, "SHOW server_version;\n")
        if not version.startswith("18.4"):
            fail(f"unexpected PostgreSQL server version: {version}")

        SUPPORT.apply_up(docker, container, prerequisite_sql[0][0], prerequisite_sql[0][2])
        SUPPORT.apply_up(docker, container, prerequisite_sql[1][0], prerequisite_sql[1][2])
        seed_legacy_revision(docker, container)
        SUPPORT.apply_up(docker, container, up3, str(migration["up_sha256"]))
        assert_legacy_heads_fail_closed(docker, container)
        assert_version_state(docker, container, "1,2,3")
        first_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in first_smoke.stdout:
            fail("first revision CAS smoke did not emit its exact pass marker")
        first_race = run_race(docker, container)

        refused = SUPPORT.apply_down(docker, container, down3, explicitly_allowed=False)
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 3 rollback without the destructive gate was not refused")
        assert_version_state(docker, container, "1,2,3")

        SUPPORT.apply_down(docker, container, down3, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2")
        assert_version_3_removed(docker, container)
        SUPPORT.apply_down(docker, container, prerequisite_sql[1][1], explicitly_allowed=True)
        SUPPORT.apply_down(docker, container, prerequisite_sql[0][1], explicitly_allowed=True)

        SUPPORT.apply_up(docker, container, prerequisite_sql[0][0], prerequisite_sql[0][2])
        SUPPORT.apply_up(docker, container, prerequisite_sql[1][0], prerequisite_sql[1][2])
        seed_legacy_revision(docker, container)
        SUPPORT.apply_up(docker, container, up3, str(migration["up_sha256"]))
        assert_legacy_heads_fail_closed(docker, container)
        second_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied revision CAS smoke did not emit its exact pass marker")
        second_race = run_race(docker, container)
        SUPPORT.apply_down(docker, container, down3, explicitly_allowed=True)
        assert_version_3_removed(docker, container)
        SUPPORT.apply_down(docker, container, prerequisite_sql[1][1], explicitly_allowed=True)
        SUPPORT.apply_down(docker, container, prerequisite_sql[0][1], explicitly_allowed=True)
        schema_count = SUPPORT.scalar(
            docker,
            container,
            "SELECT count(*) FROM pg_namespace WHERE nspname='hwpx_agent';\n",
        )
        if schema_count != "0":
            fail("final rollback left the metadata schema present")

        receipt = {
            "schema_version": "hwpx-agent.p14-03-postgres-revision-cas-audit/v1",
            "state": "pass",
            "recorded_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_tree_clean_before_run": source_tree_clean,
            "migration_contract_sha256": contract_digest,
            "validator_sha256": validator_digest,
            "test_harness_sha256": harness_digest,
            "postgres_support_sha256": support_digest,
            "image": image,
            "image_id": inspected_image.get("Id"),
            "postgres_server_version": version,
            "prerequisite_up_sha256": [value[2] for value in prerequisite_sql],
            "up_migration_sha256": migration["up_sha256"],
            "down_migration_sha256": migration["down_sha256"],
            "smoke_fixture_sha256": smoke["sha256"],
            "assertion_count_per_run": smoke["assertions_per_run"],
            "migration_apply_count": 2,
            "smoke_run_count": 2,
            "concurrent_race_run_count": 2,
            "first_race": first_race,
            "second_race": second_race,
            "legacy_head_fail_closed_exercised": True,
            "cross_tenant_denial_exercised": True,
            "authorization_denial_exercised": True,
            "sealed_dag_exercised": True,
            "stale_conflict_side_effect_free": True,
            "rollback_without_gate_refused": True,
            "version_2_preserved_after_version_3_rollback": True,
            "explicit_rollback_pass": True,
            "reapply_pass": True,
            "container_network_mode": "none",
            "host_port_published": False,
            "host_volume_mounted": False,
            "secrets_persisted": False,
            "container_removed": False,
        }
    except BaseException as error:
        primary_error = error
    finally:
        cleanup_error: BaseException | None = None
        try:
            if inspect_owned_container(docker, container, run_id):
                SUPPORT.run(docker, ["rm", "--force", container], timeout=60)
            cleanup_verified = not inspect_owned_container(docker, container, run_id)
        except BaseException as error:
            cleanup_error = error
        if cleanup_error is not None:
            if primary_error is not None:
                raise HarnessError(
                    f"{primary_error}; container cleanup also failed: {cleanup_error}"
                ) from primary_error
            raise cleanup_error

    if primary_error is not None:
        raise primary_error
    if not cleanup_verified:
        fail("owned test container removal was not verified")
    receipt["container_removed"] = True
    if args.receipt is not None:
        SUPPORT.write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("P14_REVISION_CAS_POSTGRES_PASS apply_v3=2 smoke=2 race=2 rollback_v3=2")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        HarnessError,
        OSError,
        ValueError,
        subprocess.TimeoutExpired,
        concurrent.futures.TimeoutError,
    ) as error:
        print(f"P14_REVISION_CAS_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
