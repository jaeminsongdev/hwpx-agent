from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p08 import validate_object_remainder_contract as validator


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


class ObjectRemainderContractTests(unittest.TestCase):
    def test_current_contract_is_fourteen_capability_unit_pass_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 6)
        self.assertEqual(value["implementation_files"], 9)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 14)
        self.assertEqual(value["direct_stage"], "unit_passed")
        self.assertEqual(value["direct_hwpx"], "not_run")
        self.assertEqual(value["actual_hangul"], "not_run")
        self.assertFalse(value["p08_10_green"])
        self.assertFalse(value["product_complete"])

    def test_capability_or_model_mapping_tamper_fails_closed(self) -> None:
        cases = [
            (["capability_features", "OBJ-042"], "obj.shape_insert"),
            (["models", "hwpx-agent.shape-points/v1"], ["OBJ-042"]),
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

    def test_claim_promotion_and_failure_policy_weakening_fail_closed(self) -> None:
        cases = [
            (validator.CONTRACT, ["evidence_boundary", "actual_hwpx"], True),
            (validator.CONTRACT, ["gate_decision", "actual_target"], "pass"),
            (validator.CONTRACT, ["failure_policy", 10], "source_drift_ignored"),
            (validator.QUALIFICATION, ["claims", "p08_10_green"], True),
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
            ("crates/domain-ir/src/object_special.rs", "implementation_digest"),
            ("docs/04_feature_catalog/contracts/09_obj_contracts.md", "source_lock_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    self.assertIn(expected, validator.validate(root)["errors"])

    def test_duplicate_json_path_escape_marker_and_qualification_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P08-10",', '"task": "P08-10",\n  "task": "P08-10",'),
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
            source = root / "crates/domain-ir/src/basic_shape.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    'Self::Freeform { .. } => "obj.freeform"',
                    'Self::Freeform { .. } => "obj.shape_insert"',
                ),
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("implementation_digest", errors)
            self.assertIn("implementation_marker", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            evidence = root / validator.QUALIFICATION
            value = json.loads(evidence.read_text(encoding="utf-8"))
            value["implementation_sha256"]["crates/domain-ir/src/shape_points.rs"] = "0" * 64
            evidence.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("qualification_implementation", validator.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
