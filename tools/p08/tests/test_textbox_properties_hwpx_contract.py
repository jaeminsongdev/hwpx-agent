from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p08 import validate_textbox_properties_hwpx_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT,
        validator.MIGRATION,
        validator.POLICY,
        validator.REPORT,
        validator.QUALIFICATION,
        *validator.SOURCE_SHA256,
        *validator.IMPLEMENTATION_SHA256,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class TextBoxPropertiesHwpxContractTests(unittest.TestCase):
    def test_current_contract_is_integration_only_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 5)
        self.assertEqual(value["implementation_files"], 4)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["direct_stage"], "integration_passed")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["p08_complete"])

    def test_claim_and_gate_promotions_fail_closed(self) -> None:
        cases = [
            (validator.CONTRACT, ["evidence_boundary", "actual_hangul"], True),
            (validator.CONTRACT, ["evidence_boundary", "object_bounds"], True),
            (validator.CONTRACT, ["gate_decision", "current_target"], "pass"),
            (validator.QUALIFICATION, ["claims", "product_complete"], True),
        ]
        for relative, path, replacement in cases:
            with self.subTest(relative=relative, path=path):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    value = json.loads(target.read_text(encoding="utf-8"))
                    cursor = value
                    for key in path[:-1]:
                        cursor = cursor[key]
                    cursor[path[-1]] = replacement
                    target.write_text(json.dumps(value), encoding="utf-8")
                    self.assertEqual(validator.validate(root)["state"], "fail")

    def test_source_implementation_and_marker_drift_fail_closed(self) -> None:
        cases = [
            ("docs/04_feature_catalog/09_obj.md", "source_lock_digest"),
            ("crates/hwpx-package/src/textbox_properties_hwpx.rs", "implementation_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    self.assertIn(expected, validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / "crates/hwpx-package/src/textbox_properties_hwpx.rs"
            target.write_text("drift", encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("implementation_digest", errors)
            self.assertIn("implementation_marker", errors)

    def test_duplicate_json_and_private_path_escape_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P08-13",', '"task": "P08-13",\n  "task": "P08-13",'),
                encoding="utf-8",
            )
            self.assertIn("contract_json_or_path", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            value = json.loads(target.read_text(encoding="utf-8"))
            value["policy"] = "../outside"
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")


if __name__ == "__main__":
    unittest.main()
