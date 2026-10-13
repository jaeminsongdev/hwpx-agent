from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.p09 import validate_field_object_caption_hwpx_contract as validator


def copy_tree(root: Path) -> None:
    paths = {
        validator.CONTRACT, validator.QUALIFICATION, validator.POLICY,
        validator.REPORT, validator.MIGRATION, validator.SNAPSHOT, validator.PUBLIC_EXPORT["path"],
        *validator.SOURCE_SHA256, *validator.IMPLEMENTATION_SHA256,
        *(f"{validator.OFFICIAL_BASE}/{path}" for path in validator.OFFICIAL_SHA256),
    }
    for relative in paths:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((validator.ROOT / relative).read_bytes())


class FieldObjectCaptionHwpxContractTests(unittest.TestCase):
    def test_current_bounded_static_contract_without_application_promotion(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["official_locks"], 15)
        self.assertEqual(value["implementation_locks"], 6)
        self.assertEqual(value["source_locks"], 4)
        self.assertEqual(value["actual_hangul"], "not_run")
        self.assertEqual(value["semantic_save_reopen"], "not_run")
        self.assertEqual(value["green_rows"], 0)
        self.assertFalse(value["product_complete"])

    def test_native_profile_weakening_and_claim_promotion_fail_closed(self) -> None:
        cases = [
            (["admitted_profile", "instid_required"], True),
            (["admitted_profile", "namespace"], "any"),
            (["admitted_profile", "picture_names"], ["chart"]),
            (["admitted_profile", "lock"], "1"),
            (["evidence_boundary", "actual_hangul"], True),
            (["evidence_boundary", "green_rows"], 1),
            (["evidence_boundary", "static_caption_composition"], 1),
            (["matrix_effect"], "green"),
            (["policy"], "../outside"),
        ]
        for keys, replacement in cases:
            with self.subTest(keys=keys), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                value = validator.expected_contract()
                cursor = value
                for key in keys[:-1]:
                    cursor = cursor[key]
                cursor[keys[-1]] = replacement
                (root / validator.CONTRACT).write_text(json.dumps(value), encoding="utf-8")
                self.assertIn("contract_mismatch", validator.validate(root)["errors"])

    def test_all_implementation_locks_fail_closed_on_drift(self) -> None:
        for relative in validator.IMPLEMENTATION_SHA256:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assertIn("implementation_digest", validator.validate(root)["errors"])

    def test_reference_and_official_source_drift_fail_closed(self) -> None:
        cases = [
            (next(iter(validator.SOURCE_SHA256)), "source_lock_digest"),
            (f"{validator.OFFICIAL_BASE}/OWPML/Class/Para/caption.cpp", "official_source_digest"),
            (validator.SNAPSHOT, "predecessor_snapshot_digest"),
        ]
        for relative, expected in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assertIn(expected, validator.validate(root)["errors"])

    def test_qualification_claims_tests_and_unknown_keys_fail_closed(self) -> None:
        cases = [
            (["claims", "complete_native_objects"], True),
            (["claims", "application_owned_sequence_derivation"], True),
            (["tests", "caption_public"], "10/10 PASS"),
            (["extra"], "not accepted"),
        ]
        for keys, replacement in cases:
            with self.subTest(keys=keys), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_tree(root)
                value = validator.expected_qualification()
                cursor = value
                for key in keys[:-1]:
                    cursor = cursor[key]
                cursor[keys[-1]] = replacement
                (root / validator.QUALIFICATION).write_text(json.dumps(value), encoding="utf-8")
                self.assertIn("qualification_mismatch", validator.validate(root)["errors"])

    def test_duplicate_json_and_export_removal_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            target.write_text(target.read_text(encoding="utf-8").replace(
                '"task": "P09-18",', '"task": "P09-18", "task": "P09-18",'
            ), encoding="utf-8")
            self.assertIn("contract_or_qualification_json", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.PUBLIC_EXPORT["path"]
            target.write_text(target.read_text(encoding="utf-8").replace(
                "mod field_object_caption_hwpx;", "mod missing_caption;"
            ), encoding="utf-8")
            self.assertIn("public_export", validator.validate(root)["errors"])

    def test_linked_files_and_ancestors_are_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            (real / "input.json").write_text("{}", encoding="utf-8")
            # Symbolic link creation may be unavailable on hosts without Developer Mode.
            try:
                (root / "file.json").symlink_to(real / "input.json")
                (root / "directory").symlink_to(real, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink unavailable: {type(error).__name__}")
            for path in ["file.json", "directory/input.json", "../outside"]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    validator.bounded_file(root, path)

    def test_missing_or_oversized_json_has_bounded_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tree(root)
            target = root / validator.CONTRACT
            target.write_bytes(b" " * (8 * 1024 * 1024 + 1))
            self.assertIn("contract_or_qualification_json", validator.validate(root)["errors"])
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(validator.validate(Path(directory))["state"], "fail")


if __name__ == "__main__":
    unittest.main()
