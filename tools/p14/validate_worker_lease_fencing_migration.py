from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-worker-lease-fencing-v1.json"
)
EXPECTED_IMAGE = (
    "postgres:18.4-bookworm@"
    "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)


class ContractError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise ContractError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bounded_repository_file(relative: str, maximum_bytes: int) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        fail("contract path must be a nonempty repository-relative POSIX path")
    candidate = ROOT / relative
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        fail(f"contract path is a link or junction: {relative}")
    resolved = candidate.resolve(strict=True)
    root = ROOT.resolve(strict=True)
    if root not in resolved.parents or not resolved.is_file():
        fail(f"contract path escapes the repository or is not a file: {relative}")
    if not 0 < resolved.stat().st_size <= maximum_bytes:
        fail(f"contract file exceeds its size bound: {relative}")
    return resolved


def require_digest(entry: dict[str, Any], maximum_bytes: int) -> Path:
    if set(entry) != {"path", "sha256"}:
        fail("digest entry has unexpected keys")
    path = bounded_repository_file(entry["path"], maximum_bytes)
    expected = entry["sha256"]
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        fail(f"invalid digest for {entry['path']}")
    if sha256(path) != expected:
        fail(f"digest mismatch for {entry['path']}")
    return path


def require_tokens(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{label} is missing required tokens: {missing}")


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                fail(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    document = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(document, dict):
        fail("worker lease contract root is not an object")
    return document


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, object]:
    if root.resolve() != ROOT.resolve():
        fail("worker lease validator only accepts the repository root")
    contract_path = path.resolve(strict=True)
    document = load_json(contract_path)
    expected_keys = {
        "schema_version",
        "state",
        "container_image",
        "prerequisites",
        "migration",
        "smoke_fixture",
        "source_files",
        "requirements",
    }
    if set(document) != expected_keys:
        fail("worker lease contract keys differ from the exact schema")
    if document["schema_version"] != "hwpx-agent.p14-worker-lease-fencing/v1":
        fail("worker lease contract schema version differs")
    if document["state"] != "pass" or document["container_image"] != EXPECTED_IMAGE:
        fail("worker lease contract state or image differs")

    prerequisites = document["prerequisites"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 5:
        fail("worker lease contract requires exactly five prerequisite migrations")
    for expected_version, entry in enumerate(prerequisites, start=1):
        if not isinstance(entry, dict) or set(entry) != {
            "version",
            "up_path",
            "up_sha256",
            "down_path",
            "down_sha256",
        }:
            fail("prerequisite migration entry differs")
        if entry["version"] != expected_version:
            fail("prerequisite migration order differs")
        require_digest(
            {"path": entry["up_path"], "sha256": entry["up_sha256"]},
            512 * 1024,
        )
        require_digest(
            {"path": entry["down_path"], "sha256": entry["down_sha256"]},
            256 * 1024,
        )

    migration = document["migration"]
    if not isinstance(migration, dict) or set(migration) != {
        "version",
        "name",
        "up_path",
        "up_sha256",
        "down_path",
        "down_sha256",
    }:
        fail("worker lease migration entry differs")
    if migration["version"] != 6 or migration["name"] != "p14.worker_lease_fencing_v1":
        fail("worker lease migration identity differs")
    up_path = require_digest(
        {"path": migration["up_path"], "sha256": migration["up_sha256"]},
        512 * 1024,
    )
    down_path = require_digest(
        {"path": migration["down_path"], "sha256": migration["down_sha256"]},
        256 * 1024,
    )

    smoke = document["smoke_fixture"]
    if not isinstance(smoke, dict) or set(smoke) != {
        "path",
        "sha256",
        "assertion_count",
        "pass_marker",
    }:
        fail("worker lease smoke fixture entry differs")
    smoke_path = require_digest(
        {"path": smoke["path"], "sha256": smoke["sha256"]},
        512 * 1024,
    )
    if smoke["assertion_count"] != 20 or smoke["pass_marker"] != (
        "P14_WORKER_LEASE_FENCING_SMOKE_PASS assertions=20"
    ):
        fail("worker lease smoke assertion contract differs")

    sources = document["source_files"]
    if not isinstance(sources, list) or len(sources) != 8:
        fail("worker lease contract requires exactly eight source files")
    source_paths: list[Path] = []
    for entry in sources:
        if not isinstance(entry, dict):
            fail("worker lease source entry is not an object")
        source_paths.append(require_digest(entry, 512 * 1024))

    requirements = document["requirements"]
    if requirements != {
        "exact_profile_match": True,
        "exact_capability_digest_match": True,
        "worker_heartbeat_max_seconds": 300,
        "job_lease_absolute_max_seconds": 3600,
        "late_worker_commit_rejected": True,
        "expiry_receipt_required": True,
        "retry_or_requeue_implemented": False,
        "forced_tenant_rls": True,
        "public_execute_revoked": True,
    }:
        fail("worker lease requirements differ")

    up = up_path.read_text(encoding="utf-8")
    down = down_path.read_text(encoding="utf-8")
    smoke_text = smoke_path.read_text(encoding="utf-8")
    source_text = "\n".join(item.read_text(encoding="utf-8") for item in source_paths)
    require_tokens(
        up,
        [
            "CREATE TABLE hwpx_agent.worker_registrations",
            "FORCE ROW LEVEL SECURITY",
            "CREATE POLICY tenant_isolation ON hwpx_agent.worker_registrations",
            "CREATE FUNCTION hwpx_agent.register_scheduler_worker(",
            "CREATE FUNCTION hwpx_agent.heartbeat_scheduler_worker(",
            "CREATE FUNCTION hwpx_agent.heartbeat_job_lease(",
            "CREATE FUNCTION hwpx_agent.expire_job_lease(",
            "MESSAGE = 'JOB_WORKER_NOT_QUALIFIED'",
            "MESSAGE = 'JOB_LEASE_EXPIRED'",
            "MESSAGE = 'JOB_LEASE_STILL_ACTIVE'",
            "NEW.lease_expires_at > OLD.lease_issued_at + interval '1 hour'",
            "NEW.terminal_error_code = 'LEASE_EXPIRED'",
            "REVOKE ALL ON TABLE hwpx_agent.worker_registrations FROM PUBLIC",
            "VALUES (6, 'p14.worker_lease_fencing_v1'",
        ],
        "worker lease up migration",
    )
    require_tokens(
        down,
        [
            "requires explicit hwpx_agent.allow_destructive_rollback=on",
            "requires later migrations removed first",
            "CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_state_machine_update()",
            "DROP TABLE hwpx_agent.worker_registrations",
            "DELETE FROM hwpx_agent.schema_versions WHERE version = 6",
        ],
        "worker lease down migration",
    )
    require_tokens(
        smoke_text,
        [
            "JOB_WORKER_NOT_QUALIFIED",
            "JOB_HEARTBEAT_INVALID",
            "JOB_LEASE_EXPIRED",
            "JOB_RECEIPT_ARTIFACT_NOT_QUALIFIED",
            "P14_WORKER_LEASE_FENCING_SMOKE_PASS assertions=20",
        ],
        "worker lease smoke fixture",
    )
    if len(re.findall(r"v_assertions := v_assertions \+ 1;", smoke_text)) != 20:
        fail("worker lease smoke fixture does not contain exactly 20 assertions")
    require_tokens(
        source_text,
        [
            "pub struct SchedulerService",
            "pub fn register_worker(",
            "pub fn heartbeat_worker(",
            "pub fn lease_job(",
            "pub fn heartbeat_job(",
            "pub fn expire_job(",
            "LeaseExpired",
            "LeaseStillActive",
            "fn late_worker_commit_is_rejected_then_expiry_receipt_closes_attempt()",
        ],
        "worker lease Rust sources",
    )
    return {
        "state": "pass",
        "container_image": EXPECTED_IMAGE,
        "migration_functions": 4,
        "smoke_assertions": 20,
        "source_files": len(source_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    validated = validate_contract(args.contract.resolve(), ROOT)
    print(
        "P14_WORKER_LEASE_FENCING_CONTRACT_PASS "
        f"functions={validated['migration_functions']} "
        f"assertions={validated['smoke_assertions']} "
        f"sources={validated['source_files']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"P14_WORKER_LEASE_FENCING_CONTRACT_FAIL {error}")
        raise SystemExit(1) from error
