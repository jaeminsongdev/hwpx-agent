from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = Path(__file__).parents[1] / "run_plan_review_staging_checks.py"
SPEC = importlib.util.spec_from_file_location("p16_plan_review_staging_checks", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load plan-review staging checks")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PlanReviewStagingChecksTests(unittest.TestCase):
    def test_test_token_is_read_only_and_server_clock_bound(self) -> None:
        encoded_claims = MODULE.token().split(".")[1]
        padding = "=" * (-len(encoded_claims) % 4)
        claims = json.loads(base64.urlsafe_b64decode(encoded_claims + padding))
        self.assertEqual(claims["scope"], "project.read")
        self.assertEqual(claims["sub"], MODULE.SUBJECT)
        self.assertEqual(claims["tenant_id"], MODULE.TENANT)
        self.assertEqual(claims["exp"], MODULE.NOW + 3_540)

    def test_p15_catalog_lock_is_preserved(self) -> None:
        self.assertEqual(MODULE.digest(MODULE.P15_CATALOG), MODULE.P15_CATALOG_SHA256)
        self.assertEqual(MODULE.P15_CATALOG_SHA256, "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001")

    def test_acceptance_is_owned_loopback_and_cleanup_bounded(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for required in (
            '"--pull",\n                "never"',
            '"127.0.0.1::5432"',
            'get("Labels", {}).get(LABEL) == run_id',
            '"resources_cleaned": cleaned',
            '"actual_hangul": False',
        ):
            self.assertIn(required, source)
        self.assertNotIn("docker system prune", source)

    def test_registered_path_rechecks_all_three_authorities(self) -> None:
        driver = (ROOT / "crates/plan-review-staging-driver/src/main.rs").read_text(
            encoding="utf-8"
        )
        for boundary in (
            "LocalPostgresPlanSourceRepository::connect",
            "LocalPostgresStoredPlanRegistry::connect",
            "LocalPostgresPlanReviewEvidenceRepository::connect",
            "PlanReviewRenderer",
        ):
            self.assertIn(boundary, driver)
        self.assertNotIn("StagingGateway", driver)

    def test_network_and_ciphertext_failures_are_required(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for expected in (
            '"missing_auth": 401',
            '"host_rebinding": 403',
            '"hostile_origin": 403',
            '"oversized_body": 413',
            "registered_path_rejects_ciphertext_tamper",
        ):
            self.assertIn(expected, source)


if __name__ == "__main__":
    unittest.main()
