from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.p09 import verify_p08_additive_export_source_bridge_v3 as q


class NativeFormPublicExportTests(unittest.TestCase):
    def test_live_lib_recovers_exact_archived_v2_v1_and_p08(self):
        old1, old2 = q.predecessors()
        raw = q.checked(q.ROOT / q.LIB, q.CURRENT_LIB)
        archived = q.project(raw)
        self.assertEqual(q.sha256(archived), old2.CURRENT_LIB)
        v1 = old2.project(archived)
        self.assertEqual(q.sha256(v1), old1.CURRENT_LIB)
        self.assertEqual(q.sha256(old1.project(v1)), old1.PREDECESSOR_LIB)

    def test_unknown_edits_and_missing_duplicate_or_modified_export_spans_rejected(self):
        raw = q.checked(q.ROOT / q.LIB, q.CURRENT_LIB)
        changed = [raw + b"\npub use unrelated::*;\n", raw + b" ",
                   raw.replace(b"mod asset;", b"mod altered_asset;", 1)]
        for delta in q.DELTAS:
            changed.extend((raw.replace(delta, b"", 1), raw + delta,
                            raw.replace(delta, delta.replace(b"native_form", b"altered_form"), 1)))
        for value in changed:
            self.assertNotEqual(value, raw)
            with self.subTest(sha=q.sha256(value)), self.assertRaises(ValueError):
                q.project(value, require_current=False)
        with self.assertRaisesRegex(ValueError, "current_public_export_lib_identity_changed"):
            q.project(q.checked(q.ROOT / q.ARCHIVES[q.LIB][0], q.ARCHIVES[q.LIB][1]))

    def test_all_preserved_receipt_and_component_source_pins_are_really_checked(self):
        for name in q.RECEIPTS:
            value = q.historical_sources(name)
            self.assertTrue(value)
            for path, check in value.items():
                self.assertEqual(q.sha256((q.ROOT / check["checked_path"]).read_bytes()), check["sha256"])
                if check["archived_predecessor_source"]:
                    self.assertIn(path, q.ARCHIVES)
        q27 = q.historical_sources("P09-27")
        self.assertFalse(q27["crates/hwpx-package/src/native_form_hwpx.rs"]["archived_predecessor_source"])

    def test_archived_and_receipt_tamper_is_not_qualified_as_a_current_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = q.project((q.ROOT / q.LIB).read_bytes())
            archive = root / q.ARCHIVES[q.LIB][0]
            archive.parent.mkdir(parents=True)
            archive.write_bytes(source + b"tamper")
            with self.assertRaisesRegex(ValueError, "public_export_source_identity_changed"):
                q.project((q.ROOT / q.LIB).read_bytes(), root)
            path, _ = q.RECEIPTS["P09-27"]
            output = root / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes((q.ROOT / path).read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "public_export_source_identity_changed"):
                q.record("P09-27", root)

    def test_public_library_executes_all_exact_preceding_real_cases(self):
        result = q.public_cases()
        self.assertEqual(result["passed"], 18)
        self.assertEqual(result["ignored"], 0)
        self.assertEqual(result["test_target"], "native_form_hwpx_public")
        self.assertTrue(result["compiled_via_public_library_only"])
        self.assertTrue(result["preceding_test_body_byte_exact"])

    def test_changed_cases_or_direct_source_inclusion_cannot_claim_public_execution(self):
        path, _ = q.RECEIPTS["P09-27"]
        pending = "crates/hwpx-package/tests/native_form_hwpx_pending_export.rs"
        public = (q.ROOT / q.PUBLIC_TEST).read_bytes()
        for changed in (public.replace(b"use hwpx_package::{", b"use injected_impl::{", 1),
                        public + b'\n#[path = "../src/native_form_hwpx.rs"] mod injected;\n',
                        public.replace(b"90_001", b"91_001", 1)):
            self.assertNotEqual(changed, public)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for relative in (path, pending):
                    output = root / relative
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes((q.ROOT / relative).read_bytes())
                output = root / q.PUBLIC_TEST
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(changed)
                with self.assertRaisesRegex(ValueError, "public_export_case_lineage_changed"):
                    q.public_cases(root)

    def test_full_source_successor_keeps_actual_predecessor_failures_and_non_gate_scope(self):
        value = q.verify()
        self.assertEqual(value["state"], "public_export_source_qualified_non_gate")
        self.assertTrue(value["claims"]["shared_library_export_connected"])
        for result in value["actual_predecessor_current_failures"].values():
            self.assertEqual(result["state"], "fail")
            self.assertTrue(result["actually_invoked"])
        for key in ("archived_sources_are_current_full_verifier_pass", "predecessor_receipts_rewritten",
                    "legacy_live_aggregate_now_pass", "new_adapter_target_execution", "current_target_promotion",
                    "package_part_bindings_independently_read", "production_routing_qualified", "p09_complete", "product_complete"):
            self.assertFalse(value["claims"][key])
        self.assertEqual(len(value["required_current_validators"]), 25)
        raw = str(value)
        self.assertNotIn(str(q.ROOT), raw)
        self.assertNotIn("P08 FORM INSERT", raw)


if __name__ == "__main__":
    unittest.main()
