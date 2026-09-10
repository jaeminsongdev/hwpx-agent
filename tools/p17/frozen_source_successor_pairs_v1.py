"""Verify historical P16/P17 source-successor pairs without current files."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v39 as frozen  # noqa: E402

ANCHOR_COMMIT = frozen.QUALIFICATION_COMMIT
V12_CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v12-20260907/"
    "contract.json"
)
V12_CONTRACT_BYTES = 19001
V12_CONTRACT_SHA256 = "4a03e390c3973c0ec8f6d7b69c33f0d8961967135b40d217c725d38af6d6a027"
V12_CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v12-20260907/"
    "current-host.json"
)
V12_CURRENT_BYTES = 22987
V12_CURRENT_SHA256 = "e2685452e8418e5b26b1788478d09eef516e73ada54ea092f925a5d390f63a2b"
V12_BASE_COMMIT = "240f270e09ec8e7576d49430f514dbd29e5ce689"
V12_QUALIFICATION_ID = "p17.current-workspace-source.v12.20260907"
P15_CONTRACT_RELATIVE = (
    "implementation/p16/qualification/p15-current-source-v1/contract.json"
)
P15_CONTRACT_BYTES = 13408
P15_CONTRACT_SHA256 = "5391428d584f7be36ed532ea446a07372761fb28bad9446972cef307c35a13e0"
P15_QUALIFICATION_ID = "p16.composed_current_source.p15.v1"
P15_CONTEXTS = {
    "p14_cancel": ("8d03bb6b4fb69e73f8921aa26484b400dadf941b", 1),
    "p15_artifact": ("dde79ff3fa86953c7f3e6e8e2402479eddee813e", 9),
    "p15_auth": ("8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9", 1),
    "p15_async": ("4c6224f6001c5daadaaaec907c0bba86db7c6c0f", 1),
    "p15_error": ("f36a07e988558b4481c50955a0f76bd69c516d9d", 2),
    "p15_handler": ("9e7ed73524be0049292fbdf45f2170df6f997fae", 2),
    "p15_inspector": ("7ea2f84c244fe5bbd7926ba3f176dc5acafcf624", 9),
    "p15_quota": ("e15921a59d45056c46b8ae94b6f6af778746c534", 2),
    "p15_telemetry": ("9f9c6932518175906842a2cbb5915a0fb96d0d49", 3),
    "p16_widget": ("19d1cf775e5702e1150e35624bf616f1dbf9a34c", 2),
}
P15_EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "other_pc_or_version": False,
    "p15_phase_retested": False,
    "p16_phase_complete": False,
    "production": False,
    "registered_host": False,
    "source_qualification_only": True,
}
P16_ARTIFACT_CONTRACT_RELATIVE = (
    "implementation/p16/qualification/postgres-217ba56/contract.json"
)
P16_ARTIFACT_CONTRACT_BYTES = 6_289
P16_ARTIFACT_CONTRACT_SHA256 = (
    "c37e5b773a9117ffdb4af40c95d1263e08fdf7f6e25c69c6daa3108086497530"
)
P16_ARTIFACT_QUALIFICATION_COMMIT = "eb5674edbe2df7a0e239ca9d58f47715feb1796e"
P16_ARTIFACT_SOURCE_COMMIT = "217ba56cd8a88e4d3560a5735052b18880481ff4"
P16_ARTIFACT_QUALIFICATION_ID = "p16.local_postgres_artifact.217ba56"
P16_ARTIFACT_RUNTIME_COUNT = 21
P16_ARTIFACT_GUARD_COUNT = 4
P16_ARTIFACT_CLAIMS = {
    "actual_hangul": False,
    "actual_local_artifact_acceptance": True,
    "durable_plan_or_renderer": False,
    "p15_source_qualification": False,
    "phase_complete": False,
    "production": False,
    "registered_host": False,
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSuccessorPairError(ValueError):
    """Fail-closed historical successor-pair error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSuccessorPairError(code)


def locked_json(
    root: Path,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    code: str,
) -> dict[str, Any]:
    return locked_json_at(
        root,
        ANCHOR_COMMIT,
        relative,
        expected_bytes,
        expected_sha256,
        code,
    )


def locked_json_at(
    root: Path,
    revision: str,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    code: str,
) -> dict[str, Any]:
    raw = frozen.git_blob(root, revision, relative, 512_000)
    require(len(raw) == expected_bytes, f"{code}.bytes")
    require(frozen.digest(raw) == expected_sha256, f"{code}.digest")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSuccessorPairError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def lock_map(source_locks: Iterable[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in source_locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            "lock.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSuccessorPairError("lock.identity")
        if not isinstance(expected, str):
            raise FrozenSuccessorPairError("lock.identity")
        frozen.validate_relative_path(relative)
        require(
            relative not in result
            and isinstance(expected, str)
            and HEX64.fullmatch(expected) is not None,
            "lock.identity",
        )
        result[relative] = expected
    require(len(result) > 0, "lock.empty")
    return result


def checked_path_digests(
    root: Path,
    revision: str,
    entries: Any,
    expected_count: int,
    code: str,
) -> dict[str, str]:
    require(
        isinstance(entries, list) and len(entries) == expected_count,
        f"{code}.count",
    )
    if not isinstance(entries, list):
        raise FrozenSuccessorPairError(f"{code}.entries")
    result: dict[str, str] = {}
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenSuccessorPairError(f"{code}.identity")
        require(
            relative not in result and HEX64.fullmatch(expected) is not None,
            f"{code}.identity",
        )
        raw = frozen.git_blob(root, revision, relative)
        require(frozen.digest(raw) == expected, f"{code}.digest")
        result[relative] = expected
    return result


def p16_artifact_replacements(
    root: Path, source_locks: Iterable[dict[str, Any]]
) -> dict[str, tuple[str, str]]:
    frozen.verify_commit(root, P16_ARTIFACT_SOURCE_COMMIT)
    frozen.verify_commit(root, P16_ARTIFACT_QUALIFICATION_COMMIT)
    frozen.require_ancestor(
        root, P16_ARTIFACT_SOURCE_COMMIT, P16_ARTIFACT_QUALIFICATION_COMMIT
    )
    frozen.require_ancestor(root, P16_ARTIFACT_QUALIFICATION_COMMIT, ANCHOR_COMMIT)
    contract = locked_json_at(
        root,
        P16_ARTIFACT_QUALIFICATION_COMMIT,
        P16_ARTIFACT_CONTRACT_RELATIVE,
        P16_ARTIFACT_CONTRACT_BYTES,
        P16_ARTIFACT_CONTRACT_SHA256,
        "p16.artifact.contract",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.p16-postgres-source-qualification/v1"
        and contract.get("qualification_id") == P16_ARTIFACT_QUALIFICATION_ID
        and contract.get("scope") == "current_pc_source_binding_successor_only"
        and contract.get("audited_source_commit") == P16_ARTIFACT_SOURCE_COMMIT
        and contract.get("claims") == P16_ARTIFACT_CLAIMS,
        "p16.artifact.identity",
    )
    predecessor = contract.get("predecessor")
    require(
        predecessor
        == {
            "path": "implementation/p14/postgres/p14-artifact-service-v1.json",
            "sha256": (
                "92c2cfc91ff9def57649124a196ffddac5d9b68e1899c544e2ebff0abec91c82"
            ),
        },
        "p16.artifact.predecessor",
    )
    runtime = checked_path_digests(
        root,
        P16_ARTIFACT_SOURCE_COMMIT,
        contract.get("runtime_sources"),
        P16_ARTIFACT_RUNTIME_COUNT,
        "p16.artifact.runtime",
    )
    checked_path_digests(
        root,
        P16_ARTIFACT_QUALIFICATION_COMMIT,
        contract.get("guard_sources"),
        P16_ARTIFACT_GUARD_COUNT,
        "p16.artifact.guard",
    )
    evidence = contract.get("evidence")
    require(isinstance(evidence, list) and len(evidence) == 2, "p16.artifact.evidence")
    if not isinstance(evidence, list):
        raise FrozenSuccessorPairError("p16.artifact.evidence")
    for entry in evidence:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "original_receipt_sha256",
                "path",
                "role",
                "run_id",
                "sha256",
            },
            "p16.artifact.evidence.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenSuccessorPairError("p16.artifact.evidence.identity")
        require(
            HEX64.fullmatch(expected) is not None,
            "p16.artifact.evidence.identity",
        )
        raw = frozen.git_blob(root, P16_ARTIFACT_QUALIFICATION_COMMIT, relative)
        require(frozen.digest(raw) == expected, "p16.artifact.evidence.digest")
    locks = lock_map(source_locks)
    replacements = contract.get("replacements")
    require(
        isinstance(replacements, list) and len(replacements) == 3,
        "p16.artifact.replacements",
    )
    if not isinstance(replacements, list):
        raise FrozenSuccessorPairError("p16.artifact.replacements")
    result: dict[str, tuple[str, str]] = {}
    for entry in replacements:
        require(
            isinstance(entry, dict)
            and set(entry) == {"path", "predecessor_sha256", "successor_sha256"},
            "p16.artifact.replacement.shape",
        )
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        if (
            not isinstance(relative, str)
            or not isinstance(before, str)
            or not isinstance(after, str)
        ):
            raise FrozenSuccessorPairError("p16.artifact.replacement.identity")
        require(
            HEX64.fullmatch(before) is not None
            and HEX64.fullmatch(after) is not None
            and before != after
            and relative not in result
            and locks.get(relative) == before
            and runtime.get(relative) == after,
            "p16.artifact.replacement.identity",
        )
        result[relative] = (before, after)
    return result


def v12_source_hashes(root: Path) -> dict[str, str]:
    contract = locked_json(
        root,
        V12_CONTRACT_RELATIVE,
        V12_CONTRACT_BYTES,
        V12_CONTRACT_SHA256,
        "v12.contract",
    )
    current = locked_json(
        root,
        V12_CURRENT_RELATIVE,
        V12_CURRENT_BYTES,
        V12_CURRENT_SHA256,
        "v12.current",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v12"
        and contract.get("qualification_id") == V12_QUALIFICATION_ID
        and contract.get("base_commit") == V12_BASE_COMMIT
        and contract.get("scope") == "current_pc_source_binding_successor_only",
        "v12.identity",
    )
    evidence = contract.get("evidence")
    claims = contract.get("claims")
    require(
        isinstance(evidence, dict)
        and evidence.get("path") == V12_CURRENT_RELATIVE
        and evidence.get("canonical_sha256") == V12_CURRENT_SHA256
        and isinstance(claims, dict)
        and claims.get("source_qualification_only") is True
        and claims.get("actual_hangul") is False
        and claims.get("production") is False
        and claims.get("phase_complete") is False,
        "v12.contract",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v12"
        and current.get("source_commit") == V12_BASE_COMMIT
        and current.get("claims") == claims,
        "v12.current",
    )
    implementation = contract.get("implementation_sources")
    successors = current.get("successors")
    require(
        isinstance(implementation, list)
        and len(implementation) == 107
        and isinstance(successors, list)
        and len(successors) == 14,
        "v12.sources",
    )
    if not isinstance(implementation, list) or not isinstance(successors, list):
        raise FrozenSuccessorPairError("v12.sources")
    result: dict[str, str] = {}
    for entry in implementation:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            "v12.implementation.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSuccessorPairError("v12.implementation.identity")
        if not isinstance(expected, str):
            raise FrozenSuccessorPairError("v12.implementation.identity")
        require(
            relative not in result
            and isinstance(expected, str)
            and HEX64.fullmatch(expected) is not None,
            "v12.implementation.identity",
        )
        result[relative] = expected
    for entry in successors:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "path",
                "accepted_predecessor_sha256s",
                "composition_predecessor_sha256",
                "current_sha256",
            },
            "v12.successor.shape",
        )
        relative = entry.get("path")
        expected = entry.get("current_sha256")
        if not isinstance(relative, str):
            raise FrozenSuccessorPairError("v12.successor.identity")
        if not isinstance(expected, str):
            raise FrozenSuccessorPairError("v12.successor.identity")
        require(
            relative not in result
            and isinstance(expected, str)
            and HEX64.fullmatch(expected) is not None,
            "v12.successor.identity",
        )
        result[relative] = expected
    return result


def v12_replacements(
    root: Path, source_locks: Iterable[dict[str, Any]]
) -> dict[str, tuple[str, str]]:
    qualified = v12_source_hashes(root)
    locks = lock_map(source_locks)
    result: dict[str, tuple[str, str]] = {}
    for relative, predecessor in locks.items():
        successor = qualified.get(relative)
        if successor is None or successor == predecessor:
            continue
        raw = frozen.git_blob(root, V12_BASE_COMMIT, relative)
        require(frozen.digest(raw) == successor, "v12.successor.history")
        result[relative] = (predecessor, successor)
    return result


def history_commits(root: Path, relative: str) -> tuple[str, ...]:
    frozen.validate_relative_path(relative)
    raw = frozen.git_output(
        root,
        ["log", "--format=%H", "--no-renames", ANCHOR_COMMIT, "--", relative],
        64_000,
        "history.log",
    )
    try:
        commits = tuple(raw.decode("ascii").splitlines())
    except UnicodeDecodeError as error:
        raise FrozenSuccessorPairError("history.log") from error
    require(
        0 < len(commits) <= 512
        and len(set(commits)) == len(commits)
        and all(HEX40.fullmatch(commit) for commit in commits),
        "history.commits",
    )
    return commits


@lru_cache(maxsize=256)
def _find_blob_commit(
    root_text: str,
    predecessor_commit: str,
    relative: str,
    expected_sha256: str,
) -> str:
    root = Path(root_text)
    for commit in history_commits(root, relative):
        raw = frozen.git_blob(root, commit, relative)
        if frozen.digest(raw) == expected_sha256:
            frozen.require_ancestor(root, predecessor_commit, commit)
            frozen.require_ancestor(root, commit, ANCHOR_COMMIT)
            return commit
    raise FrozenSuccessorPairError("history.successor_missing")


def root_key(root: Path) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise FrozenSuccessorPairError("root") from error
    require(resolved.is_dir(), "root")
    return str(resolved)


def p15_context_replacements(
    root: Path,
    source_locks: Iterable[dict[str, Any]],
    context: str,
) -> dict[str, tuple[str, str]]:
    context_identity = P15_CONTEXTS.get(context)
    if context_identity is None:
        raise FrozenSuccessorPairError("context.unknown")
    predecessor_commit, expected_count = context_identity
    contract = locked_json(
        root,
        P15_CONTRACT_RELATIVE,
        P15_CONTRACT_BYTES,
        P15_CONTRACT_SHA256,
        "p15.contract",
    )
    require(
        contract.get("schema_version") == "hwpx-agent.p16-p15-source-qualification/v1"
        and contract.get("qualification_id") == P15_QUALIFICATION_ID
        and contract.get("scope") == "current_pc_source_binding_successor_only"
        and contract.get("claims") == P15_EXPECTED_CLAIMS,
        "p15.identity",
    )
    contexts = contract.get("contexts")
    entries = contexts.get(context) if isinstance(contexts, dict) else None
    require(
        isinstance(entries, list) and len(entries) == expected_count, "context.entries"
    )
    if not isinstance(entries, list):
        raise FrozenSuccessorPairError("context.entries")
    locks = lock_map(source_locks)
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        require(
            isinstance(entry, dict)
            and set(entry) == {"path", "predecessor_sha256", "successor_sha256"},
            "context.shape",
        )
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        if not isinstance(relative, str):
            raise FrozenSuccessorPairError("context.identity")
        if not isinstance(before, str) or not isinstance(after, str):
            raise FrozenSuccessorPairError("context.identity")
        require(
            relative not in result
            and isinstance(before, str)
            and HEX64.fullmatch(before) is not None
            and isinstance(after, str)
            and HEX64.fullmatch(after) is not None
            and before != after
            and locks.get(relative) == before,
            "context.identity",
        )
        predecessor_raw = frozen.git_blob(root, predecessor_commit, relative)
        require(frozen.digest(predecessor_raw) == before, "context.predecessor")
        _find_blob_commit(root_key(root), predecessor_commit, relative, after)
        result[relative] = (before, after)
    return result


def clear_cache() -> None:
    _find_blob_commit.cache_clear()


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_source_successor_pairs_v1.py verify")
    try:
        values = v12_source_hashes(ROOT)
        contract = locked_json(
            ROOT,
            P15_CONTRACT_RELATIVE,
            P15_CONTRACT_BYTES,
            P15_CONTRACT_SHA256,
            "p15.contract",
        )
    except (FrozenSuccessorPairError, frozen.FrozenSourceV39Error) as error:
        print(f"P17_FROZEN_SOURCE_SUCCESSOR_PAIRS_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    summary = {
        "schema_version": "hwpx-agent.p17-frozen-source-successor-pairs/v1",
        "state": "pass",
        "v12_source_count": len(values),
        "p15_context_count": len(contract["contexts"]),
        "mutable_worktree_sources_read": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
