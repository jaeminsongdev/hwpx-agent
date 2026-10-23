from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from build_object_automation_binding_overlay import (  # noqa: E402
    PRIVATE_REVIEW,
    OverlayError,
    _load,
    build_bundle,
)
from validate_object_automation_binding_overlay import validate  # noqa: E402


class ObjectAutomationBindingOverlayTests(unittest.TestCase):
    def test_current_overlay_passes_without_runtime_promotion(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["candidate_unverified"], 40)
        self.assertEqual(result["unavailable_with_reason"], 2)
        self.assertEqual(result["runtime_verified"], 0)
        self.assertEqual(result["differential"], "not_run")

    def test_projection_covers_every_matrix_row_once(self) -> None:
        _contract, _overlay, projection = build_bundle()
        candidates = set(projection["candidate_unverified"])
        denied = set(projection["denied_by_policy"])
        unavailable = {f"OBJ-{number:03d}" for number in range(1, 59)} - candidates - denied
        self.assertEqual(len(candidates), 49)
        self.assertEqual(denied, {"OBJ-011", "OBJ-057"})
        self.assertEqual(unavailable, {
            "OBJ-004", "OBJ-005", "OBJ-008", "OBJ-009", "OBJ-044", "OBJ-046", "OBJ-058",
        })

    def test_source_route_tamper_fails_against_public_contract(self) -> None:
        review = copy.deepcopy(_load(PRIVATE_REVIEW, 1024 * 1024)[0])
        review["items"][0]["source_name"] = "DrawObjCreatorEllipse"
        with self.assertRaisesRegex(OverlayError, "public_contract_drift"):
            validate(review)

    def test_unavailable_row_promotion_fails_against_public_contract(self) -> None:
        review = copy.deepcopy(_load(PRIVATE_REVIEW, 1024 * 1024)[0])
        row = next(item for item in review["items"] if item["feature_id"] == "OBJ-046")
        row.update({
            "state": "candidate_unverified",
            "source_kind": "action_table",
            "source_name": "ShapeObjDialog",
            "mapping_mode": "reviewed_parameterized_action",
            "modal_risk": "must_probe",
            "unavailable_reason": None,
        })
        with self.assertRaisesRegex(OverlayError, "review_coverage"):
            validate(review)

    def test_runtime_claim_cannot_appear_in_generated_contract(self) -> None:
        contract, _overlay, _projection = build_bundle()
        self.assertFalse(contract["not_claimed"]["runtime_qualification"])
        self.assertFalse(contract["not_claimed"]["routing_support"])
        self.assertFalse(contract["not_claimed"]["direct_automation_differential"])
        self.assertFalse(contract["not_claimed"]["p08_complete"])


if __name__ == "__main__":
    unittest.main()
