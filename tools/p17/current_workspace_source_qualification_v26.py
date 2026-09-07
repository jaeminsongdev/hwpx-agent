"""Bind the P06-04 canonical text-evidence fix over immutable qualification v25."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v25.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v25_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v26-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "3abc86939089473f972cb09a5e1bce57"
BASE_COMMIT = "2d18ae2ca704797819be7f749e21b1dc1bfd53ac"
RECEIPT_SHA256 = "05b1f716356fbd358a6ab353c43beb0f977ab8e273f1da44eedd7a3c65d7b33c"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v25-20260907/contract.json",
    "408c8531ed2775f45cb13f20f65edf1eead6ac4363cf5201c9e0589aba671393",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "implementation/p06/tools/create-hancom-2020-table-source.ps1",
        "bytes": 10685,
        "sha256": "768261eb9cf7daea6c648d99cfec3b7d0e8ab614f8057a482754b77e0e0fe84c",
    },
    {
        "path": "tools/p06/validate_table_cell_style_contract.py",
        "bytes": 10253,
        "sha256": "2e72706f9a87734cc324de83a93ee342ad11aff08965cd9ce12956d51fe6620d",
    },
    {
        "path": "tools/p06/tests/test_table_cell_style_contract.py",
        "bytes": 4445,
        "sha256": "a1969177bf1ed58e595dcbe4362ca9c681ed22ea173c27f11010ebe6f7904d21",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v26.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v26.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V26.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_source_text_digest_canonicalized": True,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v26",
        "qualification_id": "p17.current-workspace-source.v26.20260907",
        "scope": "p06_04_table_source_canonical_text_evidence_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v26",
        "qualification_id": "p17.current-workspace-source.v26.20260907",
        "scope": "p06_04_table_source_canonical_text_evidence_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v26.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V26_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V26_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
