from __future__ import annotations
from pathlib import Path
import tempfile
import unittest
from tools.p09 import verify_p08_additive_export_source_bridge_v4 as q


class NativeFormPackagePublicExportTests(unittest.TestCase):
    def test_exact_four_export_spans_recover_all_original_libraries(self):
        raw = q.checked(q.ROOT/q.LIB,q.CURRENT_LIB)
        v3 = q.project(raw); self.assertEqual(q.sha256(v3),q.old3.CURRENT_LIB)
        v2 = q.old3.project(v3); old1,old2 = q.old3.predecessors()
        v1 = old2.project(v2); self.assertEqual(q.sha256(old1.project(v1)),old1.PREDECESSOR_LIB)
        for delta in q.DELTAS:
            for changed in (raw+delta,raw.replace(delta,b"",1),raw.replace(delta,delta.replace(b"native_form",b"altered_form"),1)):
                with self.subTest(sha=q.sha256(changed)),self.assertRaises(ValueError): q.project(changed,require_current=False)
        for changed in (raw+b" ",raw+b"\npub use unqualified::*;\n",raw.replace(b"mod asset;",b"mod changed_asset;",1)):
            with self.assertRaises(ValueError): q.project(changed,require_current=False)
        with self.assertRaisesRegex(ValueError,"current_package_public_export_lib_identity_changed"): q.project(v3)

    def test_all_three_source_capsules_and_named_archives_are_exact(self):
        for name in (*q.old3.RECEIPTS,*q.RECEIPTS):
            checked = q.historical_sources(name)
            self.assertTrue(checked)
            for path,record in checked.items():
                self.assertEqual(q.sha256((q.ROOT/record["checked_path"]).read_bytes()),record["sha256"])
        for path,digest in q.ARCHIVES.values(): q.checked(q.ROOT/path,digest)
        self.assertFalse(q.historical_sources("P09-29")["crates/hwpx-package/src/native_form_package.rs"]["archived_predecessor_source"])
        self.assertFalse(q.historical_sources("P09-30")["crates/hwpx-package/src/native_form_package_lowering.rs"]["archived_predecessor_source"])

    def test_complete_public_and_pending_bodies_equal_frozen_predecessors(self):
        for public,pending in ((q.PUBLIC_BINDING,"crates/hwpx-package/tests/native_form_package_pending_export.rs"),
                               (q.PUBLIC_OUTPUT,"crates/hwpx-package/tests/native_form_package_output_pending_export.rs")):
            value = q.public_lineage(public,pending)
            self.assertTrue(value["original_test_body_byte_exact"])
            self.assertTrue(value["pending_test_body_byte_exact"])
            self.assertTrue(value["public_library_only"])

    def test_changed_public_case_source_inclusion_or_pending_import_refused(self):
        public,pending = q.PUBLIC_BINDING,"crates/hwpx-package/tests/native_form_package_pending_export.rs"
        original = (q.ROOT/public).read_bytes()
        changed_cases = [original.replace(b"use hwpx_package::*;",b"use fake_package::*;",1),
                         original+b'\n#[path="../src/native_form_package.rs"] mod fake;\n',
                         original.replace(b"90001",b"90002",1)]
        for changed in changed_cases:
            self.assertNotEqual(changed,original)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for relative in (q.ARCHIVES[pending][0],pending):
                    destination = root/relative; destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes((q.ROOT/relative).read_bytes())
                destination = root/public; destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(changed)
                with self.assertRaises(ValueError): q.public_lineage(public,pending,root)

    def test_forged_failed_ignored_or_missing_public_test_results_refused(self):
        names = q.binding.EXPECTED_TESTS
        original = "\n".join("test "+n+" ... ok" for n in sorted(names))+"\ntest result: ok. 17 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        q.test_inventory(original,names,17)
        for changed in (original.replace("17 passed","16 passed"),original.replace(" ... ok"," ... FAILED",1),
                        original.replace(" ... ok"," ... ignored",1),original+"test extra ... ok\n"):
            with self.assertRaisesRegex(ValueError,"package_public_export_test_inventory_invalid"): q.test_inventory(changed,names,17)

    def test_current_public_source_executes_actual_oracles_and_retains_all_failures(self):
        value = q.verify()
        self.assertEqual(value["actual_public_rust_tests"]["binding"]["passed"],17)
        self.assertEqual(value["actual_public_rust_tests"]["output"]["passed"],19)
        self.assertEqual(value["actual_public_rust_tests"]["output"]["actual_library_unit_tests"]["passed"],2)
        self.assertEqual(set(value["actual_public_rust_tests"]["output"]["independent_generated_package_checks"]),set(q.output.CASES))
        self.assertEqual(len(value["actual_predecessor_current_failures"]),6)
        for failure in value["actual_predecessor_current_failures"].values():
            self.assertTrue(failure["actually_invoked"]); self.assertEqual(failure["state"],"fail")
        self.assertEqual(len(value["required_current_validators"]),25)
        self.assertEqual(sum(c["state"] == "fail" for c in value["required_current_validators"]),9)
        self.assertTrue(value["claims"]["public_package_reader_and_lowerer_tests_executed"])
        self.assertTrue(value["claims"]["complete_generated_output_packages_independently_verified"])
        for key in ("archived_sources_are_current_full_verifier_pass","predecessor_receipts_rewritten","legacy_live_aggregate_now_pass",
                    "new_adapter_target_execution","current_target_promotion","production_routing_qualified","p09_complete","product_complete"):
            self.assertFalse(value["claims"][key])
        public = q.output.SHARED.lifecycle.canonical_bytes(value).decode()
        for private in (str(q.ROOT),q.binding.prior.CAPTURE,"P08FORMINSERT"): self.assertNotIn(private,public)

    def test_missing_or_changed_archive_and_capsule_fail_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises((OSError,ValueError)): q.historical_sources("P09-30",root)
            archive = root/q.ARCHIVES[q.LIB][0]; archive.parent.mkdir(parents=True)
            archive.write_bytes((q.ROOT/q.ARCHIVES[q.LIB][0]).read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"public_export_source_identity_changed"): q.project((q.ROOT/q.LIB).read_bytes(),root)
            path,_ = q.RECEIPTS["P09-29"]; receipt = root/path; receipt.parent.mkdir(parents=True,exist_ok=True)
            receipt.write_bytes((q.ROOT/path).read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"public_export_source_identity_changed"): q.record("P09-29",root)


if __name__ == "__main__": unittest.main()
