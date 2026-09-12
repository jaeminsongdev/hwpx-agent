from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_field_core_contract as validator


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


class FieldCoreContractTests(unittest.TestCase):
    def test_current_contract_is_ten_capability_unit_pass_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["implementation_files"], 3)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 10)
        self.assertEqual(value["direct_stage"], "unit_passed")
        self.assertEqual(value["direct_hwpx"], "not_run")
        self.assertEqual(value["field_readback"], "not_run")
        self.assertFalse(value["p09_01_green"])
        self.assertFalse(value["product_complete"])

    def test_capability_state_binding_and_failure_policy_tamper_fail_closed(self) -> None:
        cases = [
            (["capability_features", "REF-008"], "ref.field_page_number"),
            (["state_binding", "result_source"], "ambient_values_allowed"),
            (["failure_policy", 6], "locked_update_allowed"),
        ]
        for path, replacement in cases:
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / validator.CONTRACT
                    value = json.loads(target.read_text(encoding="utf-8"))
                    cursor = value
                    for key in path[:-1]:
                        cursor = cursor[key]
                    cursor[path[-1]] = replacement
                    target.write_text(json.dumps(value), encoding="utf-8")
                    self.assertEqual(validator.validate(root)["state"], "fail")

    def test_claim_promotion_and_qualification_tamper_fail_closed(self) -> None:
        cases = [
            (validator.CONTRACT, ["evidence_boundary", "direct_hwpx"], True),
            (validator.CONTRACT, ["gate_decision", "actual_target"], "pass"),
            (validator.QUALIFICATION, ["claims", "p09_complete"], True),
            (validator.QUALIFICATION, ["tests", "licensed_application_used"], True),
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
        cases = [
            ("crates/domain-ir/src/field_engine.rs", "implementation_digest"),
            ("docs/04_feature_catalog/10_ref.md", "source_lock_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    self.assertIn(expected, validator.validate(root)["errors"])

    def test_duplicate_json_path_escape_and_marker_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P09-01",', '"task": "P09-01",\n  "task": "P09-01",'),
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

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            source = root / "crates/domain-ir/src/field_engine.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    'Self::UpdateResult { .. } => "ref.field_update"',
                    'Self::UpdateResult { .. } => "ref.field_lock"',
                ),
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("implementation_digest", errors)


if __name__ == "__main__":
    unittest.main()
