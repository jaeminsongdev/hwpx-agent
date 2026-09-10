"""Read and compose the immutable v12-through-v39 source successor chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v12-20260907/"
    "contract.json"
)
CONTRACT_SHA256 = "4a03e390c3973c0ec8f6d7b69c33f0d8961967135b40d217c725d38af6d6a027"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v12-20260907/"
    "current-host.json"
)
CURRENT_SHA256 = "e2685452e8418e5b26b1788478d09eef516e73ada54ea092f925a5d390f63a2b"
QUALIFICATION_ID = "p17.current-workspace-source.v12.20260907"
BASE_COMMIT = "240f270e09ec8e7576d49430f514dbd29e5ce689"
HEX = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceError(ValueError):
    """Fail-closed source qualification error without candidate data."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    candidate_relative = Path(relative)
    require(
        bool(relative)
        and len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative
        and not candidate_relative.is_absolute()
        and ".." not in candidate_relative.parts,
        "source.path",
    )
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in candidate_relative.parts:
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "source.link",
        )
    resolved = (resolved_root / candidate_relative).resolve(strict=True)
    require(
        resolved_root in resolved.parents
        and resolved.is_file()
        and 0 < resolved.stat().st_size <= maximum,
        "source.file",
    )
    return resolved


def fixed_json(root: Path, relative: str, expected_sha256: str) -> dict[str, Any]:
    raw = bounded_file(root, relative, 512_000).read_bytes()
    require(digest(raw) == expected_sha256, "qualification.digest")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceError("qualification.json") from error
    require(isinstance(value, dict), "qualification.object")
    return value


def git_blob_digest(root: Path, relative: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        timeout=30,
    )
    require(
        completed.returncode == 0 and 0 < len(completed.stdout) <= 4_000_000,
        "source.history",
    )
    return digest(completed.stdout)


def verified_source_hashes(root: Path) -> dict[str, str]:
    contract = fixed_json(root, CONTRACT_RELATIVE, CONTRACT_SHA256)
    current = fixed_json(root, CURRENT_RELATIVE, CURRENT_SHA256)
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v12"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("scope") == "current_pc_source_binding_successor_only",
        "qualification.identity",
    )
    evidence = contract.get("evidence")
    require(
        isinstance(evidence, dict)
        and evidence.get("path") == CURRENT_RELATIVE
        and evidence.get("canonical_sha256") == CURRENT_SHA256,
        "qualification.evidence",
    )
    claims = contract.get("claims")
    require(
        isinstance(claims, dict)
        and claims.get("source_qualification_only") is True
        and claims.get("p17_postgres_checkpoint_host_v11_bound") is True
        and claims.get("actual_hangul") is False
        and claims.get("other_pc_or_version") is False
        and claims.get("phase_complete") is False
        and claims.get("production") is False,
        "qualification.claims",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v12"
        and current.get("source_commit") == BASE_COMMIT
        and current.get("claims") == claims,
        "current.identity",
    )
    implementation = contract.get("implementation_sources")
    successors = current.get("successors")
    require(
        isinstance(implementation, list)
        and len(implementation) == 107
        and isinstance(successors, list)
        and len(successors) == 14,
        "qualification.sources",
    )
    if not isinstance(implementation, list) or not isinstance(successors, list):
        raise FrozenSourceError("qualification.sources")
    result: dict[str, str] = {}
    for entry in implementation:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            "implementation.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(expected_bytes, int)
            and expected_bytes > 0
            and isinstance(expected, str)
            and HEX.fullmatch(expected) is not None,
            "implementation.identity",
        )
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenSourceError("implementation.identity")
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
            "successor.shape",
        )
        relative = entry.get("path")
        expected = entry.get("current_sha256")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(expected, str)
            and HEX.fullmatch(expected) is not None
            and isinstance(accepted, list)
            and accepted == sorted(set(accepted))
            and all(
                isinstance(value, str) and HEX.fullmatch(value) for value in accepted
            )
            and isinstance(composition, str)
            and composition in accepted,
            "successor.identity",
        )
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenSourceError("successor.identity")
        result[relative] = expected
    return result


def verified_replacements(
    root: Path, source_locks: Iterable[dict[str, Any]]
) -> dict[str, tuple[str, str]]:
    qualified = verified_source_hashes(root)
    from tools.p17 import frozen_composed_source_v39 as chain

    result: dict[str, tuple[str, str]] = {}
    seen: set[str] = set()
    for entry in source_locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"}, "lock.shape"
        )
        relative = entry.get("path")
        predecessor = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in seen
            and isinstance(predecessor, str)
            and HEX.fullmatch(predecessor) is not None,
            "lock.identity",
        )
        if not isinstance(relative, str) or not isinstance(predecessor, str):
            raise FrozenSourceError("lock.identity")
        seen.add(relative)
        source = bounded_file(root, relative)
        observed = digest(source.read_bytes())
        if observed == predecessor:
            continue
        v12_successor = qualified.get(relative)
        if v12_successor is not None and v12_successor != predecessor:
            require(
                git_blob_digest(root, relative) == v12_successor,
                "source.current",
            )
        try:
            target = chain.verified_target(root, relative, predecessor)
        except chain.FrozenComposedSourceError as error:
            if str(error) == "chain.unreachable":
                continue
            raise
        if observed == target:
            result[relative] = (predecessor, target)
    return result
