import json,tempfile,unittest
from pathlib import Path
import metadata_forensic_retention615 as subject
import compact_receipt_json as compact
import crossref_lossless_receipt610 as codec

class Retention(unittest.TestCase):
    def test_01_harness_tuples_preserve_exact_original_json_bytes(self):
        row=dict(state='FAILED_ORIGINAL',steps=[dict(tests=[('case','ok')],locations=[('fixed.rs','1','2')])])
        normalized,raw=subject.normalize(row);self.assertEqual(raw,compact.raw(row));self.assertIs(type(normalized['steps'][0]['tests'][0]),list)
        self.assertEqual(compact.raw(codec.unpack(codec.pack(normalized))),raw)
    def test_02_nonjson_object_and_excessive_rows_fail_before_filesystem(self):
        with self.assertRaises(TypeError):subject.normalize(dict(state='x',value=object()))
        with self.assertRaises(ValueError):subject.normalize(dict(state='x',value='x'*subject.MAXIMUM))
    def test_03_owned_chunk_spool_retains_all_bytes_and_cannot_overwrite(self):
        parent=Path(__file__).resolve().parents[3]/'target';parent=parent.resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix='p09-metadata615-model-',dir=parent)as name:
            root=Path(name).resolve(strict=True);self.assertTrue(root.is_relative_to(parent));self.assertFalse(root.is_junction())
            (root/'private').mkdir();row=dict(state='FAILED_ORIGINAL',value='x'*160000)
            result,pin=subject.retain(root,'private/spool',row);self.assertEqual(result,row)
            metadata=json.loads((root/pin['path']).read_text());self.assertEqual(len(metadata['parts']),3)
            with self.assertRaises(ValueError):subject.retain(root,'private/spool',row)
    def test_04_failure_status_flags_and_none_are_not_promoted(self):
        value=dict(state='FAILED_ORIGINAL',cleanup=False,Native_started=False,items=None,count=0)
        normalized,raw=subject.normalize(value);self.assertEqual(normalized,value);self.assertEqual(compact.raw(normalized),raw)

if __name__=='__main__':unittest.main()
