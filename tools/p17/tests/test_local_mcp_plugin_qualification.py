from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import local_mcp_plugin_qualification as qualification  # noqa: E402
from tools.p17 import frozen_local_qualifications_v1 as frozen_local  # noqa: E402


class LocalMcpPluginQualificationTests(unittest.TestCase):
    def test_checked_in_qualification_is_exact_without_ignored_receipts(self) -> None:
        contract = frozen_local.verify("local_mcp_plugin", qualification.ROOT)
        self.assertEqual(
            contract["qualification_id"], "p17.local-mcp-plugin.v1.20260906"
        )
        self.assertTrue(contract["claims"]["actual_codex_plugin"])
        self.assertTrue(contract["claims"]["actual_codex_health_call"])
        for open_claim in (
            "persistent_credentials",
            "postgres_lifecycle",
            "actual_hangul",
            "product_network_enabled",
            "phase_complete",
        ):
            self.assertFalse(contract["claims"][open_claim])

    def test_locked_sources_are_unique_and_historical(self) -> None:
        contract = frozen_local.verify("local_mcp_plugin", qualification.ROOT)
        paths = [
            entry["path"]
            for group in ("runtime_sources", "guard_sources")
            for entry in contract[group]
        ]
        self.assertEqual(len(paths), len(set(paths)))

    def test_receipt_promotion_and_unknown_fields_fail_closed(self) -> None:
        plugin = qualification.expected_plugin_receipt()
        promoted = copy.deepcopy(plugin)
        promoted["actual_hangul"] = True
        with self.assertRaisesRegex(
            qualification.QualificationError, "plugin_receipt.claims"
        ):
            qualification.validate_receipt(promoted, plugin, "plugin_receipt")
        expanded = copy.deepcopy(plugin)
        expanded["installed_path"] = "invented"
        with self.assertRaisesRegex(
            qualification.QualificationError, "plugin_receipt.fields"
        ):
            qualification.validate_receipt(expanded, plugin, "plugin_receipt")


if __name__ == "__main__":
    unittest.main()
