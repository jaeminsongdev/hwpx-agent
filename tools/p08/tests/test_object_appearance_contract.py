from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p08 import validate_object_appearance_contract as validator


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


class ObjectAppearanceContractTests(unittest.TestCase):
    def test_current_contract_is_component_pass_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 9)
        self.assertEqual(value["implementation_files"], 6)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["static_appearance"], "pass")
        self.assertEqual(value["synthetic_section_roundtrip"], "pass")
        self.assertEqual(value["actual_target_hwpx"], "not_run")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["visual_diff"])
        self.assertFalse(value["render"])
        self.assertFalse(value["p08_05_complete"])
        self.assertFalse(value["product_complete"])

    def test_promotion_scope_weakening_and_resource_overclaim_fail(self) -> None:
        cases = [
            (validator.CONTRACT, ["gate_decision", "actual_hangul"], True),
            (validator.CONTRACT, ["not_claimed", "package_image_fill_resource_integrity"], True),
            (validator.CONTRACT, ["failure_policy", 12], "resource_integrity_pass"),
            (validator.QUALIFICATION, ["target_execution", "state"], "pass"),
            (validator.QUALIFICATION, ["claims", "p08_05_complete"], True),
            (validator.QUALIFICATION, ["claims", "visual_diff"], True),
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
            ("crates/domain-ir/src/object_appearance.rs", "implementation_digest"),
            ("docs/04_feature_catalog/contracts/09_obj_contracts.md", "source_lock_digest"),
        ]:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    self.assertIn(expected, validator.validate(root)["errors"])

    def test_duplicate_json_path_escape_marker_and_evidence_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P08-05",', '"task": "P08-05",\n  "task": "P08-05",'),
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
            target = root / "crates/hwpx-package/src/object_appearance_hwpx.rs"
            target.write_text("drift", encoding="utf-8")
            result = validator.validate(root)
            self.assertIn("implementation_digest", result["errors"])
            self.assertIn("implementation_marker", result["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            evidence = root / validator.QUALIFICATION
            value = json.loads(evidence.read_text(encoding="utf-8"))
            value["claims"]["synthetic_section_roundtrip"] = False
            evidence.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")


if __name__ == "__main__":
    unittest.main()
