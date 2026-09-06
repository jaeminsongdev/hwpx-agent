"""Freeze and verify the P17 PostgreSQL checkpoint-host current-PC evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "12e4189fc3864f0faedacd6d8e8f6adf"
BASE_COMMIT = "3b28ba8c127f4670ca6db084f905803a92fa470b"
QUALIFICATION = (
    ROOT
    / "implementation/p17/qualification/postgres-checkpoint-host-v1-20260907"
)
RECEIPT_RELATIVE = (
    f"artifacts/p17/postgres-checkpoint-host/runs/{RUN_ID}/receipt.json"
)
RECEIPT_SHA256 = "2886a430fc5dcbbc320b60645d601fced2a2dd8ae8f9b1d4571581ac015c8b8d"
IMAGE = (
    "postgres:18.4-bookworm@sha256:"
    "7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
IMAGE_ID = (
    "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
LABEL = "hwpx-agent.p17-postgres-checkpoint-host-test"
CHECKS = (
    "pinned_postgres_loopback_container",
    "all_fourteen_exact_migrations",
    "empty_rollback_requires_explicit_gate",
    "empty_rollback_and_reapply",
    "dedicated_v2_execute_only_role",
    "separate_host_and_four_client_processes",
    "one_time_tokens_cross_loopback_frame",
    "postgres_create_then_exact_replay",
    "same_key_changed_note_rejected",
    "corrupt_checkpoint_replay_fails_unavailable",
    "one_durable_request_checkpoint_audit",
    "immutable_rows_reject_changes",
    "data_loss_rollback_refused",
    "migration_digest_drift_rejected",
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
    )
)
SOURCE_BINDINGS = {
    "migration_up": MIGRATIONS[-1],
    "migration_down": "migrations/postgres/0014_p17_history_checkpoint_note.down.sql",
    "setup": "tools/p17/fixtures/p17_postgres_checkpoint_setup.sql",
    "host_probe": "crates/remote-sync-host/examples/postgres_checkpoint_host.rs",
    "client_probe": "crates/remote-sync-host/examples/postgres_checkpoint_client.rs",
    "harness": "tools/p17/run_postgres_checkpoint_host_checks.py",
    "database_contract": "implementation/p14/postgres/p14-artifact-service-v1.json",
}
RUNTIME_SOURCES = (
    "Cargo.lock",
    "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/history-service/src/types.rs",
    "crates/mcp-control-plane/src/postgres_plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_source.rs",
    "crates/mcp-control-plane/src/postgres_stored_plan.rs",
    "crates/remote-sync-host/Cargo.toml",
    "crates/remote-sync-host/src/lib.rs",
    "crates/remote-sync-host/src/postgres.rs",
    *SOURCE_BINDINGS.values(),
    *MIGRATIONS[:-1],
)
GUARD_SOURCES = (
    "deny.toml",
    "protocol/private/p17-postgres-checkpoint-host-v1.json",
    "protocol/migrations/p17-postgres-checkpoint-host-v1.md",
    "implementation/p17/P17-06_POSTGRES_CHECKPOINT_HOST_V11.md",
    "tools/p17/postgres_checkpoint_host_qualification.py",
    "tools/p17/tests/test_postgres_checkpoint_host_qualification.py",
)
CLAIMS = {
    "actual_current_pc_disposable_postgresql": True,
    "actual_separate_host_process": True,
    "actual_separate_client_processes": 4,
    "actual_loopback_checkpoint_create": True,
    "actual_exact_checkpoint_replay": True,
    "actual_changed_note_rejection": True,
    "actual_gated_empty_rollback_and_reapply": True,
    "actual_data_loss_rollback_refusal": True,
    "actual_owned_resource_cleanup": True,
    "secrets_persisted": False,
    "durable_retention_mirror_admission": False,
    "atomic_mirror_admission_and_checkpoint": False,
    "actual_pull_or_push": False,
    "persistent_credential_custody": False,
    "actual_hangul": False,
    "production": False,
    "p17_06_complete": False,
}


class QualificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(document: object) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_document(path: Path, code: str, *, canonical_only: bool) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 256_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(document, dict), f"{code}.type")
    if canonical_only:
        require(raw == canonical(document), f"{code}.canonical")
    return document


def source_lock(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    require(path.is_file(), f"source.missing:{relative}")
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def migration_hashes(root: Path) -> list[str]:
    return [digest(root / relative) for relative in MIGRATIONS]


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
            "actual_hangul",
            "production",
            "resources_cleaned",
        },
        "receipt.fields",
    )
    require(
        receipt["schema_version"]
        == "hwpx-agent.p17-postgres-checkpoint-host-run/v1",
        "receipt.schema",
    )
    require(receipt["run_id"] == RUN_ID, "receipt.run")
    require(
        receipt["scope"]
        == "current_pc_disposable_postgres_separate_process_checkpoint",
        "receipt.scope",
    )
    require(receipt["checks"] == list(CHECKS), "receipt.checks")
    require(receipt["check_count"] == len(CHECKS), "receipt.check_count")
    require(receipt["all_passed"] is True, "receipt.decision")
    require(receipt["separate_processes"] is True, "receipt.processes")
    require(type(receipt["host_pid"]) is int and receipt["host_pid"] > 0, "receipt.pid")
    require(receipt["client_process_count"] == 4, "receipt.clients")
    require(
        receipt["database"]
        == {
            "image": IMAGE,
            "image_id": IMAGE_ID,
            "migration_count": len(MIGRATIONS),
            "migration_sha256": migration_hashes(root),
        },
        "receipt.database",
    )
    checkpoint = receipt["checkpoint"]
    require(
        set(checkpoint)
        == {
            "checkpoint_id",
            "revision_id",
            "request_sha256",
            "note_sha256",
            "created",
            "replayed",
            "drift_rejected",
        },
        "receipt.checkpoint.fields",
    )
    require(
        checkpoint
        == {
            "checkpoint_id": "chk_3b1585bf6baf5accbf59adeef27283fc",
            "revision_id": "rev_d5000000000000000000000000000001",
            "request_sha256": (
                "37b408e13b22532c9b9795b4e83d1e027cd8779c8dfdc003fefdcc6fa1e860c4"
            ),
            "note_sha256": (
                "0772392b3d6fa2638a03bdca0fecc96f16feb6b102dc156b1566f70f30fb6c81"
            ),
            "created": True,
            "replayed": True,
            "drift_rejected": True,
        },
        "receipt.checkpoint",
    )
    require(
        receipt["source_sha256"]
        == {key: digest(root / relative) for key, relative in SOURCE_BINDINGS.items()},
        "receipt.sources",
    )
    require(receipt["secrets_persisted"] is False, "receipt.secrets")
    require(receipt["actual_hangul"] is False, "receipt.hangul")
    require(receipt["production"] is False, "receipt.production")
    require(receipt["resources_cleaned"] is True, "receipt.cleanup")


def receipt_path(root: Path) -> Path:
    return root / RECEIPT_RELATIVE


def verify_owned_resources_absent() -> None:
    docker = shutil.which("docker")
    require(docker is not None, "host.docker")
    for command, code in (
        ([docker, "ps", "-a", "--filter", f"label={LABEL}", "--format", "{{.ID}}"],
         "host.container"),
        ([docker, "volume", "ls", "--filter", f"label={LABEL}", "--format", "{{.Name}}"],
         "host.volume"),
    ):
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        require(result.returncode == 0 and not result.stdout.strip(), code)


def expected_current(root: Path) -> dict[str, Any]:
    receipt = receipt_path(root)
    runtime = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    return {
        "schema_version": "hwpx-agent.p17-postgres-checkpoint-host-current/v1",
        "scope": "current_pc_disposable_postgres_separate_process_checkpoint",
        "run_id": RUN_ID,
        "source_base_commit": BASE_COMMIT,
        "checks": list(CHECKS),
        "claims": CLAIMS,
        "database_image": IMAGE,
        "receipt": {"path": RECEIPT_RELATIVE, "sha256": RECEIPT_SHA256},
        "source_sha256": {entry["path"]: entry["sha256"] for entry in runtime},
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-postgres-checkpoint-host-qualification/v1",
        "qualification_id": "p17.postgres-checkpoint-host.v1.20260907",
        "source_base_commit": BASE_COMMIT,
        "scope": "current_pc_durable_checkpoint_subincrement_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "postgres-checkpoint-host-v1-20260907/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def qualify() -> tuple[Path, Path]:
    receipt = receipt_path(ROOT)
    document = load_document(receipt, "receipt", canonical_only=False)
    require(digest(receipt) == RECEIPT_SHA256, "receipt.digest")
    validate_receipt(document)
    verify_owned_resources_absent()
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / QUALIFICATION.relative_to(ROOT)
    current_path = directory / "current-host.json"
    current = load_document(current_path, "current", canonical_only=True)
    contract = load_document(directory / "contract.json", "contract", canonical_only=True)
    receipt = receipt_path(root)
    require(digest(receipt) == RECEIPT_SHA256, "receipt.digest")
    validate_receipt(load_document(receipt, "receipt", canonical_only=False), root)
    require(current == expected_current(root), "current.exact")
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verify_host() -> None:
    verify()
    verify_owned_resources_absent()


if __name__ == "__main__":
    usage = "usage: postgres_checkpoint_host_qualification.py RUN_ID|verify|verify-host"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_POSTGRES_CHECKPOINT_HOST_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_POSTGRES_CHECKPOINT_HOST_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    elif sys.argv[1] == "verify-host":
        verify_host()
        print("P17_POSTGRES_CHECKPOINT_HOST_HOST_VERIFY_PASS")
    else:
        raise SystemExit(usage)
