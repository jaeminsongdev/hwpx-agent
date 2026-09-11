from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import validate_equation_layout_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT, validator.MIGRATION, validator.POLICY, validator.REPORT,
        validator.QUALIFICATION, validator.CALIBRATION_MANIFEST,
        *validator.SOURCES, *validator.MARKERS,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class EquationLayoutContractTests(unittest.TestCase):
    def test_current_contract_is_unit_passed_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 9)
        self.assertEqual(value["implementation_files"], 12)
        self.assertTrue(value["calibration_manifest_verified"])
        self.assertTrue(value["target_toolchain_verified"])
        self.assertEqual(value["direct_stage"], "unit_passed")
        self.assertEqual(value["target_qualification"], "not_run")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["render"])
        self.assertFalse(value["product_complete"])

    def test_contract_and_source_tamper_fail(self) -> None:
        for relative, path, replacement in [
            (validator.CONTRACT, ["gate_decision", "render"], True),
            (validator.CONTRACT, ["qualification", "minimum_inline_samples"], 1),
            (validator.CONTRACT, ["target_toolchain", "manual_review_schema_version"], "forged"),
            (validator.QUALIFICATION, ["claims", "verified_estimator_active"], True),
            (validator.QUALIFICATION, ["dedicated_target_calibration", "state"], "pass"),
        ]:
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

    def test_duplicate_json_path_escape_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"task": "P07-07",', '"task": "P07-07",\n  "task": "P07-07",'), encoding="utf-8")
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
            target = root / next(iter(validator.MARKERS))
            target.write_text("drift", encoding="utf-8")
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_manifest_and_target_toolchain_raw_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CALIBRATION_MANIFEST
            target.write_bytes(target.read_bytes() + b" ")
            self.assertIn("calibration_manifest_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.PARENT
            target.write_bytes(target.read_bytes() + b"\n# drift\n")
            self.assertIn("target_toolchain_digest", validator.validate(root)["errors"])

    def test_visual_nonclaim_cannot_be_promoted_by_filling_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.QUALIFICATION
            value = json.loads(target.read_text(encoding="utf-8"))
            value["dedicated_target_calibration"]["qualification_sha256"] = "a" * 64
            target.write_text(json.dumps(value), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("qualification_target_run", result["errors"])


if __name__ == "__main__":
    unittest.main()
