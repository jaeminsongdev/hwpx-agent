"""Verify current-workspace source qualifications v20-v39 from Git history."""

from __future__ import annotations

import copy
from functools import lru_cache
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v39 as frozen  # noqa: E402

FIRST_VERSION = 20
LAST_VERSION = 39
EXPECTED_VERSIONS = tuple(range(FIRST_VERSION, LAST_VERSION + 1))
EXPECTED_V20_PREDECESSOR_COUNT = 7
EXPECTED_V20_IMPLEMENTATION_COUNT = 118
EXPECTED_V20_SUCCESSOR_COUNT = 25
EXPECTED_V20_GUARD_COUNT = 4
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceHistoryError(ValueError):
    """Fail-closed history error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceHistoryError(code)


def qualification_date(version: int) -> str:
    return "20260908" if version == 39 else "20260907"


def contract_relative(version: int) -> str:
    return (
        "implementation/p17/qualification/"
        f"current-workspace-source-v{version}-{qualification_date(version)}/"
        "contract.json"
    )


def current_relative(version: int) -> str:
    return (
        contract_relative(version).removesuffix("contract.json") + "current-host.json"
    )


def qualification_id(version: int) -> str:
    return f"p17.current-workspace-source.v{version}.{qualification_date(version)}"


def load_json(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceHistoryError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def checked_blob(
    root: Path,
    revision: str,
    relative: str,
    expected_sha256: str,
    code: str,
    expected_bytes: int | None = None,
) -> bytes:
    require(
        isinstance(expected_sha256, str)
        and HEX64.fullmatch(expected_sha256) is not None,
        f"{code}.lock",
    )
    raw = frozen.git_blob(root, revision, relative)
    if expected_bytes is not None:
        require(
            type(expected_bytes) is int
            and expected_bytes > 0
            and len(raw) == expected_bytes,
            f"{code}.bytes",
        )
    require(frozen.digest(raw) == expected_sha256, f"{code}.digest")
    return raw


def checked_source_locks(
    root: Path,
    revision: str,
    entries: Any,
    code: str,
) -> dict[str, dict[str, Any]]:
    require(isinstance(entries, list) and len(entries) > 0, f"{code}.entries")
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSourceHistoryError(f"{code}.identity")
        if not isinstance(expected_sha256, str):
            raise FrozenSourceHistoryError(f"{code}.identity")
        if type(expected_bytes) is not int:
            raise FrozenSourceHistoryError(f"{code}.identity")
        require(relative not in result, f"{code}.duplicate")
        checked_blob(
            root,
            revision,
            relative,
            expected_sha256,
            code,
            expected_bytes,
        )
        result[relative] = copy.deepcopy(entry)
    return result


def checked_successors(
    root: Path,
    revision: str,
    entries: Any,
    code: str,
) -> dict[str, dict[str, Any]]:
    require(isinstance(entries, list) and len(entries) > 0, f"{code}.entries")
    result: dict[str, dict[str, Any]] = {}
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
            f"{code}.shape",
        )
        relative = entry.get("path")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        current = entry.get("current_sha256")
        if not isinstance(relative, str):
            raise FrozenSourceHistoryError(f"{code}.identity")
        if not isinstance(current, str):
            raise FrozenSourceHistoryError(f"{code}.identity")
        require(
            relative not in result
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
            f"{code}.identity",
        )
        checked_blob(root, revision, relative, current, code)
        result[relative] = copy.deepcopy(entry)
    return result


def checked_predecessors(
    root: Path,
    revision: str,
    entries: Any,
) -> dict[str, str]:
    require(
        isinstance(entries, list) and len(entries) == EXPECTED_V20_PREDECESSOR_COUNT,
        "v20.predecessor.count",
    )
    result: dict[str, str] = {}
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            "v20.predecessor.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenSourceHistoryError("v20.predecessor.identity")
        if not isinstance(expected, str):
            raise FrozenSourceHistoryError("v20.predecessor.identity")
        require(relative not in result, "v20.predecessor.duplicate")
        checked_blob(root, revision, relative, expected, "v20.predecessor")
        result[relative] = expected
    require(
        result.get(
            "implementation/p17/qualification/"
            "current-workspace-source-v19-20260907/contract.json"
        )
        == "79b3fafc8bb080ad271b6d44cfae9754dfc3e613eaa788425e762a94a6fabcfa",
        "v20.predecessor.v19",
    )
    return result


@lru_cache(maxsize=4)
def _verified_history(root_text: str) -> dict[int, dict[str, Any]]:
    root = Path(root_text)
    expected_contract_sha256 = frozen.CONTRACT_SHA256
    snapshot_commit = frozen.QUALIFICATION_COMMIT
    result: dict[int, dict[str, Any]] = {}
    for version in range(LAST_VERSION, FIRST_VERSION - 1, -1):
        version_snapshot_commit = snapshot_commit
        frozen.verify_commit(root, snapshot_commit)
        frozen.require_ancestor(root, snapshot_commit, frozen.QUALIFICATION_COMMIT)
        contract_path = contract_relative(version)
        contract_raw = checked_blob(
            root,
            snapshot_commit,
            contract_path,
            expected_contract_sha256,
            f"v{version}.contract",
        )
        contract = load_json(contract_raw, f"v{version}.contract")
        base_commit = contract.get("base_commit")
        if not isinstance(base_commit, str):
            raise FrozenSourceHistoryError(f"v{version}.base")
        frozen.verify_commit(root, base_commit)
        frozen.require_ancestor(root, base_commit, snapshot_commit)
        require(
            contract.get("schema_version")
            == f"hwpx-agent.p17-current-workspace-source-qualification/v{version}"
            and contract.get("qualification_id") == qualification_id(version)
            and isinstance(contract.get("scope"), str)
            and isinstance(contract.get("claims"), dict),
            f"v{version}.identity",
        )
        evidence = contract.get("evidence")
        if not isinstance(evidence, dict):
            raise FrozenSourceHistoryError(f"v{version}.evidence")
        current_path = current_relative(version)
        current_sha256 = evidence.get("canonical_sha256" if version == 20 else "sha256")
        if not isinstance(current_sha256, str):
            raise FrozenSourceHistoryError(f"v{version}.evidence")
        require(
            evidence.get("path") == current_path
            and isinstance(current_sha256, str)
            and HEX64.fullmatch(current_sha256) is not None,
            f"v{version}.evidence",
        )
        current = load_json(
            checked_blob(
                root,
                snapshot_commit,
                current_path,
                current_sha256,
                f"v{version}.current",
            ),
            f"v{version}.current",
        )
        require(
            current.get("schema_version")
            == f"hwpx-agent.p17-current-workspace-source-current/v{version}"
            and current.get("claims") == contract.get("claims")
            and current.get("implementation_sources")
            == contract.get("implementation_sources"),
            f"v{version}.current.identity",
        )
        if version == 20:
            require(current.get("source_commit") == base_commit, "v20.current.base")
        else:
            require(
                current.get("base_commit") == base_commit
                and current.get("qualification_id") == qualification_id(version)
                and current.get("scope") == contract.get("scope"),
                f"v{version}.current.base",
            )

        implementation = checked_source_locks(
            root,
            base_commit,
            contract.get("implementation_sources"),
            f"v{version}.implementation",
        )
        guards = checked_source_locks(
            root,
            snapshot_commit,
            contract.get("guard_sources"),
            f"v{version}.guard",
        )
        successor_entries = current.get(
            "successors" if version == 20 else "source_successors"
        )
        successors = checked_successors(
            root,
            base_commit,
            successor_entries,
            f"v{version}.successor",
        )
        if version == 20:
            require(
                len(implementation) == EXPECTED_V20_IMPLEMENTATION_COUNT
                and len(successors) == EXPECTED_V20_SUCCESSOR_COUNT
                and len(guards) == EXPECTED_V20_GUARD_COUNT,
                "v20.counts",
            )
            predecessors = checked_predecessors(
                root, base_commit, contract.get("predecessors")
            )
        else:
            require(
                contract.get("source_successor_count") == len(successors),
                f"v{version}.successor.count",
            )
            predecessor = contract.get("predecessor")
            if not isinstance(predecessor, dict):
                raise FrozenSourceHistoryError(f"v{version}.predecessor")
            predecessor_path = predecessor.get("path")
            predecessor_sha256 = predecessor.get("sha256")
            if not isinstance(predecessor_path, str) or not isinstance(
                predecessor_sha256, str
            ):
                raise FrozenSourceHistoryError(f"v{version}.predecessor")
            require(
                predecessor
                == {
                    "path": contract_relative(version - 1),
                    "sha256": predecessor_sha256,
                }
                and predecessor == current.get("predecessor")
                and HEX64.fullmatch(predecessor_sha256) is not None,
                f"v{version}.predecessor",
            )
            predecessors = {predecessor_path: predecessor_sha256}
            expected_contract_sha256 = predecessor_sha256
            snapshot_commit = base_commit

        result[version] = {
            "snapshot_commit": version_snapshot_commit,
            "base_commit": base_commit,
            "contract": contract,
            "current": current,
            "implementation_sources": implementation,
            "successors": successors,
            "guards": guards,
            "predecessors": predecessors,
        }
    require(len(result) == LAST_VERSION - FIRST_VERSION + 1, "history.count")
    return result


def root_key(root: Path) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise FrozenSourceHistoryError("root") from error
    require(resolved.is_dir(), "root")
    return str(resolved)


def verify_version(root: Path, version: int) -> dict[str, Any]:
    require(
        type(version) is int and FIRST_VERSION <= version <= LAST_VERSION,
        "version",
    )
    return copy.deepcopy(_verified_history(root_key(root))[version]["contract"])


def verified_successors(root: Path, version: int) -> dict[str, dict[str, Any]]:
    require(
        type(version) is int and FIRST_VERSION <= version <= LAST_VERSION,
        "version",
    )
    return copy.deepcopy(_verified_history(root_key(root))[version]["successors"])


def verified_implementation_sources(
    root: Path, version: int
) -> dict[str, dict[str, Any]]:
    require(
        type(version) is int and FIRST_VERSION <= version <= LAST_VERSION,
        "version",
    )
    return copy.deepcopy(
        _verified_history(root_key(root))[version]["implementation_sources"]
    )


def clear_cache() -> None:
    _verified_history.cache_clear()


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_history_v1.py verify")
    try:
        history = _verified_history(root_key(ROOT))
    except (FrozenSourceHistoryError, frozen.FrozenSourceV39Error) as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_HISTORY_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    summary = {
        "schema_version": "hwpx-agent.p17-frozen-current-source-history/v1",
        "state": "pass",
        "first_version": FIRST_VERSION,
        "last_version": LAST_VERSION,
        "qualification_count": len(history),
        "mutable_worktree_sources_read": False,
        "receipt_blobs_verified": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
