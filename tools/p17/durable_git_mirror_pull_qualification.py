"""Qualify the exact current-PC durable Git mirror pull receipt and source commit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import validate_durable_git_mirror_pull_contract as runtime  # noqa: E402


BASE = "implementation/p17/qualification/durable-git-mirror-pull-v1-20260911"
QUALIFICATION = ROOT / BASE
SOURCE_BASE_COMMIT = "dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6"
RUN_ID = runtime.RUN_ID
RECEIPT_RELATIVE = f"artifacts/p17/durable-git-mirror-pull/runs/{RUN_ID}/receipt.json"
RECEIPT_SHA256 = runtime.RECEIPT_SHA256
CHECKS = runtime.CHECKS
RUNTIME_PATHS = tuple(
    sorted(
        {
            *runtime.RECEIPT_SOURCES,
            "crates/artifact-service/src/store/postgres_repository.rs",
            "crates/local-sync/tests/remote_adapter.rs",
            "crates/local-sync/tests/state_machine.rs",
            "crates/mcp-control-plane/src/postgres_plan_review.rs",
            "crates/mcp-control-plane/src/postgres_plan_source.rs",
            "crates/mcp-control-plane/src/postgres_stored_plan.rs",
            "crates/remote-sync-host/src/lib.rs",
            "crates/remote-sync-host/src/postgres.rs",
            "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PULL_V16.md",
            "protocol/migrations/p17-durable-git-mirror-pull-v1.md",
            "protocol/migrations/p17-remote-sync-request-v3-to-v4.md",
            "protocol/private/p17-durable-git-mirror-pull-v1.json",
            "protocol/private/p17-remote-sync-adapter-v4.json",
            "tools/p17/tests/test_atomic_mirror_checkpoint_checks.py",
            "tools/p17/tests/test_current_workspace_source_qualification_v41.py",
            "tools/p17/tests/test_durable_git_mirror_pull_contract.py",
            "tools/p17/tests/test_durable_git_mirror_push_qualification.py",
            "tools/p17/tests/test_postgres_checkpoint_host_checks.py",
            "tools/p17/validate_durable_git_mirror_pull_contract.py",
        }
    )
)
GUARD_PATHS = (
    "implementation/p17/P17_DURABLE_GIT_MIRROR_PULL_QUALIFICATION_V17.md",
    "tools/p17/durable_git_mirror_pull_qualification.py",
    "tools/p17/tests/test_durable_git_mirror_pull_qualification.py",
)
CLAIMS = {
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
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class QualificationError(ValueError):
    """Fail-closed qualification error containing only a bounded code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_relative(relative: str) -> None:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path.shape",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path.escape",
    )


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    validate_relative(relative)
    require(type(maximum) is int and 0 < maximum <= 4_000_000, "file.limit")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "file.link",
        )
    try:
        path = cursor.resolve(strict=True)
    except OSError as error:
        raise QualificationError("file.missing") from error
    require(
        resolved_root in path.parents
        and path.is_file()
        and 0 < path.stat().st_size <= maximum,
        "file.shape",
    )
    return path


def load_document(path: Path, code: str) -> dict[str, Any]:
    raw = path.read_bytes()

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{code}.duplicate")
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def git_blob(root: Path, commit: str, relative: str) -> bytes:
    require(HEX40.fullmatch(commit) is not None, "git.commit")
    validate_relative(relative)
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=30,
        check=False,
    )
    require(
        result.returncode == 0 and 0 < len(result.stdout) <= 4_000_000,
        "git.blob",
    )
    return result.stdout


def source_lock(root: Path, relative: str, *, committed: bool) -> dict[str, Any]:
    raw = bounded_file(root, relative).read_bytes()
    if committed:
        require(raw == git_blob(root, SOURCE_BASE_COMMIT, relative), "source.history")
    return {"path": relative, "bytes": len(raw), "sha256": digest(raw)}


def validate_runtime(root: Path) -> dict[str, Any]:
    try:
        contract = runtime.verify(root)
    except runtime.ContractError as error:
        raise QualificationError(f"runtime.{error}") from error
    evidence = contract.get("evidence")
    require(
        isinstance(evidence, dict)
        and evidence.get("actual_postgresql_18_4") is True
        and evidence.get("actual_disposable_local_bare_git") is True
        and evidence.get("actual_authenticated_loopback") is True
        and evidence.get("actual_clean_advance") is True
        and evidence.get("actual_conflict_preservation") is True
        and evidence.get("actual_exact_replay") is True
        and evidence.get("actual_git_database_drift_rejection") is True
        and evidence.get("actual_remote_network") is False
        and evidence.get("production") is False
        and evidence.get("actual_hangul") is False
        and evidence.get("p17_06_complete") is False
        and evidence.get("product_complete") is False,
        "runtime.claims",
    )
    return contract


def expected_current(root: Path) -> dict[str, Any]:
    validate_runtime(root)
    receipt_path = bounded_file(root, RECEIPT_RELATIVE, 262_144)
    receipt = load_document(receipt_path, "receipt")
    return {
        "schema_version": "hwpx-agent.p17-durable-git-mirror-pull-current/v1",
        "qualification_id": "p17.durable-git-mirror-pull.v1.20260911",
        "scope": "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
        "source_base_commit": SOURCE_BASE_COMMIT,
        "receipt": {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "check_count": len(CHECKS),
            "sha256": RECEIPT_SHA256,
        },
        "checks": list(CHECKS),
        "effect": receipt["effect"],
        "claims": CLAIMS,
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-durable-git-mirror-pull-qualification/v1",
        "qualification_id": "p17.durable-git-mirror-pull.v1.20260911",
        "scope": "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
        "source_base_commit": SOURCE_BASE_COMMIT,
        "claims": CLAIMS,
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "canonical_sha256": digest(current_path.read_bytes()),
        },
        "receipt": {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "check_count": len(CHECKS),
            "sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [
            source_lock(root, relative, committed=True) for relative in RUNTIME_PATHS
        ],
        "guard_sources": [
            source_lock(root, relative, committed=False) for relative in GUARD_PATHS
        ],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    receipt_path = bounded_file(root, RECEIPT_RELATIVE, 262_144)
    require(digest(receipt_path.read_bytes()) == RECEIPT_SHA256, "receipt.digest")
    validate_runtime(root)
    current_path = bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = bounded_file(root, f"{BASE}/contract.json", 512_000)
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    require(current == expected_current(root), "current.identity")
    require(contract == expected_contract(root, current_path), "contract.identity")
    return contract


def qualify() -> tuple[Path, Path]:
    receipt_path = bounded_file(ROOT, RECEIPT_RELATIVE, 262_144)
    require(digest(receipt_path.read_bytes()) == RECEIPT_SHA256, "receipt.digest")
    validate_runtime(ROOT)
    for relative in RUNTIME_PATHS:
        source_lock(ROOT, relative, committed=True)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: durable_git_mirror_pull_qualification.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current, contract = qualify()
        print(
            "P17_DURABLE_GIT_MIRROR_PULL_QUALIFICATION_PASS "
            f"current={current.name} contract={contract.name} checks={len(CHECKS)}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_DURABLE_GIT_MIRROR_PULL_QUALIFICATION_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
