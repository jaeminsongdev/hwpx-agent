"""Issuer AEAD/signing/write/readback contracts; not actual SQL/custody/native qualification."""
import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PINS = {
  "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/registry.rs": [
    7657,
    "dc164b1392ade66ce77d7421dae4835c3b26a2011e743625d17f601aa9fb0578"
  ],
  "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/provider.rs": [
    8856,
    "6d7aadaacfbca78a4e0ffb118b82d13435ddbd387faff549331ae28b25197c10"
  ],
  "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer.rs": [
    44684,
    "ea6461f312787a4e2ed313b90a4c84b2f2f84562ae7942a3474230754a70d385"
  ],
  "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer.rs": [
    10133,
    "c8ccf559cbaa3b05a8f0432b2e0364a44cb28577fe9cd593867e56562f3074ca"
  ],
  "crates/revision-service/src/postgres/source_formula_policy/issuer_registry/management.rs": [
    31783,
    "4458af3359b12c9a88a148b01580d77d9e3df058318e564d4b985bae474ad2c1"
  ]
}
ARCHIVE = "implementation/p09/source-archive/p09-139-pre-registry-provisioning/source-preimages.v1.json"
SOURCE = "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/registry/provision.rs"
TEST = "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/provision.rs"
MANAGEMENT = "crates/revision-service/src/postgres/source_formula_policy/issuer_registry/management.rs"
ISSUER = "crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer.rs"
DRIVER = "tools/p09/run_formula_issuer_registry_provision.ps1"
LINT = "tools/p09/run_formula_issuer_registry_provision_lint.ps1"

def preimages():
    doc = json.loads((ROOT / ARCHIVE).read_bytes())
    if doc["schema_version"] != "hwpx-agent.source-preimage/base64-v1" or len(doc["sources"]) != 5:
        raise ValueError("provision_parent_inventory_drift")
    result = {}
    for row in doc["sources"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        expected = PINS[row["path"]]
        if [len(raw), hashlib.sha256(raw).hexdigest()] != expected or [row["bytes"], row["sha256"]] != expected or row["path"] in result:
            raise ValueError("provision_whole_parent_preimage_drift")
        result[row["path"]] = raw
    if set(result) != set(PINS):
        raise ValueError("provision_parent_coverage_drift")
    return result

class Contracts(unittest.TestCase):
    def setUp(self):
        self.code = (ROOT / SOURCE).read_text(encoding="utf-8")
        self.management = (ROOT / MANAGEMENT).read_text(encoding="utf-8")
        self.issuer = (ROOT / ISSUER).read_text(encoding="utf-8")
        self.test = (ROOT / TEST).read_text(encoding="utf-8")

    def test_whole_parents_only_declared_changes(self):
        for path, old in preimages().items():
            new = (ROOT / path).read_bytes()
            if path == MANAGEMENT:
                start = new.index(b"    /// Preflight only, not a lease")
                end = new.index(b"    /// # Errors\n    /// SQL checks owner/CAS", start)
                self.assertEqual(new[:start] + new[end:], old)
            elif path == ISSUER:
                start = new.index(b"    /// Internal pre-sign admission")
                end = new.index(b"    /// Wraps externally produced signature", start)
                self.assertEqual(new[:start] + new[end:], old)
            else:
                anchor, replacement = (b"mod trust_wire;\n", b"mod trust_wire;\npub mod provision;\n") if path.endswith("/registry.rs") else (b"fn validate_claims(\n", b"pub(super) fn validate_claims(\n") if path.endswith("/provider.rs") else (b"mod registry;\n", b'mod registry;\n#[path = "formula_policy_issuer/provision.rs"]\nmod provision;\n')
                self.assertEqual(old.count(anchor), 1)
                self.assertEqual(old.replace(anchor, replacement), new)

    def test_project_role_preflight_preserves_original_write_time_authority(self):
        body = self.management.split("pub fn check_project_role", 1)[1].split("pub fn register_trust", 1)[0]
        for marker in ["self.authorize(context, capability)?", "context.tenant_id()", "context.subject().hex()", "project.as_uuid()", "IsolationLevel::ReadCommitted", "role=ANY($4::text[])", "Type::BOOL"]:
            self.assertIn(marker, body)
        self.assertIn('RegistryManagementCapability::Trust => vec!["owner"]', body)
        self.assertIn('RegistryManagementCapability::Approval => vec!["owner", "editor"]', body)
        self.assertIn("tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)", body)
        self.assertNotRegex(body, "GRANT|INSERT INTO|UPDATE hwpx|DELETE FROM")
        self.assertIn('"project_acl"', (ROOT / "crates/revision-service/src/postgres.rs").read_text(encoding="utf-8"))
        self.assertIn("self.roots.register_trust", self.code)
        self.assertIn("self.approvals.register_approval", self.code)

    def test_opaque_record_current_policy_and_live_claims_precede_custody(self):
        body = self.code.split("pub fn issue_approval", 1)[1].split("fn current(", 1)[0]
        self.assertIn("record: &FormulaPolicyRegistrationRecord", body)
        for marker in ["scope.tenant() != ctx.tenant_id()", "scope.subject() != ctx.subject()", "record.version()", "self.root(scope.project())", "validate_for_issuance"]:
            self.assertIn(marker, body)
        self.assertLess(body.index("validate_for_issuance"), body.index("signer.sign(") if "signer.sign(" in body else body.index(".sign(&signing)"))
        self.assertLess(body.index(".authorize_approval("), body.index(".sign(&signing)"))
        helper = self.issuer.split("pub(super) fn validate_for_issuance", 1)[1].split("/// Wraps externally", 1)[0]
        self.assertIn("provider::validate_claims(scope, policy, trust, &self.claims, now)?", helper)
        self.assertIn("trust.keys.contains_key(&self.claims.key_id)", helper)
        self.assertNotRegex(self.code, r"from_seed|SigningKey::generate|std::env|env!\(|Deserialize|private_key")

    def test_original_ed25519_and_strict_wire_are_reused_before_ingest(self):
        body = self.code.split("pub fn issue_approval", 1)[1].split("fn current(", 1)[0]
        for marker in ["PreparedFormulaApproval::from_registration_record", "prepared.envelope", "wire::decode", "UnparsedPublicKey::new", ".verify(&signing, &signature)", "provider::validate_claims"]:
            self.assertIn(marker, body.replace("\n", " ").replace("    ", "") if marker == "prepared.envelope" else body)
        self.assertLess(body.index(".verify(&signing, &signature)"), body.index("self.ingest("))
        self.assertIn("trust_wire::decode", self.code)
        self.assertIn("FORMULA_ISSUER_TRUST_SCHEMA", self.code)
        self.assertIn("trust.keys.iter()", self.code)

    def test_artifact_acl_scanner_aead_digest_and_whole_readback(self):
        for marker in ["AuthScope::DocumentRead", "AuthScope::DocumentWrite", "ArtifactKind::Evidence", "StorageState::Available", "ValidationState::Verified", "d.quarantine_reason.is_some()", "d.size_bytes > limit as u64", "self.artifacts.download", "ContentDigest::of(&raw) != digest", "got != raw", "bytes != raw"]:
            self.assertIn(marker, self.code.replace("\n", " ").replace("    ", "") if marker == "self.artifacts.download" else self.code)
        self.assertIn("self.registry.read_trust", re.sub(r"\s+", "", self.code))
        self.assertIn("got != row", self.code)
        self.assertIn("got_trust != trust", self.code)
        self.assertIn("now < before", self.code)
        self.assertIn("self.monotonic(before)", self.code)
        self.assertIn("policy.binding.source_result_artifact", self.code)

    def test_failure_stages_preserve_ambiguous_or_acknowledged_residue(self):
        for marker in ["FormulaIssuerWriteOutcome::NotAttempted", "FormulaIssuerWriteOutcome::CommitOutcomeUnknown", "FormulaIssuerWriteOutcome::Acknowledged", "RegistryGatewayError::AcknowledgedReceiptMismatch", "FormulaIssuerWorkflowStage::ArtifactIngest", "FormulaIssuerWorkflowStage::RegistryReadback", "Some(row.artifact)"]:
            self.assertIn(marker, self.code)
        self.assertIn("RevisionError::CommitOutcomeUnknown", self.code)
        self.assertNotRegex(self.code, r"\.remove\(|\.delete\(|\.reconnect\(|for attempt|retry\(")
        self.assertNotRegex(self.code, r"println!|eprintln!|pub artifact:|pub digest:")
        self.assertIn('"(<redacted>)"', self.code)

    def test_eight_genuine_source_crypto_artifact_consumer_counterexamples(self):
        self.assertEqual(len(re.findall(r"#\[test\]", self.test)), 8)
        for marker in ["generate(&s, &p, &capture)", "require_current_product_route", "no_publication(&s)", "FormulaIssuerWriteOutcome::CommitOutcomeUnknown", "FormulaIssuerWriteOutcome::Acknowledged", "s.blobs.tamper", "clock.fail", "clock.value.store(0", "preflight_denied", "same-generation-policy-drift", "called.load"]:
            self.assertIn(marker, self.test)
        self.assertIn("self.pair.sign(raw)", self.test)
        self.assertIn("usize::from(matches!(mode, 1 | 2 | 6))", self.test)

    def test_resource_guards_and_predecessor_executables_are_preserved(self):
        for path in [DRIVER, LINT]:
            code = (ROOT / path).read_text(encoding="utf-8")
            for marker in ["$protectedPins.Count -ne 28", "$sources.Count -ne 817", "'BelowNormal'", "-Count 1", "system_cpu_percent -ge 85", "available_ram_mib -lt 4096", "Get-P09ResourceDecision", "new_receipt_required", "protected_executable_drift", "source_drift"]:
                self.assertIn(marker, code)
            self.assertIn(ARCHIVE, code)
            self.assertIn("p09-138-formula-issuer-registry-management.source-progress.v1.json", code)
            self.assertNotRegex(code, "HwpObject|Remove-Item|--nocapture")

if __name__ == "__main__":
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps({"state":"PASS_SOURCE_ONLY_NOT_ACTUAL_SQL_OR_GATE" if result.wasSuccessful() else "FAIL_CLOSED",
        "tests":result.testsRun,"failures":[t._testMethodName for t,_ in result.failures],
        "errors":[t._testMethodName for t,_ in result.errors],"P09_gate":"OPEN"}))
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
