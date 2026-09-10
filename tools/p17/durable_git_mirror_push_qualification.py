"""Qualify the exact current-PC durable Git mirror push receipt and source commit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/durable-git-mirror-push-v1-20260910"
QUALIFICATION = ROOT / BASE
SOURCE_BASE_COMMIT = "2b0a74e68107931fce9a2a2f6985f5b081ad078f"
RUN_ID = "9b3ff9b352ec402aab20f1c5a387a8ec"
RECEIPT_RELATIVE = f"artifacts/p17/durable-git-mirror-push/runs/{RUN_ID}/receipt.json"
RECEIPT_SHA256 = "efca394cc9962da63c3044c1aa4b78fbe9283e8f89d40ce3ae1fbe076146dd4d"
IMAGE = (
    "postgres:18.4-bookworm@sha256:"
    "7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
IMAGE_ID = "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
CHECKS = (
    "pinned_postgres_loopback_container",
    "all_sixteen_exact_migrations",
    "empty_rollback_requires_explicit_gate",
    "empty_rollback_and_reapply",
    "dedicated_function_only_role",
    "exact_local_bare_git_repository",
    "verified_artifact_acl_required_before_plan_or_git_effect",
    "git_committed_database_finalize_interrupted_is_unavailable",
    "canonical_plan_precedes_git_effect",
    "executing_reservation_blocks_branch_mutation",
    "exact_fence_cannot_authorize_wrong_branch_head",
    "expired_lease_reacquired_with_higher_fence",
    "committed_git_observed_and_database_finalized_once",
    "exact_request_replay_has_no_extra_commit_or_revision",
    "same_key_changed_payload_rejected",
    "finalized_effect_is_immutable",
    "divergence_database_transition_interruption_is_unavailable",
    "external_ref_divergence_detected_after_interruption",
    "competing_ref_never_overwritten",
    "divergence_enters_manual_merge_without_database_revision",
    "rollback_refuses_retained_effects",
    "migration_digest_drift_rejected",
    "effect_rls_drift_rejected",
    "execute_privilege_drift_rejected",
    "public_execute_drift_rejected",
    "fixed_search_path_drift_rejected",
    "security_definer_drift_rejected",
)
MIGRATIONS = tuple(
    f"migrations/postgres/{number:04d}_{name}.up.sql"
    for number, name in (
        (1, "p14_metadata"),
        (2, "p14_artifact_service"),
        (3, "p14_revision_cas"),
        (4, "p14_history_checkpoints"),
        (5, "p14_job_state_machine"),
        (6, "p14_worker_lease_fencing"),
        (7, "p14_idempotency_reconciliation"),
        (8, "p14_cancel_cleanup"),
        (9, "p14_retention_local_mirror"),
        (10, "p16_artifact_repository"),
        (11, "p16_plan_source"),
        (12, "p16_durable_plan_store"),
        (13, "p16_plan_review_evidence"),
        (14, "p17_history_checkpoint_note"),
        (15, "p17_atomic_mirror_checkpoint"),
        (16, "p17_durable_git_mirror_push"),
    )
)
SOURCE_BINDINGS = {
    "migration_up": MIGRATIONS[-1],
    "migration_down": "migrations/postgres/0016_p17_durable_git_mirror_push.down.sql",
    "setup": "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql",
    "host_probe": "crates/remote-sync-host/examples/postgres_durable_git_push_host.rs",
    "client_probe": "crates/remote-sync-host/examples/postgres_durable_git_push_client.rs",
    "coordinator": "crates/remote-sync-host/src/durable_git_push.rs",
    "git_effect_host": "crates/remote-sync-host/src/git_mirror.rs",
    "harness": "tools/p17/run_durable_git_mirror_push_checks.py",
    "database_contract": "implementation/p14/postgres/p14-artifact-service-v1.json",
}
RUNTIME_PATHS = tuple(
    sorted(
        {
            "Cargo.lock",
            "crates/artifact-service/src/store/postgres_repository.rs",
            "crates/mcp-control-plane/src/postgres_plan_review.rs",
            "crates/mcp-control-plane/src/postgres_plan_source.rs",
            "crates/mcp-control-plane/src/postgres_stored_plan.rs",
            "crates/remote-sync-host/Cargo.toml",
            "crates/remote-sync-host/src/lib.rs",
            "crates/remote-sync-host/src/postgres.rs",
            "protocol/private/p17-durable-git-mirror-push-v1.json",
            "protocol/migrations/p17-durable-git-mirror-push-v1.md",
            "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PUSH_V14.md",
            "tools/p17/validate_durable_git_mirror_push_contract.py",
            "tools/p17/tests/test_durable_git_mirror_push_contract.py",
            "tools/p17/tests/test_atomic_mirror_checkpoint_checks.py",
            "tools/p17/tests/test_postgres_checkpoint_host_checks.py",
            *MIGRATIONS,
            *SOURCE_BINDINGS.values(),
        }
    )
)
GUARD_PATHS = (
    "implementation/p17/P17_DURABLE_GIT_MIRROR_PUSH_QUALIFICATION_V15.md",
    "tools/p17/durable_git_mirror_push_qualification.py",
    "tools/p17/tests/test_durable_git_mirror_push_qualification.py",
)
CLAIMS = {
    "actual_current_pc_postgresql_18_4": True,
    "actual_disposable_local_bare_git": True,
    "actual_authenticated_loopback": True,
    "actual_verified_artifact_acl_admission": True,
    "actual_canonical_plan_before_git_effect": True,
    "actual_committed_effect_recovery": True,
    "actual_exact_replay_without_second_effect": True,
    "actual_divergence_preservation": True,
    "actual_runtime_admission_drift_rejection": True,
    "actual_owned_resource_cleanup": True,
    "secrets_persisted": False,
    "actual_remote_network": False,
    "durable_pull": False,
    "persistent_credential_custody": False,
    "registered_host": False,
    "actual_hangul": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class QualificationError(ValueError):
    """Fail-closed qualification error containing only a bounded code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_relative(relative: str) -> str:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path",
    )
    return relative


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    validate_relative(relative)
    require(type(maximum) is int and 0 < maximum <= 4_000_000, "file.limit")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "file.link",
        )
    try:
        path = cursor.resolve(strict=True)
    except OSError as error:
        raise QualificationError("file.missing") from error
    require(
        resolved_root in path.parents
        and path.is_file()
        and 0 < path.stat().st_size <= maximum,
        "file.shape",
    )
    return path


def load_document(path: Path, code: str) -> dict[str, Any]:
    raw = path.read_bytes()

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, member in pairs:
            require(key not in value, f"{code}.duplicate")
            value[key] = member
        return value

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def git_blob(root: Path, commit: str, relative: str) -> bytes:
    require(HEX40.fullmatch(commit) is not None, "git.commit")
    validate_relative(relative)
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=30,
        check=False,
    )
    require(result.returncode == 0 and 0 < len(result.stdout) <= 4_000_000, "git.blob")
    return result.stdout


def source_digest(root: Path, relative: str) -> str:
    return digest(git_blob(root, SOURCE_BASE_COMMIT, relative))


def source_lock(root: Path, relative: str, *, committed: bool) -> dict[str, Any]:
    raw = bounded_file(root, relative).read_bytes()
    if committed:
        require(raw == git_blob(root, SOURCE_BASE_COMMIT, relative), "source.history")
    return {"path": relative, "bytes": len(raw), "sha256": digest(raw)}


def validate_receipt(receipt: dict[str, Any], root: Path = ROOT) -> None:
    require(
        set(receipt)
        == {
            "schema_version",
            "run_id",
            "scope",
            "checks",
            "check_count",
            "all_passed",
            "database",
            "effect",
            "source_sha256",
            "secrets_persisted",
            "authenticated_loopback",
            "durable_git_plan_before_effect",
            "database_and_git_exactly_once_recovery",
            "actual_remote_network",
            "actual_hangul",
            "production",
            "resources_cleaned",
        },
        "receipt.fields",
    )
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-push-run/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("scope") == "current_pc_postgresql_local_bare_git_loopback",
        "receipt.identity",
    )
    require(
        receipt.get("checks") == list(CHECKS)
        and receipt.get("check_count") == len(CHECKS)
        and receipt.get("all_passed") is True,
        "receipt.checks",
    )
    require(
        receipt.get("database")
        == {
            "image": IMAGE,
            "image_id": IMAGE_ID,
            "migration_count": len(MIGRATIONS),
            "migration_sha256": [source_digest(root, path) for path in MIGRATIONS],
        },
        "receipt.database",
    )
    effect = receipt.get("effect")
    require(
        isinstance(effect, dict)
        and set(effect)
        == {
            "first_revision_id",
            "first_result_git_oid",
            "second_result_git_oid",
            "competing_git_oid",
            "bounded_state_sha256",
            "committed_recovered",
            "exact_replay",
            "divergence_preserved",
        },
        "receipt.effect.fields",
    )
    require(
        isinstance(effect.get("first_revision_id"), str)
        and re.fullmatch(r"rev_[0-9a-f]{32}", effect["first_revision_id"]) is not None
        and all(
            isinstance(effect.get(key), str)
            and re.fullmatch(r"[0-9a-f]{40}", effect[key]) is not None
            for key in ("first_result_git_oid", "second_result_git_oid", "competing_git_oid")
        )
        and isinstance(effect.get("bounded_state_sha256"), str)
        and HEX64.fullmatch(effect["bounded_state_sha256"]) is not None
        and all(
            effect.get(key) is True
            for key in ("committed_recovered", "exact_replay", "divergence_preserved")
        ),
        "receipt.effect",
    )
    require(
        receipt.get("source_sha256")
        == {key: source_digest(root, path) for key, path in SOURCE_BINDINGS.items()},
        "receipt.sources",
    )
    for key in (
        "authenticated_loopback",
        "durable_git_plan_before_effect",
        "database_and_git_exactly_once_recovery",
        "resources_cleaned",
    ):
        require(receipt.get(key) is True, f"receipt.{key}")
    for key in ("secrets_persisted", "actual_remote_network", "actual_hangul", "production"):
        require(receipt.get(key) is False, f"receipt.{key}")


def expected_current(root: Path) -> dict[str, Any]:
    receipt_path = bounded_file(root, RECEIPT_RELATIVE, 256_000)
    receipt = load_document(receipt_path, "receipt")
    validate_receipt(receipt, root)
    return {
        "schema_version": "hwpx-agent.p17-durable-git-mirror-push-current/v1",
        "qualification_id": "p17.durable-git-mirror-push.v1.20260910",
        "scope": "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
        "source_base_commit": SOURCE_BASE_COMMIT,
        "receipt": {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "check_count": len(CHECKS),
            "sha256": RECEIPT_SHA256,
        },
        "checks": list(CHECKS),
        "source_sha256": receipt["source_sha256"],
        "claims": CLAIMS,
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-durable-git-mirror-push-qualification/v1",
        "qualification_id": "p17.durable-git-mirror-push.v1.20260910",
        "scope": "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
        "source_base_commit": SOURCE_BASE_COMMIT,
        "claims": CLAIMS,
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "canonical_sha256": digest(current_path.read_bytes()),
        },
        "receipt": {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "check_count": len(CHECKS),
            "sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [
            source_lock(root, relative, committed=True) for relative in RUNTIME_PATHS
        ],
        "guard_sources": [
            source_lock(root, relative, committed=False) for relative in GUARD_PATHS
        ],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    receipt_path = bounded_file(root, RECEIPT_RELATIVE, 256_000)
    require(digest(receipt_path.read_bytes()) == RECEIPT_SHA256, "receipt.digest")
    receipt = load_document(receipt_path, "receipt")
    validate_receipt(receipt, root)
    current_path = bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = bounded_file(root, f"{BASE}/contract.json", 512_000)
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    require(current == expected_current(root), "current.identity")
    require(contract == expected_contract(root, current_path), "contract.identity")
    return contract


def qualify() -> tuple[Path, Path]:
    receipt_path = bounded_file(ROOT, RECEIPT_RELATIVE, 256_000)
    require(digest(receipt_path.read_bytes()) == RECEIPT_SHA256, "receipt.digest")
    validate_receipt(load_document(receipt_path, "receipt"), ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: durable_git_mirror_push_qualification.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current, contract = qualify()
        print(
            "P17_DURABLE_GIT_MIRROR_PUSH_QUALIFICATION_PASS "
            f"current={current.name} contract={contract.name} checks={len(CHECKS)}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_DURABLE_GIT_MIRROR_PUSH_QUALIFICATION_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
