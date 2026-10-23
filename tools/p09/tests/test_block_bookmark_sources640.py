"""Seven new scanner controls, never native output fixtures or captures."""
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inspect_block_bookmark_sources640 as m


def package(body, name='Contents/section0.xml'):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr(name, '<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'+body+'</hp:sec>')
    return out.getvalue()


class Tests(unittest.TestCase):
    def test_point_is_not_a_block(self):
        v=m.inspect(package('<hp:bookmark name="private"/>'))
        self.assertEqual(v['point_markers'],1)
        self.assertEqual(v['block_field_candidates'],[])
    def test_matching_range_and_body_hash_without_values(self):
        v=m.inspect(package('<hp:fieldBegin id="1" type="BOOKMARK"><hp:parameters><hp:stringParam name="Name">private-name</hp:stringParam></hp:parameters></hp:fieldBegin><hp:t>private-body</hp:t><hp:fieldEnd beginIDRef="1"/>'))
        self.assertEqual(len(v['block_field_candidates']),1)
        self.assertEqual(v['block_field_candidates'][0]['body_text_utf8_bytes'],12)
        self.assertNotIn('private',json.dumps(v))
        self.assertFalse(v['block_field_candidates'][0]['Native_provenance_or_target_binding_qualified'])
    def test_wrong_end_rejected(self):
        with self.assertRaisesRegex(ValueError,'FIELD_END_BINDING'):
            m.inspect(package('<hp:fieldBegin id="1" type="BOOKMARK"/><hp:fieldEnd beginIDRef="2"/>'))
    def test_unclosed_range_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNFINISHED_FIELD_RANGE'):
            m.inspect(package('<hp:fieldBegin id="1" type="BOOKMARK"/>'))
    def test_entity_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'XML_NO_DTD_OR_ENTITY'):
            m.inspect(package('<!DOCTYPE private>'))
    def test_foreign_namespace_does_not_make_a_native_range(self):
        v=m.inspect(package('<x:fieldBegin xmlns:x="urn:other" id="1" type="BOOKMARK"/>'))
        self.assertEqual(v['block_field_candidates'],[])
    def test_zip_path_and_document_budget(self):
        with self.assertRaisesRegex(ValueError,'ZIP_NAMES'):
            m.inspect(package('', '../section0.xml'))
        with self.assertRaisesRegex(ValueError,'DOCUMENT_BYTE_BOUND'):
            m.inspect(b'x'*(4*1024*1024+1))


if __name__=='__main__':
    result=unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful() else 2)
