from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.p09 import qualify_field_object_caption_target as qualifier

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output"
MANIFEST = "42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48"


class ObjectCaptionTargetQualificationTests(unittest.TestCase):
    def setUp(self):
        if not (BUNDLE / "fixture-manifest.json").is_file():
            self.skipTest("P09-19 bounded fixture corpus unavailable")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.fixture = self.root / "fixtures/target-build/fixture/output"
        self.attempt = self.root / "implementation/p09/evidence/private/attempt"
        self.fixture.mkdir(parents=True)
        self.attempt.mkdir(parents=True)
        for path in qualifier.SOURCES:
            output = self.root / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"synthetic-test-source")
        self.manifest_path = self.fixture / "fixture-manifest.json"
        self.manifest_path.write_bytes((BUNDLE / "fixture-manifest.json").read_bytes())
        self.manifest = qualifier.oracle.load_manifest(self.manifest_path, MANIFEST)
        self.row = self.manifest["cases"][0]
        raw = (BUNDLE / self.row["file"]).read_bytes()
        (self.fixture / self.row["file"]).write_bytes(raw)
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(output, "w") as target:
            for entry in source.infolist():
                data = source.read(entry)
                if entry.filename == qualifier.oracle.SECTION:
                    data = data.replace(b'num="19"', b'num="1"', 1)
                target.writestr(entry, data)
        saved = output.getvalue()
        pdf = b"%PDF-synthetic-test-not-a-render"
        for name in ("saved.hwpx", "reopened.hwpx"):
            (self.attempt / name).write_bytes(saved)
        for name in ("saved.pdf", "reopened.pdf"):
            (self.attempt / name).write_bytes(pdf)
        self.trace = {
            "schema_version": "hwpx-agent.p09-17-field-auto-number-target-trace/v1",
            "state": "pass", "target": {**qualifier.lifecycle.TARGET, "prog_id": "HWPFrame.HwpObject.2"},
            "input_sha256": self.row["output_package_sha256"], "input_bytes": len(raw),
            "output_sha256": qualifier.oracle.sha256(saved), "output_bytes": len(saved),
            "reopened_sha256": qualifier.oracle.sha256(saved), "reopened_bytes": len(saved),
            "pdf_sha256": qualifier.oracle.sha256(pdf), "pdf_bytes": len(pdf),
            "reopened_pdf_sha256": qualifier.oracle.sha256(pdf), "reopened_pdf_bytes": len(pdf),
            "quit_invoked": True, "remaining_hwp_process_count": 0,
            "failed_phase": None, "error_code": None,
            "sessions": [{"label": label, "version": "11.0.0.9136", "register_module_return": False,
                          "process": {"process_id": index + 100,
                                      "executable_sha256": qualifier.lifecycle.TARGET["executable_sha256"]}}
                         for index, label in enumerate(("save", "reopen"))],
            "security_module": {"name": "FilePathCheckerModuleExample", "preflight_state": "pass",
                                "sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6"},
            **{key: "pass" for key in qualifier.lifecycle.LIFECYCLE_KEYS},
            **{key: False for key in qualifier.PRIVACY_KEYS},
        }

    def qualify(self, case_id="P09-19-C01"):
        raw = qualifier.lifecycle.canonical_bytes(self.trace)
        (self.attempt / "target-trace.json").write_bytes(raw)
        return qualifier.qualify(self.manifest_path, MANIFEST, case_id, self.attempt,
                                 qualifier.oracle.sha256(raw), root=self.root, access_attested=True)

    def failed_trace(self):
        self.trace.update(state="effect_unknown", failed_phase="first_open",
                          error_code="P09_FIELD_AUTO_NUMBER_TARGET_FIRST_OPEN_FAILED", quit_invoked=False)
        self.trace["sessions"] = self.trace["sessions"][:1]
        for key in qualifier.lifecycle.LIFECYCLE_KEYS:
            self.trace[key] = "not_run"
        for prefix in ("output", "pdf", "reopened", "reopened_pdf"):
            self.trace[prefix + "_sha256"] = None
            self.trace[prefix + "_bytes"] = None
        for name in ("saved.hwpx", "reopened.hwpx", "saved.pdf", "reopened.pdf"):
            (self.attempt / name).unlink()

    def test_bound_matching_snapshot_is_non_green_not_general_update_or_render(self):
        result = self.qualify()
        self.assertEqual(result["state"], "bounded_semantic_non_green")
        self.assertTrue(result["claims"]["bounded_object_caption_recalculation_19_to_1"])
        self.assertFalse(result["claims"]["general_numbering_algorithm_qualified"])
        self.assertFalse(result["claims"]["product_field_update_api_qualified"])
        self.assertEqual(result["claims"]["render"], "not_run")
        self.assertEqual(result["claims"]["green_rows"], 0)
        self.assertEqual(result["user_access"]["state"], "user_attested")
        serialized = qualifier.lifecycle.canonical_bytes(result).decode()
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("HWPFrame.HwpObject", serialized)

    def test_permission_attestation_does_not_promote_failed_open(self):
        self.failed_trace()
        result = self.qualify()
        self.assertEqual(result["state"], "failed_lifecycle_non_green")
        self.assertFalse(result["claims"]["actual_open_save_fresh_reopen"])
        self.assertFalse(result["claims"]["bounded_object_caption_recalculation_19_to_1"])
        self.assertEqual(result["snapshots"], {})

    def test_same_process_and_incomplete_reopen_are_rejected(self):
        self.trace["sessions"][1]["process"]["process_id"] = 100
        with self.assertRaisesRegex(ValueError, "fresh_session_not_independent"):
            self.qualify()
        self.trace["sessions"][1]["process"]["process_id"] = 101
        self.trace["fresh_reopen_save"] = "not_run"
        with self.assertRaises(ValueError):
            self.qualify()

    def test_wrong_case_input_and_private_effects_are_rejected(self):
        for key, replacement in (("input_sha256", "0" * 64),
                                 ("computer_use_click_or_type_invoked", True),
                                 ("remaining_hwp_process_count", False)):
            original = self.trace[key]
            self.trace[key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.qualify()
            self.trace[key] = original

    def test_tampered_output_pdf_and_trace_are_rejected(self):
        for name in ("saved.hwpx", "reopened.pdf"):
            path = self.attempt / name
            original = path.read_bytes()
            path.write_bytes(original + b"tamper")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.qualify()
            path.write_bytes(original)
        self.qualify()
        with self.assertRaisesRegex(ValueError, "evidence_digest_mismatch"):
            qualifier.lifecycle.checked_json(self.attempt / "target-trace.json", "0" * 64)

    def test_failed_open_cannot_hide_outputs_or_success_claims(self):
        self.failed_trace()
        (self.attempt / "saved.hwpx").write_bytes(b"untraced-output")
        with self.assertRaisesRegex(ValueError, "failed_open_untraced_output_rejected"):
            self.qualify()
        (self.attempt / "saved.hwpx").unlink()
        self.trace["first_save"] = "pass"
        with self.assertRaises(ValueError):
            self.qualify()

    def test_manifest_expectation_weakening_and_duplicate_trace_rejected(self):
        weakened = copy.deepcopy(self.manifest)
        weakened["cases"][0]["expected_saved_number"] = 19
        raw = json.dumps(weakened).encode()
        self.manifest_path.write_bytes(raw)
        with self.assertRaises(ValueError):
            qualifier.oracle.load_manifest(self.manifest_path, qualifier.oracle.sha256(raw))
        raw = b'{"state":"pass","state":"effect_unknown"}'
        path = self.attempt / "target-trace.json"
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            qualifier.lifecycle.checked_json(path, qualifier.oracle.sha256(raw))

    def test_boundary_escape_is_rejected(self):
        outside = self.root / "outside.json"
        outside.write_bytes(self.manifest_path.read_bytes())
        with self.assertRaises(ValueError):
            qualifier.qualify(outside, MANIFEST, "P09-19-C01", self.attempt,
                              "0" * 64, root=self.root)


if __name__ == "__main__":
    unittest.main()
