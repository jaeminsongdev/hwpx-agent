from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_mail_merge_contract as validator


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


class MailMergeContractTests(unittest.TestCase):
    def test_current_contract_is_one_capability_unit_without_generation_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["official_source_files"], 5)
        self.assertEqual(value["implementation_files"], 3)
        self.assertTrue(value["source_qualification_verified"])
        self.assertEqual(value["capabilities"], 1)
        self.assertEqual(value["native_parameter_semantics"], "unverified")
        self.assertEqual(value["provider_mapping"], "unverified")
        self.assertEqual(value["batch_generation"], "not_run")
        self.assertEqual(value["direct_hwpx"], "not_run")
        self.assertFalse(value["p09_09_green"])
        self.assertFalse(value["product_complete"])

    def test_capability_native_and_generation_boundaries_fail_closed(self) -> None:
        cases = [
            (["capability_features", "REF-046"], "ref.mailmerge_generate"),
            (["excluded_capabilities", "REF-047"], "P09"),
            (["official_model", "native_parameter_binding"], "verified"),
            (["official_model", "exact_native_structures", 0], "mailMergeField"),
            (["evidence_boundary", "focused_rust_tests"], "11/11 PASS"),
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
            (validator.CONTRACT, ["evidence_boundary", "batch_generation_implemented"], True),
            (validator.QUALIFICATION, ["claims", "ref_047_generate_implemented"], True),
            (validator.QUALIFICATION, ["claims", "plaintext_rows_stored"], True),
            (validator.QUALIFICATION, ["tests", "plaintext_rows_used"], True),
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
            "crates/domain-ir/src/mail_merge.rs",
            "crates/domain-ir/tests/mail_merge.rs",
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

    def test_duplicate_source_path_and_official_metadata_tamper_fail(self) -> None:
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
            value["qualified_facts"]["unverified_native_bindings"] = []
            target.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(validator.validate(root)["state"], "fail")


if __name__ == "__main__":
    unittest.main()
