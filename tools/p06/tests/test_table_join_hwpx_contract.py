from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_join_hwpx_contract as validator


class TableJoinHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_hangul_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 5)
        self.assertEqual(report["implementation_files"], 8)
        self.assertEqual(report["features"], 1)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertFalse(report["actual_hangul"])

    def test_source_implementation_and_catalog_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "protocol/private/p06-table-partition-v1.json"
            source.write_text(source.read_text(encoding="utf-8") + "drift", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx/partition_hwpx.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "fn render_join_section", "fn removed_render_join_section"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            catalog = root / "docs/04_feature_catalog/07_table.md"
            catalog.write_text(
                catalog.read_text(encoding="utf-8").replace(
                    "| TABLE-011 | 표 붙이기 | `table.join_table` |",
                    "| TABLE-011 | 표 붙이기 | `table.split_table` |",
                ),
                encoding="utf-8",
            )
            self.assertIn("feature_catalog_mapping", validator.validate(root)["errors"])

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
            contract["join"]["separator"] = "any_content"
            contract["join"]["lattice"] = "round_each_width"
            contract["join"]["junction"] = "drop_one_edge"
            contract["binding"]["publication"] = "return_before_reopen"
            contract["preservation"]["payload"] = "drop_payload"
            contract["preservation"]["formula"] = "drop_sibling_cache"
            contract["preservation"]["package"] = "rewrite_all_parts"
            contract["native_profile"]["pagination"] = "guess_trailing"
            contract["native_profile"]["native_ids"] = "reuse_or_allocate"
            contract["receipt"]["debug"] = "raw_ids_hashes_xml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_lock_path", "source_lock_paths_exact", "separator", "lattice",
                "junction", "publication", "payload_preservation", "formula_preservation",
                "package_preservation", "pagination_boundary", "native_ids", "receipt_debug",
            ):
                self.assertIn(code, errors)

    def test_evidence_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["formula_rebase_or_cache_clear"] = True
            contract["not_claimed"]["different_junction_edges"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            migration = root / validator.MIGRATION
            migration.write_text(
                migration.read_text(encoding="utf-8").replace("may not promote", "may promote"),
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
