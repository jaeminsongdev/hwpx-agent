"""Verify the immutable current-PC durable Git mirror push qualification."""

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

from tools.p17 import frozen_current_source_v40 as gitbase  # noqa: E402

QUALIFICATION_COMMIT = "162c143d6942a8d648dc25e8986122a61813b8d4"
BASE_COMMIT = "2b0a74e68107931fce9a2a2f6985f5b081ad078f"
QUALIFICATION_ID = "p17.durable-git-mirror-push.v1.20260910"
SCOPE = "current_pc_postgresql_local_bare_git_authenticated_loopback_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/durable-git-mirror-push-v1-20260910/"
    "contract.json"
)
CONTRACT_BYTES = 7882
CONTRACT_SHA256 = "e2c080f6be84572f567c76f474123140154471bba57d7ca793a08e27eb1f01d6"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/durable-git-mirror-push-v1-20260910/"
    "current-host.json"
)
CURRENT_BYTES = 3061
CURRENT_SHA256 = "2bc6d57d703c96d0fd6aeda23c209e7e53ee793c4f77924dc2b68a8d8cbf1f35"
RUN_ID = "9b3ff9b352ec402aab20f1c5a387a8ec"
RECEIPT_RELATIVE = (
    "artifacts/p17/durable-git-mirror-push/runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 4613
RECEIPT_SHA256 = "efca394cc9962da63c3044c1aa4b78fbe9283e8f89d40ce3ae1fbe076146dd4d"
EXPECTED_RUNTIME_COUNT = 39
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = (
    "implementation/p17/P17_DURABLE_GIT_MIRROR_PUSH_QUALIFICATION_V15.md",
    "tools/p17/durable_git_mirror_push_qualification.py",
    "tools/p17/tests/test_durable_git_mirror_push_qualification.py",
)
EXPECTED_CLAIMS = {
    "actual_authenticated_loopback": True,
    "actual_canonical_plan_before_git_effect": True,
    "actual_committed_effect_recovery": True,
    "actual_current_pc_postgresql_18_4": True,
    "actual_disposable_local_bare_git": True,
    "actual_divergence_preservation": True,
    "actual_exact_replay_without_second_effect": True,
    "actual_hangul": False,
    "actual_owned_resource_cleanup": True,
    "actual_remote_network": False,
    "actual_runtime_admission_drift_rejection": True,
    "actual_verified_artifact_acl_admission": True,
    "durable_pull": False,
    "p17_06_complete": False,
    "persistent_credential_custody": False,
    "product_complete": False,
    "production": False,
    "registered_host": False,
    "secrets_persisted": False,
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenDurableGitPushV15Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenDurableGitPushV15Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
    try:
        return gitbase.git_blob(root, revision, relative, maximum)
    except gitbase.FrozenSourceV40Error as error:
        raise FrozenDurableGitPushV15Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        gitbase.verify_commit(root, revision)
    except gitbase.FrozenSourceV40Error as error:
        raise FrozenDurableGitPushV15Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        gitbase.require_ancestor(root, ancestor, descendant)
    except gitbase.FrozenSourceV40Error as error:
        raise FrozenDurableGitPushV15Error(str(error)) from error


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, member in pairs:
        require(key not in value, "json.duplicate")
        value[key] = member
    return value


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
        raise FrozenDurableGitPushV15Error("json.invalid") from error
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
            "scope",
            "checks",
            "check_count",
            "all_passed",
            "database",
            "effect",
            "source_sha256",
            "secrets_persisted",
            "authenticated_loopback",
            "durable_git_plan_before_effect",
            "database_and_git_exactly_once_recovery",
            "actual_remote_network",
            "actual_hangul",
            "production",
            "resources_cleaned",
        },
        "receipt.shape",
    )
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-push-run/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("scope") == "current_pc_postgresql_local_bare_git_loopback"
        and receipt.get("check_count") == 27
        and isinstance(receipt.get("checks"), list)
        and len(receipt["checks"]) == 27
        and len(set(receipt["checks"])) == 27
        and receipt.get("all_passed") is True,
        "receipt.identity",
    )
    require(
        receipt["checks"][0] == "pinned_postgres_loopback_container"
        and receipt["checks"][-1] == "security_definer_drift_rejected",
        "receipt.checks",
    )
    for key in (
        "authenticated_loopback",
        "durable_git_plan_before_effect",
        "database_and_git_exactly_once_recovery",
        "resources_cleaned",
    ):
        require(receipt.get(key) is True, f"receipt.{key}")
    for key in ("secrets_persisted", "actual_remote_network", "actual_hangul", "production"):
        require(receipt.get(key) is False, f"receipt.{key}")
    database = receipt.get("database")
    require(
        isinstance(database, dict)
        and database.get("migration_count") == 16
        and isinstance(database.get("migration_sha256"), list)
        and len(database["migration_sha256"]) == 16,
        "receipt.database",
    )
    effect = receipt.get("effect")
    require(
        isinstance(effect, dict)
        and effect.get("committed_recovered") is True
        and effect.get("exact_replay") is True
        and effect.get("divergence_preserved") is True,
        "receipt.effect",
    )
    source_sha256 = receipt.get("source_sha256")
    require(
        isinstance(source_sha256, dict)
        and set(source_sha256)
        == {
            "migration_up",
            "migration_down",
            "setup",
            "host_probe",
            "client_probe",
            "coordinator",
            "git_effect_host",
            "harness",
            "database_contract",
        }
        and all(isinstance(value, str) and HEX64.fullmatch(value) for value in source_sha256.values()),
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
        set(contract)
        == {
            "schema_version",
            "qualification_id",
            "scope",
            "source_base_commit",
            "claims",
            "evidence",
            "receipt",
            "runtime_sources",
            "guard_sources",
        }
        and contract.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-push-qualification/v1"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("source_base_commit") == BASE_COMMIT,
        "contract.identity",
    )
    require(
        set(current)
        == {
            "schema_version",
            "qualification_id",
            "scope",
            "source_base_commit",
            "receipt",
            "checks",
            "source_sha256",
            "claims",
        }
        and current.get("schema_version")
        == "hwpx-agent.p17-durable-git-mirror-push-current/v1"
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
        "check_count": 27,
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
    require(
        current.get("source_sha256") == receipt.get("source_sha256"),
        "current.sources",
    )
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
        "schema_version": "hwpx-agent.p17-frozen-durable-git-mirror-push-v15/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "runtime_source_count": len(runtime_paths),
        "guard_source_count": len(guard_paths),
        "check_count": 27,
        "receipt_blob_verified": True,
        "actual_authenticated_loopback": True,
        "actual_remote_network": False,
        "durable_pull": False,
        "production": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_durable_git_mirror_push_v15.py verify")
    try:
        result = verify()
    except FrozenDurableGitPushV15Error as error:
        print(f"P17_FROZEN_DURABLE_GIT_PUSH_V15_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
