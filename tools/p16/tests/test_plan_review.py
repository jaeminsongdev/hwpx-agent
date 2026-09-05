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

    def test_visual_evidence_is_bound_to_current_preview(self) -> None:
        value = copy.deepcopy(self.policy)
        value["visual_qa"]["preview_sha256"] = "0" * 64
        self.assertIn("policy.visual.preview_digest", plan_review.validate_policy(value))

    def test_unknown_execution_and_minimum_width_captures_are_required(self) -> None:
        expected = {
            "p16-06-desktop-committed_unverified.png",
            "p16-06-desktop-unconfirmed.png",
            "p16-06-minimum-committed_unverified.png",
            "p16-06-narrow-unconfirmed.png",
            "p16-06-narrow-committed_unverified.png",
            "p16-06-minimum-ready.png",
        }
        actual = {Path(item["path"]).name for item in self.policy["visual_qa"]["captures"]}
        self.assertTrue(expected <= actual)
        for filename in expected:
            value = copy.deepcopy(self.policy)
            value["visual_qa"]["captures"] = [item for item in value["visual_qa"]["captures"] if Path(item["path"]).name != filename]
            self.assertTrue(plan_review.validate_policy(value))

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

    def test_runner_builds_the_continuity_predecessor_before_plan_review(self) -> None:
        runner = (plan_review.ROOT / "tools/p16/run_plan_review_checks.py").read_text(encoding="utf-8")
        predecessor = 'run("node","web/plugin-widget/scripts/build-continuity-widget.mjs")'
        current = 'run("node","web/plugin-widget/scripts/build-plan-review-widget.mjs")'
        self.assertIn(predecessor, runner)
        self.assertLess(runner.index(predecessor), runner.index(current))

    def test_contract_declares_only_local_component_claim(self) -> None:
        contract = build_plan_review_contract.build()
        self.assertEqual(contract["decision"], "pass_scoped_local_high_risk_confirmation_component_e2e_actual_host_pending")
        self.assertFalse(any(contract["claims"].values()))
        self.assertEqual(contract["e2e"]["call_count"], 5)
        self.assertFalse(contract["claims"]["authenticated_stored_plan_projection_integrated"])
        self.assertTrue(contract["next_task"].startswith("P16-06 "))


if __name__ == "__main__":
    unittest.main()
