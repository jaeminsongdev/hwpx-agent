from __future__ import annotations

from copy import deepcopy
import unittest

from tools.p06 import build_table_automation_binding_overlay as overlay
from tools.p06 import table_conformance as conformance


class TableAutomationBindingOverlayTests(unittest.TestCase):
    def fixtures(self) -> tuple[dict, list, dict, dict, dict[str, str]]:
        target = {
            "profile_id": conformance.TARGET_PROFILE_ID,
            "product": "Hancom Hangul 2020",
            "exact_build": conformance.TARGET_BUILD,
            "locale": conformance.TARGET_LOCALE,
            "architecture": conformance.TARGET_ARCHITECTURE,
        }
        bindings = []
        for index in range(1, conformance.EXPECTED_FEATURE_COUNT + 1):
            feature_id = f"TABLE-{index:03d}"
            bindings.append(
                {
                    "feature_id": feature_id,
                    "capability_id": f"table.feature_{index:03d}",
                    "target_profile_id": conformance.TARGET_PROFILE_ID,
                    "status": (
                        "candidate_unverified"
                        if index <= 6
                        else "unavailable_with_reason"
                    ),
                    "runtime_support_state": "unverified",
                    "routing_enabled": False,
                    "invocation": None,
                    "raw_identifiers_present": False,
                    "source_refs": [],
                    "unavailable_reason": (
                        None if index <= 6 else "no_reviewed_action_mapping"
                    ),
                }
            )
        parent = {
            "schema_version": "hwpx-agent.automation-binding-registry/v1",
            "target": target,
            "bindings": bindings,
        }
        records = []
        nodes = []
        items = []
        for index in range(1, overlay.EXPECTED_CANDIDATES + 1):
            feature_id = f"TABLE-{index:03d}"
            action_name = f"SyntheticAction{index:03d}"
            record_id = f"synthetic-record-{index:03d}"
            records.append(
                {
                    "source_kind": "action_table",
                    "original_name": action_name,
                    "record_id": record_id,
                    "description_ko": f"synthetic description {index}",
                    "parameters": [{"original_name": "-"}],
                    "locator": {"kind": "synthetic", "value": index},
                    "source_id": "synthetic-source",
                    "source_sha256": "9" * 64,
                }
            )
            nodes.append(
                {
                    "record_id": record_id,
                    "node_id": f"synthetic-node-{index:03d}",
                    "source_kind": "action_table",
                    "source_id": "synthetic-source",
                    "source_sha256": "9" * 64,
                }
            )
            items.append(
                {
                    "feature_id": feature_id,
                    "capability_id": f"table.feature_{index:03d}",
                    "action_name": action_name,
                }
            )
        digests = {
            "parent_registry_sha256": "1" * 64,
            "action_records_sha256": "2" * 64,
            "candidate_graph_sha256": "3" * 64,
            "canonical_matrix_sha256": "4" * 64,
            "private_review_sha256": "5" * 64,
        }
        review = {
            "schema_version": overlay.PRIVATE_REVIEW_SCHEMA,
            "source_locks": {
                key: digests[key]
                for key in (
                    "parent_registry_sha256",
                    "action_records_sha256",
                    "candidate_graph_sha256",
                    "canonical_matrix_sha256",
                )
            },
            "review_policy": {
                "source_kind": "action_table",
                "match": "exact_unique_official_action",
                "composition": "not_admitted",
                "runtime_qualification": "not_run",
                "routing_enabled": False,
            },
            "items": items,
        }
        graph = {
            "schema_version": "hwpx-agent.candidate-graph/v1",
            "nodes": nodes,
        }
        return parent, records, graph, review, digests

    def build(self) -> tuple[dict, dict, dict]:
        parent, records, graph, review, digests = self.fixtures()
        contract, bindings, selected = overlay.build_public_contract(
            parent, records, graph, review, digests
        )
        contract_sha256 = conformance.sha256_bytes(conformance.canonical_json(contract))
        private_overlay = overlay.build_overlay(
            parent, bindings, selected, digests, contract_sha256
        )
        projection = conformance.build_automation_projection(
            private_overlay,
            conformance.sha256_bytes(conformance.canonical_json(private_overlay)),
        )
        return contract, private_overlay, projection

    def test_exact_review_expands_candidates_without_runtime_or_routing_promotion(self) -> None:
        contract, private_overlay, projection = self.build()
        self.assertEqual(contract["coverage"]["candidate_unverified"], 32)
        self.assertEqual(contract["coverage"]["unavailable_with_reason"], 29)
        self.assertEqual(len(private_overlay["bindings"]), 61)
        self.assertEqual(
            sum(row["binding_status"] == "candidate_unverified" for row in projection["rows"]),
            32,
        )
        self.assertEqual(
            sum(
                row["binding_status"] == "unavailable_with_reason"
                for row in projection["rows"]
            ),
            29,
        )
        self.assertTrue(
            all(row["runtime_support_state"] == "unverified" for row in projection["rows"])
        )
        self.assertTrue(all(row["routing_enabled"] is False for row in projection["rows"]))
        self.assertEqual(len(conformance.validate_projection(projection)), 61)
        self.assertEqual(len(overlay.validate_public_contract_shape(contract)), 32)

    def test_public_contract_and_projection_do_not_contain_raw_identifiers(self) -> None:
        contract, _, projection = self.build()
        contract_bytes = conformance.canonical_json(contract)
        projection_bytes = conformance.canonical_json(projection)
        self.assertNotIn(b"SyntheticAction", contract_bytes)
        self.assertNotIn(b"SyntheticAction", projection_bytes)
        self.assertNotIn(b'"action_id":', contract_bytes)
        self.assertNotIn(b'"parameter_set_id":', contract_bytes)
        self.assertNotIn(b'"action_id":', projection_bytes)
        self.assertNotIn(b'"parameter_set_id":', projection_bytes)

    def test_duplicate_official_action_and_promoted_parent_fail_closed(self) -> None:
        parent, records, graph, review, digests = self.fixtures()
        records.append(deepcopy(records[0]))
        with self.assertRaisesRegex(overlay.OverlayError, "official_action_not_unique"):
            overlay.build_public_contract(parent, records, graph, review, digests)

        parent, records, graph, review, digests = self.fixtures()
        parent["bindings"][0]["runtime_support_state"] = "verified_current_target"
        with self.assertRaisesRegex(
            overlay.OverlayError, "parent_runtime_or_routing_promoted"
        ):
            overlay.build_public_contract(parent, records, graph, review, digests)

        parent, records, graph, review, digests = self.fixtures()
        graph["nodes"][0]["source_id"] = "wrong-source"
        with self.assertRaisesRegex(overlay.OverlayError, "candidate_node_source_mismatch"):
            overlay.build_public_contract(parent, records, graph, review, digests)

    def test_review_source_drift_and_candidate_demotion_fail_closed(self) -> None:
        parent, records, graph, review, digests = self.fixtures()
        review["source_locks"]["action_records_sha256"] = "0" * 64
        with self.assertRaisesRegex(overlay.OverlayError, "review_source_locks"):
            overlay.build_public_contract(parent, records, graph, review, digests)

        parent, records, graph, review, digests = self.fixtures()
        review["items"] = review["items"][6:]
        with self.assertRaisesRegex(overlay.OverlayError, "review_count"):
            overlay.build_public_contract(parent, records, graph, review, digests)

        contract, _, _ = self.build()
        contract["mappings"][0]["record_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(overlay.OverlayError, "public_contract_mapping_digest"):
            overlay.validate_public_contract_shape(contract)


if __name__ == "__main__":
    unittest.main()
