from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import validate_equation_automation_contract as validator


def copy_contract_tree(destination: Path) -> None:
    for relative in {
        validator.CONTRACT,
        validator.MIGRATION,
        validator.POLICY,
        validator.REPORT,
        validator.QUALIFICATION,
        validator.TARGET_EVIDENCE,
        "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
        *validator.EXPECTED_SOURCE_PATHS,
        *validator.IMPLEMENTATION_MARKERS,
    }:
        source = validator.ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class EquationAutomationContractTests(unittest.TestCase):
    def test_current_contract_passes(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "pass", result)
        self.assertEqual(result["source_locks"], 9)
        self.assertEqual(result["implementation_files"], 12)
        self.assertTrue(result["installed_source_qualified"])
        self.assertTrue(result["target_evidence_verified"])
        self.assertTrue(result["actual_hangul"])
        self.assertFalse(result["render"])
        self.assertFalse(result["product_complete"])

    def test_contract_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_contract_tree(root)
            path = root / validator.CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["gate_decision"]["render"] = True
            path.write_text(json.dumps(value), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("gate_decision", result["errors"])

    def test_source_and_target_tamper_fail(self) -> None:
        for relative, mutate in [
            (
                validator.QUALIFICATION,
                lambda value: value["p02_registry_boundary"].update({"routing_enabled": True}),
            ),
            (
                validator.TARGET_EVIDENCE,
                lambda value: value["claims"].update({"differential": True}),
            ),
            (
                validator.TARGET_EVIDENCE,
                lambda value: value["runtime"]["phases"].update({"edit_execute": "failed"}),
            ),
        ]:
            with self.subTest(relative=relative, mutation=mutate):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_contract_tree(root)
                    path = root / relative
                    value = json.loads(path.read_text(encoding="utf-8"))
                    mutate(value)
                    path.write_text(json.dumps(value), encoding="utf-8")
                    self.assertEqual(validator.validate(root)["state"], "fail")

    def test_duplicate_json_and_raw_action_leak_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_contract_tree(root)
            path = root / validator.CONTRACT
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace('"task": "P07-06",', '"task": "P07-06",\n  "task": "P07-06",'), encoding="utf-8")
            self.assertIn("contract_json_or_path", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_contract_tree(root)
            _, records = validator.probe_builder.load_source_records(
                root / "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
                validator.probe_builder.EXPECTED_SOURCE_RECORDS_SHA256,
            )
            binding = validator.probe_builder.resolve_bindings(records)
            leaked = next(iter(binding["actions"].values()))["action_id"]
            path = root / validator.REPORT
            path.write_text(path.read_text(encoding="utf-8") + "\n" + leaked, encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("public_raw_action_identifier", result["errors"])

    def test_failed_evidence_cannot_be_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_contract_tree(root)
            path = root / validator.TARGET_EVIDENCE
            value = json.loads(path.read_text(encoding="utf-8"))
            changed = copy.deepcopy(value)
            changed["diagnostic_history"][0]["failed_evidence_promoted"] = True
            path.write_text(json.dumps(changed), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("target_evidence_diagnostic", result["errors"])


if __name__ == "__main__":
    unittest.main()
