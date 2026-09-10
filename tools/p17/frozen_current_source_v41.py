"""Verify immutable v41 durable Git push source and runtime qualification."""

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

from tools.p17 import frozen_current_source_v40 as predecessor  # noqa: E402
from tools.p17 import frozen_durable_git_mirror_push_v15 as runtime  # noqa: E402

QUALIFICATION_COMMIT = "162c143d6942a8d648dc25e8986122a61813b8d4"
BASE_COMMIT = "2b0a74e68107931fce9a2a2f6985f5b081ad078f"
QUALIFICATION_ID = "p17.current-workspace-source.v41.20260910"
SCOPE = "p17_exact_durable_git_push_source_and_current_pc_runtime_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v41-20260910/"
    "contract.json"
)
CONTRACT_BYTES = 8271
CONTRACT_SHA256 = "fd4ce9459afe6418633846651e968abdf2068f9f5d722793d53bfdcb98fb5ffe"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v41-20260910/"
    "current-host.json"
)
CURRENT_BYTES = 17766
CURRENT_SHA256 = "28b49140ddf86a237656ef00ce3916089ca636f1a8c59b81303a1ec721c3369c"
PREDECESSOR_RELATIVE = predecessor.CONTRACT_RELATIVE
PREDECESSOR_SHA256 = predecessor.CONTRACT_SHA256
RUN_ID = "f5098f7e6661491a9eaac20e0d8e209b"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 12008
RECEIPT_SHA256 = "59491b32cffdd84f696f580f528d8276cef1dce6f6ff831e2084a24318ac667f"
EXPECTED_IMPLEMENTATION_COUNT = 20
EXPECTED_RUNTIME_QUALIFICATION_COUNT = 6
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = (
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V41.md",
    "tools/p17/current_workspace_source_qualification_v41.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v41.py",
)
EXPECTED_OVERLAP = {"crates/artifact-service/src/store/postgres_repository.rs"}
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_git_mirror_authenticated_dispatch_verified": True,
    "p17_git_mirror_postgresql_state_machine_verified": True,
    "p17_durable_git_mirror_push_current_pc_runtime_qualified": True,
    "p17_current_pc_postgresql_18_4_verified": True,
    "p17_disposable_local_bare_git_push_verified": True,
    "p17_committed_push_recovery_verified": True,
    "p17_divergent_ref_preservation_verified": True,
    "p17_durable_pull_verified": False,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV41Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV41Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
    try:
        return predecessor.git_blob(root, revision, relative, maximum)
    except predecessor.FrozenSourceV40Error as error:
        raise FrozenSourceV41Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        predecessor.verify_commit(root, revision)
    except predecessor.FrozenSourceV40Error as error:
        raise FrozenSourceV41Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        predecessor.require_ancestor(root, ancestor, descendant)
    except predecessor.FrozenSourceV40Error as error:
        raise FrozenSourceV41Error(str(error)) from error


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, member in pairs:
        require(key not in value, "json.duplicate")
        value[key] = member
    return value


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
        raise FrozenSourceV41Error("json.invalid") from error
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
            and isinstance(composition, str)
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
    except predecessor.FrozenSourceV40Error as error:
        raise FrozenSourceV41Error(str(error)) from error
    require(predecessor_result.get("state") == "pass", "predecessor.verify")
    try:
        runtime_result = runtime.verify(root)
    except runtime.FrozenDurableGitPushV15Error as error:
        raise FrozenSourceV41Error(str(error)) from error
    require(
        runtime_result.get("state") == "pass"
        and runtime_result.get("receipt_blob_verified") is True
        and runtime_result.get("actual_authenticated_loopback") is True
        and runtime_result.get("actual_remote_network") is False
        and runtime_result.get("durable_pull") is False
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
    predecessor_identity = {
        "path": PREDECESSOR_RELATIVE,
        "sha256": PREDECESSOR_SHA256,
    }
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v41"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("predecessor") == predecessor_identity,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v41"
        and current.get("qualification_id") == QUALIFICATION_ID
        and current.get("scope") == SCOPE
        and current.get("base_commit") == BASE_COMMIT
        and current.get("predecessor") == predecessor_identity,
        "current.identity",
    )
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
        == {"path": RECEIPT_RELATIVE, "run_id": RUN_ID, "receipt_sha256": RECEIPT_SHA256},
        "current.evidence",
    )
    require(
        current.get("source_successors") == receipt.get("successors"),
        "successor.cross_link",
    )
    successor_paths = validate_successors(root, current.get("source_successors"))
    implementation = contract.get("implementation_sources")
    require(implementation == current.get("implementation_sources"), "implementation.cross_link")
    implementation_paths = validate_locked_sources(
        root, BASE_COMMIT, implementation, EXPECTED_IMPLEMENTATION_COUNT, "implementation"
    )
    runtime_sources = contract.get("runtime_qualification_sources")
    require(
        runtime_sources == current.get("runtime_qualification_sources"),
        "runtime.cross_link",
    )
    runtime_paths = validate_locked_sources(
        root,
        QUALIFICATION_COMMIT,
        runtime_sources,
        EXPECTED_RUNTIME_QUALIFICATION_COUNT,
        "runtime",
    )
    guard_paths = validate_locked_sources(
        root,
        QUALIFICATION_COMMIT,
        contract.get("guard_sources"),
        EXPECTED_GUARD_COUNT,
        "guard",
    )
    require(tuple(sorted(guard_paths)) == EXPECTED_GUARD_PATHS, "guard.paths")
    require(implementation_paths & successor_paths == EXPECTED_OVERLAP, "source.overlap")
    require(not (runtime_paths & implementation_paths), "runtime.overlap")
    require(
        contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "successor.contract_count",
    )
    require(
        digest(git_blob(root, BASE_COMMIT, PREDECESSOR_RELATIVE, 512_000))
        == PREDECESSOR_SHA256,
        "predecessor.history",
    )
    return {
        "schema_version": "hwpx-agent.p17-frozen-current-source-v41-verification/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "implementation_source_count": len(implementation_paths),
        "runtime_qualification_source_count": len(runtime_paths),
        "source_successor_count": len(successor_paths),
        "guard_source_count": len(guard_paths),
        "claim_count": len(EXPECTED_CLAIMS),
        "intentional_overlap": sorted(EXPECTED_OVERLAP),
        "receipt_blob_verified": True,
        "durable_push_runtime_verified": True,
        "durable_pull": False,
        "actual_remote_network": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v41.py verify")
    try:
        result = verify()
    except FrozenSourceV41Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V41_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
