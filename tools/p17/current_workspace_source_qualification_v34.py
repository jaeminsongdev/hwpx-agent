"""Bind exact P06-05 table-layout v2 product sources over immutable v33."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v33.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v33_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v34-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "8b080b651ade4e5d85701bd47bd9e6b6"
BASE_COMMIT = "84437dd3df2a1679eda2eed7f4ca8125d5ad2e26"
RECEIPT_SHA256 = "8ad2a58f77347e7fde94259b36a59beeb35bc7de9e309b4c31800d55fa8a8977"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v33-20260907/contract.json",
    "329c111bdce1a401e4b221341d5295e4b730c6bb3b917ebd6fb6a201affab297",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/examples/p06_05_table_layout_source_diagnostic.rs",
        "bytes": 3473,
        "sha256": "9b2b10d6ded11f29799e04376b0f10f3f05ef947228ad576f717d3ada17f709f",
    },
    {
        "path": "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs",
        "bytes": 32976,
        "sha256": "6124a5ec554c059eeed8b97df6e1b7269dde40c9e4a890c1a127ca98c3b11597",
    },
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 7732,
        "sha256": "d9f0d3f81e5757bf95f4b6833410f2c5105c3b382fd4d449e266c75c6a923a75",
    },
    {
        "path": "crates/hwpx-package/src/table_layout.rs",
        "bytes": 45657,
        "sha256": "5a0ea2221982371766384536274e1c79e9dba01fa6b2ce2c3d6f56dd5b7329d0",
    },
    {
        "path": "crates/hwpx-package/tests/table_layout.rs",
        "bytes": 18475,
        "sha256": "ad5b4194c779bb8ea679ce6382c9dd1767d1b8c56797e56583021da47cb848a6",
    },
    {
        "path": "implementation/p06/P06-04_TARGET_READBACK_REPORT.md",
        "bytes": 2046,
        "sha256": "0aa66bb33471edfeb67d7b8856f3075e8c8c4f589f1fdf650bb8e03fb8e88348",
    },
    {
        "path": "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md",
        "bytes": 4755,
        "sha256": "0ea904de42376f94766d23fb0545f281b0c9f0bff46ace8677dda821eaba0fc5",
    },
    {
        "path": "implementation/p06/P06-05_TARGET_FIXTURE.md",
        "bytes": 1625,
        "sha256": "6766c887b46503ddd68ddaa5e9365f29d91805ac4ab087a3e4510cde5601a8ca",
    },
    {
        "path": "implementation/p06/tests/Test-Hancom2020TableLayoutReadback.ps1",
        "bytes": 4722,
        "sha256": "88d8281c4ff562acc13146004627e9811502e1e18b22c7ee0919725de15c27ed",
    },
    {
        "path": "implementation/p06/tools/run-hancom-2020-table-layout-readback.ps1",
        "bytes": 1349,
        "sha256": "17f7b99adb0c1ba3cfaf46f6ff7067d1c16c27d3699e12b4fe4550cef782f169",
    },
    {
        "path": "protocol/migrations/p06-table-layout-hwpx-v1-to-v2.md",
        "bytes": 1756,
        "sha256": "f6846c201db701855628de1997f55a64806c96aca9a30c48ab7308a55df5d14a",
    },
    {
        "path": "protocol/private/p06-table-layout-hwpx-v2.json",
        "bytes": 7690,
        "sha256": "6ce63a1ba5749aaa5f593add993bbb4fc68c86ec485837cc4c00e5e5f44a6008",
    },
    {
        "path": "tools/p06/tests/test_table_layout_hwpx_v2_contract.py",
        "bytes": 4354,
        "sha256": "cb75a8e00464d6b22738b384909e5bee5c77369c146c8b266123dd662752867a",
    },
    {
        "path": "tools/p06/validate_table_layout_hwpx_contract.py",
        "bytes": 9426,
        "sha256": "6fb2fb634c9cc4f16c31c34a1d5c7a48050986ae0c46b35967f2c753339ac063",
    },
    {
        "path": "tools/p06/validate_table_layout_hwpx_v2_contract.py",
        "bytes": 10365,
        "sha256": "7d4dc8447a01ebdbd8134722a1cfd85336ea21ca4b7e23cf9f38fe71f1a22df6",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v34.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v34.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V34.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_04_completion_report_source_bound": True,
    "p06_04_actual_artifact_reverified_by_source_qualification": False,
    "p06_04_complete": False,
    "p06_05_table_layout_hwpx_profile_v2_bound": True,
    "p06_05_inner_margin_typed_and_bounded": True,
    "p06_05_font_metric_target_builder_bound": True,
    "p06_05_deterministic_target_report_source_bound": True,
    "p06_05_bounded_hancom_readback_wrapper_bound": True,
    "p06_05_actual_target_hancom_readback_verified": False,
    "p06_05_target_pdf_verified": False,
    "p06_05_complete": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v34",
        "qualification_id": "p17.current-workspace-source.v34.20260907",
        "scope": "p06_05_exact_table_layout_v2_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v34",
        "qualification_id": "p17.current-workspace-source.v34.20260907",
        "scope": "p06_05_exact_table_layout_v2_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v34.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V34_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V34_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
