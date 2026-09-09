from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_absolute_reference_hwpx_contract as validator


class TableAbsoluteReferenceHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_hangul_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 5)
        self.assertEqual(report["implementation_files"], 7)
        self.assertEqual(report["features"], 1)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertFalse(report["actual_hangul"])
        self.assertFalse(report["product_complete"])

    def test_source_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "protocol/private/p06-table-formula-v1.json"
            source.write_text(source.read_text(encoding="utf-8") + "drift", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = (
                root
                / "crates/hwpx-package/src/table_ruling_hwpx/formula_reference_hwpx.rs"
            )
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "fn reference_upgrade_count", "fn removed_reference_upgrade_count"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_duplicate_path_and_semantic_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{\n  "schema_version": "duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract["input"]["profile"] = "one_formula_only"
            contract["transformation"]["formula"] = "change_coordinates"
            contract["transformation"]["cache"] = "mark_verified"
            contract["transformation"]["other_formulas"] = "rewrite_all"
            contract["lowering"]["precondition"] = "trust_caller"
            contract["lowering"]["edit_scope"] = "whole_section"
            contract["lowering"]["publication"] = "return_before_reopen"
            contract["preservation"]["document"] = "drop_caption"
            contract["receipt"]["debug"] = "raw_formula_and_cache"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_lock_path",
                "source_lock_paths_exact",
                "input_profile",
                "transition_formula",
                "transition_cache",
                "other_formulas",
                "lowering_precondition",
                "lowering_edit_scope",
                "lowering_publication",
                "preservation_document",
                "receipt_debug",
            ):
                self.assertIn(code, errors)

    def test_evidence_nonclaim_failure_policy_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["verified_formula_cache"] = True
            contract["failure_policy"].pop()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            migration = root / validator.MIGRATION
            migration.write_text(
                migration.read_text(encoding="utf-8").replace(
                    "may not promote", "may promote"
                ),
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("expected_evidence", errors)
            self.assertIn("not_claimed", errors)
            self.assertIn("failure_policy", errors)
            self.assertIn("migration_marker", errors)

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
