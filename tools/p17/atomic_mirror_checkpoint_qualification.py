"""Validate the current-PC P17 atomic mirror checkpoint receipt fail-closed."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "7c508c3590914b0eabb169477b633fc7"
RECEIPT_RELATIVE = f"artifacts/p17/atomic-mirror-checkpoint/runs/{RUN_ID}/receipt.json"
RECEIPT_SHA256 = "003d362f228c96cf6c6e717b7bfd983bb526eec818ed7167afa22e6c5728fd53"
IMAGE = (
    "postgres:18.4-bookworm@sha256:"
    "7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
IMAGE_ID = "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
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


class QualificationError(RuntimeError):
    """Bounded receipt qualification error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 256_000, f"{code}.file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(value, dict), f"{code}.type")
    return value


def workspace_digest(relative: str) -> str:
    path = ROOT / relative
    require(path.is_file(), f"source.missing:{relative}")
    return digest_file(path)


def validate_receipt(
    receipt: dict[str, Any],
    source_digest: Callable[[str], str] = workspace_digest,
) -> None:
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
        receipt["schema_version"] == "hwpx-agent.p17-atomic-mirror-checkpoint-run/v1",
        "receipt.schema",
    )
    require(receipt["run_id"] == RUN_ID, "receipt.run")
    require(
        receipt["scope"] == "current_pc_atomic_mirror_checkpoint_transaction",
        "receipt.scope",
    )
    require(receipt["checks"] == list(CHECKS), "receipt.checks")
    require(receipt["check_count"] == len(CHECKS), "receipt.check_count")
    require(receipt["all_passed"] is True, "receipt.decision")
    require(receipt["separate_processes"] is True, "receipt.processes")
    require(type(receipt["host_pid"]) is int and receipt["host_pid"] > 0, "receipt.pid")
    require(receipt["client_process_count"] == 7, "receipt.clients")
    require(
        receipt["database"]
        == {
            "image": IMAGE,
            "image_id": IMAGE_ID,
            "migration_count": len(MIGRATIONS),
            "migration_sha256": [source_digest(relative) for relative in MIGRATIONS],
        },
        "receipt.database",
    )
    checkpoint = receipt["checkpoint"]
    require(
        isinstance(checkpoint, dict)
        and set(checkpoint)
        == {
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
        },
        "receipt.checkpoint.fields",
    )
    require(
        checkpoint.get("checkpoint_id") == "chk_3b1585bf6baf5accbf59adeef27283fc"
        and checkpoint.get("revision_id") == "rev_d5000000000000000000000000000001"
        and isinstance(checkpoint.get("request_sha256"), str)
        and HEX64.fullmatch(checkpoint["request_sha256"]) is not None
        and isinstance(checkpoint.get("note_sha256"), str)
        and HEX64.fullmatch(checkpoint["note_sha256"]) is not None
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
        receipt["source_sha256"]
        == {key: source_digest(relative) for key, relative in SOURCE_BINDINGS.items()},
        "receipt.sources",
    )
    require(receipt["secrets_persisted"] is False, "receipt.secrets")
    require(
        receipt["atomic_mirror_admission_and_checkpoint"] is True,
        "receipt.atomic",
    )
    require(
        receipt["durable_retention_mirror_admission"] is True,
        "receipt.durable",
    )
    require(receipt["actual_hangul"] is False, "receipt.hangul")
    require(receipt["production"] is False, "receipt.production")
    require(receipt["resources_cleaned"] is True, "receipt.cleanup")


def validate_workspace_receipt() -> dict[str, Any]:
    path = ROOT / RECEIPT_RELATIVE
    require(digest_file(path) == RECEIPT_SHA256, "receipt.digest")
    receipt = load_document(path, "receipt")
    validate_receipt(receipt)
    return receipt


def main() -> int:
    validate_workspace_receipt()
    print(f"P17_ATOMIC_MIRROR_CHECKPOINT_QUALIFICATION_PASS checks={len(CHECKS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
