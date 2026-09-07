from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_cell_style_contract as validator


class TableCellStyleContractTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "pass", result)
        self.assertEqual(result["source_locks"], 6)
        self.assertEqual(result["implementation_files"], 7)

    def test_source_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "docs/09_roadmap/P06_table_engine.md"
            source.write_text(source.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("source_lock_digest", result["errors"])

    def test_duplicate_key_and_traversal_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{\n  "schema_version": "duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_lock_paths_exact", errors)

    def test_nonclaim_and_runtime_marker_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["not_claimed"]["other_pc_or_version"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            self.assertIn("not_claimed", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            script = root / "implementation/p06/tools/create-hancom-2020-table-source.ps1"
            script.write_text(
                script.read_text(encoding="utf-8").replace("TableCreate", "UnknownAction"),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            script = root / "implementation/p06/tools/create-hancom-2020-table-source.ps1"
            script.write_text(
                script.read_text(encoding="utf-8").replace(
                    "Get-Sha256String -Value $canonicalReopenText",
                    "Get-Sha256String -Value $reopenText",
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
            "protocol/migrations/p06-table-cell-style-v0-to-v1.md",
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
