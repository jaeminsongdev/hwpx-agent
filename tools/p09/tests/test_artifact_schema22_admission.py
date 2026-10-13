"""P142 new constructor source guards; not live DB/crypto integration evidence."""
import base64
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PARENT = "crates/artifact-service/src/store/postgres_repository.rs"
SOURCE = "crates/artifact-service/src/store/postgres_repository/schema22.rs"
ARCHIVE = "implementation/p09/source-archive/p09-142-pre-artifact-schema22/source-preimages.v1.json"


class Contracts(unittest.TestCase):
    def test_original_constructor_and_operations_exact_except_module_declaration(self):
        row = json.loads((ROOT / ARCHIVE).read_text(encoding="utf-8"))["files"][0]
        original = base64.b64decode("".join(row["base64_chunks"]), validate=True).decode("utf-8").replace("\r\n", "\n")
        current = (ROOT / PARENT).read_text(encoding="utf-8")
        self.assertEqual(current, original.replace("pub mod source_formula_policy;\n", "pub mod source_formula_policy;\npub mod schema22;\n"))

    def test_full_original_role_RLS_and_privilege_admission_remains_required(self):
        text = (ROOT / SOURCE).read_text(encoding="utf-8")
        self.assertIn("Self::connect_diagnosed(config, tenant)?", text)
        self.assertLess(text.index("Self::connect_diagnosed(config, tenant)?"), text.index("verify_schema22(&mut client)"))
        self.assertLess(text.index("verify_schema22(&mut client)"), text.index("Ok(repository)"))
        self.assertNotIn("GRANT", text)
        self.assertNotIn("DISABLE TRIGGER", text)

    def test_exact_version_and_digest_no_prefix_or_future_schema_acceptance(self):
        text = (ROOT / SOURCE).read_text(encoding="utf-8")
        for marker in ["rows.len() != 22", "ORDER BY version LIMIT 23", "MIGRATIONS.iter().chain(ADDITIONAL.iter())",
            "ContentDigest::of(source).hex()", "i64::try_from(index + 1)"]:
            self.assertIn(marker, text)
        self.assertEqual(text.count('migration!("00'), 5)

    def test_closed_diagnostics_no_key_grant_retry_or_private_outputs(self):
        text = (ROOT / SOURCE).read_text(encoding="utf-8")
        self.assertIn("PostgresConnectStage::Migrations", text)
        self.assertNotRegex(text, r"println!|eprintln!|password|INSERT |UPDATE |DELETE |retry\s*\(")
        self.assertIn("try_lock()", text)
        self.assertIn("verify_nonreplication_role(&mut client)", text)
        self.assertIn("SELECT rolreplication FROM pg_roles WHERE rolname=current_user", text)
        self.assertIn("PostgresConnectStage::Role", text)


if __name__ == "__main__":
    unittest.main()
