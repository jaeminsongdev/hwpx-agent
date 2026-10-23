from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from validate_aspect_lock_negative_qualification import (  # noqa: E402
    QualificationError,
    load,
    validate,
)


class AspectLockNegativeQualificationTests(unittest.TestCase):
    def test_exact_current_target_negative_qualification_passes(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["decision"], "CAPABILITY_UNAVAILABLE_FOR_TARGET")
        self.assertEqual(result["actual_target_runtime"], "not_run")
        self.assertEqual(result["row"], "non_green")

    def test_decision_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["decision"]["non_equivalent_surface"] = "AspectLock"
        with self.assertRaisesRegex(QualificationError, "decision"):
            validate(value, verify_installed=False, verify_source_qualification=False)

    def test_model_field_promotion_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["official_model"]["aspect_lock_field_count"] = 1
        with self.assertRaisesRegex(QualificationError, "official_model"):
            validate(value, verify_installed=False, verify_source_qualification=False)

    def test_installed_surface_promotion_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["installed_surface"]["aspect_ratio_control_token_hits"] = 1
        with self.assertRaisesRegex(QualificationError, "installed_surface"):
            validate(value, verify_installed=False, verify_source_qualification=False)

    def test_automation_promotion_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["official_automation"]["exact_binding_found"] = True
        with self.assertRaisesRegex(QualificationError, "official_automation"):
            validate(value, verify_installed=False, verify_source_qualification=False)

    def test_completion_claim_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["claims"]["p08_complete"] = True
        with self.assertRaisesRegex(QualificationError, "claims"):
            validate(value, verify_installed=False, verify_source_qualification=False)


if __name__ == "__main__":
    unittest.main()
