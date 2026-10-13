"""P144 lightweight source guards only; not Rust/SQL/native evidence."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]


class CorpusBoundary(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_locked_manifest_index_and_no_arbitrary_input_path(self):
        text = self.source("crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs")
        for token in ("configured_index()?", "rows.get(index)", "index >= 36", "index.to_string() != value",
            "manifest_digest_drift", "source_digest_drift", "VarError::NotPresent"):
            self.assertTrue(token in text)
        self.assertFalse('std::env::var("P144_SOURCE_PATH")' in text)

    def test_original_AST_and_source_anchor_bind_the_numeric_leaf(self):
        text = self.source("crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs")
        for token in ("formula.ast().expression()", "binding.source_anchor", "binding.coordinate",
            "checked_add(101)", "verify_one_leaf(original, &changed, index)?"):
            self.assertTrue(token in text)

    def test_whole_inventory_other_parts_and_outside_leaf_are_checked(self):
        text = self.source("crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs")
        for token in ("old.keys().eq(next.keys())", "next.get(path) != Some(bytes)",
            "reconstructed != *next_bytes", "old_value == new_value", "BoundedZipReader::open"):
            self.assertTrue(token in text)
        self.assertFalse("std::fs::write" in text)
        self.assertFalse("File::create" in text)

    def test_actual_identity_and_expected_outcome_are_mandatory(self):
        text = self.source("tools/p09/run_formula_issuer_corpus_probe.py")
        ast.parse(text)
        for token in ('result["source_index"] == source_index', 'result["input_mode"] == input_mode',
            'result["original_source_sha256"] == original_source_pin["sha256"]',
            'result["formula_outcome"] == expected_outcome', 'result["only_one_numeric_leaf_changed"] is True'):
            self.assertTrue(token in text)

    def test_owned_DB_scope_and_historical_executables_are_kept(self):
        text = self.source("tools/p09/run_formula_issuer_corpus_probe.py")
        for token in ('"--pull", "never"', '"127.0.0.1::5432"', '"--cpus", "1"',
            '"rm", "--force", created_id', 'destination.open("x"', '== 48',
            '"atomic_product_publication_qualified": False'):
            self.assertTrue(token in text)

    def test_Rust_harness_requires_route6_plus_index5_not_zero_tests(self):
        text = self.source("tools/p09/run_formula_issuer_corpus_unit_probe.py")
        ast.parse(text)
        self.assertTrue("(11, 0, 0, 0, 0)" in text)
        self.assertTrue('result["tests"] == EXPECTED' in text)
        self.assertTrue('"source::source_index_tests::"' in text)


if __name__ == "__main__":
    unittest.main()
