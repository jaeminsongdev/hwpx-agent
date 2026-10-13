from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.p09 import verify_p08_additive_export_source_bridge as bridge


class P08AdditiveExportSourceBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = bridge.bounded_bytes(bridge.ROOT / bridge.LIB, 2 * 1024 * 1024)

    def test_exact_raw_predecessor_projection_without_changing_live_file(self):
        projected = bridge.project(self.source)
        self.assertEqual(bridge.sha256(projected), bridge.PREDECESSOR_LIB)
        self.assertEqual(bridge.sha256(self.source), bridge.CURRENT_LIB)
        self.assertEqual((bridge.ROOT / bridge.LIB).read_bytes(), self.source)
        for delta in bridge.DELTAS:
            self.assertNotIn(delta, projected)

    def test_old_file_does_not_masquerade_as_current_lib(self):
        projected = bridge.project(self.source)
        with self.assertRaisesRegex(ValueError, "current_shared_lib_identity_changed"):
            bridge.project(projected)

    def test_existing_p08_content_drift_is_rejected_by_both_full_and_projection_locks(self):
        changed = self.source.replace(b"mod asset;", b"mod asset_drift;", 1)
        with self.assertRaisesRegex(ValueError, "current_shared_lib_identity_changed"):
            bridge.project(changed)
        with self.assertRaisesRegex(ValueError, "predecessor_projection_changed"):
            bridge.project(changed, require_current=False)

    def test_missing_duplicate_or_modified_span_cannot_be_ignored(self):
        for delta in bridge.DELTAS:
            for changed in (self.source.replace(delta, b"", 1), self.source + delta,
                            self.source.replace(delta, delta.replace(b"field_", b"changed_"), 1)):
                with self.subTest(delta=bridge.sha256(delta)), self.assertRaises(ValueError):
                    bridge.project(changed, require_current=False)

    def test_unknown_additional_exports_or_whitespace_fail_exact_projection(self):
        for extra in (b"\npub use unrelated::*;\n", b" ", b"\r\n"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                bridge.project(self.source + extra, require_current=False)

    def test_predecessor_and_added_module_drift_rejected_even_if_lib_unchanged(self):
        for mapping in (bridge.PREDECESSORS, bridge.ADDITIONS, bridge.REQUIRED_VALIDATORS):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for relative in mapping:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((bridge.ROOT / relative).read_bytes())
                self.assertEqual(bridge.check_locked(root, mapping), mapping)
                relative = next(iter(mapping))
                path = root / relative
                path.write_bytes(path.read_bytes() + b"tamper")
                with self.assertRaisesRegex(ValueError, "bridge_source_identity_changed"):
                    bridge.check_locked(root, mapping)

    def test_current_bridge_keeps_legacy_failure_and_all_gate_boundaries(self):
        result = bridge.verify()
        self.assertEqual(result["state"], "source_qualified_non_gate")
        self.assertEqual(result["legacy_asset_validator"]["errors"], ["implementation_digest"])
        self.assertEqual(result["legacy_asset_validator"]["state"], "fail")
        self.assertTrue(result["claims"]["dependency_source_qualification"])
        self.assertFalse(result["claims"]["legacy_live_aggregate_now_pass"])
        self.assertFalse(result["claims"]["current_target_promotion"])
        self.assertFalse(result["claims"]["new_target_execution"])
        self.assertFalse(result["claims"]["p09_complete"])
        self.assertEqual(len(result["required_current_validators"]), 25)
        failures = [c for c in result["required_current_validators"] if c["state"] == "fail"]
        self.assertEqual({c["path"] for c in failures}, bridge.EXPORT_DRIFT_VALIDATORS)
        for check in failures:
            self.assertEqual(check["exit_code"], 1)
            self.assertEqual(check["actual_legacy_result"]["errors"], ["implementation_digest"])
            self.assertTrue(check["unchanged_implementation_sha256"])
            self.assertEqual(check["source_admission"], "exact_export_drift_source_qualified_legacy_fail")
        self.assertEqual(len(result["unchanged_asset_implementation_sha256"]), 5)
        self.assertFalse(result["privacy"]["registry_or_trust_setting_changed"])
        self.assertNotIn(str(bridge.ROOT), bridge.canonical_bytes(result).decode())

    def test_any_non_export_error_or_missing_proof_rejects_admission(self):
        relative = next(iter(bridge.EXPORT_DRIFT_VALIDATORS))
        unchanged = {"component": "0" * 64}
        valid = {"state": "fail", "errors": ["implementation_digest"],
                 "source_qualification_verified": True, "implementation_files": 2}
        self.assertEqual(bridge.admit_result(relative, 1, valid, unchanged),
                         "exact_export_drift_source_qualified_legacy_fail")
        for patch in ({"errors": ["implementation_digest", "official_source_root"]},
                      {"source_qualification_verified": False}, {"implementation_files": 3},
                      {"official_source_locks_verified": False}, {"state": "pass"},
                      {"errors": []}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                bridge.admit_result(relative, 1, valid | patch, unchanged)
        for exit_code, locks in ((0, unchanged), (2, unchanged), (1, {})):
            with self.subTest(exit_code=exit_code, locks=locks), self.assertRaises(ValueError):
                bridge.admit_result(relative, exit_code, valid, locks)
        with self.assertRaises(ValueError):
            bridge.admit_result("unlisted_validator.py", 1, valid, unchanged)

    def test_non_export_validator_requires_genuine_pass(self):
        relative = "tools/p08/validate_drawing_canvas_contract.py"
        self.assertEqual(bridge.admit_result(relative, 0, {"state": "pass"}, {}), "pass")
        with self.assertRaises(ValueError):
            bridge.admit_result(relative, 1, {"state": "fail", "errors": ["implementation_digest"]}, {})


if __name__ == "__main__":
    unittest.main()
