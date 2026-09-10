"""Validate the private contract for the frozen durable Git push verifier."""

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

from tools.p17 import frozen_durable_git_mirror_push_v15 as frozen  # noqa: E402

CONTRACT_RELATIVE = "protocol/private/p17-frozen-durable-git-mirror-push-v15-v1.json"
SOURCE_PATHS = (
    "implementation/p17/P17_FROZEN_DURABLE_GIT_MIRROR_PUSH_V15.md",
    "protocol/migrations/p17-durable-git-mirror-push-v15-to-frozen-v1.md",
    "tools/p17/frozen_durable_git_mirror_push_v15.py",
    "tools/p17/tests/test_frozen_durable_git_mirror_push_v15.py",
    "tools/p17/tests/test_frozen_durable_git_mirror_push_v15_contract.py",
    "tools/p17/validate_frozen_durable_git_mirror_push_v15_contract.py",
)
EXPECTED_INVARIANTS = [
    "bounded_git_blob_reads",
    "committed_receipt_blob_verified",
    "duplicate_json_keys_rejected",
    "exact_full_commit_ids_and_ancestry",
    "guard_sources_from_qualification_commit",
    "implementation_sources_from_base_commit",
    "legacy_mutable_qualifier_not_loaded",
    "no_replace_refs_lazy_fetch_or_git_locks",
    "repository_selection_environment_removed",
    "typed_bounded_fail_closed_errors",
]
EXPECTED_CLAIMS = {
    "actual_authenticated_loopback": True,
    "actual_current_pc_postgresql_and_local_bare_git": True,
    "actual_remote_network": False,
    "durable_pull": False,
    "historical_v15_qualification_verified": True,
    "mutable_worktree_product_sources_authoritative": False,
    "p17_06_complete": False,
    "persistent_credential_custody": False,
    "production": False,
    "product_complete": False,
    "receipt_blob_verified": True,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenDurableGitPushV15ContractError(ValueError):
    """Fail-closed private-contract error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenDurableGitPushV15ContractError(code)


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
        frozen.gitbase.validate_relative_path(relative)
    except frozen.gitbase.FrozenSourceV40Error as error:
        raise FrozenDurableGitPushV15ContractError("source.path") from error
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
        raise FrozenDurableGitPushV15ContractError("source.file") from error
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
        raise FrozenDurableGitPushV15ContractError("contract.json") from error
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
        contract.get("schema_version")
        == "hwpx-agent.p17-frozen-durable-git-mirror-push-v15/v1"
        and contract.get("contract_id")
        == "p17.frozen-durable-git-mirror-push.v15.v1"
        and contract.get("scope")
        == "immutable_git_blob_current_pc_durable_push_qualification_verification",
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
            "receipt": {
                "path": frozen.RECEIPT_RELATIVE,
                "bytes": frozen.RECEIPT_BYTES,
                "sha256": frozen.RECEIPT_SHA256,
                "git_blob_verified": True,
            },
            "runtime_source_count": frozen.EXPECTED_RUNTIME_COUNT,
            "guard_source_count": frozen.EXPECTED_GUARD_COUNT,
            "check_count": 27,
            "claim_count": len(frozen.EXPECTED_CLAIMS),
        },
        "contract.qualification",
    )
    locks = contract.get("source_locks")
    require(isinstance(locks, list) and len(locks) == len(SOURCE_PATHS), "source.count")
    observed_paths: list[str] = []
    for entry in locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            "source.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in observed_paths
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
        and history.get("receipt_blob_verified") is True
        and history.get("actual_authenticated_loopback") is True
        and history.get("actual_remote_network") is False
        and history.get("durable_pull") is False
        and history.get("production") is False
        and history.get("product_complete") is False
        and history.get("mutable_worktree_sources_read") is False,
        "history.result",
    )
    return contract


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit(
            "usage: validate_frozen_durable_git_mirror_push_v15_contract.py verify"
        )
    try:
        verified = verify()
    except (
        FrozenDurableGitPushV15ContractError,
        frozen.FrozenDurableGitPushV15Error,
    ) as error:
        print(f"P17_FROZEN_DURABLE_GIT_PUSH_V15_CONTRACT_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(
        "P17_FROZEN_DURABLE_GIT_PUSH_V15_CONTRACT_PASS "
        f"contract={verified['contract_id']} sources={len(verified['source_locks'])}"
    )
