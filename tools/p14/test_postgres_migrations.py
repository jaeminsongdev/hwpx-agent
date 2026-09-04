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
DEFAULT_IMAGE = (
    "postgres:18.4-bookworm@"
    "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-metadata-v1.json"
)
LABEL_KEY = "hwpx-agent.p14-test"


class HarnessError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> NoReturn:
    raise HarnessError(message)


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
        stderr = completed.stderr.strip()[-2000:]
        raise HarnessError(
            f"docker command failed ({completed.returncode}): "
            f"{' '.join(arguments[:4])}: {stderr}"
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
    resolved_root = ROOT.resolve(strict=True)
    if resolved_root not in resolved.parents:
        fail(f"migration input is outside the repository root: {path}")
    if not resolved.is_file():
        fail(f"not a regular migration input: {path}")
    size = resolved.stat().st_size
    if size <= 0 or size > maximum_bytes:
        fail(f"migration input is outside its size bound: {path}")
    return resolved.read_text(encoding="utf-8")


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_metadata_migrations.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_metadata_migrations", module_path
    )
    if specification is None or specification.loader is None:
        fail("metadata migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("metadata migration contract did not validate")
    return validated


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
    repo_digests = inspected.get("RepoDigests")
    expected_digest = image.rsplit("@", 1)[1]
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
    docker: str,
    container: str,
    up_sql: str,
    up_sha256: str,
) -> None:
    prefix = (
        "SELECT set_config('hwpx_agent.migration_sha256', "
        f"'{up_sha256}', false);\n"
    )
    psql(docker, container, prefix + up_sql, timeout=120)
    stored = psql(
        docker,
        container,
        "SELECT migration_sha256 FROM hwpx_agent.schema_versions WHERE version = 1;\n",
    ).stdout.strip().splitlines()
    if not stored or stored[-1] != up_sha256:
        fail("schema_versions did not retain the exact up-migration SHA-256")


def apply_down(
    docker: str,
    container: str,
    down_sql: str,
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
        prefix + down_sql,
        timeout=120,
        check=explicitly_allowed,
    )


def schema_exists(docker: str, container: str) -> bool:
    result = psql(
        docker,
        container,
        "SELECT count(*) FROM pg_namespace WHERE nspname = 'hwpx_agent';\n",
    )
    values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return bool(values and values[-1] == "1")


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
    parser.add_argument(
        "--up",
        type=Path,
        default=ROOT / "migrations" / "postgres" / "0001_p14_metadata.up.sql",
    )
    parser.add_argument(
        "--down",
        type=Path,
        default=ROOT / "migrations" / "postgres" / "0001_p14_metadata.down.sql",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "tools" / "p14" / "fixtures" / "p14_metadata_smoke.sql",
    )
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--allow-pull", action="store_true")
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docker = shutil.which("docker")
    if docker is None:
        fail("docker executable is unavailable")
    if "@sha256:" not in args.image:
        fail("PostgreSQL image must be pinned by repository digest")

    validated_contract = validate_contract(args.contract)
    if args.image != validated_contract["container_image"]:
        fail("runtime image differs from the validated migration contract")

    up_sql = load_bounded_text(args.up, 256 * 1024)
    down_sql = load_bounded_text(args.down, 32 * 1024)
    fixture_sql = load_bounded_text(args.fixture, 256 * 1024)
    up_digest = sha256(args.up)
    down_digest = sha256(args.down)
    fixture_digest = sha256(args.fixture)
    if up_digest != validated_contract["up_sha256"]:
        fail("runtime up migration differs from the validated contract")
    if down_digest != validated_contract["down_sha256"]:
        fail("runtime down migration differs from the validated contract")
    if fixture_digest != validated_contract["smoke_fixture_sha256"]:
        fail("runtime smoke fixture differs from the validated contract")
    source_revision, source_tree_clean = git_state()
    harness_digest = sha256(Path(__file__).resolve())
    contract_digest = sha256(args.contract.resolve())
    inspected_image = ensure_image(docker, args.image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-{run_id.replace('-', '')[:12]}"
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
                args.image,
            ],
            timeout=120,
        )
        wait_until_ready(docker, container)

        version = psql(
            docker,
            container,
            "SHOW server_version;\n",
        ).stdout.strip().splitlines()[-1]
        if not version.startswith("18.4"):
            fail(f"unexpected PostgreSQL server version: {version}")

        apply_up(docker, container, up_sql, up_digest)
        first_smoke = psql(docker, container, fixture_sql, timeout=120)
        if "P14_METADATA_SMOKE_PASS assertions=19" not in first_smoke.stdout:
            fail("first migration smoke did not emit its exact pass marker")

        refused = apply_down(
            docker,
            container,
            down_sql,
            explicitly_allowed=False,
        )
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("rollback without the explicit destructive gate was not refused")
        if not schema_exists(docker, container):
            fail("refused rollback modified the metadata schema")

        apply_down(docker, container, down_sql, explicitly_allowed=True)
        if schema_exists(docker, container):
            fail("explicit rollback left the metadata schema present")

        apply_up(docker, container, up_sql, up_digest)
        second_smoke = psql(docker, container, fixture_sql, timeout=120)
        if "P14_METADATA_SMOKE_PASS assertions=19" not in second_smoke.stdout:
            fail("reapplied migration smoke did not emit its exact pass marker")
        apply_down(docker, container, down_sql, explicitly_allowed=True)
        if schema_exists(docker, container):
            fail("final explicit rollback left the metadata schema present")

        receipt = {
            "schema_version": "hwpx-agent.p14-01-postgres-migration-audit/v1",
            "state": "pass",
            "recorded_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_tree_clean_before_run": source_tree_clean,
            "migration_contract_sha256": contract_digest,
            "test_harness_sha256": harness_digest,
            "image": args.image,
            "image_id": inspected_image.get("Id"),
            "postgres_server_version": version,
            "up_migration_sha256": up_digest,
            "down_migration_sha256": down_digest,
            "smoke_fixture_sha256": fixture_digest,
            "assertion_count_per_run": 19,
            "migration_apply_pass": True,
            "rollback_without_gate_refused": True,
            "explicit_rollback_pass": True,
            "reapply_pass": True,
            "cross_tenant_denial_exercised": True,
            "immutable_revision_exercised": True,
            "job_attempt_transition_exercised": True,
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
    print("P14_POSTGRES_MIGRATION_PASS apply=2 smoke=2 refused_rollback=1 rollback=2")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HarnessError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"P14_POSTGRES_MIGRATION_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
