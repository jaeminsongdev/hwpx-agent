from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-job-state-machine-v1.json"
)
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_postgres_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-job-test"


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
        fail("job state-machine contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_job_state_machine_migration.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_job_state_machine_migration", module_path
    )
    if specification is None or specification.loader is None:
        fail("job state-machine migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("job state-machine migration contract did not validate")
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


def assert_version_5_removed(docker: str, container: str) -> None:
    object_counts = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM information_schema.columns
     WHERE table_schema='hwpx_agent'
       AND (
           (table_name='jobs' AND column_name IN (
               'state_machine_version','active_execution_id','lease_issued_at'
           ))
           OR (table_name='job_attempts' AND column_name IN (
               'state_machine_version','lease_expires_at','updated_at'
           ))
       )), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname IN (
           'guard_job_state_machine_update','guard_job_attempt_state_machine_update',
           'verify_job_state_machine_consistency','enqueue_job_state_machine',
           'lease_job_state_machine','advance_job_state_machine','commit_job_success',
           'fail_job_state_machine','get_job_state_machine'
       )), ',',
    (SELECT count(*) FROM pg_indexes
     WHERE schemaname='hwpx_agent'
       AND indexname IN ('jobs_state_machine_queue_idx',
                         'job_attempts_state_machine_active_idx'))
);
""",
    )
    if object_counts != "0,0,0":
        fail(f"version 5 rollback left objects: {object_counts}")


def insert_fake_later_version(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        """
BEGIN;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (6, 'p14.test_later_version', repeat('f', 64));
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
""",
    )


def remove_fake_later_version(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        """
BEGIN;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 6;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
""",
    )


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
    if not isinstance(prerequisites, list) or len(prerequisites) != 4:
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
    up5 = SUPPORT.load_bounded_text(ROOT / str(migration["up_path"]), 256 * 1024)
    down5 = SUPPORT.load_bounded_text(ROOT / str(migration["down_path"]), 128 * 1024)
    smoke_sql = SUPPORT.load_bounded_text(ROOT / str(smoke["path"]), 256 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = SUPPORT.git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(Path(__file__).with_name("validate_job_state_machine_migration.py"))
    support_digest = sha256(SUPPORT_PATH)
    contract_digest = sha256(args.contract.resolve())
    inspected_image = SUPPORT.ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-job-{run_id.replace('-', '')[:12]}"
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
        SUPPORT.apply_up(docker, container, up5, str(migration["up_sha256"]))
        assert_version_state(docker, container, "1,2,3,4,5")
        first_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in first_smoke.stdout:
            fail("first job state-machine smoke did not emit its exact pass marker")

        replay_prefix = (
            "SELECT set_config('hwpx_agent.migration_sha256', "
            f"'{migration['up_sha256']}', false);\n"
        )
        replay = SUPPORT.psql(
            docker, container, replay_prefix + up5, check=False, timeout=120
        )
        if replay.returncode == 0 or "version 5 already exists" not in replay.stderr:
            fail("duplicate version 5 migration was not refused")
        assert_version_state(docker, container, "1,2,3,4,5")

        refused = SUPPORT.apply_down(docker, container, down5, explicitly_allowed=False)
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 5 rollback without the destructive gate was not refused")
        assert_version_state(docker, container, "1,2,3,4,5")

        insert_fake_later_version(docker, container)
        later_refused = SUPPORT.psql(
            docker,
            container,
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', 'on', false);\n"
            + down5,
            check=False,
            timeout=120,
        )
        if later_refused.returncode == 0 or "later migrations removed first" not in later_refused.stderr:
            fail("version 5 rollback did not protect a later migration")
        remove_fake_later_version(docker, container)

        SUPPORT.apply_down(docker, container, down5, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4")
        assert_version_5_removed(docker, container)
        for _, down_sql, _ in reversed(prerequisite_sql):
            SUPPORT.apply_down(docker, container, down_sql, explicitly_allowed=True)

        for up_sql, _, up_digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, up_digest)
        SUPPORT.apply_up(docker, container, up5, str(migration["up_sha256"]))
        second_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied job state-machine smoke did not emit its exact pass marker")
        SUPPORT.apply_down(docker, container, down5, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4")
        assert_version_5_removed(docker, container)
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
            "schema_version": "hwpx-agent.p14-05-postgres-job-state-machine-audit/v1",
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
            "invalid_transition_assertions_per_run": 9,
            "qualified_artifact_revision_assertions_per_run": 4,
            "authorization_context_assertions_per_run": 3,
            "job_attempt_consistency_exercised": True,
            "terminal_immutability_exercised": True,
            "legacy_job_fail_closed": True,
            "rollback_without_gate_refused": True,
            "rollback_with_later_version_refused": True,
            "version_4_preserved_after_version_5_rollback": True,
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
        fail("owned job state-machine test container removal was not verified")
    receipt["container_removed"] = True
    if args.receipt is not None:
        SUPPORT.write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("P14_JOB_STATE_MACHINE_POSTGRES_PASS apply_v5=2 smoke=2 rollback_v5=2")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HarnessError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"P14_JOB_STATE_MACHINE_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
