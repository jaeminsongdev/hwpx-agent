from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "implementation" / "p14" / "postgres" / "p14-revision-cas-v1.json"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_IMAGE = (
    "postgres:18.4-bookworm@"
    "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "database",
    "prerequisites",
    "migration",
    "smoke_fixture",
    "required_columns",
    "required_tables",
    "required_functions",
    "required_triggers",
    "tenant_scoped_tables",
    "invariants",
    "source_locks",
    "scope",
}
EXPECTED_COLUMNS = ["projects.head_generation", "branches.head_generation"]
EXPECTED_TABLES = ["revision_graph_seals", "revision_commit_receipts"]
EXPECTED_FUNCTIONS = [
    "current_subject_sha256",
    "guard_revision_parent_insert",
    "commit_revision_cas",
]
EXPECTED_TRIGGERS = [
    "revision_parents_guard_insert",
    "revision_graph_seals_immutable",
    "revision_commit_receipts_immutable",
]
EXPECTED_TENANT_TABLES = ["revision_graph_seals", "revision_commit_receipts"]
EXPECTED_INVARIANTS = {
    "immutable_sealed_dag": True,
    "expected_head_generation_cas": True,
    "stale_conflict_side_effect_free": True,
    "concurrent_single_winner": True,
    "default_project_branch_atomic_mirror": True,
    "independent_branch_heads": True,
    "cross_tenant_revision_denial": True,
    "project_editor_or_owner_required": True,
    "available_verified_artifacts_required": True,
    "verified_revision_only": True,
    "legacy_heads_fail_closed": True,
    "transaction_local_request_context": True,
    "guarded_destructive_rollback": True,
    "migration_digest_supplied_by_runner": True,
    "database_extensions_required": False,
    "public_privileges_revoked": True,
}
EXPECTED_SOURCE_PATHS = [
    "docs/02_architecture/05_state_revision_transactions.md",
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "crates/revision-service/Cargo.toml",
    "crates/revision-service/src/lib.rs",
    "crates/revision-service/src/service.rs",
    "crates/revision-service/src/store.rs",
    "crates/revision-service/src/types.rs",
]


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("revision CAS contract root must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{label} keys differ: missing={sorted(expected - actual)} "
            f"unknown={sorted(actual - expected)}"
        )


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def resolve_bounded_file(root: Path, relative_path: Any, maximum_bytes: int) -> Path:
    if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path:
        raise ValueError("contract paths must be nonempty forward-slash paths")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"contract path escapes repository root: {relative_path}")
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ValueError(f"contract path contains a link or junction: {relative_path}")
    candidate = (root / relative).resolve(strict=True)
    resolved_root = root.resolve(strict=True)
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise ValueError(f"contract path escapes repository root: {relative_path}")
    if not candidate.is_file() or not (0 < candidate.stat().st_size <= maximum_bytes):
        raise ValueError(f"contract file is outside its regular-file bound: {relative_path}")
    return candidate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_digest(path: Path, expected: Any, label: str) -> None:
    if not isinstance(expected, str) or HEX_64.fullmatch(expected) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


def validate_up_sql(up_sql: str) -> None:
    if not up_sql.startswith("BEGIN;\n") or not up_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("up migration must have an explicit transaction boundary")
    if re.search(r"(?im)^\s*CREATE\s+EXTENSION\b", up_sql):
        raise ValueError("up migration must not require database extensions")
    if re.search(r"(?im)^\s*DROP\s+(?:SCHEMA|TABLE)\b", up_sql):
        raise ValueError("up migration contains a destructive drop")
    if re.search(r"(?m)^\s*\\", up_sql):
        raise ValueError("up migration contains a psql-only meta-command")
    if up_sql.count("ADD COLUMN head_generation bigint NOT NULL DEFAULT 0") != 2:
        raise ValueError("project/branch head-generation columns differ")
    for table in EXPECTED_TABLES:
        if up_sql.count(f"CREATE TABLE hwpx_agent.{table} (") != 1:
            raise ValueError(f"required table differs: {table}")
    for function in EXPECTED_FUNCTIONS:
        if f"CREATE FUNCTION hwpx_agent.{function}(" not in up_sql:
            raise ValueError(f"required function is missing: {function}")
    for trigger in EXPECTED_TRIGGERS:
        if not re.search(rf"CREATE TRIGGER {trigger}\b", up_sql):
            raise ValueError(f"required trigger is missing: {trigger}")

    required_snippets = [
        "current_setting('hwpx_agent.migration_sha256', true)",
        "SET head_generation = -1",
        "seal_kind IN ('legacy_unqualified', 'service_v1')",
        "MESSAGE = 'REVISION_GRAPH_SEALED'",
        "MESSAGE = 'REVISION_GRAPH_CYCLE'",
        "MESSAGE = 'REVISION_CONTEXT_MISMATCH'",
        "MESSAGE = 'REVISION_COMMIT_DENIED'",
        "MESSAGE = 'REVISION_LEGACY_HEAD_UNQUALIFIED'",
        "MESSAGE = 'REVISION_DEFAULT_HEAD_INCONSISTENT'",
        "'conflict'::text",
        "FOR UPDATE OF branch, project",
        "role IN ('editor', 'owner')",
        "storage_state = 'available'",
        "validation_state = 'verified'",
        "INSERT INTO hwpx_agent.revision_graph_seals",
        "INSERT INTO hwpx_agent.revision_commit_receipts",
        "'revision.cas_committed'",
        "SECURITY DEFINER",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "REVOKE ALL ON FUNCTION hwpx_agent.commit_revision_cas(",
        "'p14.revision_cas_v1'",
    ]
    for snippet in required_snippets:
        if snippet not in up_sql:
            raise ValueError(f"up migration is missing required SQL: {snippet}")


def validate_down_sql(down_sql: str) -> None:
    if not down_sql.startswith("BEGIN;\n") or not down_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("down migration must have an explicit transaction boundary")
    if re.search(r"(?m)^\s*\\", down_sql):
        raise ValueError("down migration contains a psql-only meta-command")
    required_snippets = [
        "hwpx_agent.allow_destructive_rollback",
        "P14 revision CAS rollback requires explicit",
        "DROP FUNCTION hwpx_agent.commit_revision_cas(",
        "DROP TABLE hwpx_agent.revision_commit_receipts",
        "DROP TABLE hwpx_agent.revision_graph_seals",
        "DROP COLUMN head_generation",
        "DELETE FROM hwpx_agent.schema_versions WHERE version = 3",
    ]
    for snippet in required_snippets:
        if snippet not in down_sql:
            raise ValueError(f"down migration is missing required SQL: {snippet}")
    if down_sql.index("DROP FUNCTION hwpx_agent.commit_revision_cas(") > down_sql.index(
        "DROP TABLE hwpx_agent.revision_commit_receipts"
    ):
        raise ValueError("down migration drops receipt storage before the writer function")


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, Any]:
    contract = load_json(path)
    require_exact_keys(contract, EXPECTED_TOP_LEVEL_KEYS, "contract")
    if contract["schema_version"] != "hwpx-agent.p14-03-revision-cas-contract/v1":
        raise ValueError("contract schema version differs")
    if contract["contract_id"] != "p14-revision-cas-v1":
        raise ValueError("contract id differs")

    database = require_object(contract["database"], "database")
    require_exact_keys(database, {"engine", "server_version", "container_image"}, "database")
    if database != {
        "engine": "PostgreSQL",
        "server_version": "18.4",
        "container_image": EXPECTED_IMAGE,
    }:
        raise ValueError("database pin differs")

    prerequisites = contract["prerequisites"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 2:
        raise ValueError("exactly two prerequisite migrations are required")
    prerequisite_paths: list[Path] = []
    for index, prerequisite_value in enumerate(prerequisites, start=1):
        prerequisite = require_object(prerequisite_value, f"prerequisite {index}")
        require_exact_keys(
            prerequisite,
            {"version", "name", "up_path", "up_sha256", "down_path", "down_sha256"},
            f"prerequisite {index}",
        )
        if prerequisite["version"] != index:
            raise ValueError("prerequisite migration order differs")
        up_path = resolve_bounded_file(root, prerequisite["up_path"], 256 * 1024)
        down_path = resolve_bounded_file(root, prerequisite["down_path"], 128 * 1024)
        require_digest(up_path, prerequisite["up_sha256"], f"prerequisite {index} up")
        require_digest(down_path, prerequisite["down_sha256"], f"prerequisite {index} down")
        prerequisite_paths.extend([up_path, down_path])

    migration = require_object(contract["migration"], "migration")
    require_exact_keys(migration, {"version", "name", "up_path", "up_sha256", "down_path", "down_sha256"}, "migration")
    if migration["version"] != 3 or migration["name"] != "p14.revision_cas_v1":
        raise ValueError("revision CAS migration identity differs")
    up_path = resolve_bounded_file(root, migration["up_path"], 256 * 1024)
    down_path = resolve_bounded_file(root, migration["down_path"], 128 * 1024)
    require_digest(up_path, migration["up_sha256"], "up migration")
    require_digest(down_path, migration["down_sha256"], "down migration")
    validate_up_sql(up_path.read_text(encoding="utf-8"))
    validate_down_sql(down_path.read_text(encoding="utf-8"))

    smoke = require_object(contract["smoke_fixture"], "smoke fixture")
    require_exact_keys(smoke, {"path", "sha256", "assertions_per_run", "pass_marker"}, "smoke fixture")
    smoke_path = resolve_bounded_file(root, smoke["path"], 256 * 1024)
    require_digest(smoke_path, smoke["sha256"], "smoke fixture")
    if smoke["assertions_per_run"] != 20 or smoke["pass_marker"] != "P14_REVISION_CAS_SMOKE_PASS assertions=20":
        raise ValueError("smoke assertion contract differs")
    smoke_sql = smoke_path.read_text(encoding="utf-8")
    if len(re.findall(r"(?m)^-- assertion [0-9]{2}:", smoke_sql)) != 20:
        raise ValueError("smoke assertion comments differ")
    if str(smoke["pass_marker"]) not in smoke_sql:
        raise ValueError("smoke pass marker is absent")

    if contract["required_columns"] != EXPECTED_COLUMNS:
        raise ValueError("required column list differs")
    if contract["required_tables"] != EXPECTED_TABLES:
        raise ValueError("required table list differs")
    if contract["required_functions"] != EXPECTED_FUNCTIONS:
        raise ValueError("required function list differs")
    if contract["required_triggers"] != EXPECTED_TRIGGERS:
        raise ValueError("required trigger list differs")
    if contract["tenant_scoped_tables"] != EXPECTED_TENANT_TABLES:
        raise ValueError("tenant-scoped table list differs")
    if contract["invariants"] != EXPECTED_INVARIANTS:
        raise ValueError("invariant contract differs")

    source_locks = contract["source_locks"]
    if not isinstance(source_locks, list) or len(source_locks) != len(EXPECTED_SOURCE_PATHS):
        raise ValueError("source-lock count differs")
    observed_paths: list[str] = []
    for index, lock_value in enumerate(source_locks):
        lock = require_object(lock_value, f"source lock {index}")
        require_exact_keys(lock, {"path", "sha256"}, f"source lock {index}")
        observed_paths.append(str(lock["path"]))
        source_path = resolve_bounded_file(root, lock["path"], 2 * 1024 * 1024)
        require_digest(source_path, lock["sha256"], f"source lock {index}")
    if observed_paths != EXPECTED_SOURCE_PATHS:
        raise ValueError("source-lock path order differs")

    scope = require_object(contract["scope"], "scope")
    require_exact_keys(
        scope,
        {
            "current_pc_local_development_only",
            "production_database_qualified",
            "production_object_store_qualified",
            "p14_phase_complete",
            "user_documents_used",
        },
        "scope",
    )
    if scope != {
        "current_pc_local_development_only": True,
        "production_database_qualified": False,
        "production_object_store_qualified": False,
        "p14_phase_complete": False,
        "user_documents_used": False,
    }:
        raise ValueError("scope contract differs")

    return {
        "schema_version": contract["schema_version"],
        "contract_id": contract["contract_id"],
        "container_image": database["container_image"],
        "prerequisite_up_sha256": [value["up_sha256"] for value in prerequisites],
        "up_sha256": migration["up_sha256"],
        "down_sha256": migration["down_sha256"],
        "smoke_fixture_sha256": smoke["sha256"],
        "smoke_assertions_per_run": smoke["assertions_per_run"],
        "state": "pass",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_contract(args.contract.resolve(), ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("P14_REVISION_CAS_CONTRACT_PASS tables=2 assertions=20")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"P14_REVISION_CAS_CONTRACT_FAILED: {error}")
        raise SystemExit(2)
