from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from tools.p06 import validate_table_layout_target_v2_contract as validator


class TableLayoutTargetV2ContractTests(unittest.TestCase):
    def test_repository_contract_and_exact_oracle_pass(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 3)
        self.assertEqual(report["evidence_files"], 13)
        self.assertEqual(report["implementation_files"], 3)

    def test_source_lock_and_publication_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/hwpx-package/examples/p06_05_table_layout_calibrated_target_fixture.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            target = root / validator.TARGET_DIRECTORY / validator.TARGET_FILES[0]
            target.write_bytes(target.read_bytes() + b"tamper")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)

    def test_trace_pdf_and_hwpx_semantic_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            trace_path = root / validator.TRACE_PATH
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["watchdog"]["remaining_hwp_process_count"] = 1
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("trace_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            pdf = root / validator.PDF_PATH
            pdf.write_bytes(b"%PDF-bad")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("pdf_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            output = root / validator.OUTPUT_PATH
            self.rewrite_section(output, b'horzsize="14100"', b'horzsize="14000"')
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("output_hwpx_semantics", errors)

    def test_duplicate_key_traversal_gate_and_history_fail_closed(self) -> None:
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
            contract["gate_decision"]["current_pc_exact_fixture_p06_05"] = "pass_by_inference"
            contract["historical_calibration_evidence"][0]["cell_line_counts"] = [1, 3, 1, 1]
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_locks_exact", errors)
            self.assertIn("gate_decision", errors)
            self.assertIn("historical_calibration_evidence", errors)

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
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT_RELATIVE.as_posix(),
            *validator.EXPECTED_SOURCE_LOCKS,
            *validator.IMPLEMENTATION_MARKERS,
            *validator.expected_evidence(),
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
