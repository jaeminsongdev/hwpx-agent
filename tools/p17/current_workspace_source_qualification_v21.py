"""Bind the exact P06-01 TableGrid implementation over immutable source qualification v20."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v20", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v21-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "ad8c1afa1c6b42d0a34469dbbd4471ca"
BASE_COMMIT = "0b8db6e695f60cae8b9e59bd988922fb7e90b9f1"
RECEIPT_SHA256 = "2ec4bd69fbe3f20003ce2b0774dc6e62fb5b039b0d3798e68502321d1e22d94f"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v20-20260907/contract.json",
    "adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/domain-ir/src/table_grid.rs",
        "bytes": 21165,
        "sha256": "40f6e2f2adecdecfa7db61c65852ec875c3fc3b3d5cd9de6a972ec63de557d86",
    },
    {
        "path": "crates/domain-ir/tests/table_grid.rs",
        "bytes": 11037,
        "sha256": "eb8401f752d4c07e1706ad8bbb6a3bed45d785852f81396802cccb37e903f239",
    },
    {
        "path": "crates/domain-ir/src/lib.rs",
        "bytes": 3068,
        "sha256": "ec5e767c7d3bf1db51056e4a6eb3acabfc21889724ae5da2646a5b657a714138",
    },
    {
        "path": "protocol/private/p06-table-grid-v1.json",
        "bytes": 2498,
        "sha256": "cb856ac0cad0209b86c940044393bed4d3ec95341bcafa7a7f921bd69d624901",
    },
    {
        "path": "protocol/migrations/p06-table-grid-v0-to-v1.md",
        "bytes": 1107,
        "sha256": "90ac47ceae9eccdb6db889ae1966269de2ba8e68d159fb194e7fc89f2b66a010",
    },
    {
        "path": "implementation/p06/P06-01_TABLE_GRID_POLICY.md",
        "bytes": 3575,
        "sha256": "adaeada3b696c8479126292c550525edfec12ebff7d240b96572695c1854cc5d",
    },
    {
        "path": "tools/p06/validate_table_grid_contract.py",
        "bytes": 6902,
        "sha256": "488dbd15fee04baf8bb238731e6b2deec69f996f27c8deb771ba840e60c4f79c",
    },
    {
        "path": "tools/p06/tests/test_table_grid_contract.py",
        "bytes": 3111,
        "sha256": "19052978ae5bdad94ea77599e3e8a1a09d93ad3cd863ccfaca9ffa3b89bf7d39",
    },
    {
        "path": "tools/p01/run_ci.py",
        "bytes": 8392,
        "sha256": "a23677452a69ecb3a9031022d03e4e685a86ec848189b5b1d980344fe08d7cf2",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v21.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v21.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V21.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_grid_v1_sources_bound": True,
    "p06_01_complete": False,
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
    path = predecessor.acceptance.bounded_file(root, relative)
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": predecessor.digest(path),
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    predecessor.require(
        receipt.get("schema_version") == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    predecessor.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    predecessor.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    predecessor.require(receipt.get("decision") == "PASS", "receipt.decision")
    predecessor.require(receipt.get("passed") is True, "receipt.passed")
    predecessor.require(receipt.get("check_count") == 11, "receipt.checks")
    predecessor.require(
        receipt.get("successors") == list(predecessor.SUCCESSORS), "receipt.successors"
    )
    predecessor.require(receipt.get("successor_count") == len(predecessor.SUCCESSORS), "receipt.count")
    predecessor.require(
        receipt.get("cargo_metadata_projection_sha256")
        == predecessor.CARGO_METADATA_PROJECTION_SHA256,
        "receipt.cargo",
    )
    predecessor.require(
        receipt.get("cargo_workspace_member_count") == predecessor.WORKSPACE_MEMBER_COUNT,
        "receipt.members",
    )
    for claim in ("actual_hangul", "registered_host", "production", "other_pc_or_version", "phase_complete"):
        predecessor.require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_implementation_sources(root: Path) -> None:
    seen: set[str] = set()
    for entry in IMPLEMENTATION_SOURCES:
        relative = entry["path"]
        predecessor.require(relative not in seen, "implementation.duplicate")
        seen.add(relative)
        path = predecessor.acceptance.bounded_file(root, relative)
        predecessor.require(path.stat().st_size == entry["bytes"], "implementation.bytes")
        predecessor.require(predecessor.digest(path) == entry["sha256"], "implementation.digest")
        predecessor.require(
            predecessor.git_digest(root, BASE_COMMIT, relative) == entry["sha256"],
            "implementation.history",
        )


def expected_current(root: Path) -> dict[str, Any]:
    receipt = predecessor.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v21",
        "qualification_id": "p17.current-workspace-source.v21.20260907",
        "scope": "p06_01_table_grid_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v21",
        "qualification_id": "p17.current-workspace-source.v21.20260907",
        "scope": "p06_01_table_grid_source_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "sha256": predecessor.digest(current_path),
            "run_id": RUN_ID,
            "receipt_path": receipt_path(root).relative_to(root).as_posix(),
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successor_count": len(predecessor.SUCCESSORS),
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    predecessor.verify(root)
    previous_path = predecessor.acceptance.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    predecessor.require(predecessor.digest(previous_path) == PREVIOUS_QUALIFICATION[1], "predecessor")
    receipt = predecessor.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    predecessor.require(predecessor.digest(receipt_path(root)) == RECEIPT_SHA256, "receipt.digest")
    validate_implementation_sources(root)
    current_path = predecessor.acceptance.bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = predecessor.acceptance.bounded_file(root, f"{BASE}/contract.json", 512_000)
    current = predecessor.load_document(current_path, "current")
    contract = predecessor.load_document(contract_path, "contract")
    predecessor.require(current == expected_current(root), "current.identity")
    predecessor.require(contract == expected_contract(root, current_path), "contract.identity")
    return contract


def qualify() -> tuple[Path, Path]:
    predecessor.verify(ROOT)
    previous_path = predecessor.acceptance.bounded_file(ROOT, PREVIOUS_QUALIFICATION[0], 512_000)
    predecessor.require(predecessor.digest(previous_path) == PREVIOUS_QUALIFICATION[1], "predecessor")
    receipt = predecessor.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    predecessor.require(predecessor.digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")
    validate_implementation_sources(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(predecessor.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(predecessor.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: current_workspace_source_qualification_v21.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V21_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V21_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification_v21.py RUN_ID|verify")
