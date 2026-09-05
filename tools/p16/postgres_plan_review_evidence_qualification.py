"""Freeze one successful v13 plan-review evidence run and its exact source set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p16/qualification/plan-review-evidence-v13-20260906-v1"
RUNTIME_SOURCES = (
    "Cargo.lock", "Cargo.toml",
    "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/domain-ir/src/capability_router.rs", "crates/domain-ir/src/semantic_summary.rs",
    "crates/domain-ir/tests/capability_router.rs", "crates/domain-ir/tests/semantic_summary.rs",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/examples/postgres_plan_review_evidence_probe.rs",
    "crates/mcp-control-plane/src/lib.rs", "crates/mcp-control-plane/src/plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_source.rs",
    "crates/mcp-control-plane/src/postgres_stored_plan.rs",
    "crates/mcp-control-plane/src/stored_plan.rs",
    *(f"migrations/postgres/{number:04d}_{name}.up.sql" for number, name in (
        (1, "p14_metadata"), (2, "p14_artifact_service"), (3, "p14_revision_cas"),
        (4, "p14_history_checkpoints"), (5, "p14_job_state_machine"),
        (6, "p14_worker_lease_fencing"), (7, "p14_idempotency_reconciliation"),
        (8, "p14_cancel_cleanup"), (9, "p14_retention_local_mirror"),
        (10, "p16_artifact_repository"), (11, "p16_plan_source"),
        (12, "p16_durable_plan_store"), (13, "p16_plan_review_evidence"),
    )),
    "migrations/postgres/0013_p16_plan_review_evidence.down.sql",
    "tools/p16/run_postgres_plan_review_evidence_checks.py",
    "tools/p16/tests/test_postgres_plan_review_evidence_checks.py",
)
GUARD_SOURCES = (
    "tools/p16/postgres_plan_review_evidence_qualification.py",
    "tools/p16/tests/test_postgres_plan_review_evidence_qualification.py",
    "implementation/p16/P16-06_POSTGRES_PLAN_REVIEW_EVIDENCE_V13.md",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def lock(path: str) -> dict[str, object]:
    source = ROOT / path
    return {"path": path, "bytes": source.stat().st_size, "sha256": digest(source)}


def canonical(document: dict[str, object]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n").encode("utf-8")


def qualify(run_id: str) -> tuple[Path, Path]:
    receipt_path = (ROOT / "artifacts/p16/postgres-plan-review-evidence/runs" / run_id
                    / "receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("schema_version") != "hwpx-agent.p16-plan-review-evidence-check/v1"
            or receipt.get("run_id") != run_id or receipt.get("passed") is not True
            or receipt.get("resources_cleaned") is not True
            or receipt.get("actual_hangul") is not False
            or receipt.get("check_count") != 19):
        raise RuntimeError("run receipt is not an exact successful v13 evidence run")
    current = {
        "schema_version": "hwpx-agent.p16-plan-review-evidence-current/v1",
        "run_id": run_id,
        "scope": receipt["scope"],
        "checks": receipt["checks"],
        "check_count": receipt["check_count"],
        "resources_cleaned": True,
        "claims": {
            "authoritative_plan_source": True, "durable_plan_store": True,
            "durable_plan_review_evidence": True, "encrypted_at_rest": True,
            "postgres_restart": True, "key_rotation": True, "tamper_rejected": True,
            "registered_host": False, "actual_hangul": False, "production": False,
            "phase_complete": False,
        },
        "source_hashes": {path: digest(ROOT / path) for path in RUNTIME_SOURCES},
    }
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-db.json"
    current_path.write_bytes(canonical(current))
    contract = {
        "schema_version": "hwpx-agent.p16-plan-review-evidence-qualification/v1",
        "qualification_id": "p16.plan-review-evidence.v13.20260906.v1",
        "base_commit": "e410843f8b5e4700098337afff8192db77407033",
        "scope": "current_pc_encrypted_durable_plan_review_evidence_successor_only",
        "claims": current["claims"],
        "evidence": {"path": str(current_path.relative_to(ROOT)).replace("\\", "/"),
                     "canonical_sha256": digest(current_path), "run_id": run_id},
        "runtime_sources": [lock(path) for path in RUNTIME_SOURCES],
        "guard_sources": [lock(path) for path in GUARD_SOURCES],
    }
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(contract))
    return current_path, contract_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: postgres_plan_review_evidence_qualification.py RUN_ID")
    current_file, contract_file = qualify(sys.argv[1])
    print(f"P16_PLAN_REVIEW_EVIDENCE_QUALIFICATION_PASS current={current_file.name} "
          f"contract={contract_file.name}")
