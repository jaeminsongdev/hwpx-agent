from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_atomic_mirror_checkpoint_v1 as qualification

ROOT = Path(__file__).resolve().parents[3]


class AtomicMirrorCheckpointQualificationTests(unittest.TestCase):
    def test_frozen_qualification_is_exact_without_product_promotion(self) -> None:
        contract = qualification.verify(ROOT)
        claims = contract["claims"]
        self.assertTrue(claims["actual_atomic_mirror_admission_and_checkpoint"])
        self.assertTrue(claims["durable_retention_mirror_admission"])
        self.assertEqual(claims["actual_separate_client_processes"], 7)
        self.assertFalse(claims["actual_pull_or_push"])
        self.assertFalse(claims["persistent_credential_custody"])
        self.assertFalse(claims["actual_hangul"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])

    def test_contract_tamper_fails_closed(self) -> None:
        original = qualification.frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = qualification.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == qualification.CONTRACT_RELATIVE:
                return raw + b"\n"
            return raw

        with patch.object(qualification.frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenAtomicMirrorCheckpointError,
                "contract.bytes",
            ):
                qualification.verify(ROOT)

    def test_runtime_source_tamper_fails_closed(self) -> None:
        original = qualification.frozen.git_blob
        target = "crates/remote-sync-host/src/postgres.rs"

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = qualification.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return b"tampered" if relative == target else raw

        with patch.object(qualification.frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenAtomicMirrorCheckpointError,
                "runtime.bytes",
            ):
                qualification.verify(ROOT)

    def test_receipt_promotion_and_unknown_field_fail_closed(self) -> None:
        raw = (ROOT / qualification.RECEIPT_RELATIVE).read_bytes()
        receipt = qualification.load_json(raw, "receipt")
        promoted = copy.deepcopy(receipt)
        promoted["actual_hangul"] = True
        with self.assertRaisesRegex(
            qualification.FrozenAtomicMirrorCheckpointError,
            "receipt.hangul",
        ):
            qualification.validate_receipt(promoted, ROOT)
        expanded = copy.deepcopy(receipt)
        expanded["authorization"] = "invented"
        with self.assertRaisesRegex(
            qualification.FrozenAtomicMirrorCheckpointError,
            "receipt.fields",
        ):
            qualification.validate_receipt(expanded, ROOT)


if __name__ == "__main__":
    unittest.main()
