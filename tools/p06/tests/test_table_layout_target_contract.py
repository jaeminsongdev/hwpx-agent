from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_layout_target_contract as validator


class TableLayoutTargetContractTests(unittest.TestCase):
    def test_repository_contract_and_exact_evidence_pass(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 3)
        self.assertEqual(report["evidence_files"], 6)
        self.assertEqual(report["implementation_files"], 5)

    def test_source_lock_and_evidence_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            component = root / "protocol/private/p06-table-layout-hwpx-v2.json"
            component.write_text(component.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            target = root / validator.TARGET_DIRECTORY / validator.TARGET_FILES[0]
            target.write_bytes(target.read_bytes() + b"tamper")
            self.assertIn("evidence_digest", validator.validate(root)["errors"])

    def test_implementation_marker_and_trace_semantics_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "edits.push((line_cache, Vec::new()))", "edits.push((line_cache, vec![0]))"
                ),
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_digest", errors)
            self.assertIn("implementation_marker", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            trace_path = root / validator.TRACE_PATH
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["output_saved"] = True
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("diagnostic_trace_semantics", errors)

    def test_duplicate_key_traversal_and_nonclaim_fail_closed(self) -> None:
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
            self.assertIn("source_locks_exact", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT_RELATIVE.as_posix()
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["not_claimed"]["new_target_hancom_2020_open"] = True
            contract["publication"]["sha256"] = "0" * 64
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("not_claimed", errors)
            self.assertIn("publication", errors)

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        evidence = {
            validator.SOURCE_PATH,
            validator.RECEIPT_PATH,
            validator.TRACE_PATH,
            *{
                f"{validator.TARGET_DIRECTORY}/{name}"
                for name in validator.TARGET_FILES
            },
        }
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
            *validator.EXPECTED_SOURCE_LOCKS,
            *validator.IMPLEMENTATION_MARKERS,
            *evidence,
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
