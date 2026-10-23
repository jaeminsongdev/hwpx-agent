from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from validate_object_surface_qualification import (  # noqa: E402
    QualificationError,
    load,
    validate,
)


class ObjectSurfaceQualificationTests(unittest.TestCase):
    def test_exact_public_qualification_passes(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["surface_present_count"], 38)
        self.assertEqual(result["automation_runtime"], "not_run")

    def test_candidate_execution_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["execution"]["action_execute_count"] = 1
        with self.assertRaisesRegex(QualificationError, "execution"):
            validate(value, verify_source_hashes=False)

    def test_completion_claim_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["claims"]["p08_complete"] = True
        with self.assertRaisesRegex(QualificationError, "claims"):
            validate(value, verify_source_hashes=False)

    def test_raw_identifier_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["cases"][0]["source_identifier_sha256"] = "DrawObjCreatorRectangle"
        with self.assertRaisesRegex(QualificationError, "case_identifier"):
            validate(value, verify_source_hashes=False)

    def test_case_surface_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(load())
        value["cases"][0]["action_created"] = False
        with self.assertRaisesRegex(QualificationError, "action_case"):
            validate(value, verify_source_hashes=False)


if __name__ == "__main__":
    unittest.main()

