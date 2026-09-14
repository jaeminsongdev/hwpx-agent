from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import validate_equation_differential_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT, validator.MIGRATION, validator.REPORT, validator.ORACLE,
        validator.QUALIFICATION, validator.DIRECT_TARGET, *validator.SOURCES,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class EquationDifferentialContractTests(unittest.TestCase):
    def test_current_contract_passes_eight_matched_cases(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 3)
        self.assertTrue(value["oracle_verified"])
        self.assertTrue(value["qualification_verified"])
        self.assertTrue(value["direct_target_evidence_verified"])
        self.assertEqual(value["matched_cases"], 8)
        self.assertEqual(value["differential"], "pass")
        self.assertTrue(value["actual_hangul"])
        self.assertFalse(value["render"])

    def test_contract_and_qualification_tamper_fail(self) -> None:
        for relative, path, replacement in [
            (validator.CONTRACT, ["gate_decision", "matched_differential"], "not_run"),
            (validator.CONTRACT, ["comparison_policy", "required_cases"], 1),
            (validator.QUALIFICATION, ["comparison", "semantic_equal_count"], 7),
            (validator.QUALIFICATION, ["claims", "actual_hangul"], False),
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

    def test_duplicate_path_escape_and_oracle_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"task": "P07-GATE",', '"task": "P07-GATE",\n  "task": "P07-GATE",'), encoding="utf-8")
            self.assertIn("contract_json_or_path", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            value = json.loads(target.read_text(encoding="utf-8"))
            value["report"] = "../outside"
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.ORACLE
            target.write_bytes(target.read_bytes() + b"\n// drift\n")
            self.assertIn("oracle_digest", validator.validate(root)["errors"])

    def test_direct_target_evidence_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.DIRECT_TARGET
            value = json.loads(target.read_text(encoding="utf-8"))
            value["claims"]["native_semantic_readback"] = False
            target.write_text(json.dumps(value), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertTrue(
                {"direct_target_digest", "direct_target_claims"}.issubset(result["errors"])
            )


if __name__ == "__main__":
    unittest.main()
