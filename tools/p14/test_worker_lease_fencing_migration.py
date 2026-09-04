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
    ROOT / "implementation" / "p14" / "postgres" / "p14-worker-lease-fencing-v1.json"
)
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_postgres_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-worker-test"


class HarnessError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise HarnessError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        fail("worker lease contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name(
        "validate_worker_lease_fencing_migration.py"
    )
    specification = importlib.util.spec_from_file_location(
        "p14_validate_worker_lease_fencing", module_path
    )
    if specification is None or specification.loader is None:
        fail("worker lease migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("worker lease migration contract did not validate")
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


def assert_version_6_removed_and_v5_restored(docker: str, container: str) -> None:
    objects = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM information_schema.tables
     WHERE table_schema='hwpx_agent' AND table_name='worker_registrations'), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname IN (
           'guard_worker_registration_update','register_scheduler_worker',
           'heartbeat_scheduler_worker','heartbeat_job_lease','expire_job_lease'
       )), ',',
    (SELECT count(*) FROM pg_indexes
     WHERE schemaname='hwpx_agent'
       AND indexname='worker_registrations_eligibility_idx'), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname='guard_job_state_machine_update'
       AND routine.prosecdef = false
       AND position('worker_registrations' in routine.prosrc) = 0
       AND position('JOB_LEASE_EXPIRED' in routine.prosrc) = 0)
);
""",
    )
    if objects != "0,0,0,1":
        fail(f"version 6 rollback left objects or failed to restore v5: {objects}")


def insert_fake_later_version(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        """
BEGIN;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (7, 'p14.test_later_version', repeat('f', 64));
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
DELETE FROM hwpx_agent.schema_versions WHERE version = 7;
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
    contract = load_contract(args.contract.resolve())
    image = str(validated["container_image"])
    prerequisites = contract["prerequisites"]
    migration = contract["migration"]
    smoke = contract["smoke_fixture"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 5:
        fail("validated prerequisite shape differs")
    if not isinstance(migration, dict) or not isinstance(smoke, dict):
        fail("validated worker lease contract sections differ")

    prerequisite_sql: list[tuple[str, str, str]] = []
    for entry in prerequisites:
        if not isinstance(entry, dict):
            fail("validated prerequisite entry differs")
        prerequisite_sql.append(
            (
                SUPPORT.load_bounded_text(ROOT / str(entry["up_path"]), 512 * 1024),
                SUPPORT.load_bounded_text(
                    ROOT / str(entry["down_path"]), 256 * 1024
                ),
                str(entry["up_sha256"]),
            )
        )
    up6 = SUPPORT.load_bounded_text(ROOT / str(migration["up_path"]), 512 * 1024)
    down6 = SUPPORT.load_bounded_text(
        ROOT / str(migration["down_path"]), 256 * 1024
    )
    smoke_sql = SUPPORT.load_bounded_text(ROOT / str(smoke["path"]), 512 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = SUPPORT.git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(
        Path(__file__).with_name("validate_worker_lease_fencing_migration.py")
    )
    support_digest = sha256(SUPPORT_PATH)
    contract_digest = sha256(args.contract.resolve())
    inspected_image = SUPPORT.ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-worker-{run_id.replace('-', '')[:12]}"
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

        for up_sql, _, digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, digest)
        assert_version_state(docker, container, "1,2,3,4,5")
        SUPPORT.apply_up(docker, container, up6, str(migration["up_sha256"]))
        assert_version_state(docker, container, "1,2,3,4,5,6")
        first_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=180)
        if expected_marker not in first_smoke.stdout:
            fail("first worker lease smoke did not emit its exact pass marker")

        replay_prefix = (
            "SELECT set_config('hwpx_agent.migration_sha256', "
            f"'{migration['up_sha256']}', false);\n"
        )
        replay = SUPPORT.psql(
            docker, container, replay_prefix + up6, check=False, timeout=120
        )
        if replay.returncode == 0 or "exact schema version 5" not in replay.stderr:
            fail("duplicate version 6 migration was not refused")
        assert_version_state(docker, container, "1,2,3,4,5,6")

        refused = SUPPORT.apply_down(docker, container, down6, explicitly_allowed=False)
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 6 rollback without the destructive gate was not refused")
        assert_version_state(docker, container, "1,2,3,4,5,6")

        insert_fake_later_version(docker, container)
        later_refused = SUPPORT.psql(
            docker,
            container,
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', 'on', false);\n"
            + down6,
            check=False,
            timeout=120,
        )
        if later_refused.returncode == 0 or "later migrations removed first" not in (
            later_refused.stderr
        ):
            fail("version 6 rollback did not protect a later migration")
        remove_fake_later_version(docker, container)

        SUPPORT.apply_down(docker, container, down6, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4,5")
        assert_version_6_removed_and_v5_restored(docker, container)
        for _, down_sql, _ in reversed(prerequisite_sql):
            SUPPORT.apply_down(docker, container, down_sql, explicitly_allowed=True)

        for up_sql, _, digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, digest)
        SUPPORT.apply_up(docker, container, up6, str(migration["up_sha256"]))
        second_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=180)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied worker lease smoke did not emit its exact pass marker")
        SUPPORT.apply_down(docker, container, down6, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4,5")
        assert_version_6_removed_and_v5_restored(docker, container)
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
            "schema_version": "hwpx-agent.p14-06-postgres-worker-lease-audit/v1",
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
            "assertion_count_per_run": smoke["assertion_count"],
            "migration_apply_count": 2,
            "smoke_run_count": 2,
            "exact_profile_capability_match_exercised": True,
            "worker_heartbeat_exercised": True,
            "job_heartbeat_exercised": True,
            "stale_fence_rejected": True,
            "late_worker_commit_rejected": True,
            "qualified_expiry_receipt_exercised": True,
            "rollback_without_gate_refused": True,
            "rollback_with_later_version_refused": True,
            "version_5_preserved_after_version_6_rollback": True,
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
        fail("owned worker lease test container removal was not verified")
    receipt["container_removed"] = True
    if args.receipt is not None:
        SUPPORT.write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("P14_WORKER_LEASE_FENCING_POSTGRES_PASS apply_v6=2 smoke=2 rollback_v6=2")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HarnessError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"P14_WORKER_LEASE_FENCING_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2) from error
