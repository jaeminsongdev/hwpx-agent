from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import postgres_checkpoint_host_qualification as qualification  # noqa: E402


class PostgresCheckpointHostQualificationTests(unittest.TestCase):
    def test_checked_in_qualification_is_exact(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.postgres-checkpoint-host.v1.20260907",
        )
        self.assertTrue(contract["claims"]["actual_current_pc_disposable_postgresql"])
        self.assertTrue(contract["claims"]["actual_exact_checkpoint_replay"])
        self.assertFalse(contract["claims"]["atomic_mirror_admission_and_checkpoint"])
        self.assertFalse(contract["claims"]["actual_pull_or_push"])
        self.assertFalse(contract["claims"]["production"])
        self.assertFalse(contract["claims"]["p17_06_complete"])

    def test_locked_sources_are_unique_and_current(self) -> None:
        contract = qualification.verify()
        paths: list[str] = []
        for group in ("runtime_sources", "guard_sources"):
            for entry in contract[group]:
                path = qualification.ROOT / entry["path"]
                self.assertEqual(path.stat().st_size, entry["bytes"], entry["path"])
                self.assertEqual(
                    qualification.digest(path), entry["sha256"], entry["path"]
                )
                paths.append(entry["path"])
        self.assertEqual(len(paths), len(set(paths)))

    def test_receipt_promotion_and_unknown_field_fail_closed(self) -> None:
        receipt = qualification.load_document(
            qualification.receipt_path(qualification.ROOT),
            "receipt",
            canonical_only=False,
        )
        promoted = copy.deepcopy(receipt)
        promoted["actual_hangul"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.hangul"):
            qualification.validate_receipt(promoted)
        expanded = copy.deepcopy(receipt)
        expanded["authorization"] = "invented"
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.fields"):
            qualification.validate_receipt(expanded)

    def test_receipt_source_drift_fails_closed(self) -> None:
        receipt = qualification.load_document(
            qualification.receipt_path(qualification.ROOT),
            "receipt",
            canonical_only=False,
        )
        drifted = copy.deepcopy(receipt)
        drifted["source_sha256"]["harness"] = "0" * 64
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.sources"):
            qualification.validate_receipt(drifted)


if __name__ == "__main__":
    unittest.main()
