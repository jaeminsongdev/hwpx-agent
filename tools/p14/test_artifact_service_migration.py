from __future__ import annotations

import argparse
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
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-artifact-service-v1.json"
)
LABEL_KEY = "hwpx-agent.p14-artifact-test"
LEGACY_TENANT_ID = "90000000-0000-0000-0000-000000000001"


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


def run(
    docker: str,
    arguments: list[str],
    *,
    input_text: str | None = None,
    timeout: int = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [docker, *arguments],
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if check and completed.returncode != 0:
        raise HarnessError(
            f"docker command failed ({completed.returncode}): "
            f"{' '.join(arguments[:4])}: {completed.stderr.strip()[-2000:]}"
        )
    return completed


def psql(
    docker: str,
    container: str,
    sql: str,
    *,
    check: bool = True,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    return run(
        docker,
        [
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
        input_text=sql,
        timeout=timeout,
        check=check,
    )


def load_bounded_text(path: Path, maximum_bytes: int) -> str:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        fail(f"migration input is a link or junction: {path}")
    resolved = path.resolve(strict=True)
    if ROOT.resolve(strict=True) not in resolved.parents:
        fail(f"migration input is outside the repository root: {path}")
    if not resolved.is_file() or not (0 < resolved.stat().st_size <= maximum_bytes):
        fail(f"migration input is outside its regular-file bound: {path}")
    return resolved.read_text(encoding="utf-8")


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_artifact_service_migration.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_artifact_service_migration", module_path
    )
    if specification is None or specification.loader is None:
        fail("artifact service migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("artifact service migration contract did not validate")
    return validated


def load_contract_document(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        fail("artifact service contract root is not an object")
    return document


def git_state() -> tuple[str, bool]:
    git = shutil.which("git")
    if git is None:
        fail("git executable is unavailable")
    revision = subprocess.run(
        [git, "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=15,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        [git, "-C", str(ROOT), "status", "--porcelain=v1", "--untracked-files=all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=15,
        check=True,
    ).stdout
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        fail("Git revision is not a full lowercase commit id")
    return revision, status == ""


def inspect_image(docker: str, image: str) -> dict[str, object] | None:
    result = run(docker, ["image", "inspect", image], check=False)
    if result.returncode != 0:
        return None
    document = json.loads(result.stdout)
    if not isinstance(document, list) or len(document) != 1:
        fail("Docker returned an ambiguous image inspection result")
    return document[0]


def ensure_image(docker: str, image: str, allow_pull: bool) -> dict[str, object]:
    inspected = inspect_image(docker, image)
    if inspected is None:
        if not allow_pull:
            fail("pinned PostgreSQL image is absent; rerun with --allow-pull")
        run(docker, ["pull", image], timeout=600)
        inspected = inspect_image(docker, image)
    if inspected is None:
        fail("pinned PostgreSQL image is unavailable after pull")
    expected_digest = image.rsplit("@", 1)[1]
    repo_digests = inspected.get("RepoDigests")
    if not isinstance(repo_digests, list) or not any(
        isinstance(value, str) and value.endswith(f"@{expected_digest}")
        for value in repo_digests
    ):
        fail("local image inspection did not bind the requested repository digest")
    return inspected


def wait_until_ready(docker: str, container: str) -> None:
    deadline = time.monotonic() + 60
    last_error = ""
    while time.monotonic() < deadline:
        result = run(
            docker,
            ["exec", container, "pg_isready", "-U", "postgres", "-d", "postgres"],
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return
        last_error = (result.stderr or result.stdout).strip()[-1000:]
        time.sleep(1)
    fail(f"PostgreSQL did not become ready within 60 seconds: {last_error}")


def apply_up(
    docker: str, container: str, sql: str, migration_sha256: str
) -> None:
    prefix = (
        "SELECT set_config('hwpx_agent.migration_sha256', "
        f"'{migration_sha256}', false);\n"
    )
    psql(docker, container, prefix + sql, timeout=120)


def apply_down(
    docker: str,
    container: str,
    sql: str,
    *,
    explicitly_allowed: bool,
) -> subprocess.CompletedProcess[str]:
    prefix = ""
    if explicitly_allowed:
        prefix = (
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', "
            "'on', false);\n"
        )
    return psql(
        docker,
        container,
        prefix + sql,
        timeout=120,
        check=explicitly_allowed,
    )


def scalar(docker: str, container: str, sql: str) -> str:
    values = [
        line.strip()
        for line in psql(docker, container, sql).stdout.splitlines()
        if line.strip()
    ]
    if not values:
        fail("expected one PostgreSQL scalar value")
    return values[-1]


def assert_version_state(
    docker: str, container: str, expected: str, *, artifact_acl_present: bool
) -> None:
    versions = scalar(
        docker,
        container,
        "SELECT string_agg(version::text, ',' ORDER BY version) "
        "FROM hwpx_agent.schema_versions;\n",
    )
    if versions != expected:
        fail(f"schema version set differs: expected {expected}, got {versions}")
    table_count = scalar(
        docker,
        container,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='hwpx_agent' AND table_name='artifact_acl';\n",
    )
    if (table_count == "1") != artifact_acl_present:
        fail("artifact_acl presence differs from the expected migration state")


def seed_legacy_artifacts(docker: str, container: str) -> None:
    psql(
        docker,
        container,
        f"""
INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES ('{LEGACY_TENANT_ID}', 'legacy-upgrade');
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, storage_state, quarantine_reason_code, encryption_key_ref, verified_at
) VALUES
    (
        '{LEGACY_TENANT_ID}', '90000000-0000-0000-0000-000000000101', repeat('a', 64), 1,
        'application/octet-stream', 'source', 'available', NULL, 'kms.legacy-v1',
        transaction_timestamp()
    ),
    (
        '{LEGACY_TENANT_ID}', '90000000-0000-0000-0000-000000000102', repeat('b', 64), 1,
        'application/octet-stream', 'source', 'quarantined', 'LEGACY_REVIEW', 'kms.legacy-v1',
        NULL
    );
""",
    )


def assert_legacy_artifacts_fail_closed(docker: str, container: str) -> None:
    count = scalar(
        docker,
        container,
        f"""
SELECT count(*)
FROM hwpx_agent.artifacts
WHERE tenant_id = '{LEGACY_TENANT_ID}'
  AND storage_state = 'orphaned'
  AND quarantine_reason_code IS NULL
  AND verified_at IS NULL
  AND service_metadata_version IS NULL
  AND object_key IS NULL
  AND authorization_generation IS NULL;
""",
    )
    if count != "2":
        fail(f"legacy artifacts were not forced closed during upgrade: {count}")


def assert_legacy_artifacts_restored(docker: str, container: str) -> None:
    count = scalar(
        docker,
        container,
        f"""
SELECT count(*)
FROM hwpx_agent.artifacts
WHERE tenant_id = '{LEGACY_TENANT_ID}'
  AND (
    (
      artifact_id = '90000000-0000-0000-0000-000000000101'
      AND storage_state = 'available'
      AND quarantine_reason_code IS NULL
      AND verified_at IS NOT NULL
    )
    OR (
      artifact_id = '90000000-0000-0000-0000-000000000102'
      AND storage_state = 'quarantined'
      AND quarantine_reason_code = 'LEGACY_REVIEW'
      AND verified_at IS NULL
    )
  );
""",
    )
    if count != "2":
        fail(f"version 2 rollback did not restore legacy artifact state: {count}")


def inspect_owned_container(docker: str, container: str, run_id: str) -> bool:
    result = run(docker, ["inspect", container], check=False)
    if result.returncode != 0:
        return False
    document = json.loads(result.stdout)
    if not isinstance(document, list) or len(document) != 1:
        fail("Docker returned an ambiguous container inspection result")
    labels = document[0].get("Config", {}).get("Labels", {})
    if not isinstance(labels, dict) or labels.get(LABEL_KEY) != run_id:
        fail("refusing to remove a container without the exact owned-run label")
    return True


def write_new_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


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
    if "@sha256:" not in image:
        fail("PostgreSQL image must be pinned by repository digest")

    prerequisite = contract["prerequisite"]
    migration = contract["migration"]
    smoke = contract["smoke_fixture"]
    if not isinstance(prerequisite, dict) or not isinstance(migration, dict) or not isinstance(smoke, dict):
        fail("validated contract sections have unexpected shapes")
    up1_path = ROOT / str(prerequisite["up_path"])
    down1_path = ROOT / str(prerequisite["down_path"])
    up2_path = ROOT / str(migration["up_path"])
    down2_path = ROOT / str(migration["down_path"])
    smoke_path = ROOT / str(smoke["path"])
    up1 = load_bounded_text(up1_path, 256 * 1024)
    down1 = load_bounded_text(down1_path, 32 * 1024)
    up2 = load_bounded_text(up2_path, 256 * 1024)
    down2 = load_bounded_text(down2_path, 64 * 1024)
    smoke_sql = load_bounded_text(smoke_path, 256 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(Path(__file__).with_name("validate_artifact_service_migration.py"))
    contract_digest = sha256(args.contract.resolve())
    inspected_image = ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-art-{run_id.replace('-', '')[:12]}"
    cleanup_verified = False
    primary_error: BaseException | None = None
    receipt: dict[str, object] = {}
    try:
        run(
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
        wait_until_ready(docker, container)
        version = scalar(docker, container, "SHOW server_version;\n")
        if not version.startswith("18.4"):
            fail(f"unexpected PostgreSQL server version: {version}")

        apply_up(docker, container, up1, str(prerequisite["up_sha256"]))
        seed_legacy_artifacts(docker, container)
        apply_up(docker, container, up2, str(migration["up_sha256"]))
        assert_legacy_artifacts_fail_closed(docker, container)
        assert_version_state(docker, container, "1,2", artifact_acl_present=True)
        first_smoke = psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in first_smoke.stdout:
            fail("first artifact service smoke did not emit its exact pass marker")

        refused = apply_down(
            docker, container, down2, explicitly_allowed=False
        )
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 2 rollback without the destructive gate was not refused")
        assert_version_state(docker, container, "1,2", artifact_acl_present=True)

        apply_down(docker, container, down2, explicitly_allowed=True)
        assert_legacy_artifacts_restored(docker, container)
        assert_version_state(docker, container, "1", artifact_acl_present=False)
        remaining_columns = scalar(
            docker,
            container,
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='hwpx_agent' AND table_name='artifacts' "
            "AND column_name IN ('object_key','encryption_nonce','authorization_generation');\n",
        )
        if remaining_columns != "0":
            fail("version 2 rollback left artifact service columns behind")

        apply_down(docker, container, down1, explicitly_allowed=True)
        apply_up(docker, container, up1, str(prerequisite["up_sha256"]))
        seed_legacy_artifacts(docker, container)
        apply_up(docker, container, up2, str(migration["up_sha256"]))
        assert_legacy_artifacts_fail_closed(docker, container)
        second_smoke = psql(docker, container, smoke_sql, timeout=120)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied artifact service smoke did not emit its exact pass marker")
        apply_down(docker, container, down2, explicitly_allowed=True)
        assert_legacy_artifacts_restored(docker, container)
        assert_version_state(docker, container, "1", artifact_acl_present=False)
        apply_down(docker, container, down1, explicitly_allowed=True)
        schema_count = scalar(
            docker,
            container,
            "SELECT count(*) FROM pg_namespace WHERE nspname='hwpx_agent';\n",
        )
        if schema_count != "0":
            fail("final rollback left the metadata schema present")

        receipt = {
            "schema_version": "hwpx-agent.p14-02-postgres-artifact-audit/v1",
            "state": "pass",
            "recorded_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_tree_clean_before_run": source_tree_clean,
            "migration_contract_sha256": contract_digest,
            "validator_sha256": validator_digest,
            "test_harness_sha256": harness_digest,
            "image": image,
            "image_id": inspected_image.get("Id"),
            "postgres_server_version": version,
            "prerequisite_up_sha256": prerequisite["up_sha256"],
            "up_migration_sha256": migration["up_sha256"],
            "down_migration_sha256": migration["down_sha256"],
            "smoke_fixture_sha256": smoke["sha256"],
            "assertion_count_per_run": smoke["assertions_per_run"],
            "migration_apply_pass": True,
            "cross_tenant_denial_exercised": True,
            "acl_generation_exercised": True,
            "quarantine_transition_exercised": True,
            "encryption_identity_immutability_exercised": True,
            "legacy_artifact_fail_closed_exercised": True,
            "legacy_artifact_rollback_restored_exercised": True,
            "rollback_without_gate_refused": True,
            "version_1_preserved_after_version_2_rollback": True,
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
                run(docker, ["rm", "--force", container], timeout=60)
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
        write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("P14_ARTIFACT_POSTGRES_PASS apply_v2=2 smoke=2 refused_rollback=1 rollback_v2=2")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HarnessError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"P14_ARTIFACT_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
