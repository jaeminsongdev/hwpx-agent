from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_merge_split_hwpx_contract as validator


class TableMergeSplitHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_hangul_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 5)
        self.assertEqual(report["implementation_files"], 8)
        self.assertEqual(report["features"], 2)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertFalse(report["actual_hangul"])

    def test_source_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "protocol/private/p06-table-merge-split-v1.json"
            source.write_text(source.read_text(encoding="utf-8") + "drift", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx/merge_split_hwpx.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "fn build_target_edges", "fn removed_build_target_edges"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            catalog = root / "docs/04_feature_catalog/07_table.md"
            catalog.write_text(
                catalog.read_text(encoding="utf-8").replace(
                    "| TABLE-016 | 셀 나누기 | `table.split_cell` |",
                    "| TABLE-016 | 셀 나누기 | `table.merge_cells` |",
                ),
                encoding="utf-8",
            )
            self.assertIn("feature_catalog_mapping", validator.validate(root)["errors"])

    def test_duplicate_and_semantic_tamper_fail_closed(self) -> None:
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
            contract["topology"]["edge_transition"] = "guess_coordinates"
            contract["topology"]["inverse_transition"] = "allow_reverse"
            contract["content_policies"]["merge_first"] = "drop_silently"
            contract["content_policies"]["split_distribute"] = "round_randomly"
            contract["binding"]["publication"] = "return_before_reopen"
            contract["preservation"]["formula"] = "drop_cache"
            contract["preservation"]["package"] = "rewrite_all_parts"
            contract["native_profile"]["split_line"] = "guess_line"
            contract["native_profile"]["formula_readback"] = "enable_mutation"
            contract["receipt"]["debug"] = "raw_ids_hashes_xml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_lock_path", "source_lock_paths_exact", "edge_transition",
                "inverse_transition", "merge_first", "split_distribute", "publication",
                "formula_preservation", "package_preservation", "split_line",
                "formula_boundary", "receipt_debug",
            ):
                self.assertIn(code, errors)

    def test_evidence_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["automation_runtime"] = True
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
