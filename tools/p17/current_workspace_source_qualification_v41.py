"""Bind the exact durable Git push implementation and current-PC qualification."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"{name}.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[2]
predecessor = load_module(
    "p17_current_workspace_source_v40_predecessor",
    Path(__file__).resolve().with_name("current_workspace_source_qualification_v40.py"),
)
runtime = load_module(
    "p17_durable_git_mirror_push_qualification",
    Path(__file__).resolve().with_name("durable_git_mirror_push_qualification.py"),
)
foundation = predecessor.foundation

BASE = "implementation/p17/qualification/current-workspace-source-v41-20260910"
QUALIFICATION = ROOT / BASE
RUN_ID = "f5098f7e6661491a9eaac20e0d8e209b"
BASE_COMMIT = "2b0a74e68107931fce9a2a2f6985f5b081ad078f"
RECEIPT_SHA256 = "59491b32cffdd84f696f580f528d8276cef1dce6f6ff831e2084a24318ac667f"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/"
    "current-workspace-source-v40-20260910/contract.json",
    "9b7cd7d3d2eda9cf3cd8bff2e9bc67f94a8a62f60a3701bfcdc53b0cd1f08c3d",
)
IMPLEMENTATION_PATHS = (
    "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/mcp-control-plane/src/postgres_plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_source.rs",
    "crates/mcp-control-plane/src/postgres_stored_plan.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_push_client.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_push_host.rs",
    "crates/remote-sync-host/src/durable_git_push.rs",
    "crates/remote-sync-host/src/lib.rs",
    "crates/remote-sync-host/src/postgres.rs",
    "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PUSH_V14.md",
    "migrations/postgres/0016_p17_durable_git_mirror_push.down.sql",
    "migrations/postgres/0016_p17_durable_git_mirror_push.up.sql",
    "protocol/migrations/p17-durable-git-mirror-push-v1.md",
    "protocol/private/p17-durable-git-mirror-push-v1.json",
    "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql",
    "tools/p17/run_durable_git_mirror_push_checks.py",
    "tools/p17/tests/test_atomic_mirror_checkpoint_checks.py",
    "tools/p17/tests/test_durable_git_mirror_push_contract.py",
    "tools/p17/tests/test_postgres_checkpoint_host_checks.py",
    "tools/p17/validate_durable_git_mirror_push_contract.py",
)
RUNTIME_QUALIFICATION_PATHS = (
    "artifacts/p17/durable-git-mirror-push/runs/"
    "9b3ff9b352ec402aab20f1c5a387a8ec/receipt.json",
    "implementation/p17/P17_DURABLE_GIT_MIRROR_PUSH_QUALIFICATION_V15.md",
    "implementation/p17/qualification/durable-git-mirror-push-v1-20260910/"
    "contract.json",
    "implementation/p17/qualification/durable-git-mirror-push-v1-20260910/"
    "current-host.json",
    "tools/p17/durable_git_mirror_push_qualification.py",
    "tools/p17/tests/test_durable_git_mirror_push_qualification.py",
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v41.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v41.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V41.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p17_git_mirror_authenticated_dispatch_verified": True,
    "p17_git_mirror_postgresql_state_machine_verified": True,
    "p17_durable_git_mirror_push_current_pc_runtime_qualified": True,
    "p17_current_pc_postgresql_18_4_verified": True,
    "p17_disposable_local_bare_git_push_verified": True,
    "p17_committed_push_recovery_verified": True,
    "p17_divergent_ref_preservation_verified": True,
    "p17_durable_pull_verified": False,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}

ARTIFACT_REPOSITORY_SUCCESSOR: dict[str, Any] = {
    "accepted_predecessor_sha256s": [
        "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
    ],
    "composition_predecessor_sha256": (
        "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
    ),
    "current_sha256": (
        "d25b45204abc9b8a693d5cca3ca2de5e0b60033edca65d3fca3d3e7fdf803769"
    ),
    "path": "crates/artifact-service/src/store/postgres_repository.rs",
}
SUCCESSORS: tuple[dict[str, Any], ...] = tuple(
    ARTIFACT_REPOSITORY_SUCCESSOR
    if entry["path"] == ARTIFACT_REPOSITORY_SUCCESSOR["path"]
    else entry
    for entry in predecessor.SUCCESSORS
)


def receipt_path(root: Path) -> Path:
    return root / f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json"


def source_lock(root: Path, relative: str) -> dict[str, Any]:
    path = foundation.acceptance.bounded_file(root, relative)
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": foundation.digest(path),
    }


def committed_source_lock(root: Path, relative: str) -> dict[str, Any]:
    lock = source_lock(root, relative)
    foundation.require(
        foundation.git_digest(root, BASE_COMMIT, relative) == lock["sha256"],
        "implementation.history",
    )
    return lock


def validate_receipt(receipt: dict[str, Any]) -> None:
    foundation.require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    foundation.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    foundation.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    foundation.require(receipt.get("decision") == "PASS", "receipt.decision")
    foundation.require(receipt.get("passed") is True, "receipt.passed")
    foundation.require(receipt.get("check_count") == 11, "receipt.checks")
    foundation.require(
        receipt.get("successors") == list(SUCCESSORS), "receipt.successors"
    )
    foundation.require(
        receipt.get("successor_count") == len(SUCCESSORS), "receipt.count"
    )
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "3f12764709ca4d34e3caa17372f7b48ff6e3f1790927fe2299d6e76459510480",
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == 25, "receipt.members"
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        foundation.require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_predecessor(root: Path) -> None:
    path = foundation.acceptance.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    foundation.require(
        foundation.digest(path) == PREVIOUS_QUALIFICATION[1], "predecessor"
    )


def validate_runtime_qualification(root: Path) -> list[dict[str, Any]]:
    contract = runtime.verify(root)
    foundation.require(
        contract.get("qualification_id")
        == "p17.durable-git-mirror-push.v1.20260910",
        "runtime.identity",
    )
    claims = contract.get("claims")
    foundation.require(
        isinstance(claims, dict)
        and claims.get("actual_authenticated_loopback") is True
        and claims.get("actual_current_pc_postgresql_18_4") is True
        and claims.get("actual_disposable_local_bare_git") is True
        and claims.get("actual_committed_effect_recovery") is True
        and claims.get("actual_divergence_preservation") is True
        and claims.get("actual_remote_network") is False
        and claims.get("durable_pull") is False
        and claims.get("production") is False
        and claims.get("product_complete") is False,
        "runtime.claims",
    )
    return [source_lock(root, relative) for relative in RUNTIME_QUALIFICATION_PATHS]


def implementation_sources(root: Path) -> list[dict[str, Any]]:
    return [committed_source_lock(root, relative) for relative in IMPLEMENTATION_PATHS]


def expected_current(root: Path) -> dict[str, Any]:
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v41",
        "qualification_id": "p17.current-workspace-source.v41.20260910",
        "scope": "p17_exact_durable_git_push_source_and_current_pc_runtime_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": receipt_path(root).relative_to(root).as_posix(),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successors": receipt["successors"],
        "implementation_sources": implementation_sources(root),
        "runtime_qualification_sources": validate_runtime_qualification(root),
        "claims": CLAIMS,
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v41",
        "qualification_id": "p17.current-workspace-source.v41.20260910",
        "scope": "p17_exact_durable_git_push_source_and_current_pc_runtime_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "sha256": foundation.digest(current_path),
            "run_id": RUN_ID,
            "receipt_path": receipt_path(root).relative_to(root).as_posix(),
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successor_count": len(SUCCESSORS),
        "implementation_sources": implementation_sources(root),
        "runtime_qualification_sources": validate_runtime_qualification(root),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    validate_predecessor(root)
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    foundation.require(
        foundation.digest(receipt_path(root)) == RECEIPT_SHA256, "receipt.digest"
    )
    current_path = foundation.acceptance.bounded_file(
        root, f"{BASE}/current-host.json", 512_000
    )
    contract_path = foundation.acceptance.bounded_file(
        root, f"{BASE}/contract.json", 512_000
    )
    current = foundation.load_document(current_path, "current")
    contract = foundation.load_document(contract_path, "contract")
    foundation.require(current == expected_current(root), "current.identity")
    foundation.require(
        contract == expected_contract(root, current_path), "contract.identity"
    )
    return contract


def qualify() -> tuple[Path, Path]:
    validate_predecessor(ROOT)
    receipt = foundation.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    foundation.require(
        foundation.digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest"
    )
    validate_runtime_qualification(ROOT)
    implementation_sources(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(foundation.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(foundation.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v41.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V41_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V41_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
