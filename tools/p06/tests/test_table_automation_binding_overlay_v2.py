from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.p06 import build_table_automation_binding_overlay_v2 as subject
from tools.p06 import table_conformance as conformance


class TableAutomationBindingOverlayV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[3]
        cls.review, cls.contract, cls.overlay, cls.projection = subject.build_bundle(cls.root)

    def test_complete_candidate_coverage_without_promotion(self) -> None:
        self.assertEqual(len(self.review["items"]), 61)
        self.assertEqual(len(self.contract["mappings"]), 61)
        self.assertEqual(len(self.overlay["bindings"]), 61)
        self.assertEqual(self.contract["coverage"]["candidate_unverified"], 61)
        self.assertEqual(self.contract["coverage"]["unavailable_with_reason"], 0)
        self.assertTrue(
            all(row["status"] == "candidate_unverified" for row in self.overlay["bindings"])
        )
        self.assertTrue(
            all(row["runtime_support_state"] == "unverified" for row in self.overlay["bindings"])
        )
        self.assertTrue(all(row["routing_enabled"] is False for row in self.overlay["bindings"]))

    def test_public_artifacts_are_redacted(self) -> None:
        for value in (self.contract, self.projection):
            serialized = conformance.canonical_json(value)
            self.assertNotIn(b'"action_id"', serialized)
            self.assertNotIn(b'"parameter_set_id"', serialized)
            self.assertNotIn(b"TableCreate", serialized)
            self.assertNotIn(b"TablePropertyDialog", serialized)

    def test_shared_actions_are_explicitly_specialized(self) -> None:
        rows = {row["feature_id"]: row for row in self.review["items"]}
        for feature_id in (
            "TABLE-034",
            "TABLE-037",
            "TABLE-038",
            "TABLE-039",
            "TABLE-042",
        ):
            self.assertEqual(rows[feature_id]["action_name"], "TablePropertyDialog")
            self.assertEqual(rows[feature_id]["mapping_mode"], "reviewed_parameterized_action")

        for feature_id in ("TABLE-022", "TABLE-023", "TABLE-024"):
            self.assertEqual(rows[feature_id]["action_name"], "TableFormula")
            self.assertEqual(
                rows[feature_id]["mapping_mode"],
                "reviewed_parameterized_action",
            )

        self.assertEqual(rows["TABLE-035"]["action_name"], "TableResizeExRight")
        self.assertEqual(rows["TABLE-035"]["mapping_mode"], "reviewed_composite_action")

        self.assertEqual(rows["TABLE-052"]["action_name"], "TableResizeExLeft")
        self.assertEqual(rows["TABLE-053"]["action_name"], "TableResizeExRight")
        self.assertEqual(rows["TABLE-056"]["action_name"], "TableTableToString")
        self.assertEqual(rows["TABLE-056"]["mapping_mode"], "reviewed_composite_action")

        bindings = {row["feature_id"]: row for row in self.overlay["bindings"]}
        self.assertEqual(rows["TABLE-009"]["action_name"], "CellZoneBorderFill")
        self.assertEqual(
            rows["TABLE-009"]["mapping_mode"],
            "reviewed_parameterized_action",
        )
        self.assertEqual(
            bindings["TABLE-042"]["invocation"]["parameter_set_id"],
            "ShapeObject",
        )

    def test_private_review_drift_fails_closed(self) -> None:
        changed = deepcopy(self.review)
        changed["items"][0]["action_name"] = "TamperedAction"
        with self.assertRaisesRegex(subject.OverlayV2Error, "private_review_drift"):
            subject.validate_review(changed, self.review)

    def test_projection_validates_against_conformance_contract(self) -> None:
        rows = conformance.validate_projection(self.projection)
        self.assertEqual(len(rows), 61)
        self.assertTrue(
            all(row["binding_status"] == "candidate_unverified" for row in rows.values())
        )

    def test_write_new_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            subject._write_new(path, {"value": 1})
            with self.assertRaises(FileExistsError):
                subject._write_new(path, {"value": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"value": 1})


if __name__ == "__main__":
    unittest.main()
