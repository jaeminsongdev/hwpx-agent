"""Verify immutable v42 durable Git pull source and runtime qualification."""

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

from tools.p17 import frozen_current_source_v41 as predecessor  # noqa: E402
from tools.p17 import frozen_durable_git_mirror_pull_v17 as runtime  # noqa: E402


QUALIFICATION_COMMIT = "f79ad78a1e984622582c620eb2f4f030fb6beeff"
BASE_COMMIT = "dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6"
QUALIFICATION_ID = "p17.current-workspace-source.v42.20260911"
SCOPE = "p17_exact_durable_git_pull_source_and_current_pc_runtime_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v42-20260911/contract.json"
)
CONTRACT_BYTES = 9_748
CONTRACT_SHA256 = "f8e72f7469daa514b2a3119ba32c74c5f99ee76c8fed468f6494bbd915aec052"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v42-20260911/"
    "current-host.json"
)
CURRENT_BYTES = 19_243
CURRENT_SHA256 = "3189b0add9703fac2c0fe993bb4f98ea3719d56bd7f978177a63e1523e7cc188"
PREDECESSOR_RELATIVE = "protocol/private/p17-frozen-current-source-v41-v1.json"
PREDECESSOR_SHA256 = "4bc4dc022804338fddf781b27936ae01197b7db9de79eeb373131b43d11a3f57"
RUN_ID = "75c0595bbf5842d2b417927b96c319f8"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 12_008
RECEIPT_SHA256 = "92fa78d9974df9159d3d4212d04e44688148a9ccb9cd32ad57f59620e4daa71c"
EXPECTED_IMPLEMENTATION_COUNT = 29
EXPECTED_RUNTIME_QUALIFICATION_COUNT = 6
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V42.md",
            "tools/p17/current_workspace_source_qualification_v42.py",
            "tools/p17/tests/test_current_workspace_source_qualification_v42.py",
        )
    )
)
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_durable_pull_verified": True,
    "p17_durable_git_mirror_pull_current_pc_runtime_qualified": True,
    "p17_git_mirror_snapshot_bound_pull_source_bound": True,
    "p17_git_mirror_pull_conflict_preservation_verified": True,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV42Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV42Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
    try:
        return predecessor.git_blob(root, revision, relative, maximum)
    except predecessor.FrozenSourceV41Error as error:
        raise FrozenSourceV42Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        predecessor.verify_commit(root, revision)
    except predecessor.FrozenSourceV41Error as error:
        raise FrozenSourceV42Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        predecessor.require_ancestor(root, ancestor, descendant)
    except predecessor.FrozenSourceV41Error as error:
        raise FrozenSourceV42Error(str(error)) from error


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "json.duplicate")
        result[key] = value
    return result


def json_blob(
    root: Path,
    revision: str,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
) -> dict[str, Any]:
    raw = git_blob(root, revision, relative, 512_000)
    require(len(raw) == expected_bytes, "json.bytes")
    require(digest(raw) == expected_sha256, "json.digest")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceV42Error("json.invalid") from error
    require(isinstance(value, dict), "json.object")
    return value


def validate_locked_sources(
    root: Path,
    revision: str,
    sources: Any,
    expected_count: int,
    code: str,
) -> set[str]:
    require(isinstance(sources, list) and len(sources) == expected_count, f"{code}.count")
    paths: set[str] = set()
    for entry in sources:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in paths
            and type(expected_bytes) is int
            and 0 < expected_bytes <= 4_000_000
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            f"{code}.identity",
        )
        raw = git_blob(root, revision, relative)
        require(len(raw) == expected_bytes, f"{code}.bytes")
        require(digest(raw) == expected_sha256, f"{code}.digest")
        paths.add(relative)
    return paths


def validate_successors(root: Path, successors: Any) -> set[str]:
    require(
        isinstance(successors, list) and len(successors) == EXPECTED_SUCCESSOR_COUNT,
        "successor.count",
    )
    paths: set[str] = set()
    for entry in successors:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "accepted_predecessor_sha256s",
                "composition_predecessor_sha256",
                "current_sha256",
                "path",
            },
            "successor.shape",
        )
        relative = entry.get("path")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        current = entry.get("current_sha256")
        require(
            isinstance(relative, str)
            and relative not in paths
            and isinstance(accepted, list)
            and 0 < len(accepted) <= 8
            and len(set(accepted)) == len(accepted)
            and all(isinstance(value, str) and HEX64.fullmatch(value) for value in accepted)
            and composition in accepted
            and isinstance(current, str)
            and HEX64.fullmatch(current) is not None,
            "successor.identity",
        )
        require(digest(git_blob(root, BASE_COMMIT, relative)) == current, "successor.history")
        paths.add(relative)
    return paths


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("source_commit") == BASE_COMMIT
        and receipt.get("decision") == "PASS"
        and receipt.get("passed") is True
        and receipt.get("check_count") == 11
        and receipt.get("successor_count") == EXPECTED_SUCCESSOR_COUNT
        and receipt.get("cargo_metadata_projection_sha256")
        == "3f12764709ca4d34e3caa17372f7b48ff6e3f1790927fe2299d6e76459510480"
        and receipt.get("cargo_workspace_member_count") == 25,
        "receipt.identity",
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        require(receipt.get(claim) is False, f"receipt.{claim}")


def verify(root: Path = ROOT) -> dict[str, Any]:
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
    require_ancestor(root, BASE_COMMIT, QUALIFICATION_COMMIT)
    try:
        predecessor_result = predecessor.verify(root)
    except predecessor.FrozenSourceV41Error as error:
        raise FrozenSourceV42Error(str(error)) from error
    require(predecessor_result.get("state") == "pass", "predecessor.verify")
    try:
        runtime_result = runtime.verify(root)
    except runtime.FrozenDurableGitPullV17Error as error:
        raise FrozenSourceV42Error(str(error)) from error
    require(
        runtime_result.get("state") == "pass"
        and runtime_result.get("receipt_blob_verified") is True
        and runtime_result.get("actual_authenticated_loopback") is True
        and runtime_result.get("actual_remote_network") is False
        and runtime_result.get("durable_pull") is True
        and runtime_result.get("product_complete") is False,
        "runtime.verify",
    )
    contract = json_blob(
        root,
        QUALIFICATION_COMMIT,
        CONTRACT_RELATIVE,
        CONTRACT_BYTES,
        CONTRACT_SHA256,
    )
    current = json_blob(
        root,
        QUALIFICATION_COMMIT,
        CURRENT_RELATIVE,
        CURRENT_BYTES,
        CURRENT_SHA256,
    )
    receipt = json_blob(
        root,
        QUALIFICATION_COMMIT,
        RECEIPT_RELATIVE,
        RECEIPT_BYTES,
        RECEIPT_SHA256,
    )
    validate_receipt(receipt)
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v42"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v42"
        and current.get("qualification_id") == QUALIFICATION_ID
        and current.get("scope") == SCOPE
        and current.get("base_commit") == BASE_COMMIT,
        "current.identity",
    )
    predecessor_identity = {
        "path": PREDECESSOR_RELATIVE,
        "sha256": PREDECESSOR_SHA256,
    }
    require(contract.get("predecessor") == predecessor_identity, "contract.predecessor")
    require(current.get("predecessor") == predecessor_identity, "current.predecessor")
    require(contract.get("claims") == EXPECTED_CLAIMS, "contract.claims")
    require(current.get("claims") == EXPECTED_CLAIMS, "current.claims")
    require(
        contract.get("evidence")
        == {
            "path": CURRENT_RELATIVE,
            "sha256": CURRENT_SHA256,
            "run_id": RUN_ID,
            "receipt_path": RECEIPT_RELATIVE,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "contract.evidence",
    )
    require(
        current.get("evidence")
        == {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "current.evidence",
    )
    successor_paths = validate_successors(root, receipt.get("successors"))
    require(current.get("source_successors") == receipt.get("successors"), "current.successors")
    implementation_paths = validate_locked_sources(
        root,
        BASE_COMMIT,
        contract.get("implementation_sources"),
        EXPECTED_IMPLEMENTATION_COUNT,
        "implementation",
    )
    require(
        current.get("implementation_sources") == contract.get("implementation_sources"),
        "current.implementation",
    )
    runtime_paths = validate_locked_sources(
        root,
        QUALIFICATION_COMMIT,
        contract.get("runtime_qualification_sources"),
        EXPECTED_RUNTIME_QUALIFICATION_COUNT,
        "runtime",
    )
    require(
        current.get("runtime_qualification_sources")
        == contract.get("runtime_qualification_sources"),
        "current.runtime",
    )
    guard_paths = validate_locked_sources(
        root,
        QUALIFICATION_COMMIT,
        contract.get("guard_sources"),
        EXPECTED_GUARD_COUNT,
        "guard",
    )
    require(tuple(sorted(guard_paths)) == EXPECTED_GUARD_PATHS, "guard.paths")
    return {
        "schema_version": "hwpx-agent.p17-frozen-current-source-v42-verification/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "implementation_source_count": len(implementation_paths),
        "runtime_qualification_source_count": len(runtime_paths),
        "source_successor_count": len(successor_paths),
        "guard_source_count": len(guard_paths),
        "claim_count": len(EXPECTED_CLAIMS),
        "receipt_blob_verified": True,
        "durable_pull_runtime_verified": True,
        "durable_pull": True,
        "actual_remote_network": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v42.py verify")
    try:
        result = verify()
    except FrozenSourceV42Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V42_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
