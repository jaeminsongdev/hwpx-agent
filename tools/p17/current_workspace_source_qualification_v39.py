"""Bind exact P06-06 current-PC target-oracle closure sources over immutable v38."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v38.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v38_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v39-20260908"
QUALIFICATION = ROOT / BASE
RUN_ID = "e159d3cf21df48b38bda3f9813d8a0d1"
BASE_COMMIT = "103bbf5b0448076e3f95db939b4d186100b6a4f4"
RECEIPT_SHA256 = "b3d0349d0e0b84900f7200938d8687cbe3b636ffecd62d2670c7197da77815c3"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v38-20260907/contract.json",
    "818e41c4e8ee46eea3b0f31b7d769eb56d19f9de46310ed73e37285cb237ebe0",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/examples/p06_06_table_formula_target_oracle.rs",
        "bytes": 27518,
        "sha256": "c2297d92919bb47cb622dd753508543c1e2ad059421796c56f69e1c6e5abdc9e",
    },
    {
        "path": "implementation/p06/P06-06_TARGET_ATTEMPTS_DIAGNOSTIC.md",
        "bytes": 3667,
        "sha256": "8c70f3dd1cd7dd27e87d1b20cb96a1b378ed3222ad1ff79644b1a77fc3bb2ced",
    },
    {
        "path": "implementation/p06/P06-06_TARGET_READBACK_REPORT.md",
        "bytes": 3969,
        "sha256": "f7eddc72e4d213025ff92131af5ae3d2d230bcfc88bb20d004dcfdfd76d93255",
    },
    {
        "path": "protocol/migrations/p06-table-formula-hwpx-v1-to-target-v2.md",
        "bytes": 1239,
        "sha256": "0a45962acc83880b532219d366b0fd8576b4ffa4d7923a62ebe983e5ad26c4a3",
    },
    {
        "path": "protocol/private/p06-table-formula-target-v2.json",
        "bytes": 11313,
        "sha256": "40eedd2b3cdd377cf60e7204f659d810354dfa9074c25ffe62a7ed11d87f3734",
    },
    {
        "path": "tools/p06/validate_table_formula_target_v2_contract.py",
        "bytes": 44298,
        "sha256": "25ece03a169462666955051a83fd048340ddd6abd4381a79ab21c169ec563f3d",
    },
    {
        "path": "tools/p06/tests/test_table_formula_target_v2_contract.py",
        "bytes": 7453,
        "sha256": "e5215143b86c3e2be455b9add19a0ef7a1d053fe6a0630e8c2732dff7636833b",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v39.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v39.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V39.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p06_06_target_oracle_checker_source_bound": True,
    "p06_06_target_access_diagnostics_source_bound": True,
    "p06_06_target_v2_contract_source_bound": True,
    "p06_06_target_v2_validator_source_bound": True,
    "p06_06_target_v2_tamper_tests_source_bound": True,
    "p06_06_completion_report_source_bound": True,
    "p06_06_actual_oracle_hashes_source_bound": True,
    "p06_06_structural_differential_verified": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v39",
        "qualification_id": "p17.current-workspace-source.v39.20260908",
        "scope": "p06_06_exact_target_oracle_closure_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v39",
        "qualification_id": "p17.current-workspace-source.v39.20260908",
        "scope": "p06_06_exact_target_oracle_closure_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v39.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V39_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V39_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
