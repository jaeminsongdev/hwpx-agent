"""P142 source contracts; runtime receipts separately prove actual AEAD/root/SQL paths."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
PROBE = "crates/product-cli/examples/formula_registry_crypto_postgres_probe.rs"
BUILD = "tools/p09/build_formula_registry_crypto_probe.ps1"
DRIVER = "tools/p09/run_formula_registry_crypto_probe.py"
FIXTURE = "tools/p09/fixtures/formula_registry_crypto.sql"


class Contracts(unittest.TestCase):
    def test_original_admitted_service_registry_and_workflow_are_used(self):
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        for token in ["connect_formula_issuer_registry_schema22", "ArtifactService::new(",
            "PostgresFormulaIssuerWriteGateway::new", "PostgresFormulaPolicyProvider::new",
            "RegistryFormulaProvisioner::new", "provisioner.install_trust(draft, 3)?",
            "reader.read_trust("]:
            self.assertIn(token, text)
        self.assertNotIn("connect_schema22_diagnosed", text)
        self.assertNotIn("impl FormulaIssuerRegistryRepository", text)
        self.assertNotIn("allow(clippy", text)

    def test_real_encryption_digest_and_audit_are_cross_checked(self):
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        for token in ["SystemRandom::new()", "random.fill(&mut key)", "Aes256GcmKeyring::new",
            "key.fill(0)", "hmac.fill(0)", "Ed25519KeyPair::generate_pkcs8",
            "artifacts.download(context, row.artifact, now)?", "ContentDigest::of(&raw) == row.digest",
            "record.content_sha256() == row.digest", "ContentDigest::of(&ciphertext)",
            "record.encryption().ciphertext_sha256", "ciphertext.windows(raw.len())", "audit_events()?"]:
            self.assertIn(re.sub(r"\s+", "", token), re.sub(r"\s+", "", text),
                "required_crypto_binding_marker_missing")

    def test_scoped_fixture_grants_not_privilege_bypass(self):
        text = (ROOT / FIXTURE).read_text(encoding="utf-8")
        self.assertIn("NOBYPASSRLS NOREPLICATION", text)
        self.assertIn("GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts", text)
        self.assertIn("GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit", text)
        self.assertNotIn("GRANT ALL", text)
        self.assertNotIn("DISABLE TRIGGER", text)
        self.assertNotIn("ALTER TABLE", text)
        self.assertNotIn("GRANT SELECT ON hwpx_agent.formula_issuer", text)

    def test_bounded_build_and_predecessor_preimage_protection(self):
        text = (ROOT / BUILD).read_text(encoding="utf-8")
        for token in ["historical_parent_archive_drift", "undeclared_original_parent_change",
            "whole_workspace_Rust_input_coverage_drift", "Test-Pins $protected", "Test-Pins $freeze",
            "--jobs','1'", "BelowNormal", "Get-P09ResourceDecision", "fresh_output_required"]:
            self.assertIn(token, text)

    def test_runtime_is_exclusive_owned_loopback_DB_with_cleanup(self):
        text = (ROOT / DRIVER).read_text(encoding="utf-8")
        for token in ["hwpx-agent.p09-142-owned-root-crypto-test", "127.0.0.1::5432", "--pull",
            "--read-only", "--memory", "--cpus", "owned_container_identity_mismatch",
            "owned_container_isolation_mismatch", 'destination.open("x"', "owned_container_removal_unverified",
            "original_root_crypto_workflow_failed", "source_freeze_exact_after"]:
            self.assertIn(token, text)
        self.assertNotIn("--password", text)
        self.assertNotIn("DISABLE TRIGGER", text)

    def test_closed_output_keeps_qualification_boundaries(self):
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        for token in ['"real_approval_signature_or_product_consumer_executed":false',
            '"durable_blob_store_qualified":false', '"production_key_custody_qualified":false',
            '"P09_gate":"OPEN"', '"product_complete":false']:
            self.assertIn(token, text)
        self.assertNotIn("eprintln!", text)
        self.assertNotIn("println!(\"{error", text)


if __name__ == "__main__":
    unittest.main()
