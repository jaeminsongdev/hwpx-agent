from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from tools.p06 import validate_table_formula_hwpx_contract as validator


class TableFormulaHwpxContractTests(unittest.TestCase):
    def test_repository_contract_source_capture_and_adapter_pass(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 6)
        self.assertEqual(report["evidence_files"], 4)
        self.assertEqual(report["implementation_files"], 5)
        self.assertEqual(report["product_target_oracle"], "not_run")
        self.assertEqual(report["p06_06"], "in_progress")

    def test_source_lock_and_evidence_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_formula.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            evidence = root / validator.SOURCE_PDF
            evidence.write_bytes(evidence.read_bytes() + b"tamper")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)

    def test_trace_and_hwpx_semantic_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            trace_path = root / validator.TRACE
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["watchdog"]["remaining_hwp_process_count"] = 1
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("trace_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / validator.SOURCE_HWPX
            self.rewrite_section(source, b"=SUM(LEFT)</hp:stringParam>",
                                 b"=SUM(ABOVE)</hp:stringParam>")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("source_hwpx_semantics", errors)

    def test_duplicate_key_path_escape_and_gate_promotion_fail_closed(self) -> None:
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
            contract["gate_decision"]["product_target_hancom_2020_oracle"] = "pass"
            contract["not_claimed"]["product_complete"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_locks_exact", errors)
            self.assertIn("gate_decision", errors)
            self.assertIn("not_claimed", errors)

    @staticmethod
    def rewrite_section(path: Path, old: bytes, new: bytes) -> None:
        temporary = path.with_suffix(".tmp")
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, "w") as target:
            for entry in source.infolist():
                payload = source.read(entry)
                if entry.filename == "Contents/section0.xml":
                    payload = payload.replace(old, new, 1)
                target.writestr(entry, payload)
        path.unlink()
        temporary.rename(path)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.REPORT,
            validator.MIGRATION,
            *validator.SOURCE_LOCKS,
            *validator.EVIDENCE,
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
