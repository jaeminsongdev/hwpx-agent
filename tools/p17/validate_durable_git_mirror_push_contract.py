"""Validate the bounded P17 authenticated durable Git mirror push contract."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "protocol/private/p17-durable-git-mirror-push-v1.json"
MIGRATION_UP = ROOT / "migrations/postgres/0016_p17_durable_git_mirror_push.up.sql"
MIGRATION_DOWN = ROOT / "migrations/postgres/0016_p17_durable_git_mirror_push.down.sql"
ORIGINAL_GUARD = ROOT / "migrations/postgres/0007_p14_idempotency_reconciliation.up.sql"
SOURCE = ROOT / "crates/remote-sync-host/src/durable_git_push.rs"
HOST = ROOT / "crates/remote-sync-host/examples/postgres_durable_git_push_host.rs"
CLIENT = ROOT / "crates/remote-sync-host/examples/postgres_durable_git_push_client.rs"
HARNESS = ROOT / "tools/p17/run_durable_git_mirror_push_checks.py"
FIXTURE = ROOT / "tools/p17/fixtures/p17_durable_git_mirror_push_setup.sql"
POLICY = ROOT / "protocol/migrations/p17-durable-git-mirror-push-v1.md"
REPORT = ROOT / "implementation/p17/P17-06_DURABLE_GIT_MIRROR_PUSH_V14.md"


class ContractError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def load_unique(path: Path) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ContractError("contract.duplicate_key")
            result[key] = value
        return result

    require(path.is_file() and 0 < path.stat().st_size <= 32_768, "contract.file")
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("contract.parse") from error
    require(isinstance(document, dict), "contract.type")
    return document


def validate(document: dict[str, Any]) -> None:
    require(
        list(document)
        == [
            "schema_version",
            "scope",
            "request",
            "database",
            "git",
            "recovery",
            "transport",
            "evidence",
        ],
        "contract.keys",
    )
    require(
        document["schema_version"] == "hwpx-agent.durable-git-mirror-push/v1",
        "schema",
    )
    request = document["request"]
    require(request["operation"] == "push", "request.operation")
    require(request["canonical_json_required"] is True, "request.canonical")
    require(request["max_bytes"] == 16_384, "request.bound")
    require(request["authentication_scope"] == "mirror.sync", "request.scope")
    require(request["single_use_credential"] is True, "request.credential")
    database = document["database"]
    require(database["exact_schema_version"] == 16, "database.version")
    require(
        database["states"] == ["executing", "finalized", "diverged"],
        "database.states",
    )
    require(database["canonical_plan_max_bytes"] == 4096, "database.plan_bound")
    for claim in (
        "plan_persisted_before_git_effect",
        "monotonic_fencing_token",
        "bounded_execution_lease",
        "branch_head_reserved_while_executing",
        "source_and_result_artifacts_verified",
        "revision_mirror_effect_finalized_atomically",
        "tenant_rls_forced",
        "security_definer_search_path_fixed",
        "public_execute_revoked",
    ):
        require(database[claim] is True, f"database.{claim}")
    require(database["application_role_has_table_mutation"] is False, "database.role")
    git = document["git"]
    require(git["reference_is_derived"] is True, "git.reference")
    require(git["accepts_caller_command_or_reference"] is False, "git.command")
    require(git["old_oid_compare_and_swap"] is True, "git.cas")
    require(
        git["observations"] == ["no_effect", "committed", "diverged"],
        "git.observations",
    )
    require(git["competing_reference_never_overwritten"] is True, "git.divergence")
    require(git["network_transport"] is False, "git.network")
    recovery = document["recovery"]
    for claim in (
        "fresh_execution_id_after_restart",
        "expired_lease_reacquired_with_higher_fence",
        "committed_git_finalizes_database_exactly_once",
        "exact_replay_creates_no_revision_or_git_commit",
        "divergence_enters_manual_merge_required",
        "uncertain_post_git_database_failure_is_unavailable",
    ):
        require(recovery[claim] is True, f"recovery.{claim}")
    require(recovery["blind_retry"] is False, "recovery.retry")
    transport = document["transport"]
    require(transport["bind_address"] == "127.0.0.1", "transport.loopback")
    require(transport["framed_and_bounded"] is True, "transport.frame")
    require(transport["arbitrary_host_configuration"] is False, "transport.host")
    require(transport["persistent_credential_custody"] is False, "transport.credential")
    evidence = document["evidence"]
    for claim in (
        "actual_postgresql_18_4",
        "actual_disposable_local_bare_git",
        "actual_authenticated_loopback",
        "actual_committed_effect_recovery",
        "actual_divergence_preservation",
    ):
        require(evidence[claim] is True, f"evidence.{claim}")
    for claim in (
        "actual_remote_network",
        "durable_pull",
        "production",
        "actual_hangul",
        "p17_06_complete",
    ):
        require(evidence[claim] is False, f"evidence.{claim}")


def validate_sources(root: Path = ROOT) -> None:
    paths = (
        MIGRATION_UP,
        MIGRATION_DOWN,
        ORIGINAL_GUARD,
        SOURCE,
        HOST,
        CLIENT,
        HARNESS,
        FIXTURE,
        POLICY,
        REPORT,
    )
    for path in paths:
        current = root / path.relative_to(ROOT)
        require(current.is_file() and 0 < current.stat().st_size <= 131_072, "source.file")
    up = (root / MIGRATION_UP.relative_to(ROOT)).read_text(encoding="utf-8")
    down = (root / MIGRATION_DOWN.relative_to(ROOT)).read_text(encoding="utf-8")
    original_guard = (root / ORIGINAL_GUARD.relative_to(ROOT)).read_text(encoding="utf-8")
    source = (root / SOURCE.relative_to(ROOT)).read_text(encoding="utf-8")
    host = (root / HOST.relative_to(ROOT)).read_text(encoding="utf-8")
    client = (root / CLIENT.relative_to(ROOT)).read_text(encoding="utf-8")
    harness = (root / HARNESS.relative_to(ROOT)).read_text(encoding="utf-8")
    report = (root / REPORT.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in (
        "CREATE TABLE hwpx_agent.git_mirror_push_effects",
        "git_mirror_push_effect_guard",
        "branches_git_mirror_push_guard",
        "ROW(v_push.result_revision_id, v_push.result_generation)",
        "guard_idempotent_revision_commit_v2",
        "store_git_mirror_push_plan_v1",
        "acquire_git_mirror_push_lease_v1",
        "mark_git_mirror_push_diverged_v1",
        "finalize_git_mirror_push_v1",
        "role IN ('editor', 'owner')",
        "FROM hwpx_agent.artifact_acl AS acl",
        "artifact.artifact_kind = 'result'",
        "artifact.storage_state = 'available' AND artifact.validation_state = 'verified'",
        "lease_fencing_token = effect.lease_fencing_token + 1",
        "FROM hwpx_agent.commit_revision_cas(",
        "REVOKE ALL ON TABLE hwpx_agent.git_mirror_push_effects FROM PUBLIC",
        "VALUES (16, 'p17.durable_git_mirror_push_v1'",
    ):
        require(token in up, f"migration.up.{token}")
    require(up.index("INSERT INTO hwpx_agent.git_mirror_push_effects") < up.index("COMMIT;"), "migration.plan")
    for token in (
        "allow_p17_durable_git_mirror_push_rollback",
        "rollback refuses retained effects",
        "CREATE OR REPLACE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2()",
        "DROP TABLE hwpx_agent.git_mirror_push_effects",
    ):
        require(token in down, f"migration.down.{token}")
    guard_pattern = re.compile(
        r"CREATE(?: OR REPLACE)? FUNCTION "
        r"hwpx_agent\.guard_idempotent_revision_commit_v2\(\)\s*.*?\n\$\$;",
        re.DOTALL,
    )
    original_match = guard_pattern.search(original_guard)
    restored_match = guard_pattern.search(down)
    require(original_match is not None and restored_match is not None, "migration.guard_block")
    original_block = original_match.group(0).replace(
        "CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1
    )
    require(original_block == restored_match.group(0), "migration.guard_restore")
    for token in (
        "LocalPostgresGitMirrorPushCoordinator",
        "GitMirrorEffectObservation::NoEffect",
        "GitMirrorEffectObservation::Committed",
        "GitMirrorEffectObservation::Diverged",
        "GitMirrorPushPlan::decode",
        "Uuid::new_v4()",
        "IsolationLevel::Serializable",
        "verify_function_security",
        "aclexplode(COALESCE(proc.proacl,acldefault('f',proc.proowner)))",
        "bool_and(proc.prosecdef)",
        "bool_and(COALESCE(proc.proconfig=",
        "GitPushDispatchError::Unavailable",
        "Any database",
    ):
        require(token in source, f"source.token.{token}")
    require(".map_err(|_| GitPushDispatchError::Unavailable)?" in source, "source.uncertain")
    require("LoopbackGitPushServer::bind" in host, "host.loopback")
    require("SingleUseCredentialProvider::new" in client, "client.single_use")
    for token in (
        "git_committed_database_finalize_interrupted_is_unavailable",
        "verified_artifact_acl_required_before_plan_or_git_effect",
        "exact_fence_cannot_authorize_wrong_branch_head",
        "divergence_database_transition_interruption_is_unavailable",
        "committed_git_observed_and_database_finalized_once",
        "competing_ref_never_overwritten",
        "rollback_refuses_retained_effects",
        "migration_digest_drift_rejected",
        "public_execute_drift_rejected",
        "fixed_search_path_drift_rejected",
        "security_definer_drift_rejected",
        '"secrets_persisted": False',
        '"actual_remote_network": False',
        '"coordinator": digest(coordinator_source)',
        '"git_effect_host": digest(git_source)',
        'docker, "rm", "--force", container',
    ):
        require(token in harness, f"harness.token.{token}")
    require('"password":' not in harness, "harness.password")
    require('"authorization":' not in harness, "harness.authorization")
    require("component evidence" in report, "report.scope")
    require("P17-06 therefore remains open" in report, "report.open")
    require("Durable pull" in report, "report.pull")


def verify(root: Path = ROOT) -> dict[str, Any]:
    document = load_unique(root / CONTRACT.relative_to(ROOT))
    validate(document)
    validate_sources(root)
    return document


if __name__ == "__main__":
    verified = verify()
    print(
        "P17_DURABLE_GIT_MIRROR_PUSH_CONTRACT_PASS "
        f"schema={verified['schema_version']}"
    )
