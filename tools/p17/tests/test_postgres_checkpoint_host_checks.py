from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]


class PostgresCheckpointHostChecksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up = (
            ROOT / "migrations/postgres/0014_p17_history_checkpoint_note.up.sql"
        ).read_text(encoding="utf-8")
        cls.down = (
            ROOT / "migrations/postgres/0014_p17_history_checkpoint_note.down.sql"
        ).read_text(encoding="utf-8")
        cls.adapter = (ROOT / "crates/remote-sync-host/src/postgres.rs").read_text(
            encoding="utf-8"
        )
        cls.host = (
            ROOT / "crates/remote-sync-host/examples/postgres_checkpoint_host.rs"
        ).read_text(encoding="utf-8")
        cls.client = (
            ROOT / "crates/remote-sync-host/examples/postgres_checkpoint_client.rs"
        ).read_text(encoding="utf-8")
        cls.harness = (
            ROOT / "tools/p17/run_postgres_checkpoint_host_checks.py"
        ).read_text(encoding="utf-8")

    def test_migration_is_exactly_versioned_and_note_preserving(self) -> None:
        required = [
            "version = 13 AND migration_name = 'p16.plan_review_evidence_v1'",
            "version >= 14",
            "ADD COLUMN note text",
            "char_length(note) BETWEEN 1 AND 1000",
            "CREATE FUNCTION hwpx_agent.create_history_checkpoint_v2(",
            "SECURITY DEFINER",
            "hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id",
            "hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256",
            "role IN ('editor', 'owner')",
            "seal.seal_kind = 'service_v1'",
            "revision_id, label, note, subject_sha256",
            "v_claim.label, v_claim.note, v_claim.subject_sha256",
            "ERRCODE = 'P1701'",
            "v_checkpoint.created_by_subject_sha256",
            "HISTORY_CHECKPOINT_STATE_MISMATCH",
            "HISTORY_CHECKPOINT_AUDIT_MISMATCH",
            "'history.checkpoint_created'",
            "REVOKE ALL ON FUNCTION hwpx_agent.create_history_checkpoint_v2(",
            "VALUES (14, 'p17.history_checkpoint_note_v2'",
        ]
        for snippet in required:
            self.assertIn(snippet, self.up)
        self.assertNotIn("GRANT EXECUTE", self.up)

    def test_rollback_refuses_immutable_note_data(self) -> None:
        required = [
            "allow_p17_history_checkpoint_note_rollback",
            "version = 14 AND migration_name = 'p17.history_checkpoint_note_v2'",
            "version > 14",
            "history_checkpoint_requests WHERE note IS NOT NULL",
            "checkpoints WHERE note IS NOT NULL",
            "rollback would discard immutable data",
            "DROP FUNCTION hwpx_agent.create_history_checkpoint_v2(",
            "DROP COLUMN note",
            "ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable",
            "ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable",
        ]
        for snippet in required:
            self.assertIn(snippet, self.down)

    def test_rust_adapter_is_loopback_exact_and_fail_closed(self) -> None:
        required = [
            "const MIGRATIONS: [&[u8]; 14]",
            'migration!("0014_p17_history_checkpoint_note.up.sql")',
            '.host("127.0.0.1")',
            "IsolationLevel::Serializable",
            ".try_lock()",
            "set_config('hwpx_agent.tenant_id',$1,true)",
            "set_config('hwpx_agent.subject_sha256',$2,true)",
            "create_history_checkpoint_v2",
            "legacy_execute",
            "history_checkpoint_requests",
            "CheckpointDispatchError::Unavailable",
            'Some("22023" | "23503" | "23505" | "23514" | "42501" | "P0002" | "P1701" | "P1702")',
        ]
        for snippet in required:
            self.assertIn(snippet, self.adapter)
        self.assertEqual(
            self.adapter.count("FROM hwpx_agent.create_history_checkpoint_v2("), 1
        )
        self.assertNotIn("retry", self.adapter.lower().split("fn dispatch", 1)[1])

    def test_separate_process_probes_are_bounded_and_secret_redacted(self) -> None:
        for source in (self.host, self.client):
            self.assertIn('const REQUIRED_MODE: &str = "isolated-current-pc";', source)
            self.assertNotIn("std::process::Command", source)
        self.assertIn("Ipv4Addr::LOCALHOST", self.host)
        self.assertIn("LoopbackCheckpointServer::bind", self.host)
        self.assertIn("LocalPostgresHistoryCheckpointDispatcher::connect", self.host)
        self.assertIn(
            'Zeroizing::new(setting("HWPX_P17_AUTH_HMAC_SECRET")?)', self.host
        )
        self.assertIn("SingleUseCredentialProvider::new", self.client)
        self.assertIn("LoopbackTcpTransport::new", self.client)
        self.assertIn('Zeroizing::new(setting("HWPX_P17_AUTHORIZATION")?)', self.client)
        self.assertNotIn("HWPX_P17_AUTHORIZATION", self.host)

    def test_harness_pins_resources_and_never_persists_secrets(self) -> None:
        required = [
            'LABEL = "hwpx-agent.p17-postgres-checkpoint-host-test"',
            "--pull",
            "never",
            '"--publish", "127.0.0.1::5432"',
            '"--memory", "512m"',
            '"--pids-limit", "128"',
            "subprocess.Popen(",
            "client_process_count",
            "same_key_changed_note_rejected",
            "corrupt_checkpoint_replay_fails_unavailable",
            "empty_rollback_requires_explicit_gate",
            "empty_rollback_and_reapply",
            "data_loss_rollback_refused",
            "migration_digest_drift_rejected",
            "execute_privilege_drift_rejected",
            '"secrets_persisted": False',
            'docker, "rm", "--force", container',
            'docker, "volume", "rm", volume',
        ]
        for snippet in required:
            self.assertIn(snippet, self.harness)
        self.assertEqual(
            len(re.findall(r'\(14, "p17_history_checkpoint_note"\)', self.harness)), 1
        )
        self.assertNotIn('"password":', self.harness)
        self.assertNotIn('"authorization":', self.harness)

    def test_every_current_postgres_adapter_accepts_migration_16(self) -> None:
        paths = [
            ROOT / "crates/artifact-service/src/store/postgres_repository.rs",
            ROOT / "crates/mcp-control-plane/src/postgres_plan_source.rs",
            ROOT / "crates/mcp-control-plane/src/postgres_stored_plan.rs",
            ROOT / "crates/mcp-control-plane/src/postgres_plan_review.rs",
        ]
        for path in paths:
            source = path.read_text(encoding="utf-8")
            self.assertIn("const MIGRATIONS: [&[u8]; 16]", source, path.as_posix())
            self.assertIn(
                'migration!("0014_p17_history_checkpoint_note.up.sql")', source
            )
            self.assertIn(
                'migration!("0015_p17_atomic_mirror_checkpoint.up.sql")', source
            )
            self.assertIn(
                'migration!("0016_p17_durable_git_mirror_push.up.sql")', source
            )
            self.assertIn("LIMIT 17", source)

    def test_fixture_has_only_the_bounded_subject_placeholder(self) -> None:
        fixture = (
            ROOT / "tools/p17/fixtures/p17_postgres_checkpoint_setup.sql"
        ).read_text(encoding="utf-8")
        self.assertEqual(fixture.count("__P17_SERVICE_SUBJECT_SHA256__"), 3)
        self.assertIn("'service_v1', 0, 1", fixture)
        self.assertIn("COMMIT;", fixture)
        self.assertNotIn("DROP ", fixture)


if __name__ == "__main__":
    unittest.main()
