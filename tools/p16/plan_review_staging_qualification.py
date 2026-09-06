"""Freeze one clean v14 plan-review staging-host run and its exact source set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p16/qualification/plan-review-host-v14-20260906-v1"
RUN_ID = "d22e85581cd44d06a016f3460a43de12"
BASE_COMMIT = "6856d5cacad6cfbceff8671b3adac85b74fe0d97"
EXPECTED_CHECKS = (
    "product_identity_and_graph_derived",
    "immutable_p15_catalog_digest_preserved",
    "all_thirteen_migrations_applied",
    "authoritative_source_seeded",
    "three_least_privilege_roles_admitted",
    "encrypted_plan_and_evidence_seeded",
    "dedicated_tool_discovered_strict",
    "immutable_resource_read_exact",
    "durable_renderer_call_passed",
    "foreign_project_call_rejected",
    "https_auth_origin_host_size_boundaries_rejected",
    "graceful_host_shutdown",
    "postgres_and_host_restart_restore_exact",
    "registered_path_rejects_ciphertext_tamper",
)
EXPECTED_NETWORK = {
    "missing_auth": 401,
    "invalid_auth": 401,
    "wrong_path": 404,
    "host_rebinding": 403,
    "hostile_origin": 403,
    "wrong_method": 405,
    "oversized_body": 413,
}
EXPECTED_OBSERVATIONS = {
    "migration_count": 13,
    "network_rejections": EXPECTED_NETWORK,
    "render_snapshot_sha256": (
        "19e193a8040d4879db6b8d2a11b95e5aa43afa49ebc7bec4d9f85e684ec79d07"
    ),
    "resource_sha256": (
        "c72ba812b6b253162c9fefb50a5f1f953962585bd7426d0faccc7248d361c32b"
    ),
    "resource_uri": "ui://hwpx-agent/plan-review/v1.html",
    "restart_snapshot_equal": True,
    "restart_snapshot_sha256": (
        "19e193a8040d4879db6b8d2a11b95e5aa43afa49ebc7bec4d9f85e684ec79d07"
    ),
    "tool_name": "render_plan_review_widget",
    "transport": "https_loopback_ephemeral",
}
RECEIPT_SHA256 = "20cfa0819b21ad0563995c757be2c323c0c05ed107ce1cf250d1c8f8c675a75c"
P15_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
CLAIMS = {
    "dedicated_local_mcp_host_registered": True,
    "immutable_p15_catalog_preserved": True,
    "authoritative_plan_source": True,
    "durable_encrypted_plan": True,
    "durable_encrypted_review_evidence": True,
    "registered_path_tamper_rejected": True,
    "postgres_and_host_restart": True,
    "actual_codex_app_installation": False,
    "actual_hangul": False,
    "production": False,
    "phase_complete": False,
}
RUNTIME_SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/auth-middleware/src/lib.rs",
    "crates/domain-ir/src/capability_router.rs",
    "crates/domain-ir/src/operation_plan.rs",
    "crates/domain-ir/src/semantic_summary.rs",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/examples/postgres_plan_review_evidence_probe.rs",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/plan_review.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/postgres_plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_source.rs",
    "crates/mcp-control-plane/src/postgres_stored_plan.rs",
    "crates/mcp-control-plane/src/stored_plan.rs",
    "crates/plan-review-staging-driver/Cargo.toml",
    "crates/plan-review-staging-driver/src/main.rs",
    *(f"migrations/postgres/{number:04d}_{name}.up.sql" for number, name in (
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
    )),
    "protocol/mcp/p15-public-tools-v1.json",
    "web/plugin-widget/package.json",
    "web/plugin-widget/scripts/build-plan-review-widget.mjs",
    "web/plugin-widget/src/plan-review-component.tsx",
    "web/plugin-widget/src/plan-review-model.ts",
    "web/plugin-widget/src/plan-review-resource.ts",
    "web/plugin-widget/src/plan-review-styles.css",
    "web/plan-review-staging/package.json",
    "web/plan-review-staging/tsconfig.json",
    "web/plan-review-staging/src/server.ts",
    "web/plan-review-staging/src/server.test.ts",
    "tools/p16/run_plan_review_staging_checks.py",
    "tools/p16/tests/test_plan_review_staging_checks.py",
    "implementation/p16/P16-06_PLAN_REVIEW_STAGING_HOST_V14.md",
)
GUARD_SOURCES = (
    "tools/p16/plan_review_staging_qualification.py",
    "tools/p16/tests/test_plan_review_staging_qualification.py",
    "implementation/p16/P16-06_REGISTERED_PLAN_REVIEW_HOST_V14.md",
)


class QualificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def source_lock(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    require(path.is_file(), "source.missing")
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and path.stat().st_size <= 256_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(document, dict), f"{code}.type")
    require(raw == canonical(document), f"{code}.canonical")
    return document


def validated_receipt(receipt: dict[str, Any], run_id: str) -> dict[str, Any]:
    require(
        set(receipt)
        == {
            "actual_hangul",
            "check_count",
            "checks",
            "decision",
            "failed_stage",
            "failure",
            "observations",
            "p15_catalog_modified",
            "p15_catalog_sha256",
            "passed",
            "qualifying",
            "resources_cleaned",
            "run_id",
            "schema_version",
            "scope",
            "source_commit",
            "tracked_clean",
        },
        "receipt.exact",
    )
    require(
        receipt.get("schema_version") == "hwpx-agent.p16-plan-review-staging-check/v1"
        and receipt.get("run_id") == run_id
        and receipt.get("scope")
        == "current_pc_disposable_postgres_dedicated_plan_review_mcp_host"
        and receipt.get("checks") == list(EXPECTED_CHECKS)
        and receipt.get("check_count") == len(EXPECTED_CHECKS)
        and receipt.get("passed") is True
        and receipt.get("qualifying") is True
        and receipt.get("decision") == "PASS"
        and receipt.get("tracked_clean") is True
        and receipt.get("resources_cleaned") is True
        and receipt.get("actual_hangul") is False
        and receipt.get("p15_catalog_modified") is False
        and receipt.get("p15_catalog_sha256") == P15_CATALOG_SHA256
        and receipt.get("failed_stage") is None
        and receipt.get("failure") is None
        and isinstance(receipt.get("source_commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", receipt["source_commit"]) is not None,
        "receipt.claims",
    )
    observations = receipt.get("observations")
    require(isinstance(observations, dict), "receipt.observations")
    require(
        observations == EXPECTED_OBSERVATIONS,
        "receipt.observations",
    )
    return receipt


def receipt_for(root: Path, run_id: str) -> tuple[dict[str, Any], Path]:
    path = root / "artifacts/p16/plan-review-staging/runs" / run_id / "receipt.json"
    require(path.is_file() and path.stat().st_size <= 64_000, "receipt.file")
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError("receipt.parse") from error
    require(isinstance(receipt, dict), "receipt.type")
    return validated_receipt(receipt, run_id), path


def documents(root: Path, run_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt, receipt_path = receipt_for(root, run_id)
    require(
        run_id == RUN_ID
        and receipt["source_commit"] == BASE_COMMIT
        and digest(receipt_path) == RECEIPT_SHA256,
        "receipt.identity",
    )
    observations = receipt["observations"]
    current = {
        "schema_version": "hwpx-agent.p16-plan-review-host-current/v1",
        "run_id": run_id,
        "source_commit": receipt["source_commit"],
        "scope": receipt["scope"],
        "checks": list(EXPECTED_CHECKS),
        "check_count": len(EXPECTED_CHECKS),
        "observations": observations,
        "resources_cleaned": True,
        "claims": CLAIMS,
        "receipt": {
            "path": receipt_path.relative_to(root).as_posix(),
            "sha256": digest(receipt_path),
        },
        "source_hashes": {relative: digest(root / relative) for relative in RUNTIME_SOURCES},
    }
    current_sha256 = hashlib.sha256(canonical(current)).hexdigest()
    current_relative = (
        "implementation/p16/qualification/plan-review-host-v14-20260906-v1/current-host.json"
    )
    contract = {
        "schema_version": "hwpx-agent.p16-plan-review-host-qualification/v1",
        "qualification_id": "p16.plan-review-host.v14.20260906.v1",
        "base_commit": receipt["source_commit"],
        "scope": "current_pc_dedicated_local_plan_review_mcp_host_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": current_relative,
            "canonical_sha256": current_sha256,
            "run_id": run_id,
            "receipt_sha256": digest(receipt_path),
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }
    return current, contract


def qualify(run_id: str) -> tuple[Path, Path]:
    current, contract = documents(ROOT, run_id)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    contract_path = QUALIFICATION / "contract.json"
    current_path.write_bytes(canonical(current))
    contract_path.write_bytes(canonical(contract))
    return current_path, contract_path


def verify(root: Path = ROOT) -> dict[str, Any]:
    current_path = root / QUALIFICATION.relative_to(ROOT) / "current-host.json"
    contract_path = root / QUALIFICATION.relative_to(ROOT) / "contract.json"
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    require(
        set(current)
        == {
            "check_count",
            "checks",
            "claims",
            "observations",
            "receipt",
            "resources_cleaned",
            "run_id",
            "schema_version",
            "scope",
            "source_commit",
            "source_hashes",
        }
        and current.get("schema_version") == "hwpx-agent.p16-plan-review-host-current/v1"
        and current.get("run_id") == RUN_ID
        and current.get("source_commit") == BASE_COMMIT
        and current.get("scope")
        == "current_pc_disposable_postgres_dedicated_plan_review_mcp_host"
        and current.get("checks") == list(EXPECTED_CHECKS)
        and current.get("check_count") == len(EXPECTED_CHECKS)
        and current.get("resources_cleaned") is True
        and current.get("claims") == CLAIMS,
        "current.exact",
    )
    observations = current.get("observations")
    require(isinstance(observations, dict), "current.observations")
    receipt = current.get("receipt")
    require(
        isinstance(receipt, dict)
        and set(receipt) == {"path", "sha256"}
        and receipt.get("path")
        == f"artifacts/p16/plan-review-staging/runs/{RUN_ID}/receipt.json"
        and receipt.get("sha256") == RECEIPT_SHA256,
        "current.receipt",
    )
    observed_receipt = {
        "schema_version": "hwpx-agent.p16-plan-review-staging-check/v1",
        "run_id": RUN_ID,
        "scope": current["scope"],
        "checks": current["checks"],
        "check_count": current["check_count"],
        "passed": True,
        "qualifying": True,
        "decision": "PASS",
        "tracked_clean": True,
        "resources_cleaned": True,
        "actual_hangul": False,
        "p15_catalog_modified": False,
        "p15_catalog_sha256": P15_CATALOG_SHA256,
        "failed_stage": None,
        "failure": None,
        "source_commit": BASE_COMMIT,
        "observations": observations,
    }
    validated_receipt(observed_receipt, RUN_ID)
    runtime_locks = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    guard_locks = [source_lock(root, relative) for relative in GUARD_SOURCES]
    require(
        current.get("source_hashes")
        == {locked["path"]: locked["sha256"] for locked in runtime_locks},
        "current.sources",
    )
    expected_contract = {
        "schema_version": "hwpx-agent.p16-plan-review-host-qualification/v1",
        "qualification_id": "p16.plan-review-host.v14.20260906.v1",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_dedicated_local_plan_review_mcp_host_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p16/qualification/"
                "plan-review-host-v14-20260906-v1/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": receipt["sha256"],
        },
        "runtime_sources": runtime_locks,
        "guard_sources": guard_locks,
    }
    require(contract == expected_contract, "contract.exact")
    return contract


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != RUN_ID:
        raise SystemExit("usage: plan_review_staging_qualification.py RUN_ID")
    current_file, contract_file = qualify(sys.argv[1])
    print(
        "P16_PLAN_REVIEW_STAGING_QUALIFICATION_PASS "
        f"current={current_file.name} contract={contract_file.name}"
    )
