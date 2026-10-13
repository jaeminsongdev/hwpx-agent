"""Explicit current-source qualification; no legacy error filtering or runtime authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE = "current_source_v2"
QUALIFICATION = "implementation/p09/evidence/p09-90-comment-current-source.qualification.v2.json"
QUALIFICATION_BYTES = 12656
QUALIFICATION_SHA256 = "5716bc516d88e00dbd93b2b8416cfcdab711bc9aff262c15e4c9eea6cc5d2a0e"
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
    "crates/domain-ir/src/comment_model.rs": "aa332c72c54480442cf64bf540ce8e75d89817c6620c3fc0b4141bc299956e1b",
    "crates/domain-ir/tests/comment_model.rs": "70de531cc94ff4f0613129de589291b9fd8cb7de7414aa0a6c63d22d73b1b5b6",
}
MAX_FILE_BYTES = 32 * 1024 * 1024


class CurrentSourceError(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CurrentSourceError("current_source_v2_duplicate_key")
        value[key] = item
    return value


def bounded_file(root: Path, relative: str, maximum: int = MAX_FILE_BYTES) -> bytes:
    if (
        not isinstance(relative, str) or not relative
        or ":" in relative or "\\" in relative
        or PurePosixPath(relative).is_absolute()
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise CurrentSourceError("current_source_v2_path")
    root = root.resolve()
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise CurrentSourceError("current_source_v2_link")
    path.resolve().relative_to(root)
    if not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise CurrentSourceError("current_source_v2_size")
    # Check again after reading: a truncated/extended file is not admitted.
    data = path.read_bytes()
    if not 0 < len(data) <= maximum:
        raise CurrentSourceError("current_source_v2_size")
    return data


def verify_pin(root: Path, pin: dict[str, Any]) -> None:
    if set(pin) != {"path", "bytes", "sha256"}:
        raise CurrentSourceError("current_source_v2_pin_shape")
    if type(pin["bytes"]) is not int or not 0 < pin["bytes"] <= MAX_FILE_BYTES:
        raise CurrentSourceError("current_source_v2_pin_size")
    data = bounded_file(root, pin["path"])
    if len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise CurrentSourceError("current_source_v2_pin_digest")


def canonical_digest(root: Path, relative: str) -> str:
    data = bounded_file(root, relative).replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    # Keep BOM; do not change XML/C++/Rust contents or strip source attributes.
    data.decode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verify_receipt(
    root: Path, authoritative: dict[str, str], official: dict[str, str],
    official_commit: str,
) -> dict[str, Any]:
    raw = bounded_file(root, QUALIFICATION, QUALIFICATION_BYTES)
    if len(raw) != QUALIFICATION_BYTES or hashlib.sha256(raw).hexdigest() != QUALIFICATION_SHA256:
        raise CurrentSourceError("current_source_v2_receipt_digest")
    value = json.loads(raw, object_pairs_hook=duplicate_guard)
    if (
        value["schema_version"] != "hwpx-agent.p09-comment-model-current-source-qualification/v2"
        or value["profile_id"] != PROFILE
        or value["implementation_canonical_sha256"] != IMPLEMENTATION_SHA256
        or value["official_commit"] != official_commit
        or value["official_source_canonical_sha256"] != official
        or value["authoritative_source_canonical_sha256"] != authoritative
    ):
        raise CurrentSourceError("current_source_v2_profile")
    pins = value["raw_pins"]
    if len(pins) != 32 or len({p["path"] for p in pins}) != len(pins):
        raise CurrentSourceError("current_source_v2_pin_coverage")
    for pin in pins:
        verify_pin(root, pin)
    for relative, expected in IMPLEMENTATION_SHA256.items():
        if canonical_digest(root, relative) != expected:
            raise CurrentSourceError("current_source_v2_implementation_digest")
    for relative, expected in authoritative.items():
        if canonical_digest(root, relative) != expected:
            raise CurrentSourceError("current_source_v2_authoritative_source")
    cache = "fixtures/target-build/official-source-cache/hwpx-owpml-model-145338/"
    for relative, expected in official.items():
        if canonical_digest(root, cache + relative) != expected:
            raise CurrentSourceError("current_source_v2_official_source")
    tests = value["Rust_component_regression"]
    if (
        tests["public_passed"] != 10 or tests["private_passed"] != 1
        or tests["total_passed"] != 11 or tests["failed"] != 0
        or tests["exit_codes"] != [0, 0]
        or value["gate"] != {"P09": "OPEN", "P09_04_green": False,
                            "P10_new_implementation": False, "goal_status": "active"}
    ):
        raise CurrentSourceError("current_source_v2_qualification_promotion")
    return value

