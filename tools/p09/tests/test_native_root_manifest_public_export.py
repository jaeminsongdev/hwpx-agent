from __future__ import annotations
from pathlib import Path
import tempfile
import unittest
from tools.p09 import verify_p08_additive_export_source_bridge_v5 as q


class NativeRootManifestPublicExportTests(unittest.TestCase):
    def copied(self, relatives):
        temporary = tempfile.TemporaryDirectory(prefix="p09-34-public-negative-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in relatives:
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((q.ROOT / relative).read_bytes())
        return root

    def test_exact_public_exports_recover_v4_v3_v2_v1_and_original_p08_bytes(self):
        raw = q.checked(q.ROOT / q.LIB, q.CURRENT_LIB)
        v4 = q.project(raw); self.assertEqual(q.sha256(v4), q.old4.CURRENT_LIB)
        v3 = q.old4.project(v4); v2 = q.old4.old3.project(v3)
        old1, old2 = q.old4.old3.predecessors()
        v1 = old2.project(v2)
        self.assertEqual(q.sha256(old1.project(v1)), old1.PREDECESSOR_LIB)
        for delta in q.DELTAS:
            for mutated in (raw + delta, raw.replace(delta, b"", 1), raw.replace(delta, delta.replace(b"native_root", b"altered_root"), 1)):
                with self.subTest(digest=q.sha256(mutated)), self.assertRaises(ValueError):
                    q.project(mutated, require_current=False)
        for mutated in (raw + b" ", raw.replace(b"mod asset;", b"mod wrong_asset;", 1), raw + b"\npub use unchecked::*;\n"):
            with self.assertRaises(ValueError): q.project(mutated, require_current=False)
        with self.assertRaisesRegex(ValueError, "current_root_public_library_identity_changed"):
            q.project(v4)

    def test_only_std_hex_helper_changes_and_no_other_source_edit_is_accepted(self):
        root = self.copied((q.preparation.MODULE, q.ARCHIVES[q.preparation.MODULE][0]))
        current = (root / q.preparation.MODULE).read_bytes()
        self.assertTrue(q.module_lineage(root)["only_declared_hash_helper_changed"])
        self.assertFalse(q.module_lineage(root)["added_runtime_dependencies"])
        for mutated in (current + b" ", current + q.NEW_HASH, current.replace(b"0123456789abcdef", b"0123456789ABCDEF", 1),
                        current.replace(b"32 * 1024 * 1024", b"64 * 1024 * 1024", 1), current.replace(q.NEW_HASH, q.OLD_HASH, 1)):
            self.assertNotEqual(current, mutated)
            (root / q.preparation.MODULE).write_bytes(mutated)
            with self.assertRaisesRegex(ValueError, "root_public_hash_only_source_delta_changed"):
                q.module_lineage(root)

    def test_complete_public_test_body_is_exact_and_source_inclusion_is_rejected(self):
        root = self.copied((q.PUBLIC_TEST, q.preparation.TEST, q.RECEIPTS["P09-33"][0]))
        current = (root / q.PUBLIC_TEST).read_bytes()
        self.assertTrue(q.public_lineage(root)["original_test_body_byte_exact"])
        for mutated in (current + b" ", current.replace(b"use hwpx_package as", b"use fake_package as", 1),
                        current + b'\n#[path="../src/native_root_manifest.rs"] mod fake;\n',
                        current.replace(b"12", b"13", 1)):
            self.assertNotEqual(current, mutated)
            (root / q.PUBLIC_TEST).write_bytes(mutated)
            with self.assertRaises(ValueError): q.public_lineage(root)

    def test_all_twelve_historical_capsules_and_eleven_exact_archives_remain_raw_pinned(self):
        historical = q.source_guard()
        self.assertEqual(len(historical), 12)
        self.assertEqual(sum(map(len, historical.values())), 194)
        self.assertTrue(historical["P09-31"][q.LIB]["archived_predecessor_source"])
        self.assertTrue(historical["P09-33"][q.preparation.MODULE]["archived_predecessor_source"])
        self.assertFalse(historical["P09-32"][q.preparation.predecessor.GENERATOR]["archived_predecessor_source"])
        for records in historical.values():
            for proof in records.values():
                q.checked(q.ROOT / proof["checked_path"], proof["sha256"])
        for path, digest in q.ARCHIVES.values(): q.checked(q.ROOT / path, digest)

    def test_missing_or_rehashed_historical_archives_and_capsules_fail_closed(self):
        name = "P09-33"
        root = self.copied((q.RECEIPTS[name][0],))
        with self.assertRaises((OSError, ValueError)): q.historical_sources(name, root)
        original = (root / q.RECEIPTS[name][0]).read_bytes()
        (root / q.RECEIPTS[name][0]).write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "public_export_source_identity_changed"): q.record(name, root)
        root = self.copied((q.ARCHIVES[q.LIB][0],))
        path = root / q.ARCHIVES[q.LIB][0]; path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "public_export_source_identity_changed"):
            q.project((q.ROOT / q.LIB).read_bytes(), root)

    def test_all_ten_preceding_full_current_verifier_failures_are_actually_invoked(self):
        failures = q.failures()
        self.assertEqual(set(failures), {"P09-21", "P09-23", "P09-27", "P09-28", "P09-29", "P09-30", "P09-31", "P09-32-preparation", "P09-32", "P09-33"})
        for failure in failures.values():
            self.assertEqual(failure["state"], "fail"); self.assertTrue(failure["actually_invoked"])

    def test_actual_public_root_tests_emit_all_six_packages_and_real_exact_receipt(self):
        result = q.root_public()
        self.assertEqual(result["passed"], 12)
        self.assertEqual(set(result["names"]), q.preparation.EXPECTED)
        self.assertTrue(result["compiled_via_public_library_only"])
        self.assertTrue(result["actual_public_typed_receipt_independently_verified"])
        self.assertEqual(set(result["independent_generated_package_checks"]), set(q.preparation.CASES))
        for receipt in result["independent_generated_package_checks"].values():
            self.assertEqual(receipt["qualification"], "package_preparation_only_native_and_typed_reference_unqualified")

    def test_retained_preparation_and_complete_native_readback_are_exact_not_new_sessions(self):
        result = q.retained_preparation_and_readback()
        self.assertTrue(result["initial_preparation_byte_exact_reproduction"])
        self.assertTrue(result["original_missing_output_delta_byte_exact"])
        self.assertTrue(result["existing_native_public_readback_exact"])
        self.assertEqual(result["existing_trace_count_reverified"], 6)
        self.assertEqual(result["existing_owned_session_count"], 10)
        self.assertFalse(result["new_native_session_started"])
        self.assertFalse(result["previous_native_failures_resolved"])
        self.assertFalse(result["pdf_render_rerun"])

    def test_full_current_successor_executes_actual_library_public_oracles_and_legacy_failures(self):
        value = q.verify()
        self.assertEqual(value["task"], "P09-34-r02")
        self.assertEqual(value["initial_v5_full_current_failure"]["state"], "fail")
        self.assertTrue(value["initial_v5_full_current_failure"]["actually_invoked"])
        self.assertEqual(value["production_library_check"]["state"], "pass")
        self.assertEqual(value["actual_public_rust_tests"]["binding"]["passed"], 17)
        self.assertEqual(value["actual_public_rust_tests"]["output"]["passed"], 19)
        self.assertEqual(value["actual_public_rust_tests"]["output"]["actual_library_unit_tests"]["passed"], 2)
        self.assertEqual(value["actual_public_rust_tests"]["root_preparation"]["passed"], 12)
        self.assertEqual(len(value["required_current_validators"]), 25)
        self.assertEqual(sum(result["state"] == "fail" for result in value["required_current_validators"]), 9)
        for key in ("exact_additive_export_chain", "public_root_preparation_exports_connected", "production_library_checked_without_test_dependencies"):
            self.assertTrue(value["claims"][key])
        for key in ("archived_sources_are_current_full_verifier_pass", "predecessor_receipts_rewritten", "legacy_live_aggregate_now_pass",
                    "new_adapter_target_execution", "current_target_promotion", "native_open_failure_resolved", "color_and_native_name_failures_resolved",
                    "typed_reference_semantics_qualified", "production_routing_qualified", "p09_complete", "product_complete"):
            self.assertFalse(value["claims"][key])
        self.assertFalse(value["privacy"]["native_session_started"])
        self.assertEqual(value["claims"]["green_rows"], 0)
        self.assertEqual(value["claims"]["render"], "not_run")
        raw = q.old4.output.SHARED.lifecycle.canonical_bytes(value).decode()
        for private in (str(q.ROOT), q.old4.binding.prior.CAPTURE, "P08FORMINSERT"):
            self.assertNotIn(private, raw)

    def test_preserved_initial_v5_is_really_invoked_and_cannot_claim_current_pass(self):
        result = q.initial_v5_failure()
        self.assertEqual(result["error_code"], "public_export_source_identity_changed")
        self.assertEqual(result["state"], "fail")
        self.assertTrue(result["actually_invoked"])


if __name__ == "__main__":
    unittest.main()
