"""Bind exact P06-05 product-target repair sources over immutable v34."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v34.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v34_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v35-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "c8a25b992e9643148c5c8d295ae589b5"
BASE_COMMIT = "73576de75175a63b0f6610580dbda71aa21556eb"
RECEIPT_SHA256 = "83cd3f3a42e317e9db1ce51ae18d4f9e0f3f7203018259d84c558d1c9a3df418"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v34-20260907/contract.json",
    "7bdd50caf207f8c25f10721d7aa930b465834ae48f97ca4471281bb081bb1a12",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs",
        "bytes": 34415,
        "sha256": "96c654e0b063303cde61c9d958f0120fb12e7737b01b3c98d3dcf58632746274",
    },
    {
        "path": "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md",
        "bytes": 5348,
        "sha256": "6cd170202025f3de3a375400009dbea2f0bc4ad585fbdbebf49e7d335b02042e",
    },
    {
        "path": "implementation/p06/P06-05_TARGET_ATTEMPT01_DIAGNOSTIC.md",
        "bytes": 1662,
        "sha256": "8b823232ffb78949ed66f003b028d00bb376d90e89fe71a08f75543000245039",
    },
    {
        "path": "implementation/p06/P06-05_TARGET_FIXTURE.md",
        "bytes": 2592,
        "sha256": "1e228d32fd5406baf2264b8730317ff8e3fd668ad41094cba9ef5b70dd94e8e3",
    },
    {
        "path": "protocol/migrations/p06-table-layout-target-v0-to-v1.md",
        "bytes": 1651,
        "sha256": "dfa26642ac9698d89f415cc6d086af96d28bf41c08ed7c6ea41933a0508f0ac2",
    },
    {
        "path": "protocol/private/p06-table-layout-target-v1.json",
        "bytes": 4960,
        "sha256": "6944329a8846a21960b3c1327be4124f88c0005ba3ed77eb16ec6aef012cddde",
    },
    {
        "path": "tools/p06/tests/test_table_layout_target_contract.py",
        "bytes": 5323,
        "sha256": "c6a1f2e43e217a42ce14576d86c6b83daca8d7594378145361b9232165cde099",
    },
    {
        "path": "tools/p06/validate_table_layout_target_contract.py",
        "bytes": 13290,
        "sha256": "f2a6bf92f4502a1eeb77517cc34900968538123dca70cebada2b6cafe78b8f76",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v35.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v35.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V35.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p06_05_target_builder_v2_bound": True,
    "p06_05_stale_layout_cache_invalidation_bound": True,
    "p06_05_product_target_contract_v1_bound": True,
    "p06_05_attempt01_failed_open_diagnostic_bound": True,
    "p06_05_replacement_target_validator_source_bound": True,
    "p06_05_actual_target_hancom_readback_verified": False,
    "p06_05_target_pdf_verified": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v35",
        "qualification_id": "p17.current-workspace-source.v35.20260907",
        "scope": "p06_05_exact_product_target_repair_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v35",
        "qualification_id": "p17.current-workspace-source.v35.20260907",
        "scope": "p06_05_exact_product_target_repair_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v35.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V35_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V35_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
