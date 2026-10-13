"""P146 source/protocol guards only; does not qualify an actual SQL consumer run."""
from pathlib import Path
import unittest

import run_formula_issuer_corpus_probe as previous
import run_formula_issuer_live_sql_probe as current
from source_guard_fixture import SourceGuardFixture


class LiveSQLConsumerBoundary(SourceGuardFixture, unittest.TestCase):
    SOURCE_FILES = (("source", "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"),
        ("driver", "tools/p09/run_formula_issuer_live_sql_probe.py"))
    SOURCE_SLICE = ("fn verify_live_approval(", "fn route_denial_matches(")

    def test_original_checks_are_preserved_and_live_checks_are_additive(self):
        self.assertEqual(current.ROOT_CHECKS[:18], previous.ROOT_CHECKS)
        self.assertEqual(len(set(current.ROOT_CHECKS)), 27)
        for name in current.ROOT_CHECKS[18:]:
            self.assertIn('"' + name + '"', self.live)
        self.assertEqual(current.CHECKS, previous.CHECKS)

    def test_stale_CAS_preserves_readback_and_original_consumer(self):
        self.assertIn("before.generation == 1", self.live)
        self.assertIn("p.registry.read_approval(&ctx, &request)? == before", self.live)
        self.assertIn("prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted", self.live)
        self.assertLess(self.live.index("live_SQL_stale_generation_rejected_without_mutation"), self.live.index("race_begin"))

    def test_race_has_two_connections_and_exact_commit_denial_counts(self):
        for token in ("let first = connect()?", "let second = connect()?", "Barrier::new(3)",
            "first.revoke_approval(ctx, revoke)", "second.revoke_approval(ctx, revoke)",
            "[one.join(), two.join()]", "commits == 1 && denials == 1"):
            self.assertIn(token, self.live)
        self.assertIn('super::config("p141_approval")', self.live)
        self.assertNotIn("postgres::Client", self.live)

    def test_callback_and_route_denial_are_strict(self):
        typed = self.source[self.source.index("fn live_denial_matches<T>("):self.source.index("fn verify_live_approval(")]
        self.assertIn("StoredFormulaPolicyError::Repository", typed)
        self.assertNotIn("RouteUnqualified", typed)
        self.assertNotIn("is_err", typed)
        self.assertIn("callback_calls.load(Ordering::SeqCst) == 0", self.live)
        self.assertIn("live_denial_matches(&StoredProductRequest::prepare_formula_with_issuer", self.live)
        self.assertIn("live_denial_matches(&prepared.require_current_product_route", self.live)

    def test_driver_preserves_original_security_and_fresh_output_boundaries(self):
        for token in ('== expected_protected_count', '"approval_revocations": 3', 'timeout=60, rust=True',
            'P146_LIVE_CASE=live_case', 'with destination.open("x"', 'source_freeze_exact_after',
            'owned_container_identity_mismatch', 'owned_container_isolation_mismatch',
            '"issuer_provisioning_generation_race_qualified": False', '"trust_revocation_consumer_qualified": False'):
            self.assertIn(token, self.driver)
        self.assertNotIn("disable trigger", self.driver.lower())
        original_driver = (current.ROOT / "tools/p09/run_formula_issuer_corpus_probe.py").read_text(encoding="utf-8")
        original_roles = [line.strip() for line in original_driver.splitlines() if "ALTER ROLE" in line]
        current_roles = [line.strip() for line in self.driver.splitlines() if "ALTER ROLE" in line]
        self.assertEqual(current_roles, original_roles)

    def test_limits_and_diagnostics_are_bounded_and_do_not_log_query_text(self):
        main = self.driver[self.driver.index("def main("):]
        self.assertLess(main.index("resources = IdleResources()"), main.index("pin(manifest_path)"))
        self.assertLess(main.index("admit(resources)"), main.index("pin(manifest_path)"))
        self.assertIn("live_progress_output_limit", main)
        self.assertIn("set(markers).issubset(allowed_markers)", main)
        self.assertIn('"app", "state", "wait_type", "wait", "blocked_count"', main)
        self.assertNotIn("'query',query", main)
        self.assertIn('"P09_gate": "OPEN"', main)


if __name__ == "__main__":
    unittest.main()
