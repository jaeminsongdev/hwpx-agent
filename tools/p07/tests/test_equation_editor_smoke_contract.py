from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import validate_equation_editor_smoke_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT, validator.MIGRATION, validator.POLICY, validator.REPORT,
        validator.QUALIFICATION, *validator.SOURCES, *validator.MARKERS,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class EquationEditorSmokeContractTests(unittest.TestCase):
    def test_current_contract_is_implementation_ready_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 9)
        self.assertEqual(value["implementation_files"], 9)
        self.assertTrue(value["harness_sources_verified"])
        self.assertEqual(value["editor_target"], "not_run")
        self.assertFalse(value["actual_hangul"])
        self.assertFalse(value["save_reopen"])
        self.assertFalse(value["render"])
        self.assertFalse(value["product_complete"])

    def test_contract_and_source_qualification_promotion_tamper_fail(self) -> None:
        for relative, path, replacement in [
            (validator.CONTRACT, ["gate_decision", "actual_hangul"], True),
            (validator.CONTRACT, ["workflow", "computer_use"], "automatic_clicks"),
            (validator.QUALIFICATION, ["claims", "target_editor_smoke"], True),
            (validator.QUALIFICATION, ["target_execution", "state"], "pass"),
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

    def test_harness_or_oracle_source_tamper_fails_exact_raw_lock(self) -> None:
        for relative in [validator.PARENT, validator.CHILD, validator.TARGET_ORACLE]:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_tree(root)
                    target = root / relative
                    target.write_bytes(target.read_bytes() + b" ")
                    result = validator.validate(root)
                    self.assertEqual(result["state"], "fail")
                    self.assertIn("harness_digest", result["errors"])

    def test_duplicate_json_path_escape_and_implementation_marker_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"task": "P07-09",', '"task": "P07-09",\n  "task": "P07-09",'), encoding="utf-8")
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
            target = root / "crates/equation-engine/src/editor_smoke.rs"
            target.write_text("drift", encoding="utf-8")
            self.assertIn("implementation_marker", validator.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
