"""Bind exact Hangul-2020 table-shape v2 product sources over immutable v32."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v32.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v32_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v33-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "7783a21d553e45eaab55497fea2b3f1c"
BASE_COMMIT = "5adba7d2b1c98f7e2fa87671f321ff6d599dde48"
RECEIPT_SHA256 = "2239e1722f4a7df6c4c1f79cb3fc95a318ae6bdbfa5d5e3368d8e4e65ae773e2"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v32-20260907/contract.json",
    "e386ea8ab4e390c14356c875529765064900d405ca7737bb8f6f2ff509f0e16f",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/examples/p06_04_preservation_diagnostic.rs",
        "bytes": 2133,
        "sha256": "8a01914315e4fbd23fc91d37318fd94a0740d496750d51e08e924c60b17e2bfe",
    },
    {
        "path": "crates/hwpx-package/examples/p06_04_table_cell_style_target_fixture.rs",
        "bytes": 11956,
        "sha256": "368e6dd081c3fa4811b7c3d44884b370a341bb3c673bb0c4ff2fc890c03b90ba",
    },
    {
        "path": "crates/hwpx-package/src/id_index.rs",
        "bytes": 49511,
        "sha256": "a4c7b2a61689345b2b910c54c2059c4e9119ed38133dcf3bc85a582297a72968",
    },
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 7669,
        "sha256": "1ca7a87040a9c39e72f8691adae717e175bad6db821a94c3b4f513d591977568",
    },
    {
        "path": "crates/hwpx-package/src/preservation.rs",
        "bytes": 19536,
        "sha256": "2b07ad95631e9b1d4dd45e7133e96afad0dbd458b48736db0f89d5f6d2986498",
    },
    {
        "path": "crates/hwpx-package/src/table_cell_style.rs",
        "bytes": 39014,
        "sha256": "6c83c1f2790876f4641f5c2e9567b1e5e05dc9e07e734a2ff235443d79641f78",
    },
    {
        "path": "crates/hwpx-package/tests/id_index.rs",
        "bytes": 16343,
        "sha256": "5445e503cd546f0d7b332653d4b5e86a0a1a0f39c9039af027deda491a67c209",
    },
    {
        "path": "crates/hwpx-package/tests/preservation_map.rs",
        "bytes": 12510,
        "sha256": "ae0173f3abeb4f88daddbbfa2e81f95701622690ff158f1b932fb746ece84acf",
    },
    {
        "path": "crates/hwpx-package/tests/table_cell_style.rs",
        "bytes": 21896,
        "sha256": "351d7e714bd4c730a81b83cdb2a6c46ac3776e9f04e232496c6a37e50a4f7afb",
    },
    {
        "path": "implementation/p06/P06-04_CELL_STYLE_POLICY.md",
        "bytes": 5089,
        "sha256": "ea6221011dd0e5795ee87666d020e9b3f030d00556985e105f5cc146cb52c2d3",
    },
    {
        "path": "protocol/migrations/p06-table-cell-style-v1-to-v2.md",
        "bytes": 1886,
        "sha256": "af8e50a8dab4c03259c4130fe67c9ceaa05e54a179bbb39851fc825efc1013eb",
    },
    {
        "path": "protocol/private/p06-table-cell-style-v2.json",
        "bytes": 5985,
        "sha256": "a4d4ab5cccd647eba18121e8366630a7b24f269a980e074d147b833263ec4696",
    },
    {
        "path": "tools/p06/tests/test_table_cell_style_v2_contract.py",
        "bytes": 4365,
        "sha256": "00748eb90e316be0f566b761106b0ce3faf77b83dd86721191aaf36f3d8c03e7",
    },
    {
        "path": "tools/p06/validate_table_cell_style_v2_contract.py",
        "bytes": 10434,
        "sha256": "1075abfb0dfed00a4124e93246254d1fbc67506ea3dffdb72123f0ffadecb63c",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v33.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v33.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V33.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_04_preservation_preview_profile_v2_bound": True,
    "p06_04_table_id_profile_v2_bound": True,
    "p06_04_cell_style_profile_v2_bound": True,
    "p06_04_v1_default_behavior_preserved": True,
    "p06_04_actual_source_capture_evidence_bound": False,
    "p06_04_product_target_artifact_bound": False,
    "p06_04_product_target_hancom_readback_verified": False,
    "p06_04_product_target_pdf_verified": False,
    "p06_04_complete": False,
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v33",
        "qualification_id": "p17.current-workspace-source.v33.20260907",
        "scope": "p06_04_exact_hancom_2020_observed_shape_v2_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v33",
        "qualification_id": "p17.current-workspace-source.v33.20260907",
        "scope": "p06_04_exact_hancom_2020_observed_shape_v2_source_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v33.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V33_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V33_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
