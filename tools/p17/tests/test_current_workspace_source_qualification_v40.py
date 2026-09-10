from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v40 as qualification


class CurrentWorkspaceSourceQualificationV40Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"], "p17.current-workspace-source.v40.20260910"
        )
        claims = contract["claims"]
        self.assertTrue(claims["p17_git_mirror_component_source_bound"])
        self.assertTrue(claims["p17_git_mirror_durable_plan_source_bound"])
        self.assertTrue(claims["p17_git_mirror_contract_and_tamper_tests_source_bound"])
        self.assertFalse(claims["p17_git_mirror_authenticated_dispatch_verified"])
        self.assertFalse(claims["p17_git_mirror_postgresql_state_machine_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["product_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 9)
        self.assertIn("crates/remote-sync-host/src/git_mirror.rs", paths)
        self.assertIn("crates/remote-sync-host/tests/git_mirror_effect.rs", paths)
        self.assertIn("protocol/private/p17-git-mirror-effect-v1.json", paths)
        self.assertIn("tools/p17/validate_git_mirror_effect_contract.py", paths)
        self.assertIn("implementation/p17/P17-06_GIT_MIRROR_EFFECT_V13.md", paths)

    def test_predecessor_is_exact_v39_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "544c68cdea536e234139bd492f7e2812fe1b7ab02826af580f307284835f287c",
        )

    def test_successor_set_is_exact_v39_delta(self) -> None:
        paths = [entry["path"] for entry in qualification.SUCCESSORS]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 28)
        self.assertEqual(paths, sorted(paths))
        self.assertIn("tools/p14/validate_artifact_service_migration.py", paths)
        self.assertIn("tools/p14/validate_cancel_cleanup.py", paths)
        receipt = qualification.foundation.load_document(
            qualification.receipt_path(qualification.ROOT), "receipt"
        )
        self.assertEqual(receipt["successors"], list(qualification.SUCCESSORS))

    def test_receipt_claim_and_successor_drift_fail_closed(self) -> None:
        receipt = qualification.foundation.load_document(
            qualification.receipt_path(qualification.ROOT), "receipt"
        )
        mutated_claim = copy.deepcopy(receipt)
        mutated_claim["actual_hangul"] = True
        with self.assertRaises(qualification.foundation.QualificationError):
            qualification.validate_receipt(mutated_claim)

        mutated_successor = copy.deepcopy(receipt)
        mutated_successor["successors"][0]["current_sha256"] = "0" * 64
        with self.assertRaises(qualification.foundation.QualificationError):
            qualification.validate_receipt(mutated_successor)


if __name__ == "__main__":
    unittest.main()
