"""Exact byte inverse units use real current/archive source; no runtime/native promotion."""
import importlib.util
import os
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p127", Path(__file__).parents[1] / "verify_comment_style_guard_progress.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class Inverse(unittest.TestCase):
    def setUp(self):
        self.before = (P.ROOT / P.ARCHIVE).read_bytes()
        self.after = (P.ROOT / P.PARENT).read_bytes()

    def test_actual_inverse(self): P.validate_inverse(self.before, self.after)
    def test_cwd_remains_real_workspace(self):
        self.assertEqual(os.fspath(P.ArchivedParentReadView()), str(P.ROOT))
    def test_missing_collection_rejected(self):
        with self.assertRaises(ValueError): P.validate_inverse(self.before, self.after.replace(P.COLLECTION, b"", 1))
    def test_duplicate_collection_rejected(self):
        with self.assertRaises(ValueError): P.validate_inverse(self.before, self.after + P.COLLECTION)
    def test_unrelated_edit_rejected(self):
        with self.assertRaises(ValueError): P.validate_inverse(self.before, self.after + b"// unrelated\n")
    def test_wrong_preimage_rejected(self):
        with self.assertRaises(ValueError): P.validate_inverse(self.before + b"// wrong\n", self.after)


if __name__ == "__main__": unittest.main(verbosity=1)
