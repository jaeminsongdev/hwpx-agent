import importlib.util
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "run_postgres_plan_review_evidence_checks.py"
SPEC = importlib.util.spec_from_file_location("p16_plan_review_evidence_checks", SOURCE)
assert SPEC is not None and SPEC.loader is not None
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class PlanReviewEvidenceCheckContract(unittest.TestCase):
    def test_migration_chain_is_exact_and_ordered(self) -> None:
        self.assertEqual(len(checks.MIGRATIONS), 13)
        self.assertEqual(checks.MIGRATIONS[-1], "0013_p16_plan_review_evidence")
        self.assertEqual(len(set(checks.MIGRATIONS)), len(checks.MIGRATIONS))

    def test_migration_is_tenant_isolated_encrypted_and_guarded(self) -> None:
        up = (checks.ROOT / "migrations/postgres/0013_p16_plan_review_evidence.up.sql")
        down = (checks.ROOT / "migrations/postgres/0013_p16_plan_review_evidence.down.sql")
        up_text = up.read_text(encoding="utf-8")
        down_text = down.read_text(encoding="utf-8")
        for token in (
            "plan_review_evidence_records", "AES-256-GCM", "FORCE ROW LEVEL SECURITY",
            "current_tenant_id()", "compiled_plan_sha256", "route_set_sha256",
            "semantic_diff_sha256", "result_graph_sha256", "evidence_sha256",
            "records are immutable", "BETWEEN 1 AND 1048576", "<> repeat('0', 64)",
        ):
            self.assertIn(token, up_text)
        self.assertIn("allow_p16_plan_review_evidence_rollback", down_text)
        self.assertIn("refuses evidence records", down_text)

    def test_checker_is_loopback_owned_bounded_and_cleans_up(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        for token in (
            '"127.0.0.1::5432"', '"--memory", "512m"', '"--pids-limit", "128"',
            '"--pull", "never"', '"resources_cleaned": cleaned', '"actual_hangul": False',
            '"ciphertext_tamper_rejected"', '"cross_tenant_rls"',
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
