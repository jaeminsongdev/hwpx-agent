from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p07 import validate_latex_adapter_contract as validator


class LatexAdapterContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_native_or_target_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 6)
        self.assertEqual(report["implementation_files"], 8)
        self.assertEqual(report["task"], "P07-02")
        self.assertEqual(report["direct_stage"], "unit_passed")
        self.assertFalse(report["actual_hwpx"])
        self.assertFalse(report["actual_hangul"])
        self.assertFalse(report["product_complete"])

    def test_source_implementation_and_migration_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "docs/03_document_model/07_equation_model.md"
            source.write_text(source.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            implementation = root / "crates/equation-engine/src/latex.rs"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace(
                    "fn expand_sequence", "fn weakened_expansion"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            (root / validator.MIGRATION).write_text("removed", encoding="utf-8")
            self.assertIn("migration_marker", validator.validate(root)["errors"])

    def test_duplicate_key_path_escape_and_ambiguity_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{"schema_version":"duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract["ambiguity"]["automatic_selection"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("ambiguity", errors)

    def test_limits_nonclaims_and_failure_policy_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["default_limits"]["expanded_tokens"] = 0
            contract["not_claimed"]["hancom_2020_target_build"] = True
            contract["failure_policy"].pop()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("default_limits", errors)
            self.assertIn("not_claimed", errors)
            self.assertIn("failure_policy", errors)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.MIGRATION,
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
