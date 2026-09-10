"""Verify the immutable v40 source qualification without mutable validators."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v39 as predecessor  # noqa: E402

QUALIFICATION_COMMIT = "7167e0e1a14c6075f57608acd7ff89bd3d14a060"
BASE_COMMIT = "131ce732e59f2360a713a14391bbff45d1dbde73"
QUALIFICATION_ID = "p17.current-workspace-source.v40.20260910"
SCOPE = "p17_exact_git_mirror_effect_source_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v40-20260910/"
    "contract.json"
)
CONTRACT_BYTES = 5064
CONTRACT_SHA256 = "9b7cd7d3d2eda9cf3cd8bff2e9bc67f94a8a62f60a3701bfcdc53b0cd1f08c3d"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v40-20260910/"
    "current-host.json"
)
CURRENT_BYTES = 14559
CURRENT_SHA256 = "ec98c23d9a819752631dcb0e56fcd5bf45ff6e9586dce993d7dbaba3f92e847a"
PREDECESSOR_RELATIVE = predecessor.CONTRACT_RELATIVE
PREDECESSOR_SHA256 = predecessor.CONTRACT_SHA256
RUN_ID = "2fc12885ddb14122a677a65db9f4c098"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_SHA256 = "a477de4698193379a3c4101d1ddf182c08353be6afade4c51e1bcebba7602151"
MAX_BLOB_BYTES = 4_000_000
REPOSITORY_ENVIRONMENT_KEYS = predecessor.REPOSITORY_ENVIRONMENT_KEYS
EXPECTED_IMPLEMENTATION_COUNT = 9
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = (
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V40.md",
    "tools/p17/current_workspace_source_qualification_v40.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v40.py",
)
EXPECTED_OVERLAP = {"Cargo.lock"}
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_git_mirror_component_source_bound": True,
    "p17_git_mirror_current_pc_local_bare_git_report_source_bound": True,
    "p17_git_mirror_durable_plan_source_bound": True,
    "p17_git_mirror_contract_and_tamper_tests_source_bound": True,
    "p17_git_mirror_authenticated_dispatch_verified": False,
    "p17_git_mirror_postgresql_state_machine_verified": False,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV40Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV40Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_revision(revision: str) -> str:
    require(
        isinstance(revision, str) and HEX40.fullmatch(revision) is not None,
        "revision",
    )
    return revision


def validate_relative_path(relative: str) -> str:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path",
    )
    return relative


def git_output(root: Path, arguments: list[str], maximum: int, code: str) -> bytes:
    try:
        return predecessor.git_output(root, arguments, maximum, code)
    except predecessor.FrozenSourceV39Error as error:
        raise FrozenSourceV40Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    validate_revision(revision)
    raw = git_output(
        root, ["rev-parse", "--verify", f"{revision}^{{commit}}"], 64, "commit"
    )
    try:
        observed = raw.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise FrozenSourceV40Error("commit") from error
    require(observed == revision, "commit")


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    validate_revision(ancestor)
    validate_revision(descendant)
    git_output(
        root,
        ["merge-base", "--is-ancestor", ancestor, descendant],
        0,
        "commit.ancestry",
    )


def git_blob(
    root: Path,
    revision: str,
    relative: str,
    maximum: int = MAX_BLOB_BYTES,
) -> bytes:
    validate_revision(revision)
    validate_relative_path(relative)
    require(type(maximum) is int and 0 < maximum <= MAX_BLOB_BYTES, "blob.limit")
    specification = f"{revision}:{relative}"
    size_raw = git_output(root, ["cat-file", "-s", specification], 32, "blob.size")
    try:
        size_text = size_raw.decode("ascii").strip()
        size = int(size_text)
    except (UnicodeDecodeError, ValueError) as error:
        raise FrozenSourceV40Error("blob.size") from error
    require(size_text.isdecimal() and 0 < size <= maximum, "blob.size")
    raw = git_output(root, ["cat-file", "blob", specification], maximum, "blob.read")
    require(len(raw) == size, "blob.bytes")
    return raw


def json_blob(
    root: Path,
    revision: str,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
) -> dict[str, Any]:
    require(
        type(expected_bytes) is int
        and 0 < expected_bytes <= 512_000
        and isinstance(expected_sha256, str)
        and HEX64.fullmatch(expected_sha256) is not None,
        "json.lock",
    )
    raw = git_blob(root, revision, relative, 512_000)
    require(len(raw) == expected_bytes, "json.bytes")
    require(digest(raw) == expected_sha256, "json.digest")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceV40Error("json.decode") from error
    require(isinstance(value, dict), "json.object")
    return value


def validate_locked_sources(
    root: Path,
    revision: str,
    entries: Any,
    expected_count: int,
    code: str,
) -> set[str]:
    require(
        isinstance(entries, list) and len(entries) == expected_count,
        f"{code}.count",
    )
    seen: set[str] = set()
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSourceV40Error(f"{code}.identity")
        require(
            relative not in seen
            and type(expected_bytes) is int
            and 0 < expected_bytes <= MAX_BLOB_BYTES
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            f"{code}.identity",
        )
        validate_relative_path(relative)
        raw = git_blob(root, revision, relative)
        require(len(raw) == expected_bytes, f"{code}.bytes")
        require(digest(raw) == expected_sha256, f"{code}.digest")
        seen.add(relative)
    return seen


def validate_successors(root: Path, entries: Any) -> set[str]:
    require(
        isinstance(entries, list) and len(entries) == EXPECTED_SUCCESSOR_COUNT,
        "successor.count",
    )
    seen: set[str] = set()
    for entry in entries:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "path",
                "accepted_predecessor_sha256s",
                "composition_predecessor_sha256",
                "current_sha256",
            },
            "successor.shape",
        )
        relative = entry.get("path")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        current = entry.get("current_sha256")
        if not isinstance(relative, str):
            raise FrozenSourceV40Error("successor.identity")
        require(
            relative not in seen
            and isinstance(accepted, list)
            and len(accepted) > 0
            and accepted == sorted(set(accepted))
            and all(
                isinstance(value, str) and HEX64.fullmatch(value) for value in accepted
            )
            and isinstance(composition, str)
            and composition in accepted
            and isinstance(current, str)
            and HEX64.fullmatch(current) is not None,
            "successor.identity",
        )
        validate_relative_path(relative)
        require(
            digest(git_blob(root, BASE_COMMIT, relative)) == current,
            "successor.history",
        )
        seen.add(relative)
    return seen


def verify(root: Path = ROOT) -> dict[str, Any]:
    try:
        previous = predecessor.verify(root)
    except predecessor.FrozenSourceV39Error as error:
        raise FrozenSourceV40Error("predecessor.verify") from error
    require(
        previous.get("state") == "pass"
        and previous.get("qualification_id") == predecessor.QUALIFICATION_ID,
        "predecessor.verify",
    )
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
    require_ancestor(root, predecessor.QUALIFICATION_COMMIT, BASE_COMMIT)
    require_ancestor(root, BASE_COMMIT, QUALIFICATION_COMMIT)

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
    require(
        set(contract)
        == {
            "base_commit",
            "claims",
            "evidence",
            "guard_sources",
            "implementation_sources",
            "predecessor",
            "qualification_id",
            "schema_version",
            "scope",
            "source_successor_count",
        },
        "contract.shape",
    )
    require(
        set(current)
        == {
            "base_commit",
            "claims",
            "evidence",
            "implementation_sources",
            "predecessor",
            "qualification_id",
            "schema_version",
            "scope",
            "source_successors",
        },
        "current.shape",
    )
    predecessor_identity = {
        "path": PREDECESSOR_RELATIVE,
        "sha256": PREDECESSOR_SHA256,
    }
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v40"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("predecessor") == predecessor_identity,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v40"
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
        == {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "current.evidence",
    )
    validate_relative_path(RECEIPT_RELATIVE)
    require(
        digest(git_blob(root, BASE_COMMIT, PREDECESSOR_RELATIVE, 512_000))
        == PREDECESSOR_SHA256,
        "predecessor.history",
    )

    implementation = contract.get("implementation_sources")
    require(
        implementation == current.get("implementation_sources"),
        "implementation.cross_link",
    )
    implementation_paths = validate_locked_sources(
        root,
        BASE_COMMIT,
        implementation,
        EXPECTED_IMPLEMENTATION_COUNT,
        "implementation",
    )
    successor_paths = validate_successors(root, current.get("source_successors"))
    require(
        implementation_paths & successor_paths == EXPECTED_OVERLAP, "source.overlap"
    )
    require(
        contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "successor.contract_count",
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
        "schema_version": "hwpx-agent.p17-frozen-current-source-v40-verification/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "contract_sha256": CONTRACT_SHA256,
        "current_sha256": CURRENT_SHA256,
        "implementation_source_count": len(implementation_paths),
        "source_successor_count": len(successor_paths),
        "guard_source_count": len(guard_paths),
        "claim_count": len(EXPECTED_CLAIMS),
        "intentional_overlap": sorted(EXPECTED_OVERLAP),
        "receipt_reference_bound": True,
        "receipt_blob_verified": False,
        "mutable_worktree_sources_read": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v40.py verify")
    try:
        result = verify()
    except FrozenSourceV40Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V40_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
