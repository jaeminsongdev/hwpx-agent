"""Bind the P06-05 HWPX table-layout adapter over immutable qualification v27."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v27.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v27_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v28-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "52e6bb043715461aac1b22ebc213dbb2"
BASE_COMMIT = "2a9f7e992dc49aea54b02a784e01e0d45cbed4b3"
RECEIPT_SHA256 = "58072df41cdbfd3c71ab207a99d4f917fb18f90edb3e034c517e14aaa7857851"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v27-20260907/contract.json",
    "eb2ca5b661ed303ba9522e401b732606621c2b63c32eaf5f2dfb8ddf6563a222",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "Cargo.lock",
        "bytes": 48909,
        "sha256": "716028407f2ac804f0a57a4e6b85dd499736dc62c6df090bbad73081ae08726e",
    },
    {
        "path": "crates/hwpx-package/Cargo.toml",
        "bytes": 594,
        "sha256": "9d58ced4050fd6d24ff337ebc145c8ad4bacd23c4cc51f129a39b9dba78662ca",
    },
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 7379,
        "sha256": "db779a65f0426e517e9551961b3434e6b205738e6badb023c9a0ef43afedc266",
    },
    {
        "path": "crates/hwpx-package/src/table_layout.rs",
        "bytes": 44233,
        "sha256": "4cd915b9ee0c1455687011370ec31dbfa1ad5f9624cabc3dba5a46c1043ff842",
    },
    {
        "path": "crates/hwpx-package/tests/table_layout.rs",
        "bytes": 17888,
        "sha256": "4431d11b589c91e8dc071a633e65ef85468fb095cf43eeffd98a43e9d0700a26",
    },
    {
        "path": "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md",
        "bytes": 3703,
        "sha256": "33383478ebe1fa36ef05383a3a67b525ca4cd31e6cd6a0d8b456b0e8a6715a5f",
    },
    {
        "path": "protocol/migrations/p06-table-layout-hwpx-v0-to-v1.md",
        "bytes": 1407,
        "sha256": "0aecaaf3ae8514573039d495790e91752960f81633c630a09afbf102cc3f34c4",
    },
    {
        "path": "protocol/private/p06-table-layout-hwpx-v1.json",
        "bytes": 5665,
        "sha256": "ab21dbcb1b646956f5e645ef10ea37c68e6416f9384fc7292bdc565acf8f4092",
    },
    {
        "path": "tools/p06/validate_table_layout_hwpx_contract.py",
        "bytes": 9412,
        "sha256": "606048089c4ab8802c8265c1d3fd5a18afb145bb1ab9098f48261cba63464ea4",
    },
    {
        "path": "tools/p06/tests/test_table_layout_hwpx_contract.py",
        "bytes": 3947,
        "sha256": "347ba73379c456125dab3eac746ec37a06011cc0375d3a9610d934284309e286",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v28.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v28.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V28.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_layout_hwpx_component_bound": True,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}
CARGO_LOCK_SUCCESSOR = {
    "accepted_predecessor_sha256s": [
        "2b4847338a70ca8b749fe0a30d4167d413fd67a1ea49e1c8aa1d49cb1c881d0e",
        "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
        "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
        "8fd1277275366b4e02fcda4750027254d7997062904649c0a2bcd10101550a59",
    ],
    "composition_predecessor_sha256": (
        "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639"
    ),
    "current_sha256": "716028407f2ac804f0a57a4e6b85dd499736dc62c6df090bbad73081ae08726e",
    "path": "Cargo.lock",
}
HWPX_MANIFEST_SUCCESSOR = {
    "accepted_predecessor_sha256s": [
        "6d3c404804f313b758223d2f21d400066d9b69e8c5df17e3446f36eb34442a73",
        "8ad8656643ccfc352aab4a7db1720e8ea2e911aa2837d0d74b73d9349adc392d",
    ],
    "composition_predecessor_sha256": (
        "6d3c404804f313b758223d2f21d400066d9b69e8c5df17e3446f36eb34442a73"
    ),
    "current_sha256": "9d58ced4050fd6d24ff337ebc145c8ad4bacd23c4cc51f129a39b9dba78662ca",
    "path": "crates/hwpx-package/Cargo.toml",
}
SUCCESSORS = tuple(
    sorted(
        [
            CARGO_LOCK_SUCCESSOR if entry["path"] == "Cargo.lock" else entry
            for entry in foundation.SUCCESSORS
        ]
        + [HWPX_MANIFEST_SUCCESSOR],
        key=lambda entry: entry["path"],
    )
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
        receipt.get("successors") == list(SUCCESSORS), "receipt.successors"
    )
    foundation.require(
        receipt.get("successor_count") == len(SUCCESSORS), "receipt.count"
    )
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "706cc008f6ca9a04791cde81491edd328de0ccd4a791ff9e7311f80f6077eaa0",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v28",
        "qualification_id": "p17.current-workspace-source.v28.20260907",
        "scope": "p06_05_hwpx_table_layout_adapter_component_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v28",
        "qualification_id": "p17.current-workspace-source.v28.20260907",
        "scope": "p06_05_hwpx_table_layout_adapter_component_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v28.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V28_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V28_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
