from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.p09 import inspect_native_form_diagnostic_fixture as q

BUNDLE = "fixtures/target-build/p09-35-native-form-diagnostics-01/output"


def repack(raw, transform, *, reverse=False, compression=None, extra=None):
    result = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(result, "w") as output:
        entries = source.infolist()
        for original in reversed(entries) if reverse else entries:
            entry = copy.copy(original)
            if compression is not None: entry.compress_type = compression
            output.writestr(entry, transform(entry.filename, source.read(original)))
        if extra: output.writestr(*extra)
    return result.getvalue()


class NativeFormDiagnosticFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = q.real_manifest()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="p09-35-diagnostic-negative-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = q.public.preparation.predecessor
        relatives = [q.q.output.prior.prior.CAPTURE, previous.MANIFEST,
                     *(q.public.preparation.CASES[name][0] for name in ("two-section-text", "two-section-radio")),
                     *(str(path.relative_to(q.ROOT)) for path in (q.ROOT / BUNDLE).iterdir())]
        for relative in relatives:
            path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((q.ROOT / relative).read_bytes())
        self.manifest = self.root / BUNDLE / "fixture-manifest.json"
        self.value = json.loads(self.manifest.read_bytes())

    def inspect(self):
        return q.inspect(self.manifest, q.q.sha(self.manifest.read_bytes()), self.root, check_authority=False)

    def write(self, value):
        self.manifest.write_bytes(json.dumps(value, ensure_ascii=False).encode())

    def change(self, index, transform, *, stage="file", **options):
        value = json.loads(self.manifest.read_bytes()); row = value["cases"][index]
        path = self.manifest.parent / row[stage]
        raw = repack(path.read_bytes(), transform, **options); path.write_bytes(raw)
        digest = q.q.sha(raw)
        key = {"file": "package_sha256", "pre_root_file": "pre_root_package_sha256", "source_file": "source_package_sha256"}[stage]
        row[key] = digest
        if stage == "file":
            row["package_bytes"] = len(raw); row["root_receipt"]["output_package_sha256"] = digest
        if stage == "pre_root_file":
            row["root_receipt"]["source_package_sha256"] = digest
            if row["property_receipt"]: row["property_receipt"]["output_package_sha256"] = digest
        self.write(value)

    def test_all_fifteen_distinct_full_inputs_and_outputs_are_independently_derived(self):
        result = self.inspect(); self.assertEqual(len(result["cases"]), 15)
        self.assertEqual([c["controls"] for c in result["cases"]], [2, 2] + [1] * 13)
        self.assertEqual([c["property_attribute_count"] for c in result["cases"]], [0,0,1,1,2,3,2,1,1,1,1,1,1,1,1])
        self.assertEqual(sum(c["root_href_attribute_count"] for c in result["cases"]), 2)
        self.assertEqual(len({c["package_sha256"] for c in result["cases"]}), 15)
        self.assertFalse(result["claims"]["actual_hangul"])
        self.assertFalse(result["claims"]["independent_python_full_domain_serializer_qualified"])
        self.assertEqual(result["claims"]["green_rows"], 0)
        q.verify_real_manifest(self.value, self.probe)

    def test_exact_public_source_capsule_fifty_pins_and_prior_receipts_remain_valid(self):
        self.assertEqual(q.authority(), q.CAPSULE_SHA)

    def test_native_product_render_promotions_extra_claims_and_boolean_coercion_rejected(self):
        for key, value in (("actual_hangul", True), ("actual_hangul", 0), ("green_rows", False), ("render", "pass"),
                           ("new_native_claim", True), ("source_policy", "native_inferred")):
            changed = copy.deepcopy(self.value); changed[key] = value; self.write(changed)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "diagnostic_manifest_claims_invalid"): self.inspect()

    def test_short_extra_duplicate_and_reordered_case_inventory_rejected(self):
        cases = self.value["cases"]
        for mutated in (cases[:-1], cases + [cases[0]], list(reversed(cases))):
            changed = copy.deepcopy(self.value); changed["cases"] = mutated; self.write(changed)
            with self.assertRaises(ValueError): self.inspect()

    def test_fixed_filenames_maps_missing_sections_and_coerced_control_counts_rejected(self):
        for key, value in (("file", "../outside.hwpx"), ("source_file", "../source.hwpx"), ("controls", True),
                           ("case_id", "P09-35-C02"), ("complete_map", q.q.expected_map(1)), ("extra", True)):
            changed = copy.deepcopy(self.value); changed["cases"][0][key] = value; self.write(changed)
            with self.subTest(key=key), self.assertRaises(ValueError): self.inspect()

    def test_red_requested_foreground_is_not_silently_approximated_to_existing_blue_style(self):
        for index in (2, 6):
            self.setUp()
            transform = lambda name, raw: q.q.edit_tag(raw, "edit", {"foreColor":"#2E74B5"}) if name == "Contents/section0.xml" else raw
            self.change(index, transform, stage="pre_root_file"); self.change(index, transform)
            with self.assertRaisesRegex(ValueError, "diagnostic_property_complete_output_mismatch"): self.inspect()

    def test_each_requested_name_metacharacter_cannot_be_removed_to_get_pass(self):
        for index in range(9, 14):
            self.setUp()
            transform = lambda name, raw: q.q.edit_tag(raw, "edit", {"name":"P09 이름 폼"}) if name == "Contents/section0.xml" else raw
            self.change(index, transform, stage="pre_root_file"); self.change(index, transform)
            with self.assertRaisesRegex(ValueError, "diagnostic_property_complete_output_mismatch"): self.inspect()

    def test_group_only_case_may_not_rename_the_native_field_or_drop_group_metacharacters(self):
        for fields in ({"groupName":"P09 그룹"}, {"name":"unexpected replacement"}):
            self.setUp()
            transform = lambda name, raw: q.q.edit_tag(raw, "edit", fields) if name == "Contents/section0.xml" else raw
            self.change(14, transform, stage="pre_root_file"); self.change(14, transform)
            with self.assertRaisesRegex(ValueError, "diagnostic_property_complete_output_mismatch"): self.inspect()

    def test_rehashed_unselected_part_header_preview_metadata_and_body_drift_not_hidden(self):
        for part in ("Contents/header.xml", "Preview/PrvImage.png", "Contents/section0.xml", "Contents/content.hpf", "settings.xml"):
            self.setUp(); self.change(0, lambda name, raw: raw + b" " if name == part else raw)
            with self.assertRaisesRegex(ValueError, "diagnostic_root_complete_output_mismatch"): self.inspect()

    def test_unprepared_old_native_failure_input_cannot_substitute_for_new_root_candidate(self):
        row = self.value["cases"][0]; source = (self.manifest.parent / row["source_file"]).read_bytes()
        (self.manifest.parent / row["file"]).write_bytes(source)
        row["package_sha256"] = q.q.sha(source); row["package_bytes"] = len(source); self.write(self.value)
        with self.assertRaisesRegex(ValueError, "diagnostic_root_complete_output_mismatch"): self.inspect()

    def test_rehashed_original_source_or_prior_failed_source_substitution_rejected(self):
        for index in (0, 2):
            self.setUp(); self.change(index, lambda name, raw: raw + b" " if name == "Contents/header.xml" else raw, stage="source_file")
            with self.assertRaisesRegex(ValueError, "diagnostic_original_source_substituted"): self.inspect()

    def test_root_noop_raw_rewrite_order_compression_and_extra_parts_rejected(self):
        for index, options in ((2, {"compression":zipfile.ZIP_STORED}), (0, {"reverse":True}),
                               (0, {"compression":zipfile.ZIP_STORED}), (0, {"extra":("extra.xml",b"<extra/>")})):
            self.setUp(); self.change(index, lambda name, raw: raw, **options)
            with self.assertRaises(ValueError): self.inspect()

    def test_root_state_transition_must_not_be_masked_and_receipts_need_exact_types(self):
        for key, value in (("packaging_transition_changes_complete_state", False), ("target_state_sha256", self.value["cases"][0]["pre_root_state_sha256"]),
                           ("root_control_intent_and_flow_preserved", 1), ("deterministic_retry", 1), ("stale_source_rejected", False)):
            changed = copy.deepcopy(self.value); changed["cases"][0][key] = value; self.write(changed)
            with self.subTest(key=key), self.assertRaises(ValueError): self.inspect()

    def test_forged_coherent_typed_hashes_or_receipts_fail_fresh_actual_public_probe(self):
        for key in ("policy_sha256", "target_state_sha256", "target_controls_sha256"):
            changed = copy.deepcopy(self.value)
            changed["cases"][2][key] = ["0"*64] if key == "target_controls_sha256" else "0"*64
            if key == "target_state_sha256":
                changed["cases"][2]["pre_root_state_sha256"] = "0"*64
                changed["cases"][2]["property_receipt"]["target_state_sha256"] = "0"*64
            with self.assertRaisesRegex(ValueError, "diagnostic_actual_public_manifest_mismatch"):
                q.verify_real_manifest(changed, self.probe)

    def test_missing_extra_files_and_active_xml_rejected_without_extraction(self):
        extra = self.manifest.parent / "unexpected.bin"; extra.write_bytes(b"not an input")
        with self.assertRaisesRegex(ValueError, "diagnostic_complete_file_inventory_invalid"): self.inspect()
        self.setUp(); self.change(0, lambda name, raw: b'<!DOCTYPE x [<!ENTITY secret "not-expanded">]><x/>' if name == "settings.xml" else raw)
        with self.assertRaisesRegex(ValueError, "form_active_xml_rejected"): self.inspect()

    def test_compiled_failed_missing_ignored_extra_results_and_full_qualification_scope(self):
        stdout = "\n".join(f"test {name} ... ok" for name in sorted(q.EXPECTED_TESTS)) + "\ntest result: ok. 4 passed; 0 failed; 0 ignored;\n"
        q.test_inventory(stdout)
        for changed in (stdout.replace(" ... ok", " ... ignored", 1), stdout.replace(" ... ok", " ... FAILED", 1),
                        stdout.replace("4 passed", "3 passed"), stdout + "test extra ... ok\n"):
            with self.assertRaises(ValueError): q.test_inventory(changed)
        path = q.ROOT / BUNDLE / "fixture-manifest.json"; digest = q.q.sha(q.public.bounded_bytes(path, 512 * 1024))
        value = q.qualify(path, digest)
        self.assertTrue(value["actual_public_generator_manifest_exact"])
        self.assertEqual(value["actual_public_generator_rust_tests"]["passed"], 4)
        self.assertEqual(value["read_only_missing_native_output_probe"]["not_run_stages"], 30)
        self.assertFalse(value["read_only_missing_native_output_probe"]["native_session_started"])
        for key in ("actual_hangul", "native_open_failure_resolved", "arbitrary_color_or_name_repair_qualified", "native_normalization_qualified", "production_routing_qualified", "p09_complete"):
            self.assertFalse(value["claims"][key])
        raw = q.q.shared.lifecycle.canonical_bytes(value).decode()
        for secret in (str(q.ROOT), "P08FORMINSERT", "P09 이름", "P09 그룹"): self.assertNotIn(secret, raw)


if __name__ == "__main__":
    unittest.main()
