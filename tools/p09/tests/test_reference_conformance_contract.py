from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p09"))

from reference_conformance import (  # noqa: E402
    COMPONENT_PROFILES,
    MATRIX,
    STATIC_SECTION_INTEGRATION,
    ConformanceError,
    build_matrix,
    load_json,
)
from validate_reference_conformance_contract import CONTRACT, validate  # noqa: E402


class ReferenceConformanceContractTests(unittest.TestCase):
    def test_private_contract_validator_passes_without_target_promotion(self) -> None:
        result = validate(run_upstream=False)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["required_rows"], 53)
        self.assertEqual(result["component_covered_rows"], 46)
        self.assertEqual(result["component_stage_counts"]["integration_passed"], 2)
        self.assertEqual(result["green_rows"], 0)
        self.assertEqual(result["actual_hangul"], "not_run")

    def test_matrix_has_every_row_and_no_false_green(self) -> None:
        matrix = load_json(MATRIX)
        self.assertEqual(
            [row["feature_id"] for row in matrix["rows"]],
            [f"REF-{number:03d}" for number in range(1, 54)],
        )
        self.assertEqual(matrix["summary"]["p09_owned_rows"], 46)
        self.assertEqual(matrix["summary"]["p11_deferred_rows"], 7)
        self.assertEqual(matrix["summary"]["component_covered_rows"], 46)
        self.assertTrue(all(row["gate_state"] == "non_green" for row in matrix["rows"]))

    def test_all_target_claims_remain_not_run_or_false(self) -> None:
        matrix = build_matrix()
        self.assertEqual(matrix["summary"]["green_rows"], 0)
        self.assertFalse(matrix["claims"]["actual_hwpx"])
        self.assertFalse(matrix["claims"]["actual_hangul"])
        self.assertFalse(matrix["claims"]["render"])
        self.assertFalse(matrix["claims"]["automation"])
        self.assertFalse(matrix["claims"]["differential"])
        for row in matrix["rows"]:
            expected = (
                "static_section_integration_passed"
                if row["feature_id"] in STATIC_SECTION_INTEGRATION
                else "not_run"
            )
            self.assertEqual(row["direct_hwpx"]["implementation_state"], expected)
            self.assertEqual(row["differential_state"], "not_run")

    def test_component_collision_fails_closed(self) -> None:
        profiles = copy.deepcopy(COMPONENT_PROFILES)
        profiles["p09-10-reference-auxiliary-v1"]["features"] += ("REF-044",)
        with self.assertRaisesRegex(ConformanceError, "component_feature_collision"):
            build_matrix(profiles_override=profiles)

    def test_deferred_row_cannot_be_promoted_to_component(self) -> None:
        profiles = copy.deepcopy(COMPONENT_PROFILES)
        features = list(profiles["p09-01-field-core-v1"]["features"])
        features[-1] = "REF-016"
        profiles["p09-01-field-core-v1"]["features"] = tuple(features)
        with self.assertRaisesRegex(ConformanceError, "component_coverage_drift"):
            build_matrix(profiles_override=profiles)

    def test_profile_and_evidence_shape_tamper_fail_closed(self) -> None:
        missing_profile = copy.deepcopy(COMPONENT_PROFILES)
        del missing_profile["p09-09-mail-merge-v1"]
        with self.assertRaisesRegex(ConformanceError, "component_profile_set"):
            build_matrix(profiles_override=missing_profile)

        private_path = copy.deepcopy(COMPONENT_PROFILES)
        private_path["p09-09-mail-merge-v1"]["evidence"] = ("D:/private/source.rs",)
        with self.assertRaisesRegex(ConformanceError, "private_evidence_path"):
            build_matrix(profiles_override=private_path)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"state":"pass","state":"green"}', encoding="utf-8")
            with self.assertRaisesRegex(ConformanceError, "duplicate_json_key"):
                load_json(Path("duplicate.json"), root=Path(temporary))

    def test_private_contract_claim_promotion_fails_closed(self) -> None:
        contract = load_json(CONTRACT)
        promoted = copy.deepcopy(contract)
        promoted["claims"]["actual_hangul"] = True
        with self.assertRaisesRegex(ConformanceError, "claim_promotion"):
            validate(contract_override=promoted, run_upstream=False)

    def test_checked_in_matrix_green_tamper_fails_closed(self) -> None:
        matrix = load_json(MATRIX)
        promoted = copy.deepcopy(matrix)
        promoted["rows"][0]["gate_state"] = "green"
        promoted["rows"][0]["blockers"] = []
        with self.assertRaisesRegex(ConformanceError, "matrix_drift"):
            validate(matrix_override=promoted, run_upstream=False)


if __name__ == "__main__":
    unittest.main()
