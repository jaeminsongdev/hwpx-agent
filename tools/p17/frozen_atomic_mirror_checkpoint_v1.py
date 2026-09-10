"""Verify the P17 atomic mirror/checkpoint qualification from immutable Git blobs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v39 as frozen  # noqa: E402

SOURCE_BASE_COMMIT = "72a59ffee3d1eee78e9d501feac5d6426285f27d"
SNAPSHOT_COMMIT = "aa3ef573ae824c666f92333fa8209a90a0b302f0"
QUALIFICATION_ID = "p17.atomic-mirror-checkpoint.v1.20260910"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/"
    "atomic-mirror-checkpoint-v1-20260910/contract.json"
)
CONTRACT_BYTES = 7_459
CONTRACT_SHA256 = "ddc640bacd8d0d44cca47b6fc8d0116d1ac4aec70f5f8caf29b06a45d2e42d8f"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/"
    "atomic-mirror-checkpoint-v1-20260910/current-host.json"
)
CURRENT_BYTES = 5_966
CURRENT_SHA256 = "48998371c56bfbe9612ebd6aaf1115444cb532f2864faf020a3803b55ab0ae52"
RECEIPT_RELATIVE = (
    "artifacts/p17/atomic-mirror-checkpoint/runs/"
    "7c508c3590914b0eabb169477b633fc7/receipt.json"
)
RECEIPT_SHA256 = "003d362f228c96cf6c6e717b7bfd983bb526eec818ed7167afa22e6c5728fd53"
IMAGE = (
    "postgres:18.4-bookworm@sha256:"
    "7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
IMAGE_ID = "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
RUNTIME_COUNT = 35
GUARD_COUNT = 6
CHECKS = (
    "pinned_postgres_loopback_container",
    "all_fifteen_exact_migrations",
    "empty_rollback_requires_explicit_gate",
    "empty_rollback_and_reapply",
    "dedicated_v3_execute_only_role",
    "separate_host_and_seven_client_processes",
    "one_time_tokens_cross_loopback_frame",
    "postgres_create_then_exact_replay",
    "same_key_changed_note_rejected",
    "durable_role_drift_rejected",
    "durable_head_drift_rejected",
    "durable_mirror_state_drift_rejected",
    "restored_state_exact_replay",
    "one_durable_request_checkpoint_audit",
    "rejected_admissions_left_no_rows",
    "mirror_state_restored_exactly",
    "immutable_rows_reject_changes",
    "migration_digest_drift_rejected",
    "mirror_policy_drift_rejected",
    "execute_privilege_drift_rejected",
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
    )
)
SOURCE_BINDINGS = {
    "migration_up": MIGRATIONS[-1],
    "migration_down": "migrations/postgres/0015_p17_atomic_mirror_checkpoint.down.sql",
    "setup": "tools/p17/fixtures/p17_atomic_mirror_checkpoint_setup.sql",
    "host_probe": (
        "crates/remote-sync-host/examples/postgres_atomic_mirror_checkpoint_host.rs"
    ),
    "client_probe": "crates/remote-sync-host/examples/postgres_checkpoint_client.rs",
    "harness": "tools/p17/run_atomic_mirror_checkpoint_checks.py",
    "database_contract": "implementation/p14/postgres/p14-artifact-service-v1.json",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenAtomicMirrorCheckpointError(ValueError):
    """Fail-closed qualification error with a bounded code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenAtomicMirrorCheckpointError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenAtomicMirrorCheckpointError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def locked_json(
    root: Path,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    code: str,
) -> dict[str, Any]:
    raw = frozen.git_blob(root, SNAPSHOT_COMMIT, relative)
    require(len(raw) == expected_bytes, f"{code}.bytes")
    require(digest(raw) == expected_sha256, f"{code}.digest")
    return load_json(raw, code)


def locked_sources(
    root: Path, entries: Any, expected_count: int, code: str
) -> dict[str, str]:
    require(
        isinstance(entries, list) and len(entries) == expected_count, f"{code}.count"
    )
    result: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise FrozenAtomicMirrorCheckpointError(f"{code}.shape")
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str) or relative in result:
            raise FrozenAtomicMirrorCheckpointError(f"{code}.identity")
        if type(expected_bytes) is not int or expected_bytes <= 0:
            raise FrozenAtomicMirrorCheckpointError(f"{code}.identity")
        if (
            not isinstance(expected_sha256, str)
            or HEX64.fullmatch(expected_sha256) is None
        ):
            raise FrozenAtomicMirrorCheckpointError(f"{code}.identity")
        raw = frozen.git_blob(root, SOURCE_BASE_COMMIT, relative)
        require(len(raw) == expected_bytes, f"{code}.bytes")
        require(digest(raw) == expected_sha256, f"{code}.digest")
        result[relative] = expected_sha256
    return result


def source_digest(root: Path, relative: str) -> str:
    return digest(frozen.git_blob(root, SOURCE_BASE_COMMIT, relative))


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
            "separate_processes",
            "host_pid",
            "client_process_count",
            "database",
            "checkpoint",
            "source_sha256",
            "secrets_persisted",
            "atomic_mirror_admission_and_checkpoint",
            "durable_retention_mirror_admission",
            "actual_hangul",
            "production",
            "resources_cleaned",
        },
        "receipt.fields",
    )
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-atomic-mirror-checkpoint-run/v1",
        "receipt.schema",
    )
    require(
        receipt.get("run_id") == "7c508c3590914b0eabb169477b633fc7",
        "receipt.run",
    )
    require(
        receipt.get("scope") == "current_pc_atomic_mirror_checkpoint_transaction",
        "receipt.scope",
    )
    require(receipt.get("checks") == list(CHECKS), "receipt.checks")
    require(receipt.get("check_count") == len(CHECKS), "receipt.check_count")
    require(receipt.get("all_passed") is True, "receipt.decision")
    require(receipt.get("separate_processes") is True, "receipt.processes")
    require(
        type(receipt.get("host_pid")) is int and receipt["host_pid"] > 0,
        "receipt.pid",
    )
    require(receipt.get("client_process_count") == 7, "receipt.clients")
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
    checkpoint = receipt.get("checkpoint")
    if not isinstance(checkpoint, dict) or set(checkpoint) != {
        "checkpoint_id",
        "revision_id",
        "request_sha256",
        "note_sha256",
        "created",
        "replayed",
        "drift_rejected",
        "durable_role_admission",
        "durable_head_admission",
        "durable_mirror_admission",
    }:
        raise FrozenAtomicMirrorCheckpointError("receipt.checkpoint.fields")
    request_digest = checkpoint.get("request_sha256")
    note_digest = checkpoint.get("note_sha256")
    require(
        checkpoint.get("checkpoint_id") == "chk_3b1585bf6baf5accbf59adeef27283fc"
        and checkpoint.get("revision_id") == "rev_d5000000000000000000000000000001"
        and isinstance(request_digest, str)
        and HEX64.fullmatch(request_digest) is not None
        and isinstance(note_digest, str)
        and HEX64.fullmatch(note_digest) is not None
        and all(
            checkpoint.get(field) is True
            for field in (
                "created",
                "replayed",
                "drift_rejected",
                "durable_role_admission",
                "durable_head_admission",
                "durable_mirror_admission",
            )
        ),
        "receipt.checkpoint",
    )
    require(
        receipt.get("source_sha256")
        == {key: source_digest(root, path) for key, path in SOURCE_BINDINGS.items()},
        "receipt.sources",
    )
    require(receipt.get("secrets_persisted") is False, "receipt.secrets")
    require(
        receipt.get("atomic_mirror_admission_and_checkpoint") is True,
        "receipt.atomic",
    )
    require(
        receipt.get("durable_retention_mirror_admission") is True,
        "receipt.durable",
    )
    require(receipt.get("actual_hangul") is False, "receipt.hangul")
    require(receipt.get("production") is False, "receipt.production")
    require(receipt.get("resources_cleaned") is True, "receipt.cleanup")


def verify(root: Path = ROOT) -> dict[str, Any]:
    frozen.verify_commit(root, SOURCE_BASE_COMMIT)
    frozen.verify_commit(root, SNAPSHOT_COMMIT)
    frozen.require_ancestor(root, frozen.QUALIFICATION_COMMIT, SOURCE_BASE_COMMIT)
    frozen.require_ancestor(root, SOURCE_BASE_COMMIT, SNAPSHOT_COMMIT)
    contract = locked_json(
        root,
        CONTRACT_RELATIVE,
        CONTRACT_BYTES,
        CONTRACT_SHA256,
        "contract",
    )
    current = locked_json(
        root,
        CURRENT_RELATIVE,
        CURRENT_BYTES,
        CURRENT_SHA256,
        "current",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-atomic-mirror-checkpoint-qualification/v1"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope")
        == "current_pc_atomic_durable_mirror_admission_and_checkpoint_only"
        and contract.get("source_base_commit") == SOURCE_BASE_COMMIT,
        "contract.identity",
    )
    require(
        contract.get("evidence")
        == {"path": CURRENT_RELATIVE, "canonical_sha256": CURRENT_SHA256},
        "contract.evidence",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-atomic-mirror-checkpoint-current/v1"
        and current.get("scope") == contract.get("scope")
        and current.get("source_base_commit") == SOURCE_BASE_COMMIT
        and current.get("claims") == contract.get("claims")
        and current.get("checks") == list(CHECKS),
        "current.identity",
    )
    runtime = locked_sources(
        root, contract.get("runtime_sources"), RUNTIME_COUNT, "runtime"
    )
    guards = locked_sources(root, contract.get("guard_sources"), GUARD_COUNT, "guard")
    require(set(runtime).isdisjoint(guards), "source.overlap")
    require(current.get("source_sha256") == runtime, "source.cross_link")
    receipt_path = root / RECEIPT_RELATIVE
    require(receipt_path.is_file(), "receipt.file")
    receipt_raw = receipt_path.read_bytes()
    require(digest(receipt_raw) == RECEIPT_SHA256, "receipt.digest")
    validate_receipt(load_json(receipt_raw, "receipt"), root)
    return contract


def main() -> int:
    try:
        verify(ROOT)
    except FrozenAtomicMirrorCheckpointError as error:
        print(f"P17_FROZEN_ATOMIC_MIRROR_CHECKPOINT_FAIL code={error}", file=sys.stderr)
        return 1
    print(
        "P17_FROZEN_ATOMIC_MIRROR_CHECKPOINT_PASS "
        f"runtime={RUNTIME_COUNT} guards={GUARD_COUNT} checks={len(CHECKS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
