from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.p09 import inspect_note_complete_fixture as q

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = "fixtures/target-build/p09-24-note-target-20261002-02/output"
MANIFEST_SHA = "ef2e30388827c40e02b99017350f434b33840ce5564c2d46b2bae9c10dac9150"


class NoteCompleteFixtureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="p09-note-complete-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in (*q.SOURCES, q.PREDECESSOR, *(str(p.relative_to(ROOT)) for p in (ROOT / BUNDLE).iterdir() if p.is_file())):
            output = self.root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes((ROOT / relative).read_bytes())
        self.manifest = self.root / BUNDLE / "fixture-manifest.json"
        self.value = json.loads(self.manifest.read_bytes())

    def inspect(self):
        raw = self.manifest.read_bytes()
        return q.inspect(self.manifest, q.shared.oracle.sha256(raw), root=self.root)

    def publish_manifest(self):
        self.manifest.write_bytes(json.dumps(self.value).encode())

    def change_package(self, index, transform, extra=None):
        row = self.value["cases"][index]
        path = self.root / BUNDLE / row["file"]
        output = io.BytesIO()
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(output, "w") as destination:
            for entry in source.infolist():
                destination.writestr(entry, transform(entry.filename, source.read(entry)))
            if extra:
                destination.writestr(*extra)
        raw = output.getvalue()
        path.write_bytes(raw)
        row["package_sha256"] = q.shared.oracle.sha256(raw)
        row["package_bytes"] = len(raw)
        with zipfile.ZipFile(path) as archive:
            row["section_sha256"] = q.shared.oracle.sha256(archive.read(q.SECTION))
        self.publish_manifest()

    def test_three_complete_packages_have_exact_notes_styles_anchors_and_seed_reversal(self):
        value = self.inspect()
        self.assertEqual(value["state"], "complete_package_static_non_green")
        self.assertEqual([len(c["native_projection"]) for c in value["cases"]], [1, 1, 2])
        for case in value["cases"]:
            self.assertTrue(case["exact_section_reversal"])
            self.assertTrue(case["all_other_expanded_parts_preserved"])
            self.assertFalse(case["actual_hangul"])
        claims = value["claims"]
        for key in ("actual_hangul", "production_routing_qualified", "note_style_convert_export_qualified",
                    "arbitrary_rich_notes", "p09_complete", "product_complete"):
            self.assertFalse(claims[key])
        self.assertEqual(claims["green_rows"], 0)
        for key in ("save_reopen", "render", "automation", "differential"):
            self.assertEqual(claims[key], "not_run")
        raw = q.shared.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn(str(self.root), raw)
        self.assertNotIn("P09 footnote &", raw)

    def test_two_complete_generations_are_byte_exact(self):
        first = ROOT / "fixtures/target-build/p09-24-note-target-20261002-01/output"
        for name in ("fixture-manifest.json", "p09-24-note-seed.hwpx", *(v[0] for v in q.CASES.values())):
            self.assertEqual((ROOT / BUNDLE / name).read_bytes(), (first / name).read_bytes())

    def test_claim_promotion_coercion_wrong_case_order_and_filename_rejected(self):
        original = copy.deepcopy(self.value)
        for key, changed in (("actual_hangul", True), ("save_reopen", "pass"), ("complete_package_graph", 1),
                             ("green_rows", False), ("seed_package_sha256", "0" * 64)):
            self.value = copy.deepcopy(original)
            self.value[key] = changed
            self.publish_manifest()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.inspect()
        self.value = copy.deepcopy(original)
        self.value["cases"].reverse()
        self.publish_manifest()
        with self.assertRaises(ValueError):
            self.inspect()
        self.value = copy.deepcopy(original)
        self.value["cases"][0]["file"] = "../outside.hwpx"
        self.publish_manifest()
        with self.assertRaisesRegex(ValueError, "note_case_filename_invalid"):
            self.inspect()

    def test_rehashed_main_text_change_cannot_hide_nonselected_damage(self):
        self.change_package(0, lambda name, raw: raw.replace(b"preserved main text", b"modified main text") if name == q.SECTION else raw)
        with self.assertRaisesRegex(ValueError, "note_nonselected_content_or_parts_changed"):
            self.inspect()

    def test_rehashed_body_change_cannot_hide_wrong_expected_value(self):
        self.change_package(0, lambda name, raw: raw.replace(b"P09 footnote", b"P09 altered ") if name == q.SECTION else raw)
        with self.assertRaisesRegex(ValueError, "note_body_expected_text_mismatch"):
            self.inspect()

    def test_wrong_native_kind_id_marker_and_unknown_attributes_rejected(self):
        path = self.root / BUNDLE / self.value["cases"][0]["file"]
        with zipfile.ZipFile(path) as archive:
            section, header = archive.read(q.SECTION), q.xml(archive.read("Contents/header.xml"))
        for before, after in ((b'instId="24001"', b'instId="24003"'), (b'number="1"', b'number="2"'),
                              (b'<hp:footNote ', b'<hp:footNote unknown="1" ')):
            changed = section.replace(before, after, 1)
            if before.startswith(b'instId'):
                projection = q.note_projection(changed, header)[0]
                self.assertNotEqual(projection[0]["native_inst_id"], 24001)
            else:
                with self.subTest(before=before), self.assertRaises(ValueError):
                    q.note_projection(changed, header)
        self.change_package(0, lambda name, raw: raw.replace(b'instId="24001"', b'instId="24003"') if name == q.SECTION else raw)
        with self.assertRaisesRegex(ValueError, "note_native_inventory_or_anchor_invalid"):
            self.inspect()

    def test_rich_body_and_stray_container_text_rejected(self):
        with zipfile.ZipFile(self.root / BUNDLE / self.value["cases"][0]["file"]) as archive:
            section, header = archive.read(q.SECTION), q.xml(archive.read("Contents/header.xml"))
        for before, after in ((b"<hp:t>P09 footnote", b"<hp:t><hp:pic/>P09 footnote"),
                              (b'<hp:run charPrIDRef="3">', b'<hp:run charPrIDRef="3">stray'),
                              (b'<hp:t>P09 footnote', b'<!--hidden--><hp:t>P09 footnote')):
            with self.subTest(before=before), self.assertRaises(ValueError):
                q.note_projection(section.replace(before, after, 1), header)

    def test_changed_header_preview_or_resource_part_is_rejected(self):
        self.change_package(2, lambda name, raw: raw + b"tamper" if name == "Preview/PrvText.txt" else raw)
        with self.assertRaisesRegex(ValueError, "note_nonselected_content_or_parts_changed"):
            self.inspect()

    def test_package_manifest_graph_cannot_point_at_missing_part(self):
        self.change_package(0, lambda name, raw: raw.replace(b'Contents/header.xml', b'Contents/absent.xml')
                            if name == "Contents/content.hpf" else raw)
        with self.assertRaisesRegex(ValueError, "note_package_manifest_graph_invalid"):
            self.inspect()

    def test_missing_body_style_definition_and_wrong_kind_are_rejected(self):
        with zipfile.ZipFile(self.root / BUNDLE / self.value["cases"][0]["file"]) as archive:
            section, header = archive.read(q.SECTION), q.xml(archive.read("Contents/header.xml"))
        changed = section.replace(b"hp:footNote", b"hp:endNote")
        with self.assertRaises(ValueError):
            q.note_projection(changed, header)
        node = next(n for n in header.iter(q.HH + "charPr") if n.get("id") == "3")
        node.set("id", "999")
        with self.assertRaisesRegex(ValueError, "note_body_style_reference_missing"):
            q.note_projection(section, header)

    def test_rehashed_combined_note_anchor_move_is_rejected(self):
        import re
        def move(name, raw):
            if name != q.SECTION:
                return raw
            wrapper = re.search(br'<hp:ctrl><hp:endNote\b.*?</hp:endNote></hp:ctrl>', raw, re.S)[0]
            raw = raw.replace(wrapper, b"", 1)
            return raw.replace(b'<hp:t>P09-24 note insertion', wrapper + b'<hp:t>P09-24 note insertion', 1)
        self.change_package(2, move)
        with self.assertRaisesRegex(ValueError, "note_native_inventory_or_anchor_invalid"):
            self.inspect()

    def test_case_alias_and_path_traversal_archive_entries_rejected(self):
        original = (self.root / BUNDLE / self.value["cases"][0]["file"]).read_bytes()
        original_manifest = copy.deepcopy(self.value)
        for name in ("contents/HEADER.xml", "../outside.xml", "Contents/extra.xml."):
            self.value = copy.deepcopy(original_manifest)
            (self.root / BUNDLE / self.value["cases"][0]["file"]).write_bytes(original)
            self.change_package(0, lambda name, raw: raw, extra=(name, b"dummy"))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "note_archive_entry_invalid"):
                self.inspect()

    def test_broken_intermediate_section_state_plan_or_negative_claim_rejected(self):
        original = copy.deepcopy(self.value)
        for key, changed in (("source_section_sha256", "0" * 64), ("source_state_sha256", "0" * 64),
                             ("plan_sha256", "bad"), ("stale_payload_rejected", 1), ("body_style_sha256", "0" * 64)):
            self.value = copy.deepcopy(original)
            self.value["cases"][2]["operations"][1][key] = changed
            self.publish_manifest()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.inspect()

    def test_frozen_implementation_and_source_seed_drift_are_rejected(self):
        path = self.root / "crates/hwpx-package/src/note_hwpx.rs"
        original = path.read_bytes()
        path.write_bytes(original + b"// source drift\n")
        with self.assertRaisesRegex(ValueError, "note_frozen_implementation_drift"):
            self.inspect()
        path.write_bytes(original)
        seed = self.root / BUNDLE / "p09-24-note-seed.hwpx"
        seed.write_bytes(seed.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "note_package_digest_mismatch"):
            self.inspect()

    def test_manifest_hash_duplicate_keys_and_outside_boundary_rejected(self):
        with self.assertRaises(ValueError):
            q.inspect(self.manifest, "0" * 64, root=self.root)
        outside = self.root / "outside.json"
        outside.write_bytes(self.manifest.read_bytes())
        with self.assertRaises(ValueError):
            q.inspect(outside, MANIFEST_SHA, root=self.root)
        self.manifest.write_bytes(b'{"task":"P09-24","task":"P09-24"}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            self.inspect()


if __name__ == "__main__":
    unittest.main()
