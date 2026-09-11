from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v47 as frozen


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_current_source_v47.py"


class FrozenCurrentSourceV47Tests(unittest.TestCase):
    def test_exact_historical_qualification_passes_without_phase_promotion(self) -> None:
        result = frozen.verify(ROOT)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["implementation_source_count"], 22)
        self.assertEqual(result["runtime_qualification_source_count"], 5)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 86)
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["credential_broker_component_verified"])
        self.assertTrue(result["all_lifecycle_operations_pure_model_verified"])
        self.assertTrue(result["current_pc_windows_issue_revoke_verified"])
        self.assertTrue(result["pinned_loopback_tls_current_pc_verified"])
        self.assertTrue(result["append_only_reconciliation_model_verified"])
        self.assertTrue(result["synthetic_ephemeral_issuer_only"])
        self.assertFalse(result["actual_external_issuer"])
        self.assertFalse(result["real_client_assertion"])
        self.assertFalse(result["real_service_credential"])
        self.assertFalse(result["windows_atomic_vault_state_integration"])
        self.assertFalse(result["windows_power_loss_durability"])
        self.assertFalse(result["credential_issuance_or_rotation"])
        self.assertFalse(result["actual_external_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["p17_06_complete"])
        self.assertFalse(result["product_complete"])
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_contract_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == frozen.CONTRACT_RELATIVE:
                return raw + b"\n"
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV47Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_component_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == frozen.COMPONENT_CONTRACT_RELATIVE:
                return b"tampered"
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV47Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_source_has_no_mutable_qualification_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            "from tools.p17 import current_workspace_source_qualification_v47",
            source,
        )
        self.assertNotIn(
            "from tools.p17 import validate_remote_credential_broker_contract",
            source,
        )
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)
        self.assertIn("frozen_current_source_v46", source)


if __name__ == "__main__":
    unittest.main()
