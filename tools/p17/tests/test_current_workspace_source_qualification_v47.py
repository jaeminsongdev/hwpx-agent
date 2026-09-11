from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v47 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV47Tests(unittest.TestCase):
    def test_exact_qualification_sources_and_nonclaims_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v47.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 22)
        self.assertEqual(len(result["runtime_qualification_sources"]), 5)
        self.assertEqual(len(result["guard_sources"]), 3)
        claims = result["claims"]
        self.assertTrue(
            claims["p17_credential_broker_current_pc_windows_issue_revoke_verified"]
        )
        self.assertTrue(
            claims["p17_credential_broker_all_lifecycle_operations_pure_model_verified"]
        )
        self.assertTrue(
            claims["p17_credential_broker_pinned_loopback_tls_current_pc_verified"]
        )
        self.assertFalse(claims["p17_external_credential_issuer_verified"])
        self.assertFalse(claims["p17_credential_issuance_rotation_verified"])
        self.assertFalse(claims["p17_real_client_assertion_verified"])
        self.assertFalse(claims["p17_windows_atomic_vault_state_integration_verified"])
        self.assertFalse(claims["p17_windows_power_loss_durability_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.foundation.git_blob

        def tampered(root: Path, revision: str, relative: str) -> bytes:
            raw = original(root, revision, relative)
            if relative == "crates/remote-credential-broker/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification.foundation, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "implementation.history"
            ):
                qualification.verify(ROOT)

    def test_runtime_gate_promotion_tamper_fails_closed(self) -> None:
        result = qualification.broker_gate.verify(ROOT)
        tampered = dict(result)
        tampered["external_issuer"] = True
        with patch.object(qualification.broker_gate, "verify", return_value=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "runtime.claims"
            ):
                qualification.validate_runtime_qualification(ROOT)

    def test_receipt_and_predecessor_are_exact(self) -> None:
        self.assertEqual(
            qualification.foundation.digest(qualification.receipt_path(ROOT).read_bytes()),
            qualification.RECEIPT_SHA256,
        )
        qualification.validate_predecessor(ROOT)


if __name__ == "__main__":
    unittest.main()
