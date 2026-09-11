from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import validate_equation_corpus_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT, validator.MIGRATION, validator.POLICY, validator.REPORT,
        validator.QUALIFICATION, validator.MANIFEST, *validator.SOURCES, *validator.MARKERS,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class EquationCorpusContractTests(unittest.TestCase):
    def test_current_contract_is_unit_passed_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 9)
        self.assertEqual(value["implementation_files"], 7)
        self.assertTrue(value["manifest_verified"])
        self.assertTrue(value["target_harness_verified"])
        self.assertEqual(value["tier_b_target"], "not_run")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["render"])
        self.assertFalse(value["product_complete"])

    def test_contract_source_and_qualification_tamper_fail(self) -> None:
        for relative, path, replacement in [
            (validator.CONTRACT, ["gate_decision", "actual_hangul"], True),
            (validator.CONTRACT, ["tier_policy", "minimum_tier_a_semantic"], 1),
            (validator.QUALIFICATION, ["claims", "tier_b_target_complete"], True),
            (validator.QUALIFICATION, ["tier_b_target_execution", "state"], "pass"),
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

    def test_manifest_digest_count_policy_and_duplicate_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.MANIFEST
            target.write_bytes(target.read_bytes() + b" ")
            result = validator.validate(root)
            self.assertIn("manifest_digest", result["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.MANIFEST
            value = json.loads(target.read_text(encoding="utf-8"))
            value["cases"][0]["tier"] = "c"
            target.write_text(json.dumps(value), encoding="utf-8")
            result = validator.validate(root)
            self.assertIn("manifest_case_policy", result["errors"])
            self.assertIn("manifest_counts", result["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.MANIFEST
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"id":"a-002"', '"id":"a-001"'), encoding="utf-8")
            self.assertIn("manifest_case_id", validator.validate(root)["errors"])

    def test_duplicate_json_path_escape_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"task": "P07-08",', '"task": "P07-08",\n  "task": "P07-08",'), encoding="utf-8")
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

    def test_target_harness_raw_source_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.PARENT
            target.write_bytes(target.read_bytes() + b"\n# drift\n")
            result = validator.validate(root)
            self.assertIn("target_harness_digest", result["errors"])


if __name__ == "__main__":
    unittest.main()
