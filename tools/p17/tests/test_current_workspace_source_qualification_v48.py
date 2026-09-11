from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v48 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV48Tests(unittest.TestCase):
    def test_exact_qualification_sources_and_nonclaims_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v48.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 33)
        self.assertEqual(len(result["runtime_qualification_sources"]), 9)
        self.assertEqual(len(result["guard_sources"]), 3)
        claims = result["claims"]
        self.assertTrue(claims["p17_remote_credential_issuer_service_component_verified"])
        self.assertTrue(
            claims["p17_client_assertion_signature_and_freshness_component_verified"]
        )
        self.assertTrue(claims["p17_issuer_all_lifecycle_operations_verified"])
        self.assertTrue(claims["p17_independently_bound_tls_issuer_current_pc_verified"])
        self.assertTrue(claims["p17_broker_fixed_sequence_slot_verified"])
        self.assertTrue(claims["p17_broker_32_writer_single_winner_verified"])
        self.assertFalse(claims["p17_external_independently_operated_issuer_verified"])
        self.assertFalse(claims["p17_external_signer_hsm_kms_verified"])
        self.assertFalse(claims["p17_real_client_assertion_verified"])
        self.assertFalse(claims["p17_windows_power_loss_durability_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.foundation.git_blob

        def tampered(root: Path, revision: str, relative: str) -> bytes:
            raw = original(root, revision, relative)
            if relative == "crates/remote-credential-issuer/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification.foundation, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "implementation.history"
            ):
                qualification.verify(ROOT)

    def test_runtime_gate_promotion_tamper_fails_closed(self) -> None:
        result = qualification.issuer_gate.verify(ROOT)
        tampered = dict(result)
        tampered["external_independently_operated_issuer"] = True
        with patch.object(qualification.issuer_gate, "verify", return_value=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "runtime.issuer_claims"
            ):
                qualification.validate_runtime_qualification(ROOT)
        broker = qualification.broker_v2_gate.verify(ROOT)
        weakened = dict(broker)
        weakened["expected_winners"] = 2
        with patch.object(
            qualification.broker_v2_gate, "verify", return_value=weakened
        ):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "runtime.broker_v2_claims"
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
