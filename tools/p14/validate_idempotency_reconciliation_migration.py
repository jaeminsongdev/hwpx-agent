from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT
    / "implementation"
    / "p14"
    / "postgres"
    / "p14-idempotency-reconciliation-v2.json"
)
EXPECTED_IMAGE = (
    "postgres:18.4-bookworm@"
    "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)


class ContractError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise ContractError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bounded_repository_file(relative: str, maximum_bytes: int) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        fail("contract path must be a nonempty repository-relative POSIX path")
    candidate = ROOT / relative
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        fail(f"contract path is a link or junction: {relative}")
    resolved = candidate.resolve(strict=True)
    root = ROOT.resolve(strict=True)
    if root not in resolved.parents or not resolved.is_file():
        fail(f"contract path escapes the repository or is not a file: {relative}")
    if not 0 < resolved.stat().st_size <= maximum_bytes:
        fail(f"contract file exceeds its size bound: {relative}")
    return resolved


def require_digest(entry: dict[str, Any], maximum_bytes: int) -> Path:
    if set(entry) != {"path", "sha256"}:
        fail("digest entry has unexpected keys")
    path = bounded_repository_file(entry["path"], maximum_bytes)
    expected = entry["sha256"]
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        fail(f"invalid digest for {entry['path']}")
    if sha256(path) != expected:
        fail(f"digest mismatch for {entry['path']}")
    return path


def require_tokens(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{label} is missing required tokens: {missing}")


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        document: dict[str, Any] = {}
        for key, value in pairs:
            if key in document:
                fail(f"duplicate JSON key: {key}")
            document[key] = value
        return document

    document = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(document, dict):
        fail("idempotency migration contract root is not an object")
    return document


def validate_security_definer_search_paths(up_sql: str) -> None:
    functions = re.findall(
        r"CREATE(?: OR REPLACE)? FUNCTION hwpx_agent\.[\s\S]+?\n\$\$;",
        up_sql,
    )
    if len(functions) < 16:
        fail("up migration exposes fewer functions than expected")
    for function in functions:
        if "SECURITY DEFINER" in function and "SET search_path = pg_catalog" not in function:
            fail("SECURITY DEFINER function lacks a fixed pg_catalog search_path")
    if re.search(r"GRANT\s+EXECUTE[\s\S]+?\s+TO\s+PUBLIC", up_sql, re.IGNORECASE):
        fail("up migration grants executable capability to PUBLIC")


def validate_commit_authorization_guard(up_sql: str) -> None:
    start_token = "CREATE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2()"
    auth_lookup_token = "        SELECT * INTO v_authorization"
    end_token = "CREATE TRIGGER revision_commit_receipts_idempotency_v2_guard"
    start = up_sql.find(start_token)
    end = up_sql.find(end_token, start + len(start_token))
    if start < 0 or end < 0:
        fail("idempotency commit authorization guard boundaries are missing")
    guard = up_sql[start:end]
    record_guard, separator, authorization_guard = guard.partition(auth_lookup_token)
    if not separator:
        fail("idempotency commit authorization lookup is missing")
    if "RETURN NEW;" in record_guard or re.search(
        r"IF NOT FOUND THEN\s+RAISE EXCEPTION USING\s+"
        r"ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';",
        record_guard,
    ) is None:
        fail("unbound revision commit is not rejected before authorization lookup")
    require_tokens(
        authorization_guard,
        [
            "FOR UPDATE NOWAIT;",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_BUSY'",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH'",
            "current_setting(\n        'hwpx_agent.commit_authorization_id', true",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_FENCE_MISMATCH'",
            "DELETE FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth",
            "RETURN NEW;",
        ],
        "idempotency commit authorization guard",
    )


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, object]:
    if root.resolve() != ROOT.resolve():
        fail("idempotency migration validator only accepts the repository root")
    document = load_json(path.resolve(strict=True))
    expected_keys = {
        "schema_version",
        "state",
        "container_image",
        "prerequisites",
        "migration",
        "smoke_fixture",
        "source_files",
        "requirements",
    }
    if set(document) != expected_keys:
        fail("idempotency migration contract keys differ from the exact schema")
    if document["schema_version"] != "hwpx-agent.p14-idempotency-reconciliation/v2":
        fail("idempotency migration contract schema version differs")
    if document["state"] != "pass" or document["container_image"] != EXPECTED_IMAGE:
        fail("idempotency migration contract state or image differs")

    prerequisites = document["prerequisites"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 6:
        fail("idempotency migration requires exactly six prerequisite migrations")
    for expected_version, entry in enumerate(prerequisites, start=1):
        if not isinstance(entry, dict) or set(entry) != {
            "version",
            "up_path",
            "up_sha256",
            "down_path",
            "down_sha256",
        }:
            fail("prerequisite migration entry differs")
        if entry["version"] != expected_version:
            fail("prerequisite migration order differs")
        require_digest(
            {"path": entry["up_path"], "sha256": entry["up_sha256"]},
            512 * 1024,
        )
        require_digest(
            {"path": entry["down_path"], "sha256": entry["down_sha256"]},
            256 * 1024,
        )

    migration = document["migration"]
    if not isinstance(migration, dict) or set(migration) != {
        "version",
        "name",
        "up_path",
        "up_sha256",
        "down_path",
        "down_sha256",
    }:
        fail("idempotency migration entry differs")
    if migration["version"] != 7 or migration["name"] != (
        "p14.idempotency_reconciliation_v2"
    ):
        fail("idempotency migration identity differs")
    up_path = require_digest(
        {"path": migration["up_path"], "sha256": migration["up_sha256"]},
        512 * 1024,
    )
    down_path = require_digest(
        {"path": migration["down_path"], "sha256": migration["down_sha256"]},
        256 * 1024,
    )

    smoke = document["smoke_fixture"]
    if not isinstance(smoke, dict) or set(smoke) != {
        "path",
        "sha256",
        "assertion_count",
        "pass_marker",
    }:
        fail("idempotency smoke fixture entry differs")
    smoke_path = require_digest(
        {"path": smoke["path"], "sha256": smoke["sha256"]},
        512 * 1024,
    )
    if smoke["assertion_count"] != 28 or smoke["pass_marker"] != (
        "P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28"
    ):
        fail("idempotency smoke assertion contract differs")

    sources = document["source_files"]
    if not isinstance(sources, list) or len(sources) != 6:
        fail("idempotency migration contract requires exactly six source files")
    source_paths: list[Path] = []
    for entry in sources:
        if not isinstance(entry, dict):
            fail("idempotency source entry is not an object")
        source_paths.append(require_digest(entry, 512 * 1024))

    requirements = document["requirements"]
    if requirements != {
        "legacy_rows_never_promoted": True,
        "record_version": 2,
        "job_state_machine_version": 2,
        "atomic_claim_job_attempt_updates": True,
        "exact_subject_project_branch_job_key_binding": True,
        "exact_request_manifest_source_effect_transaction_binding": True,
        "exact_revision_id_and_generation_binding": True,
        "branch_head_lock_closes_no_effect_toctou": True,
        "late_commit_requires_current_fence_authorization": True,
        "all_v7_revision_commits_require_bound_idempotency": True,
        "attempt_scoped_unpredictable_commit_capability": True,
        "trusted_committed_revision_oracle": True,
        "source_requalified_on_every_lease": True,
        "automation_unknown_freezes_second_effect": True,
        "automation_no_effect_requires_reconciliation": True,
        "max_attempts": 10,
        "max_delay_seconds": 86400,
        "max_ttl_seconds": 604800,
        "rollback_refuses_v2_data": True,
        "forced_tenant_rls": True,
        "public_execute_revoked": True,
        "production_service_qualified": False,
    }:
        fail("idempotency migration requirements differ")

    up_sql = up_path.read_text(encoding="utf-8")
    down_sql = down_path.read_text(encoding="utf-8")
    smoke_sql = smoke_path.read_text(encoding="utf-8")
    source_text = "\n".join(item.read_text(encoding="utf-8") for item in source_paths)
    require_tokens(
        up_sql,
        [
            "ADD COLUMN record_version smallint NOT NULL DEFAULT 1",
            "state_machine_version = 2",
            "CREATE UNIQUE INDEX idempotency_v2_job_unique_idx",
            "CREATE UNIQUE INDEX idempotency_v2_transaction_unique_idx",
            "CREATE TABLE hwpx_agent.idempotency_commit_authorizations (",
            "CREATE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2()",
            "CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(",
            "CREATE TRIGGER revision_commit_receipts_idempotency_v2_guard",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED'",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH'",
            "v_commit_authorization_id uuid := gen_random_uuid()",
            "FOR SHARE;",
            "CREATE FUNCTION hwpx_agent.claim_idempotent_job_v2(",
            "CREATE FUNCTION hwpx_agent.lease_idempotent_job_v2(",
            "CREATE FUNCTION hwpx_agent.advance_idempotent_job_v2(",
            "CREATE FUNCTION hwpx_agent.heartbeat_idempotent_job_v2(",
            "CREATE FUNCTION hwpx_agent.schedule_idempotent_retry_v2(",
            "CREATE FUNCTION hwpx_agent.mark_idempotent_outcome_unknown_v2(",
            "CREATE FUNCTION hwpx_agent.complete_idempotent_job_success_v2(",
            "CREATE FUNCTION hwpx_agent.fail_idempotent_job_terminal_v2(",
            "CREATE FUNCTION hwpx_agent.reconcile_idempotent_job_v2(",
            "CREATE FUNCTION hwpx_agent.get_idempotent_job_v2(",
            "JOIN hwpx_agent.revision_graph_seals AS seal",
            "JOIN hwpx_agent.revision_commit_receipts AS commit_receipt",
            "JOIN hwpx_agent.artifact_acl AS result_acl",
            "MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED'",
            "MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED'",
            "p_retry_class NOT IN ('transient_storage', 'transient_network')",
            "v_expires > v_record.expires_at",
            "max_attempts BETWEEN 1 AND 10",
            "expires_at <= created_at + interval '7 days'",
            "REVOKE ALL ON FUNCTION hwpx_agent.reconcile_idempotent_job_v2(",
            "VALUES (7, 'p14.idempotency_reconciliation_v2'",
        ],
        "idempotency up migration",
    )
    validate_commit_authorization_guard(up_sql)
    require_tokens(
        down_sql,
        [
            "requires explicit hwpx_agent.allow_destructive_rollback=on",
            "rollback requires later migrations removed first",
            "rollback refuses remaining version 2 data",
            "DROP TABLE hwpx_agent.idempotency_commit_authorizations",
            "DROP FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(",
            "DROP INDEX hwpx_agent.idempotency_v2_transaction_unique_idx",
            "CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_state_machine_update()",
            "MESSAGE = 'JOB_WORKER_NOT_QUALIFIED'",
            "DROP COLUMN record_version",
            "DELETE FROM hwpx_agent.schema_versions WHERE version = 7",
        ],
        "idempotency down migration",
    )
    require_tokens(
        smoke_sql,
        [
            "IDEMPOTENCY_KEY_CONFLICT",
            "IDEMPOTENCY_V2_TRANSITION_REQUIRED",
            "IDEMPOTENCY_RETRY_NOT_READY",
            "IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED",
            "IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH",
            "IDEMPOTENCY_COMMITTED_ORACLE_FAILED",
            "P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28",
        ],
        "idempotency smoke fixture",
    )
    if len(re.findall(r"v_assertions := v_assertions \+ 1;", smoke_sql)) != 28:
        fail("idempotency smoke fixture does not contain exactly 28 assertions")
    require_tokens(
        source_text,
        [
            "pub struct IdempotencyService",
            "pub enum ReconciliationObservation",
            "RevisionHead",
            "AutomationNoEffect",
            "oracle fact leaves the record frozen",
            "MAX_ATTEMPTS",
            "trusted_reconciliation_oracle_qualified",
            "Legacy version-1 rows remain readable",
        ],
        "idempotency Rust and durable-policy sources",
    )
    validate_security_definer_search_paths(up_sql)
    return {
        "state": "pass",
        "container_image": EXPECTED_IMAGE,
        "migration_functions": 11,
        "smoke_assertions": 28,
        "source_files": len(source_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    validated = validate_contract(args.contract.resolve(), ROOT)
    print(
        "P14_IDEMPOTENCY_RECONCILIATION_CONTRACT_PASS "
        f"functions={validated['migration_functions']} "
        f"assertions={validated['smoke_assertions']} "
        f"sources={validated['source_files']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"P14_IDEMPOTENCY_RECONCILIATION_CONTRACT_FAIL {error}")
        raise SystemExit(1) from error
