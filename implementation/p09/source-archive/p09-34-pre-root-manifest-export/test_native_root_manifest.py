from __future__ import annotations
import copy
import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.p09 import qualify_native_root_manifest as q


def repack(raw, transform, *, reverse=False, compression=None):
    result=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(result,"w") as output:
        entries=source.infolist()
        for entry in reversed(entries) if reverse else entries:
            data=source.read(entry); entry=copy.copy(entry)
            if compression is not None: entry.compress_type=compression
            output.writestr(entry,transform(entry.filename,data))
    return result.getvalue()


class NativeRootManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="p09-33-independent-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory=Path(cls.temp.name).resolve()
        cls.stdout=q.cargo(directory=cls.directory)

    def case(self,name):
        return ((self.directory/f"{name}-source.hwpx").read_bytes(),(self.directory/f"{name}-output.hwpx").read_bytes())

    def test_all_twelve_actual_compiled_cases_and_six_whole_package_artifacts_verified(self):
        self.assertEqual(q.test_inventory(self.stdout)["passed"],12)
        results=q.artifacts(self.directory)
        self.assertEqual([r["changed_href_attributes"] for r in results.values()],[0,1,1])
        self.assertEqual([r["entry_count"] for r in results.values()],[11,12,12])
        for result in results.values():
            self.assertEqual(result["qualification"],"package_preparation_only_native_and_typed_reference_unqualified")

    def test_predecessor_current_sources_and_pending_export_boundary_are_actual(self):
        q.sources()

    def test_rehashed_other_part_preview_header_and_body_changes_are_not_hidden(self):
        source,original=self.case("two-section-text")
        for name in ("Contents/header.xml","Contents/section0.xml","Preview/PrvImage.png","settings.xml"):
            changed=repack(original,lambda n,r:r+b" " if n==name else r)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"root_manifest_independent_complete_output_mismatch"):
                q.verify_case("two-section-text",source,changed)

    def test_rehashed_wrong_href_or_other_manifest_metadata_is_rejected(self):
        source,original=self.case("two-section-text")
        for old,new in ((b'Contents/section1.xml',b'Contents/section0.xml'),(b'application/xml',b'application/other')):
            changed=repack(original,lambda n,r:r.replace(old,new) if n=="Contents/content.hpf" else r)
            with self.subTest(old=old),self.assertRaisesRegex(ValueError,"root_manifest_independent_complete_output_mismatch"):
                q.verify_case("two-section-text",source,changed)

    def test_noop_raw_archive_and_original_source_cannot_be_replaced(self):
        source,out=self.case("actual-native")
        changed=repack(out,lambda n,r:r,compression=zipfile.ZIP_STORED)
        with self.assertRaisesRegex(ValueError,"root_manifest_original_noop_not_raw_exact"):
            q.verify_case("actual-native",source,changed)
        with self.assertRaisesRegex(ValueError,"root_manifest_original_source_substituted"):
            q.verify_case("actual-native",changed,changed)

    def test_changed_order_and_compression_fail_independent_verification(self):
        source,out=self.case("two-section-radio")
        for changed in (repack(out,lambda n,r:r,reverse=True),repack(out,lambda n,r:r,compression=zipfile.ZIP_STORED)):
            with self.assertRaisesRegex(ValueError,"root_manifest_independent_complete_output_mismatch"):
                q.verify_case("two-section-radio",source,changed)

    def test_duplicate_missing_failed_and_ignored_compiled_test_inventory_rejected(self):
        for changed in (self.stdout.replace(" ... ok"," ... ignored",1),self.stdout.replace(" ... ok"," ... FAILED",1),
                        self.stdout.replace("12 passed","11 passed"),self.stdout+f"\ntest {q.ACTUAL} ... ok\n"):
            with self.assertRaises(ValueError):q.test_inventory(changed)

    def test_complete_qualification_does_not_promote_native_public_or_product_evidence(self):
        value=q.qualify()
        self.assertFalse(value["claims"]["public_root_preparation_exports_connected"])
        self.assertFalse(value["claims"]["native_open_failure_resolved"])
        self.assertFalse(value["claims"]["color_and_native_name_failures_resolved"])
        self.assertFalse(value["privacy"]["native_session_started"])
        self.assertEqual(value["claims"]["green_rows"],0)
        self.assertFalse(value["claims"]["p09_complete"])


if __name__ == "__main__":unittest.main()
