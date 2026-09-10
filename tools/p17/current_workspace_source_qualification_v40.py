"""Bind the exact P17 Git mirror effect sources over immutable v39."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def load_predecessor() -> Any:
    path = (
        Path(__file__)
        .resolve()
        .with_name("current_workspace_source_qualification_v39.py")
    )
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_v39_predecessor", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("predecessor.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


predecessor = load_predecessor()
foundation = predecessor.foundation

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v40-20260910"
QUALIFICATION = ROOT / BASE
RUN_ID = "2fc12885ddb14122a677a65db9f4c098"
BASE_COMMIT = "131ce732e59f2360a713a14391bbff45d1dbde73"
RECEIPT_SHA256 = "a477de4698193379a3c4101d1ddf182c08353be6afade4c51e1bcebba7602151"
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/"
    "current-workspace-source-v39-20260908/contract.json",
    "544c68cdea536e234139bd492f7e2812fe1b7ab02826af580f307284835f287c",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "Cargo.lock",
        "bytes": 48922,
        "sha256": "142a53feab1aab70e7ea0ab2c08fd78b171e822142c5312b34e77d1ef67455a4",
    },
    {
        "path": "crates/remote-sync-host/Cargo.toml",
        "bytes": 962,
        "sha256": "482cf86671cd905ed9bfc8820ab2eac1e2e94b72215202e9b93666a4d6fbf3a0",
    },
    {
        "path": "crates/remote-sync-host/src/lib.rs",
        "bytes": 48141,
        "sha256": "28be7741ae3aeb8283c00c50b97bf8e2d55556d37369f84c3f9cd6edbcd80ec4",
    },
    {
        "path": "crates/remote-sync-host/src/git_mirror.rs",
        "bytes": 34370,
        "sha256": "2f1a86a8d0159a09a429ac4af11960aa43e2686a1351b9f17f501d303b631cb1",
    },
    {
        "path": "crates/remote-sync-host/tests/git_mirror_effect.rs",
        "bytes": 13568,
        "sha256": "0090f2820f822cf46cf7f04d6601c939a69544d107a8d53fe78eedbae264bed7",
    },
    {
        "path": "protocol/private/p17-git-mirror-effect-v1.json",
        "bytes": 2612,
        "sha256": "c1d466347e50e041afac3e2bfc3ffb26b7245a2b3e0de37cb499595d82b21298",
    },
    {
        "path": "implementation/p17/P17-06_GIT_MIRROR_EFFECT_V13.md",
        "bytes": 2737,
        "sha256": "08a8d4553186aa600aee516a820e4ba7448a589d50e9a220da71b0441e935616",
    },
    {
        "path": "tools/p17/validate_git_mirror_effect_contract.py",
        "bytes": 4756,
        "sha256": "79d5ebf33efbabc5f8a2ea0c305200d07fc272b8f0ee7f1b607605d9905576b5",
    },
    {
        "path": "tools/p17/tests/test_git_mirror_effect_contract.py",
        "bytes": 2463,
        "sha256": "102c4fbae60f944e186a31793d3bfd7552d4a750acae730494a32e1d9fb7a067",
    },
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v40.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v40.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V40.md",
)
CLAIMS = {
    **predecessor.CLAIMS,
    "p17_git_mirror_component_source_bound": True,
    "p17_git_mirror_current_pc_local_bare_git_report_source_bound": True,
    "p17_git_mirror_durable_plan_source_bound": True,
    "p17_git_mirror_contract_and_tamper_tests_source_bound": True,
    "p17_git_mirror_authenticated_dispatch_verified": False,
    "p17_git_mirror_postgresql_state_machine_verified": False,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
    "p06_phase_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}

CARGO_LOCK_SUCCESSOR: dict[str, Any] = {
    "accepted_predecessor_sha256s": [
        "2b4847338a70ca8b749fe0a30d4167d413fd67a1ea49e1c8aa1d49cb1c881d0e",
        "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
        "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
        "8fd1277275366b4e02fcda4750027254d7997062904649c0a2bcd10101550a59",
    ],
    "composition_predecessor_sha256": (
        "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639"
    ),
    "current_sha256": (
        "142a53feab1aab70e7ea0ab2c08fd78b171e822142c5312b34e77d1ef67455a4"
    ),
    "path": "Cargo.lock",
}
ARTIFACT_REPOSITORY_SUCCESSOR: dict[str, Any] = {
    "accepted_predecessor_sha256s": [
        "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
    ],
    "composition_predecessor_sha256": (
        "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
    ),
    "current_sha256": (
        "5501b4a8ec29f89ace16ebef7a978443ee45597a226b246cdf68601d3f82ca44"
    ),
    "path": "crates/artifact-service/src/store/postgres_repository.rs",
}
ARTIFACT_MIGRATION_SUCCESSOR: dict[str, Any] = {
    "accepted_predecessor_sha256s": [
        "6b3b050e64af2c54f4847c781ca6439afedf3bfab526094d7693811d64ba511a"
    ],
    "composition_predecessor_sha256": (
        "6b3b050e64af2c54f4847c781ca6439afedf3bfab526094d7693811d64ba511a"
    ),
    "current_sha256": (
        "3bccf326ea1b616bac9c175956986ffc110ccc672474a3cc3f957fc0800f9beb"
    ),
    "path": "tools/p14/validate_artifact_service_migration.py",
}
CANCEL_CLEANUP_SUCCESSOR: dict[str, Any] = {
    "accepted_predecessor_sha256s": [
        "0e55cd4b00a1d670b1c31238fc69e9933db68e52c95a41ec18bb709c0be128c0",
        "b1b6f3ae67d28ac42e5cdd18d7dcc787f8f7fcfd59dcdf9f441d095d5eaf10da",
    ],
    "composition_predecessor_sha256": (
        "0e55cd4b00a1d670b1c31238fc69e9933db68e52c95a41ec18bb709c0be128c0"
    ),
    "current_sha256": (
        "e8327d846f319148edf7e94f222cfd731a37f3e83176c7789b846b6c2b41aecb"
    ),
    "path": "tools/p14/validate_cancel_cleanup.py",
}
SUCCESSOR_REPLACEMENTS: dict[str, dict[str, Any]] = {
    CARGO_LOCK_SUCCESSOR["path"]: CARGO_LOCK_SUCCESSOR,
    ARTIFACT_REPOSITORY_SUCCESSOR["path"]: ARTIFACT_REPOSITORY_SUCCESSOR,
}


def replace_successor(entry: dict[str, Any]) -> dict[str, Any]:
    path = entry["path"]
    return SUCCESSOR_REPLACEMENTS[path] if path in SUCCESSOR_REPLACEMENTS else entry


SUCCESSORS: tuple[dict[str, Any], ...] = tuple(
    sorted(
        [replace_successor(entry) for entry in predecessor.SUCCESSORS]
        + [ARTIFACT_MIGRATION_SUCCESSOR, CANCEL_CLEANUP_SUCCESSOR],
        key=lambda entry: entry["path"],
    )
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
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    foundation.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    foundation.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    foundation.require(receipt.get("decision") == "PASS", "receipt.decision")
    foundation.require(receipt.get("passed") is True, "receipt.passed")
    foundation.require(receipt.get("check_count") == 11, "receipt.checks")
    foundation.require(
        receipt.get("successors") == list(SUCCESSORS), "receipt.successors"
    )
    foundation.require(
        receipt.get("successor_count") == len(SUCCESSORS), "receipt.count"
    )
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "3f12764709ca4d34e3caa17372f7b48ff6e3f1790927fe2299d6e76459510480",
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == 25, "receipt.members"
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
        foundation.require(
            path.stat().st_size == entry["bytes"], "implementation.bytes"
        )
        foundation.require(
            foundation.digest(path) == entry["sha256"], "implementation.digest"
        )
        foundation.require(
            foundation.git_digest(root, BASE_COMMIT, relative) == entry["sha256"],
            "implementation.history",
        )


def validate_predecessor(root: Path) -> None:
    path = foundation.acceptance.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    foundation.require(
        foundation.digest(path) == PREVIOUS_QUALIFICATION[1], "predecessor"
    )


def expected_current(root: Path) -> dict[str, Any]:
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v40",
        "qualification_id": "p17.current-workspace-source.v40.20260910",
        "scope": "p17_exact_git_mirror_effect_source_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v40",
        "qualification_id": "p17.current-workspace-source.v40.20260910",
        "scope": "p17_exact_git_mirror_effect_source_successor_only",
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
    foundation.require(
        contract == expected_contract(root, current_path), "contract.identity"
    )
    return contract


def qualify() -> tuple[Path, Path]:
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
    contract_path.write_bytes(
        foundation.canonical(expected_contract(ROOT, current_path))
    )
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v40.py RUN_ID|verify"
    if len(sys.argv) != 2:
        raise SystemExit(usage)
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V40_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V40_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
