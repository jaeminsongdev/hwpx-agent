import io,json,unittest,zipfile
import crossref_capture010_shape612 as subject

COMMANDS=['synthetic-private-command-'+str(i)for i in range(8)]
def package(xml,extra=None):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w')as z:
        z.writestr('Contents/section0.xml',xml)
        if extra is not None:z.writestr(extra,b'x')
    return out.getvalue()
def xml(value=COMMANDS[0]):return '<root><fieldBegin type="CROSSREF"><parameters><stringParam name="private-key">'+value+'</stringParam><integerParam name="private-int">1</integerParam></parameters></fieldBegin></root>'

class Shape(unittest.TestCase):
    def test_01_exact_decoded_match_and_no_raw_values(self):
        row=subject.inspect(package(xml()),COMMANDS[0],COMMANDS);self.assertEqual(row['crossref_fields'],1)
        self.assertEqual(row['fields'][0]['exact_selected_matching_children'],1);text=json.dumps(row)
        self.assertNotIn(COMMANDS[0],text);self.assertNotIn('private-key',text);self.assertFalse(row['parameter_key_semantics_qualified'])
    def test_02_other_candidate_is_not_selected_or_semantic_pass(self):
        row=subject.inspect(package(xml(COMMANDS[1])),COMMANDS[0],COMMANDS)
        self.assertEqual(row['fields'][0]['exact_selected_matching_children'],0);self.assertEqual(row['fields'][0]['parameter_children'][0]['other_candidate_matches'],1)
    def test_03_missing_parameters_and_other_field_kinds_stay_distinct(self):
        row=subject.inspect(package('<root><fieldBegin type="CROSSREF"/><fieldBegin type="BOOKMARK"/></root>'),COMMANDS[0],COMMANDS)
        self.assertEqual(row['crossref_fields'],1);self.assertFalse(row['fields'][0]['has_parameters'])
    def test_04_dtd_and_entity_are_rejected(self):
        for xml in('<!DOCTYPE root><root/>','<!ENTITY a "x"><root/>'):
            with self.assertRaises(ValueError):subject.inspect(package(xml),COMMANDS[0],COMMANDS)
    def test_05_path_traversal_and_excessive_zip_output_are_rejected(self):
        with self.assertRaises(ValueError):subject.inspect(package(xml(),'../foreign'),COMMANDS[0],COMMANDS)
        with self.assertRaises(ValueError):subject.inspect(b'x'*(subject.MAX_BYTES+1),COMMANDS[0],COMMANDS)
    def test_06_wrong_candidate_set_denied(self):
        for values in(COMMANDS[:7],[COMMANDS[0]]*8):
            with self.assertRaises(ValueError):subject.inspect(package(xml()),COMMANDS[0],values)
    def test_07_pressure_exception_is_not_swallowed(self):
        def stop():raise ValueError('STOP_MODEL_RESOURCE')
        with self.assertRaisesRegex(ValueError,'STOP_MODEL_RESOURCE'):subject.inspect(package(xml()),COMMANDS[0],COMMANDS,stop)
    def test_09_binary_adapter_retains_original_reader_and_exact_binding(self):
        from types import SimpleNamespace as NS
        from unittest.mock import Mock
        pin=dict(path='fixed.hwpx',bytes=2,sha256='a'*64)
        reader=NS(_read=Mock(return_value=(pin,bytearray(b'PK'))),_bind=Mock(return_value=pin))
        self.assertEqual(subject.read_package(reader,pin),b'PK');reader._read.assert_called_once_with('fixed.hwpx',parse=True)
        reader._bind.assert_called_once_with('fixed.hwpx',pin)
        reader._bind.return_value={}
        with self.assertRaises(ValueError):subject.read_package(reader,pin)
    def test_08_nested_parameter_text_is_observed_not_qualified(self):
        row=subject.inspect(package(xml('<inner>'+COMMANDS[0]+'</inner>')),COMMANDS[0],COMMANDS)
        leaf=row['fields'][0]['parameter_children'][0];self.assertEqual(leaf['nested_children'],1);self.assertTrue(leaf['exact_selected_command_match']);self.assertFalse(row['P09_complete'])

if __name__=='__main__':unittest.main()
