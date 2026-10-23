"""Pure new comparison controls: no Native, old evidence replay or file mutation."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inspect_prepared_bookmark637_render as m


class Box:
    def __init__(self, value): self.value = value
    def get_object(self): return self.value


def link():
    return Box({'/Type': '/Annot', '/Subtype': '/Link', '/Rect': [1, 2, 3, 4],
        '/C': [0, 0, 1], '/Border': [0, 0, 0], '/F': 4, '/H': '/I',
        '/A': Box({'/S': '/URI', '/URI': 'https://private.invalid/example'})})


class Page(dict):
    mediabox = [0, 0, 595, 841]
    cropbox = mediabox
    def extract_text(self): return 'private text'


class Tests(unittest.TestCase):
    def test_exact_nonblank_pass(self):
        with m.Image.new('RGB', (10, 10), 'white') as a:
            a.putpixel((1, 1), (0, 0, 0))
            self.assertTrue(m.compare_images(a, a)['accepted_pair'])

    def test_exact_blank_never_passes(self):
        with m.Image.new('RGB', (10, 10), 'white') as a:
            result = m.compare_images(a, a)
            self.assertEqual(result['changed_pixels'], 0)
            self.assertFalse(result['accepted_pair'])

    def test_nonblank_to_blank_fails(self):
        with m.Image.new('RGB', (10, 10), 'white') as a, a.copy() as b:
            a.putpixel((1, 1), (0, 0, 0))
            result = m.compare_images(a, b)
            self.assertFalse(result['accepted_pair'])
            self.assertEqual(result['changed_pixels'], 1)

    def test_single_channel_difference_is_not_tolerated(self):
        with m.Image.new('RGB', (10, 10), 'white') as a, a.copy() as b:
            a.putpixel((1, 1), (0, 0, 0))
            b.putpixel((1, 1), (1, 0, 0))
            self.assertFalse(m.compare_images(a, b)['accepted_pair'])

    def test_dimension_mismatch_fails(self):
        with m.Image.new('RGB', (10, 10), 'black') as a, m.Image.new('RGB', (10, 11), 'black') as b:
            self.assertFalse(m.compare_images(a, b)['accepted_pair'])

    def test_indirect_annotation_array_and_private_hashes(self):
        class Reader:
            is_encrypted = False
            trailer = {'/Root': Box({})}
            pages = [Page({'/Annots': Box([link()])})]
        with patch.object(m, 'PdfReader', return_value=Reader()):
            rows = m.pdf_metadata(b'%PDF-pure-reader-control')
        self.assertEqual(len(rows[0]['annotations']), 1)
        self.assertNotIn('private', json.dumps(rows))

    def test_annotation_appearance_or_active_action_rejected(self):
        bad = link(); bad.value['/AP'] = Box({})
        with self.assertRaisesRegex(ValueError, 'STATIC_LINK_PROFILE_ONLY'): m.annotation(bad)
        bad = link(); bad.value['/A'].value = {'/S': '/JavaScript', '/JS': 'private code'}
        with self.assertRaisesRegex(ValueError, 'STATIC_URI_NOT_EXECUTION'): m.annotation(bad)

    def test_image_format_and_geometry_fail_closed(self):
        with m.Image.new('RGB', (10, 10), 'black') as a:
            stream = io.BytesIO(); a.save(stream, format='BMP'); raw = stream.getvalue()
        with self.assertRaisesRegex(ValueError, 'IMAGE_PROFILE'): m.image(raw, 'PNG')
        with self.assertRaisesRegex(ValueError, 'IMAGE_GEOMETRY'): m.image(raw, 'BMP', [11, 10])


if __name__ == '__main__':
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful() else 2)
