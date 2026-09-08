from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_pagination_contract as validator


class TablePaginationContractTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 6)
        self.assertEqual(report["implementation_files"], 4)
        self.assertEqual(report["p06_07"], "in_progress")
        self.assertFalse(report["actual_hangul"])

    def test_source_and_implementation_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "docs/09_roadmap/P06_table_engine.md"
            source.write_text(source.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/domain-ir/src/table_pagination.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "HeaderSpanCrossesBody", "RemovedHeaderBoundaryFailure"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_duplicate_key_traversal_and_policy_drift_fail_closed(self) -> None:
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
            contract["page_split_policies"].pop("required_keep")
            contract["captions"]["v1_sides"] = ["top", "bottom", "left"]
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("page_split_policies", errors)
            self.assertIn("caption_sides", errors)

    def test_nonclaim_limit_and_capability_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["not_claimed"]["p06_07_complete"] = True
            contract["default_limits"]["fragments"] += 1
            contract["component_capabilities"].remove("table.caption")
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("not_claimed", errors)
            self.assertIn("default_limits", errors)
            self.assertIn("component_capabilities", errors)

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
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
