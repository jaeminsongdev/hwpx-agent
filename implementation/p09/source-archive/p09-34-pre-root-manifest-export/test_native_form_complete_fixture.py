from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.p09 import inspect_native_form_complete_fixture as q

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = "fixtures/target-build/p09-32-native-form-target-20261002-01/output"
MANIFEST_SHA = "f07a8a73dbead998db253050d011ebe58ac331c42060b31c0c7a617a23ad8ef8"


def repack(raw, transform, *, reverse=False, extra=None, compression=None):
    result = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(result, "w") as destination:
        entries = source.infolist()
        for entry in reversed(entries) if reverse else entries:
            data = source.read(entry)
            entry = copy.copy(entry)
            if compression is not None:
                entry.compress_type = compression
            destination.writestr(entry, transform(entry.filename, data))
        if extra:
            destination.writestr(*extra)
    return result.getvalue()


class CompleteNativeFormFixtureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="p09-32-form-preflight-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for relative in (q.output.prior.prior.CAPTURE, *(str(p.relative_to(ROOT)) for p in (ROOT / BUNDLE).iterdir())):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.manifest = self.root / BUNDLE / "fixture-manifest.json"
        self.original = json.loads(self.manifest.read_bytes())

    def inspect(self):
        return q.inspect(self.manifest, q.sha(self.manifest.read_bytes()), self.root, check_authority=False)

    def manifest_value(self, value):
        self.manifest.write_bytes(json.dumps(value, ensure_ascii=False).encode())

    def modify(self, index, transform, *, source=False, **options):
        value = json.loads(self.manifest.read_bytes())
        row = value["cases"][index]
        path = self.manifest.parent / row["source_file" if source else "file"]
        raw = repack(path.read_bytes(), transform, **options)
        path.write_bytes(raw)
        if source:
            row["source_package_sha256"] = q.sha(raw)
            row["receipt"]["source_package_sha256"] = q.sha(raw)
        else:
            row["package_sha256"] = q.sha(raw)
            row["package_bytes"] = len(raw)
            row["receipt"]["output_package_sha256"] = q.sha(raw)
        self.manifest_value(value)

    def test_six_complete_outputs_independently_match_source_edits_and_all_parts(self):
        result = self.inspect()
        self.assertEqual([n["changed_attributes"] for n in result["cases"]], [1, 3, 2, 4, 2, 1])
        self.assertEqual([n["controls"] for n in result["cases"]], [1, 1, 1, 1, 2, 2])
        self.assertEqual(result["claims"]["green_rows"], 0)
        self.assertFalse(result["claims"]["actual_hangul"])
        self.assertFalse(result["claims"]["independent_python_full_domain_serializer_qualified"])
        public = q.shared.lifecycle.canonical_bytes(result).decode()
        self.assertNotIn(str(self.root), public)
        self.assertNotIn("P09 새", public)

    def test_unchanged_public_source_authority_and_harness_are_still_exact(self):
        self.assertEqual(q.authority(ROOT), q.CAPSULE_SHA)

    def test_promoted_claims_coerced_boolean_and_extra_manifest_fields_rejected(self):
        for key, value in (("actual_hangul", True), ("green_rows", False), ("render", "pass"), ("new_claim", True)):
            changed = copy.deepcopy(self.original)
            changed[key] = value
            self.manifest_value(changed)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "form_manifest_claims_invalid"):
                self.inspect()

    def test_wrong_case_order_path_and_source_kind_rejected(self):
        for key, value in (("file", "../outside.hwpx"), ("case_id", "P09-32-C02"), ("source_kind", "original_native_capture")):
            changed = copy.deepcopy(self.original)
            changed["cases"][5][key] = value
            self.manifest_value(changed)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.inspect()
        changed = copy.deepcopy(self.original)
        changed["cases"].reverse()
        self.manifest_value(changed)
        with self.assertRaises(ValueError):
            self.inspect()

    def test_rehashed_wrong_intent_enabled_value_is_rejected(self):
        self.modify(0, lambda n, r: r.replace(b'enabled="0"', b'enabled="1"') if n == "Contents/section0.xml" else r)
        with self.assertRaisesRegex(ValueError, "form_independent_complete_output_mismatch"):
            self.inspect()

    def test_rehashed_nonselected_header_and_preview_damage_are_rejected(self):
        for name in ("Contents/header.xml", "Preview/PrvImage.png"):
            # Separate test snapshots keep failed mutations local, never fixture originals.
            original = (ROOT / BUNDLE / q.FILES[0]).read_bytes()
            (self.manifest.parent / q.FILES[0]).write_bytes(original)
            self.manifest_value(copy.deepcopy(self.original))
            self.modify(0, lambda n, r: r.replace(b'secCnt="1"', b'secCnt="2"') if n == "Contents/header.xml" and n == name else r + b"X" if n == name else r)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.inspect()

    def test_rehashed_source_derivation_damage_cannot_be_hidden(self):
        self.modify(4, lambda n, r: r.replace(b'tabOrder="2"', b'tabOrder="3"') if n == "Contents/section1.xml" else r, source=True)
        with self.assertRaisesRegex(ValueError, "form_complete_source_derivation_mismatch"):
            self.inspect()

    def test_original_raw_capture_not_replaced_by_recompressed_copy(self):
        self.modify(0, lambda n, r: r, source=True, compression=zipfile.ZIP_STORED)
        with self.assertRaisesRegex(ValueError, "form_original_source_substituted"):
            self.inspect()

    def test_complete_map_count_identity_and_boolean_receipt_are_checked(self):
        changed = copy.deepcopy(self.original)
        changed["cases"][4]["complete_map"]["sections"].pop()
        self.manifest_value(changed)
        with self.assertRaisesRegex(ValueError, "form_complete_map_mismatch"):
            self.inspect()
        changed = copy.deepcopy(self.original)
        changed["cases"][0]["receipt"]["changed_attributes"] = True
        self.manifest_value(changed)
        with self.assertRaisesRegex(ValueError, "form_output_receipt_mismatch"):
            self.inspect()

    def test_wrong_global_tab_and_radio_values_rejected_despite_refreshed_hashes(self):
        self.modify(5, lambda n, r: r.replace(b'value="CHECKED"', b'value="UNCHECKED"') if n == "Contents/section0.xml" else r)
        with self.assertRaisesRegex(ValueError, "form_independent_complete_output_mismatch"):
            self.inspect()

    def test_extra_part_changed_order_and_compression_rejected(self):
        for options in ({"extra": ("extra.bin", b"unexpected")}, {"reverse": True}, {"compression": zipfile.ZIP_STORED}):
            (self.manifest.parent / q.FILES[0]).write_bytes((ROOT / BUNDLE / q.FILES[0]).read_bytes())
            self.manifest_value(copy.deepcopy(self.original))
            self.modify(0, lambda n, r: r, **options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.inspect()

    def test_strict_native_semantics_do_not_mask_property_or_character_damage(self):
        raw = (ROOT / BUNDLE / q.FILES[0]).read_bytes()
        matched = q.compare_native(raw, raw)
        self.assertEqual(matched["strict_form_semantics"], "pass")
        for name, old, new in (("Contents/section0.xml", b'enabled="0"', b'enabled="1"'),
                               ("Contents/header.xml", b'height="1000"', b'height="999"')):
            changed = repack(raw, lambda n, r: r.replace(old, new) if n == name else r)
            self.assertNotEqual(changed, raw)
            observed = q.compare_native(raw, changed)
            with self.subTest(name=name):
                self.assertEqual(observed["strict_form_semantics"], "fail")
                self.assertEqual(observed["raw_preservation"], "fail")
                self.assertFalse(observed["native_normalization_qualified"])

    def test_non_form_raw_drift_is_not_semantic_acceptance_of_whole_package(self):
        raw = (ROOT / BUNDLE / q.FILES[0]).read_bytes()
        changed = repack(raw, lambda n, r: r + b"X" if n == "Preview/PrvImage.png" else r)
        result = q.compare_native(raw, changed)
        self.assertEqual(result["strict_form_semantics"], "pass")
        self.assertEqual(result["raw_preservation"], "fail")
        self.assertEqual(result["green_rows"], 0)

    def test_native_session_paths_are_complete_bounded_and_deterministic(self):
        paths = q.attempt_paths("p09-32-20261002")
        self.assertEqual(len(set(paths)), 6)
        for value in ("../escape", "x" * 41, "UPPER", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                q.attempt_paths(value)


if __name__ == "__main__":
    unittest.main()
