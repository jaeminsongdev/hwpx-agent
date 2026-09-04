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
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-history-checkpoints-v1.json"
)
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_postgres_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-history-test"
RACE_TENANT_ID = "f1000000-0000-0000-0000-000000000001"
RACE_PROJECT_ID = "f2000000-0000-0000-0000-000000000001"
RACE_REVISION_ID = "f5000000-0000-0000-0000-000000000001"
RACE_REQUEST_ID = "f7000000-0000-0000-0000-000000000001"
RACE_CHECKPOINT_ID = "f8000000-0000-0000-0000-000000000001"


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
        fail("history contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_history_checkpoints_migration.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_history_checkpoints_migration", module_path
    )
    if specification is None or specification.loader is None:
        fail("history migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("history migration contract did not validate")
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


def seed_race_project(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        f"""
BEGIN;
INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES ('{RACE_TENANT_ID}', 'history-race');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    '{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', 'history-race-project',
    'History Race', 'hancom-hangul-2020-secondary', 'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role)
VALUES ('{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', repeat('f', 64), 'owner');
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, storage_state, encryption_key_ref
) VALUES
    (
        '{RACE_TENANT_ID}', 'f4000000-0000-0000-0000-000000000001',
        repeat('1', 64), 1, 'application/octet-stream', 'source', 'staged',
        'kms.history-race'
    ),
    (
        '{RACE_TENANT_ID}', 'f4000000-0000-0000-0000-000000000002',
        repeat('2', 64), 2, 'application/octet-stream', 'result', 'staged',
        'kms.history-race'
    );
INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
    operation_plan_sha256, validation_state, validation_summary_sha256,
    created_by_subject_sha256
) VALUES (
    '{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', '{RACE_REVISION_ID}',
    'f4000000-0000-0000-0000-000000000001',
    'f4000000-0000-0000-0000-000000000002', repeat('3', 64), 'verified',
    repeat('4', 64), repeat('f', 64)
);
INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count,
    committed_generation, commit_id, commit_request_sha256,
    transaction_receipt_sha256
) VALUES (
    '{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', '{RACE_REVISION_ID}',
    'service_v1', 0, 1, 'f6000000-0000-0000-0000-000000000001',
    repeat('5', 64), repeat('6', 64)
);
COMMIT;
""",
    )


def checkpoint_race_sql(*, hold_transaction: bool) -> str:
    hold = ""
    if hold_transaction:
        hold = """
SELECT pg_advisory_xact_lock(1404);
SELECT pg_sleep(2);
"""
    return f"""
BEGIN;
SELECT set_config('hwpx_agent.tenant_id', '{RACE_TENANT_ID}', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('f', 64), true);
SELECT * FROM hwpx_agent.create_history_checkpoint(
    '{RACE_TENANT_ID}', '{RACE_PROJECT_ID}', repeat('f', 64),
    '{RACE_REQUEST_ID}', repeat('7', 64), '{RACE_CHECKPOINT_ID}',
    '{RACE_REVISION_ID}', 'Concurrent baseline'
);
{hold}COMMIT;
"""


def run_checkpoint_race(docker: str, container: str) -> dict[str, object]:
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        holder = executor.submit(
            SUPPORT.psql,
            docker,
            container,
            checkpoint_race_sql(hold_transaction=True),
            timeout=30,
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
            fail("checkpoint race holder did not publish its lock")
        contender_started = time.monotonic()
        contender = executor.submit(
            SUPPORT.psql,
            docker,
            container,
            checkpoint_race_sql(hold_transaction=False),
            timeout=30,
        )
        holder_result = holder.result(timeout=35)
        contender_result = contender.result(timeout=35)
        contender_seconds = time.monotonic() - contender_started
    elapsed = time.monotonic() - started

    outputs = [holder_result.stdout, contender_result.stdout]
    created = sum(bool(re.search(r"(?m)^created\|", output)) for output in outputs)
    replayed = sum(bool(re.search(r"(?m)^replayed\|", output)) for output in outputs)
    if created != 1 or replayed != 1:
        fail(f"concurrent checkpoint outcomes differ: created={created} replayed={replayed}")
    if contender_seconds < 1.0:
        fail(f"contender did not wait on the idempotency claim: {contender_seconds:.3f}s")

    persisted = SUPPORT.scalar(
        docker,
        container,
        f"""
SELECT concat(
    (SELECT count(*) FROM hwpx_agent.history_checkpoint_requests
     WHERE tenant_id='{RACE_TENANT_ID}' AND project_id='{RACE_PROJECT_ID}'), ',',
    (SELECT count(*) FROM hwpx_agent.checkpoints
     WHERE tenant_id='{RACE_TENANT_ID}' AND project_id='{RACE_PROJECT_ID}'), ',',
    (SELECT count(*) FROM hwpx_agent.audit_events
     WHERE tenant_id='{RACE_TENANT_ID}' AND project_id='{RACE_PROJECT_ID}'
       AND event_type='history.checkpoint_created')
);
""",
    )
    if persisted != "1,1,1":
        fail(f"concurrent checkpoint persistence differs: {persisted}")
    return {
        "created": created,
        "replayed": replayed,
        "contender_wait_seconds": round(contender_seconds, 3),
        "elapsed_seconds": round(elapsed, 3),
        "claim_checkpoint_audit_counts": persisted,
    }


def assert_version_4_removed(docker: str, container: str) -> None:
    object_counts = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM information_schema.tables
     WHERE table_schema='hwpx_agent' AND table_name='history_checkpoint_requests'), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname IN (
           'create_history_checkpoint','create_history_branch','query_revision_history'
       )), ',',
    (SELECT count(*) FROM pg_indexes
     WHERE schemaname='hwpx_agent'
       AND indexname='revision_graph_seals_history_order_idx')
);
""",
    )
    if object_counts != "0,0,0":
        fail(f"version 4 rollback left objects: {object_counts}")


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
    if not isinstance(prerequisites, list) or len(prerequisites) != 3:
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
    up4 = SUPPORT.load_bounded_text(ROOT / str(migration["up_path"]), 256 * 1024)
    down4 = SUPPORT.load_bounded_text(ROOT / str(migration["down_path"]), 128 * 1024)
    smoke_sql = SUPPORT.load_bounded_text(ROOT / str(smoke["path"]), 256 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = SUPPORT.git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(Path(__file__).with_name("validate_history_checkpoints_migration.py"))
    support_digest = sha256(SUPPORT_PATH)
    contract_digest = sha256(args.contract.resolve())
    inspected_image = SUPPORT.ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-history-{run_id.replace('-', '')[:12]}"
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

        for up_sql, _, up_digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, up_digest)
        SUPPORT.apply_up(docker, container, up4, str(migration["up_sha256"]))
        assert_version_state(docker, container, "1,2,3,4")
        first_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in first_smoke.stdout:
            fail("first history smoke did not emit its exact pass marker")
        seed_race_project(docker, container)
        first_race = run_checkpoint_race(docker, container)

        refused = SUPPORT.apply_down(docker, container, down4, explicitly_allowed=False)
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 4 rollback without the destructive gate was not refused")
        assert_version_state(docker, container, "1,2,3,4")

        SUPPORT.apply_down(docker, container, down4, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3")
        assert_version_4_removed(docker, container)
        for _, down_sql, _ in reversed(prerequisite_sql):
            SUPPORT.apply_down(docker, container, down_sql, explicitly_allowed=True)

        for up_sql, _, up_digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, up_digest)
        SUPPORT.apply_up(docker, container, up4, str(migration["up_sha256"]))
        second_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied history smoke did not emit its exact pass marker")
        seed_race_project(docker, container)
        second_race = run_checkpoint_race(docker, container)
        SUPPORT.apply_down(docker, container, down4, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3")
        assert_version_4_removed(docker, container)
        for _, down_sql, _ in reversed(prerequisite_sql):
            SUPPORT.apply_down(docker, container, down_sql, explicitly_allowed=True)
        schema_count = SUPPORT.scalar(
            docker,
            container,
            "SELECT count(*) FROM pg_namespace WHERE nspname='hwpx_agent';\n",
        )
        if schema_count != "0":
            fail("final rollback left the metadata schema present")

        receipt = {
            "schema_version": "hwpx-agent.p14-04-postgres-history-audit/v1",
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
            "concurrent_idempotency_race_count": 2,
            "first_race": first_race,
            "second_race": second_race,
            "stable_snapshot_query_exercised": True,
            "merge_dag_query_exercised": True,
            "semantic_diff_indirection_exercised": True,
            "cross_tenant_denial_exercised": True,
            "authorization_denial_exercised": True,
            "legacy_revision_fail_closed": True,
            "rollback_without_gate_refused": True,
            "version_3_preserved_after_version_4_rollback": True,
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
        fail("owned history test container removal was not verified")
    receipt["container_removed"] = True
    if args.receipt is not None:
        SUPPORT.write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("P14_HISTORY_POSTGRES_PASS apply_v4=2 smoke=2 race=2 rollback_v4=2")
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
        print(f"P14_HISTORY_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
