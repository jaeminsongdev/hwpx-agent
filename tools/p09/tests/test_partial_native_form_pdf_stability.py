import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.p09 import inspect_partial_native_form_pdf_stability as q

class PartialNativeFormPdfStabilityGuards(unittest.TestCase):
    def test_published_receipt_and_all_six_sources_remain_byte_exact(self):
        raw=q.prior.public.checked(q.ROOT/q.CAPSULE,"50838d87059287ce6274f68744ba3ea2ebc34c8101abfb8d211730e871f9022b",2097152)
        value=json.loads(raw,object_pairs_hook=q.prior.q.shared.lifecycle.duplicate_guard)
        self.assertEqual(value["source_sha256"],q.source_pins())
        self.assertEqual(len(value["source_sha256"]),6)
        self.assertFalse(value["claims"]["native_form_semantics_qualified"])
        self.assertFalse(value["claims"]["visual_acceptance_qualified"])
        self.assertFalse(value["claims"]["input_to_native_or_direct_automation_differential"])
        self.assertFalse(value["claims"]["new_native_session_started"])
        self.assertEqual(value["claims"]["green_rows"],0)

    def test_old_seven_attempts_all_thirty_five_files_and_failed_c07_are_preserved(self):
        raw=q.prior.public.checked(q.ROOT/q.CAPSULE,"50838d87059287ce6274f68744ba3ea2ebc34c8101abfb8d211730e871f9022b",2097152)
        old=json.loads(raw)["prior_partial_batch_preserved"]
        self.assertEqual(q.prior.prior_attempts(),old)
        self.assertEqual(len(old["source_sha256"]),35)
        self.assertEqual(old["cases"][6]["trace_binding"],"fail")
        self.assertEqual(old["cases"][6]["recorded_remaining"],1)
        self.assertEqual(old["not_run_cases"],8)

    def test_one_pixel_change_is_counted_without_mask_or_tolerance(self):
        with tempfile.TemporaryDirectory(prefix="p09-36-pdf-guard-",dir=q.ROOT/"fixtures/target-build") as temporary:
            left,right=Path(temporary)/"left.png",Path(temporary)/"right.png"
            image=Image.new("RGB",(100,100),"white");image.putpixel((2,2),(0,0,0));image.save(left)
            image.putpixel((4,4),(0,255,255));image.save(right)
            result=q.measure(left,right)
            self.assertEqual(result["changed_pixels"],1)
            self.assertEqual(result["absolute_rgb_delta_sum"],255)
            self.assertEqual(result["difference_bbox"],(4,4,5,5))
            equal=q.measure(left,left)
            self.assertEqual(equal["changed_pixels"],0)
            self.assertIsNone(equal["difference_bbox"])

    def test_blank_or_different_size_pages_are_not_passed_as_equal(self):
        with tempfile.TemporaryDirectory(prefix="p09-36-pdf-guard-",dir=q.ROOT/"fixtures/target-build") as temporary:
            a,b=Path(temporary)/"a.png",Path(temporary)/"b.png"
            Image.new("RGB",(100,100),"white").save(a)
            with self.assertRaisesRegex(ValueError,"partial_pdf_blank_page_rejected"):q.measure(a,a)
            Image.new("RGB",(101,100),"black").save(b)
            with self.assertRaisesRegex(ValueError,"partial_pdf_dimensions_invalid"):q.measure(a,b)

    def test_all_eight_pages_six_pairs_and_sixteen_derived_pngs_are_bound(self):
        value=json.loads(q.prior.public.checked(q.ROOT/q.CAPSULE,"50838d87059287ce6274f68744ba3ea2ebc34c8101abfb8d211730e871f9022b",2097152))
        self.assertEqual([case["case_id"] for case in value["cases"]],[f"P09-35-C{i:02}" for i in range(1,7)])
        self.assertEqual(sum(case["page_count"] for case in value["cases"]),8)
        self.assertEqual(len(value["derived_png_sha256"]),16)
        self.assertFalse(value["masks_or_tolerances_used"])
        for case in value["cases"]:
            self.assertEqual(case["state"],"equal")
            self.assertEqual(len(case["pages"]),case["page_count"])
            self.assertTrue(all(page["changed_pixels"]==page["absolute_rgb_delta_sum"]==0 for page in case["pages"]))
        for name,digest in value["derived_png_sha256"].items():
            q.prior.public.checked(q.ROOT/q.RENDERS/name,digest,16777216)

if __name__=="__main__":unittest.main()
