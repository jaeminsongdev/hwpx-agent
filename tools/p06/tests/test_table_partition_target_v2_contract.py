from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from tools.p06 import validate_table_partition_target_v2_contract as validator


class TablePartitionTargetV2ContractTests(unittest.TestCase):
    def test_repository_exact_current_pc_partition_oracle_passes(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 13)
        self.assertEqual(report["evidence_files"], 14)
        self.assertEqual(report["implementation_files"], 8)
        self.assertEqual(report["predecessors"], "pass")
        self.assertEqual(report["TABLE-010"], "oracle_verified")
        self.assertEqual(report["TABLE-011"], "oracle_verified")
        self.assertEqual(report["p06"], "in_progress")

    def test_source_lock_and_native_separator_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx/partition_hwpx.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[0]
            target = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hwpx"
            self.rewrite_part(
                target,
                "Contents/section0.xml",
                b'<hp:run charPrIDRef="0"/>',
                b'<hp:run charPrIDRef="0"><hp:t>X</hp:t></hp:run>',
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("target_oracle_hwpx_semantics", errors)

    def test_renderer_cache_and_trace_residue_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[1]
            output = root / validator.TARGET_DIRECTORY / f"{item['stem']}.hancom-2020-readback.hwpx"
            self.rewrite_part(output, "Contents/section0.xml", b'flags="393216"', b'flags="393217"')
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("target_oracle_hwpx_semantics", errors)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            item = validator.CASE_INFO[0]
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
            item = validator.CASE_INFO[0]
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
            item = validator.CASE_INFO[1]
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
