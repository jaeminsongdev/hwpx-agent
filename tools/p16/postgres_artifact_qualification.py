"""Source-bound P16 adapter successor; not a blanket source-lock or phase-Gate exemption."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REVISION = "217ba56cd8a88e4d3560a5735052b18880481ff4"
BASE = "implementation/p16/qualification/postgres-217ba56"
CONTRACT_PATH = f"{BASE}/contract.json"
PREDECESSOR_PATH = "implementation/p14/postgres/p14-artifact-service-v1.json"
PREDECESSOR_SHA256 = "92c2cfc91ff9def57649124a196ffddac5d9b68e1899c544e2ebff0abec91c82"
IMAGE = "postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_BYTES = 512 * 1024
RECEIPTS = (
    ("current", "5a68a12751804d6f84df2b42ebed2f11", "f54c42b5aef9c4324373e0f2d5ffe349bbd33615fdcc561de9bf0d1b46894228",
     "36a91a3b60ba27af0218987e7c1cb5b1a824259a76089a2cb8e4d0b71d71e4cc"),
    ("independent", "a06f2d898dd943e89ab6353e0a6f331b", "75141c0cad39c31fef899f99d5b62e676aedd188b8c59b26c0cfe294b03248f3",
     "abb65588445b5e3fc7446ccdb9e732b1d0a252acb332b4e491e92c88e8a17744"),
)
MIGRATIONS = (
    "0001_p14_metadata", "0002_p14_artifact_service", "0003_p14_revision_cas",
    "0004_p14_history_checkpoints", "0005_p14_job_state_machine", "0006_p14_worker_lease_fencing",
    "0007_p14_idempotency_reconciliation", "0008_p14_cancel_cleanup", "0009_p14_retention_local_mirror",
    "0010_p16_artifact_repository",
)
RUNTIME_PATHS = tuple(sorted((
    "Cargo.toml", "Cargo.lock", "crates/artifact-service/Cargo.toml",
    "crates/artifact-service/src/lib.rs", "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/store.rs", "crates/artifact-service/src/store/postgres_repository.rs",
    "crates/artifact-service/examples/postgres_artifact_probe.rs",
    "migrations/postgres/0010_p16_artifact_repository.down.sql",
    "tools/p16/run_postgres_artifact_checks.py", "tools/p16/tests/test_postgres_artifact_checks.py",
    *(f"migrations/postgres/{name}.up.sql" for name in MIGRATIONS),
)))
REPLACED_PATHS = (
    "crates/artifact-service/Cargo.toml",
    "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/store.rs",
)
GUARD_PATHS = (
    "tools/p16/postgres_artifact_qualification.py",
    "tools/p16/tests/test_postgres_artifact_qualification.py",
    "tools/p14/validate_artifact_service_migration.py",
    "implementation/p16/P16-06_POSTGRES_SOURCE_QUALIFICATION.md",
)
REQUIRED_CHECKS = (
    "all_ten_migrations_applied", "rollback_preserves_predecessors_and_restores_immutable_guard",
    "guarded_empty_rollback_reapply", "rust_seed", "rust_verify",
    "restart_owned_loopback_endpoint_revalidated", "rust_verify",
    "postgres_restart_preserves_encrypted_roundtrip", "rust_acl-quarantine", "rust_verify-quarantine",
    "rust_reject-role", "bypassrls_role_rejected", "rust_reject-policies", "disabled_rls_rejected",
    "rust_reject-policies", "permissive_policy_rejected", "rust_reject-privileges",
    "excessive_schema_privileges_rejected", "rust_reject-policies", "settable_owner_role_rejected",
    "cross_tenant_rls", "immutable_ciphertext_metadata", "nonempty_rollback_rejected", "rust_verify-quarantine",
)


class QualificationError(ValueError):
    """Closed, secret-free qualification failure code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def read_bounded(root: Path, relative: str, maximum: int = MAX_BYTES) -> bytes:
    require(isinstance(relative, str) and 0 < len(relative) <= 240, "path.shape")
    require("\\" not in relative and ":" not in relative and "\0" not in relative, "path.syntax")
    parts = relative.split("/")
    require(all(part not in ("", ".", "..") for part in parts)
            and not PurePosixPath(relative).is_absolute(), "path.escape")
    base = root.resolve(strict=True)
    cursor = base
    for part in parts:
        cursor /= part
        require(not cursor.is_symlink() and not (hasattr(cursor, "is_junction") and cursor.is_junction()), "path.link")
    path = cursor.resolve(strict=True)
    require(base in path.parents and path.is_file(), "path.file")
    require(0 < path.stat().st_size <= maximum, "file.bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(0 < len(raw) <= maximum, "file.bound")
    return raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_value(raw: bytes) -> Any:
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_BYTES, "json.bound")
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            require(key not in result, "json.duplicate")
            result[key] = value
        return result

    def invalid_constant(_: str) -> None:
        raise QualificationError("json.constant")

    try:
        decoded = raw.decode("utf-8")
        depth = 0
        quoted = False
        escaped = False
        for character in decoded:
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character in "[{":
                depth += 1
                require(depth <= 32, "json.depth")
            elif character in "]}":
                depth -= 1
        value = json.loads(decoded, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise QualificationError("json.invalid") from error
    return value


def exact(left: Any, right: Any) -> bool:
    """Python considers True == 1; a contract must not."""
    if type(left) is not type(right):
        return False
    if isinstance(right, dict):
        return left.keys() == right.keys() and all(exact(left[key], value) for key, value in right.items())
    if isinstance(right, list):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def validate_receipt(value: Any, run_id: str) -> dict[str, str]:
    require(isinstance(value, dict), "receipt.object")
    fixed = {
        "schema_version": "hwpx-agent.p16-postgres-artifact-acceptance/v1",
        "run_id": run_id, "decision": "PASS", "scope": "current_pc_disposable_postgres_only",
        "image": IMAGE, "failed_stage": None, "failure": None, "owned_resources_removed": True,
        "actual_hangul": False, "registered_host": False,
    }
    require(set(value) == set(fixed) | {"checks", "source_sha256", "probe_sha256"}, "receipt.keys")
    require(all(exact(value[key], wanted) for key, wanted in fixed.items()), "receipt.state")
    checks = value["checks"]
    require(isinstance(checks, list) and all(isinstance(item, str) for item in checks), "receipt.checks")
    # This observational event is optional, but only at the precise restart boundary.
    if len(checks) > 5 and checks[5] == "restart_ephemeral_port_reassigned":
        checks = checks[:5] + checks[6:]
    require(exact(checks, list(REQUIRED_CHECKS)), "receipt.checks")
    sources = value["source_sha256"]
    require(isinstance(sources, dict) and set(sources) == set(RUNTIME_PATHS), "receipt.sources")
    require(all(isinstance(item, str) and HEX.fullmatch(item) is not None for item in sources.values()), "receipt.source_digest")
    require(isinstance(value["probe_sha256"], str) and HEX.fullmatch(value["probe_sha256"]) is not None,
            "receipt.probe_digest")
    return sources


def expected_contract(root: Path) -> dict[str, Any]:
    predecessor_raw = read_bounded(root, PREDECESSOR_PATH)
    require(digest(predecessor_raw) == PREDECESSOR_SHA256, "predecessor.digest")
    predecessor = json_value(predecessor_raw)
    original = {entry["path"]: entry["sha256"] for entry in predecessor["source_locks"]}
    sources = None
    evidence = []
    for role, run_id, normalized_hash, original_hash in RECEIPTS:
        relative = f"{BASE}/{role}-db.json"
        raw = read_bounded(root, relative, 32 * 1024)
        require(digest(raw) == normalized_hash, "receipt.digest")
        current = validate_receipt(json_value(raw), run_id)
        require(sources is None or sources == current, "receipt.independent_sources")
        sources = current
        evidence.append({"role": role, "path": relative, "sha256": normalized_hash,
                         "original_receipt_sha256": original_hash, "run_id": run_id})
    require(sources is not None, "receipt.missing")
    for relative in RUNTIME_PATHS:
        require(digest(read_bounded(root, relative)) == sources[relative], "source.runtime_digest")
    return {
        "schema_version": "hwpx-agent.p16-postgres-source-qualification/v1",
        "qualification_id": "p16.local_postgres_artifact.217ba56",
        "audited_source_commit": REVISION,
        "scope": "current_pc_source_binding_successor_only",
        "predecessor": {"path": PREDECESSOR_PATH, "sha256": PREDECESSOR_SHA256},
        "replacements": [{"path": relative, "predecessor_sha256": original[relative],
                          "successor_sha256": sources[relative]} for relative in REPLACED_PATHS],
        "runtime_sources": [{"path": relative, "sha256": sources[relative]} for relative in RUNTIME_PATHS],
        "guard_sources": [{"path": relative, "sha256": digest(read_bounded(root, relative))}
                          for relative in GUARD_PATHS],
        "evidence": evidence,
        "claims": {"actual_local_artifact_acceptance": True, "phase_complete": False,
                   "p15_source_qualification": False, "durable_plan_or_renderer": False,
                   "actual_hangul": False, "registered_host": False, "production": False},
    }


def verified_replacements(root: Path) -> dict[str, tuple[str, str]]:
    try:
        contract = json_value(read_bounded(root, CONTRACT_PATH, 64 * 1024))
        expected = expected_contract(root)
        require(exact(contract, expected), "contract.exact")
        return {entry["path"]: (entry["predecessor_sha256"], entry["successor_sha256"])
                for entry in expected["replacements"]}
    except (OSError, KeyError, TypeError, RecursionError) as error:
        raise QualificationError("qualification.unavailable") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Create the new immutable contract; never overwrite")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.write:
            expected = expected_contract(ROOT)
            destination = ROOT / CONTRACT_PATH
            # A partial interrupted file cannot validate; an existing qualification is never replaced.
            with destination.open("xb") as stream:
                stream.write((json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        replacements = verified_replacements(ROOT)
    except (QualificationError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, QualificationError) else "qualification.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}))
        return 1
    print(json.dumps({"decision": "PASS", "scope": "source_binding_successor_only",
                      "replaced_sources": len(replacements), "runtime_sources": len(RUNTIME_PATHS),
                      "phase_complete": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
