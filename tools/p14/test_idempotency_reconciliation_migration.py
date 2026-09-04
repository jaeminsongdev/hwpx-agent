from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import threading
import uuid
from datetime import UTC, datetime
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
SUPPORT_PATH = Path(__file__).with_name("test_artifact_service_migration.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location("p14_postgres_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("P14 PostgreSQL support module could not be loaded")
SUPPORT = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT)
LABEL_KEY = "hwpx-agent.p14-idempotency-test"


class HarnessError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise HarnessError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        fail("idempotency contract root is not an object")
    return document


def validate_contract(path: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name(
        "validate_idempotency_reconciliation_migration.py"
    )
    specification = importlib.util.spec_from_file_location(
        "p14_validate_idempotency_reconciliation", module_path
    )
    if specification is None or specification.loader is None:
        fail("idempotency migration validator could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    validated = module.validate_contract(path.resolve(), ROOT)
    if not isinstance(validated, dict) or validated.get("state") != "pass":
        fail("idempotency migration contract did not validate")
    return validated


def inspect_owned_container(docker: str, container: str, run_id: str) -> bool:
    result = SUPPORT.run(docker, ["inspect", container], check=False)
    if result.returncode != 0:
        return False
    document = json.loads(result.stdout)
    if not isinstance(document, list) or len(document) != 1:
        fail("Docker returned an ambiguous container inspection result")
    labels = document[0].get("Config", {}).get("Labels", {})
    if not isinstance(labels, dict) or labels.get(LABEL_KEY) != run_id:
        fail("refusing to remove a container without the exact owned-run label")
    return True


def assert_version_state(docker: str, container: str, expected: str) -> None:
    versions = SUPPORT.scalar(
        docker,
        container,
        "SELECT string_agg(version::text, ',' ORDER BY version) "
        "FROM hwpx_agent.schema_versions;\n",
    )
    if versions != expected:
        fail(f"schema version set differs: expected {expected}, got {versions}")


def assert_version_7_removed_and_v6_restored(docker: str, container: str) -> None:
    objects = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM information_schema.columns
     WHERE table_schema='hwpx_agent' AND table_name='idempotency_records'
       AND column_name='record_version'), ',',
    (SELECT count(*) FROM pg_indexes
     WHERE schemaname='hwpx_agent'
       AND indexname IN (
           'idempotency_v2_retry_ready_idx','idempotency_v2_job_unique_idx',
           'idempotency_v2_transaction_unique_idx','jobs_idempotency_v2_ready_idx'
        )), ',',
    (SELECT count(*) FROM information_schema.tables
     WHERE table_schema='hwpx_agent'
       AND table_name='idempotency_commit_authorizations'), ',',
    (SELECT count(*) FROM pg_trigger AS trigger
     JOIN pg_class AS relation ON relation.oid=trigger.tgrelid
     JOIN pg_namespace AS namespace ON namespace.oid=relation.relnamespace
     WHERE namespace.nspname='hwpx_agent'
       AND trigger.tgname='revision_commit_receipts_idempotency_v2_guard'
       AND NOT trigger.tgisinternal), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname IN (
           'verify_idempotency_job_consistency','require_idempotency_v2_editor',
           'idempotency_v2_artifact_qualified','idempotency_v2_head_matches',
           'idempotency_v2_committed_effect_qualified','idempotency_v2_retry_at',
           'claim_idempotent_job_v2','lease_idempotent_job_v2',
           'advance_idempotent_job_v2','heartbeat_idempotent_job_v2',
           'schedule_idempotent_retry_v2','mark_idempotent_outcome_unknown_v2',
           'complete_idempotent_job_success_v2','fail_idempotent_job_terminal_v2',
            'reconcile_idempotent_job_v2','get_idempotent_job_v2'
            ,'guard_idempotent_revision_commit_v2','commit_idempotent_revision_cas_v2'
        )), ',',
    (SELECT count(*) FROM pg_proc AS routine
     JOIN pg_namespace AS namespace ON namespace.oid=routine.pronamespace
     WHERE namespace.nspname='hwpx_agent'
       AND routine.proname='guard_job_state_machine_update'
       AND routine.prosecdef
       AND position('JOB_WORKER_NOT_QUALIFIED' in routine.prosrc) > 0
       AND position('IDEMPOTENCY_V2_TRANSITION_REQUIRED' in routine.prosrc) = 0)
);
""",
    )
    if objects != "0,0,0,0,0,1":
        fail(f"version 7 rollback left objects or failed to restore v6: {objects}")


def insert_fake_later_version(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        """
BEGIN;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (8, 'p14.test_later_version', repeat('f', 64));
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
""",
    )


def remove_fake_later_version(docker: str, container: str) -> None:
    SUPPORT.psql(
        docker,
        container,
        """
BEGIN;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 8;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
""",
    )


def persistent_smoke(smoke_sql: str) -> str:
    stripped = smoke_sql.rstrip()
    if not stripped.endswith("ROLLBACK;"):
        fail("smoke fixture does not end in an exact rollback")
    return stripped[: -len("ROLLBACK;")] + "COMMIT;\n"


def run_concurrent_claims(docker: str, container: str) -> tuple[int, int]:
    claim_sql = """
SET hwpx_agent.tenant_id = 'd1000000-0000-0000-0000-000000000001';
SET hwpx_agent.subject_sha256 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
SELECT returned_outcome FROM hwpx_agent.claim_idempotent_job_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd8100000-0000-0000-0000-000000000004',
    'd4000000-0000-0000-0000-000000000006',
    'db000000-0000-0000-0000-000000000002', 2,
    repeat('1', 64), repeat('2', 64), lpad(to_hex(1006), 64, '0'),
    lpad(to_hex(1007), 64, '0'), lpad(to_hex(1010), 64, '0'), repeat('5', 64),
    'hancom-hangul-2020-current-pc', repeat('c', 64),
    3, 1, 4, 600, repeat('6', 64)
);
"""

    def claim_once(_: int) -> str:
        result = SUPPORT.psql(docker, container, claim_sql, timeout=60)
        outcomes = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if outcomes not in (["new"], ["replay"]):
            fail(f"concurrent claim returned an unexpected result: {outcomes}")
        return outcomes[0]

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(executor.map(claim_once, range(16)))
    new_count = outcomes.count("new")
    replay_count = outcomes.count("replay")
    if new_count != 1 or replay_count != 15:
        fail(f"concurrent claim split differs: new={new_count}, replay={replay_count}")
    row_count = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM hwpx_agent.idempotency_records
     WHERE tenant_id='d1000000-0000-0000-0000-000000000001'
       AND project_id='d2000000-0000-0000-0000-000000000001'
       AND idempotency_key='d7000000-0000-0000-0000-000000000004'), ',',
    (SELECT count(*) FROM hwpx_agent.jobs
     WHERE tenant_id='d1000000-0000-0000-0000-000000000001'
       AND project_id='d2000000-0000-0000-0000-000000000001'
       AND job_id='d8000000-0000-0000-0000-000000000004')
);
""",
    )
    if row_count != "1,1":
        fail(f"concurrent claim did not leave exactly one record/job: {row_count}")
    return new_count, replay_count


def run_commit_retry_race(docker: str, container: str) -> str:
    setup_sql = """
SET hwpx_agent.tenant_id = 'd1000000-0000-0000-0000-000000000001';
SET hwpx_agent.subject_sha256 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
SELECT * FROM hwpx_agent.lease_idempotent_job_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 60, repeat('7', 64)
);
SELECT * FROM hwpx_agent.advance_idempotent_job_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    'leased', 'staged', repeat('8', 64)
);
SELECT * FROM hwpx_agent.advance_idempotent_job_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    'staged', 'executing', repeat('8', 64)
);
SELECT * FROM hwpx_agent.advance_idempotent_job_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    'executing', 'validating', repeat('8', 64)
);
    """
    SUPPORT.psql(docker, container, setup_sql, timeout=60)
    commit_authorization_id = SUPPORT.scalar(
        docker,
        container,
        """
SELECT commit_authorization_id
FROM hwpx_agent.idempotency_commit_authorizations
WHERE tenant_id='d1000000-0000-0000-0000-000000000001'
  AND project_id='d2000000-0000-0000-0000-000000000001'
  AND idempotency_key='d7000000-0000-0000-0000-000000000004';
""",
    )
    if re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", commit_authorization_id) is None:
        fail("lease did not issue one canonical commit authorization id")

    prefix = """
SET hwpx_agent.tenant_id = 'd1000000-0000-0000-0000-000000000001';
SET hwpx_agent.subject_sha256 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
SET lock_timeout = '5s';
SET statement_timeout = '15s';
"""
    commit_sql = prefix + f"""
SELECT * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    '{commit_authorization_id}',
    'dc000000-0000-0000-0000-000000000004',
    'db000000-0000-0000-0000-000000000002', 2,
    'db000000-0000-0000-0000-000000000004',
    ARRAY['db000000-0000-0000-0000-000000000002'::uuid],
    'd4000000-0000-0000-0000-000000000006',
    'd4000000-0000-0000-0000-000000000007', NULL,
    repeat('5', 64), 'verified', repeat('7', 64),
    lpad(to_hex(1010), 64, '0'), repeat('8', 64), repeat('9', 64)
);
"""
    retry_sql = prefix + """
SELECT pg_sleep(0.2);
SELECT * FROM hwpx_agent.schedule_idempotent_retry_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    'transient_network', 'd4000000-0000-0000-0000-000000000009', repeat('d', 64)
);
"""
    barrier = threading.Barrier(2)

    def run_racer(sql: str):
        barrier.wait(timeout=10)
        return SUPPORT.psql(docker, container, sql, check=False, timeout=30)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        commit_future = executor.submit(run_racer, commit_sql)
        retry_future = executor.submit(run_racer, retry_sql)
        commit_result = commit_future.result(timeout=40)
        retry_result = retry_future.result(timeout=40)

    commit_won = commit_result.returncode == 0
    retry_won = retry_result.returncode == 0
    if commit_won == retry_won:
        fail(
            "commit/retry race did not have exactly one winner: "
            f"commit={commit_result.returncode}, retry={retry_result.returncode}"
        )
    if commit_won:
        if "IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED" not in retry_result.stderr:
            fail("commit-winning race did not fail the retry through the no-effect oracle")
        completion = SUPPORT.psql(
            docker,
            container,
            prefix
            + """
SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2(
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
    'd7000000-0000-0000-0000-000000000004',
    'd8000000-0000-0000-0000-000000000004',
    'd9000000-0000-0000-0000-000000000001',
    'da000000-0000-0000-0000-000000000031', 1, 1,
    'db000000-0000-0000-0000-000000000004',
    'd4000000-0000-0000-0000-000000000010', repeat('a', 64)
);
""",
            check=False,
            timeout=30,
        )
        if completion.returncode != 0:
            diagnostic = SUPPORT.psql(
                docker,
                container,
                prefix
                + """
SELECT json_build_object(
    'record', (SELECT row_to_json(record) FROM hwpx_agent.idempotency_records AS record
      WHERE record.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND record.project_id='d2000000-0000-0000-0000-000000000001'
        AND record.idempotency_key='d7000000-0000-0000-0000-000000000004'),
    'job', (SELECT row_to_json(job) FROM hwpx_agent.jobs AS job
      WHERE job.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND job.project_id='d2000000-0000-0000-0000-000000000001'
        AND job.job_id='d8000000-0000-0000-0000-000000000004'),
    'revision', (SELECT row_to_json(revision) FROM hwpx_agent.revisions AS revision
      WHERE revision.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND revision.project_id='d2000000-0000-0000-0000-000000000001'
        AND revision.revision_id='db000000-0000-0000-0000-000000000004'),
    'seal', (SELECT row_to_json(seal) FROM hwpx_agent.revision_graph_seals AS seal
      WHERE seal.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND seal.project_id='d2000000-0000-0000-0000-000000000001'
        AND seal.revision_id='db000000-0000-0000-0000-000000000004'),
    'commit', (SELECT row_to_json(receipt) FROM hwpx_agent.revision_commit_receipts AS receipt
      WHERE receipt.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND receipt.project_id='d2000000-0000-0000-0000-000000000001'
        AND receipt.committed_revision_id='db000000-0000-0000-0000-000000000004'),
    'head', (SELECT row_to_json(branch) FROM hwpx_agent.branches AS branch
      WHERE branch.tenant_id='d1000000-0000-0000-0000-000000000001'
        AND branch.project_id='d2000000-0000-0000-0000-000000000001'
        AND branch.branch_id='d3000000-0000-0000-0000-000000000001')
);
""",
                timeout=30,
            )
            fail(
                "commit-winning completion oracle failed: "
                f"{completion.stderr.strip()} diagnostic={diagnostic.stdout.strip()}"
            )
        expected = "db000000-0000-0000-0000-000000000004,3,terminal_success,0"
        winner = "commit"
    else:
        if "IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED" not in commit_result.stderr:
            fail("retry-winning race did not reject the superseded commit authorization")
        expected = "db000000-0000-0000-0000-000000000002,2,retry_pending,0"
        winner = "retry"

    observed = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    branch.head_revision_id, ',', branch.head_generation, ',', record.state, ',',
    (SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth
     WHERE commit_auth.tenant_id=record.tenant_id
       AND commit_auth.project_id=record.project_id
       AND commit_auth.idempotency_key=record.idempotency_key)
)
FROM hwpx_agent.branches AS branch
JOIN hwpx_agent.idempotency_records AS record
  ON record.tenant_id=branch.tenant_id AND record.project_id=branch.project_id
WHERE branch.tenant_id='d1000000-0000-0000-0000-000000000001'
  AND branch.project_id='d2000000-0000-0000-0000-000000000001'
  AND branch.branch_id='d3000000-0000-0000-0000-000000000001'
  AND record.idempotency_key='d7000000-0000-0000-0000-000000000004';
""",
    )
    if observed != expected:
        fail(f"commit/retry race durable state differs: expected {expected}, got {observed}")
    return winner


def remove_disposable_v2_data(docker: str, container: str) -> None:
    # This is explicit disposable-container cleanup, not migration behavior.
    SUPPORT.psql(
        docker,
        container,
        "TRUNCATE TABLE hwpx_agent.tenants CASCADE;\n",
        timeout=120,
    )
    counts = SUPPORT.scalar(
        docker,
        container,
        """
SELECT concat(
    (SELECT count(*) FROM hwpx_agent.idempotency_records WHERE record_version=2), ',',
    (SELECT count(*) FROM hwpx_agent.jobs WHERE state_machine_version=2), ',',
    (SELECT count(*) FROM hwpx_agent.job_attempts WHERE state_machine_version=2)
    ,',',(SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations)
);
""",
    )
    if counts != "0,0,0,0":
        fail(f"disposable v2 cleanup failed: {counts}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--allow-pull", action="store_true")
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docker = shutil.which("docker")
    if docker is None:
        fail("docker executable is unavailable")
    validated = validate_contract(args.contract)
    contract = load_contract(args.contract.resolve())
    image = str(validated["container_image"])
    prerequisites = contract["prerequisites"]
    migration = contract["migration"]
    smoke = contract["smoke_fixture"]
    if not isinstance(prerequisites, list) or len(prerequisites) != 6:
        fail("validated prerequisite shape differs")
    if not isinstance(migration, dict) or not isinstance(smoke, dict):
        fail("validated idempotency contract sections differ")

    prerequisite_sql: list[tuple[str, str, str]] = []
    for entry in prerequisites:
        if not isinstance(entry, dict):
            fail("validated prerequisite entry differs")
        prerequisite_sql.append(
            (
                SUPPORT.load_bounded_text(ROOT / str(entry["up_path"]), 512 * 1024),
                SUPPORT.load_bounded_text(ROOT / str(entry["down_path"]), 256 * 1024),
                str(entry["up_sha256"]),
            )
        )
    up7 = SUPPORT.load_bounded_text(ROOT / str(migration["up_path"]), 512 * 1024)
    down7 = SUPPORT.load_bounded_text(ROOT / str(migration["down_path"]), 256 * 1024)
    smoke_sql = SUPPORT.load_bounded_text(ROOT / str(smoke["path"]), 512 * 1024)
    expected_marker = str(smoke["pass_marker"])

    source_revision, source_tree_clean = SUPPORT.git_state()
    harness_digest = sha256(Path(__file__).resolve())
    validator_digest = sha256(
        Path(__file__).with_name("validate_idempotency_reconciliation_migration.py")
    )
    support_digest = sha256(SUPPORT_PATH)
    contract_digest = sha256(args.contract.resolve())
    inspected_image = SUPPORT.ensure_image(docker, image, args.allow_pull)

    run_id = str(uuid.uuid4())
    container = f"hwpx-agent-p14-idempotency-{run_id.replace('-', '')[:12]}"
    cleanup_verified = False
    primary_error: BaseException | None = None
    receipt: dict[str, object] = {}
    try:
        SUPPORT.run(
            docker,
            [
                "run",
                "--detach",
                "--name",
                container,
                "--label",
                f"{LABEL_KEY}={run_id}",
                "--network",
                "none",
                "--env",
                "POSTGRES_HOST_AUTH_METHOD=trust",
                image,
            ],
            timeout=120,
        )
        SUPPORT.wait_until_ready(docker, container)
        version = SUPPORT.scalar(docker, container, "SHOW server_version;\n")
        if not version.startswith("18.4"):
            fail(f"unexpected PostgreSQL server version: {version}")

        for up_sql, _, digest in prerequisite_sql:
            SUPPORT.apply_up(docker, container, up_sql, digest)
        assert_version_state(docker, container, "1,2,3,4,5,6")
        SUPPORT.apply_up(docker, container, up7, str(migration["up_sha256"]))
        assert_version_state(docker, container, "1,2,3,4,5,6,7")

        first_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=180)
        if expected_marker not in first_smoke.stdout:
            fail("first idempotency smoke did not emit its exact pass marker")

        replay_prefix = (
            "SELECT set_config('hwpx_agent.migration_sha256', "
            f"'{migration['up_sha256']}', false);\n"
        )
        replay = SUPPORT.psql(
            docker, container, replay_prefix + up7, check=False, timeout=120
        )
        if replay.returncode == 0 or "exact schema version 6" not in replay.stderr:
            fail("duplicate version 7 migration was not refused")
        assert_version_state(docker, container, "1,2,3,4,5,6,7")

        refused = SUPPORT.apply_down(docker, container, down7, explicitly_allowed=False)
        if refused.returncode == 0 or "requires explicit" not in refused.stderr:
            fail("version 7 rollback without the destructive gate was not refused")

        insert_fake_later_version(docker, container)
        later_refused = SUPPORT.psql(
            docker,
            container,
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', 'on', false);\n"
            + down7,
            check=False,
            timeout=120,
        )
        if later_refused.returncode == 0 or "later migrations removed first" not in (
            later_refused.stderr
        ):
            fail("version 7 rollback did not protect a later migration")
        remove_fake_later_version(docker, container)

        persisted = SUPPORT.psql(
            docker, container, persistent_smoke(smoke_sql), timeout=180
        )
        if expected_marker not in persisted.stdout:
            fail("persisted idempotency smoke did not emit its exact pass marker")
        new_count, replay_count = run_concurrent_claims(docker, container)
        commit_retry_race_winner = run_commit_retry_race(docker, container)

        data_refused = SUPPORT.psql(
            docker,
            container,
            "SELECT set_config('hwpx_agent.allow_destructive_rollback', 'on', false);\n"
            + down7,
            check=False,
            timeout=120,
        )
        if data_refused.returncode == 0 or "refuses remaining version 2 data" not in (
            data_refused.stderr
        ):
            fail("version 7 rollback did not protect version-2 data")
        remove_disposable_v2_data(docker, container)
        SUPPORT.apply_down(docker, container, down7, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4,5,6")
        assert_version_7_removed_and_v6_restored(docker, container)

        SUPPORT.apply_up(docker, container, up7, str(migration["up_sha256"]))
        second_smoke = SUPPORT.psql(docker, container, smoke_sql, timeout=180)
        if expected_marker not in second_smoke.stdout:
            fail("reapplied idempotency smoke did not emit its exact pass marker")
        SUPPORT.apply_down(docker, container, down7, explicitly_allowed=True)
        assert_version_state(docker, container, "1,2,3,4,5,6")
        assert_version_7_removed_and_v6_restored(docker, container)

        for _, down_sql, _ in reversed(prerequisite_sql):
            SUPPORT.apply_down(docker, container, down_sql, explicitly_allowed=True)
        schema_count = SUPPORT.scalar(
            docker,
            container,
            "SELECT count(*) FROM pg_namespace WHERE nspname='hwpx_agent';\n",
        )
        if schema_count != "0":
            fail("final rollback left the metadata schema present")

        receipt = {
            "schema_version": "hwpx-agent.p14-07-postgres-idempotency-audit/v1",
            "state": "pass",
            "recorded_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_tree_clean_before_run": source_tree_clean,
            "migration_contract_sha256": contract_digest,
            "validator_sha256": validator_digest,
            "test_harness_sha256": harness_digest,
            "postgres_support_sha256": support_digest,
            "image": image,
            "image_id": inspected_image.get("Id"),
            "postgres_server_version": version,
            "prerequisite_up_sha256": [value[2] for value in prerequisite_sql],
            "up_migration_sha256": migration["up_sha256"],
            "down_migration_sha256": migration["down_sha256"],
            "smoke_fixture_sha256": smoke["sha256"],
            "assertion_count_per_run": smoke["assertion_count"],
            "migration_apply_count": 2,
            "smoke_transaction_count": 3,
            "concurrent_claimers": 16,
            "concurrent_new_claims": new_count,
            "concurrent_replays": replay_count,
            "trusted_committed_oracle_exercised": True,
            "trusted_no_effect_oracle_exercised": True,
            "branch_head_lock_exercised": True,
            "multi_attempt_fencing_exercised": True,
            "commit_authorization_exercised": True,
            "attempt_scoped_commit_capability_exercised": True,
            "direct_unbound_commit_rejected": True,
            "late_commit_after_retry_rejected": True,
            "concurrent_commit_retry_race_winner": commit_retry_race_winner,
            "concurrent_commit_retry_exactly_one_winner": True,
            "unknown_outcome_freeze_exercised": True,
            "legacy_row_preservation_exercised": True,
            "rollback_without_gate_refused": True,
            "rollback_with_later_version_refused": True,
            "rollback_with_v2_data_refused": True,
            "version_6_preserved_after_version_7_rollback": True,
            "explicit_rollback_pass": True,
            "reapply_pass": True,
            "container_network_mode": "none",
            "host_port_published": False,
            "host_volume_mounted": False,
            "secrets_persisted": False,
            "container_removed": False,
        }
    except BaseException as error:
        primary_error = error
    finally:
        cleanup_error: BaseException | None = None
        try:
            if inspect_owned_container(docker, container, run_id):
                SUPPORT.run(docker, ["rm", "--force", container], timeout=60)
            cleanup_verified = not inspect_owned_container(docker, container, run_id)
        except BaseException as error:
            cleanup_error = error
        if cleanup_error is not None:
            if primary_error is not None:
                raise HarnessError(
                    f"{primary_error}; container cleanup also failed: {cleanup_error}"
                ) from primary_error
            raise cleanup_error

    if primary_error is not None:
        raise primary_error
    if not cleanup_verified:
        fail("owned idempotency test container removal was not verified")
    receipt["container_removed"] = True
    if args.receipt is not None:
        SUPPORT.write_new_json(args.receipt.resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print(
        "P14_IDEMPOTENCY_RECONCILIATION_POSTGRES_PASS "
        "apply_v7=2 smoke=3 concurrent_claimers=16 effect_race=1 rollback_v7=2"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HarnessError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"P14_IDEMPOTENCY_RECONCILIATION_POSTGRES_FAILED: {error}", file=sys.stderr)
        raise SystemExit(2) from error
