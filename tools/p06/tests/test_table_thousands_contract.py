from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_thousands_contract as validator


class TableThousandsContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_backend_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 5)
        self.assertEqual(report["implementation_files"], 5)
        self.assertEqual(report["features"], 2)
        self.assertEqual(report["direct_stage"], "unit_passed")
        self.assertFalse(report["actual_hwpx"])
        self.assertFalse(report["actual_hangul"])

    def test_source_and_implementation_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/domain-ir/tests/table_thousands.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/domain-ir/src/table_thousands.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "pub struct TableThousandsBuilder", "pub struct RemovedThousandsBuilder"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_duplicate_key_path_and_semantic_drift_fail_closed(self) -> None:
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
            contract["semantics"]["input_format"] = "infer_anything"
            contract["semantics"]["add"] = "rewrite_text"
            contract["semantics"]["preserve"] = "best_effort"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("semantics_input_format", errors)
            self.assertIn("semantics_add", errors)
            self.assertIn("semantics_preserve", errors)

    def test_nonclaim_and_migration_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["gate_decision"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["hancom_2020_target_build"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            migration = root / validator.MIGRATION
            migration.write_text(
                migration.read_text(encoding="utf-8").replace(
                    "no partial plan", "partial plan allowed"
                ),
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("gate_decision", errors)
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
