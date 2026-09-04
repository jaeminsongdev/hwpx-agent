from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-history-checkpoints-v1.json"
)
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
    "required_tables",
    "required_indexes",
    "required_functions",
    "required_triggers",
    "tenant_scoped_tables",
    "invariants",
    "source_locks",
    "scope",
}
EXPECTED_PREREQUISITES = [
    (1, "p14.metadata_v1"),
    (2, "p14.artifact_service_v1"),
    (3, "p14.revision_cas_v1"),
]
EXPECTED_TABLES = ["history_checkpoint_requests"]
EXPECTED_INDEXES = ["revision_graph_seals_history_order_idx"]
EXPECTED_FUNCTIONS = [
    "create_history_checkpoint",
    "create_history_branch",
    "query_revision_history",
]
EXPECTED_TRIGGERS = ["history_checkpoint_requests_immutable"]
EXPECTED_INVARIANTS = {
    "hmac_subject_tenant_bound_cursor": True,
    "cursor_expiry_and_page_bounds": True,
    "bounded_history_graph": True,
    "parent_generation_precedes_child": True,
    "stable_snapshot_head_pagination": True,
    "deterministic_merge_dag_query": True,
    "semantic_diff_artifact_indirection": True,
    "immutable_checkpoint": True,
    "checkpoint_idempotent_replay": True,
    "checkpoint_request_drift_denied": True,
    "qualified_revision_branch_only": True,
    "reader_history_only": True,
    "editor_or_owner_mutation": True,
    "cross_tenant_absence_or_denial": True,
    "legacy_revision_fail_closed": True,
    "transaction_local_request_context": True,
    "guarded_destructive_rollback": True,
    "migration_digest_supplied_by_runner": True,
    "database_extensions_required": False,
    "public_privileges_revoked": True,
}
EXPECTED_SOURCE_PATHS = [
    "docs/02_architecture/05_state_revision_transactions.md",
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "docs/06_mcp_api/01_tool_surface.md",
    "docs/06_mcp_api/02_tool_contracts.md",
    "docs/06_mcp_api/05_auth_permissions.md",
    "crates/history-service/Cargo.toml",
    "crates/history-service/src/lib.rs",
    "crates/history-service/src/cursor.rs",
    "crates/history-service/src/service.rs",
    "crates/history-service/src/store.rs",
    "crates/history-service/src/types.rs",
]


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
    )
    if not isinstance(value, dict):
        raise ValueError("history contract root must be an object")
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
        if cursor.is_symlink() or (
            hasattr(cursor, "is_junction") and cursor.is_junction()
        ):
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
    for table in EXPECTED_TABLES:
        if up_sql.count(f"CREATE TABLE hwpx_agent.{table} (") != 1:
            raise ValueError(f"required table differs: {table}")
    for index in EXPECTED_INDEXES:
        if not re.search(rf"CREATE INDEX {index}\b", up_sql):
            raise ValueError(f"required index is missing: {index}")
    for function in EXPECTED_FUNCTIONS:
        if up_sql.count(f"CREATE FUNCTION hwpx_agent.{function}(") != 1:
            raise ValueError(f"required function differs: {function}")
    for trigger in EXPECTED_TRIGGERS:
        if not re.search(rf"CREATE TRIGGER {trigger}\b", up_sql):
            raise ValueError(f"required trigger is missing: {trigger}")
    required_snippets = [
        "current_setting('hwpx_agent.migration_sha256', true)",
        "ON CONFLICT (tenant_id, project_id, request_id) DO NOTHING",
        "MESSAGE = 'HISTORY_IDEMPOTENCY_CONFLICT'",
        "MESSAGE = 'HISTORY_GRAPH_LIMIT_EXCEEDED'",
        "MESSAGE = 'HISTORY_LEGACY_REVISION_UNQUALIFIED'",
        "MESSAGE = 'HISTORY_GRAPH_GENERATION_INVALID'",
        "seal.seal_kind = 'service_v1'",
        "role IN ('editor', 'owner')",
        "role IN ('reader', 'editor', 'owner')",
        "p_limit NOT BETWEEN 1 AND 100",
        "WITH RECURSIVE reachable(revision_id)",
        "ORDER BY seal.committed_generation DESC, revision.revision_id",
        "'history.checkpoint_created'",
        "'history.branch_created'",
        "SECURITY DEFINER",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "REVOKE ALL ON FUNCTION hwpx_agent.create_history_checkpoint(",
        "REVOKE ALL ON FUNCTION hwpx_agent.create_history_branch(",
        "REVOKE ALL ON FUNCTION hwpx_agent.query_revision_history(",
        "'p14.history_checkpoints_v1'",
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
        "P14 history rollback requires explicit",
        "DROP FUNCTION hwpx_agent.query_revision_history(",
        "DROP FUNCTION hwpx_agent.create_history_branch(",
        "DROP FUNCTION hwpx_agent.create_history_checkpoint(",
        "DROP TABLE hwpx_agent.history_checkpoint_requests",
        "DELETE FROM hwpx_agent.schema_versions WHERE version = 4",
    ]
    for snippet in required_snippets:
        if snippet not in down_sql:
            raise ValueError(f"down migration is missing required SQL: {snippet}")
    if down_sql.index("DROP FUNCTION hwpx_agent.create_history_checkpoint(") > down_sql.index(
        "DROP TABLE hwpx_agent.history_checkpoint_requests"
    ):
        raise ValueError("down migration drops request storage before its writer")


def validate_contract(path: Path, root: Path = ROOT) -> dict[str, Any]:
    contract = load_json(path)
    require_exact_keys(contract, EXPECTED_TOP_LEVEL_KEYS, "contract")
    if contract["schema_version"] != "hwpx-agent.p14-04-history-checkpoints-contract/v1":
        raise ValueError("contract schema version differs")
    if contract["contract_id"] != "p14-history-checkpoints-v1":
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
    if not isinstance(prerequisites, list) or len(prerequisites) != 3:
        raise ValueError("exactly three prerequisite migrations are required")
    for index, (value, expected) in enumerate(
        zip(prerequisites, EXPECTED_PREREQUISITES, strict=True), start=1
    ):
        prerequisite = require_object(value, f"prerequisite {index}")
        require_exact_keys(
            prerequisite,
            {"version", "name", "up_path", "up_sha256", "down_path", "down_sha256"},
            f"prerequisite {index}",
        )
        if (prerequisite["version"], prerequisite["name"]) != expected:
            raise ValueError("prerequisite migration order or identity differs")
        up_path = resolve_bounded_file(root, prerequisite["up_path"], 256 * 1024)
        down_path = resolve_bounded_file(root, prerequisite["down_path"], 128 * 1024)
        require_digest(up_path, prerequisite["up_sha256"], f"prerequisite {index} up")
        require_digest(down_path, prerequisite["down_sha256"], f"prerequisite {index} down")

    migration = require_object(contract["migration"], "migration")
    require_exact_keys(
        migration,
        {"version", "name", "up_path", "up_sha256", "down_path", "down_sha256"},
        "migration",
    )
    if migration["version"] != 4 or migration["name"] != "p14.history_checkpoints_v1":
        raise ValueError("history migration identity differs")
    up_path = resolve_bounded_file(root, migration["up_path"], 256 * 1024)
    down_path = resolve_bounded_file(root, migration["down_path"], 128 * 1024)
    require_digest(up_path, migration["up_sha256"], "up migration")
    require_digest(down_path, migration["down_sha256"], "down migration")
    validate_up_sql(up_path.read_text(encoding="utf-8"))
    validate_down_sql(down_path.read_text(encoding="utf-8"))

    smoke = require_object(contract["smoke_fixture"], "smoke fixture")
    require_exact_keys(
        smoke, {"path", "sha256", "assertions_per_run", "pass_marker"}, "smoke fixture"
    )
    smoke_path = resolve_bounded_file(root, smoke["path"], 256 * 1024)
    require_digest(smoke_path, smoke["sha256"], "smoke fixture")
    if smoke["assertions_per_run"] != 26:
        raise ValueError("smoke assertion count differs")
    if smoke["pass_marker"] != "P14_HISTORY_SMOKE_PASS assertions=26":
        raise ValueError("smoke pass marker differs")
    smoke_sql = smoke_path.read_text(encoding="utf-8")
    if len(re.findall(r"(?m)^\s*-- assertion [0-9]{2}:", smoke_sql)) != 26:
        raise ValueError("smoke assertion comments differ")
    if smoke["pass_marker"] not in smoke_sql:
        raise ValueError("smoke pass marker is absent")

    if contract["required_tables"] != EXPECTED_TABLES:
        raise ValueError("required table list differs")
    if contract["required_indexes"] != EXPECTED_INDEXES:
        raise ValueError("required index list differs")
    if contract["required_functions"] != EXPECTED_FUNCTIONS:
        raise ValueError("required function list differs")
    if contract["required_triggers"] != EXPECTED_TRIGGERS:
        raise ValueError("required trigger list differs")
    if contract["tenant_scoped_tables"] != EXPECTED_TABLES:
        raise ValueError("tenant-scoped table list differs")
    if contract["invariants"] != EXPECTED_INVARIANTS:
        raise ValueError("invariant contract differs")

    source_locks = contract["source_locks"]
    if not isinstance(source_locks, list) or len(source_locks) != len(EXPECTED_SOURCE_PATHS):
        raise ValueError("source-lock count differs")
    observed_paths: list[str] = []
    for index, value in enumerate(source_locks):
        lock = require_object(value, f"source lock {index}")
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
            "production_http_api_qualified",
            "p14_phase_complete",
            "user_documents_used",
        },
        "scope",
    )
    if scope != {
        "current_pc_local_development_only": True,
        "production_database_qualified": False,
        "production_http_api_qualified": False,
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
    print("P14_HISTORY_CONTRACT_PASS functions=3 assertions=26")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"P14_HISTORY_CONTRACT_FAILED: {error}")
        raise SystemExit(2)
