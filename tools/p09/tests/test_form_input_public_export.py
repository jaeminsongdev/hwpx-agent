from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import unittest
from tools.p09 import qualify_form_input_public_export as q


class PublicAtomicFormInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = q.qualify()

    def copied(self, paths):
        temporary = tempfile.TemporaryDirectory(prefix="hwpx-p09-38-public-negative-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for path in paths:
            destination = root / path; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((q.ROOT / path).read_bytes())
        return root

    def test_actual_public_api_and_real_library_compile_all_eighteen_cases(self):
        suites = self.actual["compiled_test_suites"]
        self.assertEqual([suites[key]["passed"] for key in ("domain", "actual_capture", "actual_library_unit")], [15, 1, 2])
        self.assertEqual(self.actual["production_library_check"]["state"], "pass")
        for record in self.actual["public_case_lineage"].values():
            self.assertTrue(record["original_test_body_byte_exact"])
            self.assertTrue(record["compiled_via_public_library_only"])

    def test_unique_export_inverse_recovers_entire_raw_original(self):
        raw = (q.ROOT / q.LIB).read_bytes()
        self.assertEqual(q.project(raw), (q.ROOT / q.ARCHIVE).read_bytes())
        for changed in (raw + b" ", raw + q.DELTA, raw.replace(q.DELTA, b"", 1), raw.replace(b"mod identity;", b"mod identity_changed;")):
            with self.assertRaises(ValueError): q.project(changed)

    def test_missing_or_changed_original_archive_rejects(self):
        root = self.copied((q.LIB,))
        with self.assertRaises((OSError, ValueError)): q.project((root / q.LIB).read_bytes(), root)
        root = self.copied((q.LIB, q.ARCHIVE))
        (root / q.ARCHIVE).write_bytes((root / q.ARCHIVE).read_bytes() + b" ")
        with self.assertRaises(ValueError): q.project((root / q.LIB).read_bytes(), root)

    def test_public_case_header_body_and_source_inclusion_mutants_reject(self):
        paths = [q.CAPSULE, *(path for row in q.PUBLIC_TESTS.values() for path in row[:2])]
        for row in q.PUBLIC_TESTS.values():
            root = self.copied(paths); destination = root / row[0]; raw = destination.read_bytes()
            for changed in (raw.replace(b"use domain_ir::form_input::*;", b"use fake::*;"),
                            raw + b'\n#[path="../src/form_input.rs"] mod fake;\n', raw + b"\n// altered case body\n"):
                destination.write_bytes(changed)
                with self.assertRaises(ValueError): q.lineage(root)
            destination.write_bytes(raw)
            self.assertEqual(len(q.lineage(root)), 2)

    def test_actual_capture_hashes_and_nonrepresentable_output_not_native_promotion(self):
        probe = self.actual["actual_capture_input_probe"]
        q.prior.verify_probe(probe, self.actual["independent_package_bindings"])
        self.assertEqual(probe["old_native_output"], "nonrepresentable")
        for key, value in (("native_output_qualified", True), ("native_session_started", True),
                           ("controls", True), ("source_state_sha256", "0"*64), ("old_native_output", "pass")):
            changed = copy.deepcopy(probe); changed[key] = value
            with self.assertRaises(ValueError): q.prior.verify_probe(changed, self.actual["independent_package_bindings"])

    def test_legacy_current_failures_actually_invoked_without_hash_refresh(self):
        failures = self.actual["actual_predecessor_current_failures"]
        self.assertEqual(set(failures), {"P09-37", "P09-34-r02"})
        for failure in failures.values():
            self.assertEqual(failure["state"], "fail"); self.assertTrue(failure["actually_invoked"])
            self.assertFalse(failure["archived_capsule_rewritten"])
        legacy = self.actual["actual_legacy_current_validators"]
        self.assertEqual(len(legacy), 35)
        domain = [result for result in legacy if Path(result["path"]).name in q.LEGACY_P09]
        self.assertEqual(len(domain), 10)
        for result in domain:
            self.assertEqual(result["errors"], [q.domain_error(Path(result["path"]).name)])
        for result in legacy:
            self.assertTrue(result["actually_invoked"]); self.assertFalse(result["source_locks_refreshed"])

    def test_frozen_json_plus_public_banner_protocol_without_ignored_results(self):
        raw = '{"state":"pass","errors":[]}'
        self.assertEqual(q.legacy_result(raw), ({"state": "pass", "errors": []}, 0))
        self.assertEqual(q.legacy_result(raw + '\nP08_OBJECT_PROTECT_HWPX_CONTRACT_PASS source_locks=5 actual_hangul=false'),
                         ({"state": "pass", "errors": []}, 1))
        for changed in (raw + '\n' + raw, raw + '\n{"state":"fail"}', raw + '\nunknown text',
                        raw + '\nP08_X_PASS\nP08_X_PASS', '{"state":"pass","state":"fail"}',
                        '{"state":"fail"}\nP08_X_PASS'):
            with self.assertRaises(ValueError): q.legacy_result(changed)

    def test_source_authority_complete_offline_preflight_and_privacy_boundaries(self):
        guard = q.authority()
        self.assertEqual((guard["older_capsules"], guard["older_source_checks"], guard["historical_trace_and_artifact_files"]), (12, 194, 22))
        self.assertTrue(self.actual["unchanged_complete_diagnostic_preflight_byte_exact"])
        self.assertFalse(guard["old_domain_library_is_current_full_verifier_pass"])
        raw = q.q.shared.lifecycle.canonical_bytes(self.actual)
        for forbidden in (b"C:\\", b"D:\\", "P09 실제 입력".encode(), b'"before"'):
            self.assertTrue(forbidden not in raw, "public_component_plaintext_or_private_path_present")
        self.assertEqual(self.actual["future_native_diagnostic_batch"], {"cases": 15, "stages": 30, "state": "not_run", "typed_only_inputs_added": 0})
        for key in ("native_input_output_qualified", "native_protection_qualified", "legacy_current_aggregate_pass",
                    "legacy_tests_migrated_or_skipped", "production_routing_qualified", "new_native_execution", "p09_complete"):
            self.assertFalse(self.actual["claims"][key])


if __name__ == "__main__":
    unittest.main()
