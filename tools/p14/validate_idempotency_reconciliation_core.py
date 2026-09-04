from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "p14-idempotency-reconciliation-core-v1.json"
)
EXPECTED_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/idempotency-service/Cargo.toml",
    "crates/idempotency-service/src/lib.rs",
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "docs/12_implementation_guides/07_windows_automation_worker.md",
    "implementation/p04/P04-08_IDEMPOTENCY_CAS_POLICY.md",
]
EXPECTED_REQUIREMENTS = {
    "exact_request_and_manifest_binding": True,
    "same_key_drift_rejected": True,
    "concurrent_claimers": 16,
    "concurrent_new_claims": 1,
    "max_attempts": 10,
    "max_retry_delay_seconds": 86_400,
    "max_record_ttl_seconds": 604_800,
    "retry_requires_proven_no_effect": True,
    "unknown_outcome_blocks_new_effect": True,
    "stale_attempt_and_fence_rejected": True,
    "rust_tests": 10,
    "postgres_migration_qualified": False,
    "production_service_qualified": False,
}


class ContractError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise ContractError(message)


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                fail(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(value, dict):
        fail("idempotency core contract root must be an object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bounded_repository_file(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        fail("source path must be a nonempty repository-relative POSIX path")
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts:
        fail(f"source path escapes the repository: {relative}")
    cursor = root
    for part in value.parts:
        cursor /= part
        if cursor.is_symlink() or (
            hasattr(cursor, "is_junction") and cursor.is_junction()
        ):
            fail(f"source path contains a link or junction: {relative}")
    resolved_root = root.resolve(strict=True)
    resolved = (root / value).resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        fail(f"source path is not a repository file: {relative}")
    if not 0 < resolved.stat().st_size <= 2 * 1024 * 1024:
        fail(f"source file exceeds its bound: {relative}")
    return resolved


def require_tokens(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{label} is missing required tokens: {missing}")


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, object]:
    if root.resolve() != ROOT.resolve():
        fail("idempotency core validator only accepts the repository root")
    contract = load_json(path.resolve(strict=True))
    if set(contract) != {"schema_version", "state", "source_files", "requirements"}:
        fail("idempotency core contract keys differ")
    if contract["schema_version"] != "hwpx-agent.p14-idempotency-reconciliation-core/v1":
        fail("idempotency core schema differs")
    if contract["state"] != "rust_core_pass_sql_pending":
        fail("idempotency core state differs")
    if contract["requirements"] != EXPECTED_REQUIREMENTS:
        fail("idempotency core requirements differ")

    sources = contract["source_files"]
    if not isinstance(sources, list) or len(sources) != len(EXPECTED_PATHS):
        fail("idempotency core source count differs")
    observed_paths: list[str] = []
    source_text: dict[str, str] = {}
    for entry in sources:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            fail("idempotency core source entry differs")
        relative = entry["path"]
        expected = entry["sha256"]
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            fail(f"invalid source digest: {relative}")
        source = bounded_repository_file(root, relative)
        if sha256(source) != expected:
            fail(f"source digest mismatch: {relative}")
        observed_paths.append(relative)
        source_text[relative] = source.read_text(encoding="utf-8")
    if observed_paths != EXPECTED_PATHS:
        fail("idempotency core source order differs")

    manifest = source_text["crates/idempotency-service/Cargo.toml"]
    if "idempotency-service" not in source_text["Cargo.toml"]:
        fail("idempotency service is not a workspace member")
    require_tokens(
        manifest,
        [
            'name = "idempotency-service"',
            'artifact-service = { version = "0.1.0", path = "../artifact-service" }',
            'job-service = { version = "0.1.0", path = "../job-service" }',
            'revision-service = { version = "0.1.0", path = "../revision-service" }',
            "serde.workspace = true",
            "thiserror.workspace = true",
            "uuid.workspace = true",
            "workspace = true",
        ],
        "idempotency service manifest",
    )
    rust = source_text["crates/idempotency-service/src/lib.rs"]
    require_tokens(
        rust,
        [
            "#![forbid(unsafe_code)]",
            "pub enum IdempotencyState",
            "RetryPending",
            "OutcomeUnknown",
            "pub struct RetryPolicy",
            "pub struct RequestBinding",
            "pub struct NoEffectProof",
            "pub enum ClaimOutcome",
            "pub enum ReconciliationObservation",
            "pub fn claim(",
            "pub fn begin_attempt(",
            "pub fn retry_transient(",
            "pub fn mark_outcome_unknown(",
            "pub fn reconcile(",
            "pub fn fail_terminal(",
            "fn concurrent_claim_has_one_new_owner_and_exact_replays()",
            "fn exact_no_effect_reconciliation_is_the_only_unknown_retry_path()",
            "fn cross_subject_tenant_stale_lease_and_expired_effect_are_rejected()",
        ],
        "idempotency Rust core",
    )
    if rust.count("#[test]") != 10:
        fail("idempotency Rust test count differs")
    if re.search(r"(?m)^\s*(?:unsafe\s*\{|pub\s+unsafe\s+fn)", rust):
        fail("idempotency Rust core contains unsafe code")
    return {"state": "pass", "source_files": len(sources), "rust_tests": 10}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    result = validate_contract(args.contract, ROOT)
    print(
        "P14_IDEMPOTENCY_RECONCILIATION_CORE_PASS "
        f"sources={result['source_files']} rust_tests={result['rust_tests']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"P14_IDEMPOTENCY_RECONCILIATION_CORE_FAIL {error}")
        raise SystemExit(1) from error
