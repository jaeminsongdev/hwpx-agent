"""SQL22 source contracts only: not a PostgreSQL parser, live SQL, issuer or Gate test."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UP = "migrations/postgres/0022_p09_formula_issuer_registry.up.sql"
DOWN = "migrations/postgres/0022_p09_formula_issuer_registry.down.sql"
TABLES = ("formula_issuer_trust_versions", "formula_issuer_trust_revocations", "formula_approval_versions", "formula_approval_revocations")


def functions(source):
    pattern = r"CREATE FUNCTION hwpx_agent\.(\w+)\((.*?)\)\s*(RETURNS.*?)AS \$\$(.*?)\$\$;"
    rows = re.findall(pattern, source, re.S)
    if len(rows) != 9 or len({name for name, *_ in rows}) != 9:
        raise ValueError("SQL22_function_inventory_drift")
    return {name: {"args": args, "header": header, "body": body} for name, args, header, body in rows}


class SourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = (ROOT / UP).read_text(encoding="utf-8")
        cls.down = (ROOT / DOWN).read_text(encoding="utf-8")
        cls.fn = functions(cls.up)

    def body(self, name):
        return self.fn[name + "_v1"]["body"]

    def test_exact_schema_upgrade_digest_and_no_implicit_grants(self):
        self.assertIn("version=21 AND migration_name='p09.source_formula_policy_v1'", self.up)
        self.assertIn("WHERE version>=22", self.up)
        self.assertIn("!~ '^[0-9a-f]{64}$'", self.up)
        self.assertIn("VALUES(22,'p09.formula_issuer_registry_v1'", self.up)
        self.assertNotRegex(self.up, r"\bGRANT\b|\bALTER ROLE\b|\bCREATE ROLE\b")
        self.assertTrue(self.up.endswith("COMMIT;\n"))

    def test_four_append_only_tenant_tables_and_no_plaintext_payload(self):
        self.assertEqual(set(re.findall(r"CREATE TABLE hwpx_agent\.(\w+)", self.up)), set(TABLES))
        for table in TABLES:
            for clause in ("ENABLE ROW LEVEL SECURITY", "FORCE ROW LEVEL SECURITY"):
                self.assertIn(f"ALTER TABLE hwpx_agent.{table} {clause};", self.up)
            self.assertIn(f"CREATE POLICY tenant_isolation ON hwpx_agent.{table}", self.up)
            self.assertIn(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE", self.up)
        self.assertEqual(self.up.count("WITH CHECK(tenant_id=hwpx_agent.current_tenant_id())"), 4)
        definitions = "\n".join(re.findall(r"CREATE TABLE hwpx_agent\.\w+ \((.*?)\n\);", self.up, re.S))
        self.assertNotRegex(definitions, r"\b\w+\s+(?:jsonb?|bytea)\b|\bprivate_key\b|\bpassword\b")
        self.assertEqual(self.up.count("FOREIGN KEY"), 9)
        self.assertEqual(self.up.count("ON DELETE RESTRICT"), 9)

    def test_all_function_signatures_revoke_public_and_bound_search_path(self):
        revoked = self.up.split("REVOKE ALL ON FUNCTION", 1)[1].split("FROM PUBLIC;", 1)[0]
        dropped = set(re.findall(r"DROP FUNCTION hwpx_agent\.(\w+)\((.*?)\);", self.down))
        for name, row in self.fn.items():
            self.assertIn("SECURITY DEFINER", row["header"])
            self.assertIn("search_path=pg_catalog,hwpx_agent", row["header"])
            types = ",".join(re.sub(r"\(64\)", "", arg.strip().split(" ", 1)[1]) for arg in row["args"].split(","))
            self.assertIn(f"hwpx_agent.{name}({types})", revoked)
            self.assertIn((name, types), dropped)
        self.assertEqual(len(dropped), 9)

    def test_fixed_writer_context_project_then_membership_lock_and_owner_only_trust(self):
        body = self.body("lock_formula_issuer_scope")
        self.assertIn("require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,true)", body)
        self.assertLess(body.index("FOR UPDATE"), body.index("FOR SHARE OF acl,tenant"))
        for value in ("p_owner IS NULL", "acl.subject_sha256=p_subject", "project.state='active'", "tenant.state='active'",
                      "acl.role='owner' OR (NOT p_owner AND acl.role='editor')"):
            self.assertIn(value, body)
        self.assertIn("lock_formula_issuer_scope_v1(p_tenant,p_project,p_subject,true)", self.body("require_formula_issuer_owner"))
        for name in ("register_formula_issuer_trust", "revoke_formula_issuer_trust"):
            self.assertIn("require_formula_issuer_owner_v1", self.body(name))
        for name in ("register_formula_approval", "revoke_formula_approval"):
            body = self.body(name)
            self.assertIn("lock_formula_issuer_scope_v1(p_tenant,p_project,p_subject,false)", body)
            self.assertLess(body.index("hwpx_agent.projects"), body.index("hwpx_agent.branches"))

    def test_artifact_domains_acl_integrity_and_bounds_do_not_verify_signatures(self):
        body = self.body("require_formula_issuer_artifact")
        for value in ("p_trust IS NULL", "p_manage IS NULL", "a.content_sha256=p_digest", "a.artifact_kind='evidence'",
                      "a.service_metadata_version=1", "a.storage_state='available'", "a.validation_state='verified'",
                      "a.quarantine_reason_code IS NULL", "acl.subject_sha256=p_subject", "acl.can_read",
                      "NOT p_manage OR acl.can_manage", "THEN 32768 ELSE 16384", "source-formula-issuer-trust+json",
                      "source-formula-approval+json"):
            self.assertIn(value, body)
        self.assertNotIn("signature_verified", self.up)
        self.assertNotIn("approval_allowed", self.up)

    def test_cas_generation_scope_indexes_and_overflow_denial(self):
        for name, table in (("register_formula_issuer_trust", "formula_issuer_trust_versions"), ("register_formula_approval", "formula_approval_versions")):
            body = self.body(name)
            self.assertIn(f"coalesce(max(generation),0) INTO v_generation FROM hwpx_agent.{table}", body)
            self.assertIn("v_generation IS DISTINCT FROM p_expected_generation OR v_generation=9223372036854775807", body)
            self.assertIn("RETURN v_generation+1", body)
        for value in ("UNIQUE(tenant_id,project_id,generation)", "UNIQUE(tenant_id,project_id,policy_version_id,generation)",
                      "UNIQUE(tenant_id,project_id,trust_artifact_id)", "UNIQUE(tenant_id,project_id,approval_artifact_id)",
                      "max_approval_lifetime BETWEEN 1 AND 86400", "valid_until>valid_from"):
            self.assertIn(value, self.up)

    def test_latest_root_never_falls_back_after_expiry_revocation_or_acl_denial(self):
        body = self.body("read_formula_issuer_trust")
        self.assertIn("require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,false)", body)
        self.assertIn("ORDER BY generation DESC LIMIT 1", body)
        self.assertIn("clock_timestamp()", body)
        self.assertIn("v_now<v_trust.valid_from OR v_now>=v_trust.valid_until", body)
        self.assertIn("trust_version_id=v_trust.trust_version_id", body)
        self.assertIn("v_trust.trust_artifact_sha256,true,false", body)
        self.assertLess(body.index("ORDER BY generation"), body.index("formula_issuer_trust_revocations"))
        self.assertNotRegex(body, r"\bLOOP\b|\bCOALESCE\b|\bEXCEPTION WHEN\b")

    def test_publish_binds_current_policy_head_root_and_no_artifact_alias(self):
        body = self.body("register_formula_approval")
        self.assertIn("p_document,p_revision,p_head_generation)", body)
        self.assertIn("ROW(v_policy.policy_version_id,v_policy.generation) IS DISTINCT FROM ROW(p_policy_version,p_policy_generation)", body)
        self.assertIn("ROW(v_trust.trust_version_id,v_trust.generation) IS DISTINCT FROM ROW(p_trust_version,p_trust_generation)", body)
        self.assertIn("p_artifact=v_policy.policy_artifact_id OR p_artifact=v_policy.source_result_artifact_id OR p_artifact=v_trust.trust_artifact_id", body)
        self.assertIn("p_artifact,p_digest,false,true", body)
        self.assertLess(body.index("FOR UPDATE"), body.index("read_source_formula_policy_v1"))
        self.assertLess(body.index("read_formula_issuer_trust_v1"), body.index("INSERT INTO"))

    def test_read_approval_rechecks_latest_policy_root_revocation_acl_and_all_bindings(self):
        body = self.body("read_formula_approval")
        for value in ("read_source_formula_policy_v1", "p_policy_version,p_policy_generation", "read_formula_issuer_trust_v1",
                      "v_approval.branch_id,v_approval.document_id,v_approval.policy_generation,v_approval.trust_version_id,v_approval.trust_generation",
                      "p_branch,p_document,p_policy_generation,v_trust.trust_version_id,v_trust.generation",
                      "ORDER BY generation DESC LIMIT 1", "approval_version_id=v_approval.approval_version_id",
                      "v_approval.approval_artifact_sha256,false,false"):
            self.assertIn(value, body)
        self.assertLess(body.index("ORDER BY generation"), body.index("formula_approval_revocations"))
        self.assertNotRegex(body, r"\bLOOP\b|\bEXCEPTION WHEN\b")

    def test_administrative_revocation_uses_latest_cas_without_current_head_requirement(self):
        for name, domain in (("revoke_formula_issuer_trust", "trust"), ("revoke_formula_approval", "approval")):
            body = self.body(name)
            self.assertIn("ORDER BY generation DESC LIMIT 1", body)
            self.assertIn("p_version,p_expected_generation", body)
            self.assertIn(f"INSERT INTO hwpx_agent.formula_{'issuer_trust' if domain == 'trust' else 'approval'}_revocations", body)
            self.assertNotIn("read_source_formula_policy_v1", body)
            self.assertNotIn("read_formula_issuer_trust_v1", body)

    def test_empty_history_only_explicit_latest_rollback_and_no_cascade(self):
        for value in ("allow_destructive_rollback", "IS DISTINCT FROM 'on'", "WHERE version>22", "version=22 AND migration_name='p09.formula_issuer_registry_v1'",
                      "FORMULA_ISSUER_ROLLBACK_REFUSES_DATA_LOSS", "DELETE FROM hwpx_agent.schema_versions WHERE version=22"):
            self.assertIn(value, self.down)
        for table in TABLES:
            self.assertIn(f"EXISTS(SELECT 1 FROM hwpx_agent.{table})", self.down)
        sql = re.sub(r"--[^\n]*", "", self.down)
        self.assertNotRegex(sql, r"\bCASCADE\b|\bTRUNCATE\b")
        self.assertLess(self.down.index("FORMULA_ISSUER_ROLLBACK_REFUSES_DATA_LOSS"), self.down.index("DROP FUNCTION"))
        self.assertNotIn("DROP TABLE hwpx_agent.source_formula_policy", self.down)

    def test_function_inventory_denies_missing_or_duplicate_declaration(self):
        with self.assertRaises(ValueError):
            functions(self.up.replace("CREATE FUNCTION", "NOT_A_FUNCTION", 1))
        with self.assertRaises(ValueError):
            functions(self.up + self.up)


if __name__ == "__main__":
    unittest.main()
