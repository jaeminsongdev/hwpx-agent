from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from test_field_auto_number_target_oracle import ORACLE, package, section

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p09"))
SPEC = importlib.util.spec_from_file_location(
    "field_auto_number_target_qualification", ROOT / "tools/p09/qualify_field_auto_number_target.py"
)
assert SPEC is not None and SPEC.loader is not None
QUALIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUALIFIER)


class FieldAutoNumberTargetQualificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.fixture = self.root / "fixtures/target-build/fixture/output"
        self.attempt = self.root / "implementation/p09/evidence/private/attempt"
        self.fixture.mkdir(parents=True)
        self.attempt.mkdir(parents=True)
        for relative in QUALIFIER.SOURCE_FILES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"test-bound-source")
        source = section()
        input_bytes = package(source)
        saved_bytes = package(source.replace(b'num="2"', b'num="0"').replace(b'num="3"', b'num="0"').replace(b'num="4"', b'num="0"'))
        (self.fixture / "p09-17-field-auto-number-input.hwpx").write_bytes(input_bytes)
        for filename in ("saved.hwpx", "reopened.hwpx"):
            (self.attempt / filename).write_bytes(saved_bytes)
        for filename in ("saved.pdf", "reopened.pdf"):
            (self.attempt / filename).write_bytes(b"%PDF-test fixture")
        operations = []
        for index in range(5):
            field = QUALIFIER.EXPECTED_FIELDS[index] if index < 4 else {"feature_id": "REF-009", "case_id": "P09-17-C05"}
            operations.append({
                "feature_id": field["feature_id"], "case_id": field["case_id"],
                "capability_id": "ref.field_update" if index == 4 else (
                    "ref.field_page_number" if index == 0 else "ref.field_object_number"),
                "operation": "update_numeric_result" if index == 4 else "insert",
                "inserted_auto_numbers": 0 if index == 4 else 1,
                "updated_auto_numbers": 1 if index == 4 else 0,
                "plan_sha256": "a" * 64, "source_section_sha256": "a" * 64,
                "output_section_sha256": ORACLE.sha256(source) if index == 4 else "a" * 64,
                "source_state_sha256": "a" * 64, "target_state_sha256": "a" * 64,
                "target_document_flow_sha256": "a" * 64,
            })
        self.manifest = {
            "schema_version": "hwpx-agent.p09-17-field-auto-number-target-fixture/v1",
            "target_profile": QUALIFIER.TARGET,
            "input_file": "p09-17-field-auto-number-input.hwpx",
            "input_package_sha256": ORACLE.sha256(input_bytes),
            "input_package_bytes": len(input_bytes), "input_section_sha256": ORACLE.sha256(source),
            "field_projection": copy.deepcopy(QUALIFIER.EXPECTED_FIELDS), "operations": operations,
            "static_evidence": {"retry_package_byte_exact": True,
                                "stale_source_rejected_without_output": True, "complete_package_hwpx": True},
        }
        self.trace = {
            "schema_version": "hwpx-agent.p09-17-field-auto-number-target-trace/v1", "state": "pass",
            "target": {**QUALIFIER.TARGET, "prog_id": "HWPFrame.HwpObject.2"},
            "input_sha256": ORACLE.sha256(input_bytes), "input_bytes": len(input_bytes),
            "output_sha256": ORACLE.sha256(saved_bytes), "output_bytes": len(saved_bytes),
            "reopened_sha256": ORACLE.sha256(saved_bytes), "reopened_bytes": len(saved_bytes),
            "pdf_sha256": ORACLE.sha256(b"%PDF-test fixture"), "pdf_bytes": len(b"%PDF-test fixture"),
            "reopened_pdf_sha256": ORACLE.sha256(b"%PDF-test fixture"), "reopened_pdf_bytes": len(b"%PDF-test fixture"),
            "quit_invoked": True, "remaining_hwp_process_count": 0, "failed_phase": None, "error_code": None,
            "sessions": [{"label": label, "version": QUALIFIER.TARGET["build"], "register_module_return": False,
                          "process": {"process_id": index + 1, "executable_sha256": QUALIFIER.TARGET["executable_sha256"]}}
                         for index, label in enumerate(("save", "reopen"))],
            "security_module": {"name": "FilePathCheckerModuleExample",
                                "sha256": "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6",
                                "preflight_state": "pass"},
            **{key: "pass" for key in QUALIFIER.LIFECYCLE_KEYS},
            **{key: False for key in ("raw_document_text_present", "user_document_scanned", "external_network_invoked",
                                     "registry_or_system_setting_changed", "computer_use_click_or_type_invoked")},
        }

    def qualify(self):
        manifest_bytes = QUALIFIER.canonical_bytes(self.manifest)
        manifest_path = self.fixture / "fixture-manifest.json"
        manifest_path.write_bytes(manifest_bytes)
        trace_bytes = QUALIFIER.canonical_bytes(self.trace)
        (self.attempt / "target-trace.json").write_bytes(trace_bytes)
        return QUALIFIER.qualify(manifest_path, ORACLE.sha256(manifest_bytes), self.attempt,
                                 ORACLE.sha256(trace_bytes), root=self.root)

    def test_lifecycle_pass_cannot_hide_semantic_failures(self):
        result = self.qualify()
        self.assertEqual(result["state"], "failed_semantic_non_green")
        self.assertEqual([row["cached_result_preservation"] for row in result["cases"]],
                         ["pass", "fail", "fail", "fail", "pass"])
        self.assertTrue(result["claims"]["historical_exact_target_lifecycle"])
        self.assertFalse(result["claims"]["object_number_target_qualified"])
        self.assertFalse(result["claims"]["cached_result_preservation"])
        self.assertEqual(result["claims"]["green_rows"], 0)
        serialized = QUALIFIER.canonical_bytes(result).decode()
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("HWPFrame.HwpObject", serialized)

    def test_equal_cached_results_still_do_not_prove_recalculation_or_green(self):
        data = (self.fixture / "p09-17-field-auto-number-input.hwpx").read_bytes()
        for filename, digest_key, bytes_key in (
            ("saved.hwpx", "output_sha256", "output_bytes"),
            ("reopened.hwpx", "reopened_sha256", "reopened_bytes"),
        ):
            (self.attempt / filename).write_bytes(data)
            self.trace[digest_key] = ORACLE.sha256(data)
            self.trace[bytes_key] = len(data)
        result = self.qualify()
        self.assertEqual(result["state"], "partial_non_green")
        self.assertEqual(result["claims"]["reference_update"], "not_run")
        self.assertFalse(result["claims"]["p09_complete"])

    def test_changing_expectations_to_zero_is_rejected_even_with_new_manifest_hash(self):
        self.manifest["field_projection"][1]["number"] = 0
        with self.assertRaisesRegex(ValueError, "fixture_manifest_profile_mismatch"):
            self.qualify()

    def test_identity_and_privacy_drift_rejected(self):
        for key, value in (("input_sha256", "0" * 64), ("fresh_reopen", "not_run"),
                           ("remaining_hwp_process_count", False), ("computer_use_click_or_type_invoked", True)):
            previous = self.trace[key]
            self.trace[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.qualify()
            self.trace[key] = previous

    def test_same_process_cannot_prove_fresh_session(self):
        self.trace["sessions"][1]["process"]["process_id"] = 1
        with self.assertRaisesRegex(ValueError, "fresh_session_not_independent"):
            self.qualify()

    def test_tampered_output_and_pdf_rejected(self):
        original = (self.attempt / "saved.hwpx").read_bytes()
        (self.attempt / "saved.hwpx").write_bytes(original + b"tamper")
        with self.assertRaisesRegex(ValueError, "package_sha256_mismatch"):
            self.qualify()
        (self.attempt / "saved.hwpx").write_bytes(original)
        (self.attempt / "reopened.pdf").write_bytes(b"%PDF-tamper")
        with self.assertRaisesRegex(ValueError, "pdf_identity_mismatch"):
            self.qualify()

    def test_operation_chain_and_input_section_must_match(self):
        self.manifest["operations"][1]["source_section_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "fixture_operation_chain_mismatch"):
            self.qualify()

    def test_manifest_digest_and_duplicate_json_keys_rejected(self):
        path = self.fixture / "json-test.json"
        data = b'{"state":"fail","state":"pass"}'
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            QUALIFIER.checked_json(path, ORACLE.sha256(data))
        with self.assertRaisesRegex(ValueError, "evidence_digest_mismatch"):
            QUALIFIER.checked_json(path, "0" * 64)

    def test_outside_fixture_boundary_rejected(self):
        self.qualify()
        source = self.fixture / "fixture-manifest.json"
        outside = self.root / "outside.json"
        outside.write_bytes(source.read_bytes())
        with self.assertRaises(ValueError):
            QUALIFIER.qualify(outside, ORACLE.sha256(outside.read_bytes()), self.attempt,
                              ORACLE.sha256((self.attempt / "target-trace.json").read_bytes()), root=self.root)


if __name__ == "__main__":
    unittest.main()
