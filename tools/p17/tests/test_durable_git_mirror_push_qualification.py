from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import durable_git_mirror_push_qualification as qualification


ROOT = Path(__file__).resolve().parents[3]


class DurableGitMirrorPushQualificationTests(unittest.TestCase):
    def test_exact_current_pc_qualification_without_product_promotion(self) -> None:
        contract = qualification.verify(ROOT)
        claims = contract["claims"]
        self.assertTrue(claims["actual_current_pc_postgresql_18_4"])
        self.assertTrue(claims["actual_disposable_local_bare_git"])
        self.assertTrue(claims["actual_authenticated_loopback"])
        self.assertTrue(claims["actual_committed_effect_recovery"])
        self.assertTrue(claims["actual_divergence_preservation"])
        self.assertFalse(claims["actual_remote_network"])
        self.assertFalse(claims["durable_pull"])
        self.assertFalse(claims["persistent_credential_custody"])
        self.assertFalse(claims["actual_hangul"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_receipt_claim_and_unknown_field_tamper_fail_closed(self) -> None:
        receipt_path = ROOT / qualification.RECEIPT_RELATIVE
        receipt = qualification.load_document(receipt_path, "receipt")
        promoted = copy.deepcopy(receipt)
        promoted["actual_remote_network"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.actual_remote_network"):
            qualification.validate_receipt(promoted, ROOT)
        expanded = copy.deepcopy(receipt)
        expanded["authorization"] = "invented"
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.fields"):
            qualification.validate_receipt(expanded, ROOT)

    def test_receipt_source_and_check_tamper_fail_closed(self) -> None:
        receipt_path = ROOT / qualification.RECEIPT_RELATIVE
        receipt = qualification.load_document(receipt_path, "receipt")
        source_tamper = copy.deepcopy(receipt)
        source_tamper["source_sha256"]["coordinator"] = "0" * 64
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.sources"):
            qualification.validate_receipt(source_tamper, ROOT)
        check_tamper = copy.deepcopy(receipt)
        check_tamper["checks"] = check_tamper["checks"][:-1]
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.checks"):
            qualification.validate_receipt(check_tamper, ROOT)

    def test_committed_runtime_source_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(root: Path, commit: str, relative: str) -> bytes:
            raw = original(root, commit, relative)
            if relative == "crates/remote-sync-host/src/durable_git_push.rs":
                return raw + b"\n"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(qualification.QualificationError, "receipt.sources"):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
