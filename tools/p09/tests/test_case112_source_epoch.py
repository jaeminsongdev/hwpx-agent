"""Synthetic admission decisions only; no Cargo/Native/product execution."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_case112_source_epoch as epoch


class EpochDecisionTests(unittest.TestCase):
    def setUp(self):
        self.old = dict(path=epoch.LIBRARY, bytes=26524, sha256="a" * 64)
        self.current = dict(self.old, bytes=26562, sha256="b" * 64)
        self.binary = dict(path="target/frozen/test.exe", bytes=14216704, sha256="c" * 64)
        self.module = dict(path=epoch.MODULE, bytes=2000, sha256="d" * 64)
        self.paths = {epoch.LIBRARY, self.binary["path"]}

    def decision(self, **changes):
        args = dict(frozen_library=self.old, current_library=self.current,
            frozen_binary=self.binary, current_binary=copy.deepcopy(self.binary),
            module_pin=self.module, frozen_paths=self.paths,
            registration_present=True, registration_only_delta=True)
        args.update(changes)
        return epoch.epoch_decision(**args)

    def test_registered_new_module_requires_build_epoch_not_current_runtime_pass(self):
        result = self.decision()
        self.assertEqual(result["decision"], "REGISTERED_MODULE_ADDED_REQUIRES_CURRENT_BUILD_EPOCH")
        for key in ("current_module_compile_binding_qualified", "full_current_Rust_inventory_qualified",
                    "actual112_admitted_by_this_audit", "input_pin_rebased_or_source_overwritten"):
            self.assertFalse(result[key])

    def test_matching_library_does_not_promote_whole_build_or_product(self):
        result = self.decision(current_library=copy.deepcopy(self.old))
        self.assertTrue(result["library_matches_frozen_runtime_source"])
        self.assertFalse(result["actual112_admitted_by_this_audit"])

    def test_unknown_library_delta_requires_review(self):
        result = self.decision(registration_only_delta=False)
        self.assertEqual(result["decision"], "ADDITIONAL_LIBRARY_DRIFT_REQUIRES_EXPLICIT_SOURCE_EPOCH_REVIEW")

    def test_module_already_in_manifest_is_not_claimed_as_a_new_module(self):
        result = self.decision(frozen_paths=self.paths | {epoch.MODULE})
        self.assertFalse(result["new_module_absent_from_frozen_source"])
        self.assertFalse(result["current_module_compile_binding_qualified"])

    def test_binary_drift_or_missing_frozen_binary_is_rejected(self):
        for changes in (dict(current_binary=dict(self.binary, sha256="f" * 64)),
                        dict(frozen_paths={epoch.LIBRARY})):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.decision(**changes)

    def test_module_bounds_and_path_are_not_coerced(self):
        for changes in (dict(path="unrelated.rs"), dict(bytes=0), dict(bytes=True), dict(bytes=1048577)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.decision(module_pin=dict(self.module, **changes))

    def test_boolean_evidence_is_not_coerced(self):
        for key in ("registration_present", "registration_only_delta"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.decision(**{key: 1})

    def test_inputs_are_not_mutated(self):
        before = copy.deepcopy((self.old, self.current, self.binary, self.module, self.paths))
        self.decision()
        self.assertEqual(before, (self.old, self.current, self.binary, self.module, self.paths))


if __name__ == "__main__":
    unittest.main()
