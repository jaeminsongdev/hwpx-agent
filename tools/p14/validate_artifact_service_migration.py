from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-artifact-service-v1.json"
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
    "prerequisite",
    "migration",
    "smoke_fixture",
    "required_artifact_columns",
    "required_tables",
    "required_functions",
    "required_triggers",
    "tenant_scoped_tables",
    "invariants",
    "source_locks",
    "scope",
}
EXPECTED_COLUMNS = [
    "service_metadata_version",
    "filename",
    "object_key",
    "encryption_algorithm",
    "encryption_nonce",
    "aad_sha256",
    "ciphertext_sha256",
    "validation_state",
    "scanner_engine_ref",
    "scanner_signature_version",
    "authorization_generation",
    "legacy_storage_state",
    "legacy_quarantine_reason_code",
    "legacy_verified_at",
]
EXPECTED_FUNCTIONS = [
    "protect_artifact_service_identity",
    "protect_artifact_acl_identity",
    "bump_artifact_acl_generation",
    "require_artifact_manager",
]
EXPECTED_TRIGGERS = [
    "artifacts_protect_service_identity",
    "artifact_acl_protect_identity",
    "artifact_acl_touch_updated_at",
    "artifact_acl_bump_generation",
    "artifact_acl_manager_required",
    "artifact_service_manager_required",
]
EXPECTED_INVARIANTS = {
    "content_addressed_object_key_bound": True,
    "aes_256_gcm_metadata_complete": True,
    "scanner_evidence_complete": True,
    "legacy_artifact_fail_closed": True,
    "artifact_acl_forced_rls": True,
    "cross_tenant_artifact_denial": True,
    "cross_tenant_acl_denial": True,
    "authorization_generation_on_acl_change": True,
    "authorization_generation_on_quarantine_change": True,
    "final_manager_required": True,
    "encryption_identity_immutable": True,
    "rollback_preserves_version_1": True,
    "legacy_artifact_rollback_restores_v1": True,
    "transaction_local_tenant_context": True,
    "migration_digest_supplied_by_runner": True,
    "database_extensions_required": False,
    "public_privileges_revoked": True,
}
EXPECTED_SOURCE_PATHS = [
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "docs/06_mcp_api/06_jobs_artifacts.md",
    "docs/06_mcp_api/05_auth_permissions.md",
    "crates/artifact-service/Cargo.toml",
    "crates/foundation/src/workdir.rs",
    "crates/artifact-service/src/crypto.rs",
    "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/signed_url.rs",
    "crates/artifact-service/src/store.rs",
    "crates/artifact-service/src/types.rs",
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
        raise ValueError("artifact service contract root must be an object")
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


def qualified_source_replacements(root: Path) -> dict[str, tuple[str, str]]:
    # Execute the validator's trusted sibling, never Python supplied by a candidate data root.
    path = Path(__file__).resolve().parents[1] / "p16/postgres_artifact_qualification.py"
    try:
        spec = importlib.util.spec_from_file_location("p14_p16_postgres_source_qualification", path)
        if spec is None or spec.loader is None:
            return {}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.verified_replacements(root)
    except (OSError, ImportError, ValueError):
        # An absent/invalid successor is not permission: the original digest check below fails.
        return {}


def validate_up_sql(up_sql: str) -> None:
    if not up_sql.startswith("BEGIN;\n") or not up_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("up migration must have an explicit transaction boundary")
    if re.search(r"(?im)^\s*CREATE\s+EXTENSION\b", up_sql):
        raise ValueError("up migration must not require database extensions")
    if re.search(r"(?im)^\s*DROP\s+(?:SCHEMA|TABLE)\b", up_sql):
        raise ValueError("up migration contains a destructive drop")
    if re.search(r"(?m)^\s*\\", up_sql):
        raise ValueError("up migration contains a psql-only meta-command")
    if up_sql.count("CREATE TABLE hwpx_agent.artifact_acl (") != 1:
        raise ValueError("artifact_acl table declaration differs")
    if re.search(r"(?<![0-9a-f])0{64}(?![0-9a-f])", up_sql):
        raise ValueError("up migration contains a zero digest placeholder")

    added_columns = re.findall(r"ADD COLUMN ([a-z0-9_]+)", up_sql)
    if added_columns != EXPECTED_COLUMNS:
        raise ValueError(f"artifact column sequence differs: {added_columns}")
    for function in EXPECTED_FUNCTIONS:
        if f"CREATE FUNCTION hwpx_agent.{function}()" not in up_sql:
            raise ValueError(f"required function is missing: {function}")
    for trigger in EXPECTED_TRIGGERS:
        if not re.search(rf"CREATE (?:CONSTRAINT )?TRIGGER {trigger}\b", up_sql):
            raise ValueError(f"required trigger is missing: {trigger}")

    required_snippets = [
        "current_setting('hwpx_agent.migration_sha256', true)",
        "current_setting('hwpx_agent.migration_sha256')",
        "object_key = concat(",
        "'artifacts/v1/'",
        "'AES-256-GCM'",
        "octet_length(encryption_nonce) = 12",
        "service_metadata_version = 1",
        "storage_state IN ('staged', 'orphaned', 'purging')",
        "SET legacy_storage_state = storage_state",
        "artifacts_legacy_recovery_complete",
        "artifact ACL must retain at least one manager",
        "authorization_generation = authorization_generation + 1",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON hwpx_agent.artifact_acl",
        "tenant_id = hwpx_agent.current_tenant_id()",
        "REVOKE ALL ON TABLE hwpx_agent.artifact_acl FROM PUBLIC",
        "SECURITY DEFINER",
        "'p14.artifact_service_v1'",
    ]
    for snippet in required_snippets:
        if snippet not in up_sql:
            raise ValueError(f"up migration is missing required SQL: {snippet}")


def validate_down_sql(down_sql: str) -> None:
    if not down_sql.startswith("BEGIN;\n") or not down_sql.rstrip().endswith("COMMIT;"):
        raise ValueError("down migration must have an explicit transaction boundary")
    if re.search(r"(?m)^\s*\\", down_sql):
        raise ValueError("down migration contains a psql-only meta-command")
    if re.search(r"(?im)^\s*DROP\s+SCHEMA\b", down_sql):
        raise ValueError("version 2 rollback must preserve the version 1 schema")
    dropped_tables = re.findall(r"DROP TABLE hwpx_agent\.([a-z_]+);", down_sql)
    if dropped_tables != ["artifact_acl"]:
        raise ValueError(f"rollback table scope differs: {dropped_tables}")
    required = [
        "current_setting('hwpx_agent.allow_destructive_rollback', true)",
        "IS DISTINCT FROM 'on'",
        "DROP TABLE hwpx_agent.artifact_acl;",
        "SET storage_state = legacy_storage_state",
        "DISABLE TRIGGER schema_versions_immutable",
        "DELETE FROM hwpx_agent.schema_versions WHERE version = 2",
        "ENABLE TRIGGER schema_versions_immutable",
    ]
    for snippet in required:
        if snippet not in down_sql:
            raise ValueError(f"down migration is missing required SQL: {snippet}")
    dropped_columns = re.findall(r"DROP COLUMN ([a-z0-9_]+)", down_sql)
    if dropped_columns != list(reversed(EXPECTED_COLUMNS)):
        raise ValueError(f"rollback column sequence differs: {dropped_columns}")


def validate_contract(
    contract_path: Path = DEFAULT_CONTRACT, root: Path = ROOT
) -> dict[str, Any]:
    contract = load_json(contract_path)
    require_exact_keys(contract, EXPECTED_TOP_LEVEL_KEYS, "contract")
    if contract["schema_version"] != "hwpx-agent.p14-02-artifact-service-contract/v1":
        raise ValueError("unexpected artifact service contract schema_version")
    if contract["contract_id"] != "p14-artifact-service-v1":
        raise ValueError("unexpected artifact service contract id")

    database = require_object(contract["database"], "database")
    require_exact_keys(
        database, {"engine", "tested_server_version", "container_image"}, "database"
    )
    if database["engine"] != "postgresql" or database["tested_server_version"] != "18.4":
        raise ValueError("database engine/version differs")
    if database["container_image"] != EXPECTED_IMAGE:
        raise ValueError("PostgreSQL image is not the exact approved digest")

    prerequisite = require_object(contract["prerequisite"], "prerequisite")
    require_exact_keys(
        prerequisite,
        {"version", "migration_name", "up_path", "up_sha256", "down_path", "down_sha256"},
        "prerequisite",
    )
    if prerequisite["version"] != 1 or prerequisite["migration_name"] != "p14.metadata_v1":
        raise ValueError("version 1 prerequisite differs")
    prerequisite_up = resolve_bounded_file(root, prerequisite["up_path"], 256 * 1024)
    prerequisite_down = resolve_bounded_file(root, prerequisite["down_path"], 32 * 1024)
    require_digest(prerequisite_up, prerequisite["up_sha256"], "prerequisite up digest")
    require_digest(prerequisite_down, prerequisite["down_sha256"], "prerequisite down digest")

    migration = require_object(contract["migration"], "migration")
    require_exact_keys(
        migration,
        {
            "version",
            "migration_name",
            "up_path",
            "up_sha256",
            "down_path",
            "down_sha256",
            "rollback_gate_setting",
        },
        "migration",
    )
    if migration["version"] != 2 or migration["migration_name"] != "p14.artifact_service_v1":
        raise ValueError("version 2 migration identity differs")
    if migration["rollback_gate_setting"] != "hwpx_agent.allow_destructive_rollback=on":
        raise ValueError("rollback gate setting differs")
    up_path = resolve_bounded_file(root, migration["up_path"], 256 * 1024)
    down_path = resolve_bounded_file(root, migration["down_path"], 64 * 1024)
    require_digest(up_path, migration["up_sha256"], "up migration digest")
    require_digest(down_path, migration["down_sha256"], "down migration digest")

    smoke = require_object(contract["smoke_fixture"], "smoke_fixture")
    require_exact_keys(
        smoke, {"path", "sha256", "assertions_per_run", "pass_marker"}, "smoke_fixture"
    )
    if smoke["assertions_per_run"] != 22:
        raise ValueError("smoke assertion count differs")
    if smoke["pass_marker"] != "P14_ARTIFACT_SERVICE_SMOKE_PASS assertions=22":
        raise ValueError("smoke pass marker differs")
    smoke_path = resolve_bounded_file(root, smoke["path"], 256 * 1024)
    require_digest(smoke_path, smoke["sha256"], "smoke fixture digest")
    smoke_text = smoke_path.read_text(encoding="utf-8")
    if smoke_text.count("-- ASSERT:") != 22 or smoke["pass_marker"] not in smoke_text:
        raise ValueError("smoke assertion markers differ")
    for snippet in [
        "'hwpx_agent.tenant_id', '10000000-0000-0000-0000-000000000001', true",
        "nullif(current_setting('hwpx_agent.tenant_id', true), '') IS NOT NULL",
    ]:
        if snippet not in smoke_text:
            raise ValueError(f"smoke fixture is missing transaction-local context proof: {snippet}")

    if contract["required_artifact_columns"] != EXPECTED_COLUMNS:
        raise ValueError("required artifact column sequence differs")
    if contract["required_tables"] != ["artifact_acl"]:
        raise ValueError("required table sequence differs")
    if contract["required_functions"] != EXPECTED_FUNCTIONS:
        raise ValueError("required function sequence differs")
    if contract["required_triggers"] != EXPECTED_TRIGGERS:
        raise ValueError("required trigger sequence differs")
    if contract["tenant_scoped_tables"] != ["artifact_acl"]:
        raise ValueError("tenant-scoped table sequence differs")
    if contract["invariants"] != EXPECTED_INVARIANTS:
        raise ValueError("artifact invariant declaration differs")

    # Keep malformed SQL mutations attributable to their semantic guard. Source admission remains
    # mandatory after these read-only checks and before a successful result.
    validate_up_sql(up_path.read_text(encoding="utf-8"))
    validate_down_sql(down_path.read_text(encoding="utf-8"))
    replacements = None
    successor_bound: list[str] = []
    sources = contract["source_locks"]
    if not isinstance(sources, list) or [source.get("path") for source in sources] != EXPECTED_SOURCE_PATHS:
        raise ValueError("source lock path sequence differs")
    for index, source in enumerate(sources):
        source_object = require_object(source, f"source_locks[{index}]")
        require_exact_keys(source_object, {"path", "sha256"}, f"source_locks[{index}]")
        source_path = resolve_bounded_file(root, source_object["path"], 512 * 1024)
        expected = source_object["sha256"]
        observed = digest(source_path)
        if isinstance(expected, str) and HEX_64.fullmatch(expected) and observed != expected:
            if replacements is None:
                replacements = qualified_source_replacements(root)
            if replacements.get(source_object["path"]) == (expected, observed):
                successor_bound.append(source_object["path"])
                continue
        require_digest(source_path, expected, f"source lock {index} digest")

    expected_scope = {
        "task": "P14-02",
        "current_pc_hancom_invoked": False,
        "user_documents_scanned": False,
        "production_object_store_qualified": False,
        "production_kms_qualified": False,
        "production_malware_scanner_qualified": False,
        "later_p14_tasks_qualified": False,
    }
    if contract["scope"] != expected_scope:
        raise ValueError("P14-02 scope declaration differs")

    return {
        "schema_version": contract["schema_version"],
        "contract_id": contract["contract_id"],
        "artifact_column_count": len(EXPECTED_COLUMNS),
        "smoke_assertions_per_run": smoke["assertions_per_run"],
        "container_image": database["container_image"],
        "prerequisite_up_sha256": prerequisite["up_sha256"],
        "up_sha256": migration["up_sha256"],
        "down_sha256": migration["down_sha256"],
        "smoke_fixture_sha256": smoke["sha256"],
        "source_qualification": {
            "successor_id": "p16.local_postgres_artifact.217ba56" if successor_bound else None,
            "successor_bound_paths": successor_bound,
            "phase_completion_claimed": False,
        },
        "state": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path, nargs="?", default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    print(json.dumps(validate_contract(args.contract.resolve()), sort_keys=True))
    print("P14_ARTIFACT_SERVICE_CONTRACT_PASS columns=14 assertions=22")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
