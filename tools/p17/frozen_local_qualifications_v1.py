"""Verify five historical local P17 qualifications from immutable Git blobs."""

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

QUALIFICATIONS: dict[str, dict[str, Any]] = {
    "local_daemon": {
        "directory": "local-daemon-v1-20260906",
        "qualification_id": "p17.local-daemon.v1.20260906",
        "snapshot_commit": "05ad6bbdf03160ea269c790c76e2154921e75799",
        "contract_bytes": 2650,
        "contract_sha256": (
            "9a578d3207365bd97e97d4850a774d80c2f22aa64c2fd27b3493ff498ff897b1"
        ),
        "current_bytes": 2089,
        "current_sha256": (
            "d66801fac493158a626c5c42e3599bd1ff17495074609a6003ff79171ecb2243"
        ),
        "contract_schema": "hwpx-agent.p17-local-daemon-qualification/v1",
        "current_schema": "hwpx-agent.p17-local-daemon-current/v1",
        "source_map_key": "source_hashes",
        "runtime_count": 10,
        "guard_count": 3,
    },
    "local_mcp_plugin": {
        "directory": "local-mcp-plugin-v1-20260906",
        "qualification_id": "p17.local-mcp-plugin.v1.20260906",
        "snapshot_commit": "dd4e605cb036a47685ab61abf4a35ad4be4364fd",
        "contract_bytes": 3834,
        "contract_sha256": (
            "f4315b640113071990493d1c352f3d16c7cd4b4d22cc0fd1bd3914b4723c983e"
        ),
        "current_bytes": 3988,
        "current_sha256": (
            "46e28071257083f5ba4aadc119e28ea8b43cfcad259eb4af461318a74ee851c0"
        ),
        "contract_schema": "hwpx-agent.p17-local-mcp-plugin-qualification/v1",
        "current_schema": "hwpx-agent.p17-local-mcp-plugin-current/v1",
        "source_map_key": "source_hashes",
        "runtime_count": 17,
        "guard_count": 3,
    },
    "main_bound_plugin": {
        "directory": "main-bound-plugin-v2-20260906",
        "qualification_id": "p17.main-bound-plugin.v2.20260906",
        "snapshot_commit": "f8d3df56ceff64d0427ce0deab08b3719fa79ea1",
        "contract_bytes": 3084,
        "contract_sha256": (
            "b74800199a54d1d276267a313e89da153a098b1389c72fc570c91919584ff737"
        ),
        "current_bytes": 2928,
        "current_sha256": (
            "5911076eec68a163b63747b9dd4fde23bfe47e6c4600bd7b53f94e6ea1090985"
        ),
        "contract_schema": "hwpx-agent.p17-main-bound-plugin-qualification/v1",
        "current_schema": "hwpx-agent.p17-main-bound-plugin-current/v1",
        "source_map_key": "source_hashes",
        "runtime_count": 13,
        "guard_count": 3,
    },
    "postgres_checkpoint_host": {
        "directory": "postgres-checkpoint-host-v1-20260907",
        "qualification_id": "p17.postgres-checkpoint-host.v1.20260907",
        "snapshot_commit": "240f270e09ec8e7576d49430f514dbd29e5ce689",
        "contract_bytes": 6535,
        "contract_sha256": (
            "c8b594781c5b05f4d1487c956661a72a3ea93a5cb109186a8aacf9f8f7d08e55"
        ),
        "current_bytes": 5216,
        "current_sha256": (
            "75c7bc2dfafffa58098160cdaa6729ca728fa8e59e28e490b191d11ee6d3ad40"
        ),
        "contract_schema": "hwpx-agent.p17-postgres-checkpoint-host-qualification/v1",
        "current_schema": "hwpx-agent.p17-postgres-checkpoint-host-current/v1",
        "source_map_key": "source_sha256",
        "runtime_count": 29,
        "guard_count": 6,
    },
    "widget_plugin_prepare": {
        "directory": "widget-plugin-prepare-v1-20260906",
        "qualification_id": "p17.widget-plugin-prepare.v1.20260906",
        "snapshot_commit": "18965273fc6d2ab2a3edeee2a6bf0224aa644496",
        "contract_bytes": 3797,
        "contract_sha256": (
            "93cf63f6cce01da22a29ec8cf69ece09009e29a08f752cddd14dbc234b55f547"
        ),
        "current_bytes": 4790,
        "current_sha256": (
            "af12e7708653bf1f04c384bd667af65689a42e2033e928c0af7a6b76edbb4a27"
        ),
        "contract_schema": "hwpx-agent.p17-widget-plugin-prepare-qualification/v1",
        "current_schema": "hwpx-agent.p17-widget-plugin-prepare-current/v1",
        "source_map_key": "source_hashes",
        "runtime_count": 17,
        "guard_count": 3,
    },
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenLocalQualificationError(ValueError):
    """Fail-closed local-qualification history error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenLocalQualificationError(code)


def qualification_paths(specification: dict[str, Any]) -> tuple[str, str]:
    directory = specification["directory"]
    base = f"implementation/p17/qualification/{directory}"
    return f"{base}/contract.json", f"{base}/current-host.json"


def load_json(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenLocalQualificationError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def locked_json(
    root: Path,
    revision: str,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    code: str,
) -> dict[str, Any]:
    require(
        type(expected_bytes) is int
        and 0 < expected_bytes <= 512_000
        and isinstance(expected_sha256, str)
        and HEX64.fullmatch(expected_sha256) is not None,
        f"{code}.lock",
    )
    raw = frozen.git_blob(root, revision, relative, 512_000)
    require(len(raw) == expected_bytes, f"{code}.bytes")
    require(frozen.digest(raw) == expected_sha256, f"{code}.digest")
    return load_json(raw, code)


def locked_sources(
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
    result: dict[str, str] = {}
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenLocalQualificationError(f"{code}.identity")
        if not isinstance(expected_sha256, str):
            raise FrozenLocalQualificationError(f"{code}.identity")
        if type(expected_bytes) is not int:
            raise FrozenLocalQualificationError(f"{code}.identity")
        require(
            relative not in result
            and type(expected_bytes) is int
            and expected_bytes > 0
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            f"{code}.identity",
        )
        raw = frozen.git_blob(root, revision, relative)
        require(len(raw) == expected_bytes, f"{code}.bytes")
        require(frozen.digest(raw) == expected_sha256, f"{code}.digest")
        result[relative] = expected_sha256
    return result


def verify_base_commits(
    root: Path,
    snapshot_commit: str,
    contract: dict[str, Any],
    code: str,
) -> None:
    if "base_commit" in contract:
        revisions: Any = [contract.get("base_commit")]
    elif "source_base_commit" in contract:
        revisions = [contract.get("source_base_commit")]
    else:
        base_commits = contract.get("base_commits")
        revisions = (
            list(base_commits.values()) if isinstance(base_commits, dict) else None
        )
    require(isinstance(revisions, list) and len(revisions) > 0, f"{code}.base")
    for revision in revisions:
        require(isinstance(revision, str), f"{code}.base")
        frozen.verify_commit(root, revision)
        frozen.require_ancestor(root, revision, snapshot_commit)


@lru_cache(maxsize=16)
def _verify(root_text: str, name: str) -> dict[str, Any]:
    specification = QUALIFICATIONS.get(name)
    if not isinstance(specification, dict):
        raise FrozenLocalQualificationError("qualification.unknown")
    root = Path(root_text)
    snapshot_commit = specification.get("snapshot_commit")
    if not isinstance(snapshot_commit, str):
        raise FrozenLocalQualificationError("qualification.snapshot")
    for field in (
        "contract_bytes",
        "current_bytes",
        "runtime_count",
        "guard_count",
    ):
        if type(specification.get(field)) is not int:
            raise FrozenLocalQualificationError("qualification.count")
    for field in (
        "contract_sha256",
        "current_sha256",
        "contract_schema",
        "current_schema",
        "qualification_id",
        "source_map_key",
        "directory",
    ):
        if not isinstance(specification.get(field), str):
            raise FrozenLocalQualificationError("qualification.field")
    frozen.verify_commit(root, snapshot_commit)
    frozen.require_ancestor(root, snapshot_commit, frozen.QUALIFICATION_COMMIT)
    contract_path, current_path = qualification_paths(specification)
    contract = locked_json(
        root,
        snapshot_commit,
        contract_path,
        specification["contract_bytes"],
        specification["contract_sha256"],
        f"{name}.contract",
    )
    current = locked_json(
        root,
        snapshot_commit,
        current_path,
        specification["current_bytes"],
        specification["current_sha256"],
        f"{name}.current",
    )
    require(
        contract.get("schema_version") == specification["contract_schema"]
        and contract.get("qualification_id") == specification["qualification_id"]
        and isinstance(contract.get("scope"), str)
        and isinstance(contract.get("claims"), dict),
        f"{name}.contract.identity",
    )
    evidence = contract.get("evidence")
    require(
        isinstance(evidence, dict)
        and evidence.get("path") == current_path
        and evidence.get("canonical_sha256") == specification["current_sha256"],
        f"{name}.evidence",
    )
    require(
        current.get("schema_version") == specification["current_schema"]
        and isinstance(current.get("scope"), str)
        and current.get("claims") == contract.get("claims"),
        f"{name}.current.identity",
    )
    verify_base_commits(root, snapshot_commit, contract, name)
    runtime = locked_sources(
        root,
        snapshot_commit,
        contract.get("runtime_sources"),
        specification["runtime_count"],
        f"{name}.runtime",
    )
    guards = locked_sources(
        root,
        snapshot_commit,
        contract.get("guard_sources"),
        specification["guard_count"],
        f"{name}.guard",
    )
    require(set(runtime).isdisjoint(guards), f"{name}.source.overlap")
    require(
        current.get(specification["source_map_key"]) == runtime,
        f"{name}.source.cross_link",
    )
    return {
        "contract": contract,
        "current": current,
        "snapshot_commit": snapshot_commit,
        "runtime_sources": runtime,
        "guard_sources": guards,
    }


def root_key(root: Path) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise FrozenLocalQualificationError("root") from error
    require(resolved.is_dir(), "root")
    return str(resolved)


def verify(name: str, root: Path = ROOT) -> dict[str, Any]:
    require(isinstance(name, str), "qualification.unknown")
    return copy.deepcopy(_verify(root_key(root), name)["contract"])


def verified_sources(name: str, root: Path = ROOT) -> dict[str, dict[str, str]]:
    require(isinstance(name, str), "qualification.unknown")
    result = _verify(root_key(root), name)
    return copy.deepcopy(
        {
            "runtime_sources": result["runtime_sources"],
            "guard_sources": result["guard_sources"],
        }
    )


def clear_cache() -> None:
    _verify.cache_clear()


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_local_qualifications_v1.py verify")
    try:
        for qualification_name in QUALIFICATIONS:
            _verify(root_key(ROOT), qualification_name)
    except (FrozenLocalQualificationError, frozen.FrozenSourceV39Error) as error:
        print(f"P17_FROZEN_LOCAL_QUALIFICATIONS_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    summary = {
        "schema_version": "hwpx-agent.p17-frozen-local-qualifications/v1",
        "state": "pass",
        "qualification_count": len(QUALIFICATIONS),
        "mutable_worktree_sources_read": False,
        "receipt_blobs_verified": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
