from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.p06 import plan_table_automation_candidate_6_batch as planner


def candidate(
    feature_id: str,
    capability_id: str,
    parameter_state: str,
) -> dict[str, object]:
    parameter_set_id = None if parameter_state == "source_declares_none" else f"P{feature_id}"
    return {
        "binding_key": (
            f"{capability_id}@hancom-hangul-2020-secondary/11.0.0.9136/ko-KR"
        ),
        "feature_id": feature_id,
        "capability_id": capability_id,
        "status": "candidate_unverified",
        "scope_class": "artifact_semantics",
        "runtime_support_state": "unverified",
        "routing_enabled": False,
        "invocation": {
            "kind": "action",
            "action_id": f"Action{feature_id}",
            "parameter_set_id": parameter_set_id,
            "parameter_set_state": parameter_state,
            "parameter_map_state": "pending_runtime_probe",
            "parameter_map": [],
        },
    }


def success_inputs() -> tuple[dict[str, object], dict[str, object]]:
    registry_rows = [
        candidate(
            feature_id,
            capability_id,
            planner.EXPECTED_PARAMETER_STATE[feature_id],
        )
        for feature_id, capability_id, _ in planner.EXPECTED_ROWS
    ]
    registry: dict[str, object] = {
        "schema_version": "registry/v1",
        "source_lock_id": "source",
        "restricted_derivative": True,
        "generator": {},
        "inputs": {},
        "target": {
            "profile_id": planner.EXPECTED_TARGET["profile_id"],
            "product": planner.EXPECTED_TARGET["product"],
            "major_release": "2020",
            "exact_build": planner.EXPECTED_TARGET["build"],
            "locale": planner.EXPECTED_TARGET["locale"],
            "architecture": planner.EXPECTED_TARGET["architecture"],
            "license_state": "approved",
            "routing_enabled": False,
        },
        "bindings": registry_rows,
        "coverage": {},
        "runtime_qualification": {
            "state": "not_run",
            "probe_required": True,
            "qualified_binding_count": 0,
        },
    }
    projection_rows = [
        {
            "feature_id": feature_id,
            "capability_id": capability_id,
            "binding_status": "candidate_unverified",
            "runtime_support_state": "unverified",
            "routing_enabled": False,
        }
        for feature_id, capability_id, _ in planner.EXPECTED_ROWS
    ]
    projection: dict[str, object] = {
        "schema_version": "projection/v1",
        "target": {
            **planner.EXPECTED_TARGET,
            "scope": "current_pc_personal_local_development",
        },
        "source_registry_sha256": "a" * 64,
        "row_count": 61,
        "rows": projection_rows,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
    }
    return registry, projection


class TableAutomationCandidate6BatchPlanTests(unittest.TestCase):
    def build(self) -> dict[str, object]:
        registry, projection = success_inputs()
        return planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_builds_exact_six_in_feature_order_without_execution(self) -> None:
        request = self.build()
        self.assertEqual(request["case_count"], 6)
        self.assertEqual(
            [case["feature_id"] for case in request["cases"]],
            [feature_id for feature_id, _, _ in planner.EXPECTED_ROWS],
        )
        self.assertTrue(all(case["execute"] is False for case in request["cases"]))
        self.assertFalse(request["policy"]["candidate_action_execute_allowed"])
        self.assertEqual(request["promotion"]["runtime_support_state"], "not_eligible")
        self.assertFalse(request["promotion"]["routing_enabled"])

    def test_registry_extra_root_key_fails_closed(self) -> None:
        registry, projection = success_inputs()
        registry["unexpected"] = False
        with self.assertRaisesRegex(planner.CandidateBatchPlanError, "input_shape_mismatch"):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_candidate_status_drift_fails_closed(self) -> None:
        registry, projection = success_inputs()
        rows = registry["bindings"]
        assert isinstance(rows, list)
        rows[0]["status"] = "verified"
        with self.assertRaisesRegex(
            planner.CandidateBatchPlanError, "candidate_boundary_mismatch"
        ):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_duplicate_candidate_fails_closed(self) -> None:
        registry, projection = success_inputs()
        rows = registry["bindings"]
        assert isinstance(rows, list)
        rows.append(dict(rows[0]))
        with self.assertRaisesRegex(
            planner.CandidateBatchPlanError, "candidate_identity_mismatch"
        ):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_duplicate_action_identifier_fails_closed(self) -> None:
        registry, projection = success_inputs()
        rows = registry["bindings"]
        assert isinstance(rows, list)
        rows[1]["invocation"]["action_id"] = rows[0]["invocation"]["action_id"]
        with self.assertRaisesRegex(
            planner.CandidateBatchPlanError, "candidate_action_id_duplicate"
        ):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_parameter_map_must_remain_pending_and_empty(self) -> None:
        registry, projection = success_inputs()
        rows = registry["bindings"]
        assert isinstance(rows, list)
        rows[2]["invocation"]["parameter_map"] = [{"name": "unsafe"}]
        with self.assertRaisesRegex(
            planner.CandidateBatchPlanError, "candidate_boundary_mismatch"
        ):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_projection_privacy_and_source_hash_are_exact(self) -> None:
        registry, projection = success_inputs()
        projection["source_registry_sha256"] = "9" * 64
        with self.assertRaisesRegex(
            planner.CandidateBatchPlanError, "input_boundary_mismatch"
        ):
            planner.build_request(registry, "a" * 64, projection, "b" * 64)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(planner.CandidateBatchPlanError, "duplicate_json_key"):
            json.loads(
                '{"state":"planned","state":"pass"}',
                object_pairs_hook=planner.reject_duplicate_keys,
            )

    def test_publish_is_create_new_and_hash_bound(self) -> None:
        request = self.build()
        with tempfile.TemporaryDirectory(dir=planner.ROOT / "target") as directory:
            root = Path(directory).resolve()
            with mock.patch.object(planner, "TARGET_ROOT", root):
                output, sha256 = planner.publish_request(
                    "p06-09-table-automation-candidate-6-20991231-99", request
                )
                self.assertEqual(output.name, "request.json")
                self.assertEqual(
                    sha256, hashlib.sha256(output.read_bytes()).hexdigest()
                )
                with self.assertRaisesRegex(
                    planner.CandidateBatchPlanError, "attempt_already_exists"
                ):
                    planner.publish_request(
                        "p06-09-table-automation-candidate-6-20991231-99", request
                    )


if __name__ == "__main__":
    unittest.main()
