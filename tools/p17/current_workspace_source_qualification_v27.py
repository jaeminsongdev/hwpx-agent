"""Bind the pure P06-05 table-layout solver over immutable qualification v26."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v26.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v26_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v27-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "8cf3238190794aabb7914564c4f7bd85"
BASE_COMMIT = "5760aee7aac05c4bbdc9d6c03605dd78738bc7c4"
RECEIPT_SHA256 = "8dafccb15d0fd729e1ba6e2a25dc736334e5a80e364183630e4f649585373653"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v26-20260907/contract.json",
    "60867a4ab87dbec6327610cfd4d682826d35368c606ea736867012aa970749d1",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/domain-ir/src/table_layout.rs",
        "bytes": 42080,
        "sha256": "25323009d00036cbd6b9464057e38fd4e8ef17af11feb6d9a052eb98636911c2",
    },
    {
        "path": "crates/domain-ir/src/lib.rs",
        "bytes": 3956,
        "sha256": "6c554dd94fadc206a716dc52e6892ca3e8d38a2d01c5524a1823e727c442ace8",
    },
    {
        "path": "crates/domain-ir/tests/table_layout.rs",
        "bytes": 18199,
        "sha256": "02e59fffc0afb1323cf70a7448f05ecb238fd7a9c5fc538658800da8688690dc",
    },
    {
        "path": "implementation/p06/P06-05_TABLE_LAYOUT_POLICY.md",
        "bytes": 4710,
        "sha256": "ef7ef28f639543e1fd53295035cf642e618f40665c7d4ead505a12f4e869dfd5",
    },
    {
        "path": "protocol/migrations/p06-table-layout-v0-to-v1.md",
        "bytes": 1501,
        "sha256": "b4d0d2ff1f175dea1e4ecc55111cd5ada46e42044e194e2f51124f43ec2eb677",
    },
    {
        "path": "protocol/private/p06-table-layout-v1.json",
        "bytes": 4747,
        "sha256": "a376aea78209005518cd886a33bb47baaadc0955022bf5f85ac86f7189ac43e9",
    },
    {
        "path": "tools/p06/validate_table_layout_contract.py",
        "bytes": 10484,
        "sha256": "01bc7a7a11091c910142b0cdd8f1f53c252b724c594af92eb3cb1a03375a33fc",
    },
    {
        "path": "tools/p06/tests/test_table_layout_contract.py",
        "bytes": 3913,
        "sha256": "fefcbc404b0e8370567260bf87d60b9f2b3901466f2dcd41e0229d4ffd3cb306",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v27.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v27.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V27.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_layout_solver_component_bound": True,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}


def receipt_path(root: Path) -> Path:
    return root / f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json"


def source_lock(root: Path, relative: str) -> dict[str, Any]:
    path = foundation.acceptance.bounded_file(root, relative)
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": foundation.digest(path),
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    foundation.require(
        receipt.get("schema_version") == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    foundation.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    foundation.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    foundation.require(receipt.get("decision") == "PASS", "receipt.decision")
    foundation.require(receipt.get("passed") is True, "receipt.passed")
    foundation.require(receipt.get("check_count") == 11, "receipt.checks")
    foundation.require(
        receipt.get("successors") == list(foundation.SUCCESSORS), "receipt.successors"
    )
    foundation.require(
        receipt.get("successor_count") == len(foundation.SUCCESSORS), "receipt.count"
    )
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == foundation.CARGO_METADATA_PROJECTION_SHA256,
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == foundation.WORKSPACE_MEMBER_COUNT,
        "receipt.members",
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        foundation.require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_implementation_sources(root: Path) -> None:
    seen: set[str] = set()
    for entry in IMPLEMENTATION_SOURCES:
        relative = entry["path"]
        foundation.require(relative not in seen, "implementation.duplicate")
        seen.add(relative)
        path = foundation.acceptance.bounded_file(root, relative)
        foundation.require(path.stat().st_size == entry["bytes"], "implementation.bytes")
        foundation.require(foundation.digest(path) == entry["sha256"], "implementation.digest")
        foundation.require(
            foundation.git_digest(root, BASE_COMMIT, relative) == entry["sha256"],
            "implementation.history",
        )


def validate_predecessor(root: Path) -> None:
    previous_path = foundation.acceptance.bounded_file(
        root, PREVIOUS_QUALIFICATION[0], 512_000
    )
    foundation.require(
        foundation.digest(previous_path) == PREVIOUS_QUALIFICATION[1], "predecessor"
    )


def expected_current(root: Path) -> dict[str, Any]:
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v27",
        "qualification_id": "p17.current-workspace-source.v27.20260907",
        "scope": "p06_05_pure_table_layout_solver_component_source_successor_only",
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
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "claims": CLAIMS,
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v27",
        "qualification_id": "p17.current-workspace-source.v27.20260907",
        "scope": "p06_05_pure_table_layout_solver_component_source_successor_only",
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
        "source_successor_count": len(foundation.SUCCESSORS),
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    foundation.verify(root)
    validate_predecessor(root)
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    foundation.require(
        foundation.digest(receipt_path(root)) == RECEIPT_SHA256, "receipt.digest"
    )
    validate_implementation_sources(root)
    current_path = foundation.acceptance.bounded_file(
        root, f"{BASE}/current-host.json", 512_000
    )
    contract_path = foundation.acceptance.bounded_file(
        root, f"{BASE}/contract.json", 512_000
    )
    current = foundation.load_document(current_path, "current")
    contract = foundation.load_document(contract_path, "contract")
    foundation.require(current == expected_current(root), "current.identity")
    foundation.require(contract == expected_contract(root, current_path), "contract.identity")
    return contract


def qualify() -> tuple[Path, Path]:
    foundation.verify(ROOT)
    validate_predecessor(ROOT)
    receipt = foundation.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    foundation.require(
        foundation.digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest"
    )
    validate_implementation_sources(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(foundation.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(foundation.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v27.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V27_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V27_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
