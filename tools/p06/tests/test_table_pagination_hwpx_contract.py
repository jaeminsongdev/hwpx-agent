from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_pagination_hwpx_contract as validator


class TablePaginationHwpxContractTests(unittest.TestCase):
    def test_repository_static_adapter_contract_passes_without_gate_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 4)
        self.assertEqual(report["implementation_files"], 4)
        self.assertEqual(report["static_hwpx_adapter_component"], "pass")
        self.assertEqual(report["actual_hancom_2020_boundary_page_suite"], "not_run")
        self.assertEqual(report["p06_07"], "in_progress")

    def test_source_lock_and_marker_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_pagination.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            report = root / validator.REPORT
            report.write_text("missing markers", encoding="utf-8")
            self.assertIn("implementation_markers", validator.validate(root)["errors"])

    def test_duplicate_key_and_path_escape_fail_closed(self) -> None:
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
            contract["source_locks"][0]["path"] = "../outside.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_locks_exact", errors)

    def test_renderer_and_product_gate_promotion_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["gate_decision"]["actual_hancom_2020_boundary_page_suite"] = "pass"
            contract["gate_decision"]["p06_07"] = "pass"
            contract["not_claimed"]["product_complete"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("gate_decision", errors)
            self.assertIn("not_claimed", errors)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.REPORT,
            validator.MIGRATION,
            *validator.SOURCE_LOCKS,
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
