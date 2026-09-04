from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "implementation/p14/postgres/p14-cancel-cleanup-v1.json"
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


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        document: dict[str, Any] = {}
        for key, value in pairs:
            if key in document:
                fail(f"duplicate JSON key: {key}")
            document[key] = value
        return document

    document = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(document, dict):
        fail("cancel cleanup contract root is not an object")
    return document


def bounded_file(relative: str, maximum_bytes: int) -> Path:
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
    path = bounded_file(entry["path"], maximum_bytes)
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


def validate_security_definer_search_paths(up_sql: str) -> int:
    functions = re.findall(
        r"CREATE(?: OR REPLACE)? FUNCTION hwpx_agent\.[\s\S]+?\n\$\$;", up_sql
    )
    if len(functions) < 9:
        fail("cancel cleanup migration exposes fewer functions than expected")
    for function in functions:
        if "SECURITY DEFINER" in function and "SET search_path = pg_catalog" not in function:
            fail("SECURITY DEFINER function lacks a fixed pg_catalog search path")
    if re.search(r"GRANT\s+EXECUTE[\s\S]+?\s+TO\s+PUBLIC", up_sql, re.IGNORECASE):
        fail("cancel cleanup migration grants executable capability to PUBLIC")
    return len(functions)


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, object]:
    if root.resolve() != ROOT.resolve():
        fail("cancel cleanup validator only accepts the repository root")
    document = load_json(path.resolve(strict=True))
    if set(document) != {
        "schema_version",
        "state",
        "container_image",
        "prerequisites",
        "migration",
        "smoke_fixture",
        "regression_fixture",
        "source_files",
        "requirements",
    }:
        fail("cancel cleanup contract keys differ from the exact schema")
    if document["schema_version"] != "hwpx-agent.p14-cancel-cleanup/v1":
        fail("cancel cleanup contract schema version differs")
    if document["state"] != "pass" or document["container_image"] != EXPECTED_IMAGE:
        fail("cancel cleanup contract state or image differs")

    prerequisites = document["prerequisites"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 7:
        fail("cancel cleanup requires exactly seven prerequisite migrations")
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
            {"path": entry["up_path"], "sha256": entry["up_sha256"]}, 512 * 1024
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
        fail("cancel cleanup migration entry differs")
    if migration["version"] != 8 or migration["name"] != "p14.cancel_cleanup_v1":
        fail("cancel cleanup migration identity differs")
    up_path = require_digest(
        {"path": migration["up_path"], "sha256": migration["up_sha256"]},
        512 * 1024,
    )
    down_path = require_digest(
        {"path": migration["down_path"], "sha256": migration["down_sha256"]},
        256 * 1024,
    )

    smoke = document["smoke_fixture"]
    regression = document["regression_fixture"]
    for fixture, count, marker in (
        (smoke, 18, "P14_CANCEL_CLEANUP_SMOKE_PASS assertions=18"),
        (
            regression,
            28,
            "P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28",
        ),
    ):
        if not isinstance(fixture, dict) or set(fixture) != {
            "path",
            "sha256",
            "assertion_count",
            "pass_marker",
        }:
            fail("cancel cleanup fixture entry differs")
        fixture_path = require_digest(
            {"path": fixture["path"], "sha256": fixture["sha256"]}, 512 * 1024
        )
        if fixture["assertion_count"] != count or fixture["pass_marker"] != marker:
            fail("cancel cleanup fixture metadata differs")
        if marker not in fixture_path.read_text(encoding="utf-8"):
            fail("cancel cleanup fixture marker is absent")

    source_files = document["source_files"]
    if not isinstance(source_files, list) or len(source_files) != 8:
        fail("cancel cleanup source manifest must contain exactly eight files")
    source_paths = [require_digest(entry, 256 * 1024) for entry in source_files]
    if [path.relative_to(ROOT).as_posix() for path in source_paths] != [
        ".gitignore",
        "crates/artifact-service/src/bin/p14_cleanup_worker.rs",
        "crates/artifact-service/src/store.rs",
        "crates/foundation/src/workdir.rs",
        "crates/operation-engine/src/transaction.rs",
        "implementation/p14/P14-08_CLEANUP_POLICY.md",
        "tools/p14/test_cancel_cleanup_migration.py",
        "tools/p14/validate_cancel_cleanup.py",
    ]:
        fail("cancel cleanup source manifest order or paths differ")

    requirements = document["requirements"]
    expected_requirements = {
        "opaque_handles_only": True,
        "queued_cancel_immediate": True,
        "active_cancel_safe_point": True,
        "started_effect_becomes_unknown": True,
        "committed_effect_is_too_late": True,
        "source_artifact_protected": True,
        "reference_rechecked_before_cleanup": True,
        "orphan_claim_reserves_purging": True,
        "cleanup_lease_max_seconds": 300,
        "cleanup_max_attempts": 3,
        "stale_fence_rejected": True,
        "before_and_after_effect_faults": True,
        "rollback_refuses_v8_data": True,
        "forced_tenant_rls": True,
        "public_execute_revoked": True,
        "hangul_runtime_required": False,
        "production_service_qualified": False,
    }
    if requirements != expected_requirements:
        fail("cancel cleanup requirements differ from the exact policy")

    up_sql = up_path.read_text(encoding="utf-8")
    down_sql = down_path.read_text(encoding="utf-8")
    worker = source_paths[1].read_text(encoding="utf-8")
    function_count = validate_security_definer_search_paths(up_sql)
    require_tokens(
        up_sql,
        [
            "CREATE TABLE hwpx_agent.job_cancellation_requests",
            "CREATE TABLE hwpx_agent.job_effect_markers",
            "CREATE TABLE hwpx_agent.cleanup_tasks",
            "allow_cancel_cleanup_v1_transition",
            "SAFE_POINT_CANCELLATION_PENDING",
            "CLEANUP_SOURCE_PROTECTED",
            "CLEANUP_TARGET_REFERENCED",
            "storage_state = 'purging'",
            "lease_expires_at <= lease_issued_at + interval '5 minutes'",
            "attempt_count BETWEEN 0 AND 3",
            "FOR UPDATE OF task SKIP LOCKED",
            "CLEANUP_LEASE_MISMATCH",
            "ORPHAN_CLEANUP",
            "FORCE ROW LEVEL SECURITY",
            "cancel_cleanup_v1_rollback_functions",
        ],
        "up migration",
    )
    require_tokens(
        down_sql,
        [
            "allow_destructive_rollback",
            "rollback refuses remaining version 8 data",
            "DROP TABLE hwpx_agent.cleanup_tasks",
            "jobs_state_machine_complete_v7",
            "job_attempts_state_machine_complete_v7",
            "EXECUTE v_job_guard",
            "DELETE FROM hwpx_agent.schema_versions WHERE version = 8",
        ],
        "down migration",
    )
    require_tokens(
        worker,
        [
            "#![forbid(unsafe_code)]",
            "MAX_CLEANUP_LEASE_SECONDS: u64 = 300",
            "MAX_CLEANUP_ATTEMPTS: u16 = 3",
            "SourceArtifactProtected",
            "OutcomeUnknown",
            "AfterExternalCleanupBeforeReceipt",
            "recheck_orphan_projection",
            "verify_bounded_digest",
            "WorkspaceAlreadyAbsent",
            "ArtifactAlreadyQuarantined",
        ],
        "cleanup worker core",
    )
    return {
        "schema_version": document["schema_version"],
        "state": "pass",
        "functions": function_count,
        "smoke_assertions": smoke["assertion_count"],
        "regression_assertions": regression["assertion_count"],
        "source_files": len(source_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    arguments = parser.parse_args()
    try:
        result = validate_contract(arguments.contract)
    except (ContractError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
