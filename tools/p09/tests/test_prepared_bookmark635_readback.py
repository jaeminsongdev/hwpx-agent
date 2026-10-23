"""Strict behavior of the unchanged633 field-span observer. No Native/replay."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inspect_prepared_bookmark633 as subject

NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'


def document(body):
    return ET.fromstring('<hp:sec xmlns:hp="'+NS+'"><hp:p>'+body+'</hp:p></hp:sec>')


def field(text='result', end='7', params=''):
    return '<hp:run><hp:fieldBegin id="7" type="CROSSREF" dirty="0">'+params+'</hp:fieldBegin></hp:run><hp:run><hp:t>'+text+'</hp:t></hp:run><hp:run><hp:fieldEnd beginIDRef="'+end+'"/></hp:run>'


class Contracts(unittest.TestCase):
    def read(self, body): return subject.observe(document(body))

    def test_01_exact_one_field_and_balanced_end(self):
        row = self.read(field())
        self.assertEqual(row['crossref_count'], 1)
        self.assertEqual(row['crossrefs'][0]['display_sha256'], subject.digest('result'))

    def test_02_paragraph_text_outside_field_excluded(self):
        row = self.read('<hp:run><hp:t>outside-before</hp:t></hp:run>'+field()+'<hp:run><hp:t>outside-after</hp:t></hp:run>')
        self.assertEqual(row['crossrefs'][0]['display_sha256'], subject.digest('result'))

    def test_03_multiple_runs_concatenate_in_order(self):
        body = field().replace('<hp:t>result</hp:t>', '<hp:t>res</hp:t></hp:run><hp:run><hp:t>ult</hp:t>')
        self.assertEqual(self.read(body)['crossrefs'][0]['display_sha256'], subject.digest('result'))

    def test_04_wrong_end_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'MATCHED_FIELD_END'):
            self.read(field(end='8'))

    def test_05_unclosed_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'COMPLETE_FIELD_SPAN'):
            self.read(field().replace('<hp:fieldEnd beginIDRef="7"/>', ''))

    def test_06_structured_display_not_silently_flattened(self):
        with self.assertRaisesRegex(ValueError, 'PLAIN_FIELD_DISPLAY_PROFILE'):
            self.read(field('<hp:tab/>'))

    def test_07_duplicate_parameter_names_rejected(self):
        value = '<hp:parameters><hp:stringParam name="Command">a</hp:stringParam><hp:stringParam name="Command">b</hp:stringParam></hp:parameters>'
        with self.assertRaisesRegex(ValueError, 'UNIQUE_PARAMETER_NAMES'):
            self.read(field(params=value))

    def test_08_parameter_values_never_in_report(self):
        secret = 'MODEL_PRIVATE_SENTINEL_VALUE'
        row = self.read(field(params='<hp:parameters><hp:stringParam name="Command">'+secret+'</hp:stringParam></hp:parameters>'))
        self.assertNotIn(secret, json.dumps(row))
        self.assertEqual(row['crossrefs'][0]['command_sha256'], subject.digest(secret))

    def test_09_foreign_namespace_field_not_accepted(self):
        body = field().replace('hp:fieldBegin', 'other:fieldBegin').replace('id="7"', 'xmlns:other="urn:other" id="7"', 1)
        self.assertEqual(self.read(body)['crossref_count'], 0)

    def test_10_empty_display_distinct_from_zero(self):
        a, b = self.read(field(''))['crossrefs'][0], self.read(field('0'))['crossrefs'][0]
        self.assertTrue(a['display_is_empty'])
        self.assertFalse(b['display_is_empty'])
        self.assertTrue(b['display_is_ascii_integer'])
        self.assertNotEqual(a['display_sha256'], b['display_sha256'])

    def test_11_boolean_and_parameter_text_are_not_display(self):
        row = self.read(field('1', params='<hp:parameters><hp:booleanParam name="RefHyperLink">false</hp:booleanParam></hp:parameters>'))
        self.assertEqual(row['crossrefs'][0]['display_sha256'], subject.digest('1'))
        self.assertEqual(row['crossrefs'][0]['parameter_hashes']['RefHyperLink'], subject.digest('false'))

    def test_12_dirty_flag_is_observed_not_reinterpreted_as_execution(self):
        row = self.read(field('not-calculated').replace('dirty="0"', 'dirty="1"'))
        self.assertEqual(row['crossrefs'][0]['dirty'], '1')
        self.assertNotIn('semantic_acceptance_qualified', row)


if __name__ == '__main__':
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
                         failed_tests=[str(t) for t, _ in result.errors+result.failures], actual_native_started=False)))
    sys.exit(0 if result.wasSuccessful() else 2)
