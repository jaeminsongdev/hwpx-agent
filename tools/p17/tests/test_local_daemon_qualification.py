from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import local_daemon_qualification as qualification  # noqa: E402
from tools.p17 import frozen_local_qualifications_v1 as frozen_local  # noqa: E402


class LocalDaemonQualificationTests(unittest.TestCase):
    def test_checked_in_qualification_is_exact_without_local_receipt(self) -> None:
        contract = frozen_local.verify("local_daemon", qualification.ROOT)
        self.assertEqual(contract["qualification_id"], "p17.local-daemon.v1.20260906")
        self.assertTrue(contract["claims"]["local_daemon"])
        for open_claim in (
            "actual_codex_plugin",
            "persistent_credentials",
            "postgres_lifecycle",
            "actual_hangul",
            "network_used",
            "phase_complete",
        ):
            self.assertFalse(contract["claims"][open_claim])

    def test_locked_sources_are_unique_and_historical(self) -> None:
        contract = frozen_local.verify("local_daemon", qualification.ROOT)
        paths = [
            entry["path"]
            for group in ("runtime_sources", "guard_sources")
            for entry in contract[group]
        ]
        self.assertEqual(len(paths), len(set(paths)))

    def test_receipt_claim_promotion_and_unknown_field_fail_closed(self) -> None:
        receipt = qualification.expected_receipt()
        promoted = copy.deepcopy(receipt)
        promoted["actual_hangul"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.claims"):
            qualification.validate_receipt(promoted)
        expanded = copy.deepcopy(receipt)
        expanded["actual_codex_plugin_id"] = "invented"
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.fields"):
            qualification.validate_receipt(expanded)


if __name__ == "__main__":
    unittest.main()
