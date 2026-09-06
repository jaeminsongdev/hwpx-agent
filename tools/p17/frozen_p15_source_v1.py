"""Read exact P15 source-successor contexts without loading their mutable validator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Iterable


CONTRACT_RELATIVE = "implementation/p16/qualification/p15-current-source-v1/contract.json"
CONTRACT_SHA256 = "5391428d584f7be36ed532ea446a07372761fb28bad9446972cef307c35a13e0"
QUALIFICATION_ID = "p16.composed_current_source.p15.v1"
CONTEXTS = {
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
EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "other_pc_or_version": False,
    "p15_phase_retested": False,
    "p16_phase_complete": False,
    "production": False,
    "registered_host": False,
    "source_qualification_only": True,
}
HEX = re.compile(r"[0-9a-f]{64}\Z")


class FrozenP15SourceError(ValueError):
    """Fail-closed source qualification error without candidate data."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenP15SourceError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "source.path",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and all(part not in ("", ".", "..") for part in value.parts),
        "source.path",
    )
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in value.parts:
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "source.link",
        )
    resolved = cursor.resolve(strict=True)
    require(
        resolved_root in resolved.parents
        and resolved.is_file()
        and 0 < resolved.stat().st_size <= maximum,
        "source.file",
    )
    return resolved


def fixed_contract(root: Path) -> dict[str, Any]:
    raw = bounded_file(root, CONTRACT_RELATIVE, 512_000).read_bytes()
    require(digest(raw) == CONTRACT_SHA256, "qualification.digest")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenP15SourceError("qualification.json") from error
    require(
        isinstance(value, dict)
        and value.get("schema_version") == "hwpx-agent.p16-p15-source-qualification/v1"
        and value.get("qualification_id") == QUALIFICATION_ID
        and value.get("scope") == "current_pc_source_binding_successor_only"
        and value.get("claims") == EXPECTED_CLAIMS,
        "qualification.identity",
    )
    return value


def git_blob_digest(root: Path, revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
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


def verified_replacements(
    root: Path,
    source_locks: Iterable[dict[str, Any]],
    context: str,
) -> dict[str, tuple[str, str]]:
    context_identity = CONTEXTS.get(context)
    require(context_identity is not None, "context.unknown")
    revision, expected_count = context_identity
    contract = fixed_contract(root)
    contexts = contract.get("contexts")
    entries = contexts.get(context) if isinstance(contexts, dict) else None
    require(
        isinstance(entries, list) and len(entries) == expected_count,
        "context.entries",
    )
    locks: dict[str, str] = {}
    for entry in source_locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            "lock.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in locks
            and isinstance(expected, str)
            and HEX.fullmatch(expected) is not None,
            "lock.identity",
        )
        locks[relative] = expected
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {"path", "predecessor_sha256", "successor_sha256"},
            "context.entry",
        )
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(before, str)
            and HEX.fullmatch(before) is not None
            and isinstance(after, str)
            and HEX.fullmatch(after) is not None
            and before != after
            and locks.get(relative) == before
            and git_blob_digest(root, revision, relative) == before,
            "context.identity",
        )
        observed = digest(bounded_file(root, relative).read_bytes())
        if observed == after:
            result[relative] = (before, after)
    return result
