"""Bind exact P06-06 structural target and access diagnostics over immutable v37."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v37.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v37_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v38-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "cbc7c29f6e684595a4c0c3bf49029d48"
BASE_COMMIT = "6e906ae7aa3a77a850c7c95b8cd3bb40795befe6"
RECEIPT_SHA256 = "e8492a60f732c424ca7b2a5316dba6c036bcd10d9030895c0d02d50d4649d951"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v37-20260907/contract.json",
    "f254ed93256a578539a95d64bb425ab29d5cc0af8b0c4d7406d09c02895cefa8",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/src/id_index.rs",
        "bytes": 51424,
        "sha256": "5a6014e211bf26ddedb1f7160b50357429b0394a2bc7a6e66da02c9cad2352d1",
    },
    {
        "path": "crates/hwpx-package/tests/id_index.rs",
        "bytes": 19208,
        "sha256": "f1d3f8979537aceedd4d9804b712947287fa13db150bfc4247d7c75ecd0d768b",
    },
    {
        "path": "crates/hwpx-package/examples/p06_06_table_formula_structural_target_fixture.rs",
        "bytes": 23204,
        "sha256": "89ea28960353b3db43a4974e0557df79b74af61915e0d7112332b0ad6cdefcd9",
    },
    {
        "path": "crates/hwpx-package/examples/p06_06_table_formula_target_oracle.rs",
        "bytes": 17074,
        "sha256": "37a01b2326517ae5fd21eb8da98bff51f54653128ae405f24afe72f115c1dc0c",
    },
    {
        "path": "implementation/p06/tools/run-hancom-2020-formula-target-readback.ps1",
        "bytes": 1359,
        "sha256": "72387acbc71f32bc99ea68e3c99495e550779005e4217886708940fd01095425",
    },
    {
        "path": "implementation/p06/tests/Test-Hancom2020FormulaTargetReadback.ps1",
        "bytes": 5070,
        "sha256": "4e26c156fa3520547f00973be76b5924fb0de4330a16221785060e9a9b96caa3",
    },
    {
        "path": "implementation/p05/tools/invoke-hancom-2020-bounded-readback.ps1",
        "bytes": 20729,
        "sha256": "f13474940e14754a483409d428c814c2c05c6ca9428143aff73337a82f5fcf18",
    },
    {
        "path": "implementation/p05/tests/Test-Hancom2020BoundedReadback.ps1",
        "bytes": 8729,
        "sha256": "720d8127bae05b3f65600da4a55c85671b078c6e069da0f1dd7c5e9ecb147633",
    },
    {
        "path": "implementation/p06/P06-06_TARGET_ATTEMPTS_DIAGNOSTIC.md",
        "bytes": 3371,
        "sha256": "dab86b5259586317dac752c1c175c0d6c0c199e2a95c25733550eae820a4f198",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v38.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v38.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V38.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p06_06_formula_id_profile_source_bound": True,
    "p06_06_structural_target_source_bound": True,
    "p06_06_target_oracle_checker_source_bound": True,
    "p06_06_target_access_diagnostics_source_bound": True,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v38",
        "qualification_id": "p17.current-workspace-source.v38.20260907",
        "scope": "p06_06_structural_target_and_access_diagnostics_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v38",
        "qualification_id": "p17.current-workspace-source.v38.20260907",
        "scope": "p06_06_structural_target_and_access_diagnostics_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v38.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V38_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V38_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
