from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-metadata-v1.json"
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
    "migrations",
    "smoke_fixture",
    "required_tables",
    "tenant_scoped_tables",
    "invariants",
    "source_locks",
    "scope",
}
EXPECTED_TABLES = [
    "schema_versions",
    "tenants",
    "projects",
    "project_acl",
    "artifacts",
    "revisions",
    "branches",
    "revision_parents",
    "checkpoints",
    "jobs",
    "job_attempts",
    "idempotency_records",
    "audit_events",
]
EXPECTED_TENANT_TABLES = [
    "tenants",
    "projects",
    "branches",
    "project_acl",
    "artifacts",
    "revisions",
    "revision_parents",
    "checkpoints",
    "jobs",
    "job_attempts",
    "idempotency_records",
    "audit_events",
]
EXPECTED_INVARIANTS = {
    "row_level_security_forced": True,
    "cross_tenant_foreign_keys_composite": True,
    "revisions_immutable": True,
    "checkpoints_immutable": True,
    "audit_events_immutable": True,
    "artifact_content_identity_immutable": True,
    "job_request_identity_immutable": True,
    "job_attempt_identity_immutable": True,
    "idempotency_request_identity_immutable": True,
    "migration_digest_supplied_by_runner": True,
    "public_privileges_revoked": True,
    "database_extensions_required": False,
}


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
        raise ValueError("migration contract root must be an object")
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
        raise ValueError("contract file paths must be nonempty forward-slash paths")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"contract path escapes repository root: {relative_path}")
    unresolved = root / relative
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink() or (
            hasattr(cursor, "is_junction") and cursor.is_junction()
        ):
            raise ValueError(f"contract path contains a link or junction: {relative_path}")
    candidate = unresolved.resolve(strict=True)
    resolved_root = root.resolve(strict=True)
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise ValueError(f"contract path escapes repository root: {relative_path}")
    if not candidate.is_file():
        raise ValueError(f"contract path is not a regular file: {relative_path}")
    size = candidate.stat().st_size
    if size <= 0 or size > maximum_bytes:
        raise ValueError(f"contract file is outside its size bound: {relative_path}")
    return candidate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_digest(path: Path, expected: Any, label: str) -> None:
    if not isinstance(expected, str) or HEX_64.fullmatch(expected) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


def validate_up_sql(up_sql: str, tenant_tables: list[str]) -> None:
    if not up_sql.startswith("BEGIN;\n") or not up_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("up migration must have one explicit transaction boundary")
    if re.search(r"(?im)^\s*CREATE\s+EXTENSION\b", up_sql):
        raise ValueError("up migration must not require database extensions")
    if re.search(r"(?im)^\s*DROP\s+(?:SCHEMA|TABLE)\b", up_sql):
        raise ValueError("up migration contains a destructive drop")
    if re.search(r"(?m)^\s*\\", up_sql):
        raise ValueError("up migration contains a psql-only meta-command")

    created = re.findall(r"CREATE TABLE hwpx_agent\.([a-z_]+) \(", up_sql)
    if created != EXPECTED_TABLES:
        raise ValueError(f"created table sequence differs: {created}")

    rls_array_match = re.search(
        r"FOREACH table_name IN ARRAY ARRAY\[(.*?)\]\s+LOOP",
        up_sql,
        re.DOTALL,
    )
    if rls_array_match is None:
        raise ValueError("tenant RLS table array is missing")
    rls_tables = re.findall(r"'([a-z_]+)'", rls_array_match.group(1))
    if rls_tables != tenant_tables:
        raise ValueError(f"tenant RLS table sequence differs: {rls_tables}")

    if re.search(r"(?<![0-9a-f])0{64}(?![0-9a-f])", up_sql):
        raise ValueError("up migration contains a zero digest placeholder")

    required_snippets = [
        "CREATE POLICY tenant_isolation",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "tenant_id = hwpx_agent.current_tenant_id()",
        "REVOKE ALL ON SCHEMA hwpx_agent FROM PUBLIC",
        "REVOKE ALL ON ALL TABLES IN SCHEMA hwpx_agent FROM PUBLIC",
        "REVOKE ALL ON ALL SEQUENCES IN SCHEMA hwpx_agent FROM PUBLIC",
        "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA hwpx_agent FROM PUBLIC",
        "current_setting('hwpx_agent.migration_sha256')",
        "CREATE TRIGGER revisions_immutable",
        "CREATE TRIGGER checkpoints_immutable",
        "CREATE TRIGGER audit_events_immutable",
        "CREATE TRIGGER artifacts_protect_identity",
        "CREATE TRIGGER jobs_protect_identity",
        "CREATE TRIGGER job_attempts_protect_identity",
        "CREATE TRIGGER idempotency_protect_identity",
        "projects_head_revision_fk",
        "branches_one_default_idx",
        "jobs_active_lease_consistency",
        "jobs_terminal_result_consistency",
        "idempotency_terminal_consistency",
    ]
    for snippet in required_snippets:
        if snippet not in up_sql:
            raise ValueError(f"up migration is missing required SQL: {snippet}")


def validate_down_sql(down_sql: str) -> None:
    if not down_sql.startswith("BEGIN;\n") or not down_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("down migration must have one explicit transaction boundary")
    if re.search(r"(?m)^\s*\\", down_sql):
        raise ValueError("down migration contains a psql-only meta-command")
    required = [
        "current_setting('hwpx_agent.allow_destructive_rollback', true)",
        "IS DISTINCT FROM 'on'",
        "ERRCODE = '55000'",
        "DROP SCHEMA hwpx_agent CASCADE",
    ]
    for snippet in required:
        if snippet not in down_sql:
            raise ValueError(f"down migration is missing required SQL: {snippet}")
    if down_sql.count("DROP SCHEMA hwpx_agent CASCADE") != 1:
        raise ValueError("down migration must contain exactly one schema drop")


def validate_contract(contract_path: Path = DEFAULT_CONTRACT, root: Path = ROOT) -> dict[str, Any]:
    contract = load_json(contract_path)
    require_exact_keys(contract, EXPECTED_TOP_LEVEL_KEYS, "contract")
    if contract["schema_version"] != "hwpx-agent.p14-01-postgres-migration-contract/v1":
        raise ValueError("unexpected migration contract schema_version")
    if contract["contract_id"] != "p14-metadata-v1":
        raise ValueError("unexpected migration contract id")

    database = require_object(contract["database"], "database")
    require_exact_keys(
        database,
        {"engine", "tested_server_version", "container_image"},
        "database",
    )
    if database["engine"] != "postgresql" or database["tested_server_version"] != "18.4":
        raise ValueError("database engine/version pin differs")
    image = database["container_image"]
    if not isinstance(image, str) or re.fullmatch(
        r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image
    ) is None:
        raise ValueError("PostgreSQL image is not pinned by exact repository digest")
    if image != EXPECTED_IMAGE:
        raise ValueError("PostgreSQL image digest differs from the approved P14-01 pin")

    migrations = require_object(contract["migrations"], "migrations")
    require_exact_keys(
        migrations,
        {"up_path", "up_sha256", "down_path", "down_sha256", "rollback_gate_setting"},
        "migrations",
    )
    if migrations["rollback_gate_setting"] != "hwpx_agent.allow_destructive_rollback=on":
        raise ValueError("rollback gate setting differs")
    up_path = resolve_bounded_file(root, migrations["up_path"], 256 * 1024)
    down_path = resolve_bounded_file(root, migrations["down_path"], 32 * 1024)
    require_digest(up_path, migrations["up_sha256"], "up migration digest")
    require_digest(down_path, migrations["down_sha256"], "down migration digest")

    smoke = require_object(contract["smoke_fixture"], "smoke_fixture")
    require_exact_keys(smoke, {"path", "sha256", "assertions_per_run"}, "smoke_fixture")
    if smoke["assertions_per_run"] != 19:
        raise ValueError("smoke assertion count differs")
    smoke_path = resolve_bounded_file(root, smoke["path"], 256 * 1024)
    require_digest(smoke_path, smoke["sha256"], "smoke fixture digest")
    marker = "P14_METADATA_SMOKE_PASS assertions=19"
    if marker not in smoke_path.read_text(encoding="utf-8"):
        raise ValueError("smoke fixture exact pass marker is missing")

    if contract["required_tables"] != EXPECTED_TABLES:
        raise ValueError("required table sequence differs")
    if contract["tenant_scoped_tables"] != EXPECTED_TENANT_TABLES:
        raise ValueError("tenant-scoped table sequence differs")
    if contract["invariants"] != EXPECTED_INVARIANTS:
        raise ValueError("migration invariant declaration differs")

    source_locks = contract["source_locks"]
    if not isinstance(source_locks, list) or len(source_locks) != 3:
        raise ValueError("exactly three source locks are required")
    for index, source in enumerate(source_locks):
        source_object = require_object(source, f"source_locks[{index}]")
        require_exact_keys(source_object, {"path", "sha256"}, f"source_locks[{index}]")
        source_path = resolve_bounded_file(root, source_object["path"], 512 * 1024)
        require_digest(source_path, source_object["sha256"], f"source lock {index} digest")

    scope = require_object(contract["scope"], "scope")
    expected_scope = {
        "task": "P14-01",
        "current_pc_hancom_invoked": False,
        "user_documents_scanned": False,
        "production_database_qualified": False,
        "artifact_service_qualified": False,
        "later_p14_tasks_qualified": False,
    }
    if scope != expected_scope:
        raise ValueError("P14-01 scope declaration differs")

    validate_up_sql(up_path.read_text(encoding="utf-8"), EXPECTED_TENANT_TABLES)
    validate_down_sql(down_path.read_text(encoding="utf-8"))
    return {
        "schema_version": contract["schema_version"],
        "contract_id": contract["contract_id"],
        "table_count": len(EXPECTED_TABLES),
        "tenant_scoped_table_count": len(EXPECTED_TENANT_TABLES),
        "smoke_assertions_per_run": smoke["assertions_per_run"],
        "smoke_fixture_sha256": smoke["sha256"],
        "container_image": database["container_image"],
        "up_sha256": migrations["up_sha256"],
        "down_sha256": migrations["down_sha256"],
        "state": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path, nargs="?", default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    print(json.dumps(validate_contract(args.contract.resolve()), sort_keys=True))
    print("P14_METADATA_CONTRACT_PASS tables=13 tenant_scoped=12 assertions=19")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
