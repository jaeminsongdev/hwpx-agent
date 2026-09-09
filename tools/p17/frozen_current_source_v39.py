"""Verify the immutable v39 source qualification without mutable validators."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION_COMMIT = "ebece5eaea645e2de0f2ba50227995969969e623"
BASE_COMMIT = "103bbf5b0448076e3f95db939b4d186100b6a4f4"
QUALIFICATION_ID = "p17.current-workspace-source.v39.20260908"
SCOPE = "p06_06_exact_target_oracle_closure_source_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v39-20260908/"
    "contract.json"
)
CONTRACT_BYTES = 4493
CONTRACT_SHA256 = "544c68cdea536e234139bd492f7e2812fe1b7ab02826af580f307284835f287c"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v39-20260908/"
    "current-host.json"
)
CURRENT_BYTES = 13245
CURRENT_SHA256 = "cb0b4acdc16433d858047026587752bb563a763bcd4f8eec48437f74f8941927"
PREDECESSOR_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v38-20260907/"
    "contract.json"
)
PREDECESSOR_SHA256 = "818e41c4e8ee46eea3b0f31b7d769eb56d19f9de46310ed73e37285cb237ebe0"
RUN_ID = "e159d3cf21df48b38bda3f9813d8a0d1"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_SHA256 = "b3d0349d0e0b84900f7200938d8687cbe3b636ffecd62d2670c7197da77815c3"
MAX_BLOB_BYTES = 4_000_000
REPOSITORY_ENVIRONMENT_KEYS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
)
EXPECTED_IMPLEMENTATION_COUNT = 7
EXPECTED_SUCCESSOR_COUNT = 26
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = (
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V39.md",
    "tools/p17/current_workspace_source_qualification_v39.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v39.py",
)
EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "other_pc_or_version": False,
    "p06_04_actual_artifact_reverified_by_source_qualification": False,
    "p06_04_complete": False,
    "p06_04_completion_report_source_bound": True,
    "p06_05_actual_oracle_hashes_source_bound": True,
    "p06_05_actual_target_hancom_readback_verified": False,
    "p06_05_attempt01_failed_open_diagnostic_bound": True,
    "p06_05_bounded_hancom_readback_wrapper_bound": True,
    "p06_05_calibrated_target_builder_bound": True,
    "p06_05_calibration_history_hashes_source_bound": True,
    "p06_05_complete": False,
    "p06_05_deterministic_target_report_source_bound": True,
    "p06_05_font_metric_target_builder_bound": True,
    "p06_05_inner_margin_typed_and_bounded": True,
    "p06_05_product_target_contract_v1_bound": True,
    "p06_05_product_target_contract_v2_bound": True,
    "p06_05_replacement_target_validator_source_bound": True,
    "p06_05_stale_layout_cache_invalidation_bound": True,
    "p06_05_table_layout_hwpx_profile_v2_bound": True,
    "p06_05_target_builder_v2_bound": True,
    "p06_05_target_pdf_verified": False,
    "p06_05_target_v2_validator_source_bound": True,
    "p06_06_actual_oracle_hashes_source_bound": True,
    "p06_06_actual_source_adapter_readback_verified": False,
    "p06_06_actual_source_capture_verified": False,
    "p06_06_actual_source_evidence_hashes_bound": True,
    "p06_06_adapter_contract_validator_source_bound": True,
    "p06_06_complete": False,
    "p06_06_completion_report_source_bound": True,
    "p06_06_formula_id_profile_source_bound": True,
    "p06_06_hwpx_adapter_source_bound": True,
    "p06_06_product_target_oracle_verified": False,
    "p06_06_structural_differential_verified": False,
    "p06_06_structural_target_source_bound": True,
    "p06_06_target_access_diagnostics_source_bound": True,
    "p06_06_target_oracle_checker_source_bound": True,
    "p06_06_target_v2_contract_source_bound": True,
    "p06_06_target_v2_tamper_tests_source_bound": True,
    "p06_06_target_v2_validator_source_bound": True,
    "p06_phase_complete": False,
    "product_complete": False,
    "production": False,
    "registered_host": False,
    "source_qualification_only": True,
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV39Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV39Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_revision(revision: str) -> str:
    require(
        isinstance(revision, str) and HEX40.fullmatch(revision) is not None, "revision"
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
    require(type(maximum) is int and 0 <= maximum <= MAX_BLOB_BYTES, "git.limit")
    try:
        resolved = root.resolve(strict=True)
        require(resolved.is_dir(), "git.root")
        environment = os.environ.copy()
        for key in REPOSITORY_ENVIRONMENT_KEYS:
            environment.pop(key, None)
        environment.update(
            {
                "GCM_INTERACTIVE": "Never",
                "GIT_NO_LAZY_FETCH": "1",
                "GIT_NO_REPLACE_OBJECTS": "1",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        completed = subprocess.run(
            ["git", *arguments],
            cwd=resolved,
            stdin=subprocess.DEVNULL,
            check=False,
            capture_output=True,
            env=environment,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise FrozenSourceV39Error(code) from error
    require(completed.returncode == 0 and len(completed.stdout) <= maximum, code)
    return completed.stdout


def verify_commit(root: Path, revision: str) -> None:
    validate_revision(revision)
    raw = git_output(
        root, ["rev-parse", "--verify", f"{revision}^{{commit}}"], 64, "commit"
    )
    try:
        observed = raw.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise FrozenSourceV39Error("commit") from error
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
        raise FrozenSourceV39Error("blob.size") from error
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
        raise FrozenSourceV39Error("json.decode") from error
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
        isinstance(entries, list) and len(entries) == expected_count, f"{code}.count"
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
            raise FrozenSourceV39Error(f"{code}.identity")
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
            raise FrozenSourceV39Error("successor.identity")
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
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
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
    predecessor = {"path": PREDECESSOR_RELATIVE, "sha256": PREDECESSOR_SHA256}
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v39"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("predecessor") == predecessor,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v39"
        and current.get("qualification_id") == QUALIFICATION_ID
        and current.get("scope") == SCOPE
        and current.get("base_commit") == BASE_COMMIT
        and current.get("predecessor") == predecessor,
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
    successors = current.get("source_successors")
    successor_paths = validate_successors(root, successors)
    require(implementation_paths.isdisjoint(successor_paths), "source.overlap")
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
        "schema_version": "hwpx-agent.p17-frozen-current-source-v39-verification/v1",
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
        "receipt_reference_bound": True,
        "receipt_blob_verified": False,
        "mutable_worktree_sources_read": False,
        "actual_hangul": False,
        "production": False,
        "product_complete": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v39.py verify")
    try:
        result = verify()
    except FrozenSourceV39Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V39_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
