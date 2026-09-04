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
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "implementation/p14/postgres/p14-cancel-cleanup-v1.json"
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_cleanup_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-cleanup-test"


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
        fail("cancel cleanup contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("validate_cancel_cleanup.py")
    specification = importlib.util.spec_from_file_location(
        "p14_validate_cancel_cleanup", module_path
    )
    if specification is None or specification.loader is None:
        fail("cancel cleanup validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("cancel cleanup contract did not validate")
    return validated


def bounded_text(path: Path, maximum_bytes: int) -> str:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        fail(f"migration input is a link or junction: {path}")
    resolved = path.resolve(strict=True)
    if ROOT.resolve(strict=True) not in resolved.parents:
        fail(f"migration input is outside the repository root: {path}")
    if not resolved.is_file() or not 0 < resolved.stat().st_size <= maximum_bytes:
        fail(f"migration input exceeds its regular-file bound: {path}")
    return resolved.read_text(encoding="utf-8")


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


def start_container(docker: str, image: str, run_id: str, suffix: str) -> str:
    container = f"hwpx-agent-p14-cleanup-{run_id.replace('-', '')[:10]}-{suffix}"
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
            "--tmpfs",
            "/var/lib/postgresql:rw,nosuid,size=512m",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            image,
        ],
        timeout=120,
    )
    SUPPORT.wait_until_ready(docker, container)
    return container


def remove_container(docker: str, container: str, run_id: str) -> None:
    if inspect_owned_container(docker, container, run_id):
        SUPPORT.run(docker, ["rm", "--force", container], timeout=60)
    if inspect_owned_container(docker, container, run_id):
        fail("owned cleanup test container removal was not verified")


def apply_all(
    docker: str,
    container: str,
    migrations: list[tuple[str, str]],
) -> None:
    for sql, digest in migrations:
        SUPPORT.apply_up(docker, container, sql, digest)
    versions = SUPPORT.scalar(
        docker,
        container,
        "SELECT string_agg(version::text, ',' ORDER BY version) "
        "FROM hwpx_agent.schema_versions;\n",
    )
    if versions != "1,2,3,4,5,6,7,8":
        fail(f"schema version set differs after apply: {versions}")


def run_fixture(
    docker: str, container: str, sql: str, marker: str, *, commit: bool = False
) -> None:
    if commit:
        stripped = sql.rstrip()
        if not stripped.endswith("ROLLBACK;"):
            fail("committed fault fixture lacks its bounded final rollback")
        sql = stripped[: -len("ROLLBACK;")] + "COMMIT;\n"
    result = SUPPORT.psql(docker, container, sql, timeout=180)
    if marker not in result.stdout:
        fail(f"fixture did not emit its exact pass marker: {marker}")


def concurrent_claim(docker: str, container: str) -> tuple[int, int]:
    context = (
        "SELECT set_config('hwpx_agent.tenant_id', "
        "'e1000000-0000-0000-0000-000000000001', false);\n"
        "SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), false);\n"
    )
    queue_sql = context + """
SELECT hwpx_agent.queue_orphan_cleanup_v1(
    'e1000000-0000-0000-0000-000000000001',
    'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'e8000000-0000-0000-0000-000000000001',
    'ec000000-0000-0000-0000-000000000006',
    'e4000000-0000-0000-0000-000000000006', repeat('4', 64)
);
"""
    SUPPORT.psql(docker, container, queue_sql)

    def claim(index: int) -> tuple[bool, str]:
        execution_id = f"ee000000-0000-0000-0001-{index:012d}"
        sql = context + f"""
SELECT returned_cleanup_task_id
FROM hwpx_agent.claim_cleanup_task_v1(
    'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
    'e9000000-0000-0000-0000-000000000001',
    '{execution_id}', 30, repeat('5', 64)
);
"""
        result = SUPPORT.psql(docker, container, sql, check=False, timeout=60)
        return result.returncode == 0, result.stdout + result.stderr

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(claim, range(1, 9)))
    winners = sum(1 for success, _ in results if success)
    expected_misses = sum(
        1
        for success, output in results
        if not success and "CLEANUP_TASK_NOT_FOUND" in output
    )
    if winners != 1 or expected_misses != 7:
        fail(
            "concurrent cleanup claim did not produce one winner and seven bounded misses: "
            f"winners={winners}, misses={expected_misses}"
        )
    return winners, expected_misses


def assert_container_isolated(docker: str, container: str) -> None:
    result = SUPPORT.run(docker, ["inspect", container])
    document = json.loads(result.stdout)[0]
    if document.get("HostConfig", {}).get("NetworkMode") != "none":
        fail("cleanup test container is not network isolated")
    if document.get("NetworkSettings", {}).get("Ports") not in ({}, None):
        fail("cleanup test container publishes a host port")
    mounts = document.get("Mounts", [])
    if not isinstance(mounts, list) or any(
        isinstance(mount, dict) and mount.get("Type") in {"bind", "volume"}
        for mount in mounts
    ):
        fail("cleanup test container uses a host bind or volume")


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
    arguments = parse_args()
    docker = shutil.which("docker")
    if docker is None:
        fail("docker executable is unavailable")
    validated = validate_contract(arguments.contract)
    contract = load_contract(arguments.contract.resolve())
    image = str(contract["container_image"])
    inspected_image = SUPPORT.ensure_image(docker, image, arguments.allow_pull)
    prerequisites = contract["prerequisites"]
    migration = contract["migration"]
    smoke = contract["smoke_fixture"]
    regression = contract["regression_fixture"]
    if not isinstance(prerequisites, list) or not isinstance(migration, dict):
        fail("validated migration sections have unexpected shapes")
    migrations: list[tuple[str, str]] = []
    for entry in [*prerequisites, migration]:
        if not isinstance(entry, dict):
            fail("validated migration entry is not an object")
        migrations.append(
            (
                bounded_text(ROOT / str(entry["up_path"]), 512 * 1024),
                str(entry["up_sha256"]),
            )
        )
    down_sql = bounded_text(ROOT / str(migration["down_path"]), 256 * 1024)
    smoke_sql = bounded_text(ROOT / str(smoke["path"]), 512 * 1024)
    regression_sql = bounded_text(ROOT / str(regression["path"]), 512 * 1024)
    source_revision, source_tree_clean = git_state()
    run_id = str(uuid.uuid4())
    active_containers: list[str] = []
    primary_error: BaseException | None = None
    receipt: dict[str, object] = {}
    try:
        fault_container = start_container(docker, image, run_id, "fault")
        active_containers.append(fault_container)
        assert_container_isolated(docker, fault_container)
        server_version = SUPPORT.scalar(docker, fault_container, "SHOW server_version;\n")
        if not server_version.startswith("18.4"):
            fail(f"unexpected PostgreSQL server version: {server_version}")
        apply_all(docker, fault_container, migrations)
        run_fixture(
            docker,
            fault_container,
            regression_sql,
            str(regression["pass_marker"]),
        )
        run_fixture(
            docker,
            fault_container,
            smoke_sql,
            str(smoke["pass_marker"]),
            commit=True,
        )
        claim_winners, claim_misses = concurrent_claim(docker, fault_container)
        refused_with_data = SUPPORT.psql(
            docker,
            fault_container,
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', "
            "'on', false);\n" + down_sql,
            check=False,
            timeout=120,
        )
        if refused_with_data.returncode == 0 or (
            "rollback refuses remaining version 8 data" not in refused_with_data.stderr
        ):
            fail("version 8 rollback did not refuse remaining cleanup data")

        clean_container = start_container(docker, image, run_id, "clean")
        active_containers.append(clean_container)
        assert_container_isolated(docker, clean_container)
        apply_all(docker, clean_container, migrations)
        run_fixture(
            docker, clean_container, smoke_sql, str(smoke["pass_marker"])
        )
        run_fixture(
            docker, clean_container, regression_sql, str(regression["pass_marker"])
        )
        refused_without_gate = SUPPORT.apply_down(
            docker, clean_container, down_sql, explicitly_allowed=False
        )
        if refused_without_gate.returncode == 0 or (
            "requires explicit" not in refused_without_gate.stderr
        ):
            fail("version 8 rollback without its destructive gate was not refused")
        SUPPORT.apply_down(
            docker, clean_container, down_sql, explicitly_allowed=True
        )
        rollback_state = SUPPORT.scalar(
            docker,
            clean_container,
            """
SELECT concat(
    (SELECT string_agg(version::text, ',' ORDER BY version)
     FROM hwpx_agent.schema_versions), '|',
    (SELECT count(*) FROM information_schema.tables
     WHERE table_schema='hwpx_agent' AND table_name IN (
         'cleanup_tasks','job_cancellation_requests','job_effect_markers',
         'cancel_cleanup_v1_rollback_functions'
     )), '|',
    position('allow_cancel_cleanup_v1_transition' in
        pg_get_functiondef('hwpx_agent.guard_job_state_machine_update()'::regprocedure))
);
""",
        )
        if rollback_state != "1,2,3,4,5,6,7|0|0":
            fail(f"version 8 rollback did not restore exact v7 shape: {rollback_state}")
        SUPPORT.apply_up(
            docker, clean_container, migrations[-1][0], migrations[-1][1]
        )
        run_fixture(
            docker, clean_container, smoke_sql, str(smoke["pass_marker"])
        )
        run_fixture(
            docker, clean_container, regression_sql, str(regression["pass_marker"])
        )

        receipt = {
            "schema_version": "hwpx-agent.p14-08-postgres-cancel-cleanup-audit/v1",
            "state": "pass",
            "recorded_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_tree_clean_before_run": source_tree_clean,
            "contract_sha256": sha256(arguments.contract.resolve()),
            "validator_sha256": sha256(Path(__file__).with_name("validate_cancel_cleanup.py")),
            "harness_sha256": sha256(Path(__file__).resolve()),
            "migration_up_sha256": migration["up_sha256"],
            "migration_down_sha256": migration["down_sha256"],
            "smoke_fixture_sha256": smoke["sha256"],
            "regression_fixture_sha256": regression["sha256"],
            "postgres_server_version": server_version,
            "image": image,
            "image_id": inspected_image.get("Id"),
            "smoke_assertions_per_run": smoke["assertion_count"],
            "smoke_runs": 3,
            "regression_assertions_per_run": regression["assertion_count"],
            "regression_runs": 2,
            "concurrent_claimers": 8,
            "concurrent_claim_winners": claim_winners,
            "concurrent_claim_bounded_misses": claim_misses,
            "before_external_fault_exercised": True,
            "after_external_before_receipt_fault_exercised": True,
            "stale_fence_rejected": True,
            "reference_race_rejected": True,
            "source_artifact_protected": True,
            "rollback_without_gate_refused": True,
            "rollback_with_v8_data_refused": True,
            "clean_rollback_to_v7_pass": True,
            "reapply_pass": True,
            "container_network_mode": "none",
            "host_port_published": False,
            "host_volume_mounted": False,
            "containers_removed": False,
        }
    except BaseException as error:
        primary_error = error
    finally:
        cleanup_error: BaseException | None = None
        for container in reversed(active_containers):
            try:
                remove_container(docker, container, run_id)
            except BaseException as error:
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            if primary_error is not None:
                raise HarnessError(
                    f"{primary_error}; container cleanup also failed: {cleanup_error}"
                ) from primary_error
            raise cleanup_error
    if primary_error is not None:
        raise primary_error
    receipt["containers_removed"] = True
    if arguments.receipt is not None:
        write_new_json(arguments.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print(
        "P14_CANCEL_CLEANUP_POSTGRES_PASS "
        "smoke=3 regression=2 claimers=8 winners=1 rollback=1 reapply=1"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        HarnessError,
        SUPPORT.HarnessError,
        OSError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"P14_CANCEL_CLEANUP_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
