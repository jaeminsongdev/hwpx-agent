from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import validate_table_chart_render_diff_v2_contract as validator


class TableChartRenderDiffV2ContractTests(unittest.TestCase):
    def test_repository_qualification_and_retry_pass_without_green_promotion(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "pass", result)
        self.assertEqual(result["runs"], 4)
        self.assertEqual(result["artifacts"], 20)
        self.assertEqual(result["progress_events"], 48)
        self.assertEqual(result["required_render_diff"], "pass")
        self.assertEqual(result["rollback_or_retry"], "pass")
        self.assertEqual(result["TABLE-006"], "oracle_verified")
        self.assertEqual(result["automation_runtime"], "not_run")
        self.assertEqual(result["release_differential"], "not_run")
        self.assertFalse(result["product_complete"])

    def test_predecessor_profile_and_source_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            predecessor = root / validator.PREDECESSOR
            predecessor.write_text(
                predecessor.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_digest", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            predecessor = root / validator.PREDECESSOR
            content = json.loads(predecessor.read_text(encoding="utf-8"))
            content["frozen_profile"]["maximum_differing_pixel_ratio"] = 1.0
            predecessor.write_text(json.dumps(content), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_digest", errors)
            self.assertIn("frozen_profile", errors)

    def test_artifact_trace_and_progress_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            artifact = root / validator.RUNS[0]["artifacts"][0]["path"]
            artifact.write_bytes(artifact.read_bytes() + b"tamper")
            self.assertIn("artifact_identity", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            trace_path = root / validator.RUNS[1]["artifacts"][2]["path"]
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["watchdog"]["remaining_hwp_process_count"] = 1
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("artifact_identity", errors)
            self.assertIn("watchdog_finalizer", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            progress_path = root / validator.RUNS[2]["artifacts"][4]["path"]
            rows = progress_path.read_text(encoding="utf-8").splitlines()
            rows[4], rows[5] = rows[5], rows[4]
            progress_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("artifact_identity", errors)
            self.assertIn("progress_semantics", errors)

    def test_receipt_gate_privacy_and_nonclaim_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            receipt_path = root / validator.RECEIPT
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["gate_decision"]["automation_runtime"] = "pass"
            receipt["not_claimed"]["product_complete"] = True
            receipt["privacy"]["absolute_paths"] = True
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("receipt_semantics", errors)
            self.assertIn("receipt_privacy", errors)

    def test_contract_duplicate_key_path_and_gate_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{\n  "schema_version": "duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(
                validator.validate(root)["errors"],
                ["contract_json_or_path"],
            )

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["runs"][0]["artifacts"][0]["path"] = "../outside.hwpx"
            contract["gate_decision"]["release_differential"] = "pass"
            contract["not_claimed"]["table_006_green"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            self.assertIn("contract_semantics", validator.validate(root)["errors"])

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.PREDECESSOR,
            validator.MIGRATION,
            validator.POLICY,
            validator.REPORT,
            validator.RECEIPT,
            *validator.SOURCE_LOCKS,
            *(
                item["path"]
                for run in validator.RUNS
                for item in run["artifacts"]
            ),
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
