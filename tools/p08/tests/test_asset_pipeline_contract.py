from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p08 import validate_asset_pipeline_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT,
        validator.MIGRATION,
        validator.POLICY,
        validator.REPORT,
        validator.QUALIFICATION,
        *validator.SOURCES,
        *validator.MARKERS,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class AssetPipelineContractTests(unittest.TestCase):
    def test_current_contract_is_component_pass_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 8)
        self.assertEqual(value["implementation_files"], 6)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["direct_stage"], "unit_passed")
        self.assertEqual(value["asset_target"], "not_run")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["render"])
        self.assertFalse(value["product_complete"])

    def test_contract_or_qualification_promotion_and_policy_tamper_fail(self) -> None:
        cases = [
            (validator.CONTRACT, ["gate_decision", "actual_hangul"], True),
            (validator.CONTRACT, ["not_claimed", "pixel_decode"], True),
            (validator.CONTRACT, ["failure_policy", 2], "declared_media_optional"),
            (validator.QUALIFICATION, ["target_execution", "state"], "pass"),
            (validator.QUALIFICATION, ["claims", "render"], True),
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

    def test_implementation_and_authoritative_source_drift_fail_exact_locks(self) -> None:
        for relative, expected in [
            ("crates/hwpx-package/src/asset.rs", "implementation_digest"),
            ("docs/03_document_model/08_drawing_image_chart.md", "source_lock_digest"),
        ]:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    self.assertIn(expected, validator.validate(root)["errors"])

    def test_duplicate_json_path_escape_and_marker_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P08-01",', '"task": "P08-01",\n  "task": "P08-01",'),
                encoding="utf-8",
            )
            self.assertIn("contract_json_or_path", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            contract = root / validator.CONTRACT
            value = json.loads(contract.read_text(encoding="utf-8"))
            value["policy"] = "../outside"
            contract.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / "crates/hwpx-package/src/asset.rs"
            target.write_text("drift", encoding="utf-8")
            result = validator.validate(root)
            self.assertIn("implementation_digest", result["errors"])
            self.assertIn("implementation_marker", result["errors"])


if __name__ == "__main__":
    unittest.main()
