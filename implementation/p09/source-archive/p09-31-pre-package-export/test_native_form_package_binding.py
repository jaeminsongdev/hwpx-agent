from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import unittest
from tools.p09 import qualify_native_form_package_binding as q


class NativeFormPackageBindingTests(unittest.TestCase):
    def test_actual_package_fingerprints_are_independent_of_rust_or_caller_hashes(self):
        value = q.independent_actual()
        self.assertEqual(value["package_sha256"], q.prior.CAPTURE_SHA)
        self.assertEqual(value["section_count"], 1)
        self.assertEqual(value["verified_overlay_issues"], 2)
        self.assertEqual(value["legacy_index_state"], "id_index_validation_failed")
        self.assertFalse(value["bindings"]["protection_signal_observed"])

    def test_omitted_forged_failed_or_ignored_test_results_not_admitted(self):
        original = "\n".join("test " + name + " ... ok" for name in sorted(q.EXPECTED_TESTS)) + "\ntest result: ok. 17 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.04s\n"
        q.test_output(original)
        for changed in (original.replace("17 passed", "16 passed"), original.replace(" ... ok", " ... ignored", 1),
                        original.replace(" ... ok", " ... FAILED", 1), original + "test forged ... ok\n"):
            with self.subTest(length=len(changed)), self.assertRaisesRegex(ValueError, "native_form_package_test_inventory_invalid"):
                q.test_output(changed)

    def test_altered_metadata_flow_types_or_false_legacy_pass_reject_probe(self):
        original = q.independent_actual()
        for key, value in (("package_sha256", "0"*64), ("document_flow_sha256", "a1"*32),
                           ("section_count", True), ("legacy_index_state", "pass"), ("verified_overlay_issues", 0), ("unknown", False)):
            changed = copy.deepcopy(original); changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "native_form_package_independent_probe_mismatch"):
                q.verify_probe(changed, original)
        changed = copy.deepcopy(original); changed["bindings"]["style_catalog_sha256"] = "0"*64
        with self.assertRaises(ValueError): q.verify_probe(changed, original)

    def test_real_compiled_component_and_independent_probe_keep_non_gate_scope(self):
        value = q.qualify()
        self.assertEqual(value["actual_rust_tests"]["passed"], 17)
        self.assertTrue(value["claims"]["complete_package_bindings_independently_read"])
        for key in ("package_component_exports_connected", "package_lowering_implemented", "complete_target_cases_prepared",
                    "new_native_target_execution", "general_document_protection_qualified", "nonzero_form_border_type_qualified",
                    "production_routing_qualified", "p09_complete", "product_complete"):
            self.assertFalse(value["claims"][key])
        raw = q.SHARED.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn("P08FORMINSERT", raw); self.assertNotIn(str(q.ROOT), raw)

    def test_missing_capture_and_authority_not_replaced_with_synthetic_or_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises((OSError, ValueError)): q.independent_actual(root)
            with self.assertRaises((OSError, ValueError)): q.sources(root)

    def test_current_export_source_pins_and_original_capture_unchanged(self):
        value = q.sources()
        self.assertEqual(value["shared_lib"]["current_raw_sha256"], q.export.CURRENT_LIB)
        self.assertEqual(q.export.sha256((q.ROOT / q.prior.CAPTURE).read_bytes()), q.prior.CAPTURE_SHA)


if __name__ == "__main__": unittest.main()
