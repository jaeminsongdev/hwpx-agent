from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_hyperlink_hwpx_contract as validator


def copy_tree(root: Path) -> None:
    for relative in {
        validator.CONTRACT,
        validator.MIGRATION,
        validator.POLICY,
        validator.REPORT,
        validator.QUALIFICATION,
        *validator.SOURCE_SHA256,
        *validator.IMPLEMENTATION_SHA256,
    }:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class HyperlinkHwpxContractTests(unittest.TestCase):
    def test_current_contract_is_exact_static_integration_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["official_source_files"], 11)
        self.assertEqual(value["implementation_files"], 5)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 2)
        self.assertEqual(value["direct_stage"], "integration_passed")
        self.assertEqual(value["actual_hangul"], "not_run")
        self.assertFalse(value["p09_14_green"])
        self.assertFalse(value["product_complete"])

    def test_native_profile_and_claim_tamper_fail_closed(self) -> None:
        cases = [
            (["native_profile", "parameters", 3, 2], "HWPHYPERLINK_TYPE_FILE"),
            (["capability_features", "REF-034"], "ref.hyperlink_delete"),
            (["evidence_boundary", "actual_hangul"], True),
            (["gate_decision", "actual_target"], "pass"),
        ]
        for path, replacement in cases:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / validator.CONTRACT
                value = json.loads(target.read_text(encoding="utf-8"))
                cursor = value
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = replacement
                target.write_text(json.dumps(value), encoding="utf-8")
                self.assertEqual(validator.validate(root)["state"], "fail")

    def test_source_implementation_and_qualification_drift_fail_closed(self) -> None:
        cases = [
            ("crates/hwpx-package/src/hyperlink_hwpx.rs", "implementation_digest"),
            ("docs/04_feature_catalog/10_ref.md", "source_lock_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assertIn(expected, validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.QUALIFICATION
            value = json.loads(target.read_text(encoding="utf-8"))
            value["claims"]["generated_output_hancom_open"] = True
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("qualification_claims", validator.validate(root)["errors"])

    def test_duplicate_key_private_path_and_discovery_promotion_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace('"task": "P09-14",', '"task": "P09-14",\n  "task": "P09-14",'),
                encoding="utf-8",
            )
            self.assertIn("contract_json_or_path", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            value = json.loads(target.read_text(encoding="utf-8"))
            value["policy"] = "../outside"
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.QUALIFICATION
            value = json.loads(target.read_text(encoding="utf-8"))
            value["discovery"]["private_artifacts_committed"] = True
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("qualification_discovery", validator.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
