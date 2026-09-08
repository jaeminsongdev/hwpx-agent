from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_ruling_hwpx_contract as validator


class TableRulingHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_hangul_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 5)
        self.assertEqual(report["implementation_files"], 6)
        self.assertEqual(report["features"], 2)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertFalse(report["actual_hangul"])

    def test_source_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "protocol/private/p06-table-ruling-v1.json"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "fn validate_outer_plan", "fn removed_validate_outer_plan"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_duplicate_key_mapping_and_preservation_tamper_fail_closed(self) -> None:
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
            contract["native_mapping"]["grid_topology"] = "best_effort"
            contract["native_mapping"]["outer_creation"] = "insert_anywhere"
            contract["lowering"]["existing_precondition"] = "trust_caller"
            contract["lowering"]["publication"] = "return_before_readback"
            contract["preservation"]["formula"] = "drop_cache"
            contract["preservation"]["unselected_section"] = "rewrite_all"
            contract["representability"]["cell_side"] = "pick_first"
            contract["representability"]["structural_formula"] = "guess"
            contract["receipt"]["debug"] = "raw_xml_and_hashes"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("native_grid_topology", errors)
            self.assertIn("native_outer_creation", errors)
            self.assertIn("lowering_existing_precondition", errors)
            self.assertIn("lowering_publication", errors)
            self.assertIn("preservation_formula", errors)
            self.assertIn("preservation_unselected_section", errors)
            self.assertIn("representability_cell_side", errors)
            self.assertIn("representability_structural_formula", errors)
            self.assertIn("receipt_debug", errors)

    def test_evidence_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["structural_formula_native_lowering"] = True
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
