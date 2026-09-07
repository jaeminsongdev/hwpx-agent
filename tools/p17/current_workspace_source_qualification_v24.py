"""Bind exact P06-04 cell-style sources over immutable source qualification v23."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v23.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v23_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v24-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "402b0e3af3f34108b2ab670c70bcdf64"
BASE_COMMIT = "29e96cc54d03f96031cc059b7590846dc1a528ed"
RECEIPT_SHA256 = "00869670774e8ada8c052e8f30c7764c03b90016f33996c126dd4a0c9c45b4b2"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v23-20260907/contract.json",
    "62ed365ab62c367f4c25483a53333c185d34bfcbca09aa60d695da5780184aff",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/src/table_cell_style.rs",
        "bytes": 33039,
        "sha256": "a5ace34b69e0cdff2c2ff4b869d8409fe9d64d49ed2593ecc71d63bbe3fd44f4",
    },
    {
        "path": "crates/hwpx-package/tests/table_cell_style.rs",
        "bytes": 18309,
        "sha256": "ad4b1acfcc153b13ad9f03384d928dd0702948219e9b8de3584dd7097c90b09c",
    },
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 7092,
        "sha256": "5a9096c3ee3fa191c0e56d8bc82d5eb156e257356168dae99715cfb5b0b1e19e",
    },
    {
        "path": "crates/hwpx-package/examples/p06_04_table_cell_style_target_fixture.rs",
        "bytes": 11628,
        "sha256": "2d560be2629b002b7abf6c5a8e85be54b212f4697d8e3dbe021bc966c10bb106",
    },
    {
        "path": "protocol/private/p06-table-cell-style-v1.json",
        "bytes": 4671,
        "sha256": "18467b54bd22698fe29dbd257d6e218176bd39be125c428b687a288ce6bec7d5",
    },
    {
        "path": "protocol/migrations/p06-table-cell-style-v0-to-v1.md",
        "bytes": 1182,
        "sha256": "76f5e03680c81be25f2183c36b15c17c6778a05fb52ec0039903343d2b24b478",
    },
    {
        "path": "implementation/p06/P06-04_CELL_STYLE_POLICY.md",
        "bytes": 4014,
        "sha256": "d9c6654cc160bbae69a0ec5910f1bfbf8cc4e12f649422eb2f7c0df25a3e41a7",
    },
    {
        "path": "implementation/p06/tools/create-hancom-2020-table-source.ps1",
        "bytes": 10291,
        "sha256": "1de233ba43918e7edd1e0d662606b6f456e254974f4352758fd6fb156403fa61",
    },
    {
        "path": "tools/p06/validate_table_cell_style_contract.py",
        "bytes": 9391,
        "sha256": "e122e73e409a91f7e45858276135a80946ca677425590f6e7f7556765883c2cd",
    },
    {
        "path": "tools/p06/tests/test_table_cell_style_contract.py",
        "bytes": 3862,
        "sha256": "a7ad6e612ac6aeb0db166c05617934fa317503f801a890609ced9cd97a3c3f1c",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v24.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v24.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V24.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_cell_style_v1_sources_bound": True,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v24",
        "qualification_id": "p17.current-workspace-source.v24.20260907",
        "scope": "p06_04_table_cell_style_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v24",
        "qualification_id": "p17.current-workspace-source.v24.20260907",
        "scope": "p06_04_table_cell_style_source_successor_only",
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
        raise SystemExit("usage: current_workspace_source_qualification_v24.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V24_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V24_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification_v24.py RUN_ID|verify")
