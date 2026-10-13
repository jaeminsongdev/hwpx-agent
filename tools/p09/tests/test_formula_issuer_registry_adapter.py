"""Source guards, not execution evidence for credential-bound Rust SQL22 adapters."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
PROBE = "crates/revision-service/examples/formula_issuer_registry_postgres_probe.rs"
DRIVER = "tools/p09/run_formula_issuer_registry_adapter.py"
BUILD = "tools/p09/build_formula_issuer_registry_adapter.ps1"
FIXTURE = "tools/p09/fixtures/formula_issuer_registry_adapter.sql"


class AdapterContracts(unittest.TestCase):
    def test_original_adapters_not_reimplemented_or_bypassed(self):
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        for name in ["LocalPostgresFormulaIssuerRegistryRepository::connect", "LocalPostgresFormulaRegistryManagementRepository::connect",
            "read_trust", "read_approval", "register_trust", "register_approval", "revoke_trust", "revoke_approval"]:
            self.assertIn(name, text)
        self.assertNotRegex(text, r"postgres::Client|batch_execute|ALTER ROLE|GRANT |unsafe\s*\{")

    def test_negative_checks_are_typed_error_checks(self):
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("matches!("), 18)
        for code in ["InvalidRequest", "NotFound", "RepositoryFailure"]:
            self.assertIn("Err(RevisionError::" + code + ")", text)
        self.assertIn("root_readback_all_fields_exact", text)
        self.assertIn("actual == root", text)
        self.assertIn("actual == approval", text)

    def test_profiles_minimal_and_bad_grants_deliberate(self):
        text = (ROOT / FIXTURE).read_text(encoding="utf-8")
        self.assertEqual(text.count("LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"), 5)
        self.assertNotRegex(text, r"GRANT ALL|\bSUPERUSER;|\bBYPASSRLS;")
        self.assertIn("IF n<>1 THEN RAISE EXCEPTION", text)
        self.assertIn("TO p141_bad_direct;", text)
        self.assertIn("TO p141_bad_helper;", text)
        self.assertNotIn("TO PUBLIC", text)

    def test_owned_loopback_container_limits_and_cleanup(self):
        text = (ROOT / DRIVER).read_text(encoding="utf-8")
        for token in ['"127.0.0.1::5432"', 'host["NetworkMode"] == "bridge"', 'not item["Mounts"]',
            'host["ReadonlyRootfs"] is True', 'host["Memory"] == host["MemorySwap"] == 536870912',
            'host["NanoCpus"] == 1000000000', 'host["PidsLimit"] == 64', '"--pull", "never"',
            'item["Id"] == created_id', '"rm", "--force", created_id', '"inspect", created_id']:
            self.assertIn(token, text)
        self.assertNotIn('"rm", "--force", name', text)

    def test_secrets_and_receipts_not_overwritten(self):
        text = (ROOT / DRIVER).read_text(encoding="utf-8")
        self.assertIn('destination.open("x"', text)
        self.assertIn('P141_DB_PASSWORD=password', text)
        self.assertIn('"--env", "POSTGRES_PASSWORD", IMAGE', text)
        self.assertNotRegex(text, r'print\([^\n]*(?:password|stderr|stdout|Config)')
        self.assertNotIn('receipt["password"]', text)
        self.assertNotIn('"--password", password', text)

    def test_build_preserves_inputs_and_runtime_profile(self):
        text = (ROOT / BUILD).read_text(encoding="utf-8")
        for token in ['--jobs', "'1'", 'BelowNormal', 'ProcessorAffinity', '$protected.Count -ne 35',
            '$sources.Count -ne 823', 'Test-Pins $old.source_freeze', 'Test-Pins $freeze',
            'extra-filename=-p141-', 'CARGO_PROFILE_DEV_OPT_LEVEL', 'CARGO_PROFILE_DEV_OVERFLOW_CHECKS',
            "'--profile','dev'", '-not $profile.test']:
            self.assertIn(token, text)
        self.assertIn("$diagnostics.Count -eq 0", text)
        self.assertIn("other_rust_workload_running", text)

    def test_original_sql22_and_schema_negative_are_executed(self):
        text = (ROOT / DRIVER).read_text(encoding="utf-8")
        for token in ['"original_SQL22_checks_committed"', 'len(set(checks)) == 37',
            'probe("metadata", CHECKS)', 'probe("changed_schema_denied"', 'probe("correct_schema_admitted"',
            'pin(executable["path"]) == executable', 'get("P09_gate")']:
            if token == 'get("P09_gate")':
                self.assertIn('doc["P09_gate"] == "OPEN"', text)
            else:
                self.assertIn(token, text)
        self.assertIn("CREATE DATABASE p141_correct_schema TEMPLATE p141_changed_schema", text)
        self.assertNotIn("UPDATE hwpx_agent.schema_versions", text)
        self.assertNotIn("DISABLE TRIGGER", text)

    def test_check_catalog_is_exact_and_scope_not_promoted(self):
        # AST-only extraction avoids importing/executing the Docker/resource dispatcher.
        import ast
        tree = ast.parse((ROOT / DRIVER).read_text(encoding="utf-8"))
        checks = next(ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CHECKS" for t in node.targets))
        self.assertEqual(len(checks), 42)
        self.assertEqual(len(set(checks)), 42)
        text = (ROOT / PROBE).read_text(encoding="utf-8")
        self.assertTrue(all('"' + name + '"' in text for name in checks))
        driver = (ROOT / DRIVER).read_text(encoding="utf-8")
        for token in ['"real_AEAD_or_Ed25519_executed": False', '"production_key_custody_qualified": False',
            '"atomic_product_publication_qualified": False', '"native_application_executed": False', '"product_complete": False']:
            self.assertIn(token, driver)


if __name__ == "__main__":
    unittest.main()
