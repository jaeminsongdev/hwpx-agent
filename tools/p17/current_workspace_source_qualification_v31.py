"""Bind the P06-06 pure FormulaAst component over immutable qualification v30."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v30.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v30_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v31-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "7fe87b6cf5ea435ca8f037559d371b0e"
BASE_COMMIT = "cc925658d2c08e1a67118fc2a1b426f3c9929651"
RECEIPT_SHA256 = "98ca665071096c1c1e95ad919b0b0acbf632cbc8928ea39c0ab63ce5f7ae6481"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v30-20260907/contract.json",
    "fe4523ca2141f99574566ff0197e4ac465c5cadc8e4397ca7276854d84e27357",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/domain-ir/src/lib.rs",
        "bytes": 4445,
        "sha256": "904657bd86827657fee6c82e5a99ad11290777e5d885db35edd31d615d614c4f",
    },
    {
        "path": "crates/domain-ir/src/table_formula.rs",
        "bytes": 55631,
        "sha256": "8fff089ece75d4a0a4efe103d010b0d15705a6d139ba0843f63edf3a50134876",
    },
    {
        "path": "crates/domain-ir/tests/table_formula.rs",
        "bytes": 17463,
        "sha256": "2f4043b39b27e781ab106757ab592517208f7c26489bce1cb84d1fe92247160d",
    },
    {
        "path": "implementation/p06/P06-06_FORMULA_AST_POLICY.md",
        "bytes": 3293,
        "sha256": "b416dad4e346ea9a168f65ece73464e76c7d4c815988691eba61c2bc47a16d14",
    },
    {
        "path": "protocol/migrations/p06-table-formula-v0-to-v1.md",
        "bytes": 1599,
        "sha256": "4f4a0c98100e966fae7ff942d31d556c1dc29b20f3e915d1814e6f011db9c66e",
    },
    {
        "path": "protocol/private/p06-table-formula-v1.json",
        "bytes": 5774,
        "sha256": "5bec3721f4283549af8cd1e7c850600d56ddc4a02a329298cecfa5920d7db0f3",
    },
    {
        "path": "tools/p06/validate_table_formula_contract.py",
        "bytes": 13857,
        "sha256": "f8adad78d86960fea3184f9364f54f842e469f83f320b513f5170dc5a6af7e15",
    },
    {
        "path": "tools/p06/tests/test_table_formula_contract.py",
        "bytes": 4307,
        "sha256": "b1c64cf6f37e8a9a23657a7f09c1be96226b29239f19fb7122d651ad23640d91",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v31.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v31.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V31.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_06_formula_ast_core_bound": True,
    "p06_06_row_column_reference_transform_bound": True,
    "p06_06_exact_grid_formula_cell_readback_bound": True,
    "p06_06_formula_evaluation_verified": False,
    "p06_06_oracle_cache_verified": False,
    "p06_06_hwpx_lowering_verified": False,
    "p06_06_hancom_2020_oracle_verified": False,
    "p06_06_complete": False,
    "p06_04_complete": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v31",
        "qualification_id": "p17.current-workspace-source.v31.20260907",
        "scope": "p06_06_formula_ast_pure_component_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v31",
        "qualification_id": "p17.current-workspace-source.v31.20260907",
        "scope": "p06_06_formula_ast_pure_component_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v31.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V31_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V31_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
