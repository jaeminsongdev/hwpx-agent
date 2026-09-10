"""Verify the immutable P16 artifact-service source successor."""

from __future__ import annotations

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
QUALIFICATION_COMMIT = "eb5674edbe2df7a0e239ca9d58f47715feb1796e"
SOURCE_COMMIT = "217ba56cd8a88e4d3560a5735052b18880481ff4"
CONTRACT_RELATIVE = "implementation/p16/qualification/postgres-217ba56/contract.json"
CONTRACT_BYTES = 6_289
CONTRACT_SHA256 = "c37e5b773a9117ffdb4af40c95d1263e08fdf7f6e25c69c6daa3108086497530"
QUALIFICATION_ID = "p16.local_postgres_artifact.217ba56"
SCOPE = "current_pc_source_binding_successor_only"
PREDECESSOR = {
    "path": "implementation/p14/postgres/p14-artifact-service-v1.json",
    "sha256": "92c2cfc91ff9def57649124a196ffddac5d9b68e1899c544e2ebff0abec91c82",
}
EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "actual_local_artifact_acceptance": True,
    "durable_plan_or_renderer": False,
    "p15_source_qualification": False,
    "phase_complete": False,
    "production": False,
    "registered_host": False,
}
EXPECTED_EVIDENCE = {
    "current": {
        "path": "implementation/p16/qualification/postgres-217ba56/current-db.json",
        "bytes": 3_950,
        "sha256": "f54c42b5aef9c4324373e0f2d5ffe349bbd33615fdcc561de9bf0d1b46894228",
        "run_id": "5a68a12751804d6f84df2b42ebed2f11",
    },
    "independent": {
        "path": (
            "implementation/p16/qualification/postgres-217ba56/independent-db.json"
        ),
        "bytes": 3_950,
        "sha256": "75141c0cad39c31fef899f99d5b62e676aedd188b8c59b26c0cfe294b03248f3",
        "run_id": "a06f2d898dd943e89ab6353e0a6f331b",
    },
}
EXPECTED_REPLACEMENTS = {
    "crates/artifact-service/Cargo.toml": (
        "13e9eaf8ab4d754f91673190b7dbf53bb968b000c8d8d33ba5d915c4d9cf72d1",
        "574c7dbfb13194183afe5664ff1bc43142e7730e0a0ce2086687d9bed981c69f",
    ),
    "crates/artifact-service/src/service.rs": (
        "d69af7f2a6e3411f6b367252c0ecddca8a9b7dd4bdf690ea459f987aaadf8c54",
        "f6c9f9eec62944434cd0eeca40fa1767bffbf49bfb92a99cd543a50b29fb1713",
    ),
    "crates/artifact-service/src/store.rs": (
        "72d4a74d318743494cefb842554a671ae212f56133d0f9987395c2f3dcb2c4e2",
        "ff803fce425c82cf19ed10b0aaa8b6b377c6bc9525f77ec8d70fa2168509f672",
    ),
}
EXPECTED_CONTRACT_KEYS = {
    "audited_source_commit",
    "claims",
    "evidence",
    "guard_sources",
    "predecessor",
    "qualification_id",
    "replacements",
    "runtime_sources",
    "schema_version",
    "scope",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenP16ArtifactSuccessorError(ValueError):
    """Fail-closed immutable P16 artifact successor error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenP16ArtifactSuccessorError(code)


def locked_json(
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
        raise FrozenP16ArtifactSuccessorError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def lock_map(source_locks: Iterable[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in source_locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            "source_lock.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(expected, str)
            and HEX64.fullmatch(expected) is not None,
            "source_lock.identity",
        )
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenP16ArtifactSuccessorError("source_lock.identity")
        result[relative] = expected
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
    result: dict[str, str] = {}
    if not isinstance(entries, list):
        raise FrozenP16ArtifactSuccessorError(f"{code}.entries")
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(expected, str)
            and HEX64.fullmatch(expected) is not None,
            f"{code}.identity",
        )
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FrozenP16ArtifactSuccessorError(f"{code}.identity")
        raw = frozen.git_blob(root, revision, relative)
        require(frozen.digest(raw) == expected, f"{code}.digest")
        result[relative] = expected
    return result


def verify_evidence(root: Path, entries: Any) -> None:
    require(isinstance(entries, list) and len(entries) == 2, "evidence.count")
    seen: set[str] = set()
    if not isinstance(entries, list):
        raise FrozenP16ArtifactSuccessorError("evidence.entries")
    for entry in entries:
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
            "evidence.shape",
        )
        role = entry.get("role")
        expected = EXPECTED_EVIDENCE.get(role) if isinstance(role, str) else None
        require(expected is not None and role not in seen, "evidence.identity")
        if expected is None or not isinstance(role, str):
            raise FrozenP16ArtifactSuccessorError("evidence.identity")
        require(
            entry.get("path") == expected["path"]
            and entry.get("sha256") == expected["sha256"]
            and entry.get("run_id") == expected["run_id"]
            and isinstance(entry.get("original_receipt_sha256"), str)
            and HEX64.fullmatch(entry["original_receipt_sha256"]) is not None,
            "evidence.identity",
        )
        receipt = locked_json(
            root,
            QUALIFICATION_COMMIT,
            expected["path"],
            expected["bytes"],
            expected["sha256"],
            "evidence.receipt",
        )
        require(
            receipt.get("decision") == "PASS"
            and receipt.get("actual_hangul") is False
            and receipt.get("registered_host") is False
            and receipt.get("owned_resources_removed") is True
            and receipt.get("run_id") == expected["run_id"],
            "evidence.receipt.claims",
        )
        seen.add(role)
    require(seen == set(EXPECTED_EVIDENCE), "evidence.roles")


def verified_replacements(
    root: Path = ROOT,
    source_locks: Iterable[dict[str, Any]] = (),
) -> dict[str, tuple[str, str]]:
    frozen.verify_commit(root, SOURCE_COMMIT)
    frozen.verify_commit(root, QUALIFICATION_COMMIT)
    frozen.require_ancestor(root, SOURCE_COMMIT, QUALIFICATION_COMMIT)
    frozen.require_ancestor(root, QUALIFICATION_COMMIT, ANCHOR_COMMIT)
    contract = locked_json(
        root,
        QUALIFICATION_COMMIT,
        CONTRACT_RELATIVE,
        CONTRACT_BYTES,
        CONTRACT_SHA256,
        "contract",
    )
    require(set(contract) == EXPECTED_CONTRACT_KEYS, "contract.shape")
    require(
        contract.get("schema_version")
        == "hwpx-agent.p16-postgres-source-qualification/v1"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("audited_source_commit") == SOURCE_COMMIT
        and contract.get("claims") == EXPECTED_CLAIMS,
        "contract.identity",
    )
    require(contract.get("predecessor") == PREDECESSOR, "contract.predecessor")
    predecessor = frozen.git_blob(root, SOURCE_COMMIT, PREDECESSOR["path"], 512_000)
    require(frozen.digest(predecessor) == PREDECESSOR["sha256"], "predecessor.digest")
    runtime = checked_path_digests(
        root, SOURCE_COMMIT, contract.get("runtime_sources"), 21, "runtime"
    )
    checked_path_digests(
        root, QUALIFICATION_COMMIT, contract.get("guard_sources"), 4, "guard"
    )
    verify_evidence(root, contract.get("evidence"))

    locks = lock_map(source_locks)
    replacements = contract.get("replacements")
    require(
        isinstance(replacements, list) and len(replacements) == 3, "replacement.count"
    )
    result: dict[str, tuple[str, str]] = {}
    if not isinstance(replacements, list):
        raise FrozenP16ArtifactSuccessorError("replacement.entries")
    for entry in replacements:
        require(
            isinstance(entry, dict)
            and set(entry) == {"path", "predecessor_sha256", "successor_sha256"},
            "replacement.shape",
        )
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        require(
            isinstance(relative, str)
            and isinstance(before, str)
            and isinstance(after, str)
            and EXPECTED_REPLACEMENTS.get(relative) == (before, after)
            and locks.get(relative) == before
            and runtime.get(relative) == after
            and relative not in result,
            "replacement.identity",
        )
        if (
            not isinstance(relative, str)
            or not isinstance(before, str)
            or not isinstance(after, str)
        ):
            raise FrozenP16ArtifactSuccessorError("replacement.identity")
        result[relative] = (before, after)
    require(result == EXPECTED_REPLACEMENTS, "replacement.exact")
    return result


if __name__ == "__main__":
    raise SystemExit("library-only immutable verifier")
