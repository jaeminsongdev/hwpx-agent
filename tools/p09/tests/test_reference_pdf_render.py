"""Pure adversarial controls, no native evidence/dispatch/session creation."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image
from tools.p09 import reference_pdf_render as r
from tools.p09 import reference_render_consumer as c


class Page(dict):
    def __init__(self, **extra):
        super().__init__({'/Resources': {}}, **extra)
        self.mediabox = [0, 0, 595, 841]
        self.cropbox = self.mediabox.copy()


class Reader:
    def __init__(self, pages, encrypted=False):
        self.pages, self.is_encrypted = pages, encrypted
        self.trailer = {'/Root': {}}


class Tests(unittest.TestCase):
    def meta(self, pages=None, encrypted=False):
        with patch.object(r, 'PdfReader', return_value=Reader(pages or [Page()], encrypted)):
            return r.geometry(b'%PDF-pure-parser-fixture-not-native')

    def test_actual_original_geometry(self):
        raw = r.bounded(r.ROOT / c.HISTORICAL[0][0], c.HISTORICAL[0][1])
        self.assertEqual(r.geometry(raw)[0]['raster_sizes'], {'96': [794, 1122], '192': [1587, 2243]})

    def test_pdf_magic_and_size(self):
        for raw in (b'', b'not_pdf', b'%PDF-' + b'x' * r.MAX_BYTES):
            with self.assertRaises(ValueError): r.geometry(raw)

    def test_wrong_source_hash(self):
        with self.assertRaisesRegex(ValueError, 'p57_input_sha256'):
            r.bounded(r.ROOT / c.HISTORICAL[0][0], '0' * 64)

    def test_encryption_rejected(self):
        with self.assertRaisesRegex(ValueError, 'p57_encrypted_pdf'): self.meta(encrypted=True)

    def test_page_count_bound(self):
        with self.assertRaisesRegex(ValueError, 'p57_page_count'): self.meta([Page()] * 33)

    def test_geometry_nan_and_crop(self):
        for mode in ('nan', 'crop'):
            p = Page()
            if mode == 'nan': p.mediabox[0] = float('nan')
            else: p.cropbox[2] = 596
            with self.assertRaisesRegex(ValueError, 'p57_page_geometry'): self.meta([p])

    def test_rotation_and_userunit(self):
        self.assertEqual(self.meta([Page(**{'/Rotate': 90})])[0]['raster_sizes']['96'], [1122, 794])
        for props in ({'/Rotate': True}, {'/Rotate': 45}, {'/UserUnit': 2}):
            with self.assertRaises(ValueError): self.meta([Page(**props)])

    def test_pixel_allocations_bound_before_render(self):
        p = Page(); p.mediabox = p.cropbox = [0, 0, 14400, 14400]
        with self.assertRaisesRegex(ValueError, 'p57_page_pixel_boundary'): self.meta([p])
        with self.assertRaisesRegex(ValueError, 'p57_total_pixel_boundary'): self.meta([Page()] * 32)

    def test_external_fonts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'p57_external_font_rejected'):
            r.font_scope({'/Font': {'/F': {'/Subtype': '/Type1'}}})
        r.font_scope({'/Font': {'/F': {'/FontDescriptor': {'/FontFile2': object()}}}})

    def test_recursive_resources_bound(self):
        resource = {}
        for _ in range(18): resource = {'/XObject': {'/F': {'/Subtype': '/Form', '/Resources': resource}}}
        with self.assertRaisesRegex(ValueError, 'p57_resource_depth'): r.font_scope(resource)

    def test_unsupported_appearances_rejected(self):
        with self.assertRaisesRegex(ValueError, 'p57_annotation_appearance_unsupported'):
            self.meta([Page(**{'/Annots': [object()]})])
        for resource in ({'/Pattern': {'/P': object()}}, {'/ExtGState': {'/G': {'/Font': ['x', 1]}}}):
            with self.assertRaises(ValueError): r.font_scope(resource)

    def test_exact_blank_not_semantic_acceptance(self):
        with Image.new('RGB', (3, 3), 'white') as a:
            value = r.pixels(a, a)
            self.assertEqual((value['state'], value['changed_pixels'], value['left_nonwhite_bbox']),
                             ('exact_pixels', 0, None))

    def test_unmasked_rgb_difference(self):
        with Image.new('RGB', (3, 3), 'white') as a, Image.new('RGB', (3, 3), 'white') as b:
            b.putpixel((2, 1), (254, 253, 252))
            value = r.pixels(a, b)
            self.assertEqual((value['changed_pixels'], value['rgb_delta_sum'], value['difference_bbox']),
                             (1, 6, [2, 1, 3, 2]))

    def test_dimension_or_mode_mismatch(self):
        with Image.new('RGB', (2, 2)) as a, Image.new('RGB', (3, 2)) as b, Image.new('L', (2, 2)) as gray:
            self.assertEqual(r.pixels(a, b)['state'], 'dimension_mismatch')
            with self.assertRaisesRegex(ValueError, 'p57_rgb_required'): r.pixels(gray, gray)

    def test_current_failed_or_unclaimed_not_promoted(self):
        record = {'harness_exit': 0, 'lifecycle': 'pass', 'artifacts': {
            n: {'lifecycle_claim_bound': True} for n in ('saved.pdf', 'reopened.pdf')}}
        self.assertTrue(c.stage_eligible(record))
        for bad in ({**record, 'harness_exit': 2}, {**record, 'lifecycle': 'fail'}, {**record, 'artifacts': {}}):
            self.assertFalse(c.stage_eligible(bad))

    def test_all17_direct_baselines_absent(self):
        values = c.direct_baselines()
        self.assertEqual(tuple(v['case_id'] for v in values), c.q.EXPECTED_IDS)
        self.assertTrue(all(v['state'] == 'NOT_RUN' and not v['historical_baseline_reused'] for v in values))

    def test_numeric_full_page_mapping_and_missing_page(self):
        # Component fixture, deliberately never bound/published as native evidence.
        class Fake(r.Renderer):
            def __init__(self): self.identity = {}
            def runtime_identity(self): return {}
            def render_page(self, pdf, directory, page, dpi, size):
                return Image.new('RGB', tuple(size), 'white')
        meta = {'media_box': [0, 0, 1, 1], 'crop_box': [0, 0, 1, 1], 'rotation': 0,
                'user_unit': 1, 'raster_sizes': {'96': [2, 2], '192': [3, 3]}}
        with patch.object(r, 'geometry', side_effect=[[copy.deepcopy(meta) for _ in range(12)],
                                                     [copy.deepcopy(meta) for _ in range(11)]]):
            value = Fake().compare(b'pure_left_component', b'pure_right_component')
        self.assertEqual([p['page'] for p in value['pages']], list(range(1, 13)))
        self.assertEqual(value['pages'][-1]['state'], 'missing_right_page')
        self.assertEqual(value['state'], 'mismatch')

    def test_geometry_changes_not_hidden_by_equal_pixels(self):
        class Fake(r.Renderer):
            def __init__(self): self.identity = {}
            def runtime_identity(self): return {}
            def render_page(self, pdf, directory, page, dpi, size): return Image.new('RGB', tuple(size), 'white')
        meta = {'media_box': [0, 0, 1, 1], 'crop_box': [0, 0, 1, 1], 'rotation': 0,
                'user_unit': 1, 'raster_sizes': {'96': [2, 2], '192': [3, 3]}}
        other = {**meta, 'crop_box': [0, 0, .5, 1]}
        with patch.object(r, 'geometry', side_effect=[[meta], [other]]): value = Fake().compare(b'a', b'b')
        self.assertEqual(value['state'], 'mismatch')


if __name__ == '__main__': unittest.main()
