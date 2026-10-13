from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from tools.p09 import qualify_note_native_batch as q


class NoteNativeBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.captures = {}
        for case, (slot, digest) in q.ATTEMPTS.items():
            path = q.ROOT / "implementation/p09/evidence/private" / slot
            trace = q.shared.lifecycle.checked_json(path / "target-trace.json", digest)
            _, section, _, header = q.prepared.package(path / "saved.hwpx", trace["output_sha256"])
            cls.captures[case] = (section, header, trace, path)

    def test_three_actual_captures_have_bound_body_and_declared_native_additions(self):
        for case, (section, header, _, _) in self.captures.items():
            with self.subTest(case=case):
                projection, additions, _ = q.native_projection(section, header)
                self.assertEqual(len(projection), 2 if case.endswith("03") else 1)
                self.assertEqual(additions["native_added_suffix_wchar"], 41)
                self.assertEqual(additions["native_layout_count"], 1 + 2 * len(projection))
                self.assertEqual(additions["body_auto_number_field_count"], 0)
                self.assertEqual(additions["preparation_oracle_state"], "fail")

    def test_frozen_preparation_oracle_really_rejects_actual_native_marker(self):
        section, header, _, _ = self.captures["P09-24-C01"]
        with self.assertRaisesRegex(ValueError, "note_marker_shape_invalid"):
            q.prepared.note_projection(section, header)

    def test_unknown_or_changed_native_suffix_rejected(self):
        section, header, _, _ = self.captures["P09-24-C01"]
        for changed in (section.replace(b'suffixChar="41"', b'suffixChar="42"'),
                        section.replace(b'suffixChar="41"', b'prefixChar="41"'),
                        section.replace(b'suffixChar="41"', b'suffixChar="41" unknown="1"')):
            with self.subTest(sha=q.shared.oracle.sha256(changed)), self.assertRaisesRegex(ValueError, "native_note_marker_observation_invalid"):
                q.native_projection(changed, header)

    def test_layout_grammar_and_inventory_not_blindly_ignored(self):
        section, header, _, _ = self.captures["P09-24-C01"]
        mutations = (section.replace(b'<hp:linesegarray>', b'<hp:linesegarray changed="1">', 1),
                     section.replace(b'baseline="', b'unknown="', 1),
                     section.replace(b'<hp:linesegarray>', b'<hp:wrong>', 1),
                     section.replace(b'textpos="0"', b'textpos="00"', 1))
        for value in mutations:
            with self.subTest(sha=q.shared.oracle.sha256(value)), self.assertRaises((ValueError, q.ET.ParseError)):
                q.native_projection(value, header)

    def test_body_or_character_style_damage_does_not_match_original(self):
        section, header, _, _ = self.captures["P09-24-C01"]
        original, _, _ = q.native_projection(section, header)
        changed = section.replace(b'P09 footnote', b'P09 tampered', 1)
        with self.assertRaisesRegex(ValueError, "note_body_expected_text_mismatch"):
            q.native_projection(changed, header)
        changed = section.replace(b'charPrIDRef="3"', b'charPrIDRef="0"', 1)
        with self.assertRaisesRegex(ValueError, "note_body_run_shape_invalid"):
            q.native_projection(changed, header)
        self.assertEqual(len(original), 1)

    def test_mixed_instance_or_anchor_drift_is_visible(self):
        section, header, _, _ = self.captures["P09-24-C03"]
        original, _, _ = q.native_projection(section, header)
        changed = section.replace(b'instId="24002"', b'instId="24003"')
        moved, _, _ = q.native_projection(changed, header)
        self.assertNotEqual(moved, original)
        self.assertNotEqual(moved[-1]["native_inst_id"], original[-1]["native_inst_id"])

    def test_native_styles_cannot_disappear_or_mutate_unnoticed(self):
        _, header, _, _ = self.captures["P09-24-C01"]
        original = q.style_definitions(header)
        changed = copy.deepcopy(header)
        node = next(n for n in changed.iter(q.prepared.HH + "charPr") if n.get("id") == "3")
        node.set("height", "999")
        self.assertNotEqual(q.style_definitions(changed), original)
        node.set("id", "300")
        with self.assertRaisesRegex(ValueError, "native_note_style_inventory_invalid"):
            q.style_definitions(changed)

    def test_reused_native_process_or_claim_coercion_rejected(self):
        _, _, trace, _ = self.captures["P09-24-C01"]
        manifest = {"input_package_sha256": trace["input_sha256"], "input_package_bytes": trace["input_bytes"]}
        bad = copy.deepcopy(trace)
        bad["sessions"][1]["process"]["process_id"] = bad["sessions"][0]["process"]["process_id"]
        with self.assertRaisesRegex(ValueError, "fresh_session_not_independent"):
            q.shared.lifecycle.verify_trace(bad, manifest)
        bad = copy.deepcopy(trace)
        bad["remaining_hwp_process_count"] = False
        with self.assertRaisesRegex(ValueError, "lifecycle_trace_mismatch"):
            q.shared.lifecycle.verify_trace(bad, manifest)

    def test_native_two_page_mixed_pdf_stability_not_one_page_shortcut(self):
        _, _, _, path = self.captures["P09-24-C03"]
        observed = q.pdf_stability(path / "saved.pdf", path / "reopened.pdf", 2)
        self.assertEqual(observed["state"], "equal")
        self.assertEqual(len(observed["pages"]), 2)
        self.assertEqual(sum(p["changed_pixels"] for p in observed["pages"]), 0)
        self.assertFalse(observed["masks_or_tolerances_used"])
        with self.assertRaisesRegex(ValueError, "native_note_pdf_page_profile_invalid"):
            q.pdf_stability(path / "saved.pdf", path / "reopened.pdf", 1)

    def test_actual_qualification_stays_private_scoped_and_non_green(self):
        value = q.qualify()
        self.assertEqual(value["state"], "failed_semantic_non_green")
        self.assertEqual(len(value["cases"]), 3)
        self.assertTrue(value["claims"]["actual_three_case_save_fresh_reopen"])
        self.assertFalse(value["claims"]["bounded_note_body_preservation"])
        self.assertTrue(value["claims"]["bounded_note_text_style_anchor_readback"])
        self.assertTrue(all(row["errors"] for row in value["cases"]))
        self.assertTrue(all(snap["typed_text_style_marker_anchor_equal"] for row in value["cases"] for snap in row["snapshots"].values()))
        for key in ("native_body_numbering_qualified", "product_routing_qualified", "p09_complete", "product_complete"):
            self.assertFalse(value["claims"][key])
        self.assertEqual(value["claims"]["green_rows"], 0)
        raw = q.shared.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn("P09 footnote &", raw)
        self.assertNotIn(str(q.ROOT), raw)
        self.assertTrue(all(row["user_access_state"] == "not_attested" for row in value["cases"]))

    def test_preparation_source_drift_fails_before_artifact_use(self):
        prior = q.shared.lifecycle.checked_json(q.ROOT / q.PREPARATION, q.PREPARATION_SHA)
        first = next(iter(prior["source_sha256"]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (q.PREPARATION, first):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((q.ROOT / name).read_bytes())
            target = root / first
            target.write_bytes(target.read_bytes() + b"\n# drift\n")
            with self.assertRaisesRegex(ValueError, "native_note_preparation_source_drift"):
                q.qualify(root)


if __name__ == "__main__":
    unittest.main()
