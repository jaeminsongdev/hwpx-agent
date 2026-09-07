"""Bind exact P06-06 Hangul 2020 formula adapter sources over immutable v36."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v36.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v36_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v37-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "35e5459c8f3f492e81837945fed09247"
BASE_COMMIT = "9814876d3848a173c00035ead14b78c718201720"
RECEIPT_SHA256 = "2d230b29f891f851fc3256b01f027cc5b5ddecdffb5250c167bd5003d17dff4b"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v36-20260907/contract.json",
    "9758f4510a17459e28667aacbe729ee43336729218dea9343dc57dd11c5138ab",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 8006,
        "sha256": "aa7e68f25bbe24391ee8b3f50a37f369944908f6820c0850edd22e91835d268d",
    },
    {
        "path": "crates/hwpx-package/src/table_formula.rs",
        "bytes": 41330,
        "sha256": "f9d802195d3f86fab07b1c0fcbb33131cf37b47db8910d348c6492693c394540",
    },
    {
        "path": "crates/hwpx-package/tests/table_formula.rs",
        "bytes": 11510,
        "sha256": "c279de8ab7e976071446d5fa74d7bb24fc5c39d6383f82aadf03b365eafef5f3",
    },
    {
        "path": "crates/hwpx-package/examples/p06_06_table_formula_source_adapter.rs",
        "bytes": 4992,
        "sha256": "630d7efe3dbd4409378d5eea0519ba4f5131e9bcea7d8e7996f8249ccabc51ce",
    },
    {
        "path": "implementation/p06/P06-06_FORMULA_HWPX_ADAPTER_REPORT.md",
        "bytes": 2805,
        "sha256": "03a9958b36223a252cb45a817dddf4a1eb3376593bc3b48427459d8b94617ea9",
    },
    {
        "path": "protocol/migrations/p06-table-formula-v1-to-hwpx-v1.md",
        "bytes": 1198,
        "sha256": "b0b3a53a66bc497a482780ce358cad546e24e8951ea26187a18f282c41d390b9",
    },
    {
        "path": "protocol/private/p06-table-formula-hwpx-v1.json",
        "bytes": 5766,
        "sha256": "fb1b0b53c51852d0e66999e2634d232885742d725064f065bb8db82a67784e8b",
    },
    {
        "path": "tools/p06/tests/test_table_formula_hwpx_contract.py",
        "bytes": 5090,
        "sha256": "834cd1178aa27b2c65d991eb559170255754ab24edd142b53f6ccd92e26cd148",
    },
    {
        "path": "tools/p06/validate_table_formula_hwpx_contract.py",
        "bytes": 14777,
        "sha256": "1d0b3e7db8b2d51e617dbb80999946b38473ef765c8f03ebeffb382c02b8c439",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v37.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v37.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V37.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p06_06_hwpx_adapter_source_bound": True,
    "p06_06_actual_source_evidence_hashes_bound": True,
    "p06_06_adapter_contract_validator_source_bound": True,
    "p06_06_actual_source_capture_verified": False,
    "p06_06_actual_source_adapter_readback_verified": False,
    "p06_06_product_target_oracle_verified": False,
    "p06_06_complete": False,
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
    return {"path": relative, "bytes": path.stat().st_size, "sha256": foundation.digest(path)}


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
        "actual_hangul", "registered_host", "production", "other_pc_or_version", "phase_complete"
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
    path = foundation.acceptance.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    foundation.require(foundation.digest(path) == PREVIOUS_QUALIFICATION[1], "predecessor")


def expected_current(root: Path) -> dict[str, Any]:
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v37",
        "qualification_id": "p17.current-workspace-source.v37.20260907",
        "scope": "p06_06_hancom_2020_formula_adapter_source_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {"path": PREVIOUS_QUALIFICATION[0], "sha256": PREVIOUS_QUALIFICATION[1]},
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v37",
        "qualification_id": "p17.current-workspace-source.v37.20260907",
        "scope": "p06_06_hancom_2020_formula_adapter_source_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {"path": PREVIOUS_QUALIFICATION[0], "sha256": PREVIOUS_QUALIFICATION[1]},
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
    current_path = foundation.acceptance.bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = foundation.acceptance.bounded_file(root, f"{BASE}/contract.json", 512_000)
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
    usage = "usage: current_workspace_source_qualification_v37.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V37_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V37_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
