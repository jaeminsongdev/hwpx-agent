from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.p09 import qualify_click_here_update_target as q

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = "fixtures/target-build/p09-22-click-here-update-target-20261002-02/output"
MANIFEST_SHA = "d61d28d10aff3e9b7ee4e73a397ba0e96e97630737ff9718862b6ddb12387876"
ATTEMPT = "implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-22-20261002-c01-attempt01"
TRACE_SHA = "9d34161d5181cf5d374843a09aee985db7f89b884bc4280275e5e14604b18f3f"


class ClickHereUpdateTargetTests(unittest.TestCase):
    def setUp(self):
        # Current-PC captured corpus is mandatory, never replaced by a synthetic PASS or skip.
        temporary = tempfile.TemporaryDirectory(prefix="p09-click-here-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        relatives = [q.BRIDGE, *q.SOURCES,
                     "fixtures/target-build/official-source-cache/devcenter-archive-main-20260906/hwp-automation/HwpAutomation.pdf"]
        for directory in (BUNDLE, ATTEMPT, q.DISCOVERY):
            relatives.extend(str(p.relative_to(ROOT)) for p in (ROOT / directory).iterdir() if p.is_file())
        for relative in dict.fromkeys(relatives):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        self.manifest = self.root / BUNDLE / "fixture-manifest.json"
        self.value = json.loads(self.manifest.read_bytes())
        self.attempt = self.root / ATTEMPT
        self.trace = json.loads((self.attempt / "target-trace.json").read_bytes())

    def prepare(self):
        raw = self.manifest.read_bytes()
        return q.prepare(self.manifest, q.oracle.sha256(raw), root=self.root)

    def qualify(self):
        raw = q.lifecycle.canonical_bytes(self.trace)
        (self.attempt / "target-trace.json").write_bytes(raw)
        return q.qualify(self.manifest, MANIFEST_SHA, "P09-22-C01", self.attempt,
                         q.oracle.sha256(raw), root=self.root, access_attested=True)

    def rewrite_package(self, path, edit):
        buffer = io.BytesIO()
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(buffer, "w") as output:
            for entry in source.infolist():
                output.writestr(entry, edit(entry.filename, source.read(entry)))
        path.write_bytes(buffer.getvalue())
        return buffer.getvalue()

    def test_two_real_inputs_preserve_exact_declared_edit_boundary(self):
        _, rows = self.prepare()
        self.assertEqual(list(rows), list(q.CASES))
        self.assertEqual(rows["P09-22-C01"][1]["selected_character_style_refs"], ["7"])
        self.assertEqual(rows["P09-22-C02"][1]["selected_character_style_refs"], ["0"])

    def test_repeat_complete_package_generation_is_identical(self):
        retry = ROOT / "fixtures/target-build/p09-22-click-here-update-target-20261002-01/output"
        for name in ("fixture-manifest.json", *(row[2] for row in q.CASES.values())):
            self.assertEqual((ROOT / BUNDLE / name).read_bytes(), (retry / name).read_bytes())

    def test_actual_trace_preserves_cache_and_reports_real_differential_mismatch(self):
        value = q.qualify(self.manifest, MANIFEST_SHA, "P09-22-C01", self.attempt,
                          TRACE_SHA, root=self.root, access_attested=True)
        self.assertEqual(value["state"], "bounded_cached_semantic_non_green")
        self.assertEqual(value["errors"], [])
        self.assertTrue(value["claims"]["bounded_existing_click_here_cache_preservation"])
        self.assertEqual(value["saved_reopened_pdf_stability"]["changed_pixels"], 0)
        compared = value["automation_comparison"]
        self.assertEqual(compared["state"], "observed_mismatch_non_gate")
        self.assertTrue(compared["text_equal"])
        self.assertFalse(compared["character_definitions_equal"])
        self.assertEqual(compared["pdf"]["changed_pixels"], 920)
        self.assertEqual(compared["pdf"]["absolute_rgb_delta_sum"], 215567)
        self.assertFalse(compared["pdf"]["masks_or_tolerances_used"])
        self.assertFalse(compared["product_differential_qualified"])
        self.assertEqual(value["register_module_returns"], [False, False])
        for key in ("p09_complete", "product_complete", "product_routing_qualified",
                    "general_field_update_api_qualified", "field_insertion_qualified", "field_locking_qualified"):
            self.assertFalse(value["claims"][key])
        self.assertEqual(value["claims"]["green_rows"], 0)
        encoded = q.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn("P09 value &", encoded)

    def test_manifest_promotion_bool_coercion_and_case_substitution_rejected(self):
        for key, changed in (("actual_hangul", True), ("render", "pass"), ("green_rows", False),
                             ("p09_complete", True), ("complete_package_graph", 1)):
            value = copy.deepcopy(self.value)
            value[key] = changed
            self.manifest.write_bytes(json.dumps(value).encode())
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare()
        value = copy.deepcopy(self.value)
        value["cases"].reverse()
        self.manifest.write_bytes(json.dumps(value).encode())
        with self.assertRaises(ValueError):
            self.prepare()

    def test_manifest_native_identity_display_and_source_claims_rejected(self):
        for key, changed in (("native_field_id", 1210042100), ("expected_display_sha256", "0" * 64),
                             ("file", "../outside.hwpx"), ("stale_source_rejected", 1),
                             ("source_package_sha256", "0" * 64)):
            value = copy.deepcopy(self.value)
            value["cases"][0][key] = changed
            self.manifest.write_bytes(json.dumps(value).encode())
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare()

    def test_rehashed_nonselected_content_change_is_not_hidden_by_manifest(self):
        path = self.root / BUNDLE / q.CASES["P09-22-C01"][2]
        raw = self.rewrite_package(path, lambda name, data: data.replace(b'paraPrIDRef="0"', b'paraPrIDRef="1"', 1)
                                   if name == q.oracle.SECTION else data)
        self.value["cases"][0]["output_package_sha256"] = q.oracle.sha256(raw)
        self.value["cases"][0]["output_package_bytes"] = len(raw)
        self.manifest.write_bytes(json.dumps(self.value).encode())
        with self.assertRaisesRegex(ValueError, "click_declared_edits_or_resources_changed"):
            self.prepare()

    def test_selected_value_change_cannot_be_hidden_by_rehashing(self):
        path = self.root / BUNDLE / q.CASES["P09-22-C01"][2]
        raw = self.rewrite_package(path, lambda name, data: data.replace(b"P09 value", b"P09 other", 1)
                                   if name == q.oracle.SECTION else data)
        self.value["cases"][0]["output_package_sha256"] = q.oracle.sha256(raw)
        self.manifest.write_bytes(json.dumps(self.value).encode())
        with self.assertRaises(ValueError):
            self.prepare()

    def test_duplicate_pair_rich_text_unknown_parameter_and_cross_pair_rejected(self):
        row = self.value["cases"][0]
        with zipfile.ZipFile(self.root / BUNDLE / row["file"]) as archive:
            section, header = archive.read(q.oracle.SECTION), archive.read("Contents/header.xml")
        changes = [(b'fieldid="627272811"/>', b'fieldid="627272812"/>'),
                   (b'type="CLICK_HERE"', b'type="PAGE"'),
                   (b'name="Prop"', b'name="Other"'),
                   (b'<hp:t>P09 value', b'<hp:t><hp:unknown/>P09 value'),
                   (b'<hp:fieldEnd ', b'<hp:fieldEnd unknown="1" '),
                   (b'<hp:parameters ', b'<hp:parameters unknown="1" ')]
        for old, new in changes:
            self.assertIn(old, section)
            with self.subTest(change=old), self.assertRaises(ValueError):
                q.native(section.replace(old, new, 1), header)

    def test_trace_drift_wrong_profile_nonfresh_session_and_privacy_rejected(self):
        for key, changed in (("input_sha256", "0" * 64), ("input_bytes", False),
                             ("fresh_reopen", "not_run"), ("remaining_hwp_process_count", False),
                             ("computer_use_click_or_type_invoked", True)):
            original = self.trace[key]
            self.trace[key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.qualify()
            self.trace[key] = original
        self.trace["sessions"][1]["process"]["process_id"] = self.trace["sessions"][0]["process"]["process_id"]
        with self.assertRaisesRegex(ValueError, "fresh_session_not_independent"):
            self.qualify()

    def test_target_output_and_pdf_hash_or_size_drift_rejected(self):
        for filename in ("saved.hwpx", "reopened.pdf"):
            path = self.attempt / filename
            raw = path.read_bytes()
            path.write_bytes(raw + b"tamper")
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.qualify()
            path.write_bytes(raw)
        self.trace["output_bytes"] = False
        with self.assertRaises(ValueError):
            self.qualify()

    def test_rehashed_saved_semantic_failure_is_retained_not_promoted(self):
        raw = self.rewrite_package(self.attempt / "saved.hwpx",
                                   lambda name, data: data.replace(b"P09 value", b"P09 other", 1)
                                   if name == q.oracle.SECTION else data)
        # Adversarial derivative of the captured trace, not published as real target evidence.
        self.trace["output_sha256"] = q.oracle.sha256(raw)
        self.trace["output_bytes"] = len(raw)
        value = self.qualify()
        self.assertEqual(value["state"], "failed_semantic_non_green")
        self.assertIn("saved_field_section_changed", value["errors"])
        self.assertFalse(value["claims"]["bounded_existing_click_here_cache_preservation"])
        self.assertTrue(value["claims"]["actual_open_save_fresh_reopen"])
        self.assertEqual(value["claims"]["green_rows"], 0)

    def test_native_discovery_artifact_and_source_bridge_drift_rejected(self):
        path = self.root / q.DISCOVERY / "filled.hwpx"
        original = path.read_bytes()
        path.write_bytes(original + b"tamper")
        with self.assertRaises(ValueError):
            q.discovery(self.root)
        path.write_bytes(original)
        path = self.root / "crates/hwpx-package/src/click_here_hwpx.rs"
        path.write_bytes(path.read_bytes() + b"// drift\n")
        with self.assertRaisesRegex(ValueError, "click_source_bridge_drift"):
            self.qualify()

    def test_outside_boundary_duplicate_json_and_wrong_hash_rejected(self):
        outside = self.root / "outside.json"
        outside.write_bytes(self.manifest.read_bytes())
        with self.assertRaises(ValueError):
            q.prepare(outside, MANIFEST_SHA, root=self.root)
        with self.assertRaises(ValueError):
            q.prepare(self.manifest, "0" * 64, root=self.root)
        self.manifest.write_bytes(b'{"task":"P09-22","task":"P09-22"}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            self.prepare()

    def test_discovery_cannot_outlive_changed_lifecycle_helper_or_official_api(self):
        for relative in ("implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1",
                         "fixtures/target-build/official-source-cache/devcenter-archive-main-20260906/hwp-automation/HwpAutomation.pdf"):
            path = self.root / relative
            raw = path.read_bytes()
            path.write_bytes(raw + b"drift")
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "click_discovery_authority_drift"):
                q.discovery(self.root)
            path.write_bytes(raw)


if __name__ == "__main__":
    unittest.main()
