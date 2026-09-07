"""Bind the P06-04 active-document source fix over immutable qualification v29."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v29.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v29_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v30-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "c293904577104418951d7370aa0ccbc1"
BASE_COMMIT = "7c49beffa8776e99f3eae9ada0c6f70a5ea2f0e3"
RECEIPT_SHA256 = "f40470ea4951d4b16dfeaa14aceb120d51914653f0bd25dbf2b8dfae17beb741"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v29-20260907/contract.json",
    "bf18ccec5be200cda7a4c00cabe68741adf0e5c01a38d6977bb570fa88299876",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "implementation/p06/tools/create-hancom-2020-table-source.ps1",
        "bytes": 11226,
        "sha256": "29b6e0161fead54b669f0e40dc30d1fa8e10a954612f8df8a97fb6087c5948f5",
    },
    {
        "path": "implementation/p06/tests/Test-Hancom2020CellStyleReadback.ps1",
        "bytes": 5294,
        "sha256": "f0f05b39c934aeb2b558a3aa4b74808fbfce5770d0fb94d94135f19f13abcc3c",
    },
    {
        "path": "tools/p06/validate_table_cell_style_contract.py",
        "bytes": 10536,
        "sha256": "8c0d2e7cd564f6a99a888ad488cfed8f4121d653c37b1e940c44d0675a5f7bd5",
    },
    {
        "path": "protocol/private/p06-table-cell-style-v1.json",
        "bytes": 4832,
        "sha256": "8788b6a5dd96d56d40c9bc3f5dfaf3ea307efdaa5c1ee66700a48dd7cf51ff08",
    },
    {
        "path": "implementation/p06/P06-04_CELL_STYLE_POLICY.md",
        "bytes": 4550,
        "sha256": "0b27b1a7c22e8dcba5a2d8bac2646527412428d91a5f5f54b3fa70ca224b0b25",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v30.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v30.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V30.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_04_active_document_fix_bound": True,
    "p06_04_pre_save_marker_gate_bound": True,
    "diagnostic_attempt03_pass": False,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "actual_hangul_retry": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}
SUCCESSORS = predecessor.SUCCESSORS


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
    foundation.require(receipt.get("successors") == list(SUCCESSORS), "receipt.successors")
    foundation.require(receipt.get("successor_count") == len(SUCCESSORS), "receipt.count")
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "14159fe60a20ba6ee8a4402f1c4c6928a3b2298f44a06c4c8c603c14fff4334f",
        "receipt.cargo",
    )
    foundation.require(receipt.get("cargo_workspace_member_count") == 25, "receipt.members")
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v30",
        "qualification_id": "p17.current-workspace-source.v30.20260907",
        "scope": "p06_04_active_document_source_fix_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v30",
        "qualification_id": "p17.current-workspace-source.v30.20260907",
        "scope": "p06_04_active_document_source_fix_successor_only",
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
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    validate_predecessor(root)
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    foundation.require(foundation.digest(receipt_path(root)) == RECEIPT_SHA256, "receipt.digest")
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
    validate_predecessor(ROOT)
    receipt = foundation.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    foundation.require(foundation.digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")
    validate_implementation_sources(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(foundation.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(foundation.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v30.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V30_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V30_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
