from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_toc_index_contract as validator


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


class TocIndexContractTests(unittest.TestCase):
    def test_current_contract_is_five_capability_unit_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["official_source_files"], 13)
        self.assertEqual(value["implementation_files"], 3)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 5)
        self.assertEqual(value["native_generation_semantics"], "unverified")
        self.assertEqual(value["ref_040_update"], "not_implemented_p11_owned")
        self.assertEqual(value["direct_hwpx"], "not_run")
        self.assertFalse(value["p09_07_green"])
        self.assertFalse(value["product_complete"])

    def test_capability_scope_and_native_boundary_tamper_fail_closed(self) -> None:
        cases = [
            (["capability_features", "REF-037"], "ref.toc_update"),
            (["excluded_capabilities", "REF-040"], "P09"),
            (["official_model", "toc_semantic_binding"], "verified"),
            (["official_model", "exact_native_structures", 0], "tocField"),
            (["evidence_boundary", "focused_rust_tests"], "12/12 PASS"),
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

    def test_claim_promotion_and_qualification_tamper_fail_closed(self) -> None:
        cases = [
            (validator.CONTRACT, ["evidence_boundary", "direct_hwpx"], True),
            (validator.CONTRACT, ["gate_decision", "actual_target"], "pass"),
            (validator.QUALIFICATION, ["claims", "ref_040_update_implemented"], True),
            (validator.QUALIFICATION, ["tests", "licensed_application_used"], True),
        ]
        for relative, path, replacement in cases:
            with self.subTest(relative=relative, path=path), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                value = json.loads(target.read_text(encoding="utf-8"))
                cursor = value
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = replacement
                target.write_text(json.dumps(value), encoding="utf-8")
                self.assertEqual(validator.validate(root)["state"], "fail")

    def test_implementation_and_authoritative_source_drift_fail_exact_locks(self) -> None:
        cases = [
            ("crates/domain-ir/src/toc_index.rs", "implementation_digest"),
            ("docs/04_feature_catalog/10_ref.md", "source_lock_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assertIn(expected, validator.validate(root)["errors"])

    def test_duplicate_path_and_official_source_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"task": "P09-07",', '"task": "P09-07",\n  "task": "P09-07",'), encoding="utf-8")
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
            value["official_model"]["source_sha256"]["OWPML/Class/enumdef.h"] = "0" * 64
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("qualification_official_sources", validator.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
