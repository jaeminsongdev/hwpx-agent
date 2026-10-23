"""Publication/storage only: no native claim/worker, old-generation outputs or source edits."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import compact_receipt_json as compact
import crossref_generation008_publication as subject
import crossref_inline_receipt567 as layout

def row():return dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',generation=8,P09_gate='OPEN',P10_started=False,
    accepted_count_delta=0,Native011_executed=False,native_startup_qualified=False,crossref_semantics_qualified=False,
    fixed_eight_executed=False,cleanup=False,error_code='P09_XREF_BIND_SOURCE_READ_LEASE_FAILED')

class Publication(unittest.TestCase):
    def setUp(self):
        self.parent=Path(__file__).resolve().parents[3]/'target';self.parent=self.parent.resolve(strict=True)
        self.temp=tempfile.TemporaryDirectory(prefix='p09-pub573-model-',dir=self.parent);self.root=Path(self.temp.name).resolve(strict=True)
        self.assertTrue(self.root.is_relative_to(self.parent));self.assertFalse(self.root.is_junction())
        (self.root/subject.SPOOL).parent.mkdir(parents=True)
        self.addCleanup(self.clean_owned)
    def clean_owned(self):
        self.assertTrue(self.root.is_relative_to(self.parent));self.assertTrue(self.root.name.startswith('p09-pub573-model-'))
        self.assertFalse(self.root.is_symlink());self.assertFalse(self.root.is_junction());self.temp.cleanup()
        self.assertFalse(self.root.exists())
    def test_failure_is_retained_and_original_writer_publishes_complete_inline_packet(self):
        value=row();raw=compact.raw(value);proof=subject.publish_final(self.root,value)
        published=(self.root/subject.OUTPUT).read_bytes()
        self.assertEqual(proof['sha256'],hashlib.sha256(published).hexdigest());self.assertLessEqual(len(published),262144)
        self.assertEqual(compact.raw(layout.unpack(json.loads(published))),raw)
        self.assertEqual(compact.raw(subject.retained_row(self.root)),raw)
        self.assertNotIn(subject.SPOOL,published.decode());self.assertEqual(compact.raw(value),raw)
    def test_original_outer_limit_failure_from_repeated_pins_is_published_losslessly(self):
        value=row();pin=dict(path='implementation/p09/tools/closed-fixed-input.ps1',bytes=1234,sha256='a'*64)
        found=False
        for count in range(900,1900,10):
            value['source_pins']=[copy.deepcopy(pin)for _ in range(count)]
            try:compact.pack(value)
            except ValueError as error:
                if error.args==('COMPACT_RECEIPT_OUTER_LIMIT',):found=True;break
        self.assertTrue(found);raw=compact.raw(value);proof=subject.publish_final(self.root,value)
        self.assertLessEqual(proof['bytes'],262144)
        self.assertEqual(compact.raw(layout.unpack(json.loads((self.root/subject.OUTPUT).read_bytes()))),raw)
        self.assertEqual(compact.raw(subject.retained_row(self.root)),raw)
    def test_even_new_codec_failure_keeps_exact_row_and_does_not_publish_fake_terminal_result(self):
        value=row();value['synthetic_quoted_data']='"'*90000
        with self.assertRaisesRegex(ValueError,'^XREF008_PUBLICATION_ENCODING_FAILED_EXACT_RAW_ROW_RETAINED$'):
            subject.publish_final(self.root,value)
        self.assertFalse((self.root/subject.OUTPUT).exists())
        self.assertEqual(compact.raw(subject.retained_row(self.root)),compact.raw(value))
    def test_invalid_generation_and_authority_changes_fail_before_any_spool_write(self):
        for key,val in(('generation',4),('generation',True),('P09_gate','CLOSED'),('P10_started',True),('accepted_count_delta',1),
            ('accepted_count_delta',False),('Native011_executed',True),('native_startup_qualified',True),('crossref_semantics_qualified',True),('state','PASS_P09')):
            value=row();value[key]=val
            with self.subTest(key=key,val=val):
                with self.assertRaises(ValueError):subject.publish_final(self.root,value)
                self.assertFalse((self.root/subject.SPOOL).exists());self.assertFalse((self.root/subject.OUTPUT).exists())
    def test_existing_result_and_spool_are_never_overwritten_or_reused(self):
        subject.publish_final(self.root,row());before=(self.root/subject.OUTPUT).read_bytes()
        with self.assertRaises(ValueError):subject.publish_final(self.root,row())
        self.assertEqual((self.root/subject.OUTPUT).read_bytes(),before)
        (self.root/subject.OUTPUT).unlink()
        with self.assertRaisesRegex(ValueError,'SPOOL_IMMUTABLE_NO_REPLAY'):subject.publish_final(self.root,row())
    def test_corrupted_part_cannot_be_read_as_preserved_evidence(self):
        subject.publish_final(self.root,row());part=self.root/subject.SPOOL/'part-0000.bin'
        part.write_bytes(b'corrupt-owned-test-fixture')
        with self.assertRaisesRegex(ValueError,'PART_INTEGRITY'):subject.retained_row(self.root)
    def test_manifest_path_traversal_is_rejected_without_reading_external_files(self):
        subject.publish_final(self.root,row());path=self.root/subject.SPOOL/subject.MANIFEST
        manifest=json.loads(path.read_bytes());manifest['parts'][0]['path']='../../foreign'
        path.write_bytes(compact.raw(manifest))
        with self.assertRaisesRegex(ValueError,'EXACT_PART'):subject.retained_row(self.root)
    def test_row_limit_and_reparse_directory_fail_closed(self):
        value=row();value['oversize']='x'*subject.MAX_BYTES
        with self.assertRaisesRegex(ValueError,'ROW_BOUND'):subject.publish_final(self.root,value)
        with patch.object(Path,'is_junction',return_value=True):
            with self.assertRaises(ValueError):subject.publish_final(self.root,row())
        self.assertFalse((self.root/subject.SPOOL).exists())
    def test_captured_eight_remains_semantically_unqualified_and_does_not_publish_any_claim(self):
        value=row();value.update(state='CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED',fixed_eight_executed=True,captured_cases=8)
        subject.publish_final(self.root,value);restored=subject.retained_row(self.root)
        self.assertFalse(restored['native_startup_qualified']);self.assertEqual(restored['P09_gate'],'OPEN')
        self.assertFalse((self.root/'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim008.v1.json').exists())
        for old in range(1,7):self.assertFalse((self.root/f'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run{old:03}.v1.json').exists())
    def test_preserved003_values_round_trip_only_in_synthetic_temporary008_namespace(self):
        path=Path(__file__).resolve().parents[3]/'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run003.v1.json'
        before=path.read_bytes();digest=hashlib.sha256(before).hexdigest()
        self.assertEqual(digest,'901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a')
        value=compact.unpack(json.loads(before));value['original_model_generation']=value['generation'];value['generation']=7
        value['temporary_publication_model_only_not_new_native_result']=True
        raw=compact.raw(value);subject.publish_final(self.root,value)
        self.assertEqual(compact.raw(subject.retained_row(self.root)),raw)
        self.assertEqual(compact.raw(layout.unpack(json.loads((self.root/subject.OUTPUT).read_bytes()))),raw)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)

if __name__=='__main__':unittest.main()
