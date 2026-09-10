from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v44 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV44Tests(unittest.TestCase):
    def test_exact_qualification_and_counts_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v44.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 10)
        self.assertEqual(len(result["runtime_qualification_sources"]), 2)
        self.assertEqual(len(result["guard_sources"]), 3)

    def test_tls_claims_remain_bounded(self) -> None:
        result = qualification.verify(ROOT)
        claims = result["claims"]
        self.assertTrue(claims["p17_remote_tls_transport_current_pc_loopback_qualified"])
        self.assertTrue(claims["p17_remote_tls_transport_synthetic_certificate_only"])
        self.assertFalse(claims["p17_remote_tls_transport_external_network_verified"])
        self.assertFalse(claims["p17_real_service_certificate_verified"])
        self.assertFalse(claims["p17_real_service_credential_verified"])
        self.assertFalse(claims["p17_credential_issuance_rotation_verified"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["product_complete"])

    def test_base_implementation_is_exact_committed_history(self) -> None:
        original = qualification.foundation.git_blob

        def tampered(root: Path, revision: str, relative: str) -> bytes:
            raw = original(root, revision, relative)
            if relative == "crates/remote-tls-transport/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification.foundation, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError,
                "implementation.history",
            ):
                qualification.verify(ROOT)

    def test_runtime_promotion_tamper_fails_closed(self) -> None:
        original = qualification.tls.verify

        def promoted(root: Path = ROOT) -> dict[str, object]:
            result = original(root)
            result["actual_external_remote_network"] = True
            return result

        with patch.object(qualification.tls, "verify", side_effect=promoted):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError,
                "runtime.claims",
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
