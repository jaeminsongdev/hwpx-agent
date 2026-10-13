from __future__ import annotations

import copy
import io
import json
import re
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

from tools.p09 import inspect_field_object_caption_target as oracle

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output"
MANIFEST_SHA256 = "42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48"


class FieldObjectCaptionTargetOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (BUNDLE / "fixture-manifest.json").is_file():
            raise unittest.SkipTest("P09-19 isolated current-PC corpus is not present")
        cls.manifest = oracle.load_manifest(BUNDLE / "fixture-manifest.json", MANIFEST_SHA256)

    def changed_package(self, root: Path, case_id: str, source: bytes, target: bytes) -> Path:
        original = BUNDLE / oracle.FILES[case_id]
        output = io.BytesIO()
        with zipfile.ZipFile(original) as archive, zipfile.ZipFile(output, "w") as writer:
            for entry in archive.infolist():
                data = archive.read(entry)
                if entry.filename == oracle.SECTION:
                    if source not in data:
                        self.fail("test source delta absent")
                    data = data.replace(source, target, 1)
                writer.writestr(entry, data)
        path = root / "test-snapshot.hwpx"
        path.write_bytes(output.getvalue())
        return path

    def test_all_four_real_object_packages_pass_only_static_input_scope(self) -> None:
        for case_id in oracle.CASES:
            with self.subTest(case=case_id):
                value = oracle.inspect(BUNDLE / oracle.FILES[case_id], self.manifest, case_id, "input")
                self.assertEqual(value["state"], "pass", value)
                self.assertEqual(value["caption_number"], 19)
                self.assertTrue(value["caption_object_binding"])
                self.assertFalse(value["actual_hangul"])
                self.assertEqual(value["green_rows"], 0)

    def test_preserved_cached_19_is_not_application_recalculation(self) -> None:
        for case_id in oracle.CASES:
            with self.subTest(case=case_id):
                value = oracle.inspect(BUNDLE / oracle.FILES[case_id], self.manifest, case_id, "saved")
                self.assertIn("application_number_expectation_mismatch", value["errors"])
                self.assertEqual(value["state"], "fail")

    def test_simulated_numeric_one_never_claims_real_lifecycle_or_target_qualification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.changed_package(Path(directory), "P09-19-C01", b'num="19"', b'num="1"')
            value = oracle.inspect(path, self.manifest, "P09-19-C01", "reopened")
            self.assertEqual(value["state"], "pass", value)
            self.assertFalse(value["actual_hangul"])
            self.assertFalse(value["model_expectation_target_qualified"])
            self.assertEqual(value["lifecycle_qualification"], "not_run")
            self.assertFalse(value["product_complete"])

    def test_wrong_numbering_kind_and_locked_target_fail(self) -> None:
        for source, target, error in [
            (b'numberingType="PICTURE"', b'numberingType="NONE"', "native_object_kind_or_lock_mismatch"),
            (b'lock="0"', b'lock="1"', "native_object_kind_or_lock_mismatch"),
            (b'<hp:autoNum num="19" numType="PICTURE"><hp:autoNumFormat type="DIGIT"', b'<hp:autoNum num="19" numType="PICTURE"><hp:autoNumFormat type="ROMAN_CAPITAL"', "number_format_invalid"),
        ]:
            with self.subTest(delta=source), tempfile.TemporaryDirectory() as directory:
                path = self.changed_package(Path(directory), "P09-19-C01", source, target)
                self.assertIn(error, oracle.inspect(path, self.manifest, "P09-19-C01", "saved")["errors"])

    def test_number_outside_selected_caption_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(BUNDLE / oracle.FILES["P09-19-C01"]) as archive:
                section = archive.read(oracle.SECTION)
            caption = re.search(br'<hp:caption\b.*?</hp:caption>', section, re.S).group()
            control = re.search(br'<hp:ctrl><hp:autoNum\b.*?</hp:ctrl>', caption, re.S).group()
            replacement = caption.replace(control, b"") + control
            path = self.changed_package(Path(directory), "P09-19-C01", caption, replacement)
            with self.assertRaisesRegex(ValueError, "object_caption_number_binding_invalid"):
                oracle.inspect(path, self.manifest, "P09-19-C01", "saved")

    def test_native_identity_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.changed_package(Path(directory), "P09-19-C02", b'id="8102"', b'id="8103"')
            with self.assertRaisesRegex(ValueError, "selected_object_identity_invalid"):
                oracle.inspect(path, self.manifest, "P09-19-C02", "saved")

    def test_manifest_weakening_promotion_and_path_escape_are_rejected(self) -> None:
        for keys, replacement in [
            (["cases", 0, "expected_saved_number"], 19),
            (["cases", 0, "file"], "../outside.hwpx"),
            (["cases", 0, "native_object_id"], 0),
            (["cases", 0, "retry_checks", "stale_source_rejected"], 1),
            (["actual_hangul"], True),
        ]:
            with self.subTest(keys=keys), tempfile.TemporaryDirectory() as directory:
                value = copy.deepcopy(self.manifest)
                cursor = value
                for key in keys[:-1]:
                    cursor = cursor[key]
                cursor[keys[-1]] = replacement
                raw = json.dumps(value).encode()
                path = Path(directory) / "manifest.json"
                path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    oracle.load_manifest(path, oracle.sha256(raw))

    def test_digest_drift_and_duplicate_json_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            oracle.load_manifest(BUNDLE / "fixture-manifest.json", "0" * 64)
        with self.assertRaises(ValueError):
            oracle.inspect(BUNDLE / oracle.FILES["P09-19-C01"], self.manifest, "P09-19-C01", "input", "0" * 64)
        with tempfile.TemporaryDirectory() as directory:
            raw = b'{"task":"P09-19","task":"P09-19"}'
            path = Path(directory) / "manifest.json"
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                oracle.load_manifest(path, oracle.sha256(raw))

    def test_duplicate_zip_entry_and_active_xml_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.hwpx"
            with warnings.catch_warnings(), zipfile.ZipFile(path, "w") as archive:
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(oracle.SECTION, b"one")
                archive.writestr("unrelated", b"two")
                archive.writestr("unrelated", b"three")
            with self.assertRaises(ValueError):
                oracle.package_snapshot(path, None)
        with tempfile.TemporaryDirectory() as directory:
            path = self.changed_package(Path(directory), "P09-19-C01", b'<?xml', b'<!DOCTYPE test><!ENTITY injected "x"><?xml')
            with self.assertRaises(ValueError):
                oracle.package_snapshot(path, None)


if __name__ == "__main__":
    unittest.main()
