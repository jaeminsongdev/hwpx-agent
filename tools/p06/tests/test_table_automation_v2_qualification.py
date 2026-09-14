from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

from tools.p06 import finalize_table_automation_v2_qualification as finalizer
from tools.p06 import table_conformance as conformance


class TableAutomationV2QualificationTests(unittest.TestCase):
    def test_current_exact_target_bundle_passes_all_61_rows(self) -> None:
        outputs = finalizer.build_outputs()
        receipt = outputs["receipt"]
        self.assertEqual(len(receipt["rows"]), 61)
        self.assertEqual(receipt["summary"]["runtime_verified_current_target"], 61)
        self.assertEqual(receipt["summary"]["differential_exact_match"], 61)
        self.assertEqual(receipt["summary"]["routing_enabled"], 61)
        self.assertEqual(outputs["qualified_overlay"]["runtime_qualification"]["state"], "pass")
        rows = conformance.validate_projection(outputs["projection"])
        self.assertEqual(len(rows), 61)
        self.assertTrue(all(row["routing_enabled"] for row in rows.values()))
        public = conformance.canonical_json(receipt) + conformance.canonical_json(
            outputs["projection"]
        )
        self.assertNotIn(b'"action_id":', public)
        self.assertNotIn(b'"parameter_set_id":', public)
        self.assertNotIn(b':\\\\', public)

    def test_trace_safety_tamper_fails_closed(self) -> None:
        real_load = finalizer._load

        def tampered(root, relative, maximum=32 * 1024 * 1024):
            value, digest = real_load(root, relative, maximum)
            if relative == finalizer.RUNTIME_TRACES[0]:
                value = deepcopy(value)
                value["file_open_or_save_invoked"] = True
            return value, digest

        with patch.object(finalizer, "_load", side_effect=tampered):
            with self.assertRaisesRegex(finalizer.QualificationError, "runtime_trace_safety"):
                finalizer.build_outputs()

    def test_action_identity_tamper_fails_closed(self) -> None:
        real_load = finalizer._load

        def tampered(root, relative, maximum=32 * 1024 * 1024):
            value, digest = real_load(root, relative, maximum)
            if relative == finalizer.CANDIDATE_OVERLAY:
                value = deepcopy(value)
                value["bindings"][0]["invocation"]["action_id"] = "WrongAction"
            return value, digest

        with patch.object(finalizer, "_load", side_effect=tampered):
            with self.assertRaisesRegex(finalizer.QualificationError, "candidate_binding_action"):
                finalizer.build_outputs()

    def test_missing_direct_oracle_fails_closed(self) -> None:
        real_load = finalizer._load

        def tampered(root, relative, maximum=32 * 1024 * 1024):
            value, digest = real_load(root, relative, maximum)
            if relative == finalizer.DIRECT_EVIDENCE:
                value = deepcopy(value)
                value["records"][0]["stage"] = "integration_passed"
            return value, digest

        with patch.object(finalizer, "_load", side_effect=tampered):
            with self.assertRaisesRegex(finalizer.QualificationError, "direct_oracle_state"):
                finalizer.build_outputs()


if __name__ == "__main__":
    unittest.main()
