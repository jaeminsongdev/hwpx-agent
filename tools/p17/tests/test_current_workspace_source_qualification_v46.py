from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v46 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV46Tests(unittest.TestCase):
    def test_exact_qualification_sources_and_nonclaims_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v46.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 10)
        self.assertEqual(len(result["runtime_qualification_sources"]), 2)
        self.assertEqual(len(result["guard_sources"]), 3)
        claims = result["claims"]
        self.assertTrue(
            claims["p17_remote_credential_lifecycle_current_pc_pure_component_verified"]
        )
        self.assertTrue(
            claims[
                "p17_remote_credential_lifecycle_issue_refresh_rotate_revoke_component_verified"
            ]
        )
        self.assertFalse(claims["p17_external_credential_issuer_verified"])
        self.assertFalse(claims["p17_credential_issuance_rotation_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.foundation.git_blob

        def tampered(root: Path, revision: str, relative: str) -> bytes:
            raw = original(root, revision, relative)
            if relative == "crates/remote-credential-lifecycle/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification.foundation, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "implementation.history"
            ):
                qualification.verify(ROOT)

    def test_receipt_and_predecessor_are_exact(self) -> None:
        self.assertEqual(
            qualification.foundation.digest(qualification.receipt_path(ROOT).read_bytes()),
            qualification.RECEIPT_SHA256,
        )
        qualification.validate_predecessor(ROOT)


if __name__ == "__main__":
    unittest.main()
