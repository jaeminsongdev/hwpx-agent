from __future__ import annotations

import copy
import unittest

from tools.p09 import qualify_native_form_complete_batch as q


class CompleteNativeFormBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traces = q.verified_traces()
        cls.actual = q.rust_observations()

    def test_initial_preparation_capsule_and_exact_observer_only_delta_are_preserved(self):
        bridge = q.source_bridge()
        self.assertEqual(bridge["initial_preparation_sha256"], q.PREPARATION_SHA)
        self.assertTrue(bridge["exact_archive_and_single_missing_output_delta"])

    def test_all_six_real_traces_have_ten_independent_owned_sessions_and_two_failures(self):
        self.assertEqual([n[3] for n in self.traces], [True, True, True, True, False, False])
        self.assertEqual(sum(len(n[2]["sessions"]) for n in self.traces), 10)
        for _, _, trace, passed in self.traces:
            self.assertEqual(trace["remaining_hwp_process_count"], 0)
            if not passed:
                self.assertEqual(trace["failed_phase"], "first_open")
                self.assertIsNone(trace["output_sha256"])

    def test_actual_complete_public_readback_has_real_control_matches_but_no_whole_state_pass(self):
        q.verify_rust(self.actual, self.traces)
        for result in self.actual["cases"][:4]:
            for stage in ("saved", "reopened"):
                self.assertEqual(result[stage]["complete_public_reader"], "pass")
                self.assertFalse(result[stage]["complete_target_state_exact"])
                self.assertFalse(result[stage]["complete_package_bindings_exact"])
                self.assertTrue(result[stage]["document_flow_exact"])
        self.assertEqual([n["saved"]["target_control_fingerprints_exact"] for n in self.actual["cases"][:4]], [True, False, False, True])

    def test_wrong_native_hash_and_boolean_coercion_in_public_readback_are_rejected(self):
        for key, value in (("package_sha256", "0" * 64), ("package_bytes", True), ("complete_target_state_exact", 0)):
            changed = copy.deepcopy(self.actual)
            changed["cases"][0]["saved"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                q.verify_rust(changed, self.traces)

    def test_failed_native_outputs_cannot_be_promoted_to_pass(self):
        changed = copy.deepcopy(self.actual)
        changed["cases"][4]["saved"] = copy.deepcopy(changed["cases"][0]["saved"])
        with self.assertRaisesRegex(ValueError, "native_form_missing_output_promoted"):
            q.verify_rust(changed, self.traces)

    def test_case_substitution_extra_fields_and_short_inventory_are_rejected(self):
        changed = copy.deepcopy(self.actual)
        changed["cases"].reverse()
        with self.assertRaises(ValueError):
            q.verify_rust(changed, self.traces)
        changed = copy.deepcopy(self.actual)
        changed["cases"][0]["saved"]["ignored_claim"] = True
        with self.assertRaises(ValueError):
            q.verify_rust(changed, self.traces)
        changed = copy.deepcopy(self.actual)
        changed["cases"].pop()
        with self.assertRaises(ValueError):
            q.verify_rust(changed, self.traces)


if __name__ == "__main__":
    unittest.main()
