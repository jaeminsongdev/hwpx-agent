from __future__ import annotations
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.p09 import inspect_native_form_value_output as oracle
from tools.p09 import qualify_native_form_value_output as q


class NativeFormValueOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=q.ROOT / "fixtures/target-build")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.actual = q.generate(cls.directory)
        cls.original = {p.name: p.read_bytes() for p in cls.directory.iterdir()}

    def copied(self):
        temporary = tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=q.ROOT / "fixtures/target-build")
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name)
        for name, raw in self.original.items():
            (destination / name).write_bytes(raw)
        return destination

    def altered_output(self, label, transform):
        destination = self.copied()
        manifest = json.loads((destination / "fixture-manifest.json").read_bytes())
        row = next(r for r in manifest["cases"] if r["case"] == label)
        original = (destination / row["output"]["path"]).read_bytes()
        expanded = oracle.load_zip(original)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for name, method, value in transform(expanded):
                archive.writestr(name, value, compress_type=method)
        value = output.getvalue()
        (destination / row["output"]["path"]).write_bytes(value)
        row["output"]["bytes"], row["output"]["sha256"] = len(value), oracle.sha(value)
        row["receipt"]["output_package_sha256"] = oracle.sha(value)
        (destination / "fixture-manifest.json").write_bytes(json.dumps(manifest, separators=(",", ":")).encode())
        return destination

    def test_five_actual_compiled_outputs_independently_verify_full_parts_gaps_values_and_fingerprints(self):
        self.assertEqual(self.actual["compiled_tests"]["passed"], 25)
        independent = self.actual["independent_oracle"]
        self.assertEqual([r["case"] for r in independent["cases"]], list(oracle.CASES))
        self.assertEqual([r["changed_controls"] for r in independent["cases"]], [1, 6, 1, 4, 2])
        self.assertEqual([r["controls"] for r in independent["cases"]], [1, 6, 6, 6, 6])
        self.assertEqual(independent["artifact_files"], 11)
        self.assertTrue(independent["whole_package_and_gap_preservation"])
        self.assertFalse(independent["native_execution_qualified"])
        self.assertEqual(oracle.inspect_bundle(self.directory), independent)

    def test_wrong_target_value_with_coherently_updated_package_claims_rejects(self):
        destination = self.altered_output("five-kinds", lambda parts: [(n, m, v.replace("新".encode(), b"X") if n == "Contents/section0.xml" else v) for n, m, v in parts])
        with self.assertRaisesRegex(ValueError, "value_oracle_whole_section_gaps"):
            oracle.inspect_bundle(destination)

    def test_unknown_attribute_child_and_nonsection_bytes_are_not_discarded(self):
        for name, a, b in [("Contents/section0.xml", b"opaque &amp; fixed", b"coherent-unknown-change"), ("Contents/section1.xml", b"opaque-bytes", b"changed"), ("Contents/header.xml", b'secCnt="2"', b'secCnt="3"')]:
            destination = self.altered_output("five-kinds", lambda parts: [(n, m, v.replace(a, b) if n == name else v) for n, m, v in parts])
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(destination)

    def test_preserved_text_head_quotes_delimiters_and_whitespace_reject_undeclared_changes(self):
        for label, a, b in [("empty-text", b"preserved' >", b"preserved'>"), ("five-kinds", b"selectedValue='b'", b'selectedValue="b"'), ("five-kinds", b"</hp:text>", b"</hp:text >")]:
            destination = self.altered_output(label, lambda parts: [(n, m, v.replace(a, b) if n == "Contents/section0.xml" else v) for n, m, v in parts])
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(destination)

    def test_extra_missing_reordered_or_recompressed_parts_cannot_pass_claims(self):
        transforms = [lambda p: [*p, ("undeclared.bin", 0, b"extra")], lambda p: p[:-1],
                      lambda p: [p[0], p[2], p[1], *p[3:]], lambda p: [(n, 0 if m == 8 else 8, v) if i == 1 else (n, m, v) for i, (n, m, v) in enumerate(p)]]
        for transform in transforms:
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(self.altered_output("five-kinds", transform))

    def test_duplicate_and_alias_zip_names_dtd_entities_and_invalid_managed_spans_reject(self):
        for transform in [lambda p: [*p, p[-1]], lambda p: [*p, ("contents/SECTION0.xml", 0, b"alias")]]:
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(self.altered_output("five-kinds", transform))
        for xml in [b'<!DOCTYPE a [<!ENTITY x "value">]><a>&x;</a>', b'<a xmlns:hp="'+oracle.HP.encode()+b'"><hp:edit><hp:text/><hp:text/></hp:edit></a>']:
            with self.assertRaises(ValueError):
                oracle.controls(xml)

    def test_native_identity_injection_and_partial_required_radio_outputs_reject(self):
        for a, b in [(b'name="component0"', b'id="90001" name="component0"'), (b'value="UNCHECKED" radioGroupName="cross-section-radio"', b'value="CHECKED" radioGroupName="cross-section-radio"')]:
            destination = self.altered_output("five-kinds", lambda p: [(n, m, v.replace(a, b) if n == "Contents/section0.xml" else v) for n, m, v in p])
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(destination)

    def test_receipt_boolean_counts_false_promotion_extra_fields_and_digest_drift_reject(self):
        for key, value in [("changed_controls", True), ("profile", "v1"), ("qualification", "native_pass"), ("output_package_sha256", "0"*64), ("unexpected", "value")]:
            destination = self.copied()
            manifest = json.loads((destination / "fixture-manifest.json").read_bytes())
            manifest["cases"][0]["receipt"][key] = value
            (destination / "fixture-manifest.json").write_bytes(json.dumps(manifest).encode())
            with self.assertRaises(ValueError):
                oracle.inspect_bundle(destination)

    def test_manifest_duplicate_coercion_traversal_missing_and_extra_files_reject(self):
        destination = self.copied()
        raw = (destination / "fixture-manifest.json").read_bytes()
        (destination / "fixture-manifest.json").write_bytes(raw.replace(b'"cases":', b'"profile":"extra","cases":', 1))
        with self.assertRaises(ValueError): oracle.inspect_bundle(destination)
        for field, value in [("bytes", True), ("path", "../outside.hwpx")]:
            destination = self.copied()
            manifest = json.loads((destination / "fixture-manifest.json").read_bytes())
            manifest["cases"][0]["source"][field] = value
            (destination / "fixture-manifest.json").write_bytes(json.dumps(manifest).encode())
            with self.assertRaises(ValueError): oracle.inspect_bundle(destination)
        destination = self.copied(); (destination / "extra.bin").write_bytes(b"extra")
        with self.assertRaises(ValueError): oracle.inspect_bundle(destination)
        destination = self.copied(); (destination / "actual-output.hwpx").unlink()
        with self.assertRaises(OSError): oracle.inspect_bundle(destination)

    def test_artifact_directory_and_nonempty_generation_boundaries_reject(self):
        with self.assertRaises(ValueError): oracle.directory_guard(Path("relative"))
        with self.assertRaises(ValueError): oracle.directory_guard(self.directory.parent)
        with self.assertRaises(ValueError): q.generate(self.directory)

    def test_coherently_rehashed_reset_source_and_output_cannot_break_actual_transition_linkage(self):
        destination = self.copied()
        manifest = json.loads((destination / "fixture-manifest.json").read_bytes())
        row = next(r for r in manifest["cases"] if r["case"] == "reset-defaults")
        for label in ("source", "output"):
            source = (destination / row[label]["path"]).read_bytes()
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w") as archive:
                for name, method, value in oracle.load_zip(source):
                    if name == "Contents/section0.xml": value = value.replace(b"opaque &amp; fixed", b"coherent-drift")
                    archive.writestr(name, value, compress_type=method)
            raw = output.getvalue()
            (destination / row[label]["path"]).write_bytes(raw)
            row[label]["bytes"], row[label]["sha256"] = len(raw), oracle.sha(raw)
            row["receipt"][label+"_package_sha256"] = oracle.sha(raw)
        (destination / "fixture-manifest.json").write_bytes(json.dumps(manifest).encode())
        with self.assertRaisesRegex(ValueError, "value_oracle_transition_linkage"):
            oracle.inspect_bundle(destination)

    def test_compiled_protocol_requires_all_exact_cases_without_skip_filter_duplicates(self):
        good = "\n".join(f"test {name} ... ok" for name in sorted(q.EXPECTED_TESTS)) + "\ntest result: ok. 25 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.tests_protocol(good)["passed"], 25)
        first, second = sorted(q.EXPECTED_TESTS)[:2]
        for bad in [good.replace(first, second), good.replace("... ok", "... ignored", 1), good.replace("0 filtered out", "1 filtered out"), good + f"test {first} ... ok\n"]:
            with self.assertRaises(ValueError): q.tests_protocol(bad)

    def test_independent_summary_exposes_hashes_not_raw_values_paths_or_native_claims(self):
        raw = json.dumps(self.actual["independent_oracle"], ensure_ascii=False)
        for secret in ("caller-default", "opaque-bytes", "新", "🚀", str(q.ROOT), str(self.directory)):
            self.assertNotIn(secret, raw)
        self.assertFalse(self.actual["independent_oracle"]["public_export_qualified"])


if __name__ == "__main__":
    unittest.main()
