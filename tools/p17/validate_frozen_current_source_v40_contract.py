"""Validate the private contract for immutable v40 source verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v40 as frozen  # noqa: E402

CONTRACT_RELATIVE = "protocol/private/p17-frozen-current-source-v40-v1.json"
SOURCE_PATHS = (
    "implementation/p17/P17_FROZEN_CURRENT_WORKSPACE_SOURCE_V40.md",
    "protocol/migrations/p17-current-workspace-source-v40-to-frozen-v1.md",
    "tools/p17/frozen_current_source_v39.py",
    "tools/p17/frozen_current_source_v40.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v40.py",
    "tools/p17/tests/test_frozen_current_source_v40.py",
    "tools/p17/tests/test_frozen_current_source_v40_contract.py",
    "tools/p17/validate_frozen_current_source_v40_contract.py",
)
EXPECTED_INVARIANTS = [
    "bounded_git_blob_reads",
    "exact_full_commit_ids",
    "exact_intentional_cargo_lock_overlap",
    "fail_closed_typed_errors",
    "frozen_v39_predecessor_verified",
    "historical_files_from_git_only",
    "legacy_mutable_validators_not_loaded",
    "no_replace_refs_lazy_fetch_or_git_locks",
    "repository_selection_environment_removed",
    "receipt_digest_bound_without_receipt_blob_claim",
]
EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "historical_v40_committed_source_state_verified": True,
    "mutable_worktree_product_sources_authoritative": False,
    "other_pc_or_version": False,
    "p17_06_complete": False,
    "p17_authenticated_dispatch_verified": False,
    "p17_phase_complete": False,
    "p17_postgresql_sync_state_machine_verified": False,
    "p17_remote_network_sync_verified": False,
    "product_complete": False,
    "production": False,
    "receipt_blob_verified": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV40ContractError(ValueError):
    """Fail-closed private-contract error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV40ContractError(code)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, member in pairs:
        require(key not in value, "contract.duplicate")
        value[key] = member
    return value


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    require(type(maximum) is int and 0 < maximum <= 4_000_000, "source.limit")
    try:
        frozen.validate_relative_path(relative)
    except frozen.FrozenSourceV40Error as error:
        raise FrozenSourceV40ContractError("source.path") from error
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "source.link",
        )
    try:
        resolved = cursor.resolve(strict=True)
    except OSError as error:
        raise FrozenSourceV40ContractError("source.file") from error
    require(
        resolved_root in resolved.parents
        and resolved.is_file()
        and 0 < resolved.stat().st_size <= maximum,
        "source.file",
    )
    return resolved


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    raw = bounded_file(root, CONTRACT_RELATIVE, 512_000).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceV40ContractError("contract.json") from error
    require(isinstance(value, dict), "contract.object")
    return value


def validate_document(root: Path, contract: dict[str, Any]) -> None:
    require(
        set(contract)
        == {
            "schema_version",
            "contract_id",
            "scope",
            "qualification",
            "invariants",
            "claims",
            "source_locks",
        },
        "contract.shape",
    )
    require(
        contract.get("schema_version") == "hwpx-agent.p17-frozen-current-source-v40/v1"
        and contract.get("contract_id") == "p17.frozen-current-source.v40.v1"
        and contract.get("scope")
        == "immutable_git_blob_historical_source_qualification_verification",
        "contract.identity",
    )
    require(contract.get("invariants") == EXPECTED_INVARIANTS, "contract.invariants")
    require(contract.get("claims") == EXPECTED_CLAIMS, "contract.claims")
    require(
        contract.get("qualification")
        == {
            "qualification_id": frozen.QUALIFICATION_ID,
            "qualification_commit": frozen.QUALIFICATION_COMMIT,
            "base_commit": frozen.BASE_COMMIT,
            "contract": {
                "path": frozen.CONTRACT_RELATIVE,
                "bytes": frozen.CONTRACT_BYTES,
                "sha256": frozen.CONTRACT_SHA256,
            },
            "current": {
                "path": frozen.CURRENT_RELATIVE,
                "bytes": frozen.CURRENT_BYTES,
                "sha256": frozen.CURRENT_SHA256,
            },
            "predecessor": {
                "path": frozen.PREDECESSOR_RELATIVE,
                "sha256": frozen.PREDECESSOR_SHA256,
            },
            "receipt": {
                "path": frozen.RECEIPT_RELATIVE,
                "sha256": frozen.RECEIPT_SHA256,
                "git_blob_verified": False,
            },
            "implementation_source_count": frozen.EXPECTED_IMPLEMENTATION_COUNT,
            "source_successor_count": frozen.EXPECTED_SUCCESSOR_COUNT,
            "guard_source_count": frozen.EXPECTED_GUARD_COUNT,
            "claim_count": len(frozen.EXPECTED_CLAIMS),
            "intentional_overlap": sorted(frozen.EXPECTED_OVERLAP),
        },
        "contract.qualification",
    )
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        raise FrozenSourceV40ContractError("source.count")
    require(len(locks) == len(SOURCE_PATHS), "source.count")
    observed_paths: list[str] = []
    for entry in locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            "source.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSourceV40ContractError("source.identity")
        require(
            relative not in observed_paths
            and type(expected_bytes) is int
            and 0 < expected_bytes <= 4_000_000
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            "source.identity",
        )
        path = bounded_file(root, relative)
        require(path.stat().st_size == expected_bytes, "source.bytes")
        require(digest(path) == expected_sha256, "source.digest")
        observed_paths.append(relative)
    require(tuple(observed_paths) == SOURCE_PATHS, "source.paths")


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract = load_contract(root)
    validate_document(root, contract)
    history = frozen.verify(root)
    require(
        history.get("state") == "pass"
        and history.get("qualification_id") == frozen.QUALIFICATION_ID
        and history.get("implementation_source_count")
        == frozen.EXPECTED_IMPLEMENTATION_COUNT
        and history.get("source_successor_count") == frozen.EXPECTED_SUCCESSOR_COUNT
        and history.get("guard_source_count") == frozen.EXPECTED_GUARD_COUNT
        and history.get("intentional_overlap") == sorted(frozen.EXPECTED_OVERLAP)
        and history.get("receipt_blob_verified") is False
        and history.get("mutable_worktree_sources_read") is False
        and history.get("actual_hangul") is False
        and history.get("production") is False
        and history.get("product_complete") is False,
        "history.result",
    )
    return contract


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: validate_frozen_current_source_v40_contract.py verify")
    try:
        verified = verify()
    except (FrozenSourceV40ContractError, frozen.FrozenSourceV40Error) as error:
        print(
            f"P17_FROZEN_CURRENT_SOURCE_V40_CONTRACT_FAIL code={error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print(
        "P17_FROZEN_CURRENT_SOURCE_V40_CONTRACT_PASS "
        f"contract={verified['contract_id']} sources={len(verified['source_locks'])}"
    )
