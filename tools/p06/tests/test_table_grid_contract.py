from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_grid_contract as validator


class TableGridContractTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "pass", result)
        self.assertEqual(result["source_locks"], 4)
        self.assertEqual(result["implementation_files"], 3)

    def test_source_tamper_fails_without_relabeling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "docs/03_document_model/06_table_model.md"
            source.write_text(source.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("source_lock_digest", result["errors"])

    def test_source_locks_are_portable_across_lf_and_crlf_checkouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "docs/09_roadmap/P06_table_engine.md"
            text = source.read_text(encoding="utf-8")
            source.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))
            lf_result = validator.validate(root)
            self.assertEqual(lf_result["state"], "pass", lf_result)

            source.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n").encode("utf-8"))
            crlf_result = validator.validate(root)
            self.assertEqual(crlf_result["state"], "pass", crlf_result)

    def test_traversal_source_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("source_lock_path", result["errors"])
            self.assertIn("source_lock_paths_exact", result["errors"])

    def test_duplicate_contract_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace(
                    "{\n",
                    '{\n  "schema_version": "duplicate",\n',
                    1,
                ),
                encoding="utf-8",
            )
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertEqual(result["errors"], ["contract_json_or_path"])

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
            "protocol/migrations/p06-table-grid-v0-to-v1.md",
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
