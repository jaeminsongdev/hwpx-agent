from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.p09 import qualify_native_form_observation_component as q
from tools.p09 import verify_p08_additive_export_source_bridge_v3 as current


class NativeFormObservationTests(unittest.TestCase):
    def test_real_compiled_successor_tests_execute_without_native_session(self):
        value = q.run_tests()
        self.assertEqual(value["passed"], 18)
        self.assertEqual(value["ignored"], 0)
        self.assertEqual(set(value["test_names"]), q.EXPECTED_TESTS)

    def test_fake_missing_extra_failed_or_ignored_test_results_rejected(self):
        original = "\n".join("test " + name + " ... ok" for name in sorted(q.EXPECTED_TESTS)) + "\ntest result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.04s\n"
        q.verify_test_output(original)
        for changed in (original.replace("18 passed", "17 passed"), original.replace(" ... ok", " ... ignored", 1),
                        original.replace(" ... ok", " ... FAILED", 1), original + "test invented ... ok\n",
                        original.replace(next(iter(sorted(q.EXPECTED_TESTS))), "invented", 1)):
            with self.subTest(length=len(changed)), self.assertRaisesRegex(ValueError, "native_form_observation_test_inventory_or_result_invalid"):
                q.verify_test_output(changed)

    def test_actual_capsule_preserves_missing_id_and_excludes_false_product_claims(self):
        with self.assertRaisesRegex(ValueError, "native_form_observation_pending_export_boundary_changed"):
            q.qualify()
        value = current.record("P09-27")
        current.historical_sources("P09-27")
        self.assertEqual(value["state"], "observed_native_identity_component_non_green")
        self.assertFalse(value["capture"]["native_id_present"])
        self.assertFalse(value["capture"]["native_instance_id_present"])
        self.assertTrue(value["claims"]["observed_missing_id_reader_and_property_lowering_implemented"])
        for key in ("shared_library_export_connected", "new_native_target_execution", "complete_target_packages_prepared",
                    "package_part_bindings_independently_read", "production_routing_qualified", "p09_complete", "product_complete"):
            self.assertFalse(value["claims"][key])
        raw = q.shared.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn("P08 FORM INSERT", raw)
        self.assertNotIn(str(q.ROOT), raw)

    def test_original_capture_and_source_authorities_are_unchanged(self):
        with self.assertRaisesRegex(ValueError, "native_form_observation_pending_export_boundary_changed"):
            q.checked_sources()
        previous = q.shared.lifecycle.checked_json(q.ROOT / q.COMPATIBILITY, q.COMPATIBILITY_SHA)
        current.historical_sources("P09-27")
        lib_sha = current.ARCHIVES[current.LIB][1]
        self.assertEqual(q.prior.capture(), previous["capture"])
        self.assertEqual(lib_sha, "1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09")
        self.assertEqual(q.shared.oracle.sha256((q.ROOT / q.prior.CAPTURE).read_bytes()), q.prior.CAPTURE_SHA)

    def test_missing_corpus_is_an_error_not_skipped_or_synthetic(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises((OSError, ValueError)):
                q.prior.capture(Path(directory))

    def test_prior_source_change_not_hidden_by_successor_claims(self):
        previous = q.shared.lifecycle.checked_json(q.ROOT / q.COMPATIBILITY, q.COMPATIBILITY_SHA)
        first = next(iter(previous["source_sha256"]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (q.COMPATIBILITY, q.BRIDGE, first):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((q.ROOT / name).read_bytes())
            target = root / first
            target.write_bytes(target.read_bytes() + b"\n# source drift\n")
            with self.assertRaisesRegex(ValueError, "native_form_observation_predecessor_drift"):
                q.checked_sources(root)


if __name__ == "__main__":
    unittest.main()
