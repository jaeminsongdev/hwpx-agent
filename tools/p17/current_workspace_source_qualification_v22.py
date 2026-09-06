"""Bind the exact P06-02 table operations over immutable source qualification v21."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_foundation() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v20_foundation", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("foundation.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


foundation = load_foundation()

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v22-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "b3105583c99c49878eeeda58e5841567"
BASE_COMMIT = "f0f5c1e162d46993593b1f4a45fc8afd2c620a34"
RECEIPT_SHA256 = "f527e309bc07c6217a63d07cdfa0576b38106e451a0e113e1574ec695d19ea5b"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v21-20260907/contract.json",
    "27d25fb3c6b1ac5f0c2761b054f9c80172534c2450cb619cafdc7ee01dc4fec9",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/domain-ir/src/table_operations.rs",
        "bytes": 22118,
        "sha256": "6207304320b32e90b6b17c4e1f2c2f8524745f047642b533e8631498cc10b965",
    },
    {
        "path": "crates/domain-ir/tests/table_operations.rs",
        "bytes": 14385,
        "sha256": "0e3dbbb67e7803b2d0c819e69387c35c37641f226f0c52bf87c45cfdfebb4b6a",
    },
    {
        "path": "crates/domain-ir/src/lib.rs",
        "bytes": 3281,
        "sha256": "c1ac1b439d8ab4be5f6bb211e45bfbeb909dfb2b80068b794c838c9c2d007aec",
    },
    {
        "path": "protocol/private/p06-table-operations-v1.json",
        "bytes": 3326,
        "sha256": "f4c51abc336265b99113b5f9c699a75327ebdbae3d257397a88da15f509aaf91",
    },
    {
        "path": "protocol/migrations/p06-table-operations-v0-to-v1.md",
        "bytes": 1065,
        "sha256": "52e22e9ff6c645eea42ba31333aa0e150d3d48d93e9bfbbfa3ce77df08ac46ca",
    },
    {
        "path": "implementation/p06/P06-02_TABLE_OPERATIONS_POLICY.md",
        "bytes": 3468,
        "sha256": "d56a0852847c891ffdacd2677f11e689037b58f10302f2462e4dcfea9a72f521",
    },
    {
        "path": "tools/p06/validate_table_operations_contract.py",
        "bytes": 9355,
        "sha256": "b54a9389a2326d0d10e1c2ba5ba2f2390d831f55b88a2a8d1fb4a830215a2e2f",
    },
    {
        "path": "tools/p06/tests/test_table_operations_contract.py",
        "bytes": 4538,
        "sha256": "56950c10aeae066e31e6eca99eb48cc75f503663a968532b0be3ebec73b0a67b",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v22.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v22.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V22.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_operations_v1_sources_bound": True,
    "p06_02_complete": False,
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
    # v21 locked the previous lib.rs. P06-02 intentionally supersedes that export file, so v22
    # composes the immutable v21 contract digest instead of replaying v21 against current bytes.
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v22",
        "qualification_id": "p17.current-workspace-source.v22.20260907",
        "scope": "p06_02_table_operations_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v22",
        "qualification_id": "p17.current-workspace-source.v22.20260907",
        "scope": "p06_02_table_operations_source_successor_only",
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
    if len(sys.argv) != 2:
        raise SystemExit("usage: current_workspace_source_qualification_v22.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V22_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V22_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification_v22.py RUN_ID|verify")
