from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_operations_contract as validator


class TableOperationsContractTests(unittest.TestCase):
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

    def test_source_locks_accept_lf_and_crlf_checkouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "docs/09_roadmap/P06_table_engine.md"
            text = source.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            source.write_bytes(text.encode("utf-8"))
            self.assertEqual(validator.validate(root)["state"], "pass")
            source.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(validator.validate(root)["state"], "pass")

    def test_traversal_source_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("source_lock_path_or_encoding", result["errors"])
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

    def test_policy_tamper_and_omitted_nonclaim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["span_policy"]["insert_inside_span"] = "expand"
            del contract["not_claimed"]["other_pc_or_version"]
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = validator.validate(root)
            self.assertEqual(result["state"], "fail")
            self.assertIn("span_policy", result["errors"])
            self.assertIn("not_claimed", result["errors"])

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
            "protocol/migrations/p06-table-operations-v0-to-v1.md",
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
