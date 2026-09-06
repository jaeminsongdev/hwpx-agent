from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import widget_plugin_prepare_qualification as qualification  # noqa: E402


class WidgetPluginPrepareQualificationTests(unittest.TestCase):
    def test_checked_in_qualification_is_exact_without_ignored_receipt(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.widget-plugin-prepare.v1.20260906",
        )
        self.assertTrue(contract["claims"]["actual_codex_plugin"])
        self.assertTrue(contract["claims"]["actual_read_only_prepare"])
        self.assertFalse(contract["claims"]["actual_trusted_ui"])
        self.assertFalse(contract["claims"]["actual_git_effect"])
        self.assertFalse(contract["claims"]["phase_complete"])

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
        receipt = qualification.expected_receipt()
        promoted = copy.deepcopy(receipt)
        promoted["actual_trusted_ui"] = True
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.claims"):
            qualification.validate_receipt(promoted)
        expanded = copy.deepcopy(receipt)
        expanded["confirmation_token"] = "invented"
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.fields"):
            qualification.validate_receipt(expanded)


if __name__ == "__main__":
    unittest.main()
