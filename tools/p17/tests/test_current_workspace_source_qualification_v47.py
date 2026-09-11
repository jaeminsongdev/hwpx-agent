from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v47 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV47Tests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v47.20260911",
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_source_counts_are_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["implementation_source_count"], 22)
        self.assertEqual(result["runtime_qualification_source_count"], 5)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 86)

    def test_broker_claims_do_not_promote_external_or_product(self) -> None:
        result = qualification.verify(ROOT)
        self.assertTrue(result["credential_broker_component_verified"])
        self.assertTrue(result["all_lifecycle_operations_pure_model_verified"])
        self.assertTrue(result["current_pc_windows_issue_revoke_verified"])
        self.assertTrue(result["pinned_loopback_tls_current_pc_verified"])
        self.assertTrue(result["synthetic_ephemeral_issuer_only"])
        self.assertFalse(result["actual_external_issuer"])
        self.assertFalse(result["real_client_assertion"])
        self.assertFalse(result["real_service_credential"])
        self.assertFalse(result["windows_atomic_vault_state_integration"])
        self.assertFalse(result["windows_power_loss_durability"])
        self.assertFalse(result["actual_external_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["p17_06_complete"])
        self.assertFalse(result["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/remote-credential-broker/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenSourceV47Error, "implementation.bytes"
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
