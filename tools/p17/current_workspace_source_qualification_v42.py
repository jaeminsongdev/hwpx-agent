"""Bind the exact durable Git pull implementation and current-PC qualification."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import durable_git_mirror_pull_qualification as runtime  # noqa: E402
from tools.p17 import frozen_current_source_v41 as predecessor  # noqa: E402
from tools.p17 import run_current_workspace_source_checks as acceptance  # noqa: E402


BASE = "implementation/p17/qualification/current-workspace-source-v42-20260911"
QUALIFICATION = ROOT / BASE
RUN_ID = "75c0595bbf5842d2b417927b96c319f8"
BASE_COMMIT = "dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6"
RECEIPT_SHA256 = "92fa78d9974df9159d3d4212d04e44688148a9ccb9cd32ad57f59620e4daa71c"
PREVIOUS_QUALIFICATION = (
    "protocol/private/p17-frozen-current-source-v41-v1.json",
    "4bc4dc022804338fddf781b27936ae01197b7db9de79eeb373131b43d11a3f57",
)
IMPLEMENTATION_PATHS = (
    "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/local-sync/src/adapter.rs",
    "crates/local-sync/src/lib.rs",
    "crates/local-sync/tests/remote_adapter.rs",
    "crates/local-sync/tests/state_machine.rs",
    "crates/mcp-control-plane/src/postgres_plan_review.rs",
    "crates/mcp-control-plane/src/postgres_plan_source.rs",
    "crates/mcp-control-plane/src/postgres_stored_plan.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_pull_client.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_pull_host.rs",
    "crates/remote-sync-host/src/durable_git_pull.rs",
    "crates/remote-sync-host/src/durable_git_push.rs",
    "crates/remote-sync-host/src/lib.rs",
    "crates/remote-sync-host/src/postgres.rs",
    "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PULL_V16.md",
    "migrations/postgres/0017_p17_durable_git_mirror_pull.down.sql",
    "migrations/postgres/0017_p17_durable_git_mirror_pull.up.sql",
    "protocol/migrations/p17-durable-git-mirror-pull-v1.md",
    "protocol/migrations/p17-remote-sync-request-v3-to-v4.md",
    "protocol/private/p17-durable-git-mirror-pull-v1.json",
    "protocol/private/p17-remote-sync-adapter-v4.json",
    "tools/p17/fixtures/p17_durable_git_mirror_pull_seed.sql",
    "tools/p17/run_durable_git_mirror_pull_checks.py",
    "tools/p17/tests/test_atomic_mirror_checkpoint_checks.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v41.py",
    "tools/p17/tests/test_durable_git_mirror_pull_contract.py",
    "tools/p17/tests/test_durable_git_mirror_push_qualification.py",
    "tools/p17/tests/test_postgres_checkpoint_host_checks.py",
    "tools/p17/validate_durable_git_mirror_pull_contract.py",
)
RUNTIME_QUALIFICATION_PATHS = (
    "artifacts/p17/durable-git-mirror-pull/runs/"
    "4162580f49da402983be6a8527e9721e/receipt.json",
    "implementation/p17/P17_DURABLE_GIT_MIRROR_PULL_QUALIFICATION_V17.md",
    "implementation/p17/qualification/durable-git-mirror-pull-v1-20260911/"
    "contract.json",
    "implementation/p17/qualification/durable-git-mirror-pull-v1-20260911/"
    "current-host.json",
    "tools/p17/durable_git_mirror_pull_qualification.py",
    "tools/p17/tests/test_durable_git_mirror_pull_qualification.py",
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v42.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v42.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V42.md",
)
CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_durable_pull_verified": True,
    "p17_durable_git_mirror_pull_current_pc_runtime_qualified": True,
    "p17_git_mirror_snapshot_bound_pull_source_bound": True,
    "p17_git_mirror_pull_conflict_preservation_verified": True,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}


def receipt_path(root: Path) -> Path:
    return root / f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json"


def source_lock(root: Path, relative: str, *, committed: bool = False) -> dict[str, Any]:
    path = runtime.bounded_file(root, relative)
    raw = path.read_bytes()
    if committed:
        runtime.require(
            raw == runtime.git_blob(root, BASE_COMMIT, relative),
            "implementation.history",
        )
    return {"path": relative, "bytes": len(raw), "sha256": runtime.digest(raw)}


def validate_predecessor(root: Path) -> None:
    predecessor.verify(root)
    path = runtime.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    runtime.require(
        runtime.digest(path.read_bytes()) == PREVIOUS_QUALIFICATION[1],
        "predecessor.digest",
    )


def expected_successors(root: Path) -> list[dict[str, Any]]:
    try:
        return acceptance.current_source_entries(root, BASE_COMMIT)
    except acceptance.AcceptanceError as error:
        raise runtime.QualificationError(f"successors.{error}") from error


def validate_receipt(receipt: dict[str, Any], root: Path) -> None:
    runtime.require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    runtime.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    runtime.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    runtime.require(receipt.get("decision") == "PASS", "receipt.decision")
    runtime.require(receipt.get("passed") is True, "receipt.passed")
    runtime.require(receipt.get("check_count") == 11, "receipt.checks")
    successors = expected_successors(root)
    runtime.require(receipt.get("successors") == successors, "receipt.successors")
    runtime.require(receipt.get("successor_count") == len(successors), "receipt.count")
    runtime.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "3f12764709ca4d34e3caa17372f7b48ff6e3f1790927fe2299d6e76459510480",
        "receipt.cargo",
    )
    runtime.require(
        receipt.get("cargo_workspace_member_count") == 25,
        "receipt.members",
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        runtime.require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_runtime_qualification(root: Path) -> list[dict[str, Any]]:
    contract = runtime.verify(root)
    runtime.require(
        contract.get("qualification_id")
        == "p17.durable-git-mirror-pull.v1.20260911",
        "runtime.identity",
    )
    claims = contract.get("claims")
    runtime.require(
        isinstance(claims, dict)
        and claims.get("actual_authenticated_loopback") is True
        and claims.get("actual_current_pc_postgresql_18_4") is True
        and claims.get("actual_disposable_local_bare_git") is True
        and claims.get("durable_pull") is True
        and claims.get("actual_clean_remote_advance") is True
        and claims.get("actual_ahead_conflict_preservation") is True
        and claims.get("actual_exact_replay_without_second_observation") is True
        and claims.get("actual_remote_network") is False
        and claims.get("production") is False
        and claims.get("p17_06_complete") is False
        and claims.get("product_complete") is False,
        "runtime.claims",
    )
    return [source_lock(root, relative) for relative in RUNTIME_QUALIFICATION_PATHS]


def implementation_sources(root: Path) -> list[dict[str, Any]]:
    return [source_lock(root, relative, committed=True) for relative in IMPLEMENTATION_PATHS]


def expected_current(root: Path) -> dict[str, Any]:
    receipt = runtime.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt, root)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v42",
        "qualification_id": "p17.current-workspace-source.v42.20260911",
        "scope": "p17_exact_durable_git_pull_source_and_current_pc_runtime_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v42",
        "qualification_id": "p17.current-workspace-source.v42.20260911",
        "scope": "p17_exact_durable_git_pull_source_and_current_pc_runtime_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "sha256": runtime.digest(current_path.read_bytes()),
            "run_id": RUN_ID,
            "receipt_path": receipt_path(root).relative_to(root).as_posix(),
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successor_count": len(expected_successors(root)),
        "implementation_sources": implementation_sources(root),
        "runtime_qualification_sources": validate_runtime_qualification(root),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    validate_predecessor(root)
    receipt = runtime.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt, root)
    runtime.require(
        runtime.digest(receipt_path(root).read_bytes()) == RECEIPT_SHA256,
        "receipt.digest",
    )
    current_path = runtime.bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = runtime.bounded_file(root, f"{BASE}/contract.json", 512_000)
    current = runtime.load_document(current_path, "current")
    contract = runtime.load_document(contract_path, "contract")
    runtime.require(current == expected_current(root), "current.identity")
    runtime.require(contract == expected_contract(root, current_path), "contract.identity")
    return contract


def qualify() -> tuple[Path, Path]:
    validate_predecessor(ROOT)
    receipt = runtime.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt, ROOT)
    runtime.require(
        runtime.digest(receipt_path(ROOT).read_bytes()) == RECEIPT_SHA256,
        "receipt.digest",
    )
    implementation_sources(ROOT)
    validate_runtime_qualification(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(runtime.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(runtime.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v42.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V42_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V42_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
