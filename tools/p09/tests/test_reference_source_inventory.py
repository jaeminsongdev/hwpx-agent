import io
import struct
import unittest
from unittest.mock import patch
import zipfile

import reference_source_inventory as m


def xml(body=''):
    return ('<s xmlns:h="' + m.PARAGRAPH_NS + '">' + body + '</s>').encode()


def package(section=None, extras=()):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', b'application/hwp+zip')
        z.writestr('Contents/section0.xml', xml() if section is None else section)
        for name, value in extras:
            z.writestr(name, value)
    return out.getvalue()


class Tests(unittest.TestCase):
    def test_observed_not_invented_reference_validation(self):
        raw = package(xml('<h:bookmark name="private"/><h:fieldBegin type="HYPERLINK"/>'))
        row = m.inspect(raw)
        self.assertEqual(row['observed_controls']['bookmark'], 1)
        self.assertEqual(row['observed_field_types'], {'HYPERLINK': 1})
        self.assertEqual(row['package_sha256'], m.digest(raw))
        self.assertFalse(row['product_reference_validation_executed'])
        self.assertFalse(row['targets_or_reference_edges_resolved'])
        self.assertFalse(row['typed_state_created'])
        self.assertEqual(row['files_written'], 0)
        self.assertNotIn('private', str(row))

    def test_namespace_and_unknown_values_not_fabricated(self):
        row = m.inspect(package(xml('<fieldBegin type="FORMULA"/><h:fieldBegin type="secret value"/><h:fieldBegin/>')))
        self.assertEqual(row['observed_controls']['fieldBegin'], 2)
        self.assertEqual(row['unknown_field_types'], 1)
        self.assertEqual(row['missing_field_types'], 1)
        self.assertNotIn('secret', str(row))

    def test_alias_prefix_is_namespace_correct(self):
        row = m.scan_xml(('<x xmlns:q="' + m.PARAGRAPH_NS + '"><q:autoNum/></x>').encode())
        self.assertEqual(row['controls']['autoNum'], 1)

    def test_all_xml_and_hpf_scanned_without_role_claim(self):
        row = m.inspect(package(extras=[('Contents/content.hpf', xml('<h:fieldEnd/>'))]))
        self.assertEqual(len(row['xml_parts']), 2)
        self.assertEqual(row['observed_controls']['fieldEnd'], 1)
        self.assertFalse(row['xml_role_assignment_or_spine_completeness_qualified'])

    def test_one_member_expansion_and_one_scan(self):
        calls = []
        original = m.member_bytes
        def read(z, info, check):
            calls.append(info.filename)
            return original(z, info, check)
        with patch.object(m, 'member_bytes', read):
            row = m.inspect(package(extras=[('BinData/a.bin', b'abc')]))
        self.assertEqual(calls, ['mimetype', 'Contents/section0.xml', 'BinData/a.bin'])
        self.assertEqual(row['member_expansion_passes'], 1)
        self.assertEqual(row['XML_scan_passes'], 1)

    def test_directory_limit_checked_before_zip_allocation(self):
        raw = bytearray(package())
        end = raw.rfind(b'PK\x05\x06')
        struct.pack_into('<HH', raw, end + 8, 65535, 65535)
        with patch.object(m.zipfile, 'ZipFile', side_effect=AssertionError('NO_ALLOCATION')):
            with self.assertRaisesRegex(ValueError, 'CLOSED_BOUNDED_DIRECTORY'):
                m.inspect(bytes(raw))

    def test_archive_and_central_directory_bounds(self):
        raw = package()
        with patch.object(m, 'MAX_ARCHIVE', len(raw) - 1):
            with self.assertRaisesRegex(ValueError, 'ARCHIVE_SIZE'):
                m.inspect(raw)
        with self.assertRaises(ValueError):
            m.inspect(raw + b'trailing')

    def test_duplicate_case_alias_and_traversal(self):
        for name in ('contents/SECTION0.xml', '../a.xml', '/a.xml', 'a:stream', 'a./b.xml'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.inspect(package(extras=[(name, xml())]))
        # Windows ZipFile's writer normalizes backslashes before writing. Inject
        # equal-length raw names in both ZIP records to exercise the real reader.
        raw = package(extras=[('a_b.xml', xml())])
        for name in (b'a\\b.xml', b'a\x00b.xml'):
            with self.subTest(raw_name=name), self.assertRaises(ValueError):
                m.inspect(raw.replace(b'a_b.xml', name))

    def test_symlink_encryption_and_unsupported_compression_rejected(self):
        for mode in ('link', 'encrypted', 'compression'):
            info = zipfile.ZipInfo('a.xml')
            if mode == 'link': info.external_attr = 0o120777 << 16
            if mode == 'encrypted': info.flag_bits = 1
            if mode == 'compression': info.compress_type = zipfile.ZIP_LZMA
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'BOUNDED_PLAIN_MEMBER'):
                m.direct_member(info)

    def test_member_and_total_expanded_budgets(self):
        raw = package()
        for limit in ('MAX_MEMBER', 'MAX_EXPANDED'):
            with self.subTest(limit=limit), patch.object(m, limit, 1), self.assertRaises(ValueError):
                m.inspect(raw)

    def test_dtd_and_encoded_dtd_rejected(self):
        variants = [b'<!DOCTYPE s [<!ENTITY x "secret">]><s>&x;</s>',
            '<!DOCTYPE s><s/>'.encode('utf-16'), b'<?xml version="1.0" encoding="UTF-16"?><s/>']
        for raw in variants:
            with self.subTest(raw=raw[:15]), self.assertRaises((ValueError, UnicodeError)):
                m.inspect(package(raw))

    def test_malformed_xml_and_archive_rejected(self):
        with self.assertRaises(m.ET.ParseError): m.inspect(package(b'<s>'))
        with self.assertRaises(ValueError): m.inspect(b'not zip')

    def test_document_element_and_depth_budgets(self):
        with patch.object(m, 'MAX_DEPTH', 2), self.assertRaisesRegex(ValueError, 'XML_ELEMENT_OR_DEPTH_LIMIT'):
            m.inspect(package(b'<a><b><c/></b></a>'))
        with patch.object(m, 'MAX_ELEMENTS', 2), self.assertRaisesRegex(ValueError, 'XML_ELEMENT_OR_DEPTH_LIMIT'):
            m.inspect(package(extras=[('second.xml', b'<s><a/></s>')]))

    def test_pacer_or_resource_stop_propagates_without_success(self):
        count = [0]
        def stop():
            count[0] += 1
            if count[0] == 6: raise ValueError('ORIGINAL_RESOURCE_STOP')
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_RESOURCE_STOP'):
            m.inspect(package(), stop)

    def test_crc_is_checked_for_opaque_nonxml_too(self):
        raw = bytearray(package(extras=[('binary.bin', b'opaque')]))
        # Corrupt the advertised CRC in the central record, not a path/value.
        at = raw.rfind(b'PK\x01\x02')
        raw[at + 16] ^= 1
        with self.assertRaises(zipfile.BadZipFile): m.inspect(bytes(raw))

    def test_missing_or_wrong_hwpx_mimetype_rejected(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', b'not hwpx')
            z.writestr('x.xml', xml())
        with self.assertRaisesRegex(ValueError, 'HWPX_MIMETYPE'): m.inspect(out.getvalue())

    def test_streaming_does_not_retain_whole_element_subtrees(self):
        value = m.scan_xml(xml('<h:bookmark/>' * 2000))
        self.assertEqual(value['elements'], 2001)
        self.assertEqual(value['controls']['bookmark'], 2000)

    def test_checkpoint_on_xml_elements(self):
        checks = []
        row = m.scan_xml(xml('<a/><b/>'), lambda: checks.append(True))
        self.assertEqual(len(checks), row['elements'])

    def test_console_summary_binds_archive_but_omits_per_part_dump(self):
        inventory = m.inspect(package())
        row = dict(inventories=[dict(case_id='synthetic', role='control', inventory=inventory)],
            original_resource_samples=[], state='PASS_SYNTHETIC')
        result = m.console_summary(row)
        self.assertEqual(result['inventories'][0]['package_sha256'], inventory['package_sha256'])
        self.assertEqual(result['inventories'][0]['xml_parts'], len(inventory['xml_parts']))
        self.assertEqual(result['inventories'][0]['observed_controls'], inventory['observed_controls'])
        self.assertIn('xml_parts', row['inventories'][0]['inventory'])
        self.assertNotIn('original_resource_samples', result)
        self.assertTrue(result['stdout_is_summary_not_lossless_per_part_or_sample_record'])

    def test_console_summary_missing_resources_are_not_zero(self):
        row = m.console_summary(dict(inventories=[], original_resource_samples=[]))
        self.assertEqual(row['resource_summary']['samples'], 0)
        self.assertIsNone(row['resource_summary']['owned_CPU_max_machine_percent'])
        self.assertIsNone(row['resource_summary']['commit_used_max_percent'])

    def test_console_summary_uses_all_retained_samples(self):
        row = m.console_summary(dict(inventories=[], original_resource_samples=[
            dict(system_cpu_percent=20, parent_cpu_machine_percent=1, parent_private_mib=14,
                available_ram_percent=25, commit_used_percent=50),
            dict(system_cpu_percent=40, parent_cpu_machine_percent=0, parent_private_mib=15,
                available_ram_percent=15, commit_used_percent=60)]))
        self.assertEqual(row['resource_summary'], dict(samples=2, system_CPU_max_percent=40,
            owned_CPU_max_machine_percent=1, private_MiB_max=15, available_RAM_min_percent=15,
            commit_used_max_percent=60))


if __name__ == '__main__':
    unittest.main()
