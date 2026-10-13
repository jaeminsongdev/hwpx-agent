"""No DB/native execution: parser/protocol/source predicate coverage only."""
import json
import hashlib
from pathlib import Path
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from tools.p09 import source_policy_oracle_diagnostics as M

ROOT = Path(__file__).resolve().parents[3]
RECEIPT = "8" * 32  # Synthetic, never an actual artifact identity.

class OracleDiagnosticsTests(unittest.TestCase):
    def test_ten_owned_cases_are_exactly_bounded(self):
        for case in range(10):
            context = M.parse_context(f"P84_DB_ERROR code=55000\nP84_ORACLE_CONTEXT case={case} receipt={RECEIPT}\n")
            self.assertEqual(context.case, case)
            self.assertEqual(context.receipt, RECEIPT)
            self.assertNotIn(RECEIPT, repr(context))

    def test_missing_duplicate_malformed_and_injected_context_never_query(self):
        good = f"P84_ORACLE_CONTEXT case=0 receipt={RECEIPT}"
        for value in ["", good+"\n"+good, good+" SQL", good.replace("case=0", "case=10"),
                      good.replace(RECEIPT, "0"*32), good.replace(RECEIPT, "'; DELETE FROM x;--"),
                      good.replace("receipt=", "receipt=PRIVATE-"), good+"a"]:
            self.assertIsNone(M.parse_context(value))

    def test_context_budgets_nontext_and_invalid_unicode_redact(self):
        for value in [None, 1, "a"*(M.MAX_BYTES+1), "\ud800"]:
            self.assertIsNone(M.parse_context(value))
            self.assertEqual(M.closed_literal_reasons(value, {"TEST_POLICY_SAMPLE"}), [])

    def test_query_uses_same_owned_case_result_job_receipt_not_current_head_guess(self):
        context = M.OwnedContext(9, RECEIPT)
        query = M.query(ROOT, context)
        self.assertIn(f"v.revision_id='{209:032x}'::uuid", query)
        self.assertIn(f"r.idempotency_key='{509:032x}'::uuid", query)
        self.assertIn(f"r.job_id = '{609:032x}'::uuid", query)
        self.assertIn(f"ra.artifact_id='{RECEIPT}'::uuid", query)
        self.assertNotIn("$", query)
        self.assertNotIn("v.revision_id=b.head_revision_id", query)

    def test_wrong_case_type_zero_id_and_untrusted_query_hash_reject(self):
        for context in [None, M.OwnedContext(True, RECEIPT), M.OwnedContext(10, RECEIPT),
                        M.OwnedContext(-1, RECEIPT), M.OwnedContext(0, 1), M.OwnedContext(0, "0"*32)]:
            with self.assertRaises(ValueError): M.query(ROOT, context)
        with patch.object(M, "SQL_SHA256", "0"*64):
            with self.assertRaises(ValueError): M.query(ROOT, M.OwnedContext(0, RECEIPT))

    def test_all_forty_columns_are_unique_and_present_once(self):
        self.assertEqual(len(M.CHECKS), 40)
        self.assertEqual(len(set(M.CHECKS)), 40)
        text = (ROOT / M.SQL_PATH).read_text(encoding="utf-8")
        self.assertEqual(tuple(re.findall(r"\) AS ([a-z_]+)", text)), M.CHECKS)

    def test_bool_false_and_null_unknown_are_not_defaults_or_cause_claims(self):
        values = {key: True for key in M.CHECKS}
        values[M.CHECKS[0]] = False
        values[M.CHECKS[1]] = None
        result = M.decode_snapshot(json.dumps(values))
        self.assertIs(result["checks"][M.CHECKS[0]], False)
        self.assertIsNone(result["checks"][M.CHECKS[1]])
        self.assertFalse(result["root_cause_proven"])
        self.assertFalse(result["original_atomic_oracle_verified"])
        self.assertNotIn(RECEIPT, json.dumps(result))

    def test_missing_extra_duplicate_nonbool_and_full_log_do_not_enter_receipts(self):
        values = {key: True for key in M.CHECKS}
        missing = dict(values); missing.pop(M.CHECKS[0])
        extra = dict(values); extra["PRIVATE-PATH"] = "SECRET"
        for data in [missing, extra, [], None] + [{**values, M.CHECKS[0]: v} for v in [0, 1, "true", "SECRET", [], {}]]:
            with self.assertRaises(ValueError): M.decode_snapshot(json.dumps(data))
        duplicate = json.dumps(values)[:-1] + ',"head_revision":false}'
        with self.assertRaises(ValueError): M.decode_snapshot(duplicate)
        for data in ["FULL PRIVATE LOG", "x"*(M.MAX_BYTES+1)]:
            with self.assertRaises(ValueError): M.decode_snapshot(data)

    def test_only_literal_known_local_failure_codes_are_retained(self):
        allowed = M.literal_reason_codes(["RAISE EXCEPTION 'TEST_POLICY_SAMPLE'; MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED'; RAISE EXCEPTION 'DYNAMIC_%';"])
        self.assertEqual(allowed, {"TEST_POLICY_SAMPLE", "IDEMPOTENCY_COMMITTED_ORACLE_FAILED"})
        log = "password PRIVATE-PATH TEST_POLICY_FAKE_SECRET TEST_POLICY_SAMPLE IDEMPOTENCY_COMMITTED_ORACLE_FAILED"
        self.assertEqual(M.closed_literal_reasons(log, allowed), sorted(allowed))
        self.assertEqual(M.closed_literal_reasons("TEST_POLICY_SAMPLE_SECRET", allowed), [])

    def test_original_atomic_oracle_predicates_are_covered_by_observation_clauses(self):
        original = (ROOT / "migrations/postgres/0007_p14_idempotency_reconciliation.up.sql").read_text(encoding="utf-8")
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), "cc60353df6cf3c51155417e39d0f1f4c348d2a6282bba7d63de9ea0282be5e5d")
        body = original.split("CREATE FUNCTION hwpx_agent.idempotency_v2_committed_effect_qualified(", 1)[1].split("$$;", 1)[0]
        where = body.split("WHERE revision.tenant_id = p_tenant_id", 1)[1]
        statements = re.findall(r"AND ([^\n]+)", where)
        query = (ROOT / M.SQL_PATH).read_text(encoding="utf-8")
        replacements = {"revision.": "v.", "result_artifact.": "a.", "result_acl.": "acl.", "seal.": "s.", "commit_receipt.": "c.",
                        "p_source_artifact_id": "r.source_artifact_id", "p_operation_plan_sha256": "j.operation_plan_sha256",
                        "p_subject_sha256": "$3::character(64)", "p_expected_effect_sha256": "r.expected_effect_sha256",
                        "p_expected_generation": "r.expected_revision_generation", "p_transaction_receipt_sha256": "r.transaction_receipt_sha256",
                        "p_branch_id": "r.branch_id", "p_expected_revision_id": "r.expected_revision_id"}
        for statement in statements:
            if statement == "revision.project_id = p_project_id":
                self.assertIn("v.project_id=r.project_id", query); continue
            if statement == "revision.revision_id = p_result_revision_id":
                self.assertIn("v.revision_id=$6", query); continue
            if statement == "result_acl.subject_sha256 = p_subject_sha256":
                self.assertIn("acl.subject_sha256=$3::character(64)", query); continue
            for old, new in replacements.items(): statement = statement.replace(old, new)
            self.assertIn(statement, query)
        self.assertEqual(len(statements), 24)

    def test_current_application_grants_do_not_expand_for_diagnostics(self):
        runner = (ROOT / "tools/p09/run_stored_source_policy_postgres_checks.py").read_text(encoding="utf-8")
        self.assertNotIn("GRANT SELECT ON hwpx_agent.idempotency_records TO p84_revision_app", runner)
        self.assertIn("ROOT, child.stderr, environment,", runner)
        worker = (ROOT / "crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.rs").read_text(encoding="utf-8")
        self.assertNotIn("query_one", worker)
        self.assertNotIn("query_opt", worker)

    def test_owner_checks_precede_the_readonly_query(self):
        calls = []
        stderr = f"P84_ORACLE_CONTEXT case=0 receipt={RECEIPT}"
        result = M.capture(ROOT, stderr, lambda: calls.append("owner"),
            lambda text: (calls.append("query") or SimpleNamespace(returncode=0, stdout=json.dumps({key: None for key in M.CHECKS}))))
        self.assertEqual(calls, ["owner", "query"])
        self.assertFalse(result["root_cause_proven"])

    def test_owner_failure_or_missing_context_never_executes_query(self):
        stderr = f"P84_ORACLE_CONTEXT case=0 receipt={RECEIPT}"
        for value in [stderr, "unrelated secret stderr"]:
            calls = []
            def owner(): raise ValueError("PRIVATE_OWNER_TOKEN")
            result = M.capture(ROOT, value, owner, lambda text: calls.append(text))
            self.assertEqual(calls, [])
            self.assertFalse(result["root_cause_proven"])
            self.assertNotIn("PRIVATE", json.dumps(result))

    def test_query_protocol_and_timeout_failures_never_replace_primary_error(self):
        import subprocess
        stderr = f"P84_ORACLE_CONTEXT case=0 receipt={RECEIPT}"
        for error in [ValueError("PRIVATE"), RuntimeError("TOKEN"), subprocess.TimeoutExpired("SECRET COMMAND", 5), TypeError("PRIVATE")]:
            def execute(text): raise error
            result = M.capture(ROOT, stderr, lambda: None, execute)
            self.assertEqual(result["state"], "unavailable_diagnostic_NOT_cause")
            self.assertFalse(result["root_cause_proven"])
            self.assertNotIn(RECEIPT, json.dumps(result))
        for completed in [SimpleNamespace(returncode=1, stdout="PRIVATE"), SimpleNamespace(returncode=0, stdout="PRIVATE")]:
            result = M.capture(ROOT, stderr, lambda: None, lambda text: completed)
            self.assertFalse(result["root_cause_proven"])
            self.assertNotIn("PRIVATE", json.dumps(result))

if __name__ == "__main__": unittest.main()
