"""Source shape checks only; six Rust enum tests are added but NOT_RUN here."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]


class TypedRouteBoundary(unittest.TestCase):
    def source(self):
        return (ROOT / "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs").read_text(encoding="utf-8")

    def test_original_route_result_uses_exact_typed_classifier(self):
        block = self.source().split('"full_product_route_not_falsely_enabled"', 1)[1].split("let after", 1)[0]
        self.assertTrue("route_denial_matches(" in block)
        self.assertTrue("prepared.require_current_product_route(provider, &deps)" in block)
        self.assertFalse(".is_err()" in block)

    def test_both_typed_route_branches_and_no_any_error_pattern(self):
        block = self.source().split("fn route_denial_matches(", 1)[1].split("fn consumer_error(", 1)[0]
        for token in ('"changed"', '"unchanged"', "Operation::RouteUnqualified", "Compiler::Source(Output::RouteUnqualified)"):
            self.assertTrue(token in block)
        self.assertFalse("Err(_)" in block)
        self.assertFalse("is_err" in block)

    def test_six_pending_Rust_cases_are_explicit(self):
        block = self.source().split("mod route_tests", 1)[1]
        self.assertEqual(len(re.findall(r"#\[test\]", block)), 6)
        for token in ("FormulaIssuerError::Signature", "StoredFormulaPolicyError::Repository",
            "rejects_wrong_outcome_route_branch", "rejects_product_route_success", "rejects_unknown_outcome"):
            self.assertTrue(token in block)


if __name__ == "__main__":
    unittest.main()
