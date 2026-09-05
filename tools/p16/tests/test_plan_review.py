from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_plan_review_contract
import plan_review


class PlanReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(plan_review.POLICY_PATH.read_text(encoding="utf-8"))

    def test_policy_is_exact(self) -> None:
        self.assertEqual(plan_review.validate_policy(self.policy), [])

    def test_unknown_policy_field_is_rejected(self) -> None:
        value = copy.deepcopy(self.policy)
        value["extra"] = True
        self.assertEqual(plan_review.validate_policy(value), ["policy.fields"])

    def test_confirmation_cannot_be_weakened(self) -> None:
        value = copy.deepcopy(self.policy)
        value["confirmation"]["repeat_dry_run"] = False
        self.assertIn("policy.confirmation", plan_review.validate_policy(value))

    def test_closed_csp_is_required(self) -> None:
        value = copy.deepcopy(self.policy)
        value["resource"]["csp"]["connectDomains"] = ["https://example.invalid"]
        self.assertIn("policy.resource", plan_review.validate_policy(value))

    def test_exact_browser_evidence_is_locked(self) -> None:
        value = copy.deepcopy(self.policy)
        value["visual_qa"]["captures"][0]["sha256"] = "0" * 64
        self.assertIn("policy.visual.image.digest", plan_review.validate_policy(value))

    def test_predecessor_and_catalog_are_exact(self) -> None:
        self.assertEqual(plan_review.validate_predecessor(), [])
        self.assertEqual(plan_review.validate_catalog(), [])

    def test_authored_sources_are_offline_and_redacted(self) -> None:
        self.assertEqual(plan_review.validate_sources(), [])

    def test_css_has_responsive_accessible_tokens(self) -> None:
        self.assertEqual(plan_review.validate_css(), [])

    def test_bundle_is_bounded_and_has_protocol_markers(self) -> None:
        value = plan_review.BUNDLE_PATH.read_bytes()
        self.assertEqual(plan_review.validate_bundle_bytes(value), [])

    def test_bundle_rejects_eval_and_local_storage(self) -> None:
        base = plan_review.BUNDLE_PATH.read_bytes()
        self.assertTrue(plan_review.validate_bundle_bytes(base + b"eval('x')"))
        self.assertTrue(plan_review.validate_bundle_bytes(base + b"localStorage"))

    def test_all_sources_and_bundles_validate(self) -> None:
        bundles, errors = plan_review.validate_all()
        self.assertEqual(errors, [])
        self.assertIsNotNone(bundles)
        self.assertLessEqual(bundles["resource"]["bytes"], 800_000)

    def test_contract_source_paths_are_unique(self) -> None:
        self.assertEqual(len(build_plan_review_contract.LOCAL_SOURCES), len(set(build_plan_review_contract.LOCAL_SOURCES)))

    def test_contract_declares_only_local_component_claim(self) -> None:
        contract = build_plan_review_contract.build()
        self.assertEqual(contract["decision"], "pass_scoped_local_high_risk_confirmation_component_e2e_actual_host_pending")
        self.assertFalse(any(contract["claims"].values()))
        self.assertEqual(contract["e2e"]["call_count"], 5)


if __name__ == "__main__":
    unittest.main()
