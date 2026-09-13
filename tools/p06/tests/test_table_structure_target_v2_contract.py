from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from tools.p06 import validate_table_structure_target_v2_contract as validator


class TableStructureTargetV2ContractTests(unittest.TestCase):
    def test_repository_combined_structure_oracle_passes(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 9)
        self.assertEqual(report["evidence_files"], 26)
        self.assertEqual(report["implementation_files"], 8)
        self.assertEqual(report["predecessor"], "pass")
        for feature_id in ("TABLE-012", "TABLE-013", "TABLE-014", "TABLE-015"):
            self.assertEqual(report[feature_id], "oracle_verified")
        self.assertEqual(report["p06"], "in_progress")

    def test_source_lock_and_native_empty_cell_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx/structure_hwpx.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[0]
            target = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hwpx"
            self.rewrite_part(
                target,
                "Contents/section0.xml",
                b'pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>',
                b'pageBreak="1" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>',
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("target_oracle_hwpx_semantics", errors)

    def test_renderer_cache_and_trace_residue_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[1]
            output = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hancom-2020-readback.hwpx"
            self.rewrite_part(
                output,
                "Contents/section0.xml",
                b"<hp:linesegarray>",
                b"<hp:linesegarray><hp:synthetic-tamper/>",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("target_oracle_hwpx_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[2]
            trace_path = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hancom-2020-trace.json"
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["watchdog"]["remaining_hwp_process_count"] = 1
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("trace_or_progress_semantics", errors)

    def test_progress_pdf_and_receipt_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[3]
            progress = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hancom-2020-trace.json.progress.jsonl"
            lines = progress.read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[-1])
            event["state"] = "failed"
            lines[-1] = json.dumps(event)
            progress.write_text("\n".join(lines), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("trace_or_progress_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[0]
            pdf = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hancom-2020-render.pdf"
            pdf.write_bytes(b"%PDF-bad")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("pdf_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            receipt = root / validator.RECEIPT
            receipt.write_text(receipt.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("evidence_digest", validator.validate(root)["errors"])

    def test_duplicate_key_path_escape_and_gate_promotion_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{\n  "schema_version": "duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.json"
            contract["gate_decision"]["p06"] = "pass"
            contract["not_claimed"]["product_complete"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path_or_encoding", errors)
            self.assertIn("source_locks_exact", errors)
            self.assertIn("gate_decision", errors)
            self.assertIn("not_claimed", errors)

    @staticmethod
    def rewrite_part(path: Path, part_name: str, old: bytes, new: bytes) -> None:
        temporary = path.with_suffix(".tmp")
        changed = 0
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, "w") as target:
            for entry in source.infolist():
                payload = source.read(entry)
                if entry.filename == part_name:
                    replaced = payload.replace(old, new, 1)
                    changed += int(replaced != payload)
                    payload = replaced
                target.writestr(entry, payload)
        if changed != 1:
            raise AssertionError("test mutation did not match exactly once")
        path.unlink()
        temporary.rename(path)

    @staticmethod
    def copy_validation_tree(destination: Path) -> Path:
        root = destination / "repo"
        for relative in validator.expected_validation_tree():
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
