import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.p09 import prepare_crossref_discovery_fixture as subject


class CrossrefDiscoveryFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (subject.ROOT / subject.BASE).read_bytes()

    def test_fixed_native_base_and_all_nondelta_parts_are_preserved(self):
        value, metadata = subject.prepare(self.raw)
        self.assertEqual(metadata['generated_input']['sha256'], subject.sha(value))
        self.assertGreater(metadata['preserved_nonsection_parts'], 0)
        with zipfile.ZipFile(io.BytesIO(value)) as output:
            section = output.read(subject.package_tools.SECTION)
        self.assertEqual(section.count(b'<hp:bookmark '), 1)
        self.assertIn(subject.TEXT.encode(), section)
        self.assertEqual(subject.sha(self.raw), subject.BASE_SHA)

    def test_repeated_pure_preparation_is_deterministic_and_does_not_write(self):
        self.assertTrue(subject.prepare(self.raw) == subject.prepare(self.raw))

    def test_wrong_source_hash_rejects_before_rebuild(self):
        for raw in (b'', self.raw + b'x', self.raw[:-1] + b'x'):
            with self.assertRaisesRegex(ValueError, '^CROSSREF_FIXTURE_EXACT_FROZEN_NATIVE_SAVED_BASE$'):
                subject.prepare(raw)

    def test_section_profile_dtd_existing_bookmark_and_identifier_limits_reject(self):
        valid = (b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
                 b'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
                 b'<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>x</hp:t></hp:run></hp:p></hs:sec>')
        for raw in (valid.replace(b'id="0"', b'id="4294967295"', 1),
                    valid.replace(b'<hp:t>x</hp:t>', b'<hp:ctrl><hp:bookmark name="old"/></hp:ctrl>'),
                    valid.replace(b' charPrIDRef="0"', b''), b'<!DOCTYPE root []>' + valid):
            with self.assertRaises(ValueError):
                subject.insert_paragraph(raw)

    def test_exclusive_publication_does_not_overwrite_owned_or_unrelated_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'retained.bin'
            subject.package_tools.publish(path, b'original')
            with self.assertRaises(ValueError):
                subject.package_tools.publish(path, b'replacement')
            self.assertEqual(path.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
