from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from validate_object_shape_canary_qualification import (  # noqa: E402
    QualificationError,
    load,
    validate,
)


class ObjectShapeCanaryQualificationTests(unittest.TestCase):
    def test_exact_public_qualification_passes(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["qualified_canary_case_count"], 5)
        self.assertEqual(result["differential"], "not_run")

    def test_missing_effect_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["cases"][0]["effect_observed"] = False
        with self.assertRaisesRegex(QualificationError, "case_state"):
            validate(value, verify_source_hashes=False)

    def test_false_raw_exact_promotion_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["cases"][0]["undo_raw_exact"] = True
        with self.assertRaisesRegex(QualificationError, "shadow_raw_boundary"):
            validate(value, verify_source_hashes=False)

    def test_normalization_scope_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["normalization"]["scope"] = "all_empty_attributes"
        with self.assertRaisesRegex(QualificationError, "normalization"):
            validate(value, verify_source_hashes=False)

    def test_completion_claim_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["claims"]["p08_complete"] = True
        with self.assertRaisesRegex(QualificationError, "claims"):
            validate(value, verify_source_hashes=False)


if __name__ == "__main__":
    unittest.main()
