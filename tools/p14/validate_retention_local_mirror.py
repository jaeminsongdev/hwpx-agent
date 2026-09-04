from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "implementation/p14/postgres/p14-retention-local-mirror-v1.json"
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
        fail("retention mirror contract root is not an object")
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
    if len(functions) != 18:
        fail("retention mirror migration function count differs from the exact contract")
    for function in functions:
        if "SECURITY DEFINER" in function and "SET search_path = pg_catalog" not in function:
            fail("SECURITY DEFINER function lacks a fixed pg_catalog search path")
    if re.search(r"GRANT\s+EXECUTE[\s\S]+?\s+TO\s+PUBLIC", up_sql, re.IGNORECASE):
        fail("retention mirror migration grants executable capability to PUBLIC")
    if len(re.findall(r"REVOKE ALL ON FUNCTION hwpx_agent\.", up_sql)) != len(functions):
        fail("retention mirror migration does not revoke every function from PUBLIC")
    return len(functions)


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, object]:
    if root.resolve() != ROOT.resolve():
        fail("retention mirror validator only accepts the repository root")
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
        fail("retention mirror contract keys differ from the exact schema")
    if document["schema_version"] != "hwpx-agent.p14-retention-local-mirror/v1":
        fail("retention mirror contract schema version differs")
    if document["state"] != "pass" or document["container_image"] != EXPECTED_IMAGE:
        fail("retention mirror contract state or image differs")

    prerequisites = document["prerequisites"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 8:
        fail("retention mirror requires exactly eight prerequisite migrations")
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
        fail("retention mirror migration entry differs")
    if migration["version"] != 9 or migration["name"] != "p14.retention_local_mirror_v1":
        fail("retention mirror migration identity differs")
    up_path = require_digest(
        {"path": migration["up_path"], "sha256": migration["up_sha256"]},
        512 * 1024,
    )
    down_path = require_digest(
        {"path": migration["down_path"], "sha256": migration["down_sha256"]},
        256 * 1024,
    )

    fixture_specs = (
        (
            document["smoke_fixture"],
            32,
            "P14_RETENTION_LOCAL_MIRROR_SMOKE_PASS assertions=32",
        ),
        (
            document["regression_fixture"],
            28,
            "P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28",
        ),
    )
    fixture_paths: list[Path] = []
    for fixture, count, marker in fixture_specs:
        if not isinstance(fixture, dict) or set(fixture) != {
            "path",
            "sha256",
            "assertion_count",
            "pass_marker",
        }:
            fail("retention mirror fixture entry differs")
        fixture_path = require_digest(
            {"path": fixture["path"], "sha256": fixture["sha256"]}, 1024 * 1024
        )
        if fixture["assertion_count"] != count or fixture["pass_marker"] != marker:
            fail("retention mirror fixture metadata differs")
        if marker not in fixture_path.read_text(encoding="utf-8"):
            fail("retention mirror fixture marker is absent")
        fixture_paths.append(fixture_path)

    source_files = document["source_files"]
    if not isinstance(source_files, list) or len(source_files) != 9:
        fail("retention mirror source manifest must contain exactly nine files")
    source_paths = [require_digest(entry, 512 * 1024) for entry in source_files]
    if [item.relative_to(ROOT).as_posix() for item in source_paths] != [
        "Cargo.lock",
        "Cargo.toml",
        "crates/retention-sync-service/Cargo.toml",
        "crates/retention-sync-service/src/lib.rs",
        "implementation/p14/P14-09_RETENTION_SYNC_POLICY.md",
        "tools/p14/test_retention_local_mirror_migration.py",
        "tools/p14/validate_idempotency_reconciliation_core.py",
        "tools/p14/validate_idempotency_reconciliation_migration.py",
        "tools/p14/validate_retention_local_mirror.py",
    ]:
        fail("retention mirror source manifest order or paths differ")

    requirements = document["requirements"]
    expected_requirements = {
        "retention_class_count": 7,
        "retention_max_seconds": 315360000,
        "tombstone_grace_max_seconds": 604800,
        "purge_lease_max_seconds": 300,
        "purge_max_attempts": 3,
        "legal_hold_blocks_delete": True,
        "active_purge_blocks_new_hold": True,
        "shared_reference_rechecked": True,
        "new_references_blocked_after_tombstone": True,
        "exact_delete_replay": True,
        "immutable_purge_receipt": True,
        "trusted_subject_context_bound": True,
        "mirror_digest_only": True,
        "mirror_exact_head_cas": True,
        "mirror_push_subject_bound": True,
        "revision_receipt_bound": True,
        "operation_plan_bound": True,
        "conflict_resolutions": ["rebase_operation_plan", "branch", "manual_merge"],
        "expired_push_recoverable": True,
        "expired_push_requires_new_identity": True,
        "single_generation_reservation": True,
        "unique_active_push_identity": True,
        "forced_tenant_rls": True,
        "public_execute_revoked": True,
        "rollback_refuses_v9_data": True,
        "fixture_remote_seed_is_temporary": True,
        "hangul_runtime_required": False,
        "production_service_qualified": False,
    }
    if requirements != expected_requirements:
        fail("retention mirror requirements differ from the exact policy")

    up_sql = up_path.read_text(encoding="utf-8")
    down_sql = down_path.read_text(encoding="utf-8")
    smoke_sql = fixture_paths[0].read_text(encoding="utf-8")
    rust_source = source_paths[3].read_text(encoding="utf-8")
    policy = source_paths[4].read_text(encoding="utf-8")
    harness = source_paths[5].read_text(encoding="utf-8")
    core_supersession = source_paths[6].read_text(encoding="utf-8")
    migration_supersession = source_paths[7].read_text(encoding="utf-8")
    function_count = validate_security_definer_search_paths(up_sql)
    require_tokens(
        up_sql,
        [
            "CREATE TABLE hwpx_agent.retention_policies",
            "CREATE TABLE hwpx_agent.retention_policy_rules",
            "char_length(retention_policy_id) BETWEEN 3 AND 128",
            "CREATE TABLE hwpx_agent.legal_holds",
            "CREATE TABLE hwpx_agent.artifact_deletion_requests",
            "CREATE TABLE hwpx_agent.artifact_purge_receipts",
            "CREATE TABLE hwpx_agent.project_local_mirrors",
            "CREATE TABLE hwpx_agent.local_mirror_conflicts",
            "REVOKE ALL ON FUNCTION hwpx_agent.protect_p14_09_identity() FROM PUBLIC",
            "p_subject_sha256 <> hwpx_agent.current_subject_sha256()",
            "RETENTION_PURGE_IN_PROGRESS",
            "v_existing.subject_sha256 = p_subject_sha256",
            "v_existing.request_kind = p_request_kind",
            "record_artifact_purge_failure_v1",
            "failed_terminal",
            "artifact_referenced_outside_project_v1",
            "CREATE FUNCTION hwpx_agent.guard_new_artifact_reference_v1()",
            "revisions_retention_reference_guard",
            "jobs_retention_reference_guard",
            "cleanup_tasks_retention_reference_guard",
            "RETENTION_ARTIFACT_UNAVAILABLE",
            "active_push_subject_sha256",
            "local_mirror_push_reservation_idx",
            "local_mirror_active_push_identity_idx",
            "MIRROR_PUSH_ID_CONFLICT",
            "MIRROR_PLAN_MISMATCH",
            "revision_commit_receipts AS receipt",
            "FOR SHARE OF branch, revision, receipt",
            "clock_timestamp()",
            "FORCE ROW LEVEL SECURITY",
        ],
        "up migration",
    )
    require_tokens(
        down_sql,
        [
            "allow_p14_retention_mirror_rollback",
            "IS DISTINCT FROM 'yes'",
            "rollback refuses version 9 data",
            "artifacts_service_metadata_complete_v8",
            "artifacts_object_key_binding_v8",
            "DISABLE TRIGGER schema_versions_immutable",
            "DROP TRIGGER revisions_retention_reference_guard",
            "DROP FUNCTION hwpx_agent.guard_new_artifact_reference_v1()",
        ],
        "down migration",
    )
    require_tokens(
        smoke_sql,
        [
            "CREATE FUNCTION pg_temp.seed_remote_commit",
            "CREATE FUNCTION pg_temp.try_tombstoned_revision_reference",
            "session_replication_role",
            "REVOKE ALL ON FUNCTION pg_temp.seed_remote_commit",
            "P14_RETENTION_LOCAL_MIRROR_SMOKE_PASS assertions=32",
            "MIRROR_PLAN_MISMATCH",
            "RETENTION_PURGE_IN_PROGRESS",
            "assertion 07 drift unexpectedly succeeded",
            "assertion 07 reference race unexpectedly succeeded",
            "assertion 05 oversized policy unexpectedly succeeded",
            "assertion 08 missing artifact alias unexpectedly succeeded",
        ],
        "smoke fixture",
    )
    if "CREATE FUNCTION hwpx_agent.seed_remote_commit" in smoke_sql:
        fail("fixture helper leaked into the product schema")
    require_tokens(
        rust_source,
        [
            "pub enum RetentionClass",
            "pub fn record_purge_failure",
            "PurgeFailureState::Terminal",
            "RetentionSyncError::PurgeInProgress",
            "RetentionSyncError::MirrorPlanMismatch",
            "pub struct MirrorRegistration",
            "device_sha256",
            "policy_expiry: bool",
            "deletion_requests",
            "push_reservations",
            "ManualMergeRequired",
            "#![forbid(unsafe_code)]",
        ],
        "Rust retention service",
    )
    require_tokens(
        policy,
        [
            "The local-mirror API never overwrites the branch head.",
            "P14-07 idempotency/revision regression fixture",
            "guards every newly inserted or changed artifact reference",
            "No Hangul runtime is required",
            "production object storage",
        ],
        "retention policy",
    )
    require_tokens(
        harness,
        [
            '"new_references_blocked_after_tombstone": True',
            '"legal_hold_overtake_rejected": True',
            '"expired_push_requires_new_identity": True',
            '"unique_active_push_identity": True',
        ],
        "retention harness",
    )
    for supersession, revision, label in [
        (
            core_supersession,
            "0f4128c73c55e14fac2c2e84dc5077fa2010119c",
            "P14-07 core supersession",
        ),
        (
            migration_supersession,
            "d84a442f866942a64dc478708dfd2942c4538af6",
            "P14-07 migration supersession",
        ),
    ]:
        require_tokens(
            supersession,
            [
                "P14_09_SUPERSEDING_CONTRACT",
                "P14_09_SUPERSEDED_PATHS",
                revision,
                '"git"',
                '"show"',
            ],
            label,
        )
    return {
        "schema_version": document["schema_version"],
        "state": "pass",
        "prerequisite_count": len(prerequisites),
        "function_count": function_count,
        "smoke_assertion_count": document["smoke_fixture"]["assertion_count"],
        "regression_assertion_count": document["regression_fixture"]["assertion_count"],
        "source_file_count": len(source_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    arguments = parser.parse_args()
    result = validate_contract(arguments.contract)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("P14_RETENTION_LOCAL_MIRROR_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"P14_RETENTION_LOCAL_MIRROR_CONTRACT_FAILED: {error}")
        raise SystemExit(2)
