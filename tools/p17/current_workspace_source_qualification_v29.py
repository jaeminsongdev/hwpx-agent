"""Bind the P06-05 current-PC font-metric component over immutable qualification v28."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v28.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v28_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v29-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "99fd2af086e14d3e9d97daa2f01b6408"
BASE_COMMIT = "42aba1cb2539cd5b798c783ac81fb23796d3980e"
RECEIPT_SHA256 = "41a03372ef614af2c4691dfb7a70005e7237dbed4983c694fb3de7f4fbcbdfa9"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v28-20260907/contract.json",
    "55fb75ca03e7331b246d3cc309df84455fa0a32b087a23b73bc7b24ad011091e",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/Cargo.toml",
        "bytes": 594,
        "sha256": "a5aa9d0b462c8935ff41245131f4a4326392bc25ea3395c6ece8c6f170748d9d",
    },
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 7576,
        "sha256": "edc66b299e5ab616c37a55016f8af7427e1fd24d7de9787ee8aad5d13f8695bf",
    },
    {
        "path": "crates/hwpx-package/src/font_metric_receipt.rs",
        "bytes": 15575,
        "sha256": "f1a8680cf0756cc2e740ed99f318be1ee2788f4fb75bd1d0c2d0dd69ef416bd1",
    },
    {
        "path": "crates/hwpx-package/tests/font_metric_receipt.rs",
        "bytes": 9694,
        "sha256": "9a2accfec028a72e0a81326fd78cf9af45b14255c823ef63f12e2e49f7e661df",
    },
    {
        "path": "crates/hwpx-package/examples/p06_05_verify_current_font_metric_receipt.rs",
        "bytes": 2977,
        "sha256": "cbff6648d4bd443d5de3701192c8e909064ac232aad1eb1213468b97aa25f68d",
    },
    {
        "path": "implementation/p06/P06-05_FONT_METRIC_POLICY.md",
        "bytes": 4088,
        "sha256": "2030c266569c149b5c60a61069b46028bc5ac63cc8a215f2ff755ff9f4e34927",
    },
    {
        "path": "implementation/p06/tests/Test-Hancom2020LayoutFontMetric.ps1",
        "bytes": 5567,
        "sha256": "6df8a438f3b4b13586b01be06c636a63c8078c9024e29a2cb8ab7a933cefa35a",
    },
    {
        "path": "implementation/p06/tools/measure-hancom-2020-layout-font.ps1",
        "bytes": 11986,
        "sha256": "7ac81458ce19b9d9b1ea358bb793a50692cc5d67c22dd5202c9da2721360f055",
    },
    {
        "path": "implementation/p06/tools/verify-current-font-metric-receipt.py",
        "bytes": 8649,
        "sha256": "3862b36140b44da82c75267f4d1d78b34a801bafb8ee0c1f5327e399cd045c65",
    },
    {
        "path": "protocol/migrations/p06-font-metric-receipt-v0-to-v1.md",
        "bytes": 1727,
        "sha256": "b5e62e3c919ba9218188fd024e001c80b54cf2addfcc456154974b5b8eb3ad0f",
    },
    {
        "path": "protocol/private/p06-font-metric-receipt-v1.json",
        "bytes": 6601,
        "sha256": "18d59b25a5c5051600f1a0a5076bb675498cb7692b706b14f30cc798bc981ea8",
    },
    {
        "path": "tools/p06/tests/test_font_metric_contract.py",
        "bytes": 3955,
        "sha256": "94607774cb1cce8256b1cf2e7e6f0dfc281c05bfe75ad0582838507f43993b9f",
    },
    {
        "path": "tools/p06/validate_font_metric_contract.py",
        "bytes": 10969,
        "sha256": "7e48953f52555a854369d102d43f78ec48ca4443ce39f2965458da1e63820c5b",
    },
    {
        "path": "tools/p17/run_current_workspace_source_checks.py",
        "bytes": 17423,
        "sha256": "8cc864fd618177323d348ac564d690acc47967c86df065b8cf924c2c0cbbf9a9",
    },
    {
        "path": "tools/p17/tests/test_current_workspace_source_checks.py",
        "bytes": 5657,
        "sha256": "6ad4ed4018a031fccba6af90987869120aca01dfd1809011a4638ea466aee936",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v29.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v29.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V29.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_current_font_metric_component_bound": True,
    "actual_current_pc_installed_font_measurement": True,
    "windows_powershell_5_1_and_powershell_7_equal": True,
    "actual_hangul_renderer": False,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}
HWPX_MANIFEST_SUCCESSOR = {
    "accepted_predecessor_sha256s": [
        "6d3c404804f313b758223d2f21d400066d9b69e8c5df17e3446f36eb34442a73",
        "8ad8656643ccfc352aab4a7db1720e8ea2e911aa2837d0d74b73d9349adc392d",
    ],
    "composition_predecessor_sha256": (
        "6d3c404804f313b758223d2f21d400066d9b69e8c5df17e3446f36eb34442a73"
    ),
    "current_sha256": "a5aa9d0b462c8935ff41245131f4a4326392bc25ea3395c6ece8c6f170748d9d",
    "path": "crates/hwpx-package/Cargo.toml",
}
SUCCESSORS = tuple(
    HWPX_MANIFEST_SUCCESSOR
    if entry["path"] == "crates/hwpx-package/Cargo.toml"
    else entry
    for entry in predecessor.SUCCESSORS
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v29",
        "qualification_id": "p17.current-workspace-source.v29.20260907",
        "scope": "p06_05_current_pc_font_metric_component_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v29",
        "qualification_id": "p17.current-workspace-source.v29.20260907",
        "scope": "p06_05_current_pc_font_metric_component_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v29.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V29_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V29_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
