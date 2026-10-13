"""Negative checks for the bounded byte verifier, not comment semantic acceptance."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location(
    "review_metadata_progress", Path(__file__).resolve().parents[1] / "verify_review_metadata_progress.py"
)
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ByteVerifierTests(unittest.TestCase):
    def test_complete_bytes_and_length_not_only_declared_hash_are_checked(self):
        with tempfile.TemporaryDirectory(prefix="p09-95-byte-oracle-") as directory:
            root = Path(directory)
            # These are temporary test-only bytes, never repository or native originals.
            (root / "fixture").write_bytes(b"SYNTHETIC")
            with mock.patch.object(VERIFIER, "ROOT", root):
                record = VERIFIER.pin("fixture")
                self.assertTrue(VERIFIER.exact(record))
                self.assertFalse(VERIFIER.exact({**record, "bytes": record["bytes"] + 1}))
                self.assertFalse(VERIFIER.exact({**record, "sha256": "0" * 64}))
                self.assertFalse(VERIFIER.exact(record, "missing"))

    def test_previous_checkpoint_is_not_admitted_after_hash_refresh(self):
        real_pin = VERIFIER.pin

        def forged(path):
            value = real_pin(path)
            return {**value, "sha256": "0" * 64} if path == VERIFIER.PREVIOUS else value

        with mock.patch.object(VERIFIER, "pin", forged):
            with self.assertRaisesRegex(ValueError, "previous_checkpoint_drift"):
                VERIFIER.previous_audit()

    def test_original_old_executable_cannot_be_omitted_or_refreshed(self):
        real_pin = VERIFIER.pin

        def forged(path):
            value = real_pin(path)
            return {**value, "sha256": "0" * 64} if path.endswith("stored_comment_provider-9065c76bcbac10b7.exe") else value

        with mock.patch.object(VERIFIER, "pin", forged):
            with self.assertRaisesRegex(ValueError, "previous_raw_pin_not_preserved"):
                VERIFIER.previous_audit()


if __name__ == "__main__":
    unittest.main()
