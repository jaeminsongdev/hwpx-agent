"""Pure bounded fixture inverse/ZIP tests; no target, files, or product."""
import io
import zipfile
import unittest

import prepare_caption_isolation_controls as module

START = b'<hs:sec xmlns:hs="urn:fixture" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
END = b'</hs:sec>'
CTRL = b'<hp:ctrl><hp:autoNum num="19" numType="PICTURE"/></hp:ctrl>'
BASE = START + b'<hp:p><hp:run><hp:t>fixture</hp:t></hp:run></hp:p>' + END
NUMBERED = BASE.replace(b'<hp:t>', CTRL + b'<hp:t>', 1)


def archive(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as zip:
        for name, value in entries:
            zip.writestr(name, value)
    return output.getvalue()


class Tests(unittest.TestCase):
    def test_inverse_requires_exact_old_preinsertion_hash(self):
        self.assertEqual(module.remove_number(NUMBERED, module.digest(BASE)), BASE)
        with self.assertRaises(ValueError):
            module.remove_number(NUMBERED, '0' * 64)

    def test_no_duplicate_or_wrong_cached_number_is_accepted(self):
        for raw in (BASE, NUMBERED.replace(CTRL, CTRL * 2), NUMBERED.replace(b'num="19"', b'num="1"')):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    module.remove_number(raw, module.digest(BASE))

    def test_active_xml_rejected_before_parse(self):
        for declaration in (b'<!DOCTYPE sec>', b'<!ENTITY evil "x">'):
            with self.assertRaises(ValueError):
                module.remove_number(declaration + NUMBERED, module.digest(BASE))

    def test_rectangle_only_declared_category_change(self):
        source = b'<hp:rect numberingType="NONE"/>'
        prepared = source.replace(b'NONE', b'PICTURE')
        module.prove_preparation(prepared, source, 'P09-19-C01', b'caption')
        with self.assertRaises(ValueError):
            module.prove_preparation(prepared + b' ', source, 'P09-19-C01', b'caption')

    def test_equation_only_exact_caption_attachment(self):
        source = b'<hp:equation></hp:equation>'
        caption = b'<hp:caption></hp:caption>'
        prepared = source.replace(b'</hp:equation>', caption + b'</hp:equation>')
        module.prove_preparation(prepared, source, 'P09-19-C04', caption)
        with self.assertRaises(ValueError):
            module.prove_preparation(prepared.replace(caption, caption * 2), source, 'P09-19-C04', caption)

    def test_unknown_case_cannot_broaden_scope(self):
        with self.assertRaises(ValueError):
            module.prove_preparation(BASE, BASE, 'P09-19-C02', b'caption')

    def test_archive_preserves_other_parts_and_member_order(self):
        entries = [('mimetype', b'application/hwp+zip'), (module.SECTION, NUMBERED), ('BinData/image1.png', b'fixture')]
        raw = archive(entries)
        checks = []
        result = module.rebuild(raw, BASE, lambda: checks.append(True))
        self.assertEqual(len(checks), 3)
        with zipfile.ZipFile(io.BytesIO(result)) as zip:
            self.assertEqual(zip.namelist(), [name for name, _ in entries])
            self.assertEqual(zip.read(module.SECTION), BASE)
            self.assertEqual(zip.read('BinData/image1.png'), b'fixture')
            self.assertEqual(zip.read('mimetype'), b'application/hwp+zip')
        self.assertEqual(module.rebuild(raw, BASE), result)

    def test_archive_missing_section_or_path_escape_rejected(self):
        for entries in ([('other.xml', b'x')], [(module.SECTION, NUMBERED), ('../escape', b'x')]):
            with self.assertRaises(ValueError):
                module.rebuild(archive(entries), BASE)

    def test_resource_checkpoint_failure_is_not_swallowed(self):
        error = ValueError('TEST_RESOURCE_STOP')
        def fail():
            raise error
        with self.assertRaises(ValueError) as caught:
            module.rebuild(archive([(module.SECTION, NUMBERED)]), BASE, fail)
        self.assertIs(caught.exception, error)
