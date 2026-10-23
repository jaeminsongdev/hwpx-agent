from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from validate_object_target_qualification import (  # noqa: E402
    QualificationError,
    load,
    validate,
)


class ObjectTargetQualificationTests(unittest.TestCase):
    def test_exact_public_qualification_passes(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["feature_count"], 41)
        self.assertEqual(result["direct_stage"], "oracle_verified")
        self.assertEqual(result["required_matrix"], "non_green")

    def test_feature_set_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["feature_ids"][0] = "OBJ-044"
        with self.assertRaisesRegex(QualificationError, "feature_set"):
            validate(value, verify_source_hashes=False)

    def test_receipt_identity_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["identities"]["oracle_report_sha256"] = "0" * 64
        with self.assertRaisesRegex(QualificationError, "identities"):
            validate(value, verify_source_hashes=False)

    def test_user_attestation_boundary_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["user_access"]["computer_use_click_or_type_invoked"] = True
        with self.assertRaisesRegex(QualificationError, "user_access"):
            validate(value, verify_source_hashes=False)

    def test_completion_claim_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["claims"]["p08_complete"] = True
        with self.assertRaisesRegex(QualificationError, "claims"):
            validate(value, verify_source_hashes=False)


if __name__ == "__main__":
    unittest.main()
