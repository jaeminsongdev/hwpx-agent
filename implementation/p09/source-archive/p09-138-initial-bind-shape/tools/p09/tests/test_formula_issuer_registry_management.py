"""SQL22 management source contracts; actual SQL/issuer installation/native remain NOT_RUN."""
import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PARENT = "crates/revision-service/src/postgres/source_formula_policy/issuer_registry.rs"
SOURCE = "crates/revision-service/src/postgres/source_formula_policy/issuer_registry/management.rs"
ARCHIVE = "implementation/p09/source-archive/p09-138-pre-registry-management/source-preimages.v1.json"
DRIVER = "tools/p09/run_formula_issuer_registry_management.ps1"
LINT = "tools/p09/run_formula_issuer_registry_management_lint.ps1"


def preimage():
    doc = json.loads((ROOT / ARCHIVE).read_bytes())
    if doc["schema_version"] != "hwpx-agent.source-preimage/base64-v1" or len(doc["sources"]) != 1:
        raise ValueError("management_parent_inventory_drift")
    row = doc["sources"][0]
    raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
    expected = (22357, "ecb8cfb918b020469de369e1a1c5267bc68e74f236f388c4fcfb10aeb90a0e97")
    if row["path"] != PARENT or (row["bytes"], row["sha256"]) != expected or (len(raw), hashlib.sha256(raw).hexdigest()) != expected:
        raise ValueError("management_parent_whole_preimage_drift")
    return raw


class Contracts(unittest.TestCase):
    def setUp(self):
        self.code = (ROOT / SOURCE).read_text(encoding="utf-8")
        self.sql = (ROOT / "migrations/postgres/0022_p09_formula_issuer_registry.up.sql").read_text(encoding="utf-8")

    def test_parent_changed_only_by_management_module(self):
        raw = preimage()
        head = raw.split(b"\n", 1)[0] + b"\n"
        self.assertEqual(raw.count(head), 1)
        self.assertEqual(raw.replace(head, head + b"pub mod management;\n", 1), (ROOT / PARENT).read_bytes())

    def test_named_queries_match_sql22_arities_and_bind_order(self):
        for constant, function, arguments in [
            ("REGISTER_TRUST", "register_formula_issuer_trust_v1", 11),
            ("REGISTER_APPROVAL", "register_formula_approval_v1", 15),
            ("REVOKE_TRUST", "revoke_formula_issuer_trust_v1", 5),
            ("REVOKE_APPROVAL", "revoke_formula_approval_v1", 8),
        ]:
            declaration = re.search(r"CREATE FUNCTION hwpx_agent\." + function + r"\((.*?)\)\s*RETURNS", self.sql, re.S).group(1)
            query = re.search(r"const " + constant + r': &str = "(.*?)";', self.code, re.S).group(1)
            self.assertEqual(len(declaration.split(",")), arguments)
            self.assertEqual([int(n) for n in re.findall(r"\$(\d+)", query)], list(range(1, arguments + 1)))
            self.assertIn("hwpx_agent." + function, query)
        normalized = re.sub(r"\s+", "", self.code)
        root = "&context.tenant_id().as_uuid(),&r.project.as_uuid(),&context.subject().hex(),&r.version,&request.expected_generation,&r.issuer,&sql_integer(r.valid_from)?,&sql_integer(r.valid_until)?,&sql_integer(r.max_approval_lifetime)?,&r.artifact.as_uuid(),&r.digest.hex(),"
        approval = "&context.tenant_id().as_uuid(),&r.project.as_uuid(),&r.branch.as_uuid(),&context.subject().hex(),&r.document,&r.version,&request.expected_generation,&r.policy_version,&sql_integer(r.policy_generation)?,&revision,&sql_integer(request.source.head().generation())?,&r.trust_version,&sql_integer(r.trust_generation)?,&r.artifact.as_uuid(),&r.digest.hex(),"
        self.assertIn("query_one(REGISTER_TRUST,&[" + root + "])", normalized)
        self.assertIn("query_one(REGISTER_APPROVAL,&[" + approval + "])", normalized)

    def test_profiles_allow_only_two_writes_and_preserve_full_security_checks(self):
        body = self.code.split("fn admit_management_security", 1)[1].split("#[cfg(test)]", 1)[0]
        entries = re.findall(r'"hwpx_agent\.(\w+)\([^"\n]+\)",\s*(false|capability == RegistryManagementCapability::\w+),', body)
        self.assertEqual(len(entries), 9)
        for function, permission in entries:
            if function.startswith(("register_formula_issuer_trust", "revoke_formula_issuer_trust")):
                self.assertEqual(permission, "capability == RegistryManagementCapability::Trust")
            elif function.startswith(("register_formula_approval", "revoke_formula_approval")):
                self.assertEqual(permission, "capability == RegistryManagementCapability::Approval")
            else:
                self.assertEqual(permission, "false")
        for guard in ["relforcerowsecurity", "tenant_isolation", "WITH_CHECK_UNUSED_SENTINEL", "immutable", "prosecdef", "bounded_path", "no_public", "pg_has_role(c.relowner,'SET')", "pg_has_role(p.proowner,'SET')"]:
            if guard != "WITH_CHECK_UNUSED_SENTINEL":
                self.assertIn(guard, body)
        self.assertIn("SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER", body)
        self.assertIn("p.with_check='(tenant_id = hwpx_agent.current_tenant_id())'", body)
        self.assertNotRegex(self.code, r"(?im)^\s*(?:GRANT|INSERT|DELETE|UPDATE)\s")

    def test_fixed_context_no_lease_and_original_scoped_commit(self):
        for check in ["admit_schema22", "admit_read_policies", "admit_guarded_writes", "admit_form_policy_security", "admit_policy_security"]:
            self.assertIn(check + "(&mut client)?", self.code)
        self.assertIn("admit_management_security(&mut client, capability)?", self.code)
        self.assertIn('host("127.0.0.1")', self.code)
        self.assertIn("lease: None", self.code)
        self.assertIn("self.inner.authorize_context(context)?", self.code)
        self.assertEqual(self.code.count("IsolationLevel::ReadCommitted"), 4)
        self.assertEqual(self.code.count("self.authorize(context, RegistryManagementCapability::"), 4)
        original = (ROOT / "crates/revision-service/src/postgres.rs").read_text(encoding="utf-8")
        self.assertIn("RevisionError::CommitOutcomeUnknown", original)
        self.assertNotRegex(self.code, r"\.commit\(|\.reconnect\(|for attempt|derive\([^)]*Deserialize")

    def test_requests_and_acknowledgements_are_checked_not_trust_records(self):
        self.assertIn("expected.checked_add(1)", self.code)
        self.assertIn("if sql_integer(proposed)? != next", self.code)
        self.assertEqual(self.code.count("self.record.creator != context.subject()"), 2)
        self.assertIn("postgres::types::Type::INT8", self.code)
        self.assertIn("postgres::types::Type::VOID", self.code)
        self.assertIn("expected.checked_add(1) != Some(actual)", self.code)
        self.assertIn("NOT authenticated row readback", self.code)
        self.assertNotRegex(self.code, r"pub (?:action|tenant|project|version|generation|actor):")

    def test_revocation_has_no_live_head_or_root_requirement(self):
        req = self.code.split("pub struct FormulaApprovalRevocation {", 1)[1].split("impl FormulaApprovalRevocation", 1)[0]
        self.assertNotRegex(req, "RevisionHead|source|trust_generation|trust_version")
        body = self.code.split("pub fn revoke_approval(", 1)[1].split("macro_rules!", 1)[0]
        self.assertNotRegex(body, "read_trust|read_approval|revision_id|read_source_formula")
        self.assertIn("bytes.len() > 128", self.code)
        self.assertIn("!generation(expected_generation)", self.code)
        self.assertIn("revocation_survives_head_root_absence_and_exhausted_generation", self.code)

    def test_debug_and_runtime_counterexamples_are_bounded(self):
        self.assertIn('"(<redacted>)"', self.code)
        self.assertEqual(len(re.findall(r"#\[test\]", self.code)), 8)
        for name in ["trust_registration_denies_other_tenant_and_creator", "scalar_acknowledgement_rejects_wrong_generation", "approval_registration_binds_current_policy_and_fixed_creator"]:
            self.assertIn(name, self.code)
        self.assertNotRegex(self.code, r"println!|eprintln!|private_key|password\(\"|serde_json")

    def test_runners_preserve_old_executables_and_resource_thresholds(self):
        for path in [DRIVER, LINT]:
            text = (ROOT / path).read_text(encoding="utf-8")
            for guard in ["$protectedPins.Count -ne 27", "$sources.Count -ne 813", "-Count 1", "'BelowNormal'", "system_cpu_percent -ge 85", "available_ram_mib -lt 4096", "Get-P09ResourceDecision", "new_receipt_required", "source_drift", "protected_executable_drift"]:
                self.assertIn(guard, text)
            self.assertIn("p09-137-formula-issuer-registry-reads.source-progress.v1.json", text)
            self.assertIn(ARCHIVE, text)
            self.assertNotRegex(text, r"HwpObject|Start-Process.*Hangul|Remove-Item|--nocapture")


if __name__ == "__main__":
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps({"state": "PASS_SOURCE_ONLY_NOT_ACTUAL_SQL_OR_GATE" if result.wasSuccessful() else "FAIL_CLOSED",
        "tests": result.testsRun, "failures": [t._testMethodName for t, _ in result.failures],
        "errors": [t._testMethodName for t, _ in result.errors], "P09_gate": "OPEN"}))
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
