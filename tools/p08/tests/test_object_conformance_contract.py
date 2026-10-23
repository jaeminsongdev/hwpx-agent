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
    def test_complete_validator_passes_with_bounded_p08_target_evidence(self) -> None:
        result = validate(run_upstream=False)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["required_rows"], 58)
        self.assertEqual(result["implementation_covered_rows"], 53)
        self.assertEqual(result["green_rows"], 41)
        self.assertEqual(result["actual_hangul"], "pass")
        self.assertEqual(result["render"], "pass")
        self.assertEqual(result["obj044"], "CAPABILITY_UNAVAILABLE_FOR_TARGET")
        self.assertEqual(result["automation"], "34_verified_8_unavailable")
        self.assertEqual(result["p08"], "pass_with_target_unavailable")

    def test_obj044_negative_qualification_is_required(self) -> None:
        direct = load_json(DIRECT)
        tampered = copy.deepcopy(direct)
        profile = next(
            item for item in tampered["profiles"]
            if item["profile_id"] == "object-properties-component-v1"
        )
        profile["evidence_files"].remove(
            "implementation/p08/evidence/"
            "p08-21-aspect-lock-negative-qualification.current-2020.v1.json"
        )
        with self.assertRaisesRegex(ConformanceError, "obj044_negative_qualification_missing"):
            build_matrix(direct_override=tampered)

    def test_matrix_has_exact_p08_green_set_and_p11_stays_deferred(self) -> None:
        matrix = load_json(MATRIX)
        self.assertEqual(
            [row["feature_id"] for row in matrix["rows"]],
            [f"OBJ-{number:03d}" for number in range(1, 59)],
        )
        self.assertEqual(matrix["summary"]["direct_stage_counts"], {
            "cataloged": 5,
            "unit_passed": 10,
            "integration_passed": 2,
            "oracle_verified": 41,
        })
        p08 = [row for row in matrix["rows"] if row["catalog_phase"] == "P08"]
        p11 = [row for row in matrix["rows"] if row["catalog_phase"] == "P11"]
        self.assertEqual(sum(row["gate_state"] == "green" for row in p08), 41)
        self.assertEqual(
            next(row for row in p08 if row["feature_id"] == "OBJ-044")["phase_acceptance"],
            "target_unavailable_accepted",
        )
        self.assertTrue(all(row["gate_state"] == "non_green" for row in p11))
        self.assertEqual(matrix["summary"]["differential_counts"], {
            "exact_match": 34,
            "not_applicable_fallback_unavailable": 7,
            "not_applicable_target_capability_unavailable": 1,
            "not_run": 16,
        })
        self.assertEqual(matrix["summary"]["automation_binding_counts"], {
            "verified_current_target": 34,
            "candidate_unverified": 9,
            "denied_by_policy": 2,
            "unavailable_with_reason": 13,
        })

    def test_direct_collision_and_oracle_demotion_fail_closed(self) -> None:
        direct = load_json(DIRECT)
        collided = copy.deepcopy(direct)
        collided["profiles"][1]["feature_ids"].append("OBJ-002")
        with self.assertRaises(ConformanceError):
            build_matrix(direct_override=collided)

        promoted = copy.deepcopy(direct)
        promoted["profiles"][0]["stage"] = "integration_passed"
        with self.assertRaisesRegex(ConformanceError, "direct_profile_semantic_drift"):
            build_matrix(direct_override=promoted)

        wrong_qualification = copy.deepcopy(direct)
        wrong_qualification["target_qualification_file"] = "implementation/p08/evidence/other.json"
        with self.assertRaisesRegex(ConformanceError, "direct_target_qualification"):
            build_matrix(direct_override=wrong_qualification)

    def test_automation_and_threshold_claim_tamper_fail_closed(self) -> None:
        automation = load_json(AUTOMATION)
        promoted = copy.deepcopy(automation)
        promoted["verified_current_target"].append("OBJ-048")
        with self.assertRaisesRegex(ConformanceError, "automation_feature_set|automation_semantic_drift"):
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
        promoted_contract["claims"]["p08_complete_current_pc"] = False
        with self.assertRaisesRegex(ConformanceError, "contract_drift"):
            validate(contract_override=promoted_contract, run_upstream=False)

        matrix = load_json(MATRIX)
        promoted_matrix = copy.deepcopy(matrix)
        obj044 = next(row for row in promoted_matrix["rows"] if row["feature_id"] == "OBJ-044")
        obj044["gate_state"] = "green"
        obj044["blockers"] = []
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
