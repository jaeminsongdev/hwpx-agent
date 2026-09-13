from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p06 import table_chart_render_diff as render_diff
from tools.p06 import validate_table_chart_render_diff_contract as validator


class TableChartRenderDiffContractTests(unittest.TestCase):
    def test_repository_contract_passes_only_at_calibration_boundary(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "pass", result)
        self.assertEqual(result["source_locks"], 2)
        self.assertEqual(result["artifacts"], 4)
        self.assertEqual(result["profile"], "frozen_after_calibration")
        self.assertEqual(result["calibration_fit"], "pass")
        self.assertEqual(result["required_render_diff"], "not_run")
        self.assertEqual(result["TABLE-006"], "integration_passed")
        self.assertFalse(result["product_complete"])

    def test_contract_profile_and_source_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["frozen_profile"]["maximum_differing_pixel_ratio"] = 1.0
            contract["qualification_rule"][
                "calibration_pair_may_satisfy_required_render_diff"
            ] = True
            contract["gate_decision"]["required_render_diff"] = "pass"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("frozen_profile", errors)
            self.assertIn("contract_semantics", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "tools/p06/table_chart_render_diff.py"
            source.write_text(source.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

    def test_receipt_artifact_and_document_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            receipt_path = root / validator.RECEIPT
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["observation"]["raster"]["outside_allowed_diff_box_pixels"] = 1
            receipt["gate_decision"]["required_render_diff"] = "pass"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("receipt_observation", errors)
            self.assertIn("receipt_semantics", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            pdf = root / validator.ARTIFACTS["product_pdf"]["path"]
            pdf.write_bytes(pdf.read_bytes() + b"drift")
            self.assertIn("artifact_identity", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            report = root / validator.REPORT
            report.write_text(
                report.read_text(encoding="utf-8").replace("0/61 green", "61/61 green"),
                encoding="utf-8",
            )
            self.assertIn("document_marker", validator.validate(root)["errors"])

    def test_runtime_observation_threshold_and_semantic_tamper_fail_closed(self) -> None:
        contract = json.loads((validator.ROOT / validator.CONTRACT).read_text(encoding="utf-8"))
        profile = contract["frozen_profile"]
        receipt = json.loads((validator.ROOT / validator.RECEIPT).read_text(encoding="utf-8"))
        raster = copy.deepcopy(receipt["observation"]["raster"])
        raster.pop("render_dpi")
        observation = {
            "native_pdf_identity": copy.deepcopy(profile["pdf_identity"]),
            "product_pdf_identity": copy.deepcopy(profile["pdf_identity"]),
            "native_words": [
                {"text": text, "bbox": copy.deepcopy(box)}
                for text, box in zip(profile["expected_words"], profile["expected_word_boxes"])
            ],
            "product_words": [
                {"text": text, "bbox": copy.deepcopy(box)}
                for text, box in zip(profile["expected_words"], profile["expected_word_boxes"])
            ],
            "raster": raster,
            "native_hwpx_semantics": copy.deepcopy(profile["hwpx_semantics"]),
            "product_hwpx_semantics": copy.deepcopy(profile["hwpx_semantics"]),
        }
        self.assertEqual(render_diff.validate_observation(observation, profile), [])

        outside = copy.deepcopy(observation)
        outside["raster"]["outside_allowed_diff_box_pixels"] = 1
        self.assertIn("raster_diff_region", render_diff.validate_observation(outside, profile))

        geometry = copy.deepcopy(observation)
        geometry["native_words"][0]["bbox"][0] += 0.01
        self.assertIn("word_bbox", render_diff.validate_observation(geometry, profile))

        semantics = copy.deepcopy(observation)
        semantics["product_hwpx_semantics"]["series_count"] = 1
        self.assertIn("hwpx_semantics", render_diff.validate_observation(semantics, profile))

        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / "profile.json"
            relaxed = copy.deepcopy(contract)
            relaxed["frozen_profile"]["maximum_differing_pixel_ratio"] = 1.0
            profile_path.write_text(json.dumps(relaxed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                render_diff.load_profile(profile_path)

            duplicate = (validator.ROOT / validator.CONTRACT).read_text(encoding="utf-8")
            profile_path.write_text(
                duplicate.replace("{\n", '{\n  "schema_version": "duplicate",\n', 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate profile key"):
                render_diff.load_profile(profile_path)

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
