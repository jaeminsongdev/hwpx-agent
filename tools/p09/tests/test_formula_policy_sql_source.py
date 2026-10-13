"""SQL21/Rust source contracts only. Does not execute SQL, connect, or qualify issuer/native."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SQL20 = "migrations/postgres/0020_p09_source_form_policy.up.sql"
SQL21 = "migrations/postgres/0021_p09_source_formula_policy.up.sql"
REV20 = "crates/revision-service/src/postgres/source_form_policy.rs"
REV21 = "crates/revision-service/src/postgres/source_formula_policy.rs"
ART21 = "crates/artifact-service/src/store/postgres_repository/source_formula_policy.rs"
REG21 = "crates/revision-service/src/postgres/source_formula_policy/registration.rs"
BRIDGE = "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/postgres.rs"
PREIMAGE = "implementation/p09/source-archive/p09-117-pre-formula-policy-sql/"
PARENTS = {"crates/revision-service/src/postgres.rs": "pub mod source_formula_policy;\n",
           "crates/artifact-service/src/store/postgres_repository.rs": "pub mod source_formula_policy;\n",
           "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas.rs": "pub mod postgres;\n"}
def text(path):
    return (ROOT/path).read_text(encoding="utf-8")
def tokens(value):
    return re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|\d+|[^\s]', value)
def function(value, name, next_name):
    return value[value.index("fn "+name+"("):value.index("fn "+next_name+"(")]

class FormulaPolicySqlSourceTests(unittest.TestCase):
    def test_whole_sql_derivative_keeps_every_original_guard_in_separate_domain(self):
        expected = text(SQL20).replace("source_form_policy", "source_formula_policy").replace("FORM_POLICY_", "FORMULA_POLICY_")
        expected = expected.replace("version = 19 AND migration_name = 'p09.authorized_full_ir_intent_v1'", "version = 20 AND migration_name = 'p09.source_form_policy_v1'")
        expected = expected.replace("WHERE version >= 20", "WHERE version >= 21").replace("REQUIRES_SCHEMA_19", "REQUIRES_SCHEMA_20")
        expected = expected.replace("VALUES(20,'p09.source_formula_policy_v1'", "VALUES(21,'p09.source_formula_policy_v1'")
        expected = expected.replace("application/vnd.hwpx-agent.source-form-policy+json", "application/vnd.hwpx-agent.source-table-formula-policy+json")
        self.assertEqual(text(SQL21), "-- P09-117: separate FORMULA policy DATA domain; not signed issuer/execution qualification.\n"+expected)

    def test_old_form_security_admission_is_kept_whole_not_replaced_with_formula_checks(self):
        old = function(text(REV20), "admit_policy_security", "decode_row").replace("fn admit_policy_security(", "fn admit_form_policy_security(")
        new = function(text(REV21), "admit_form_policy_security", "decode_row")
        self.assertEqual(tokens(old), tokens(new))
        self.assertIn("admit_form_policy_security(&mut client)?", text(REV21))
        self.assertIn("admit_policy_security(&mut client)?", text(REV21))

    def test_formula_security_admission_retains_original_role_rls_privileges_and_function_checks(self):
        old = function(text(REV20), "admit_policy_security", "decode_row").replace("source_form_policy", "source_formula_policy")
        new = function(text(REV21), "admit_policy_security", "admit_form_policy_security")
        self.assertEqual(tokens(old), tokens(new))

    def test_three_parents_only_add_declared_modules_exact_whole_preimages(self):
        for path, module in PARENTS.items():
            raw = (ROOT/path).read_bytes()
            self.assertEqual(raw.count(module.encode()), 1)
            self.assertEqual(raw.replace(module.encode(), b"", 1), (ROOT/(PREIMAGE+path)).read_bytes())

    def test_exact_schema21_uses_all_21_fingerprints_and_refuses_future_rows(self):
        for path in [REV21,ART21]:
            value = text(path)
            self.assertIn("LIMIT 22",value)
            self.assertIn("rows.len() != 21",value)
            self.assertIn("ContentDigest::of(migration).hex()",value)
            self.assertIn("0020_p09_source_form_policy.up.sql",value)
            self.assertIn("0021_p09_source_formula_policy.up.sql",value)
        self.assertIn("chain([MIGRATION20, MIGRATION21].iter())",text(REV21))
        self.assertIn("const ADDITIONS: [&[u8]; 4]",text(ART21))

    def test_bounded_subject_fixed_transaction_and_original_revision_service_reused(self):
        value = text(REV21)
        self.assertIn("self.inner.authorize_context(context)?",value)
        self.assertIn("IsolationLevel::RepeatableRead",value)
        self.assertIn("self.inner.clone()",value)
        for path in [REV21,ART21]:
            value = text(path)
            for clause in ['host("127.0.0.1")','connect_timeout(Duration::from_secs(3))','statement_timeout=5000','lock_timeout=1000','transaction_timeout=10000','search_path=pg_catalog']:
                self.assertIn(clause,value)

    def test_field_media_only_evidence_and_full_source_policy_acl_state_checks(self):
        value = text(SQL21)
        self.assertNotIn("application/vnd.hwpx-agent.source-form-policy+json",value)
        for clause in ["policy.artifact_kind='evidence'","result.artifact_kind='result'","result_acl.can_read","policy_acl.can_read","policy_acl.can_manage","policy.validation_state='verified'","policy.quarantine_reason_code IS NULL","policy.size_bytes BETWEEN 1 AND 1048576"]:
            self.assertIn(clause,value)

    def test_latest_revoked_policy_never_falls_back_and_source_head_must_match(self):
        value = text(SQL21)
        self.assertIn("ORDER BY generation DESC LIMIT 1",value)
        self.assertIn("source_formula_policy_revocations",value)
        self.assertIn("ROW(v_head,v_generation) IS DISTINCT FROM ROW(p_revision,p_head_generation)",value)
        self.assertIn("FORMULA_POLICY_NOT_CURRENT",value)

    def test_registration_original_transaction_source_generation_cas_readback_and_no_retry(self):
        value = text(REG21)
        for clause in ["IsolationLevel::ReadCommitted","register_source_formula_policy_v1","decode_row(&row,context,s)","record.source_result!=request.source.result","record.creator!=context.subject()","record.policy_digest!=request.digest"]:
            self.assertIn(clause,value)
        self.assertIn("FOR UPDATE",text(SQL21))
        self.assertIn("v_generation IS DISTINCT FROM p_expected_generation",text(SQL21))
        self.assertNotIn("loop {",value)

    def test_no_plaintext_policy_values_or_caller_approval_in_sql_metadata(self):
        value = text(SQL21)
        table=value[value.index("CREATE TABLE"):value.index("CREATE FUNCTION")]
        for forbidden in ["allow_recalculation","jsonb","plaintext","caller_approved"]:
            self.assertNotIn(forbidden,table)
        self.assertIn("policy_artifact_sha256",table)
        self.assertIn("source_package_sha256",table)

    def test_formula_bridge_uses_private_original_scope_and_only_new_formula_repository(self):
        value = text(BRIDGE)
        self.assertIn("impl FormulaPolicyRepository for PostgresFormulaPolicyProvider",value)
        self.assertIn("SourceFormulaPolicyReadRequest::new",value)
        self.assertIn("scope.tenant(), scope.subject()",value)
        self.assertIn("scope.head()",value)
        self.assertNotIn("serde_json",value)

    def test_artifact_connection_has_unambiguous_formula_specific_name(self):
        value = text(ART21)
        self.assertIn("pub fn connect_source_formula_policy_schema21",value)
        self.assertNotIn("pub fn connect_source_form_policy_schema21",value)

    def test_new_rollback_requires_explicit_gate_empty_history_latest_schema(self):
        value = text("migrations/postgres/0021_p09_source_formula_policy.down.sql")
        for clause in ["allow_destructive_rollback","IS DISTINCT FROM 'on'","version>21","version=21","FORMULA_POLICY_ROLLBACK_REFUSES_DATA_LOSS","FROM hwpx_agent.source_formula_policy_versions","FROM hwpx_agent.source_formula_policy_revocations"]:
            self.assertIn(clause,value)
        self.assertNotIn("DROP TABLE hwpx_agent.source_form_policy_",value)
        self.assertNotIn("CASCADE",value)

if __name__ == "__main__":
    unittest.main()
