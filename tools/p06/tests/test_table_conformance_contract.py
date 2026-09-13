from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_conformance_contract as validator


class TableConformanceContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_promoting_matrix(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 466)
        self.assertEqual(report["schemas"], 3)
        self.assertEqual(report["green_rows"], 0)
        self.assertEqual(report["required_matrix"], "non_green")
        self.assertEqual(report["p06_07"], "pass")
        self.assertEqual(report["p06_09"], "in_progress")
        self.assertFalse(report["product_complete"])

    def test_locked_source_and_committed_report_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            policy = root / validator.POLICY
            policy.write_text(policy.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            report_path = root / validator.REPORT
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["summary"]["green_rows"] = 1
            report_path.write_text(json.dumps(report), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_digest", errors)
            self.assertIn("report_drift", errors)
            self.assertIn("report_summary", errors)

    def test_duplicate_contract_key_and_traversal_fail_closed(self) -> None:
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
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)

    def test_green_rule_nonclaim_and_schema_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["green_rule"].pop()
            contract["not_claimed"]["p06_09_complete"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("green_rule", errors)
            self.assertIn("not_claimed", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            schema_path = root / validator.SCHEMAS[0]
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["type"] = "not-a-json-schema-type"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_digest", errors)
            self.assertIn("schema_invalid", errors)

    def test_source_locks_accept_a_crlf_checkout_without_weakening_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            roadmap = root / "docs/09_roadmap/P06_table_engine.md"
            source = roadmap.read_bytes().replace(b"\r\n", b"\n")
            self.assertNotIn(b"\r", source)
            roadmap.write_bytes(source.replace(b"\n", b"\r\n"))
            report = validator.validate(root)
            self.assertEqual(report["state"], "pass", report)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        evidence = json.loads(
            (validator.ROOT / "implementation/p06/p06-09-current-2020-direct-evidence.json")
            .read_text(encoding="utf-8")
        )
        referenced_evidence = {
            item["path"]
            for record in evidence["records"]
            for item in record["evidence_files"]
        }
        paths = {
            validator.CONTRACT,
            *validator.EXPECTED_SOURCE_PATHS,
            *referenced_evidence,
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
