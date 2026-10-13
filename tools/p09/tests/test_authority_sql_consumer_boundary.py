"""P148 source/protocol guards, not actual SQL or product acceptance."""
from pathlib import Path
import unittest

import run_formula_issuer_corpus_probe as baseline
import run_formula_issuer_authority_sql_probe as current
from source_guard_fixture import SourceGuardFixture


class AuthoritySQLConsumerBoundary(SourceGuardFixture, unittest.TestCase):
    SOURCE_FILES = (("source", "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs"),
        ("driver", "tools/p09/run_formula_issuer_authority_sql_probe.py"))
    SOURCE_SLICE = ("fn verify_live_authority(", "fn revocation_race(")

    def test_original_checks_and_security_metadata_are_preserved(self):
        self.assertEqual(current.ROOT_CHECKS[:18], baseline.ROOT_CHECKS)
        self.assertEqual(current.CHECKS, baseline.CHECKS)
        self.assertEqual(len(current.ROOT_CHECKS), 33)
        self.assertEqual(len(set(current.ROOT_CHECKS)), 33)
        for name in current.ROOT_CHECKS[18:]:
            self.assertIn('"' + name + '"', self.live)

    def test_exact_opt_in_rejects_conflicting_live_case(self):
        self.assertIn('std::env::var("P148_LIVE_CASE")?', self.live)
        self.assertIn('matches!(case.as_str(), "trust" | "policy")', self.live)
        self.assertIn('std::env::var_os("P146_LIVE_CASE").is_some()', self.live)
        self.assertNotIn("unwrap_or", self.live)

    def test_rejected_stale_CAS_preserves_rows_and_candidate(self):
        self.assertIn("FormulaIssuerTrustRevocation::new(p.project, before.version, 5)?", self.live)
        self.assertIn("binding.policy_version,\n            2,", self.live)
        self.assertIn("p.registry.read_trust(&ctx, p.project)? == before", self.live)
        self.assertIn("repository.read_current(&ctx, &request)? == before", self.live)
        self.assertIn("prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted", self.live)
        self.assertLess(self.live.index("verify_authority_stale(probe"), self.live.index("verify_authority_revoke(probe"))

    def test_original_typed_revoke_and_commit_receipts(self):
        for token in ('super::config("p141_root")?', "RegistryManagementCapability::Trust",
                      "receipt.action() == FormulaRegistryManagementAction::RevokeTrust",
                      "PostgresFormulaPolicyRevoker::new(repository.clone())",
                      "policy.revoke(&source, provider, &revoker, now()?)?",
                      "receipt.policy_sha256 == before.policy_digest"):
            self.assertIn(token, self.live)
        self.assertNotIn("postgres::Client", self.live)
        self.assertNotIn("read_formula_policy", self.live)

    def test_callback_and_route_require_exact_repository_denial(self):
        typed = self.source[self.source.index("fn live_denial_matches<T>("):self.source.index("fn verify_live_approval(")]
        self.assertIn("StoredFormulaPolicyError::Repository", typed)
        self.assertNotIn("RouteUnqualified", typed)
        self.assertNotIn("is_err", typed)
        self.assertIn("callbacks.load(Ordering::SeqCst) == 0", self.live)
        self.assertIn("live_denial_matches(&StoredProductRequest::prepare_formula_with_issuer", self.live)
        self.assertIn("live_denial_matches(&prepared.require_current_product_route", self.live)

    def test_original_source_head_ingests_and_unrelated_authority(self):
        for token in ("== source_before", "== binding.head", "ingests_after == ingests_before",
                      "== *policy_before", "== *root_before", "*cached_policy.receipt()"):
            self.assertIn(token, self.live)
        self.assertIn("StoredFormulaPolicyError::Repository", self.live)

    def test_driver_keeps_original_privileges_isolation_and_fresh_output(self):
        prior = (current.ROOT / "tools/p09/run_formula_issuer_corpus_probe.py").read_text(encoding="utf-8")
        self.assertEqual([line.strip() for line in self.driver.splitlines() if "ALTER ROLE" in line],
                         [line.strip() for line in prior.splitlines() if "ALTER ROLE" in line])
        for token in ('timeout=60, rust=True', 'P148_LIVE_CASE=live_case', 'with destination.open("x"',
                      'owned_container_identity_mismatch', 'owned_container_isolation_mismatch',
                      '"root_revocations": 3 if live_case == "trust" else 2',
                      '"current_source_policy_revocations": 1 if live_case == "policy" else 0',
                      'JOIN hwpx_agent.source_formula_policy_versions v',
                      '"production_key_custody_qualified": False', '"atomic_product_publication_qualified": False'):
            self.assertIn(token, self.driver)
        self.assertNotIn("disable trigger", self.driver.lower())

    def test_resource_admission_precedes_hash_and_stops_remain_bounded(self):
        main = self.driver[self.driver.index("def main("):]
        self.assertLess(main.index("observed_limits(resources)"), main.index("pin(manifest_path)"))
        self.assertLess(main.index("admit_or_explain(resources)"), main.index("pin(manifest_path)"))
        for token in ('"container_memory_bytes": 536870912', '"pids_limit": 64',
                      '"cpu_stop_percent": 85', '"minimum_available_ram_mib": 4096',
                      '"post_hash_idle_RAM_min_mib": 8192', 'capture = BoundedProcessCapture(process)'):
            self.assertIn(token, main)
        helper = (current.ROOT / "tools/p09/bounded_process_progress.py").read_text(encoding="utf-8")
        self.assertIn('LIMIT = 32768', helper)
        self.assertIn('live_progress_output_limit', helper)


if __name__ == "__main__":
    unittest.main()
