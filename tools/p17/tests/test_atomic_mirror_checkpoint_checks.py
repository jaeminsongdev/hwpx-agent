from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]


class AtomicMirrorCheckpointChecksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up = (
            ROOT / "migrations/postgres/0015_p17_atomic_mirror_checkpoint.up.sql"
        ).read_text(encoding="utf-8")
        cls.down = (
            ROOT / "migrations/postgres/0015_p17_atomic_mirror_checkpoint.down.sql"
        ).read_text(encoding="utf-8")
        cls.adapter = (ROOT / "crates/remote-sync-host/src/postgres.rs").read_text(
            encoding="utf-8"
        )
        cls.host = (
            ROOT
            / "crates/remote-sync-host/examples/postgres_atomic_mirror_checkpoint_host.rs"
        ).read_text(encoding="utf-8")
        cls.harness = (
            ROOT / "tools/p17/run_atomic_mirror_checkpoint_checks.py"
        ).read_text(encoding="utf-8")

    def test_migration_locks_durable_admission_before_checkpoint(self) -> None:
        required = (
            "version = 14 AND migration_name = 'p17.history_checkpoint_note_v2'",
            "version >= 15",
            "CREATE FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(",
            "SECURITY DEFINER",
            "role IN ('editor', 'owner')",
            "FROM hwpx_agent.project_local_mirrors AS mirror",
            "v_mirror.state <> 'clean'",
            "v_mirror.pending_plan_sha256 IS NOT NULL",
            "v_mirror.active_push_id IS NOT NULL",
            "FROM hwpx_agent.branches AS branch",
            "FOR SHARE",
            "ERRCODE = 'P1702'",
            "FROM hwpx_agent.create_history_checkpoint_v2(",
            "REVOKE ALL ON FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(",
            "VALUES (15, 'p17.atomic_mirror_checkpoint_v3'",
        )
        for snippet in required:
            self.assertIn(snippet, self.up)
        self.assertLess(
            self.up.index("FROM hwpx_agent.project_acl"),
            self.up.index("FROM hwpx_agent.project_local_mirrors AS mirror"),
        )
        self.assertLess(
            self.up.index("FROM hwpx_agent.project_local_mirrors AS mirror"),
            self.up.index("FROM hwpx_agent.branches AS branch"),
        )
        self.assertLess(
            self.up.index("FROM hwpx_agent.branches AS branch"),
            self.up.index("FROM hwpx_agent.create_history_checkpoint_v2("),
        )
        self.assertNotIn("GRANT EXECUTE", self.up)

    def test_rollback_is_exact_and_explicit(self) -> None:
        for snippet in (
            "allow_p17_atomic_mirror_checkpoint_rollback",
            "version = 15 AND migration_name = 'p17.atomic_mirror_checkpoint_v3'",
            "version > 15",
            "DROP FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(",
            "DISABLE TRIGGER schema_versions_immutable",
            "ENABLE TRIGGER schema_versions_immutable",
        ):
            self.assertIn(snippet, self.down)
        self.assertNotIn("DROP TABLE", self.down)
        self.assertNotIn("DROP COLUMN", self.down)

    def test_current_dispatcher_is_exact_least_privilege_and_no_retry(self) -> None:
        for snippet in (
            "const ATOMIC_MIGRATIONS: [&[u8]; 15]",
            "const CURRENT_ATOMIC_MIGRATIONS: [&[u8]; 17]",
            'migration!("0015_p17_atomic_mirror_checkpoint.up.sql")',
            'migration!("0016_p17_durable_git_mirror_push.up.sql")',
            'migration!("0017_p17_durable_git_mirror_pull.up.sql")',
            "LocalPostgresAtomicMirrorCheckpointDispatcher",
            "IsolationLevel::Serializable",
            "create_mirror_history_checkpoint_v3",
            "ORDER BY version LIMIT 17",
            "verify_atomic_policies",
            "verify_atomic_privileges",
            "P1702",
            "CheckpointDispatchError::Unavailable",
        ):
            self.assertIn(snippet, self.adapter)
        dispatch = self.adapter.split(
            "impl CheckpointDispatcher for LocalPostgresAtomicMirrorCheckpointDispatcher",
            1,
        )[1].split("fn verify_database", 1)[0]
        self.assertEqual(
            dispatch.count("FROM hwpx_agent.create_mirror_history_checkpoint_v3("), 1
        )
        self.assertNotIn("retry", dispatch.lower())

    def test_all_current_consumers_fail_closed_after_version_17(self) -> None:
        paths = (
            "crates/artifact-service/src/store/postgres_repository.rs",
            "crates/mcp-control-plane/src/postgres_plan_source.rs",
            "crates/mcp-control-plane/src/postgres_stored_plan.rs",
            "crates/mcp-control-plane/src/postgres_plan_review.rs",
        )
        for relative in paths:
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("const MIGRATIONS: [&[u8]; 17]", source, relative)
            self.assertIn(
                'migration!("0015_p17_atomic_mirror_checkpoint.up.sql")',
                source,
                relative,
            )
            self.assertIn(
                'migration!("0016_p17_durable_git_mirror_push.up.sql")',
                source,
                relative,
            )
            self.assertIn(
                'migration!("0017_p17_durable_git_mirror_pull.up.sql")',
                source,
                relative,
            )
            self.assertIn("LIMIT 17", source, relative)

    def test_probe_fixture_and_harness_are_bounded(self) -> None:
        self.assertIn(
            'const REQUIRED_MODE: &str = "isolated-current-pc-atomic-mirror";',
            self.host,
        )
        self.assertIn(
            "LocalPostgresAtomicMirrorCheckpointDispatcher::connect", self.host
        )
        self.assertNotIn("std::process::Command", self.host)
        fixture = (
            ROOT / "tools/p17/fixtures/p17_atomic_mirror_checkpoint_setup.sql"
        ).read_text(encoding="utf-8")
        self.assertEqual(fixture.count("__P17_SERVICE_SUBJECT_SHA256__"), 4)
        self.assertIn("INSERT INTO hwpx_agent.project_local_mirrors", fixture)
        self.assertIn(
            "observed_revision_id, observed_generation, snapshot_sha256", fixture
        )
        for snippet in (
            'LABEL = "hwpx-agent.p17-atomic-mirror-checkpoint-test"',
            '"--pull",',
            '"never",',
            '"--publish",',
            '"127.0.0.1::5432",',
            "client_process_count",
            "durable_role_drift_rejected",
            "durable_head_drift_rejected",
            "durable_mirror_state_drift_rejected",
            "mirror_policy_drift_rejected",
            '"secrets_persisted": False',
            '"actual_hangul": False',
            '"production": False',
        ):
            self.assertIn(snippet, self.harness)
        self.assertNotIn('"password":', self.harness)
        self.assertNotIn('"authorization":', self.harness)


if __name__ == "__main__":
    unittest.main()
