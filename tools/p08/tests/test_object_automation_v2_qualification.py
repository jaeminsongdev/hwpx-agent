from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

import finalize_object_automation_v2_qualification as finalizer  # noqa: E402
from validate_object_automation_v2_qualification import (  # noqa: E402
    ValidationError,
    validate,
)


class ObjectAutomationV2QualificationTests(unittest.TestCase):
    def test_deterministic_rebuild_and_validator_pass(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["automation_runtime_verified"], 34)
        self.assertEqual(result["automation_unavailable_with_reason"], 8)
        self.assertEqual(result["p08_green_rows"], 41)
        self.assertEqual(result["p08_phase_gate"], "pass_with_target_unavailable")

    def test_public_receipt_does_not_leak_private_paths_or_action_names(self) -> None:
        receipt = finalizer.load_json(finalizer.PUBLIC_RECEIPT)
        serialized = finalizer.canonical_bytes(receipt).decode("utf-8")
        self.assertNotIn("evidence/private", serialized)
        self.assertNotIn("DrawObjCreatorRectangle", serialized)
        self.assertNotIn("ShapeObjDialog", serialized)
        self.assertNotIn("D:/", serialized)

    def test_runtime_promotion_tamper_fails_closed(self) -> None:
        receipt = finalizer.load_json(finalizer.PUBLIC_RECEIPT)
        tampered = copy.deepcopy(receipt)
        row = next(item for item in tampered["rows"] if item["feature_id"] == "OBJ-003")
        row["automation_runtime"]["state"] = "verified_current_target"
        with self.assertRaisesRegex(ValidationError, "deterministic_output_drift:receipt"):
            validate(receipt_override=tampered)

    def test_unavailable_fallback_cannot_be_routed(self) -> None:
        projection = finalizer.load_json(finalizer.PUBLIC_PROJECTION)
        tampered = copy.deepcopy(projection)
        tampered["verified_current_target"].append("OBJ-048")
        with self.assertRaisesRegex(ValidationError, "deterministic_output_drift:projection"):
            validate(projection_override=tampered)


if __name__ == "__main__":
    unittest.main()
