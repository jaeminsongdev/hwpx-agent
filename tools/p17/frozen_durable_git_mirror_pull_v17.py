"""Verify the immutable current-PC durable Git mirror pull qualification."""

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

from tools.p17 import frozen_current_source_v41 as gitbase  # noqa: E402


QUALIFICATION_COMMIT = "f79ad78a1e984622582c620eb2f4f030fb6beeff"
BASE_COMMIT = "dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6"
QUALIFICATION_ID = "p17.durable-git-mirror-pull.v1.20260911"
SCOPE = "current_pc_postgresql_local_bare_git_authenticated_loopback_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/durable-git-mirror-pull-v1-20260911/"
    "contract.json"
)
CONTRACT_BYTES = 9_279
CONTRACT_SHA256 = "159018052ef5a1d8f01f1550fb44b006f9bb1de68fbdd8fd1ab7fdefeffe0900"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/durable-git-mirror-pull-v1-20260911/"
    "current-host.json"
)
CURRENT_BYTES = 2_437
CURRENT_SHA256 = "d9d102803157e242af532f36d3eb53bbd9b439ace129de5b05f454c3686b3a36"
RUN_ID = "4162580f49da402983be6a8527e9721e"
RECEIPT_RELATIVE = (
    "artifacts/p17/durable-git-mirror-pull/runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 5_685
RECEIPT_SHA256 = "059ec3ebbf1f871af86b7df84fc38a878bb2ca52fb68f3074b6b419668f390a5"
EXPECTED_RUNTIME_COUNT = 48
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_DURABLE_GIT_MIRROR_PULL_QUALIFICATION_V17.md",
            "tools/p17/durable_git_mirror_pull_qualification.py",
            "tools/p17/tests/test_durable_git_mirror_pull_qualification.py",
        )
    )
)
EXPECTED_CLAIMS = {
    "actual_current_pc_postgresql_18_4": True,
    "actual_disposable_local_bare_git": True,
    "actual_authenticated_loopback": True,
    "actual_observed_snapshot_backfill": True,
    "actual_clean_remote_advance": True,
    "actual_ahead_conflict_preservation": True,
    "actual_exact_replay_without_second_observation": True,
    "actual_git_database_drift_rejection": True,
    "actual_runtime_admission_drift_rejection": True,
    "actual_owned_resource_cleanup": True,
    "durable_pull": True,
    "secrets_persisted": False,
    "actual_remote_network": False,
    "persistent_credential_custody": False,
    "registered_host": False,
    "actual_hangul": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenDurableGitPullV17Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenDurableGitPullV17Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
    try:
        return gitbase.git_blob(root, revision, relative, maximum)
    except gitbase.FrozenSourceV41Error as error:
        raise FrozenDurableGitPullV17Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        gitbase.verify_commit(root, revision)
    except gitbase.FrozenSourceV41Error as error:
        raise FrozenDurableGitPullV17Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        gitbase.require_ancestor(root, ancestor, descendant)
    except gitbase.FrozenSourceV41Error as error:
        raise FrozenDurableGitPullV17Error(str(error)) from error


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "json.duplicate")
        result[key] = value
    return result


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
        raise FrozenDurableGitPullV17Error("json.invalid") from error
    require(isinstance(value, dict), "json.object")
    return value


def validate_locked_sources(
    root: Path,
    revision: str,
    sources: Any,
    expected_count: int,
    code: str,
) -> tuple[str, ...]:
    require(isinstance(sources, list) and len(sources) == expected_count, f"{code}.count")
    paths: list[str] = []
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
        paths.append(relative)
    return tuple(paths)


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(
        set(receipt)
        == {
            "schema_version",
            "run_id",
            "state",
            "scope",
            "checks",
            "check_count",
            "postgres",
            "git",
            "claims",
            "effect",
            "source_sha256",
            "resources_cleaned",
        },
        "receipt.shape",
    )
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-pull-run/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("state") == "pass"
        and receipt.get("scope") == SCOPE
        and receipt.get("check_count") == 20
        and isinstance(receipt.get("checks"), list)
        and len(receipt["checks"]) == 20
        and len(set(receipt["checks"])) == 20
        and receipt["checks"][0] == "pinned_postgres_loopback_container"
        and receipt["checks"][-1] == "retained_observation_rollback_refused",
        "receipt.identity",
    )
    require(
        receipt.get("claims")
        == {
            "authenticated_loopback": True,
            "durable_pull": True,
            "persistent_credential_custody": False,
            "production": False,
            "registered_host": False,
            "secrets_persisted": False,
            "actual_remote_network": False,
            "actual_hangul": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
        "receipt.claims",
    )
    require(
        receipt.get("postgres", {}).get("loopback_only") is True
        and receipt.get("git")
        == {"object_format": "sha1", "bare": True, "remote_network": False}
        and receipt.get("resources_cleaned") is True,
        "receipt.environment",
    )
    effect = receipt.get("effect")
    require(
        isinstance(effect, dict)
        and effect.get("remote_generation") == 2
        and effect.get("observation_count") == 3
        and effect.get("conflict_count") == 1
        and effect.get("updated_response_replayed") is True
        and effect.get("conflict_response_replayed") is True
        and effect.get("local_conflict_state_preserved") is True
        and HEX64.fullmatch(effect.get("bounded_state_sha256", "")) is not None,
        "receipt.effect",
    )
    sources = receipt.get("source_sha256")
    require(
        isinstance(sources, dict)
        and len(sources) == 29
        and all(isinstance(value, str) and HEX64.fullmatch(value) for value in sources.values()),
        "receipt.sources",
    )


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
    receipt = json_blob(
        root,
        QUALIFICATION_COMMIT,
        RECEIPT_RELATIVE,
        RECEIPT_BYTES,
        RECEIPT_SHA256,
    )
    validate_receipt(receipt)
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-pull-qualification/v1"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("source_base_commit") == BASE_COMMIT,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-pull-current/v1"
        and current.get("qualification_id") == QUALIFICATION_ID
        and current.get("scope") == SCOPE
        and current.get("source_base_commit") == BASE_COMMIT,
        "current.identity",
    )
    require(contract.get("claims") == EXPECTED_CLAIMS, "contract.claims")
    require(current.get("claims") == EXPECTED_CLAIMS, "current.claims")
    receipt_identity = {
        "path": RECEIPT_RELATIVE,
        "run_id": RUN_ID,
        "check_count": 20,
        "sha256": RECEIPT_SHA256,
    }
    require(contract.get("receipt") == receipt_identity, "contract.receipt")
    require(current.get("receipt") == receipt_identity, "current.receipt")
    require(
        contract.get("evidence")
        == {"path": CURRENT_RELATIVE, "canonical_sha256": CURRENT_SHA256},
        "contract.evidence",
    )
    require(current.get("checks") == receipt.get("checks"), "current.checks")
    require(current.get("effect") == receipt.get("effect"), "current.effect")
    runtime_paths = validate_locked_sources(
        root,
        BASE_COMMIT,
        contract.get("runtime_sources"),
        EXPECTED_RUNTIME_COUNT,
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
    return {
        "schema_version": "hwpx-agent.p17-frozen-durable-git-mirror-pull-v17/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "runtime_source_count": len(runtime_paths),
        "guard_source_count": len(guard_paths),
        "check_count": 20,
        "receipt_blob_verified": True,
        "actual_authenticated_loopback": True,
        "actual_remote_network": False,
        "durable_pull": True,
        "production": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_durable_git_mirror_pull_v17.py verify")
    try:
        result = verify()
    except FrozenDurableGitPullV17Error as error:
        print(f"P17_FROZEN_DURABLE_GIT_PULL_V17_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
