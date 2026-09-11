from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p07 import validate_equation_hwpx_contract as validator


class EquationHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_target_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 10)
        self.assertEqual(report["implementation_files"], 9)
        self.assertTrue(report["installed_source_qualified"])
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertTrue(report["synthetic_closed_hwpx"])
        self.assertFalse(report["actual_hangul"])
        self.assertFalse(report["product_complete"])

    def test_source_implementation_migration_and_evidence_tamper_fail(self) -> None:
        for relative, needle, expected in [
            ("implementation/p07/P07-04_EQEDIT_REPORT.md", "\ntamper\n", "source_lock_digest"),
            ("crates/hwpx-package/src/equation.rs", "EquationHwpxLowerer", "implementation_marker"),
            (validator.MIGRATION, "separate P07 Gates", "document_marker"),
        ]:
            with tempfile.TemporaryDirectory() as directory:
                root = self.copy_tree(Path(directory))
                path = root / relative
                text = path.read_text(encoding="utf-8")
                path.write_text(text.replace(needle, "removed") if needle in text else text + needle, encoding="utf-8")
                self.assertIn(expected, validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            path = root / validator.QUALIFICATION
            value = json.loads(path.read_text(encoding="utf-8"))
            value["claims"]["new_lowerer_actual_hangul_execution"] = True
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("qualification_claims", validator.validate(root)["errors"])

    def test_duplicate_key_path_escape_and_binding_weakening_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            path = root / validator.CONTRACT
            original = path.read_text(encoding="utf-8")
            path.write_text(original.replace("{\n", '{"schema_version":"duplicate",\n', 1), encoding="utf-8")
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            path = root / validator.CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["source_locks"][0]["path"] = "../outside"
            value["binding"]["source"] = "selected_section_only"
            value["preservation"]["byte_proof"] = "none"
            path.write_text(json.dumps(value), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("binding", errors)
            self.assertIn("preservation", errors)

    def test_limits_nonclaims_and_gate_promotion_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            path = root / validator.CONTRACT
            value = json.loads(path.read_text(encoding="utf-8"))
            value["default_limits"]["section_bytes"] = 0
            value["native_profile"]["extent"] = "trusted_constant"
            value["not_claimed"]["new_lowerer_actual_hangul_execution"] = True
            value["gate_decision"]["actual_hangul"] = True
            value["failure_policy"].pop()
            path.write_text(json.dumps(value), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for expected in ("default_limits", "native_profile", "not_claimed", "gate_decision", "failure_policy"):
                self.assertIn(expected, errors)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.MIGRATION,
            validator.POLICY,
            validator.REPORT,
            validator.QUALIFICATION,
            *validator.EXPECTED_SOURCE_PATHS,
            *validator.IMPLEMENTATION_MARKERS,
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
