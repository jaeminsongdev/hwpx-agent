"""Boundary controls for pixel comparisons; no image changes or Native calls."""
import io,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import renamed_bitmap767 as bmp

def sample():
    header=bytearray(54);header[:2]=b'BM';struct.pack_into('<I',header,2,70);struct.pack_into('<I',header,10,54)
    struct.pack_into('<IiiHHI',header,14,40,2,2,1,24,0)
    return bytes(header)+bytes([0,0,0,255,255,255,0,0,255,255,255,255,255,255,0,0])
class Controls(unittest.TestCase):
    def test_header_resolution_changes_are_recorded_without_rewriting_original(self):
        a=sample();b=bytearray(a);struct.pack_into('<i',b,38,3780)
        x=bmp.describe(a,lambda:None);y=bmp.describe(bytes(b),lambda:None)
        self.assertNotEqual(x['file_sha256'],y['file_sha256']);self.assertNotEqual(x['header_sha256'],y['header_sha256'])
        self.assertEqual(x['pixel_sha256'],y['pixel_sha256']);self.assertFalse(y['source_bytes_rewritten'])
    def test_padding_is_separate_and_does_not_hide_actual_pixel_changes(self):
        a=bmp.describe(sample(),lambda:None);b=bytearray(sample());b[60]=7;c=bmp.describe(bytes(b),lambda:None)
        self.assertEqual(a['pixel_sha256'],c['pixel_sha256']);self.assertNotEqual(a['row_padding_sha256'],c['row_padding_sha256'])
        b[54]=255;self.assertNotEqual(a['pixel_sha256'],bmp.describe(bytes(b),lambda:None)['pixel_sha256'])
    def test_nonwhite_channels_and_top_down_row_locations_are_exact(self):
        a=bmp.describe(sample(),lambda:None);self.assertEqual((a['nonwhite_color_channels'],a['nonwhite_rows'],a['first_nonwhite_row'],a['last_nonwhite_row']),(3,1,1,1))
        b=bytearray(sample());b[54:60]=b'\xff'*6;a=bmp.describe(bytes(b),lambda:None)
        self.assertEqual(a['nonwhite_color_channels'],0);self.assertIsNone(a['first_nonwhite_row'])
    def test_bad_signature_size_offset_planes_depth_and_compression_rejected(self):
        for offset,fmt,value in((0,'<H',0),(2,'<I',69),(10,'<I',55),(26,'<H',2),(28,'<H',32),(30,'<I',1)):
            b=bytearray(sample());struct.pack_into(fmt,b,offset,value)
            with self.assertRaises(ValueError):bmp.describe(bytes(b),lambda:None)
    def test_dimension_budgets_and_trailing_or_missing_rows_rejected(self):
        for offset,value in((18,0),(18,4097),(22,-2),(22,4097)):
            b=bytearray(sample());struct.pack_into('<i',b,offset,value)
            with self.assertRaises(ValueError):bmp.describe(bytes(b),lambda:None)
        for b in(sample()[:-1],sample()+b'\x00'):
            with self.assertRaises(ValueError):bmp.describe(b,lambda:None)
    def test_original_checkpoint_stop_propagates(self):
        check=Mock(side_effect=ValueError('MODEL_RESOURCE_STOP'))
        with self.assertRaisesRegex(ValueError,'MODEL_RESOURCE_STOP'):bmp.describe(sample(),check)
    def test_no_producer_or_semantic_authority_is_issued(self):
        value=bmp.describe(sample(),lambda:None)
        self.assertFalse(value['native_producer_attested_by_parser']);self.assertFalse(value['semantic_or_OCR_acceptance'])
if __name__=='__main__':
    out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),actual_native_started=False,failed_test_ids=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures])))
    raise SystemExit(0 if result.wasSuccessful()else 2)
