"""Lightweight source boundaries only. Not Rust execution, DB, native or Gate proof."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]


class Boundaries(unittest.TestCase):
    def text(self, path):
        return (ROOT / path).read_text(encoding="utf-8-sig")

    def test_closed_no_change_not_any_error_fallback(self):
        source = self.text("crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs")
        self.assertTrue("FormulaResultOutputError::NoChange" in source)
        self.assertTrue("Err(error) => Err(Box::new(error))" in source)
        self.assertTrue("evaluation.verify_source(&input.raw)?" in source)
        self.assertTrue("actual_outcome == expected_outcome" in source)

    def test_original_paths_and_no_forged_policy_record(self):
        source = self.text("crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs")
        for token in ("self.registrar.register_formula_policy(scope, record)?", "provisioner.issue_approval(scope, record, &signer, 0, 60)",
            "StoredProductRequest::prepare_formula_with_issuer", "prepared.with_verified_bytes", "signature_approval_SQL_commit_readback"):
            self.assertTrue(token in source, "required_original_path_token_missing")
        self.assertFalse("FormulaPolicyRegistrationRecord {" in source)

    def test_worker_real_lease_sequence_and_bounded_connection(self):
        worker = self.text("crates/product-cli/examples/formula_issuer_product_postgres_probe/worker.rs")
        for token in ("claim_idempotent_job_with_full_ir_v1", "lease_idempotent_job_v2", "advance_idempotent_job_v2",
            "complete_idempotent_job_success_v2", "RevisionCommitLease::bind", "connect_timeout"):
            self.assertTrue(token in worker, "worker_sequence_missing")
        self.assertFalse("Failure::Fixture" in worker)

    def test_fixture_isolation(self):
        sql = self.text("tools/p09/fixtures/formula_issuer_product.sql")
        self.assertTrue("NOBYPASSRLS NOREPLICATION" in sql)
        self.assertTrue("P143_WORKER_WRITER_OR_HELPER_PRIVILEGE" in sql)
        for forbidden in ("DISABLE TRIGGER", "UPDATE hwpx_agent.schema_versions", "INSERT INTO hwpx_agent.revisions",
            "INSERT INTO hwpx_agent.idempotency", "INSERT INTO hwpx_agent.formula_approval_versions"):
            self.assertFalse(forbidden in sql)

    def test_driver_closed_scope_and_own_cleanup(self):
        driver = self.text("tools/p09/run_formula_issuer_product_probe.py")
        ast.parse(driver)
        for token in ('"--pull", "never"', '"127.0.0.1::5432"', '"--memory", "512m"',
            '"--cpus", "1"', '"rm", "--force", created_id', 'destination.open("x"',
            '"atomic_product_publication_qualified": False', '"all_36_source_inputs_qualified": False'):
            self.assertTrue(token in driver, "driver_boundary_missing")

    def test_failed_and_historical_not_promoted(self):
        audit = self.text("tools/p09/verify_formula_issuer_product_progress.py")
        self.assertTrue('"current_accepted_build": None' in audit)
        self.assertTrue('"NOT_RUN_RESOURCE_STOP_AND_DEFER"' in audit)
        self.assertTrue('run["state"] == "FAIL_CLOSED"' in audit)


if __name__ == "__main__":
    unittest.main()
