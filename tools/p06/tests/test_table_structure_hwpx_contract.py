from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_structure_hwpx_contract as validator


class TableStructureHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_hangul_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 6)
        self.assertEqual(report["implementation_files"], 11)
        self.assertEqual(report["features"], 4)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertFalse(report["actual_hangul"])

    def test_source_implementation_and_catalog_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "protocol/private/p06-table-operations-v1.json"
            source.write_text(source.read_text(encoding="utf-8") + "drift", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/domain-ir/src/table_structure.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "fn validate_edges(", "fn removed_validate_edges("
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            catalog = root / "docs/04_feature_catalog/07_table.md"
            catalog.write_text(
                catalog.read_text(encoding="utf-8").replace(
                    "| TABLE-014 | 줄 지우기 | `table.delete_rows` |",
                    "| TABLE-014 | 줄 지우기 | `table.delete_columns` |",
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
            contract["transition"]["grid"] = "allow_partial_span"
            contract["transition"]["edges"] = "drop_collapsed_edge"
            contract["transition"]["formula"] = "guess_references_and_cache"
            contract["binding"]["publication"] = "return_before_reopen"
            contract["preservation"]["payload"] = "drop_payload"
            contract["preservation"]["pagination"] = "guess_header_and_caption"
            contract["preservation"]["package"] = "rewrite_all_parts"
            contract["native_profile"]["formula"] = "accept_any_formula"
            contract["native_profile"]["repeat_header"] = "toggle_flag"
            contract["receipt"]["debug"] = "raw_ids_hashes_xml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_lock_path", "source_lock_paths_exact", "grid_transition",
                "edge_transition", "formula_transition", "publication",
                "payload_preservation", "pagination_preservation", "package_preservation",
                "formula_profile", "repeat_header_profile", "receipt_debug",
            ):
                self.assertIn(code, errors)

    def test_evidence_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["expected_evidence"]["adapter_tests"] = 7
            contract["not_claimed"]["hangul_2020_target_build"] = True
            contract["not_claimed"]["repeat_header_enable_disable_transition"] = True
            contract["not_claimed"]["insertion_inside_span_or_partial_span_delete"] = True
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
