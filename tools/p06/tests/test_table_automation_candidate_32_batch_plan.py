from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.p06 import build_table_automation_binding_overlay as binding_overlay
from tools.p06 import plan_table_automation_candidate_32_batch as planner
from tools.p06 import table_conformance as conformance


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def success_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    expected = {
        feature_id: (capability_id, context)
        for feature_id, capability_id, context in planner.EXPECTED_ROWS
    }
    bindings: list[dict[str, object]] = []
    projection_rows: list[dict[str, object]] = []
    mappings: list[dict[str, object]] = []
    documented = set(list(expected)[:14])

    for number in range(1, 62):
        feature_id = f"TABLE-{number:03d}"
        if feature_id in expected:
            capability_id = expected[feature_id][0]
            parameter_state = (
                "documented_candidate"
                if feature_id in documented
                else "source_declares_none"
            )
            action_id = f"Action{number:03d}"
            parameter_set_id = (
                f"Parameter{number:03d}"
                if parameter_state == "documented_candidate"
                else None
            )
            bindings.append(
                {
                    "binding_key": (
                        f"{capability_id}@hancom-hangul-2020-secondary/"
                        "11.0.0.9136/ko-KR"
                    ),
                    "feature_id": feature_id,
                    "capability_id": capability_id,
                    "status": "candidate_unverified",
                    "runtime_support_state": "unverified",
                    "routing_enabled": False,
                    "raw_identifiers_present": True,
                    "invocation": {
                        "kind": "action",
                        "action_id": action_id,
                        "parameter_set_id": parameter_set_id,
                        "parameter_set_state": parameter_state,
                        "parameter_map_state": "pending_runtime_probe",
                        "parameter_map": [],
                    },
                }
            )
            projection_status = "candidate_unverified"
            mappings.append(
                {
                    "feature_id": feature_id,
                    "capability_id": capability_id,
                    "record_id_sha256": "1" * 64,
                    "node_id_sha256": "2" * 64,
                    "action_identifier_sha256": digest(action_id),
                    "description_sha256": "3" * 64,
                    "parameter_signal_sha256": digest(
                        parameter_set_id if parameter_set_id is not None else "-"
                    ),
                    "parameter_set_state": parameter_state,
                    "locator_sha256": "4" * 64,
                    "record_sha256": "5" * 64,
                }
            )
        else:
            capability_id = f"table.placeholder_{number:03d}"
            projection_status = "unavailable_with_reason"
            bindings.append(
                {
                    "binding_key": (
                        f"{capability_id}@hancom-hangul-2020-secondary/"
                        "11.0.0.9136/ko-KR"
                    ),
                    "feature_id": feature_id,
                    "capability_id": capability_id,
                    "status": "unavailable_with_reason",
                    "runtime_support_state": "unverified",
                    "routing_enabled": False,
                    "raw_identifiers_present": False,
                }
            )
        projection_rows.append(
            {
                "feature_id": feature_id,
                "capability_id": capability_id,
                "binding_status": projection_status,
                "runtime_support_state": "unverified",
                "routing_enabled": False,
            }
        )

    contract: dict[str, object] = {
        "schema_version": binding_overlay.PUBLIC_CONTRACT_SCHEMA,
        "target": {
            **planner.EXPECTED_TARGET,
            "scope": "current_pc_personal_local_development",
        },
        "source_locks": {
            key: str(index) * 64
            for index, key in enumerate(sorted(binding_overlay.SOURCE_LOCK_KEYS), 1)
        },
        "review_policy": {
            "source": "official_action_table_records",
            "match": "exact_unique_action_identifier",
            "composition": "not_admitted",
            "ambiguous_or_partial_matches": "unavailable_with_reason",
        },
        "coverage": {
            "required_rows": 61,
            "candidate_unverified": 32,
            "unavailable_with_reason": 29,
            "runtime_verified": 0,
            "routing_enabled": 0,
        },
        "mappings": mappings,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
            "absolute_private_paths": False,
        },
        "not_claimed": {
            "runtime_qualification": False,
            "routing_support": False,
            "direct_automation_differential": False,
            "p06_09_complete": False,
            "p06_phase_complete": False,
            "product_complete": False,
        },
    }
    contract_sha256 = "c" * 64
    overlay: dict[str, object] = {
        "schema_version": binding_overlay.OVERLAY_SCHEMA,
        "restricted_derivative": True,
        "routing_enabled": False,
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
        "coverage": {
            "required_rows": 61,
            "candidate_unverified": 32,
            "unavailable_with_reason": 29,
        },
        "runtime_qualification": {
            "state": "not_run",
            "verified_current_target": 0,
            "failed_current_target": 0,
        },
        "review_contract_sha256": contract_sha256,
        "bindings": bindings,
    }
    projection: dict[str, object] = {
        "schema_version": conformance.PROJECTION_SCHEMA_VERSION,
        "source_registry_sha256": "a" * 64,
        "target": {
            **planner.EXPECTED_TARGET,
            "scope": "current_pc_personal_local_development",
        },
        "row_count": 61,
        "rows": projection_rows,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
    }
    return overlay, projection, contract


class TableAutomationCandidate32BatchPlanTests(unittest.TestCase):
    def build(self) -> dict[str, object]:
        overlay, projection, contract = success_inputs()
        return planner.build_request(
            overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
        )

    def test_builds_exact_32_in_one_session_without_candidate_execution(self) -> None:
        request = self.build()
        self.assertEqual(request["case_count"], 32)
        self.assertEqual(
            [case["feature_id"] for case in request["cases"]],
            [feature_id for feature_id, _, _ in planner.EXPECTED_ROWS],
        )
        self.assertEqual(
            request["session_strategy"],
            "one_hwp_session_32_isolated_disposable_documents",
        )
        self.assertTrue(
            all(case["execute_candidate_under_probe"] is False for case in request["cases"])
        )
        self.assertEqual(request["fixture_policy"]["blank_document_case_count"], 1)
        self.assertEqual(request["fixture_policy"]["selected_text_case_count"], 1)
        self.assertEqual(request["fixture_policy"]["generated_table_context_case_count"], 30)
        self.assertEqual(request["fixture_policy"]["table_create_fixture_action_execute_count"], 30)
        self.assertFalse(request["fixture_policy"]["fixture_execution_qualifies_runtime"])
        self.assertEqual(request["promotion"]["runtime_support_state"], "not_eligible")
        self.assertFalse(request["promotion"]["routing_enabled"])

    def test_private_overlay_digest_mismatch_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        projection["source_registry_sha256"] = "9" * 64
        with self.assertRaisesRegex(
            planner.Candidate32PlanError, "projection_source_digest_mismatch"
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_contract_digest_mismatch_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        overlay["review_contract_sha256"] = "9" * 64
        with self.assertRaisesRegex(
            planner.Candidate32PlanError, "review_contract_digest_mismatch"
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_action_hash_mismatch_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        contract["mappings"][0]["action_identifier_sha256"] = "9" * 64
        with self.assertRaisesRegex(
            planner.Candidate32PlanError, "candidate_action_identity"
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_parameter_hash_mismatch_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        contract["mappings"][0]["parameter_signal_sha256"] = "9" * 64
        with self.assertRaisesRegex(planner.Candidate32PlanError, "parameter_set_boundary"):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_parameter_state_mismatch_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        contract["mappings"][0]["parameter_set_state"] = "source_declares_none"
        with self.assertRaisesRegex(
            planner.Candidate32PlanError, "candidate_boundary_mismatch"
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_duplicate_candidate_identity_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        overlay["bindings"].append(dict(overlay["bindings"][0]))
        with self.assertRaisesRegex(
            planner.Candidate32PlanError,
            "private_bindings_shape|candidate_identity_mismatch",
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_promoted_runtime_or_routing_fails_closed(self) -> None:
        overlay, projection, contract = success_inputs()
        overlay["bindings"][0]["runtime_support_state"] = "verified"
        overlay["bindings"][0]["routing_enabled"] = True
        with self.assertRaisesRegex(
            planner.Candidate32PlanError,
            "private_all_rows_boundary|candidate_boundary_mismatch",
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_unavailable_row_cannot_hide_runtime_or_routing_promotion(self) -> None:
        overlay, projection, contract = success_inputs()
        overlay["bindings"][-1]["runtime_support_state"] = "verified"
        projection["rows"][-1]["routing_enabled"] = True
        with self.assertRaisesRegex(
            planner.Candidate32PlanError,
            "projection_all_rows_boundary|private_all_rows_boundary",
        ):
            planner.build_request(
                overlay, "a" * 64, projection, "b" * 64, contract, "c" * 64
            )

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(planner.Candidate32PlanError, "duplicate_json_key"):
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
                    "p06-09-table-automation-candidate-32-20991231-99", request
                )
                self.assertEqual(output.name, "request.json")
                self.assertEqual(sha256, hashlib.sha256(output.read_bytes()).hexdigest())
                with self.assertRaisesRegex(
                    planner.Candidate32PlanError, "attempt_already_exists"
                ):
                    planner.publish_request(
                        "p06-09-table-automation-candidate-32-20991231-99", request
                    )


if __name__ == "__main__":
    unittest.main()
