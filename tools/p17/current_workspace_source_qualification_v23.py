"""Bind exact P06-03 merge/split sources over immutable source qualification v22."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = Path(__file__).resolve().with_name("current_workspace_source_qualification_v22.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v22_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v23-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "d39fd169945141d5ae2f968cb0b10b08"
BASE_COMMIT = "0bd152dd85fa42632f8f7213e96e445af44524be"
RECEIPT_SHA256 = "e6ba2648c19874056a22646db9fde8948d89864227d260546ecd40768fb043bf"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v22-20260907/contract.json",
    "2d52898b8d232ea819f4f875a3760ba676dc7d67899f78687987014cead3e176",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/domain-ir/src/table_merge_split.rs",
        "bytes": 41871,
        "sha256": "43dd43780d1de769d126cc2256c9d5c6f33d5e69c37848d203ef6823145b1566",
    },
    {
        "path": "crates/domain-ir/tests/table_merge_split.rs",
        "bytes": 21916,
        "sha256": "c52e3704ef1e34456daee85dd4d9daa15dee29a99246296fe726457d46ded694",
    },
    {
        "path": "crates/domain-ir/src/lib.rs",
        "bytes": 3590,
        "sha256": "6542a3a510f0754eff911d5d441e0688bbcf88c109c96e74b0ba70f8eb1251ca",
    },
    {
        "path": "protocol/private/p06-table-merge-split-v1.json",
        "bytes": 4536,
        "sha256": "df000b5250c7538ff9dfa29e46ea2e737957706cbc242c712370bf287f7f3af7",
    },
    {
        "path": "protocol/migrations/p06-table-merge-split-v0-to-v1.md",
        "bytes": 1300,
        "sha256": "7c53e7de4807e25064a60d8424f95ed6cfa935d0498abc5fa55c487293250f0c",
    },
    {
        "path": "implementation/p06/P06-03_MERGE_SPLIT_POLICY.md",
        "bytes": 4559,
        "sha256": "f461cb931655a6cff94d4a5bc642dafb55575ad73529b3e325565d2a023f6132",
    },
    {
        "path": "tools/p06/validate_table_merge_split_contract.py",
        "bytes": 10950,
        "sha256": "b7eb71560752c8f2b1ea0b589136bd94ad29ec1efe97ac368ed4dd5df920c1f7",
    },
    {
        "path": "tools/p06/tests/test_table_merge_split_contract.py",
        "bytes": 4495,
        "sha256": "41812ebde8cacf45d2006248a4c09103f8411d57fb0dfa3e88834770b2f48bd3",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v23.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v23.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V23.md",
)
CLAIMS = {
    "source_qualification_only": True,
    "p06_table_merge_split_v1_sources_bound": True,
    "p06_03_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}


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
        receipt.get("successors") == list(foundation.SUCCESSORS), "receipt.successors"
    )
    foundation.require(
        receipt.get("successor_count") == len(foundation.SUCCESSORS), "receipt.count"
    )
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == foundation.CARGO_METADATA_PROJECTION_SHA256,
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == foundation.WORKSPACE_MEMBER_COUNT,
        "receipt.members",
    )
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
    # P06-03 supersedes the lib.rs export locked by v22. Compose the immutable v22 contract digest
    # rather than replaying obsolete workspace bytes or rewriting predecessor evidence.
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v23",
        "qualification_id": "p17.current-workspace-source.v23.20260907",
        "scope": "p06_03_table_merge_split_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v23",
        "qualification_id": "p17.current-workspace-source.v23.20260907",
        "scope": "p06_03_table_merge_split_source_successor_only",
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
        "source_successor_count": len(foundation.SUCCESSORS),
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
    if len(sys.argv) != 2:
        raise SystemExit("usage: current_workspace_source_qualification_v23.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V23_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V23_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification_v23.py RUN_ID|verify")
