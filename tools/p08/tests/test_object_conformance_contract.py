from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p08"))

from object_conformance import (  # noqa: E402
    AUTOMATION,
    DIRECT,
    MATRIX,
    THRESHOLDS,
    ConformanceError,
    build_matrix,
    load_json,
)
from validate_object_conformance_contract import CONTRACT, validate  # noqa: E402


class ObjectConformanceContractTests(unittest.TestCase):
    def test_complete_validator_passes_without_promoting_target_evidence(self) -> None:
        result = validate(run_upstream=False)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["required_rows"], 58)
        self.assertEqual(result["implementation_covered_rows"], 39)
        self.assertEqual(result["green_rows"], 0)
        self.assertEqual(result["actual_hangul"], "not_run")
        self.assertEqual(result["render"], "not_run")

    def test_matrix_has_every_exact_catalog_row_and_no_false_green(self) -> None:
        matrix = load_json(MATRIX)
        self.assertEqual(
            [row["feature_id"] for row in matrix["rows"]],
            [f"OBJ-{number:03d}" for number in range(1, 59)],
        )
        self.assertEqual(matrix["summary"]["direct_stage_counts"], {
            "cataloged": 19,
            "unit_passed": 17,
            "integration_passed": 22,
            "oracle_verified": 0,
        })
        self.assertTrue(all(row["gate_state"] == "non_green" for row in matrix["rows"]))
        self.assertTrue(all(row["differential_state"] == "not_run" for row in matrix["rows"]))

    def test_direct_collision_and_false_oracle_promotion_fail_closed(self) -> None:
        direct = load_json(DIRECT)
        collided = copy.deepcopy(direct)
        collided["profiles"][1]["feature_ids"].append("OBJ-002")
        with self.assertRaises(ConformanceError):
            build_matrix(direct_override=collided)

        promoted = copy.deepcopy(direct)
        promoted["profiles"][0]["stage"] = "oracle_verified"
        with self.assertRaisesRegex(ConformanceError, "direct_profile_semantic_drift"):
            build_matrix(direct_override=promoted)

    def test_automation_and_threshold_claim_tamper_fail_closed(self) -> None:
        automation = load_json(AUTOMATION)
        promoted = copy.deepcopy(automation)
        promoted["actual_target_profile"] = True
        with self.assertRaisesRegex(ConformanceError, "automation_private_or_actual_claim"):
            build_matrix(automation_override=promoted)

        thresholds = load_json(THRESHOLDS)
        weakened = copy.deepcopy(thresholds)
        weakened["render_profiles"]["object-affected-region-strict-v1"][
            "unchanged_region_changed_pixels_max"
        ] = 1
        with self.assertRaisesRegex(ConformanceError, "render_threshold_weakened"):
            build_matrix(threshold_override=weakened)

    def test_contract_claim_and_matrix_green_tamper_fail_closed(self) -> None:
        contract = load_json(CONTRACT)
        promoted_contract = copy.deepcopy(contract)
        promoted_contract["claims"]["actual_hangul"] = True
        with self.assertRaisesRegex(ConformanceError, "claim_promotion"):
            validate(contract_override=promoted_contract, run_upstream=False)

        matrix = load_json(MATRIX)
        promoted_matrix = copy.deepcopy(matrix)
        promoted_matrix["rows"][0]["gate_state"] = "green"
        promoted_matrix["rows"][0]["blockers"] = []
        with self.assertRaisesRegex(ConformanceError, "matrix_drift"):
            validate(matrix_override=promoted_matrix, run_upstream=False)

    def test_duplicate_json_key_is_rejected_before_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"state":"pass","state":"green"}', encoding="utf-8")
            with self.assertRaisesRegex(ConformanceError, "duplicate_json_key"):
                load_json(Path("duplicate.json"), root=Path(temporary))


if __name__ == "__main__":
    unittest.main()
