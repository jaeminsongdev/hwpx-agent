"""SQL22 read bridge source guards, not SQL/RLS runtime or production key qualification."""
import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = "implementation/p09/source-archive/p09-137-pre-registry-reads/parent-preimages.v1.json"
REVISION = "crates/revision-service/src/postgres/source_formula_policy/issuer_registry.rs"
ARTIFACT = "crates/artifact-service/src/store/postgres_repository/source_formula_policy/issuer_registry.rs"
PRODUCT = "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/registry.rs"
WIRE = "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/registry/trust_wire.rs"
TEST = "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/registry.rs"
DRIVER = "tools/p09/run_formula_issuer_registry_reads.ps1"
UP = "migrations/postgres/0022_p09_formula_issuer_registry.up.sql"
PARENT_PINS = {
    "crates/revision-service/src/postgres/source_formula_policy.rs": (19635, "c5a5abf49c5912444fa3e71f0ef999687f2613c8ef423801c349ac2547c48c7d"),
    "crates/artifact-service/src/store/postgres_repository/source_formula_policy.rs": (3108, "25a2f76dec6e187c966742898de6a3be614cf3085820649c8e5f42595ab498c2"),
    "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer.rs": (10115, "82ea6bd2482d2bf5bff0a2a469a867e7126386e9b8aabec60080adadc4dbdcbd"),
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer.rs": (44624, "4d979a48068dcd29f2141e1fb641e9fa2748430ae6ad7d2c5b08f44e07baf328"),
}


def preimages():
    doc = json.loads((ROOT / ARCHIVE).read_bytes())
    if doc["schema_version"] != "hwpx-agent.source-preimage/base64-v1":
        raise ValueError("wrong_preimage_schema")
    result = {}
    for row in doc["parents"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        expected = PARENT_PINS[row["path"]]
        if (len(raw), hashlib.sha256(raw).hexdigest()) != expected or (row["bytes"], row["sha256"]) != expected or row["path"] in result:
            raise ValueError("parent_preimage_not_exact")
        result[row["path"]] = raw
    if set(result) != set(PARENT_PINS):
        raise ValueError("parent_preimage_coverage_drift")
    return result


class Contracts(unittest.TestCase):
    def text(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_whole_parent_preimages_and_only_declared_modules(self):
        for path, before in preimages().items():
            if path.endswith("formula_policy_issuer.rs"):
                old = b"mod corpus;\n"
                new = old + b'#[path = "formula_policy_issuer/registry.rs"]\nmod registry;\n'
            else:
                old = b"pub mod revocation;\n" if "/revision-service/" in path else b"use super::*;\n" if "/artifact-service/" in path else b"pub mod product;\n"
                new = old + (b"pub mod issuer_registry;\n" if "/product-cli/" not in path else b"pub mod registry;\n")
            self.assertEqual(before.count(old), 1)
            self.assertEqual(before.replace(old, new), (ROOT / path).read_bytes())

    def test_exact_schema22_and_all_original_admission_helpers(self):
        r, a = self.text(REVISION), self.text(ARTIFACT)
        for code in (r, a):
            self.assertIn("LIMIT 23", code)
            self.assertIn("rows.len() != 22", code)
            self.assertIn("0022_p09_formula_issuer_registry.up.sql", code)
            self.assertIn('host("127.0.0.1")', code)
            self.assertIn("rolreplication", code)
        for check in ["admit_read_policies", "admit_guarded_writes", "admit_form_policy_security", "admit_policy_security", "admit_registry_security"]:
            self.assertIn(check + "(&mut client)?", r)
        for check in ["verify_role", "verify_policies", "verify_privileges"]:
            self.assertIn(check + "(&mut client)?", a)

    def test_selected_columns_are_sql22_columns_not_guessed_names(self):
        r, sql = self.text(REVISION), self.text(UP)
        for name, table in [("READ_TRUST", "formula_issuer_trust_versions"), ("READ_APPROVAL", "formula_approval_versions")]:
            query = re.search(r"const " + name + r': &str = "SELECT (.*?)FROM ', r, re.S).group(1)
            definition = re.search(r"CREATE TABLE hwpx_agent\." + table + r" \((.*?)\n\);", sql, re.S).group(1)
            columns = [c.strip().split("::")[0] for c in query.split(",")]
            for column in columns:
                self.assertRegex(definition, r"\b" + column + r"\s+(?:uuid|bigint|text|character)\b")
        self.assertIn("row.len() != 11", r)
        self.assertIn("row.len() != 13", r)

    def test_fixed_subject_repeatable_read_bounds_and_no_retry(self):
        r = self.text(REVISION)
        self.assertEqual(r.count("self.policy.inner.authorize_context(context)?"), 2)
        self.assertEqual(r.count("IsolationLevel::RepeatableRead"), 2)
        self.assertIn("context.subject().hex()", r)
        self.assertIn("record.validate_for(context, project)?", r)
        self.assertIn("record.validate_for(context, request)?", r)
        self.assertIn("policy_version.is_nil()", r)
        self.assertIn("self.valid_until > i64::MAX as u64", r)
        self.assertNotRegex(r, r"(?i)retry|reconnect|unwrap\(|expect\(")

    def test_registry_function_and_table_least_privilege(self):
        r, sql = self.text(REVISION), self.text(UP)
        signatures = re.findall(r'"hwpx_agent\.(\w+)_v1\([^"\n]*\)"\s*,\s*(true|false)', r)
        self.assertEqual(len(signatures), 9)
        self.assertEqual({name for name, flag in signatures if flag == "true"}, {"read_formula_issuer_trust", "read_formula_approval"})
        self.assertEqual({name + "_v1" for name, _ in signatures}, set(re.findall(r"CREATE FUNCTION hwpx_agent\.(\w+)\(", sql)))
        for field in ["relrowsecurity", "relforcerowsecurity", "owner_role", "direct", "policy", "immutable", "prosecdef", "bounded_path", "no_public"]:
            self.assertIn('"' + field + '"', r)
        self.assertIn("pg_has_role(p.proowner,'SET')", r)
        self.assertIn("SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER", r)

    def test_root_payload_is_strict_object_with_bounded_keys_and_whole_metadata(self):
        w = self.text(WIRE)
        self.assertEqual(w.count("#[serde(deny_unknown_fields)]"), 2)
        self.assertIn("d.deserialize_map", w)
        self.assertIn("object_only(d).map(Self)", w)
        self.assertIn("decoder.end()", w)
        self.assertIn("p.keys.len() > 8", w)
        self.assertIn("k.public_key_hex.len() != 64", w)
        self.assertIn("FormulaIssuerKey::new", w)
        self.assertIn("FormulaIssuerTrust::new", w)
        for field in ["tenant", "project", "trust_version", "generation", "issuer", "valid_from", "valid_until", "max_approval_lifetime"]:
            self.assertIn("p." + field, w)
        self.assertNotIn("serde_json::Value", w)

    def test_original_artifact_signature_and_live_trust_checks_not_replaced(self):
        p, t = self.text(PRODUCT), self.text(TEST)
        for check in ["get_descriptor", ".download", "ContentDigest::of(&raw)", "AuthScope::DocumentRead", "ValidationState::Verified", "StorageState::Available", "d.quarantine_reason.is_some()", "row.validate_for", "after < before", "live(&row, after)?"]:
            self.assertIn(check, p)
        self.assertIn("row.trust_version != root.version", p)
        self.assertIn("row.trust_generation != root.generation", p)
        self.assertEqual(t.count("#[test]"), 7)
        for check in ["prepare_formula_with_issuer", "with_verified_bytes", "require_current_product_route", "no_publication", "quarantine", "same_generation", "signature_hex"]:
            self.assertIn(check, t)

    def test_resource_guards_immutable_receipts_and_old_executables(self):
        d = self.text(DRIVER)
        for check in ["$protectedPins.Count -ne 21", "$sources.Count -lt 808", "current_executable_already_exists", "new_receipt_required", "BelowNormal", "-Count 1", "'--jobs','1'", "--test-threads=1", "$before.system_cpu_percent -ge 85", "$before.available_ram_mib -lt 4096", "Get-P09ResourceDecision", "$proc.Kill($true)", "$sourceExact", "$oldExact"]:
            self.assertIn(check, d)
        self.assertEqual(d.count("$selection=switch($Suite)"), 1)
        self.assertIn("-p137-", d)
        self.assertNotIn("form_stored_provider-9df9", d)


if __name__ == "__main__":
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps({"executed": result.testsRun, "passed": result.testsRun-len(result.failures)-len(result.errors),
        "failed_names": [t._testMethodName for t, _ in result.failures], "error_names": [t._testMethodName for t, _ in result.errors],
        "actual_sql_executed": False, "P09_gate": "OPEN"}, separators=(",", ":")))
    raise SystemExit(0 if result.wasSuccessful() else 1)
