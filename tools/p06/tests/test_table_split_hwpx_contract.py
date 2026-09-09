from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_split_hwpx_contract as validator


class TableSplitHwpxContractTests(unittest.TestCase):
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
                    "fn render_split_section", "fn removed_render_split_section"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            catalog = root / "docs/04_feature_catalog/07_table.md"
            catalog.write_text(
                catalog.read_text(encoding="utf-8").replace(
                    "| TABLE-010 | 표 나누기 | `table.split_table` |",
                    "| TABLE-010 | 표 나누기 | `table.join_table` |",
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
            contract["split"]["boundary"] = "guess_cursor"
            contract["split"]["second"] = "reuse_identity"
            contract["binding"]["publication"] = "return_before_reopen"
            contract["preservation"]["payload"] = "drop_payload"
            contract["preservation"]["formula"] = "drop_sibling_cache"
            contract["preservation"]["package"] = "rewrite_all_parts"
            contract["native_profile"]["repeat_header"] = "claim_unknown"
            contract["native_profile"]["caption"] = "claim_unknown"
            contract["native_profile"]["native_ids"] = "reuse_ids"
            contract["receipt"]["debug"] = "raw_ids_hashes_xml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_lock_path", "source_lock_paths_exact", "boundary", "second_table",
                "publication", "payload_preservation", "formula_preservation",
                "package_preservation", "repeat_header_boundary", "caption_boundary",
                "native_ids", "receipt_debug",
            ):
                self.assertIn(code, errors)

    def test_evidence_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["repeat_header_split"] = True
            contract["not_claimed"]["join_table"] = True
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
