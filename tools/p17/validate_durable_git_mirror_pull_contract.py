"""Validate the bounded P17 authenticated durable Git mirror pull contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "protocol/private/p17-durable-git-mirror-pull-v1.json"
ADAPTER_CONTRACT = ROOT / "protocol/private/p17-remote-sync-adapter-v4.json"
ADAPTER_MIGRATION = ROOT / "protocol/migrations/p17-remote-sync-request-v3-to-v4.md"
POLICY = ROOT / "protocol/migrations/p17-durable-git-mirror-pull-v1.md"
REPORT = ROOT / "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PULL_V16.md"
MIGRATION_UP = ROOT / "migrations/postgres/0017_p17_durable_git_mirror_pull.up.sql"
MIGRATION_DOWN = ROOT / "migrations/postgres/0017_p17_durable_git_mirror_pull.down.sql"
LOCAL_SYNC = ROOT / "crates/local-sync/src/lib.rs"
ADAPTER = ROOT / "crates/local-sync/src/adapter.rs"
SOURCE = ROOT / "crates/remote-sync-host/src/durable_git_pull.rs"
HOST = ROOT / "crates/remote-sync-host/examples/postgres_durable_git_pull_host.rs"
CLIENT = ROOT / "crates/remote-sync-host/examples/postgres_durable_git_pull_client.rs"
HARNESS = ROOT / "tools/p17/run_durable_git_mirror_pull_checks.py"
SEED = ROOT / "tools/p17/fixtures/p17_durable_git_mirror_pull_seed.sql"
RUN_ID = "4162580f49da402983be6a8527e9721e"
RECEIPT = ROOT / f"artifacts/p17/durable-git-mirror-pull/runs/{RUN_ID}/receipt.json"
RECEIPT_SHA256 = "059ec3ebbf1f871af86b7df84fc38a878bb2ca52fb68f3074b6b419668f390a5"
IMAGE = (
    "postgres:18.4-bookworm@sha256:"
    "7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
)
IMAGE_ID = "sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
CHECKS = (
    "pinned_postgres_loopback_container",
    "all_seventeen_exact_migrations",
    "rollback_requires_gate_and_empty_reapply_succeeds",
    "dedicated_function_only_role",
    "exact_local_bare_git_repository",
    "exact_observed_snapshot_backfill_and_seed",
    "git_and_database_seeded_by_durable_push",
    "clean_remote_advance_is_atomic",
    "updated_response_replays_without_second_observation",
    "ahead_remote_advance_records_conflict",
    "conflict_preserves_local_snapshot_and_plan",
    "conflict_response_replays_exactly",
    "same_head_same_snapshot_is_unchanged",
    "three_immutable_observations_and_one_conflict",
    "terminal_observation_is_immutable",
    "git_database_drift_is_unavailable_without_mutation",
    "missing_execute_privilege_rejected",
    "public_execute_drift_rejected",
    "observation_trigger_drift_rejected",
    "retained_observation_rollback_refused",
)
MIGRATIONS = tuple(
    f"migrations/postgres/{number:04d}_{name}.up.sql"
    for number, name in (
        (1, "p14_metadata"),
        (2, "p14_artifact_service"),
        (3, "p14_revision_cas"),
        (4, "p14_history_checkpoints"),
        (5, "p14_job_state_machine"),
        (6, "p14_worker_lease_fencing"),
        (7, "p14_idempotency_reconciliation"),
        (8, "p14_cancel_cleanup"),
        (9, "p14_retention_local_mirror"),
        (10, "p16_artifact_repository"),
        (11, "p16_plan_source"),
        (12, "p16_durable_plan_store"),
        (13, "p16_plan_review_evidence"),
        (14, "p17_history_checkpoint_note"),
        (15, "p17_atomic_mirror_checkpoint"),
        (16, "p17_durable_git_mirror_push"),
        (17, "p17_durable_git_mirror_pull"),
    )
)
RECEIPT_SOURCES = (
    "crates/local-sync/src/adapter.rs",
    "crates/local-sync/src/lib.rs",
    "crates/remote-sync-host/src/durable_git_pull.rs",
    "crates/remote-sync-host/src/durable_git_push.rs",
    "crates/remote-sync-host/src/git_mirror.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_pull_host.rs",
    "crates/remote-sync-host/examples/postgres_durable_git_pull_client.rs",
    "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql",
    "tools/p17/fixtures/p17_durable_git_mirror_pull_seed.sql",
    "tools/p17/run_durable_git_mirror_pull_checks.py",
    "implementation/p14/postgres/p14-artifact-service-v1.json",
    *MIGRATIONS,
    "migrations/postgres/0017_p17_durable_git_mirror_pull.down.sql",
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"rev_[0-9a-f]{32}\Z")
OID40 = re.compile(r"[0-9a-f]{40}\Z")


class ContractError(RuntimeError):
    """Fail-closed validation error containing only a bounded code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def load_unique(path: Path, maximum: int = 262_144) -> dict[str, Any]:
    require(
        path.is_file()
        and not path.is_symlink()
        and not (hasattr(path, "is_junction") and path.is_junction())
        and 0 < path.stat().st_size <= maximum,
        "document.file",
    )

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            require(key not in result, "document.duplicate_key")
            result[key] = value
        return result

    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("document.parse") from error
    require(isinstance(document, dict), "document.type")
    return document


def digest_file(path: Path) -> str:
    require(path.is_file() and 0 < path.stat().st_size <= 4_000_000, "source.file")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate(document: dict[str, Any]) -> None:
    require(
        list(document)
        == [
            "schema_version",
            "scope",
            "request",
            "database",
            "git",
            "reconciliation",
            "rollback",
            "transport",
            "evidence",
        ],
        "contract.keys",
    )
    require(
        document["schema_version"] == "hwpx-agent.durable-git-mirror-pull/v1"
        and document["scope"]
        == "current_pc_postgresql_local_bare_git_authenticated_loopback_component",
        "contract.identity",
    )
    request = document["request"]
    require(
        request
        == {
            "wire_schema": "hwpx-agent.remote-sync-request/v4",
            "operation": "pull",
            "canonical_json_required": True,
            "maximum_bytes": 16_384,
            "authentication_scope": "mirror.sync",
            "single_use_credential": True,
            "request_sha256_bound": True,
            "observed_head_bound": True,
            "observed_snapshot_sha256_bound": True,
            "observation_id_derived_from_authenticated_request": True,
        },
        "contract.request",
    )
    database = document["database"]
    require(database.get("exact_schema_version") == 17, "contract.database.version")
    require(
        database.get("outcomes") == ["unchanged", "updated", "conflict"],
        "contract.database.outcomes",
    )
    for claim in (
        "observed_snapshot_backfilled_and_required",
        "remote_revision_artifact_verified_and_acl_checked",
        "serializable_reconciliation",
        "clean_advance_is_atomic",
        "ahead_conflict_preserves_local_snapshot_and_plan",
        "terminal_observation_is_immutable",
        "exact_replay_creates_no_second_observation_or_conflict",
        "tenant_rls_forced",
        "security_definer_search_path_fixed",
        "public_execute_revoked",
    ):
        require(database.get(claim) is True, f"contract.database.{claim}")
    require(database.get("application_role_has_table_mutation") is False, "contract.database.role")
    git = document["git"]
    require(git.get("access") == "read_only", "contract.git.access")
    require(git.get("reference_is_derived") is True, "contract.git.reference")
    require(git.get("accepts_caller_command_or_reference") is False, "contract.git.command")
    require(
        git.get("observation_fields")
        == [
            "revision_id",
            "generation",
            "snapshot_sha256",
            "commit_oid",
            "git_state_sha256",
        ],
        "contract.git.observation",
    )
    require(git.get("database_and_git_state_must_match") is True, "contract.git.binding")
    require(git.get("remote_network") is False, "contract.git.network")
    reconciliation = document["reconciliation"]
    require(reconciliation.get("same_head_same_snapshot") == "unchanged", "contract.reconcile.same")
    require(reconciliation.get("clean_strict_descendant") == "updated", "contract.reconcile.clean")
    require(reconciliation.get("ahead_strict_descendant") == "conflict", "contract.reconcile.ahead")
    require(reconciliation.get("local_conflict_payload_preserved") is True, "contract.reconcile.payload")
    require(reconciliation.get("rewritten_or_older_remote_head") == "rejected", "contract.reconcile.rewrite")
    require(
        reconciliation.get("git_database_drift")
        == "unavailable_without_database_mutation",
        "contract.reconcile.drift",
    )
    require(reconciliation.get("blind_retry") is False, "contract.reconcile.retry")
    rollback = document["rollback"]
    for claim in (
        "explicit_gate_required",
        "later_migrations_must_be_absent",
        "retained_observations_refuse_rollback",
        "empty_rollback_and_reapply_verified",
    ):
        require(rollback.get(claim) is True, f"contract.rollback.{claim}")
    require(rollback.get("exact_version_required") == 17, "contract.rollback.version")
    transport = document["transport"]
    require(transport.get("bind_address") == "127.0.0.1", "contract.transport.bind")
    require(transport.get("framed_and_bounded") is True, "contract.transport.frame")
    require(transport.get("arbitrary_host_configuration") is False, "contract.transport.host")
    require(transport.get("persistent_credential_custody") is False, "contract.transport.credential")
    evidence = document["evidence"]
    for claim in (
        "actual_postgresql_18_4",
        "actual_disposable_local_bare_git",
        "actual_authenticated_loopback",
        "actual_clean_advance",
        "actual_conflict_preservation",
        "actual_exact_replay",
        "actual_git_database_drift_rejection",
        "actual_owned_resource_cleanup",
    ):
        require(evidence.get(claim) is True, f"contract.evidence.{claim}")
    for claim in (
        "actual_remote_network",
        "persistent_credential_custody",
        "registered_host",
        "production",
        "actual_hangul",
        "p17_06_complete",
        "product_complete",
    ):
        require(evidence.get(claim) is False, f"contract.evidence.{claim}")


def validate_adapter(document: dict[str, Any]) -> None:
    require(
        document.get("schema_version") == "hwpx-agent.remote-sync-adapter/v4",
        "adapter.schema",
    )
    require(
        document.get("request_schema_versions")
        == {
            "pull": "hwpx-agent.remote-sync-request/v4",
            "push": "hwpx-agent.remote-sync-request/v3",
            "checkpoint": "hwpx-agent.remote-sync-request/v3",
        },
        "adapter.versions",
    )
    require(
        document.get("migration", {}).get("v3_pull_accepted_by_v4_host") is False
        and document.get("migration", {}).get("push_and_checkpoint_request_contracts_unchanged")
        is True,
        "adapter.migration",
    )
    require(
        document.get("pull", {}).get("required_fields")
        == ["observed_head", "observed_snapshot_sha256"]
        and document.get("pull", {}).get("head_and_snapshot_bound_in_request_sha256") is True,
        "adapter.pull",
    )
    for claim in (
        "persistent_credential_custody",
        "actual_remote_service",
        "production_authentication",
        "actual_hangul",
        "p17_06_pass",
        "product_complete",
    ):
        require(document.get("not_claimed", {}).get(claim) is False, f"adapter.nonclaim.{claim}")


def validate_receipt(receipt: dict[str, Any], root: Path = ROOT) -> None:
    require(
        list(receipt)
        == [
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
        ],
        "receipt.keys",
    )
    require(
        receipt.get("schema_version") == "hwpx-agent.p17-durable-git-mirror-pull-run/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("state") == "pass"
        and receipt.get("scope")
        == "current_pc_postgresql_local_bare_git_authenticated_loopback_only",
        "receipt.identity",
    )
    require(
        receipt.get("checks") == list(CHECKS)
        and receipt.get("check_count") == len(CHECKS),
        "receipt.checks",
    )
    require(
        receipt.get("postgres")
        == {
            "version": "18.4 (Debian 18.4-1.pgdg12+1)",
            "image": IMAGE,
            "image_id": IMAGE_ID,
            "loopback_only": True,
        },
        "receipt.postgres",
    )
    require(
        receipt.get("git")
        == {"object_format": "sha1", "bare": True, "remote_network": False},
        "receipt.git",
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
    effect = receipt.get("effect")
    require(
        isinstance(effect, dict)
        and set(effect)
        == {
            "first_revision_id",
            "second_revision_id",
            "remote_generation",
            "remote_git_oid",
            "observation_count",
            "conflict_count",
            "bounded_state_sha256",
            "updated_response_replayed",
            "conflict_response_replayed",
            "local_conflict_state_preserved",
        },
        "receipt.effect.keys",
    )
    require(
        REVISION.fullmatch(effect.get("first_revision_id", "")) is not None
        and REVISION.fullmatch(effect.get("second_revision_id", "")) is not None
        and effect.get("first_revision_id") != effect.get("second_revision_id")
        and effect.get("remote_generation") == 2
        and OID40.fullmatch(effect.get("remote_git_oid", "")) is not None
        and effect.get("observation_count") == 3
        and effect.get("conflict_count") == 1
        and HEX64.fullmatch(effect.get("bounded_state_sha256", "")) is not None
        and effect.get("updated_response_replayed") is True
        and effect.get("conflict_response_replayed") is True
        and effect.get("local_conflict_state_preserved") is True,
        "receipt.effect",
    )
    sources = receipt.get("source_sha256")
    require(isinstance(sources, dict) and set(sources) == set(RECEIPT_SOURCES), "receipt.sources.keys")
    for relative in RECEIPT_SOURCES:
        require(
            sources.get(relative) == digest_file(root / relative),
            "receipt.sources.digest",
        )
    require(receipt.get("resources_cleaned") is True, "receipt.cleanup")


def validate_sources(root: Path = ROOT) -> None:
    paths = (
        CONTRACT,
        ADAPTER_CONTRACT,
        ADAPTER_MIGRATION,
        POLICY,
        REPORT,
        MIGRATION_UP,
        MIGRATION_DOWN,
        LOCAL_SYNC,
        ADAPTER,
        SOURCE,
        HOST,
        CLIENT,
        HARNESS,
        SEED,
    )
    for path in paths:
        current = root / path.relative_to(ROOT)
        require(current.is_file() and 0 < current.stat().st_size <= 262_144, "source.path")
    up = (root / MIGRATION_UP.relative_to(ROOT)).read_text(encoding="utf-8")
    down = (root / MIGRATION_DOWN.relative_to(ROOT)).read_text(encoding="utf-8")
    source = (root / SOURCE.relative_to(ROOT)).read_text(encoding="utf-8")
    adapter = (root / ADAPTER.relative_to(ROOT)).read_text(encoding="utf-8")
    local_sync = (root / LOCAL_SYNC.relative_to(ROOT)).read_text(encoding="utf-8")
    harness = (root / HARNESS.relative_to(ROOT)).read_text(encoding="utf-8")
    report = (root / REPORT.relative_to(ROOT)).read_text(encoding="utf-8")
    adapter_migration = (root / ADAPTER_MIGRATION.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in (
        "ADD COLUMN observed_snapshot_sha256 character(64)",
        "CREATE TABLE hwpx_agent.git_mirror_pull_observations",
        "CREATE FUNCTION hwpx_agent.reconcile_git_mirror_pull_v1(",
        "WITH RECURSIVE chain",
        "JOIN hwpx_agent.artifact_acl AS acl",
        "GIT_MIRROR_PULL_OBSERVED_STATE_DRIFT",
        "GIT_MIRROR_PULL_REMOTE_STATE_DRIFT",
        "INSERT INTO hwpx_agent.local_mirror_conflicts",
        "ALTER TABLE hwpx_agent.git_mirror_pull_observations FORCE ROW LEVEL SECURITY",
        "REVOKE ALL ON TABLE hwpx_agent.git_mirror_pull_observations FROM PUBLIC",
        "VALUES (17, 'p17.durable_git_mirror_pull_v1'",
    ):
        require(token in up, "source.migration_up")
    for token in (
        "allow_p17_durable_git_mirror_pull_rollback",
        "rollback refuses retained observations",
        "DROP TABLE hwpx_agent.git_mirror_pull_observations",
        "DROP COLUMN observed_snapshot_sha256",
    ):
        require(token in down, "source.migration_down")
    for token in (
        "hwpx-agent.remote-sync-request/v4",
        "observed_snapshot_sha256",
        "GitPullDispatchRequest",
        "GitMirrorEffectHost::open",
        ".read_branch(",
        "IsolationLevel::Serializable",
        "verify_function_security",
        "aclexplode(COALESCE(proc.proacl,acldefault('f',proc.proowner)))",
        "GitPullDispatchError::Unavailable",
    ):
        require(token in source, "source.coordinator")
    require("observed_snapshot_sha256" in adapter, "source.adapter.snapshot")
    require("REMOTE_SYNC_PULL_REQUEST_SCHEMA_VERSION" in adapter, "source.adapter.version")
    require("hwpx-agent.remote-sync-request/v4" in local_sync, "source.local_sync.version")
    for token in CHECKS:
        require(token in harness, "source.harness.check")
    require(
        harness.index('require(cleaned, "owned_resource_cleanup_failed")')
        < harness.index('receipt["resources_cleaned"] = True')
        < harness.index("receipt_path.write_text"),
        "source.harness.cleanup_order",
    )
    require('"HWPX_P17_LEASE_SECONDS"] = "30"' in harness, "source.harness.seed_lease")
    require('"tools/p17/run_durable_git_mirror_pull_checks.py"' in harness, "source.harness.self_lock")
    require('"password":' not in harness and '"authorization":' not in harness, "source.harness.secret")
    require("only the `pull` operation" in adapter_migration, "source.adapter_migration")
    require("component PASS; P17-06 remains open" in report, "source.report.scope")
    require(
        "does not exercise a remote Git network or service" in report,
        "source.report.remote_nonclaim",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    document = load_unique(root / CONTRACT.relative_to(ROOT))
    validate(document)
    validate_adapter(load_unique(root / ADAPTER_CONTRACT.relative_to(ROOT)))
    validate_sources(root)
    receipt_path = root / RECEIPT.relative_to(ROOT)
    require(digest_file(receipt_path) == RECEIPT_SHA256, "receipt.digest")
    raw = receipt_path.read_bytes()
    require(
        b"Bearer " not in raw
        and b"POSTGRES_PASSWORD" not in raw
        and b"HWPX_P17_AUTHORIZATION" not in raw,
        "receipt.secret",
    )
    validate_receipt(load_unique(receipt_path), root)
    return document


if __name__ == "__main__":
    verified = verify()
    print(
        "P17_DURABLE_GIT_MIRROR_PULL_CONTRACT_PASS "
        f"schema={verified['schema_version']} checks={len(CHECKS)} receipt={RUN_ID}"
    )
