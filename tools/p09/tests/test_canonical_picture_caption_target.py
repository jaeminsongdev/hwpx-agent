from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.p09 import qualify_canonical_picture_caption_target as successor

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "fixtures/target-build/p09-20-canonical-picture-number-target-20261002-01/output"
MANIFEST = "6dbc3dfe553753e08292338229ce3c5a4470f5bd33f99678c05da960d07000e9"


class CanonicalPictureCaptionTargetTests(unittest.TestCase):
    def setUp(self):
        if not (BUNDLE / "fixture-manifest.json").is_file():
            self.skipTest("P09-20 bounded fixture corpus unavailable")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.fixture = self.root / "fixtures/target-build/successor/output"
        self.fixture.mkdir(parents=True)
        for relative in (successor.CANONICAL, successor.CAPTION):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.path = self.fixture / "fixture-manifest.json"
        self.path.write_bytes((BUNDLE / "fixture-manifest.json").read_bytes())
        self.value = json.loads(self.path.read_bytes())
        self.package = self.fixture / successor.oracle.FILES[successor.CASE]
        self.package.write_bytes((BUNDLE / self.package.name).read_bytes())

    def test_real_payload_and_all_binary_resources_restore_byte_exact(self):
        _, result = successor.prepare(self.path, MANIFEST, root=self.root)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["caption_number"], 19)
        self.assertFalse(result["actual_hangul"])
        self.assertEqual(result["green_rows"], 0)

    def test_two_fixture_generations_are_identical(self):
        retry = ROOT / "fixtures/target-build/p09-20-canonical-picture-number-target-20261002-02/output"
        for name in ("fixture-manifest.json", self.package.name):
            self.assertEqual((BUNDLE / name).read_bytes(), (retry / name).read_bytes())

    def test_prior_failed_seed_and_weakened_expectation_are_rejected(self):
        for key, changed in (("source_package_sha256", "e7a202dd4ff75e0cda74681e99d8aec4c490a68189f8c0d658a2b2ea764d857c"),
                             ("expected_saved_number", 19), ("native_object_id", 8103),
                             ("retry_checks", {"stale_source_rejected": 1, "deterministic_retry": True})):
            value = copy.deepcopy(self.value)
            value["cases"][0][key] = changed
            raw = json.dumps(value).encode()
            self.path.write_bytes(raw)
            with self.subTest(key=key), self.assertRaises(ValueError):
                successor.prepare(self.path, successor.oracle.sha256(raw), root=self.root)

    def test_manifest_cannot_promote_target_or_render(self):
        for key, changed in (("actual_hangul", True), ("render", "pass"), ("green_rows", 1)):
            value = copy.deepcopy(self.value)
            value[key] = changed
            raw = json.dumps(value).encode()
            self.path.write_bytes(raw)
            with self.subTest(key=key), self.assertRaises(ValueError):
                successor.prepare(self.path, successor.oracle.sha256(raw), root=self.root)

    def test_native_seed_and_generated_package_digest_drift_rejected(self):
        path = self.root / successor.CANONICAL
        original = path.read_bytes()
        path.write_bytes(original + b"tamper")
        with self.assertRaisesRegex(ValueError, "package_sha256_mismatch"):
            successor.prepare(self.path, MANIFEST, root=self.root)
        path.write_bytes(original)
        self.package.write_bytes(self.package.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "package_sha256_mismatch"):
            successor.prepare(self.path, MANIFEST, root=self.root)

    def test_same_digest_adversarial_native_content_change_does_not_hide_reversal_failure(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(self.package) as source, zipfile.ZipFile(buffer, "w") as output:
            for entry in source.infolist():
                data = source.read(entry)
                if entry.filename == successor.oracle.SECTION:
                    data = data.replace(b'numberingType="PICTURE"', b'numberingType="TABLE"', 1)
                output.writestr(entry, data)
        raw = buffer.getvalue()
        self.package.write_bytes(raw)
        self.value["cases"][0]["output_package_sha256"] = successor.oracle.sha256(raw)
        self.value["cases"][0]["output_package_bytes"] = len(raw)
        raw = json.dumps(self.value).encode()
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "canonical_native_payload_preservation_failed"):
            successor.prepare(self.path, successor.oracle.sha256(raw), root=self.root)

    def test_output_and_manifest_boundary_escape_rejected(self):
        outside = self.root / "outside.json"
        outside.write_bytes(self.path.read_bytes())
        with self.assertRaises(ValueError):
            successor.prepare(outside, MANIFEST, root=self.root)

    def make_synthetic_trace(self):
        # This is a negative-test corpus, never published as actual target evidence.
        self.attempt = self.root / "implementation/p09/evidence/private/synthetic-attempt"
        self.attempt.mkdir(parents=True)
        for relative in successor.SOURCES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic-source")
        output = io.BytesIO()
        with zipfile.ZipFile(self.package) as source, zipfile.ZipFile(output, "w") as target:
            for entry in source.infolist():
                raw = source.read(entry)
                if entry.filename == successor.oracle.SECTION:
                    raw = raw.replace(b'num="19"', b'num="1"', 1)
                target.writestr(entry, raw)
        saved = output.getvalue()
        pdf = b"%PDF-synthetic-never-render-qualified"
        for name in ("saved.hwpx", "reopened.hwpx"):
            (self.attempt / name).write_bytes(saved)
        for name in ("saved.pdf", "reopened.pdf"):
            (self.attempt / name).write_bytes(pdf)
        self.trace = {
            "schema_version": "hwpx-agent.p09-17-field-auto-number-target-trace/v1",
            "state": "pass", "target": {**successor.lifecycle.TARGET, "prog_id": "HWPFrame.HwpObject.2"},
            "input_sha256": self.value["cases"][0]["output_package_sha256"],
            "input_bytes": self.value["cases"][0]["output_package_bytes"],
            "output_sha256": successor.oracle.sha256(saved), "output_bytes": len(saved),
            "reopened_sha256": successor.oracle.sha256(saved), "reopened_bytes": len(saved),
            "pdf_sha256": successor.oracle.sha256(pdf), "pdf_bytes": len(pdf),
            "reopened_pdf_sha256": successor.oracle.sha256(pdf), "reopened_pdf_bytes": len(pdf),
            "quit_invoked": True, "remaining_hwp_process_count": 0, "failed_phase": None, "error_code": None,
            "security_module": {"name": "FilePathCheckerModuleExample", "preflight_state": "pass",
                                "sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6"},
            "sessions": [{"label": label, "version": "11.0.0.9136", "register_module_return": False,
                          "process": {"process_id": index + 100,
                                      "executable_sha256": successor.lifecycle.TARGET["executable_sha256"]}}
                         for index, label in enumerate(("save", "reopen"))],
            **{key: "pass" for key in successor.lifecycle.LIFECYCLE_KEYS},
            **{key: False for key in successor.shared.PRIVACY_KEYS},
        }

    def qualify_trace(self):
        raw = successor.lifecycle.canonical_bytes(self.trace)
        (self.attempt / "target-trace.json").write_bytes(raw)
        return successor.qualify(self.path, MANIFEST, self.attempt, successor.oracle.sha256(raw),
                                 root=self.root, access_attested=True)

    def test_synthetic_matching_lifecycle_never_qualifies_general_update_render_or_gate(self):
        self.make_synthetic_trace()
        result = self.qualify_trace()
        self.assertEqual(result["state"], "bounded_semantic_non_green")
        self.assertTrue(result["claims"]["bounded_picture_caption_recalculation_19_to_1"])
        self.assertFalse(result["claims"]["product_field_update_api_qualified"])
        self.assertEqual(result["claims"]["render"], "not_run")
        self.assertEqual(result["claims"]["green_rows"], 0)
        self.assertFalse(result["claims"]["p09_complete"])
        self.assertNotIn(str(self.root), successor.lifecycle.canonical_bytes(result).decode())

    def test_stale_trace_size_privacy_and_same_process_rejected(self):
        self.make_synthetic_trace()
        for key, value in (("input_sha256", "0" * 64), ("reopened_bytes", False),
                           ("computer_use_click_or_type_invoked", True), ("fresh_reopen", "not_run")):
            previous = self.trace[key]
            self.trace[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.qualify_trace()
            self.trace[key] = previous
        self.trace["sessions"][1]["process"]["process_id"] = 100
        with self.assertRaisesRegex(ValueError, "fresh_session_not_independent"):
            self.qualify_trace()

    def test_saved_package_and_pdf_tampering_rejected(self):
        self.make_synthetic_trace()
        for name in ("saved.hwpx", "reopened.pdf"):
            path = self.attempt / name
            original = path.read_bytes()
            path.write_bytes(original + b"tamper")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.qualify_trace()
            path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
