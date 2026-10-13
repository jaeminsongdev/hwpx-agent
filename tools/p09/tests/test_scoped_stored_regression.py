"""Coverage-set unit only. Actual receipt validation is separate in the audit command."""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "p126", Path(__file__).parents[1] / "audit_scoped_stored_regression.py"
)
P126 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P126)


class Coverage(unittest.TestCase):
    def setUp(self):
        self.imported = [f"actual_import::unit_{i:03d}" for i in range(200)]
        self.documents = [f"full_document::unit_{i:03d}" for i in range(20)]
        self.roots = P126.R.P123.ROOT_NAMES.copy()
        self.inventory = [*self.imported, *self.documents, *self.roots]

    def check(self):
        return P126.validate_coverage(self.inventory, self.imported, self.documents, self.roots)

    def test_disjoint_228(self): self.assertEqual(self.check(), 228)
    def test_missing_import(self):
        self.imported.pop()
        with self.assertRaises(ValueError): self.check()
    def test_duplicate_import(self):
        self.imported[1] = self.imported[0]
        with self.assertRaises(ValueError): self.check()
    def test_duplicate_document(self):
        self.documents[1] = self.documents[0]
        with self.assertRaises(ValueError): self.check()
    def test_wrong_root(self):
        self.roots[0] = "unexpected_root"
        with self.assertRaises(ValueError): self.check()
    def test_foreign_test(self):
        self.imported[0] = "actual_import::foreign"
        with self.assertRaises(ValueError): self.check()
    def test_wrong_inventory(self):
        self.inventory[0] = self.inventory[1]
        with self.assertRaises(ValueError): self.check()
    def test_order_irrelevant(self):
        self.inventory.reverse()
        self.assertEqual(self.check(), 228)


if __name__ == "__main__": unittest.main(verbosity=1)
