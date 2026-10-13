from __future__ import annotations
import copy
import unittest
from tools.p09 import qualify_form_input_component as q


class AtomicFormInputComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = q.qualify()

    def test_actual_body_compiles_all_twenty_exact_named_cases_without_native_promotion(self):
        self.assertEqual(self.actual["compiled_test_suites"]["domain"]["passed"], 17)
        self.assertEqual(self.actual["compiled_test_suites"]["actual_capture"]["passed"], 3)
        self.assertFalse(self.actual["claims"]["public_export_qualified"])
        self.assertFalse(self.actual["claims"]["new_native_execution"])
        self.assertFalse(self.actual["claims"]["native_input_output_qualified"])
        self.assertFalse(self.actual["claims"]["p09_complete"])
        self.assertEqual(self.actual["claims"]["green_rows"], 0)

    def test_actual_native_capture_is_only_typed_input_and_old_output_stays_rejected(self):
        q.verify_probe(self.actual["actual_capture_input_probe"], self.actual["independent_package_bindings"])
        self.assertEqual(self.actual["actual_capture_input_probe"]["old_native_output"], "nonrepresentable")
        self.assertEqual(self.actual["future_native_diagnostic_batch"], {"cases": 15, "stages": 30, "state": "not_run", "typed_only_inputs_added": 0})
        self.assertEqual(self.actual["unchanged_legacy_validator"]["state"], "pass")

    def test_forged_probe_hashes_coercions_native_and_privacy_promotions_reject(self):
        for key, value in (("source_state_sha256", "0"*64), ("target_state_sha256", "0"*64), ("plan_sha256", "0"*64),
                           ("controls", True), ("every_other_complete_state_field_exact", 1), ("native_output_qualified", True),
                           ("native_session_started", True), ("old_native_output", "pass"), ("raw_document_text_present", True), ("green_rows", False)):
            changed = copy.deepcopy(self.actual["actual_capture_input_probe"]); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                q.verify_probe(changed, self.actual["independent_package_bindings"])
        changed = copy.deepcopy(self.actual["actual_capture_input_probe"]); changed["ignored_claim"] = True
        with self.assertRaises(ValueError): q.verify_probe(changed, self.actual["independent_package_bindings"])

    def test_independent_package_and_flow_substitution_reject(self):
        for key in ("package_sha256", "document_flow_sha256"):
            changed = copy.deepcopy(self.actual["independent_package_bindings"]); changed[key] = "0"*64
            with self.assertRaises(ValueError): q.verify_probe(self.actual["actual_capture_input_probe"], changed)

    def test_test_name_missing_duplicate_extra_failed_ignored_and_filtered_reject(self):
        names = sorted(q.DOMAIN_TESTS)
        lines = [f"test {name} ... ok" for name in names]
        summary = "test result: ok. 17 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.1s"
        base = "\n".join([*lines, summary]); self.assertEqual(q.verify_tests(base, q.DOMAIN_TESTS)["passed"], 17)
        for mutated in (lines[:-1], lines+[lines[0]], [*lines[:-1], "test extra_case ... ok"],
                        [lines[0].replace("ok", "FAILED"), *lines[1:]], [lines[0].replace("ok", "ignored"), *lines[1:]]):
            with self.assertRaises(ValueError): q.verify_tests("\n".join([*mutated,summary]), q.DOMAIN_TESTS)
        for summary_mutant in (summary.replace("0 filtered", "1 filtered"), summary+"\n"+summary):
            with self.assertRaises(ValueError): q.verify_tests("\n".join([*lines,summary_mutant]), q.DOMAIN_TESTS)

    def test_source_authority_and_redacted_public_component_capsule(self):
        q.authority()
        self.assertEqual(len(self.actual["source_sha256"]), 6)
        self.assertEqual(len(self.actual["unchanged_domain_source_sha256"]), 3)
        raw = q.q.shared.lifecycle.canonical_bytes(self.actual)
        # The public test name contains the English word "before". A quoted
        # fixture value is forbidden; test-name metadata is not document text.
        for forbidden in (b"C:\\", b"D:\\", "P09 실제 입력".encode(), b'"before"', "기본값".encode()):
            self.assertTrue(forbidden not in raw, "public_component_plaintext_or_private_path_present")
        self.assertFalse(self.actual["privacy"]["trust_or_registry_changed"])


if __name__ == "__main__":
    unittest.main()
