from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import current_workspace_source_qualification as qualification  # noqa: E402
from tools.p17 import frozen_current_source_history_v1 as history  # noqa: E402


class CurrentWorkspaceSourceQualificationTests(unittest.TestCase):
    def test_checked_in_contract_is_exact_and_bounded(self) -> None:
        contract = history.verify_version(qualification.ROOT, 20)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v20.20260907",
        )
        self.assertTrue(contract["claims"]["source_qualification_only"])
        self.assertTrue(contract["claims"]["p05_diagnostic_dependencies_bound"])
        self.assertTrue(contract["claims"]["p05_identity_rebinding_sources_bound"])
        self.assertTrue(contract["claims"]["p05_dense_flow_sources_bound"])
        self.assertTrue(contract["claims"]["p05_dense_actual_receipt_bound"])
        self.assertTrue(contract["claims"]["p05_header_footer_failed_attempts_bound"])
        self.assertTrue(
            contract["claims"]["p05_header_footer_numeric_paragraph_id_repair_bound"]
        )
        self.assertTrue(contract["claims"]["p05_vs1_coordinate_gate_sources_bound"])
        self.assertTrue(contract["claims"]["p17_local_conflict_resolver_bound"])
        self.assertTrue(contract["claims"]["p17_stale_head_widget_v2_bound"])
        self.assertTrue(contract["claims"]["p17_remote_sync_mirror_binding_v2_bound"])
        self.assertTrue(
            contract["claims"]["p17_remote_sync_checkpoint_intent_v3_bound"]
        )
        self.assertTrue(contract["claims"]["p17_local_mirror_v5_bound"])
        self.assertTrue(contract["claims"]["p17_checkpoint_service_mapping_v6_bound"])
        self.assertTrue(contract["claims"]["p17_authorized_mirror_admission_v7_bound"])
        self.assertTrue(
            contract["claims"]["p17_authenticated_checkpoint_host_v8_bound"]
        )
        self.assertTrue(contract["claims"]["p17_history_checkpoint_dispatch_v9_bound"])
        self.assertTrue(contract["claims"]["p17_loopback_tcp_transport_v10_bound"])
        self.assertTrue(contract["claims"]["p17_postgres_checkpoint_host_v11_bound"])
        self.assertTrue(contract["claims"]["docs_source_successor_bridge_v13_bound"])
        self.assertTrue(contract["claims"]["ambiguous_source_baseline_guard_v13_bound"])
        self.assertTrue(
            contract["claims"]["telemetry_source_successor_bridge_v14_bound"]
        )
        self.assertTrue(contract["claims"]["frozen_p15_source_contexts_v15_bound"])
        self.assertTrue(
            contract["claims"]["docs_source_only_widget_validation_v16_bound"]
        )
        self.assertTrue(
            contract["claims"]["complete_source_fallback_negative_v17_bound"]
        )
        self.assertTrue(
            contract["claims"]["retention_mirror_source_successor_v18_bound"]
        )
        self.assertTrue(contract["claims"]["p15_auth_source_successor_v19_bound"])
        self.assertTrue(contract["claims"]["p05_current_hangul_gate_sources_v20_bound"])
        self.assertFalse(contract["claims"]["actual_hangul"])
        self.assertFalse(contract["claims"]["phase_complete"])

    def test_successors_are_historical_commit_exact_and_unique(self) -> None:
        successors = history.verified_successors(qualification.ROOT, 20)
        self.assertEqual(len(successors), 25)
        self.assertEqual(
            set(successors), {entry["path"] for entry in qualification.SUCCESSORS}
        )

    def test_implementation_sources_are_exact_base_commit_blobs(self) -> None:
        sources = history.verified_implementation_sources(qualification.ROOT, 20)
        self.assertEqual(len(sources), 118)
        self.assertEqual(
            set(sources),
            {entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES},
        )

    def test_receipt_promotion_and_unknown_path_fail_closed(self) -> None:
        receipt = qualification.expected_receipt()
        promoted = copy.deepcopy(receipt)
        promoted["phase_complete"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.exact"):
            qualification.validate_receipt(promoted)
        expanded = copy.deepcopy(receipt)
        expanded["successors"].append(
            {
                "path": "unknown",
                "accepted_predecessor_sha256s": ["0" * 64],
                "composition_predecessor_sha256": "0" * 64,
                "current_sha256": "1" * 64,
            }
        )
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.exact"):
            qualification.validate_receipt(expanded)


if __name__ == "__main__":
    unittest.main()
