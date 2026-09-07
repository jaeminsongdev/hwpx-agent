"""Bind exact P06-05 calibrated target and oracle-contract sources over immutable v35."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v35.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v35_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v36-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "3d1319eb167744489cc5b282f4b41a72"
BASE_COMMIT = "97741561c748e575eaf4c06c47acb4c15a9ab266"
RECEIPT_SHA256 = "932e64ef14546a04186c454b4bbffdc1afd14072d7f0e11ac08e9770fcd0df08"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v35-20260907/contract.json",
    "37a2b79a528cb90b59482286ab7835674e34e2f08dddfed0c71a99dcecec72a1",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/examples/p06_05_table_layout_calibrated_target_fixture.rs",
        "bytes": 20291,
        "sha256": "193958e8b1269895f205c18521526307acb5f9b81f86966a5c51ee8f802571f6",
    },
    {
        "path": "implementation/p06/P06-05_TARGET_READBACK_REPORT.md",
        "bytes": 3535,
        "sha256": "e52bdecbc84852a41110992c89358e74e36ad137da1063b7d5a9551ed6900022",
    },
    {
        "path": "protocol/migrations/p06-table-layout-target-v1-to-v2.md",
        "bytes": 1543,
        "sha256": "97b6453c93360aa078cf5e7ea6c3087eee04ee7b6c1159a977f91af1d05d3291",
    },
    {
        "path": "protocol/private/p06-table-layout-target-v2.json",
        "bytes": 7594,
        "sha256": "c8418b8bb86a1aebd6bce2266f06631142e9683aba5e1172cc168a87b8091be9",
    },
    {
        "path": "tools/p06/tests/test_table_layout_target_v2_contract.py",
        "bytes": 5496,
        "sha256": "2179f915bf5d328388467dba9c7661dbadd45e1f70ea0f2b208ab106c5cc625f",
    },
    {
        "path": "tools/p06/validate_table_layout_target_v2_contract.py",
        "bytes": 24020,
        "sha256": "6f1ea2675aac02d000a24024bfd38b41c32d42923b7e760c4cbcbbcaec47bc7c",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v36.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v36.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V36.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p06_05_calibrated_target_builder_bound": True,
    "p06_05_product_target_contract_v2_bound": True,
    "p06_05_calibration_history_hashes_source_bound": True,
    "p06_05_actual_oracle_hashes_source_bound": True,
    "p06_05_target_v2_validator_source_bound": True,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v36",
        "qualification_id": "p17.current-workspace-source.v36.20260907",
        "scope": "p06_05_calibrated_target_contract_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v36",
        "qualification_id": "p17.current-workspace-source.v36.20260907",
        "scope": "p06_05_calibrated_target_contract_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v36.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V36_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V36_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
