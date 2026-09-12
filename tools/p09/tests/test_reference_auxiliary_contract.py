from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_reference_auxiliary_contract as validator


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


class ReferenceAuxiliaryContractTests(unittest.TestCase):
    def test_current_contract_is_six_unit_capabilities_without_target_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["official_source_files"], 9)
        self.assertEqual(value["implementation_files"], 3)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 6)
        self.assertEqual(value["native_parameter_semantics"], "unverified")
        self.assertEqual(value["direct_stage"], "unit_passed")
        self.assertEqual(value["direct_hwpx"], "not_run")
        self.assertFalse(value["p09_10_green"])
        self.assertFalse(value["product_complete"])

    def test_capability_official_and_test_count_tamper_fail_closed(self) -> None:
        cases = [
            (["capability_features", "REF-048"], "ref.caption_insert"),
            (["capability_features", "REF-053"], "ref.reference_repair"),
            (["official_model", "native_parameter_binding"], "verified"),
            (["evidence_boundary", "focused_rust_tests"], "14/14 PASS"),
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

    def test_claim_promotion_and_privacy_tamper_fail_closed(self) -> None:
        cases = [
            (validator.CONTRACT, ["evidence_boundary", "direct_hwpx"], True),
            (validator.CONTRACT, ["evidence_boundary", "reference_repair_implemented"], True),
            (validator.QUALIFICATION, ["claims", "actual_hangul"], True),
            (validator.QUALIFICATION, ["claims", "data_link_access_implemented"], True),
            (validator.QUALIFICATION, ["tests", "raw_external_path_used"], True),
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
        for relative in [
            "crates/domain-ir/src/reference_auxiliary.rs",
            "crates/domain-ir/tests/reference_auxiliary.rs",
            "docs/04_feature_catalog/10_ref.md",
        ]:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                target.write_text(target.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
                value = validator.validate(root)
                self.assertEqual(value["state"], "fail")
                self.assertTrue(any(error.startswith("digest:") for error in value["errors"]))

    def test_duplicate_source_path_and_official_fact_tamper_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            value = json.loads(target.read_text(encoding="utf-8"))
            value["source_locks"][1]["path"] = value["source_locks"][0]["path"]
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.QUALIFICATION
            value = json.loads(target.read_text(encoding="utf-8"))
            value["qualified_facts"]["proofreading_field_type_count"] = 18
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")


if __name__ == "__main__":
    unittest.main()
