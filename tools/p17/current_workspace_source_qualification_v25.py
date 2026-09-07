"""Bind exact P06-04 runtime-readback sources over immutable qualification v24."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v24.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v24_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v25-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "3af6a98241e649f4b3f08e943bb2a61f"
BASE_COMMIT = "6d7bf929644cfb8c2ae326c351431df73711a95e"
RECEIPT_SHA256 = "c55d51b40764ecccbfba839f35555d6edd8850a6134994f4d77037b61280c043"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v24-20260907/contract.json",
    "02e12717738bf70bf76ea69da516a583ed06901ed294700c3853e9b0f84e3d19",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "implementation/p06/P06-04_CELL_STYLE_POLICY.md",
        "bytes": 4407,
        "sha256": "ec80e91562487fbc1fcda0979cae66d7ecdb828d81bead9792b2debfaad17367",
    },
    {
        "path": "implementation/p06/tools/run-hancom-2020-cell-style-readback.ps1",
        "bytes": 1351,
        "sha256": "4b408b32bf5c1728e8d22aa0521a0f0b2d7816d27ca6e0076768b80601a5fb55",
    },
    {
        "path": "implementation/p06/tests/Test-Hancom2020CellStyleReadback.ps1",
        "bytes": 4746,
        "sha256": "829a9f4eec68794c46626eb895bf35ca414a4543e7dfad3183c5d02c51cd52ee",
    },
    {
        "path": "protocol/private/p06-table-cell-style-v1.json",
        "bytes": 4791,
        "sha256": "64c6d2a2c3da5cee4da635ed2cea463e1925f1b73027ebd6b7d626238e5e5b34",
    },
    {
        "path": "tools/p06/validate_table_cell_style_contract.py",
        "bytes": 10162,
        "sha256": "20a20110a74e4e7ffe1975f3c3dcb6013f1f94be4b0ea78e8a1a049b9e26d098",
    },
    {
        "path": "tools/p06/tests/test_table_cell_style_contract.py",
        "bytes": 3862,
        "sha256": "a228e299e839214371172d434804ba19b032fadc4baacac790f4661097cccd63",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v25.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v25.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V25.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_cell_style_runtime_readback_sources_bound": True,
    "p06_04_complete": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v25",
        "qualification_id": "p17.current-workspace-source.v25.20260907",
        "scope": "p06_04_table_cell_style_runtime_readback_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v25",
        "qualification_id": "p17.current-workspace-source.v25.20260907",
        "scope": "p06_04_table_cell_style_runtime_readback_source_successor_only",
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
        raise SystemExit("usage: current_workspace_source_qualification_v25.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V25_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V25_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification_v25.py RUN_ID|verify")
