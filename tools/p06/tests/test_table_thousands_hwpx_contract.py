from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_thousands_hwpx_contract as validator


class TableThousandsHwpxContractTests(unittest.TestCase):
    def test_repository_contract_passes_at_exact_integration_boundary(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 10)
        self.assertEqual(report["evidence_files"], 6)
        self.assertEqual(report["implementation_files"], 10)
        self.assertEqual(report["features"], 2)
        self.assertEqual(report["direct_stage"], "integration_passed")
        self.assertTrue(report["actual_hancom_native_source"])
        self.assertFalse(report["direct_output_package_save_reopen"])
        self.assertFalse(report["direct_output_render"])
        self.assertEqual(report["automation_runtime"], "not_run")

    def test_source_and_implementation_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_formula/thousands_hwpx.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n// drift\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "implementation/p06/P06-09_TABLE_THOUSANDS_HWPX_POLICY.md"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "direct_hwpx / integration_passed", "direct_hwpx / oracle_verified"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

    def test_duplicate_path_semantics_and_nonclaim_tamper_fail_closed(self) -> None:
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
            contract["transition"]["remove"] = "rewrite_native_metadata"
            contract["binding"]["build"] = "skip_recheck"
            contract["preservation"]["section"] = "best_effort"
            contract["expected_evidence"]["direct_stage"] = "oracle_verified"
            contract["not_claimed"]["direct_output_render"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            for code in (
                "source_locks_exact", "transition", "binding", "preservation",
                "expected_evidence", "not_claimed",
            ):
                self.assertIn(code, errors)

    def test_target_progress_receipt_and_migration_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            target = root / validator.ARTIFACTS["removed"]["path"]
            target.write_bytes(target.read_bytes() + b"drift")
            self.assertIn("evidence_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            receipt_path = root / validator.RECEIPT
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["gate_decision"]["direct_output_render"] = "pass"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertIn("evidence_receipt", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            migration = root / validator.MIGRATION
            migration.write_text(
                migration.read_text(encoding="utf-8").replace(
                    "may not be inferred", "may be inferred"
                ),
                encoding="utf-8",
            )
            self.assertIn("migration_marker", validator.validate(root)["errors"])

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.MIGRATION,
            validator.POLICY,
            validator.REPORT,
            validator.RECEIPT,
            *validator.SOURCE_LOCKS,
            *validator.IMPLEMENTATION_MARKERS,
            *(item["path"] for item in validator.ARTIFACTS.values()),
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
