from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from tools.p09 import qualify_native_form_compatibility as q

ROOT = Path(__file__).resolve().parents[3]


class NativeFormCompatibilityTests(unittest.TestCase):
    def test_actual_saved_control_has_no_native_identity_and_has_real_anchor(self):
        value = q.capture()
        self.assertFalse(value["native_id_present"])
        self.assertFalse(value["native_instance_id_present"])
        self.assertEqual(value["control_count"], 1)
        self.assertEqual(value["native_tag"], "edit")
        self.assertEqual(value["geometry_child_names"], ["sz", "pos", "outMargin"])

    def test_actual_rust_probe_reproduces_gaps_and_stays_non_green(self):
        value = q.run_probe()
        q.verify_probe(value)
        self.assertEqual(value["legacy_actual_capture_error"], "form_control_hwpx_invalid_attribute")
        self.assertTrue(value["diagnostic_wrong_anchor_and_shape_binding_admitted"])
        self.assertFalse(value["actual_form_target_pass"])

    def test_claim_promotion_coercion_and_unknown_probe_fields_rejected(self):
        original = q.run_probe()
        for key, changed in (("actual_form_target_pass", True), ("native_session_started", True),
                             ("green_rows", False), ("source_capture_preserved", 1),
                             ("capture_package_sha256", "0" * 64), ("unknown", False)):
            value = copy.deepcopy(original)
            value[key] = changed
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "native_form_probe_contract_invalid"):
                q.verify_probe(value)

    def test_capture_hash_and_missing_corpus_fail_without_substitution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / q.CAPTURE
            path.parent.mkdir(parents=True)
            with self.assertRaises((OSError, ValueError)):
                q.capture(root)
            path.write_bytes((ROOT / q.CAPTURE).read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "package_sha256_mismatch"):
                q.capture(root)

    def test_qualified_record_has_no_raw_text_private_paths_or_false_gate(self):
        value = q.qualify()
        raw = q.shared.lifecycle.canonical_bytes(value).decode()
        self.assertNotIn("P08 FORM INSERT", raw)
        self.assertNotIn(str(ROOT), raw)
        self.assertFalse(value["claims"]["new_native_identity_profile_implemented"])
        self.assertFalse(value["claims"]["actual_new_form_target_execution"])
        self.assertFalse(value["claims"]["product_complete"])
        self.assertFalse(value["claims"]["p09_complete"])
        self.assertEqual(value["claims"]["green_rows"], 0)

    def test_source_lock_drift_is_not_qualified_as_a_runtime_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (q.CAPTURE, *q.predecessor.IMPLEMENTATION_SHA256):
                output = root / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes((ROOT / relative).read_bytes())
            path = root / "crates/hwpx-package/src/form_control_hwpx.rs"
            path.write_bytes(path.read_bytes() + b"// drift\n")
            with self.assertRaisesRegex(ValueError, "native_form_predecessor_implementation_drift"):
                q.qualify(root)


if __name__ == "__main__":
    unittest.main()
