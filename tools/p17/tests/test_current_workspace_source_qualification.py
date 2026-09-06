from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import current_workspace_source_qualification as qualification  # noqa: E402


class CurrentWorkspaceSourceQualificationTests(unittest.TestCase):
    def test_checked_in_contract_is_exact_and_bounded(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v10.20260906",
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
        self.assertTrue(
            contract["claims"]["p17_remote_sync_mirror_binding_v2_bound"]
        )
        self.assertTrue(
            contract["claims"]["p17_remote_sync_checkpoint_intent_v3_bound"]
        )
        self.assertTrue(contract["claims"]["p17_local_mirror_v5_bound"])
        self.assertFalse(contract["claims"]["actual_hangul"])
        self.assertFalse(contract["claims"]["phase_complete"])

    def test_successors_are_current_commit_exact_and_unique(self) -> None:
        successors = qualification.verified_successors()
        self.assertEqual(len(successors), 14)
        self.assertEqual(set(successors), {entry["path"] for entry in qualification.SUCCESSORS})
        for relative, entry in successors.items():
            self.assertEqual(
                qualification.digest(qualification.acceptance.bounded_file(qualification.ROOT, relative)),
                entry["current_sha256"],
            )
            self.assertEqual(
                qualification.git_digest(qualification.ROOT, qualification.BASE_COMMIT, relative),
                entry["current_sha256"],
            )

    def test_implementation_sources_are_exact_base_commit_blobs(self) -> None:
        sources = qualification.verified_implementation_sources()
        self.assertEqual(len(sources), 60)
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
