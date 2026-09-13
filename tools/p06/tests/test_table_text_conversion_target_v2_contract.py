from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from tools.p06 import validate_table_text_conversion_target_v2_contract as validator


class TableTextConversionTargetV2ContractTests(unittest.TestCase):
    def test_repository_exact_current_pc_oracle_passes(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 12)
        self.assertEqual(report["evidence_files"], 23)
        self.assertEqual(report["implementation_files"], 4)
        self.assertEqual(report["predecessors"], {"TABLE-004": "pass", "TABLE-005": "pass"})
        self.assertTrue(report["actual_hangul"])
        self.assertEqual(report["render"], "pass")
        self.assertEqual(report["rollback_or_retry"], "pass")
        self.assertEqual(report["automation_runtime"], "not_run")
        self.assertEqual(report["differential"], "not_run")
        self.assertEqual(report["p06"], "in_progress")

    def test_source_lock_and_output_semantic_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / "crates/hwpx-package/src/table_ruling_hwpx/text_conversion_hwpx.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            output = root / validator.output_path(validator.CASE_SPECS[0])
            self.rewrite_part(output, "Contents/section0.xml", b'rowCnt="3"', b'rowCnt="9"')
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("hwpx_semantics", errors)

    def test_source_locks_accept_crlf_checkout_without_weakening_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            source = root / (
                "implementation/p06/tools/"
                "run-hancom-2020-table-text-conversion-target-batch-engine.ps1"
            )
            payload = source.read_bytes().replace(b"\r\n", b"\n")
            source.write_bytes(payload.replace(b"\n", b"\r\n"))
            self.assertEqual(validator.validate(root)["state"], "pass")

    def test_trace_progress_and_history_tamper_fail(self) -> None:
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
            progress_path = root / validator.PROGRESS_PATH
            lines = progress_path.read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[-1])
            event["state"] = "failed"
            lines[-1] = json.dumps(event)
            progress_path.write_text("\n".join(lines), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("progress_semantics", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            history_path = root / validator.HISTORICAL[0][0]
            history = json.loads(history_path.read_text(encoding="utf-8"))
            history["state"] = "pass"
            history_path.write_text(json.dumps(history), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("historical_semantics", errors)

    def test_manifest_pdf_and_receipt_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            manifest_path = root / validator.MANIFEST_PATH
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["actual_hangul_2020"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("manifest_semantics", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            pdf = root / validator.pdf_path(validator.CASE_SPECS[0])
            pdf.write_bytes(b"%PDF-bad")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("pdf_semantics", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_validation_tree(Path(directory))
            receipt_path = root / validator.RECEIPT
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["gate_decision"]["p06"] = "pass"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("evidence_digest", errors)
            self.assertIn("receipt_semantics", errors)

    def test_contract_duplicate_path_escape_and_overclaim_fail_closed(self) -> None:
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
            contract["historical_attempts"]["promoted_to_pass"] = 1
            contract["gate_decision"]["p06"] = "pass"
            contract["not_claimed"]["product_complete"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_locks_exact", errors)
            self.assertIn("historical_attempts", errors)
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
