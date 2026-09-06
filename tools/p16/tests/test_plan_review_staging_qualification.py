from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import plan_review_staging_qualification as qualification  # noqa: E402


class PlanReviewStagingQualificationTests(unittest.TestCase):
    def test_checked_in_qualification_is_exact(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"], "p16.plan-review-host.v14.20260906.v1"
        )
        self.assertTrue(contract["claims"]["dedicated_local_mcp_host_registered"])
        for open_claim in (
            "actual_codex_app_installation",
            "actual_hangul",
            "production",
            "phase_complete",
        ):
            self.assertFalse(contract["claims"][open_claim])

    def test_every_locked_source_is_current_and_unique(self) -> None:
        contract = qualification.verify()
        paths: list[str] = []
        for group in ("runtime_sources", "guard_sources"):
            for locked in contract[group]:
                path = qualification.ROOT / locked["path"]
                self.assertTrue(path.is_file(), locked["path"])
                self.assertEqual(path.stat().st_size, locked["bytes"], locked["path"])
                self.assertEqual(qualification.digest(path), locked["sha256"], locked["path"])
                paths.append(locked["path"])
        self.assertEqual(len(paths), len(set(paths)))

    def test_receipt_claim_promotion_and_unknown_fields_fail_closed(self) -> None:
        current_path = qualification.QUALIFICATION / "current-host.json"
        current = qualification.json.loads(current_path.read_text(encoding="utf-8"))
        receipt = self.receipt_from_current(current)
        promoted = copy.deepcopy(receipt)
        promoted["actual_hangul"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.claims"):
            qualification.validated_receipt(promoted, current["run_id"])
        expanded = copy.deepcopy(receipt)
        expanded["actual_codex_app_installation"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.exact"):
            qualification.validated_receipt(expanded, current["run_id"])

    def test_observation_drift_fails_closed(self) -> None:
        current_path = qualification.QUALIFICATION / "current-host.json"
        current = qualification.json.loads(current_path.read_text(encoding="utf-8"))
        receipt = self.receipt_from_current(current)
        drifted = copy.deepcopy(receipt)
        drifted["observations"]["restart_snapshot_equal"] = False
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.observations"):
            qualification.validated_receipt(drifted, current["run_id"])

    def test_receipt_digest_is_frozen(self) -> None:
        current_path = qualification.QUALIFICATION / "current-host.json"
        current = qualification.json.loads(current_path.read_text(encoding="utf-8"))
        self.assertEqual(current["receipt"]["sha256"], qualification.RECEIPT_SHA256)

    @staticmethod
    def receipt_from_current(current: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "hwpx-agent.p16-plan-review-staging-check/v1",
            "run_id": qualification.RUN_ID,
            "scope": current["scope"],
            "checks": current["checks"],
            "check_count": current["check_count"],
            "passed": True,
            "qualifying": True,
            "decision": "PASS",
            "tracked_clean": True,
            "resources_cleaned": True,
            "actual_hangul": False,
            "p15_catalog_modified": False,
            "p15_catalog_sha256": qualification.P15_CATALOG_SHA256,
            "failed_stage": None,
            "failure": None,
            "source_commit": qualification.BASE_COMMIT,
            "observations": current["observations"],
        }


if __name__ == "__main__":
    unittest.main()
